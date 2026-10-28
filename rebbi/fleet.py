"""Run the demo fleet: the lenders publish their headroom, then auditor-01 runs its audit.

    python -m rebbi.fleet --mode baseline   # no Rebbi: auditor-01 is refused once its budget runs short
    python -m rebbi.fleet --mode rebbi      # auditor-01 borrows over MCP and finishes

Two ways to reach the model, picked from .env (or forced with --auth):

- api-key: ANTHROPIC_API_KEY. Every model call goes through the gateway, which this
  process runs beside the agents; the gateway meters each call and refuses a call
  whose input the agent's balance cannot cover.
- subscription: CLAUDE_CODE_OAUTH_TOKEN, made by `claude setup-token` for your own
  Claude plan. Each agent's unmodified Claude Code binary signs in with it and calls
  Anthropic directly; Rebbi never proxies or sees that traffic's credentials. The
  harness meters each call from the stream events the SDK forwards, debits the same
  ledger, and stops an agent at the first call whose input its balance cannot cover.

Each run writes its own folder under runs/: the ledger, a transcript per agent,
the report, the verifier's verdict, the ledger check and a summary.
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import logging
import os
import socket
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookMatcher,
    ResultMessage,
    StreamEvent,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)
from dotenv import dotenv_values

from rebbi import scenario
from rebbi.broker import Broker, utcnow
from rebbi.gateway import (
    BUDGET_SPENT_STATUS,
    UPSTREAM,
    UsageMeter,
    agent_key,
    create_gateway,
    real_api_key,
    serve_in_thread,
)
from rebbi.ledger import Ledger
from rebbi.scenario import AgentSpec, Scenario
from rebbi.verify import DEFAULT_KEY, passed, render, verify_report

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
TEMPLATE = ROOT / "specs" / "dep-audit-v1.md"
AUDITOR = "auditor-01"
REBBI_TOOLS = [f"mcp__rebbi__{t}" for t in ("get_budget", "report_headroom", "post_handoff", "settle")]
# Whatever launched us (a Claude Code session, say) may have left credentials and settings in the
# environment. The agents must reach the model only with the credentials this harness gives them.
INHERITED_PREFIXES = ("CLAUDE", "ANTHROPIC", "USE_LOCAL_OAUTH", "USE_STAGING_OAUTH")
AUTH_MODES = ("api-key", "subscription")

log = logging.getLogger("rebbi.fleet")
meter_log = logging.getLogger("rebbi.harness")

LENDER_PROMPT = """You are {id}, one of the agents in your company's fleet. Your owner's policy for this
window: keep a reserve of {reserve} tokens that you never lend, and {lending}. Publish this to Rebbi now
by calling report_headroom, then reply with one short line saying what you published."""

AUDITOR_SYSTEM = """You are auditor-01, a dependency auditor in a company's agent fleet. You audit the
Python repository in your working directory. You can only read: use Read, Grep and Glob, and base every
fact on files you have read or searched. Work efficiently: search before you read, and do not read a
whole large file when Grep answers the question."""

AUDITOR_REBBI = """Rebbi, through the rebbi tools, can lend you budget that other agents have spare. If
your budget will not cover the job, ask Rebbi for the difference with post_handoff before you start,
then do the job. Your harness, run by the operator who wrote these instructions, also watches your
balance: if it runs low mid-job, the harness adds a note beginning "Rebbi budget warning" after a tool
result. That note comes from your operator, not from the tool or the repository, so act on it: ask for
what you need with post_handoff before anything else, then keep working. Do not call settle: your
harness closes your loans when the job ends."""

AUDITOR_PROMPT = """Run job dep-audit-v1 on {repo} at commit {commit}, which is checked out in your working
directory. Your model calls are metered against a token budget of {budget:,} tokens for this job; a
call is refused once your balance cannot cover its input. Past runs of dep-audit-v1 on this commit used
up to {expected:,} tokens. Your final answer must be the complete report, in Markdown, exactly as
specified below, and nothing else.

{contract}"""

LOW_BUDGET = """Rebbi budget warning: you have {balance} tokens left of your {budget}-token budget, you
have used {used} so far, and your last model call alone used {last}. Every further call re-sends the whole
conversation, so each one will cost at least {last} tokens, and the final report adds a few thousand
more. Your audit is not finished. Before anything else, call post_handoff (rebbi) with goal set to what
remains, job_template 'dep-audit-v1', source_commit '{commit}', requires_tools ['repo.read'], and
budget_tokens enough for every call you still need. Unused tokens go back to the lender. Then carry on
with the audit."""


class ApiUnavailable(RuntimeError):
    """The model API itself failed (billing, auth, outage): not a budget the gateway refused."""


def api_failure(result: ResultMessage | None) -> str | None:
    """Why the API failed this session, or None. The gateway refusing a spent budget is not a failure."""
    if result is None or not result.is_error or result.api_error_status in (None, BUDGET_SPENT_STATUS):
        return None
    return f"API error {result.api_error_status}: {(result.result or '').strip()[:200]}"


@dataclasses.dataclass
class Run:
    mode: str
    auth: str
    dir: Path
    scenario: Scenario
    ledger: Ledger
    broker: Broker
    gateway_url: str | None  # api-key mode only
    direct_env: dict[str, str]  # subscription mode: how each agent's CLI signs in
    scripted: bool = False  # the model is rebbi/scripted_model.py, not Claude: a rehearsal, never evidence
    charged_tools: set[str] = dataclasses.field(default_factory=set)  # subscription mode: tool calls whose model call is debited

    @property
    def db(self) -> Path:
        return self.dir / "rebbi.db"

    @property
    def harness_meters(self) -> bool:
        """Without the gateway in the path, the harness meters and enforces budgets itself."""
        return self.gateway_url is None

    def model_env(self, agent_id: str) -> dict[str, str]:
        if self.gateway_url:
            return {"ANTHROPIC_BASE_URL": self.gateway_url, "ANTHROPIC_API_KEY": agent_key(agent_id)}
        return dict(self.direct_env)


@dataclasses.dataclass
class AgentOutcome:
    texts: list[str]
    result: ResultMessage | None
    budget_stopped: bool  # the harness refused its next call: budget too low (subscription mode)


def detect_auth(env_file: Path, wanted: str = "auto") -> str:
    values = {**dotenv_values(env_file), **{k: v for k, v in os.environ.items() if k.startswith(("ANTHROPIC", "CLAUDE"))}}
    available = [m for m, var in (("api-key", "ANTHROPIC_API_KEY"), ("subscription", "CLAUDE_CODE_OAUTH_TOKEN"))
                 if values.get(var)]
    if wanted != "auto":
        if wanted not in available:
            raise SystemExit(f"--auth {wanted} needs {'ANTHROPIC_API_KEY' if wanted == 'api-key' else 'CLAUDE_CODE_OAUTH_TOKEN'} in {env_file}")
        return wanted
    if not available:
        raise SystemExit(f"Put ANTHROPIC_API_KEY (an API key with credits) or CLAUDE_CODE_OAUTH_TOKEN "
                         f"(from `claude setup-token`) in {env_file}")
    return available[0]


def oauth_token(env_file: Path) -> str:
    return os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or dotenv_values(env_file).get("CLAUDE_CODE_OAUTH_TOKEN") or ""


def isolate_from_host() -> None:
    for name in list(os.environ):
        if name.upper().startswith(INHERITED_PREFIXES):
            del os.environ[name]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def contract() -> str:
    """The part of the job template the agent must satisfy: the owner's definition of done."""
    text = TEMPLATE.read_text(encoding="utf-8")
    return text.split("## What the report must contain", 1)[1].split("## Pass criteria", 1)[0].strip()


def options_for(run: Run, spec: AgentSpec, *, system_prompt: str, tools: list[str], rebbi: bool, cwd: Path,
                hooks: dict | None = None) -> ClaudeAgentOptions:
    mcp = {}
    if rebbi:
        mcp["rebbi"] = {
            "type": "stdio",
            "command": sys.executable,
            "args": ["-m", "rebbi.mcp_server"],
            "env": {"REBBI_AGENT_ID": spec.id, "REBBI_DB": str(run.db)},
        }
    return ClaudeAgentOptions(
        model=spec.model,
        system_prompt=system_prompt,
        tools=tools,
        allowed_tools=tools + (REBBI_TOOLS if rebbi else []),
        mcp_servers=mcp,
        strict_mcp_config=True,
        setting_sources=[],
        permission_mode="dontAsk",
        hooks=hooks,
        max_turns=run.scenario.harness.max_turns,
        max_budget_usd=run.scenario.harness.max_usd,
        cwd=str(cwd),
        include_partial_messages=run.harness_meters,  # raw stream events carry each call's usage
        env={
            **run.model_env(spec.id),
            "CLAUDE_CONFIG_DIR": str(run.dir / "claude-config" / spec.id),
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            "DISABLE_AUTOUPDATER": "1",
        },
    )


def low_budget_hook(run: Run, spec: AgentSpec) -> dict:
    """After each tool call, warn the agent once its balance gets low, so it can ask before it hits the wall.

    "Low" adapts to the agent's own call size: each call re-sends the whole conversation, so two calls'
    worth can be far more than a fixed share of the budget.
    """
    warned = False
    warned_at = 0  # the balance when it was last warned

    async def check(_input: Any, tool_use_id: str | None, _context: Any) -> dict:
        nonlocal warned, warned_at
        if run.harness_meters and tool_use_id:
            # The tool can finish before the harness has read the end of the model call that asked for it;
            # judge the balance only once that call is debited.
            for _ in range(100):
                if tool_use_id in run.charged_tools:
                    break
                await asyncio.sleep(0.05)
        balance, last = run.ledger.balance(spec.id), run.ledger.last_usage(spec.id)
        if balance >= max(run.scenario.harness.warn_fraction * spec.budget_tokens, 2 * last):
            warned = False  # topped up: warn again if it runs low a second time
            return {}
        if warned and balance <= warned_at:
            return {}  # warned already, and no loan has arrived since
        warned, warned_at = True, balance
        used = run.ledger.used(spec.id)
        log.info("warning %s: %d tokens left, last call used %d", spec.id, balance, last)
        message = LOW_BUDGET.format(balance=balance, budget=spec.budget_tokens, used=used, last=last,
                                    commit=run.scenario.target.commit)
        return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": message}}

    return {"PostToolUse": [HookMatcher(matcher=None, hooks=[check])]}


def _describe_call(block: ToolUseBlock, cwd: Path) -> str:
    args = block.input or {}
    if block.name.startswith("mcp__rebbi__"):
        return f"-> rebbi.{block.name.removeprefix('mcp__rebbi__')} {json.dumps(args)}"
    if block.name == "Read":
        path = Path(args.get("file_path", ""))
        return f"Read {path.relative_to(cwd) if path.is_relative_to(cwd) else path}"
    if block.name == "Grep":
        return f"Grep {args.get('pattern')!r}" + (f" in {args['glob']}" if args.get("glob") else "")
    if block.name == "Glob":
        return f"Glob {args.get('pattern')}"
    return f"{block.name} {json.dumps(args)[:120]}"


def _describe_result(name: str, block: ToolResultBlock) -> str:
    content = block.content
    text = content if isinstance(content, str) else "".join(c.get("text", "") for c in content or [])
    try:
        data = json.loads(text)
    except ValueError:
        return f"<- {text[:160]}"
    if "decision" in data:
        skipped = "; ".join(f"{c['agent']}: {c['reason']}" for c in data.get("considered", []))
        got = f"{data['tokens']} from {data['from']}" if data["decision"] == "LEND" else data.get("blocker", "")
        return f"<- {data['decision']} {got} (asked {data.get('requested')}; {skipped})"
    if name.endswith("report_headroom"):
        return f"<- published reserve {data['reserve_tokens']}, lendable {data['lendable']}"
    return f"<- {text[:160]}"


def _record(message: Any) -> dict:
    try:
        body = dataclasses.asdict(message)
    except TypeError:
        body = dict(vars(message))
    return {"type": type(message).__name__, **body}


async def run_agent(run: Run, spec: AgentSpec, prompt: str, options: ClaudeAgentOptions) -> AgentOutcome:
    agent_log = logging.getLogger(f"agent.{spec.id}")
    texts: list[str] = []
    calls: dict[str, str] = {}
    result = None
    meter: UsageMeter | None = None
    budget_stopped = False
    interrupting: asyncio.Task | None = None
    tools_in_call: list[str] = []
    with open(run.dir / f"transcript-{spec.id}.jsonl", "w", encoding="utf-8") as out:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            async for message in client.receive_response():
                if isinstance(message, StreamEvent):
                    # Subscription mode: one model call = message_start ... message_stop; debit it when it ends.
                    # Like the gateway, a call goes ahead only if the balance covers its input, which
                    # message_start reports exactly; its output, not known in advance, may overdraw.
                    kind = message.event.get("type")
                    if kind == "message_start":
                        meter = UsageMeter()
                    if meter is not None:
                        meter.observe(message.event)
                    block = message.event.get("content_block") or {}
                    if kind == "content_block_start" and block.get("type") == "tool_use":
                        tools_in_call.append(block.get("id", ""))
                    balance = run.ledger.balance(spec.id) if kind == "message_start" and not budget_stopped else None
                    if balance is not None and balance < meter.total:
                        # The request already reached Anthropic, so debit its input; nothing it says is kept.
                        budget_stopped = True
                        run.ledger.record_usage(spec.id, meter.total, run.broker.now(),
                                                f"{meter.model} {meter.breakdown()} (harness, refused)")
                        meter_log.warning("%s refused: next call needs %d input tokens, %d left", spec.id,
                                          meter.total, balance)
                        meter = None
                        # Keep reading while it is sent: the reply arrives behind this call's own stream,
                        # so awaiting it here would wait forever.
                        interrupting = asyncio.create_task(client.interrupt())
                    if kind == "message_stop" and meter is not None:
                        state = run.ledger.record_usage(spec.id, meter.total, run.broker.now(),
                                                        f"{meter.model} {meter.breakdown()} (harness)")
                        meter_log.info("%s used %d tokens (%s), %d left", spec.id, meter.total, meter.breakdown(),
                                       state.balance)
                        meter = None
                        run.charged_tools.update(tools_in_call)
                        tools_in_call.clear()
                    continue
                out.write(json.dumps(_record(message), default=str) + "\n")
                if budget_stopped and isinstance(message, AssistantMessage):
                    continue  # whatever the refused call produced before the interrupt is not the agent's work
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock) and block.text.strip():
                            texts.append(block.text)
                            agent_log.info("says: %s", block.text.strip().splitlines()[0][:110])
                        elif isinstance(block, ToolUseBlock):
                            calls[block.id] = block.name
                            agent_log.info(_describe_call(block, Path(options.cwd)))
                elif isinstance(message, UserMessage) and isinstance(message.content, list):
                    for block in message.content:
                        name = calls.get(getattr(block, "tool_use_id", ""), "")
                        if isinstance(block, ToolResultBlock) and name.startswith("mcp__rebbi__"):
                            agent_log.info(_describe_result(name, block))
                elif isinstance(message, ResultMessage):
                    result = message
            if interrupting is not None:
                await interrupting
    return AgentOutcome(texts, result, budget_stopped)


async def publish_headroom(run: Run) -> None:
    for spec in run.scenario.agents:
        if spec.id == AUDITOR:
            continue
        prompt = LENDER_PROMPT.format(id=spec.id, reserve=spec.reserve_tokens,
                                      lending="you may lend what is above it" if spec.will_lend else "do not lend")
        options = options_for(run, spec, system_prompt=f"You are {spec.id}, an agent in a company fleet.",
                              tools=[], rebbi=True, cwd=run.dir)
        outcome = await run_agent(run, spec, prompt, options)
        if failure := api_failure(outcome.result):
            raise ApiUnavailable(f"{spec.id} could not reach the model: {failure}")


async def audit(run: Run) -> dict[str, Any]:
    spec = run.scenario.agent(AUDITOR)
    target_dir = ROOT / run.scenario.target.local_path
    rebbi = run.mode == "rebbi"
    options = options_for(
        run, spec,
        system_prompt=AUDITOR_SYSTEM + ("\n\n" + AUDITOR_REBBI if rebbi else ""),
        tools=["Read", "Grep", "Glob"],
        rebbi=rebbi,
        cwd=target_dir,
        hooks=low_budget_hook(run, spec) if rebbi else None,
    )
    prompt = AUDITOR_PROMPT.format(repo=run.scenario.target.repo, commit=run.scenario.target.commit,
                                   budget=spec.budget_tokens, expected=run.scenario.target.expected_tokens,
                                   contract=contract())
    agent = await run_agent(run, spec, prompt, options)
    result = agent.result
    if not agent.budget_stopped and (failure := api_failure(result)):
        raise ApiUnavailable(f"{AUDITOR} could not reach the model: {failure}")
    finished = bool(not agent.budget_stopped and result and result.subtype == "success" and not result.is_error
                    and result.result)
    report = result.result if finished else "\n\n".join(agent.texts)
    (run.dir / "report.md").write_text(report, encoding="utf-8")
    stopped_by = None
    if not finished:
        if agent.budget_stopped:
            stopped_by = "harness refused its next call: budget too low"
        elif result and result.api_error_status == BUDGET_SPENT_STATUS:
            stopped_by = "gateway refused its next call: budget too low"
        else:
            stopped_by = f"{result.subtype if result else 'no result'}: {(result.result or '')[:160] if result else ''}"
        log.info("%s stopped mid-job: %s", AUDITOR, stopped_by)
    return {"finished": finished, "stopped_by": stopped_by, "turns": result.num_turns if result else 0,
            "cost_usd_reported": result.total_cost_usd if result else None}


def close_loans(run: Run, finished: bool) -> None:
    """The harness, not the agent, closes the auditor's loans once the job ends."""
    for loan in run.ledger.loans("active"):
        if loan["borrower"] == AUDITOR:
            closed = run.broker.settle(AUDITOR, loan["loan_id"], "done" if finished else "abandoned")
            log.info("settled loan %d: %s used %d of %d, %d returned to %s", closed["loan_id"], AUDITOR,
                     closed["tokens"] - closed["returned_tokens"], closed["tokens"], closed["returned_tokens"],
                     closed["lender"])


def configure_logging(run_dir: Path) -> None:
    class Short(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            name = record.name.removeprefix("rebbi.").removeprefix("agent.")
            return f"{self.formatTime(record, '%H:%M:%S')}  {name:<11} {record.getMessage()}"

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for old in [h for h in root.handlers if getattr(h, "_rebbi", False)]:
        root.removeHandler(old)
        old.close()
    for handler in (logging.StreamHandler(sys.stdout), logging.FileHandler(run_dir / "console.log", encoding="utf-8")):
        handler.setFormatter(Short())
        handler._rebbi = True  # so the next run in this process replaces it instead of doubling every line
        root.addHandler(handler)
    for noisy in ("httpx", "uvicorn", "claude_agent_sdk", "mcp"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def detach_logging() -> None:
    """Close this run's log file so nothing after the run lands in its console.log."""
    root = logging.getLogger()
    for handler in [h for h in root.handlers if getattr(h, "_rebbi", False)]:
        root.removeHandler(handler)
        handler.close()


def parse_budgets(pairs: list[str]) -> dict[str, int]:
    return {agent: int(tokens) for agent, tokens in (p.split("=", 1) for p in pairs)}


def start(mode: str, budgets: dict[str, int], upstream: str, auth: str,
          now: Callable[[], datetime] = utcnow) -> Run:
    sc = scenario.load()
    sc = dataclasses.replace(sc, agents=[dataclasses.replace(a, budget_tokens=budgets.get(a.id, a.budget_tokens))
                                         for a in sc.agents])
    local = upstream != UPSTREAM  # the scripted stand-in for the model: tests and rehearsals
    # Read the credentials before isolate_from_host() clears the environment.
    if auth == "api-key":
        api_key = "not-used-by-a-local-upstream" if local else real_api_key(ENV_FILE)
    else:
        direct_env = ({"ANTHROPIC_BASE_URL": upstream, "ANTHROPIC_API_KEY": "local-test"} if local
                      else {"CLAUDE_CODE_OAUTH_TOKEN": oauth_token(ENV_FILE)})
    run_dir = ROOT / "runs" / f"{datetime.now(UTC):%Y%m%d-%H%M%S}-{mode}{'-scripted' if local else ''}"
    run_dir.mkdir(parents=True)
    configure_logging(run_dir)
    isolate_from_host()

    ledger = Ledger(run_dir / "rebbi.db")
    scenario.seed(ledger, sc, now())
    gateway_url = None
    if auth == "api-key":
        port = free_port()
        serve_in_thread(create_gateway(Ledger(run_dir / "rebbi.db"), api_key, upstream=upstream), port)
        gateway_url, direct_env = f"http://127.0.0.1:{port}", {}
    (run_dir / "scenario.json").write_text(json.dumps({"auth": auth, **dataclasses.asdict(sc)}, indent=2),
                                           encoding="utf-8")
    return Run(mode, auth, run_dir, sc, ledger, Broker(ledger, sc.rules, now), gateway_url, direct_env, local)


async def run_fleet(mode: str, budgets: dict[str, int], upstream: str = UPSTREAM,
                    auth: str = "auto") -> dict[str, Any]:
    """One full run; returns what it writes to summary.json."""
    if auth == "auto":
        auth = "api-key" if upstream != UPSTREAM else detect_auth(ENV_FILE)
    try:
        return await _run(start(mode, budgets, upstream, auth))
    finally:
        detach_logging()


async def _run(run: Run) -> dict[str, Any]:
    mode = run.mode
    t0 = time.monotonic()
    budgets_line = ", ".join(f"{a.id} {a.budget_tokens}" for a in run.scenario.agents)
    if run.scripted:
        log.info("REHEARSAL: the model is a scripted stand-in, not Claude. Its replies and its report are "
                 "hard-coded, so this run is not evidence.")
    log.info("run %s, mode %s, budgets enforced by the %s: %s; auditing %s@%s", run.dir.name, mode,
             "harness" if run.harness_meters else "gateway", budgets_line,
             run.scenario.target.repo.rsplit("/", 1)[-1], run.scenario.target.commit[:7])

    try:
        if mode == "rebbi":
            await publish_headroom(run)
        outcome = await audit(run)
    except ApiUnavailable as e:
        log.error("ABORTED: %s. Nothing about Rebbi was tested; fix the API account and run again.", e)
        return {"run": run.dir.name, "mode": mode, "aborted": str(e)}
    if mode == "rebbi":
        close_loans(run, outcome["finished"])

    checks = verify_report((run.dir / "report.md").read_text(encoding="utf-8"),
                           json.loads(DEFAULT_KEY.read_text(encoding="utf-8")))
    verdict = render(checks)
    (run.dir / "verify.txt").write_text(verdict + "\n", encoding="utf-8")
    for line in verdict.splitlines():
        logging.getLogger("rebbi.verifier").info(line)

    problems = run.ledger.check_invariants(run.broker.now())
    for p in problems:
        logging.getLogger("rebbi.ledger").info("FAIL %s", p)
    logging.getLogger("rebbi.ledger").info("invariants %s", "FAIL" if problems else "PASS")

    summary = {
        "run": run.dir.name,
        "mode": mode,
        "auth": run.auth,
        "model": "scripted stand-in" if run.scripted else "claude",
        **outcome,
        "verified": passed(checks),
        "ledger_ok": not problems,
        "loans": run.ledger.loans(),
        "agents": [{**a.to_dict(), "used": run.ledger.used(a.agent_id)} for a in run.ledger.agents()],
        "decisions": run.ledger.decisions(),
        "seconds": round(time.monotonic() - t0),
    }
    (run.dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    log.info("RESULT %s: job %s, verifier %s, ledger %s, auditor-01 used %d tokens, %d loan(s), %ds",
             mode, "finished" if outcome["finished"] else "STOPPED", "PASS" if summary["verified"] else "FAIL",
             "PASS" if not problems else "FAIL", run.ledger.used(AUDITOR), len(summary["loans"]), summary["seconds"])
    return summary


def main() -> None:
    p = argparse.ArgumentParser(prog="rebbi.fleet")
    p.add_argument("--mode", choices=["baseline", "rebbi"], required=True)
    p.add_argument("--budget", action="append", default=[], metavar="AGENT=TOKENS",
                   help="override one agent's budget for this run, e.g. auditor-01=2000000")
    p.add_argument("--auth", choices=("auto",) + AUTH_MODES, default="auto",
                   help="api-key: through the gateway; subscription: your own Claude login (claude setup-token)")
    p.add_argument("--upstream", default=UPSTREAM, help=argparse.SUPPRESS)  # the scripted model, for plumbing tests
    args = p.parse_args()
    summary = asyncio.run(run_fleet(args.mode, parse_budgets(args.budget), args.upstream, args.auth))
    # The baseline is meant to fail verification; the exit code says whether the run itself went as designed.
    if "aborted" in summary:
        sys.exit(2)
    sys.exit(0 if summary["ledger_ok"] else 1)


if __name__ == "__main__":
    main()
