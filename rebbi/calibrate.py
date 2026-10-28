"""Turn a measurement run into stand-in numbers for config/scenario.toml.

    python -m rebbi.fleet --mode rebbi --budget auditor-01=3000000   # measure: a budget too big to run out
    python -m rebbi.calibrate runs/<that run>

It prints what the audit really cost, call by call, and a proposal under which auditor-01 can afford
the one call in which it asks Rebbi for the difference, but not a second call, so without Rebbi it is
refused before it can write its report; analyst-07 can cover the rest and writer-03 cannot lend.
Pietro owns the final numbers; this only keeps them consistent with what the model actually spends.

Why the budget is sized to the first call rather than to a share of the job: a real audit is two or
three large calls, because each call re-sends the conversation, and a call goes ahead only if the
balance covers its input. Whatever the auditor does in its second call, borrowing or writing the whole
report, that call re-sends the first, so only a budget below two calls stops the job without Rebbi.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from pathlib import Path

from rebbi import scenario

AUDITOR = "auditor-01"
# The rebbi tools and instructions make auditor-01's first call this much larger than in the baseline.
REBBI_OVERHEAD = 1_200


def round_up(n: float, step: int = 5_000) -> int:
    return int(math.ceil(n / step) * step)


def measure(run_dir: Path) -> dict[str, list[int]]:
    """Each agent's model calls, in order, in tokens."""
    db = sqlite3.connect(run_dir / "rebbi.db")
    out: dict[str, list[int]] = {}
    for agent_id, tokens in db.execute("SELECT agent_id, -tokens FROM entries WHERE kind = 'usage' ORDER BY entry_id"):
        out.setdefault(agent_id, []).append(tokens)
    db.close()
    return out


def propose(m: dict[str, list[int]]) -> str:
    sc = scenario.load()
    calls = m[AUDITOR]
    first, total = calls[0], sum(calls)
    # Enough for the call it asks in; under two of the baseline's (smaller) first calls.
    floor, ceiling = first, 2 * (first - REBBI_OVERHEAD)
    auditor = int(round((floor + ceiling) / 2, -3))
    need = total - auditor + first  # the rest of the job, plus the call that asks
    loan_cap = round_up(need * 1.5)  # the agent's own estimate will be rough; leave room
    analyst, writer = sc.agent("analyst-07"), sc.agent("writer-03")
    analyst_own, writer_own = sum(m.get("analyst-07", [])), sum(m.get("writer-03", []))
    analyst_budget = round_up(analyst.reserve_tokens + analyst.expected_demand_tokens + analyst_own + loan_cap * 1.2)
    # Exactly its reserve plus declared demand: nothing to lend, even before its own calls.
    writer_budget = writer.reserve_tokens + writer.expected_demand_tokens
    return f"""# Proposed from {total:,} tokens measured for the full audit, {len(calls)} calls: {', '.join(f'{c:,}' for c in calls)}.
# auditor-01's budget sits between its first call with Rebbi ({floor:,}) and two baseline first calls (~{ceiling:,}).
[rules]
max_loan_tokens = {loan_cap}
min_loan_tokens = {sc.rules.min_loan_tokens}
loan_ttl_s = {sc.rules.loan_ttl_s}

[target]
expected_tokens = {round_up(total, 1_000)}

auditor-01:  budget_tokens = {auditor}
analyst-07:  budget_tokens = {analyst_budget}   # reserve {analyst.reserve_tokens} + demand {analyst.expected_demand_tokens} + its own calls {analyst_own} + room for one capped loan
writer-03:   budget_tokens = {writer_budget}   # reserve {writer.reserve_tokens} + demand {writer.expected_demand_tokens}: nothing left to lend (its own calls took {writer_own})
"""


def main() -> None:
    p = argparse.ArgumentParser(prog="rebbi.calibrate")
    p.add_argument("run", type=Path)
    args = p.parse_args()
    m = measure(args.run)
    if AUDITOR not in m:
        sys.exit(f"{args.run} has no usage for {AUDITOR}")
    summary = json.loads((args.run / "summary.json").read_text(encoding="utf-8"))
    if not summary.get("finished"):
        print("warning: the auditor did not finish in this run, so this measures a lower bound\n")
    for agent_id, calls in sorted(m.items()):
        print(f"{agent_id:<11} {len(calls):>3} calls, {sum(calls):>9,} tokens, largest call {max(calls):,}")
    print()
    print(propose(m))


if __name__ == "__main__":
    main()
