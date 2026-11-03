"""Does the hint wording decide whether the auditor borrows before it starts?

    python scripts/wording_check.py 5

Runs the rebbi arm on sqlite-utils-3.38 N times with the HW6 wording ("on this commit") and N times
with the current wording, alternating, and prints whether each run's first auditor action was post_handoff.
"""

import asyncio
import json
import sys

from rebbi import fleet

OLD = " Past runs of dep-audit-v1 on this commit used up to {expected:,} tokens."
NEW = fleet.COST_HINT


async def main(n: int) -> None:
    results = []
    for i in range(n):
        for name, hint in (("old", OLD), ("new", NEW)):
            fleet.COST_HINT = hint
            s = await fleet.run_fleet("rebbi", {}, target="sqlite-utils-3.38")
            first = next((d["at"] for d in s["decisions"]), None)
            results.append({"wording": name, "run": s["run"], "borrowed": bool(s["loans"]), "verified": s["verified"],
                            "first_decision_at": first})
            print("WORDING", json.dumps(results[-1]), flush=True)
    for name in ("old", "new"):
        rs = [r for r in results if r["wording"] == name]
        print(f"SUMMARY {name}: borrowed {sum(r['borrowed'] for r in rs)}/{len(rs)}, "
              f"verified {sum(r['verified'] for r in rs)}/{len(rs)}")


asyncio.run(main(int(sys.argv[1])))
