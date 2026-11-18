"""Stand-ins for the model in v2: a scripted backend (rehearsal: real tests on the reference solutions) and a
replay backend (the gate: costs and test results resampled from the calibration runs, no code runs)."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any

from rebbi.demo.backend import TurnOutput
from rebbi.demo2 import suite

SLUG = re.compile(r"Exercise `([\w-]+)`")


async def _meter(gate, total: int, note: str) -> bool:
    """Run one metered call through the gate. False: refused or cut off."""
    if gate is None:
        return True
    inp = int(total * 0.75)
    if not gate.before(inp):
        gate.after(inp, f"{note} (refused)")
        return False
    return gate.after(total, note) is not False


class ScriptedBackend:
    """No model. Coder and Reviewer return the reference solution (one in five exercises first gets the stub,
    so the fix path runs). For the rehearsal and the preflight; zero plan usage."""

    scripted = True
    SIZE = {"planner": 1200, "researcher": 2400, "coder": 2000, "evaluator": 900, "reviewer": 1500, "manager": 1500}

    def __init__(self, seed: int = 0, reference: Path = suite.EXERCISES / "_reference"):
        self.seed, self.reference = seed, reference

    async def turn(self, agent, model, system, prompt, gate, window) -> TurnOutput:
        role = agent.split("-")[0]
        m = SLUG.search(prompt)
        slug = m.group(1) if m else "-"
        rnd = random.Random(f"{self.seed}-{agent}-{window}-{slug}-{len(prompt)}")
        size = int(self.SIZE.get(role, 1500) * (0.7 + 0.6 * rnd.random()))
        if role == "manager":
            text = manager_reply(prompt)
        elif role == "planner":
            text = json.dumps(re.findall(r"^- ([\w-]+):", prompt, re.M)[::-1][:30])
        elif role in ("coder", "reviewer") and "```python block" in prompt:
            ref = self.reference / f"{slug}.py"
            stub_first = role == "coder" and int.from_bytes(slug.encode()[:2], "big") % 5 == 0
            body = ref.read_text(encoding="utf-8") if ref.exists() and not stub_first else "# stub\n"
            text = f"```python\n{body}\n```"
        else:
            text = f"Scripted {role} note."
        text += f"\nSHAREABLE: {30 + 10 * (window % 4)}%"
        ok = await _meter(gate, size, "scripted")
        return TurnOutput(text if ok else "", not ok, 1, [{"agent": agent, "window": window, "text": text}])


class ReplayBackend:
    """Costs drawn from the calibration calls of the same role and kind; test results replayed per exercise."""

    scripted = True

    def __init__(self, calls: list[dict[str, Any]], tests: list[dict[str, Any]], seed: int = 0):
        self.rnd = random.Random(seed)
        self.pool: dict[str, list[int]] = {}
        for c in calls:
            if not c.get("stopped") and c.get("total"):
                self.pool.setdefault(f"{c['role']}:{c['kind']}", []).append(int(c["total"]))
        self.first: dict[str, tuple[int, int]] = {}
        self.fixes: dict[str, list[tuple[int, int]]] = {}
        for t in tests:
            if t.get("by") == "coder" and t["slug"] not in self.first:
                self.first[t["slug"]] = (t["passed"], t["total"])
            elif t.get("by") == "reviewer":
                self.fixes.setdefault(t["slug"], []).append((t["passed"], t["total"]))
        rates = [p / n for p, n in self.first.values() if n]
        self.first_pass_share = sum(1 for r in rates if r >= 1) / len(rates) if rates else 0.7
        self.used_fixes: dict[str, int] = {}
        self.last: dict[str, int] = {}

    def cost(self, key: str) -> int:
        pool = self.pool.get(key)
        if not pool:
            role = key.split(":")[0]
            pool = [v for k, vs in self.pool.items() if k.startswith(role + ":") for v in vs] or [1500]
        return self.rnd.choice(pool)

    async def turn(self, agent, model, system, prompt, gate, window) -> TurnOutput:
        role = agent.split("-")[0]
        m = SLUG.search(prompt)
        slug = m.group(1) if m else "-"
        mn = re.search(r"(\d+)/(\d+) tests pass", prompt)
        n = int(mn.group(2)) if mn else None
        if role == "planner":
            kind, text = "plan", "[]"
        elif role == "researcher":
            kind, text = "spec", "notes"
        elif role == "coder":
            kind = "code"
            p, t = self.first.get(slug, (None, None))
            if p is None:
                t = 10
                p = t if self.rnd.random() < self.first_pass_share else int(t * self.rnd.random())
            self.last[slug] = p
            text = f"```python\n# replay-result: {p}/{t}\n```"
        elif role == "evaluator":
            kind, text = "report", "report"
        else:
            if "```python block" in prompt:
                kind = "fix"
                k = self.used_fixes.get(slug, 0)
                seq = self.fixes.get(slug, [])
                if k < len(seq):
                    p, t = seq[k]
                else:
                    t = n or 10
                    prev = self.last.get(slug, 0)
                    p = t if self.rnd.random() < 0.5 else prev
                self.used_fixes[slug] = k + 1
                self.last[slug] = max(self.last.get(slug, 0), p)
                text = f"```python\n# replay-result: {p}/{t}\n```"
            else:
                kind, text = "approve", "APPROVE"
        text += f"\nSHAREABLE: {self.rnd.choice([10, 20, 30, 40, 50])}%"
        ok = await _meter(gate, self.cost(f"{role}:{kind}"), "replay")
        return TurnOutput(text if ok else "", not ok, 1, [{"agent": agent, "window": window, "text": ""}])


def manager_reply(prompt: str) -> str:
    w = {"planner": 10, "researcher": 25, "coder": 30, "evaluator": 15, "reviewer": 20}
    return json.dumps({"budget_pct": w, "shareable_pct": {"planner": 50, "researcher": 30, "coder": 10,
                                                          "evaluator": 40, "reviewer": 30}})
