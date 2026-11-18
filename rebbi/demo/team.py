"""One run: a team of five agents climbs the circle-packing hill, window by window.

A window is one round of five turns (Planner, Researcher, Coder, Evaluator, Reviewer). Budgets refill at the
end of each window; what is left expires. A call whose input the agent's balance cannot cover is refused
(an interruption), unless Rebbi lends the difference first.
"""

from __future__ import annotations

import json
import re
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from rebbi.broker import Broker, HandoffRequest, utcnow
from rebbi.demo import hill
from rebbi.demo.backend import Backend, PlanLimit, extract_code, parse_shareable
from rebbi.demo.market import Market, reserve_for
from rebbi.ledger import Ledger
from rebbi.rules import LendingRules

ROLES = ["planner", "researcher", "coder", "evaluator", "reviewer"]
ROLE_TEXT = {
    "planner": "Planner: reads the attempt log and picks the next idea to try.",
    "researcher": "Researcher: reads the current best code and past attempts, writes notes on what to try.",
    "coder": "Coder: writes a new complete solve.py (the largest and most expensive turn).",
    "evaluator": "Evaluator: runs the fixed evaluator and reports the score and the reason.",
    "reviewer": "Reviewer: accepts the candidate as the new best only if it is valid and better.",
}
HAIKU, SONNET = "claude-haiku-5-5", "claude-sonnet-5-5"
SHAREABLE_LINE = "\nEnd your reply with one line: SHAREABLE: <0-100>% (the share of your budget other agents may borrow)."
MAX_WINDOWS = 20
# Protocol 2 (Nov 18, 01:00): a call's whole cost (output included) must fit the agent's balance, after a Rebbi
# loan where allowed; otherwise the call is cut off when the balance runs out and its output is lost. Protocol 1
# checked only a call's input, so an agent could spend twice its budget and the budgets never bound.
PROTOCOL = 2

TASK = """Task: place n = {n} disjoint circles inside the unit square [0,1]x[0,1] to maximize the sum of their radii.
The team's candidate is one file, solve.py, with a constant `N = {n}` and a function `pack()` returning
(centers, radii): centers has shape ({n}, 2), radii shape ({n},). Every circle must lie inside the square and no
two circles may overlap (tolerance 1e-9). Only the Python standard library, numpy{scipy} may be imported. pack() must
finish within 60 seconds; the evaluator sets numpy and random seeds to 0. The evaluator scores the arrays that
pack() returns. Score = sum of radii, or 0 if anything is invalid."""


@dataclass
class RunConfig:
    run_id: str
    scenario: str  # cal, 1, 2, 3, 3-on-B, 3b, 4
    exercise: str  # A or B
    repeat: int
    models: dict[str, str]
    budgets: dict[str, int]  # tokens per agent per window
    T: int
    shareable_pct: dict[str, float] = field(default_factory=dict)
    rebbi: bool = False
    market: bool = False
    max_windows: int = MAX_WINDOWS
    summit: float | None = None  # stop when the best score reaches it
    forbid_scipy: bool = False
    settings: dict[str, Any] = field(default_factory=dict)  # frozen manager output, etc.

    @property
    def n(self) -> int:
        return hill.EXERCISES[self.exercise]


@dataclass
class RunResult:
    windows: list[dict[str, Any]]
    events: list[dict[str, Any]]
    best_score: float
    best_code: str
    ledger_problems: list[str]
    status: str = "complete"


def scrub(text: str) -> str:
    return re.sub(r"sk-ant[\w-]+|Bearer\s+\S+|CLAUDE_CODE_OAUTH_TOKEN=\S+", "[removed]", text)


class Gate:
    """Meters one agent's calls against its ledger balance; borrows from Rebbi first when allowed."""

    def __init__(self, team: "Team", agent: str):
        self.team, self.agent = team, agent

    def before(self, input_tokens: int) -> bool:
        t, a = self.team, self.agent
        balance = t.ledger.balance(a)
        if balance < input_tokens and t.cfg.rebbi:
            balance = t.top_up(a, input_tokens, balance)
        if balance >= input_tokens:
            return True
        st = t.stats[a]
        st["unmet"] += input_tokens - balance
        st["interrupted"] = True
        t.event("interruption", agent=a, needed=input_tokens, balance=balance)
        return False

    def after(self, total_tokens: int, note: str) -> bool:
        """Debit a finished call. False: the call cost more than the balance (after any Rebbi loan), so it is
        treated as cut off when the balance ran out: the balance is spent and the call's output is lost."""
        t, a = self.team, self.agent
        st = t.stats[a]
        if note.endswith("(refused)"):  # refused at the start (before() already counted it); input debited
            t.ledger.record_usage(a, total_tokens, t.now(), note)
            st["used"] += total_tokens
            return False
        balance = t.ledger.balance(a)
        if total_tokens > balance and t.cfg.rebbi:
            balance = t.top_up(a, total_tokens, balance, ask=total_tokens - max(balance, 0))
        if total_tokens <= balance:
            t.ledger.record_usage(a, total_tokens, t.now(), note)
            st["used"] += total_tokens
            return True
        spent = max(balance, 0)
        if spent:
            t.ledger.record_usage(a, spent, t.now(), note + " (cut off: budget ran out)")
        st["used"] += spent
        st["unmet"] += total_tokens - spent
        st["interrupted"] = True
        t.event("interruption", agent=a, needed=total_tokens, balance=balance, cut_off=True)
        return False


class Team:
    def __init__(self, cfg: RunConfig, backend: Backend, run_dir: Path, now=utcnow):
        self.cfg, self.backend, self.dir, self.now = cfg, backend, run_dir, now
        run_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = Ledger(run_dir / "rebbi.db")
        rules = LendingRules(max_loan_tokens=max(cfg.T, 1), min_loan_tokens=1, loan_ttl_s=86400)
        self.broker = Broker(self.ledger, rules, now)
        self.market = Market(cfg.budgets) if cfg.market else None
        self.declared = {r: (50.0 if cfg.market else cfg.shareable_pct.get(r, 0.0)) for r in ROLES}
        for r in ROLES:
            self.ledger.register_agent(r, "demo", cfg.budgets[r], 0, 0, False, now())
        self.events: list[dict[str, Any]] = []
        self.stats: dict[str, dict[str, Any]] = {}
        self.window = 0
        self.best_code = hill.start_solve(cfg.n)
        first = hill.evaluate(self.best_code, cfg.n, cfg.forbid_scipy)
        self.best_score, self.best_packing = first.score, {"centers": first.centers, "radii": first.radii}
        self.log: list[dict[str, Any]] = []
        self.windows: list[dict[str, Any]] = []

    # -- helpers ---------------------------------------------------------------------------------

    def event(self, kind: str, **fields: Any) -> None:
        e = {"at": self.now().isoformat(timespec="seconds"), "window": self.window, "kind": kind, **fields}
        self.events.append(e)
        with open(self.dir / "events.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(e) + "\n")

    def top_up(self, agent: str, needed: int, balance: int, ask: int | None = None) -> int:
        """Ask Rebbi, for an agent whose call its balance cannot cover. Returns the balance afterwards."""
        ask = min(2 * needed - balance if ask is None else ask, self.broker.rules.max_loan_tokens)
        if self.market:
            limit = self.market.borrow_limit(agent, self.declared[agent], self.ledger.agent(agent).borrowed_tokens)
            ask = min(ask, limit)
            if ask < needed - balance:
                self.event("loan", borrower=agent, tokens=0, asked=ask, decision="CANNOT_MOVE",
                           blocker="market: no claim left" if limit else "market: shareable is 0%")
                return balance
        answer = self.broker.post_handoff(agent, HandoffRequest(goal=f"{agent} needs {needed} tokens for a call",
                                                                budget_tokens=ask))
        lend = answer["decision"] == "LEND"
        self.event("loan", borrower=agent, lender=answer.get("from"), tokens=answer.get("tokens", 0), asked=ask,
                   decision=answer["decision"], partial=answer.get("partial", False),
                   limit_reason=answer.get("limit_reason"), loan_id=answer.get("loan_id"))
        if lend:
            st = self.stats
            st[agent]["borrowed"] += answer["tokens"]
            st[answer["from"]]["lent"] += answer["tokens"]
        return self.ledger.balance(agent)

    def settle_loans(self, agent: str) -> None:
        """The borrower's turn is over: unspent borrowed tokens go back to the lender."""
        for loan in self.ledger.loans("active"):
            if loan["borrower"] != agent:
                continue
            closed = self.broker.settle(agent, loan["loan_id"], "done")
            consumed = closed["tokens"] - closed["returned_tokens"]
            if self.market:
                self.market.settle(loan["lender"], agent, consumed)
            self.event("settle", loan_id=loan["loan_id"], borrower=agent, lender=loan["lender"],
                       tokens=closed["tokens"], returned=closed["returned_tokens"])

    def apply_headroom(self, agent: str) -> None:
        if not self.cfg.rebbi:
            return
        reserve = reserve_for(self.cfg.budgets[agent], self.declared[agent])
        self.ledger.set_headroom(agent, reserve, True, self.now())
        self.stats[agent]["reserve"] = reserve

    def attempt_log(self, last: int = 8) -> str:
        if not self.log:
            return "(no attempts yet)"
        return "\n".join(f"window {e['window']}: idea={e['idea'][:160]!r} score={e['score']:.4f} "
                         f"reason={e['reason']} accepted={e['accepted']}" for e in self.log[-last:])

    # -- one window ------------------------------------------------------------------------------

    async def turn(self, agent: str, system: str, prompt: str) -> str:
        if self.cfg.market:
            prompt += SHAREABLE_LINE
        out = await self.backend.turn(agent, self.cfg.models[agent], system, prompt, Gate(self, agent), self.window)
        self.settle_loans(agent)
        with open(self.dir / "transcripts.jsonl", "a", encoding="utf-8") as f:
            for t in out.transcript:
                f.write(json.dumps({**t, "prompt": scrub(prompt)[:6000], "text": scrub(t["text"])}) + "\n")
        if self.cfg.market and not out.stopped and (pct := parse_shareable(out.text)) is not None:
            self.declared[agent] = pct
            self.stats[agent]["shareable_pct"] = pct
            self.apply_headroom(agent)
        return "" if out.stopped else out.text

    async def run_window(self) -> dict[str, Any]:
        w = self.window
        task = TASK.format(n=self.cfg.n, scipy="" if self.cfg.forbid_scipy else ", scipy")
        self.stats = {r: {"budget": self.cfg.budgets[r], "shareable_pct": self.declared[r], "reserve": 0, "used": 0,
                          "lent": 0, "borrowed": 0, "expired": 0, "unmet": 0, "interrupted": False} for r in ROLES}
        for r in ROLES:
            self.apply_headroom(r)
        sys_for = lambda r: f"You are the {ROLE_TEXT[r]} You work in a team of five on this task.\n{task}"  # noqa: E731
        best = f"Current best score: {self.best_score:.4f}.\nCurrent best solve.py:\n```python\n{self.best_code[:12000]}\n```"

        plan = await self.turn("planner", sys_for("planner"),
                               f"Attempt log:\n{self.attempt_log()}\n\nCurrent best score: {self.best_score:.4f}.\n"
                               "Pick the next idea to try, in at most 80 words.")
        notes = await self.turn("researcher", sys_for("researcher"),
                                f"{best}\n\nAttempt log:\n{self.attempt_log()}\n\nPlanner's idea: {plan or '(none)'}\n"
                                "Write notes on how to implement and improve on it, at most 150 words.")
        reply = await self.turn("coder", sys_for("coder"),
                                f"{best}\n\nPlanner's idea: {plan or '(none)'}\nResearcher's notes: {notes or '(none)'}\n"
                                "Write the complete new solve.py in one ```python block, with the line N = "
                                f"{self.cfg.n}.")
        code = extract_code(reply)
        if code is None:
            ev = hill.Evaluation(0.0, False, "no candidate: the coder produced no code block"
                                 if reply else "no candidate: the coder was out of budget")
        else:
            ev = hill.evaluate(code, self.cfg.n, self.cfg.forbid_scipy)
        report = await self.turn("evaluator", sys_for("evaluator"),
                                 f"Evaluator result: score={ev.score:.4f} valid={ev.valid} reason={ev.reason}.\n"
                                 f"Current best: {self.best_score:.4f}. Report both in two sentences.")
        verdict = await self.turn("reviewer", sys_for("reviewer"),
                                  f"Candidate: score={ev.score:.4f}, reason={ev.reason}. Evaluator report: "
                                  f"{report or '(none)'}\nCurrent best: {self.best_score:.4f}. Reply ACCEPT or REJECT "
                                  "with one sentence.")
        accepted = bool(ev.valid and ev.score > self.best_score and report and verdict)
        if accepted:
            self.best_score, self.best_code = ev.score, code
            self.best_packing = {"centers": ev.centers, "radii": ev.radii}
            self.event("acceptance", score=ev.score)
        self.log.append({"window": w, "idea": plan or "(none)", "score": ev.score, "reason": ev.reason,
                         "accepted": accepted})

        # End of the window: close loans, expire what is left, refill for the next one.
        for loan in self.ledger.loans("active"):
            self.broker.settle(loan["borrower"], loan["loan_id"], "done")
        for r in ROLES:
            left = self.ledger.balance(r)
            if left > 0:
                self.ledger.record_usage(r, left, self.now(), "expired at refill")
            elif left < 0:  # a refused call's input is debited and can overdraw; forgive it at the refill
                self.ledger.grant(r, -left, self.now(), "overdraft forgiven at refill")
            self.stats[r]["expired"] = max(left, 0)
            self.stats[r]["overdraft"] = max(-left, 0)
            if self.market:
                self.stats[r]["claim_balance"] = round(self.market.claims[r], 1)
        row = {"window": w, "agents": self.stats,
               "team": {"candidate_score": ev.score, "candidate_reason": ev.reason, "accepted": accepted,
                        "best_score": self.best_score, "best_packing": self.best_packing,
                        "tokens_used": sum(s["used"] for s in self.stats.values())}}
        with open(self.dir / "windows.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        self.windows.append(row)
        return row

    async def run(self) -> RunResult:
        for w in range(1, self.cfg.max_windows + 1):
            self.window = w
            if w > 1:
                for r in ROLES:
                    self.ledger.grant(r, self.cfg.budgets[r], self.now())
            await self.run_window()
            if self.cfg.summit is not None and self.best_score >= self.cfg.summit:
                break
        (self.dir / "solve_best.py").write_text(self.best_code, encoding="utf-8")
        problems = self.ledger.check_invariants(self.now())
        (self.dir / "ledger_check.txt").write_text("PASS\n" if not problems else "FAIL\n" + "\n".join(problems) + "\n",
                                                   encoding="utf-8")
        return RunResult(self.windows, self.events, self.best_score, self.best_code, problems)


def summarize(cfg: RunConfig, res: RunResult, started: datetime, ended: datetime) -> dict[str, Any]:
    """The results.csv row for a finished run."""
    ws = res.windows
    reached = next((w["window"] for w in ws if cfg.summit is not None and w["team"]["best_score"] >= cfg.summit), None)
    loans = [e for e in res.events if e["kind"] == "loan" and e["decision"] == "LEND"]
    return {
        "run_id": cfg.run_id, "scenario": cfg.scenario, "exercise": cfg.exercise, "repeat": cfg.repeat,
        "models": "/".join(sorted(set(cfg.models.values()))), "T": cfg.T, "budgets": json.dumps(cfg.budgets),
        "shareable_pct": json.dumps(cfg.shareable_pct) if cfg.shareable_pct else "",
        "windows_to_summit": reached if reached is not None else "not reached",
        "best_score": round(res.best_score, 6), "tokens_issued": cfg.T * len(ws) if cfg.scenario != "cal"
        else sum(cfg.budgets.values()) * len(ws),
        "tokens_used": sum(a["used"] for w in ws for a in w["agents"].values()),
        "tokens_expired": sum(a["expired"] for w in ws for a in w["agents"].values()),
        "interruptions": sum(1 for e in res.events if e["kind"] == "interruption"),
        "loans_count": len(loans), "tokens_moved": sum(e["tokens"] for e in loans),
        "ledger_check": "PASS" if not res.ledger_problems else "FAIL", "status": res.status,
        "started_at": started.isoformat(timespec="seconds"), "ended_at": ended.isoformat(timespec="seconds"),
    }


def calibration_numbers(windows: list[dict[str, Any]]) -> dict[str, Any]:
    """T = median team tokens per window rounded to 1,000; summit = best score at the end of window 8."""
    per_window = [w["team"]["tokens_used"] for w in windows]
    T = round(statistics.median(per_window) / 1000) * 1000
    at = lambda k: windows[min(k, len(windows)) - 1]["team"]["best_score"]  # noqa: E731
    demand = {r: round(statistics.median(w["agents"][r]["used"] for w in windows)) for r in ROLES}
    return {"T": T, "summit_A": at(8), "score_w2": at(2), "per_role_demand": demand,
            "summit_B": at(8) * (2.937 / 2.635),
            # Protocol 2 summit: 99.5% of the calibration best at window 8 (that best equalled the published record,
            # 2.635983, so a summit at the record itself would measure luck, not budgets).
            "target_A": round(0.995 * at(8), 4), "target_B": round(0.995 * at(8) * (2.937 / 2.635), 4)}


def flat_hill(windows: list[dict[str, Any]]) -> bool:
    """The calibration team's score at the end of window 2 is at least 98% of its score at the end of window 8."""
    n = calibration_numbers(windows)
    return n["summit_A"] > 0 and n["score_w2"] >= 0.98 * n["summit_A"]


_ = PlanLimit
