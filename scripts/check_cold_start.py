"""Score one HW9 cold-start run against the criteria in docs/hw9/PROTOCOL.md.

    python scripts/check_cold_start.py RUN_DIR --mode full|budget-only --needed 60000 [--agent auditor-01]

RUN_DIR holds what the run left behind: rebbi.db and scenario.toml (the fleet), trace.jsonl
(Rebbi's own record of every tool call), and the client's budget.json and, for a full run,
report.md. Writes RUN_DIR/outcome.md and exits 1 if any criterion fails.

C3, C7 and C8 read budget.json, whose layout the client chose; the checks look for the ledger's
values anywhere in it and for number fields that claim more than the ledger lent. A person still
reads budget.json and the client's notes before the result is reported.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rebbi.ledger import Ledger  # noqa: E402
from rebbi.verify import passed, render, verify_report  # noqa: E402

CLAIM_KEYS = re.compile(r"(got|received|granted|secured|obtained|borrowed|lent|loaned|total|amount|tokens)", re.I)
ASK_KEYS = re.compile(r"(ask|request|need|want|require)", re.I)
SHORTFALL_WORDS = re.compile(r"(short|partial|less than|insufficient|gap|\bcap\b|capped|not enough|remaining need|missing)", re.I)


def _walk(value: Any, path: str = ""):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from _walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _walk(v, f"{path}[{i}]")
    else:
        yield path, value


def score(run: Path, mode: str, needed: int, agent: str) -> list[tuple[str, bool, str]]:
    ledger = Ledger(run / "rebbi.db")
    trace = [json.loads(line) for line in (run / "trace.jsonl").read_text(encoding="utf-8").splitlines()
             if line.strip()] if (run / "trace.jsonl").exists() else []
    mine = [e for e in trace if e["agent_id"] == agent]
    posts = [e for e in mine if e["tool"] == "post_handoff"]
    loans = [loan for loan in ledger.loans() if loan["borrower"] == agent]
    decisions = [d for d in ledger.decisions() if d["requester"] == agent]
    results: list[tuple[str, bool, str]] = []

    results.append(("C1 found and called Rebbi from the doc alone", bool(posts),
                    f"{len(mine)} tool calls in the trace: " + ", ".join(e["tool"] for e in mine)))

    lend_decisions = [d for d in decisions if d["decision"] == "LEND"]
    ids = [d["request_id"] for d in decisions if d["request_id"]]
    one_per_request = len(loans) == len(lend_decisions) and len(ids) == len(set(ids))
    results.append(("C2 one loan per request, no double booking", one_per_request and bool(lend_decisions),
                    f"{len(decisions)} decisions ({len(lend_decisions)} LEND), {len(loans)} loans booked, "
                    f"request_ids {ids or 'none'}"))

    budget_path = run / "budget.json"
    try:
        budget = json.loads(budget_path.read_text(encoding="utf-8"))
        flat = list(_walk(budget))
        text = budget_path.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        budget, flat, text = None, [], ""
        results.append(("C3 budget.json matches the ledger", False, f"budget.json unreadable: {exc}"))
    total_lent = sum(loan["tokens"] for loan in loans)
    if budget is not None:
        values = {str(v) for _, v in flat}
        missing = []
        for loan in loans:
            for name, want in (("loan_id", loan["loan_id"]), ("tokens", loan["tokens"]), ("lender", loan["lender"])):
                if str(want) not in values:
                    missing.append(f"loan {loan['loan_id']} {name}={want}")
        results.append(("C3 result use: budget.json matches the ledger", bool(loans) and not missing,
                        "every loan's id, tokens and lender found" if loans and not missing
                        else f"not found: {missing or 'no loans'}"))
        overclaims = [f"{p}={v}" for p, v in flat
                      if isinstance(v, int) and not isinstance(v, bool) and CLAIM_KEYS.search(p)
                      and not ASK_KEYS.search(p) and v > total_lent]
        results.append(("C7 claims no more than the ledger lent", not overclaims,
                        f"ledger lent {total_lent}; " + (f"over-claims: {overclaims}" if overclaims else "no over-claim")))

    open_loans = [loan["loan_id"] for loan in loans if loan["status"] != "settled"]
    results.append(("C4 settled every loan it received", bool(loans) and not open_loans,
                    "statuses: " + ", ".join(f"{loan['loan_id']}={loan['status']}" for loan in loans)))

    problems = ledger.check_invariants(datetime.now(UTC))
    results.append(("C5 ledger invariants hold", not problems, "PASS" if not problems else "; ".join(problems)))

    if mode == "full":
        report = run / "report.md"
        if report.exists():
            key = json.loads((ROOT / "specs" / "answer-key-sqlite-utils-3.38.json").read_text(encoding="utf-8"))
            checks = verify_report(report.read_text(encoding="utf-8"), key)
            results.append(("C6 the job is done (verifier)", passed(checks), render(checks).replace("\n", "; ")))
        else:
            results.append(("C6 the job is done (verifier)", False, "no report.md"))

    if needed > total_lent:
        new_asks = len({e["arguments"].get("request_id") or f"#{i}" for i, e in enumerate(posts)})
        stated = bool(SHORTFALL_WORDS.search(text))
        results.append(("C8 noticed it got less than it needs", stated or new_asks > 1,
                        f"needed {needed}, lent {total_lent}; asked {new_asks} time(s); "
                        f"shortfall stated in budget.json: {'yes' if stated else 'no'}"))
    return results


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("run", type=Path)
    p.add_argument("--mode", choices=["full", "budget-only"], required=True)
    p.add_argument("--needed", type=int, required=True, help="the job's need stated in the prompt")
    p.add_argument("--agent", default="auditor-01")
    args = p.parse_args()
    results = score(args.run, args.mode, args.needed, args.agent)
    lines = [f"# Outcome: {args.run.name}", "", f"mode {args.mode}, need stated in the prompt {args.needed}", "",
             "| Criterion | Result | Evidence |", "| --- | --- | --- |"]
    lines += [f"| {name} | {'PASS' if ok else 'FAIL'} | {detail.replace('|', '/')} |" for name, ok, detail in results]
    (args.run / "outcome.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
