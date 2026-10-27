"""The demo for the video: the same fleet and budgets, first without Rebbi, then with it.

    python -m rebbi.demo                     # baseline, then Rebbi, then the side-by-side check
    python -m rebbi.demo --auth subscription
    python -m rebbi.demo --rehearsal         # no credentials: the scripted model, labelled on every line

The closing table is the evidence shot: the baseline job stops and fails verification; with Rebbi
the auditor borrows, finishes, passes verification, and no lender drops below its reserve.

A rehearsal runs the same harness, gateway, MCP server, ledger and verifier against
rebbi/scripted_model.py. It gives the video's timing and shot order before a real run exists; its
replies and report are hard-coded, so its footage is never the submission.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rebbi import fleet
from rebbi.gateway import UPSTREAM, serve_in_thread
from rebbi.scripted_model import create_scripted_model

ROOT = Path(__file__).resolve().parent.parent


def banner(text: str) -> None:
    line = "=" * 78
    print(f"\n{line}\n  {text}\n{line}", flush=True)


def checks(run_dir: Path) -> str:
    lines = (run_dir / "verify.txt").read_text(encoding="utf-8").splitlines()[:-1]
    failed = [line.removeprefix("FAIL").strip().split(":")[0] for line in lines if line.startswith("FAIL")]
    return f"first failure: {failed[0]}" if failed else f"all {len(lines)} checks"


def loan_line(s: dict[str, Any]) -> tuple[str, str]:
    if not s["loans"]:
        return "none", "-"
    parts, reserves = [], []
    for loan in s["loans"]:
        parts.append(f"{loan['tokens']} from {loan['lender']}, {loan['returned_tokens']} returned")
        intact = loan["lender_balance_after"] >= loan["lender_reserve"]
        reserves.append(f"{'intact' if intact else 'BROKEN'} ({loan['lender_balance_after']} >= {loan['lender_reserve']})")
    return "; ".join(parts), "; ".join(reserves)


def compare(base: dict[str, Any], rebbi: dict[str, Any]) -> str:
    rows = [("", "baseline: Rebbi off", "Rebbi on")]
    for s in (base, rebbi):
        s["_dir"] = ROOT / "runs" / s["run"]
    rows.append(("model", base["model"], rebbi["model"]))
    rows.append(("job", *("finished" if s["finished"] else f"STOPPED ({s['stopped_by']})" for s in (base, rebbi))))
    rows.append(("verifier", *(f"{'PASS' if s['verified'] else 'FAIL'} ({checks(s['_dir'])})" for s in (base, rebbi))))
    loans = [loan_line(s) for s in (base, rebbi)]
    rows.append(("loan", *(lo for lo, _ in loans)))
    rows.append(("lender reserve", *(res for _, res in loans)))
    rows.append(("ledger invariants", *("PASS" if s["ledger_ok"] else "FAIL" for s in (base, rebbi))))
    used = [next(a["used"] for a in s["agents"] if a["agent_id"] == fleet.AUDITOR) for s in (base, rebbi)]
    rows.append(("auditor-01 tokens", *(f"{u:,}" for u in used)))
    rows.append(("run folder", base["run"], rebbi["run"]))
    width = [max(len(str(r[i])) for r in rows) for i in range(3)]
    return "\n".join("  ".join(str(c).ljust(width[i]) for i, c in enumerate(r)).rstrip() for r in rows)


async def main_async(auth: str, budgets: dict[str, int], rehearsal: bool = False) -> int:
    upstream, tag = UPSTREAM, ""
    if rehearsal:
        port = fleet.free_port()
        serve_in_thread(create_scripted_model(), port)
        upstream, auth, tag = f"http://127.0.0.1:{port}", "api-key", "REHEARSAL, scripted model, not Claude.  "
    banner(f"{tag}1/2  BASELINE: Rebbi off. auditor-01 has only its own budget.")
    base = await fleet.run_fleet("baseline", budgets, upstream, auth)
    if "aborted" in base:
        return 2
    banner(f"{tag}2/2  REBBI ON: same fleet, same budgets. auditor-01 can borrow over MCP.")
    rebbi = await fleet.run_fleet("rebbi", budgets, upstream, auth)
    if "aborted" in rebbi:
        return 2
    table = compare(base, rebbi)
    banner(f"{tag}RESULT: the same job, the same budgets")
    print(table, flush=True)
    kind = "rehearsal" if rehearsal else "demo"
    out = ROOT / "runs" / f"{datetime.now(UTC):%Y%m%d-%H%M%S}-{kind}-comparison.txt"
    out.write_text(table + "\n", encoding="utf-8")
    print(f"\nsaved {out.relative_to(ROOT)}")
    as_designed = not base["verified"] and rebbi["verified"] and base["ledger_ok"] and rebbi["ledger_ok"]
    return 0 if as_designed else 1


def main() -> None:
    p = argparse.ArgumentParser(prog="rebbi.demo")
    p.add_argument("--auth", choices=("auto",) + fleet.AUTH_MODES, default="auto")
    p.add_argument("--budget", action="append", default=[], metavar="AGENT=TOKENS")
    p.add_argument("--rehearsal", action="store_true",
                   help="run against the scripted model: no credentials needed, never evidence")
    args = p.parse_args()
    sys.exit(asyncio.run(main_async(args.auth, fleet.parse_budgets(args.budget), args.rehearsal)))


if __name__ == "__main__":
    main()
