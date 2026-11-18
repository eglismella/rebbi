"""One v2 run: five agents ship a set of exercises through a four-stage pipeline, window by window.

Stages: Researcher writes spec notes -> Coder writes the file (tests run) -> Evaluator writes a test report ->
Reviewer approves it (all tests pass) or rewrites it (tests run again). Work handed to the next role becomes
available at the NEXT window, like a daily hand-off, so the pipeline fills and drains: early windows load the
Researcher, late windows load the Evaluator and Reviewer. That is where fixed budgets leave tokens idle.

Before each item an agent checks that its balance covers the expected cost of the call (its running mean
cost). If not, it asks Rebbi for the difference (scenarios 3, 3b, 4); if it still cannot cover it, it stops
and the rest of its queue waits (an interruption). A call that costs more than the balance is cut off and its
output is lost (protocol 2 of the pilot). Unused tokens expire at the refill.
"""

from __future__ import annotations

import json
import re
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from rebbi.broker import Broker, utcnow
from rebbi.demo.backend import Backend, extract_code, parse_shareable
from rebbi.demo.market import Market, reserve_for
from rebbi.demo.team import Gate, Team as PilotTeam
from rebbi.demo2 import suite
from rebbi.ledger import Ledger
from rebbi.rules import LendingRules

ROLES = ["planner", "researcher", "coder", "evaluator", "reviewer"]
STAGE_ROLE = {"new": "researcher", "spec": "coder", "coded": "evaluator", "reported": "reviewer"}
ROLE_TEXT = {
    "planner": "Planner: once per window, orders the open exercises so the team works on the right ones first.",
    "researcher": "Researcher: reads an exercise's instructions and tests and writes implementation notes.",
    "coder": "Coder: writes the solution file from the stub and the Researcher's notes; the tests then run.",
    "evaluator": "Evaluator: reads each test run and writes a short test report or diagnosis.",
    "reviewer": "Reviewer: approves passing solutions; rewrites failing ones from the diagnosis.",
}
HAIKU = "claude-haiku-5-5"
MAX_WINDOWS = 60
MAX_FIXES = 2  # Reviewer rewrites before an exercise ships with what it passes
MAX_FIXES_REOPENED = 5  # once nothing else is open, partly passing exercises reopen up to this many rewrites
DEFAULT_COST = {("planner", "plan"): 1500, ("researcher", "spec"): 2600, ("coder", "code"): 2200,
                ("evaluator", "report"): 1100, ("reviewer", "approve"): 1000, ("reviewer", "fix"): 2600}
SHAREABLE_LINE = "\nEnd your reply with one line: SHAREABLE: <0-100>% (the share of your budget other agents may borrow)."
PHASES = ["Explore", "Build", "Polish"]


@dataclass
class RunConfig:
    run_id: str
    scenario: str  # cal, 1, 2, 3, 3-on-B, 3b, 4
    exercise: str  # A or B
    repeat: int
    budgets: dict[str, int]
    T: int
    shareable_pct: dict[str, float] = field(default_factory=dict)
    rebbi: bool = False
    market: bool = False
    max_windows: int = MAX_WINDOWS
    summit: float | None = None  # percent of the set's tests passing in shipped exercises
    model: str = HAIKU
    cost_prior: dict[str, int] = field(default_factory=dict)  # "role_kind" -> tokens, from calibration
    settings: dict[str, Any] = field(default_factory=dict)
    replay: bool = False  # test results come from markers (replay backend), no code runs


@dataclass
class Item:
    ex: suite.Exercise
    stage: str = "new"
    ready: int = 1  # first window in which the next role may pick it up
    notes: str = ""
    code: str = ""
    result: suite.TestResult | None = None
    report: str = ""
    fixes: int = 0
    shipped_passed: int = 0  # best result shipped so far (an exercise never loses shipped tests)
    reopened: bool = False


@dataclass
class RunResult:
    windows: list[dict[str, Any]]
    events: list[dict[str, Any]]
    calls: list[dict[str, Any]]
    score: float
    ledger_problems: list[str]
    exhausted: bool = False
    status: str = "complete"


def scrub(text: str) -> str:
    return re.sub(r"sk-ant[\w-]+|Bearer\s+\S+|CLAUDE_CODE_OAUTH_TOKEN=\S+", "[removed]", text)


class MeterGate(Gate):
    """The pilot gate (protocol 2), also recording each call's whole cost."""

    def __init__(self, team: "Team", agent: str):
        super().__init__(team, agent)
        self.totals: list[int] = []

    def after(self, total_tokens: int, note: str) -> bool:
        self.totals.append(total_tokens)
        return super().after(total_tokens, note)


class Team:
    # Borrow the pilot's Rebbi plumbing unchanged: loans, settlement, headroom.
    top_up = PilotTeam.top_up
    settle_loans = PilotTeam.settle_loans
    apply_headroom = PilotTeam.apply_headroom
    event = PilotTeam.event

    def __init__(self, cfg: RunConfig, backend: Backend, run_dir: Path, exercises: list[suite.Exercise], now=utcnow):
        self.cfg, self.backend, self.dir, self.now = cfg, backend, run_dir, now
        run_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = Ledger(run_dir / "rebbi.db")
        rules = LendingRules(max_loan_tokens=max(cfg.T, 1), min_loan_tokens=1, loan_ttl_s=86400)
        self.broker = Broker(self.ledger, rules, now)
        self.market = Market(cfg.budgets) if cfg.market else None
        self.declared = {r: (50.0 if cfg.market else cfg.shareable_pct.get(r, 0.0)) for r in ROLES}
        for r in ROLES:
            self.ledger.register_agent(r, "demo2", cfg.budgets[r], 0, 0, False, now())
        self.exercises = exercises
        self.items = [Item(e) for e in exercises]
        self.priority = [e.slug for e in exercises]
        self.events: list[dict[str, Any]] = []
        self.calls: list[dict[str, Any]] = []
        self.observed: dict[tuple[str, str], list[int]] = {}
        self.stats: dict[str, dict[str, Any]] = {}
        self.window = 0
        self.windows: list[dict[str, Any]] = []

    # -- costs ------------------------------------------------------------------------------------

    def estimate(self, role: str, kind: str) -> int:
        seen = self.observed.get((role, kind), [])
        if len(seen) >= 2:
            return int(statistics.mean(seen))
        return int(self.cfg.cost_prior.get(f"{role}_{kind}", DEFAULT_COST[(role, kind)]))

    def afford(self, role: str, need: int) -> bool:
        balance = self.ledger.balance(role)
        if balance >= need:
            return True
        if self.cfg.rebbi:
            before = len(self.events)
            balance = self.top_up(role, need, balance, ask=need - max(balance, 0))
            for e in self.events[before:]:
                if e["kind"] == "loan" and e.get("decision") != "LEND":
                    self.stats[role]["denied"] = e.get("blocker") or e.get("limit_reason") or "pool empty"
        return balance >= need

    # -- one call -----------------------------------------------------------------------------------

    async def call(self, role: str, kind: str, slug: str, system: str, prompt: str) -> str | None:
        """One model call for one item. None: refused or cut off (the output is lost)."""
        if self.cfg.market:
            prompt += SHAREABLE_LINE
        gate = MeterGate(self, role)
        out = await self.backend.turn(role, self.cfg.model, system, prompt, gate, self.window)
        total = sum(gate.totals)
        self.calls.append({"window": self.window, "role": role, "kind": kind, "slug": slug, "total": total,
                           "stopped": out.stopped})
        with open(self.dir / "calls.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({**self.calls[-1], "prompt": scrub(prompt)[:4000], "text": scrub(out.text)[:4000]}) + "\n")
        if out.stopped:
            return None
        self.observed.setdefault((role, kind), []).append(total)
        if self.cfg.market and (pct := parse_shareable(out.text)) is not None:
            self.declared[role] = pct
            self.stats[role]["shareable_pct"] = pct
            self.apply_headroom(role)
        return out.text

    def system(self, role: str) -> str:
        return (f"You are the {ROLE_TEXT[role]} You work in a team of five AI agents that ships a set of Python "
                "exercises; each counts once its tests pass. Be brief: every token comes from your budget.")

    # -- the four stages ---------------------------------------------------------------------------------

    async def do_item(self, role: str, it: Item) -> bool:
        """Run one item through this role's stage. False: the call was refused or cut off."""
        ex, w = it.ex, self.window
        if role == "researcher":
            text = await self.call(role, "spec", ex.slug, self.system(role),
                                   f"Exercise `{ex.slug}`.\nInstructions:\n{ex.instructions[:suite.DOCS_CHARS]}\n\n"
                                   f"Tests (excerpt):\n```python\n{ex.tests[:suite.TESTS_CHARS]}\n```\n"
                                   f"Stub file `{ex.solution_file}`:\n```python\n{ex.stub[:1500]}\n```\n"
                                   "Write implementation notes for the Coder, who will NOT see the instructions or the "
                                   "tests: exact names and signatures, required behaviour, edge cases, and the exact "
                                   "error types and messages the tests expect. At most 220 words.")
            if text is None:
                return False
            it.notes, it.stage = text, "spec"
        elif role == "coder":
            text = await self.call(role, "code", ex.slug, self.system(role),
                                   f"Exercise `{ex.slug}`. Stub file `{ex.solution_file}`:\n```python\n{ex.stub[:1500]}\n```\n"
                                   f"Researcher's notes:\n{it.notes or '(none)'}\n\nWrite the complete file "
                                   f"`{ex.solution_file}` in one ```python block. Standard library only.")
            if text is None:
                return False
            it.code = extract_code(text) or ex.stub
            it.result = suite.run_tests(ex, it.code, self.cfg.replay)
            it.stage = "coded"
            self.event("tests", slug=ex.slug, by="coder", passed=it.result.passed, total=it.result.total)
        elif role == "evaluator":
            res = it.result or suite.TestResult(0, ex.ntests)
            if res.all_pass:
                prompt = (f"Exercise `{ex.slug}`: all {res.total} tests pass. Confirm in one sentence for the Reviewer "
                          "what the code covers.")
            else:
                prompt = (f"Exercise `{ex.slug}`: {res.passed}/{res.total} tests pass.\nFailures (excerpt):\n"
                          f"{suite.failure_excerpt(res)}\n\nCode:\n```python\n{it.code[:5000]}\n```\n"
                          "Write a diagnosis for the Reviewer: what is wrong and how to fix it. At most 120 words.")
            text = await self.call(role, "report", ex.slug, self.system(role), prompt)
            if text is None:
                return False
            it.report, it.stage = text, "reported"
        elif role == "reviewer":
            res = it.result or suite.TestResult(0, ex.ntests)
            if res.all_pass:
                text = await self.call(role, "approve", ex.slug, self.system(role),
                                       f"Exercise `{ex.slug}` passes all {res.total} tests. Evaluator: {it.report[:600]}\n"
                                       f"Code:\n```python\n{it.code[:4000]}\n```\nReply APPROVE and one sentence.")
                if text is None:
                    return False
                self.ship(it, res.passed)
            else:
                text = await self.call(role, "fix", ex.slug, self.system(role),
                                       f"Exercise `{ex.slug}`: {res.passed}/{res.total} tests pass.\nEvaluator's "
                                       f"diagnosis:\n{it.report[:1200]}\n\nFailing tests:\n```python\n"
                                       f"{ex.test_source(res.failing)}\n```\nCurrent `{ex.solution_file}`:\n```python\n"
                                       f"{it.code[:5000]}\n```\nWrite the complete corrected file in one ```python block.")
                if text is None:
                    return False
                code = extract_code(text)
                if code:
                    new = suite.run_tests(ex, code, self.cfg.replay)
                    if new.passed >= res.passed:
                        it.code, it.result = code, new
                it.fixes += 1
                self.event("tests", slug=ex.slug, by="reviewer", passed=it.result.passed, total=it.result.total)
                if it.result.all_pass or it.fixes >= self.fix_limit(it):
                    self.ship(it, it.result.passed)
                else:
                    it.stage = "coded"
        it.ready = w + 1
        return True

    def fix_limit(self, it: Item) -> int:
        return MAX_FIXES_REOPENED if it.reopened else MAX_FIXES

    def ship(self, it: Item, passed: int) -> None:
        if passed > it.shipped_passed:
            it.shipped_passed = passed
        it.stage = "shipped"
        self.event("shipped", slug=it.ex.slug, passed=it.shipped_passed, total=it.ex.ntests)

    def reopen_if_idle(self) -> None:
        """Nothing else open: partly passing shipped exercises go back to the Evaluator for more rewrites."""
        if any(it.stage != "shipped" for it in self.items):
            return
        for it in self.items:
            if it.shipped_passed < it.ex.ntests and it.fixes < MAX_FIXES_REOPENED:
                it.stage, it.ready, it.reopened = "coded", self.window, True
                self.event("reopened", slug=it.ex.slug, fixes=it.fixes)

    # -- the window -----------------------------------------------------------------------------------

    def score(self) -> float:
        return suite.score({it.ex.slug: it.shipped_passed for it in self.items}, self.exercises)

    def phase(self) -> int:
        stages = [it.stage for it in self.items]
        new = stages.count("new")
        if new >= len(stages) / 3:
            return 0
        if new or stages.count("spec"):
            return 1
        return 2

    def queue(self, role: str) -> list[Item]:
        rank = {s: i for i, s in enumerate(self.priority)}
        q = [it for it in self.items if STAGE_ROLE.get(it.stage) == role and it.ready <= self.window]
        return sorted(q, key=lambda it: rank.get(it.ex.slug, 10_000))

    async def plan(self) -> None:
        open_items = [it for it in self.items if it.stage != "shipped"]
        if not open_items:
            return
        st = self.stats["planner"]
        st["queue"] = 1
        need = self.estimate("planner", "plan")
        if not self.afford("planner", need):
            st["interrupted"], st["unmet"] = True, st["unmet"] + need
            self.event("blocked", agent="planner", needed=need, balance=self.ledger.balance("planner"))
            return
        counts = {s: sum(1 for it in self.items if it.stage == s) for s in ("new", "spec", "coded", "reported", "shipped")}
        board = "\n".join(f"- {it.ex.slug}: {it.stage}, difficulty {it.ex.difficulty}"
                          + (f", tests {it.result.passed}/{it.result.total}" if it.result else "")
                          for it in open_items[:40])
        budgets = {r: self.cfg.budgets[r] for r in ROLES}
        text = await self.call("planner", "plan", "-", self.system("planner"),
                               f"Window {self.window}. Board: {json.dumps(counts)}.\nOpen exercises:\n{board}\n"
                               f"Budgets per window: {json.dumps(budgets)}.\nReply with a JSON list of up to 30 exercise "
                               "names in the order the team should work on them (most valuable first).")
        if text is None:
            st["interrupted"], st["cut_off"] = True, True
            return
        st["done"] = 1
        m = re.search(r"\[.*?\]", text, re.S)
        try:
            order = [s for s in json.loads(m.group(0)) if isinstance(s, str)] if m else []
        except ValueError:
            order = []
        known = {it.ex.slug for it in self.items}
        order = [s for s in order if s in known]
        self.priority = order + [s for s in self.priority if s not in order]

    async def work(self, role: str) -> None:
        st = self.stats[role]
        q = self.queue(role)
        st["queue"] = len(q)
        for i, it in enumerate(q):
            kind = {"researcher": "spec", "coder": "code", "evaluator": "report"}.get(role)
            if role == "reviewer":
                kind = "approve" if (it.result and it.result.all_pass) else "fix"
            need = self.estimate(role, kind)
            if not self.afford(role, need):
                left = q[i:]
                st["interrupted"] = True
                st["unmet"] += sum(self.estimate(role, self.kind_for(role, x)) for x in left)
                st["left"] = len(left)
                self.event("blocked", agent=role, needed=need, balance=self.ledger.balance(role), waiting=len(left))
                break
            ok = await self.do_item(role, it)
            if not ok:
                st["interrupted"], st["cut_off"] = True, True
                st["left"] = len(q) - i
                st["unmet"] += sum(self.estimate(role, self.kind_for(role, x)) for x in q[i + 1:])
                break
            st["done"] += 1
        self.settle_loans(role)

    @staticmethod
    def kind_for(role: str, it: Item) -> str:
        if role == "reviewer":
            return "approve" if (it.result and it.result.all_pass) else "fix"
        return {"researcher": "spec", "coder": "code", "evaluator": "report", "planner": "plan"}[role]

    async def run_window(self) -> dict[str, Any]:
        w = self.window
        self.stats = {r: {"budget": self.cfg.budgets[r], "shareable_pct": self.declared[r], "reserve": 0, "used": 0,
                          "lent": 0, "borrowed": 0, "expired": 0, "unmet": 0, "interrupted": False, "cut_off": False,
                          "denied": None, "queue": 0, "done": 0, "left": 0} for r in ROLES}
        for r in ROLES:
            self.apply_headroom(r)
        self.reopen_if_idle()
        phase = self.phase()
        n_events = len(self.events)
        await self.plan()
        self.settle_loans("planner")
        for role in ROLES[1:]:
            await self.work(role)
        for loan in self.ledger.loans("active"):
            self.broker.settle(loan["borrower"], loan["loan_id"], "done")
        for r in ROLES:
            left = self.ledger.balance(r)
            if left > 0:
                self.ledger.record_usage(r, left, self.now(), "expired at refill")
            elif left < 0:
                self.ledger.grant(r, -left, self.now(), "overdraft forgiven at refill")
            self.stats[r]["expired"] = max(left, 0)
            self.stats[r]["overdraft"] = max(-left, 0)
            if self.market:
                self.stats[r]["claim_balance"] = round(self.market.claims[r], 1)
        loans = [{"from": e.get("lender"), "to": e["borrower"], "tokens": e.get("tokens", 0)}
                 for e in self.events[n_events:] if e["kind"] == "loan" and e.get("decision") == "LEND"]
        stages = {s: sum(1 for it in self.items if it.stage == s) for s in ("new", "spec", "coded", "reported", "shipped")}
        row = {"window": w, "agents": self.stats,
               "team": {"score": round(self.score(), 3), "phase": phase, "stages": stages, "loans": loans,
                        "tokens_used": sum(s["used"] for s in self.stats.values())}}
        with open(self.dir / "windows.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        self.windows.append(row)
        return row

    def finished(self) -> bool:
        if self.cfg.summit is not None and self.score() >= self.cfg.summit:
            return True
        exhausted = all(it.stage == "shipped" and (it.shipped_passed >= it.ex.ntests or it.fixes >= MAX_FIXES_REOPENED)
                        for it in self.items)
        return exhausted

    async def run(self) -> RunResult:
        for w in range(1, self.cfg.max_windows + 1):
            self.window = w
            if w > 1:
                for r in ROLES:
                    self.ledger.grant(r, self.cfg.budgets[r], self.now())
            await self.run_window()
            if self.finished():
                break
        problems = self.ledger.check_invariants(self.now())
        (self.dir / "ledger_check.txt").write_text("PASS\n" if not problems else "FAIL\n" + "\n".join(problems) + "\n",
                                                   encoding="utf-8")
        exhausted = self.cfg.summit is not None and self.score() < self.cfg.summit and self.finished()
        return RunResult(self.windows, self.events, self.calls, self.score(), problems, exhausted)


def summarize(cfg: RunConfig, res: RunResult, started: datetime, ended: datetime) -> dict[str, Any]:
    ws = res.windows
    reached = next((w["window"] for w in ws if cfg.summit is not None and w["team"]["score"] >= cfg.summit), None)
    loans = [e for e in res.events if e["kind"] == "loan" and e.get("decision") == "LEND"]
    agents = [a for w in ws for a in w["agents"].values()]
    return {
        "run_id": cfg.run_id, "scenario": cfg.scenario, "exercise": cfg.exercise, "repeat": cfg.repeat,
        "model": cfg.model, "T": cfg.T, "budgets": json.dumps(cfg.budgets),
        "shareable_pct": json.dumps(cfg.shareable_pct) if cfg.shareable_pct else "",
        "summit": cfg.summit, "windows": len(ws),
        "windows_to_summit": reached if reached is not None else ("exhausted" if res.exhausted else "not reached"),
        "final_score": round(res.score, 3),
        "tokens_issued": sum(cfg.budgets.values()) * len(ws),
        "tokens_used": sum(a["used"] for a in agents),
        "tokens_expired": sum(a["expired"] for a in agents),
        "interruptions": sum(1 for a in agents if a["interrupted"]),
        "cut_offs": sum(1 for a in agents if a["cut_off"]),
        "loans_count": len(loans), "tokens_moved": sum(e.get("tokens", 0) for e in loans),
        "ledger_check": "PASS" if not res.ledger_problems else "FAIL", "status": res.status,
        "started_at": started.isoformat(timespec="seconds"), "ended_at": ended.isoformat(timespec="seconds"),
        "wall_seconds": round((ended - started).total_seconds()),
    }
