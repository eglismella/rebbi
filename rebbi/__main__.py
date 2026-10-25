"""Operator commands for the demo.

    python -m rebbi seed --reset     # fresh ledger from config/scenario.toml
    python -m rebbi status           # agents, loans and broker decisions
    python -m rebbi check            # ledger invariants; exit 1 if any is broken
    python -m rebbi fetch-target     # clone the audit repo at its pinned commit
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from rebbi import rules as lending
from rebbi import scenario
from rebbi.broker import utcnow
from rebbi.ledger import Ledger


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="rebbi")
    p.add_argument("--db", default="rebbi.db")
    p.add_argument("--scenario", default=str(scenario.DEFAULT_SCENARIO))
    sub = p.add_subparsers(dest="cmd", required=True)
    seed = sub.add_parser("seed", help="register the scenario's agents and grant their budgets")
    seed.add_argument("--reset", action="store_true", help="delete the existing ledger first")
    sub.add_parser("status", help="show agents, loans and decisions")
    sub.add_parser("check", help="check the ledger invariants")
    sub.add_parser("fetch-target", help="clone the audit repo at the commit pinned in the scenario")
    args = p.parse_args(argv)

    if args.cmd == "fetch-target":
        target = scenario.load(args.scenario).target
        dest = scenario.DEFAULT_SCENARIO.parent.parent / target.local_path
        if not dest.exists():
            dest.mkdir(parents=True)
            git = lambda *a: subprocess.run(["git", "-C", str(dest), *a], check=True)  # noqa: E731
            git("init", "-q")
            git("fetch", "-q", "--depth", "1", target.repo, target.commit)
            git("checkout", "-q", "FETCH_HEAD")
        head = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
        if head != target.commit:
            print(f"{dest} is at {head}, not the pinned {target.commit}")
            return 1
        print(f"{dest} is at the pinned commit {head}")
        return 0

    if args.cmd == "seed":
        if args.reset:
            for suffix in ("", "-wal", "-shm"):
                Path(args.db + suffix).unlink(missing_ok=True)
        sc = scenario.load(args.scenario)
        scenario.seed(Ledger(args.db), sc, utcnow())
        print(f"seeded {len(sc.agents)} agents into {args.db}")
        return 0

    ledger = Ledger(args.db)
    if args.cmd == "status":
        print(f"{'agent':<12} {'balance':>9} {'reserve':>9} {'demand':>9} {'lendable':>9}  lends")
        for a in ledger.agents():
            print(f"{a.agent_id:<12} {a.balance:>9} {a.reserve_tokens:>9} {a.expected_demand_tokens:>9} "
                  f"{lending.lendable(a):>9}  {'yes' if a.will_lend else 'no'}")
        for loan in ledger.loans():
            print(f"loan {loan['loan_id']}: {loan['lender']} -> {loan['borrower']} {loan['tokens']} tokens, "
                  f"{loan['status']}, returned {loan['returned_tokens']}")
        for d in ledger.decisions():
            r = d["response"]
            print(f"decision {d['decision_id']} at {d['at']}: {d['requester']} asked {r['requested']} -> "
                  f"{d['decision']} {r.get('tokens', '')} {r.get('from', r.get('blocker', ''))}")
        return 0

    problems = ledger.check_invariants(utcnow())
    for problem in problems:
        print("FAIL", problem)
    print("ledger invariants: " + ("FAIL" if problems else "PASS"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
