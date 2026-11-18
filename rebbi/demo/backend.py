"""How an agent turn reaches a model: the real Claude Agent SDK, or a scripted stand-in.

Both call `gate.before(input_tokens)` when a model call starts and `gate.after(total_tokens, note)` when it
ends. The gate (team.Gate) decides whether the agent's balance covers the call and debits the ledger.
"""

from __future__ import annotations

import asyncio
import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from rebbi.gateway import UsageMeter

MAX_CALLS = 6  # model calls per agent turn
EXTERNAL = re.compile(r"usage limit|rate.?limit|\b429\b|overloaded|\b529\b|authenticat|unauthori[sz]ed|\b401\b|"
                      r"invalid (api key|token)|credit balance|hit your limit|quota|out of extra usage", re.I)


class PlanLimit(RuntimeError):
    """The plan or the API refused us (limit, 429, overloaded, authentication): not a Rebbi budget stop."""


def classify_external(text: str | None, status: int | None = None) -> bool:
    """True if an error is the plan or API stopping us, as opposed to anything the experiment causes."""
    if status in (401, 403, 429, 529):
        return True
    return bool(text and EXTERNAL.search(text))


class Gate(Protocol):
    def before(self, input_tokens: int) -> bool: ...  # False: the balance cannot cover this call

    def after(self, total_tokens: int, note: str) -> None: ...


@dataclass
class TurnOutput:
    text: str
    stopped: bool  # the gate refused a call: the agent's budget ran out mid-turn
    calls: int = 0
    transcript: list[dict[str, Any]] = field(default_factory=list)


class Backend(Protocol):
    scripted: bool

    async def turn(self, agent: str, model: str, system: str, prompt: str, gate: Gate | None,
                   window: int) -> TurnOutput: ...


class SdkBackend:
    """Claude Agent SDK in subscription mode: each call is metered from the stream, as in rebbi/fleet.py."""

    scripted = False

    def __init__(self, token: str, config_dir: Path):
        self.token = token
        self.config_dir = config_dir
        config_dir.mkdir(parents=True, exist_ok=True)

    async def turn(self, agent, model, system, prompt, gate, window) -> TurnOutput:
        from claude_agent_sdk import (AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, ResultMessage,
                                      StreamEvent, TextBlock)
        options = ClaudeAgentOptions(
            model=model, system_prompt=system, tools=[], allowed_tools=[], mcp_servers={}, strict_mcp_config=True,
            setting_sources=[], permission_mode="dontAsk", max_turns=MAX_CALLS, cwd=str(self.config_dir),
            include_partial_messages=True,
            env={"CLAUDE_CODE_OAUTH_TOKEN": self.token, "CLAUDE_CONFIG_DIR": str(self.config_dir / agent),
                 "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "DISABLE_AUTOUPDATER": "1"})
        texts: list[str] = []
        meter: UsageMeter | None = None
        stopped, calls, result = False, 0, None
        interrupting: asyncio.Task | None = None
        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)
                async for message in client.receive_response():
                    if isinstance(message, StreamEvent):
                        kind = message.event.get("type")
                        if kind == "message_start":
                            meter = UsageMeter()
                        if meter is not None:
                            meter.observe(message.event)
                        if kind == "message_start" and not stopped and gate and not gate.before(meter.total):
                            stopped = True
                            gate.after(meter.total, f"{meter.model} {meter.breakdown()} (refused)")
                            meter = None
                            interrupting = asyncio.create_task(client.interrupt())
                        if kind == "message_stop" and meter is not None:
                            calls += 1
                            if gate:
                                gate.after(meter.total, f"{meter.model} {meter.breakdown()}")
                            meter = None
                        continue
                    if stopped:
                        continue
                    if isinstance(message, AssistantMessage):
                        texts += [b.text for b in message.content if isinstance(b, TextBlock) and b.text.strip()]
                    elif isinstance(message, ResultMessage):
                        result = message
                if interrupting is not None:
                    await interrupting
        except Exception as e:  # noqa: BLE001
            if classify_external(str(e)):
                raise PlanLimit(str(e)[:300]) from e
            raise
        if result is not None and result.is_error and not stopped:
            detail = f"{result.api_error_status} {(result.result or '')[:200]}"
            if classify_external(result.result, result.api_error_status):
                raise PlanLimit(detail)
            raise RuntimeError(f"{agent} failed: {detail}")
        text = result.result if result is not None and result.result and not stopped else "\n".join(texts)
        return TurnOutput(text or "", stopped, calls, [{"agent": agent, "window": window, "text": text or ""}])


SCRIPTED_SOLVE = '''import numpy as np

N = {n}
TRIALS = {trials}


def pack():
    k = int(np.ceil(np.sqrt(N)))
    g = np.array([[(i % k + 0.5) / k, (i // k + 0.5) / k] for i in range(N)])
    share = 0.7 + 0.29 * min(1.0, TRIALS / 400)
    return g, np.full(N, 0.5 / k * share)
'''


class ScriptedBackend:
    """No model: replies and token counts come from a seeded formula. For the rehearsal and the tests."""

    scripted = True
    BASE = {"planner": 6000, "researcher": 9000, "coder": 22000, "evaluator": 4000, "reviewer": 5000,
            "manager": 3000}

    def __init__(self, seed: int = 0):
        self.seed = seed

    def _jitter(self, agent: str, window: int) -> float:
        return 0.7 + 0.6 * random.Random(f"{self.seed}-{agent}-{window}").random()

    async def turn(self, agent, model, system, prompt, gate, window) -> TurnOutput:
        role = agent.split("-")[0]
        size = int(self.BASE.get(role, 5000) * self._jitter(agent, window) * (1 + window / 20))
        if role == "coder":
            n = re.search(r"^N = (\d+)", prompt, re.M)
            code = SCRIPTED_SOLVE.format(n=int(n.group(1)) if n else 26, trials=40 * (window + 1))
            text = f"```python\n{code}\n```"
        elif role == "manager":
            text = self.manager_reply(prompt)
        else:
            text = f"Scripted {role} note for window {window}. SHAREABLE: {30 + 10 * (window % 4)}%"
        calls, stopped = 0, False
        for _ in range(2):
            if gate and not gate.before(size // 2):
                stopped = True
                gate.after(size // 2, "scripted (refused)")
                break
            if gate:
                gate.after(size // 2, "scripted")
            calls += 1
        return TurnOutput("" if stopped else text, stopped, calls, [{"agent": agent, "window": window, "text": text}])

    @staticmethod
    def manager_reply(prompt: str) -> str:
        m = re.search(r"TOTAL=(\d+)", prompt)
        total = int(m.group(1)) if m else 100000
        w = {"planner": 0.15, "researcher": 0.2, "coder": 0.35, "evaluator": 0.1, "reviewer": 0.2}
        return json.dumps({"budgets": {k: int(total * v) for k, v in w.items()},
                           "shareable_pct": {"planner": 60, "researcher": 40, "coder": 10, "evaluator": 70,
                                             "reviewer": 50}})


def extract_code(text: str) -> str | None:
    """The largest fenced python block in a reply, or None."""
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, re.S)
    return max(blocks, key=len) if blocks else None


def parse_shareable(text: str) -> int | None:
    m = re.search(r"SHAREABLE:\s*(\d{1,3})\s*%", text, re.I)
    return min(100, int(m.group(1))) if m else None


def parse_json(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except ValueError:
        return None
