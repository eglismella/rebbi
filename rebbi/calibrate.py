"""Turn a measurement run into stand-in numbers for config/scenario.toml.

    python -m rebbi.fleet --mode rebbi --budget auditor-01=3000000   # measure: a budget too big to run out
    python -m rebbi.calibrate runs/<that run>

It prints what the audit really cost and a [[agents]] / [rules] proposal that makes auditor-01
stall about halfway, analyst-07 able to cover the rest, and writer-03 unable to lend. Pietro owns
the final numbers; this only keeps them consistent with what the model actually spends.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from pathlib import Path

from rebbi import scenario


def round_up(n: float, step: int = 5_000) -> int:
    return int(math.ceil(n / step) * step)


def measure(run_dir: Path) -> dict[str, dict[str, int]]:
    db = sqlite3.connect(run_dir / "rebbi.db")
    out = {}
    for agent_id, calls, total, largest in db.execute(
        "SELECT agent_id, COUNT(*), -SUM(tokens), -MIN(tokens) FROM entries WHERE kind = 'usage' GROUP BY agent_id"
    ):
        out[agent_id] = {"calls": calls, "total": total, "largest": largest}
    db.close()
    return out


def propose(m: dict[str, dict[str, int]], stall_at: float = 0.5) -> str:
    sc = scenario.load()
    need = m["auditor-01"]["total"]
    auditor = round_up(need * stall_at)
    shortfall = need - auditor
    loan_cap = round_up(shortfall * 1.5)  # the agent's own estimate will be rough; leave room
    analyst, writer = sc.agent("analyst-07"), sc.agent("writer-03")
    analyst_own = m.get("analyst-07", {}).get("total", 0)
    writer_own = m.get("writer-03", {}).get("total", 0)
    analyst_budget = round_up(analyst.reserve_tokens + analyst.expected_demand_tokens + analyst_own + loan_cap * 1.2)
    writer_budget = round_up(writer.reserve_tokens + writer.expected_demand_tokens + writer_own, 1_000)
    return f"""# Proposed from {need:,} tokens measured for the full audit ({m['auditor-01']['calls']} calls,
# largest {m['auditor-01']['largest']:,}). auditor-01 runs out about {int(stall_at * 100)}% of the way through.
[rules]
max_loan_tokens = {loan_cap}
min_loan_tokens = {sc.rules.min_loan_tokens}
loan_ttl_s = {sc.rules.loan_ttl_s}

auditor-01:  budget_tokens = {auditor}
analyst-07:  budget_tokens = {analyst_budget}   # reserve {analyst.reserve_tokens} + demand {analyst.expected_demand_tokens} + its own calls {analyst_own} + room for one capped loan
writer-03:   budget_tokens = {writer_budget}   # reserve {writer.reserve_tokens} + demand {writer.expected_demand_tokens} + its own calls {writer_own}: nothing left to lend
"""


def main() -> None:
    p = argparse.ArgumentParser(prog="rebbi.calibrate")
    p.add_argument("run", type=Path)
    p.add_argument("--stall-at", type=float, default=0.5, help="share of the job auditor-01 can do alone")
    args = p.parse_args()
    m = measure(args.run)
    if "auditor-01" not in m:
        sys.exit(f"{args.run} has no usage for auditor-01")
    summary = json.loads((args.run / "summary.json").read_text(encoding="utf-8"))
    if not summary.get("finished"):
        print("warning: the auditor did not finish in this run, so this measures a lower bound\n")
    for agent_id, stats in sorted(m.items()):
        print(f"{agent_id:<11} {stats['calls']:>3} calls, {stats['total']:>9,} tokens, largest call {stats['largest']:,}")
    print()
    print(propose(m, args.stall_at))


if __name__ == "__main__":
    main()
