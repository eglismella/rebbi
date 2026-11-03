"""The HW7 benchmark: the cases in config/bench.toml, under each arm, several times.

    python -m rebbi.bench --label main                    # every case, every arm, 3 runs each
    python -m rebbi.bench --label stress-hint --cases sqlite-utils-3.38,csvs-to-sqlite-1.3.1 \\
        --arms upfront,rebbi --hint-tokens 15000          # one stress setting on the tuning cases
    python -m rebbi.bench --label stress-scarce --budget analyst-07=120000 ...   # a lender with little to spare
    python -m rebbi.bench --resume runs/bench/<folder>    # finish a benchmark that stopped
    python -m rebbi.bench --rehearsal --repeats 1         # the scripted model: plumbing only, never evidence

Arms (fleet.MODES): baseline, Rebbi off; upfront, Rebbi off but the job's expected cost is moved to the
auditor before it starts; rebbi, the auditor borrows over MCP. The arms take turns case by case, and the
whole list repeats. A run succeeds only if the verifier passes, the ledger check passes and no loan left
its lender below its reserve (docs/bench/PLAN.md). Each run's row goes to results.csv as soon as it
ends, so a benchmark that stops keeps what it measured, and --resume runs only what is missing.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import statistics
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rebbi import fleet
from rebbi.gateway import UPSTREAM, serve_in_thread
from rebbi.scripted_model import BUDGETS, create_scripted_model

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "config" / "bench.toml"
FIELDS = ["label", "case", "kind", "split", "arm", "repeat", "target", "hint_tokens", "model", "run",
          "success", "finished", "verified", "checks_passed", "first_failure", "ledger_ok", "reserves_intact",
          "loans", "lend_decisions", "cannot_move", "auto_requests", "borrowed", "returned", "moved_upfront",
          "auditor_tokens", "fleet_tokens", "seconds", "auditor_usd", "turns", "stopped_by"]


def load_cases(path: Path = CASES) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def plan(settings: dict[str, Any], cases: dict[str, Any]) -> list[tuple[dict[str, Any], str, int]]:
    """(case, arm, repeat) in run order: each case under each of its arms, then the next case; then repeat."""
    chosen = [c for c in cases["cases"] if c["name"] in settings["cases"]]
    return [(case, arm, repeat)
            for repeat in range(1, settings["repeats"] + 1)
            for case in chosen
            for arm in settings["arms"] if arm in case.get("arms", cases["arms"])]


def row(label: str, case: dict[str, Any], arm: str, repeat: int, s: dict[str, Any]) -> dict[str, Any]:
    used = {a["agent_id"]: a["used"] for a in s["agents"]}
    loans, decisions = s["loans"], [d["decision"] for d in s["decisions"]]
    failed = [c for c in s["checks"] if not c["ok"]]
    reserves_intact = all(loan["lender_balance_after"] >= loan["lender_reserve"] for loan in loans)
    return {
        "label": label, "case": case["name"], "kind": case["kind"], "split": case["split"], "arm": arm,
        "repeat": repeat, "target": s["target"], "hint_tokens": s["hint_tokens"], "model": s["model"],
        "run": s["run"],
        "success": s["verified"] and s["ledger_ok"] and reserves_intact,
        "finished": s["finished"], "verified": s["verified"],
        "checks_passed": f"{len(s['checks']) - len(failed)}/{len(s['checks'])}",
        "first_failure": f"{failed[0]['name']}: {failed[0]['detail']}"[:200] if failed else "",
        "ledger_ok": s["ledger_ok"], "reserves_intact": reserves_intact,
        "loans": len(loans), "lend_decisions": decisions.count("LEND"), "cannot_move": decisions.count("CANNOT_MOVE"),
        "auto_requests": sum(d["request"]["goal"].startswith(fleet.AUTO_GOAL) for d in s["decisions"]),
        "borrowed": sum(loan["tokens"] for loan in loans),
        "returned": sum(loan["returned_tokens"] or 0 for loan in loans),
        "moved_upfront": (s["upfront"] or {}).get("tokens", 0),
        "auditor_tokens": used[fleet.AUDITOR], "fleet_tokens": sum(used.values()),
        "seconds": s["seconds"], "auditor_usd": s["cost_usd_reported"], "turns": s["turns"],
        "stopped_by": s["stopped_by"] or "",
    }


def read_rows(out: Path) -> list[dict[str, Any]]:
    path = out / "results.csv"
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def append_row(out: Path, r: dict[str, Any]) -> None:
    path = out / "results.csv"
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            writer.writeheader()
        writer.writerow(r)


def _yes(value: Any) -> bool:
    return str(value) == "True"  # csv stores booleans as text


def _spread(values: list[int]) -> str:
    """Median, then the range when runs differ: '27,516 (17,000-34,516)'."""
    if not values:
        return "-"
    mid = f"{round(statistics.median(values)):,}"
    return mid if min(values) == max(values) else f"{mid} ({min(values):,}-{max(values):,})"


def table(rows: list[dict[str, Any]]) -> str:
    """One line per case and arm, then per arm over the ordinary and hard cases: all, tuning, fresh."""
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in rows:
        groups.setdefault((r["case"], r["arm"]), []).append(r)
    for pool in ("all", "tuning", "fresh"):
        for r in rows:
            if r["kind"] != "failure" and pool in ("all", r["split"]):
                groups.setdefault((f"{pool} ordinary + hard", r["arm"]), []).append(r)
    head = ["case", "arm", "success", "verifier PASS", "auditor tokens", "fleet tokens", "seconds",
            "loans", "auditor $", "reserves intact", "ledger PASS"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for (case, arm), rs in groups.items():
        n = len(rs)
        usd = [float(r["auditor_usd"]) for r in rs if r["auditor_usd"] not in ("", "None", None)]
        lines.append("| " + " | ".join([
            case, arm,
            f"{sum(_yes(r['success']) for r in rs)}/{n}",
            f"{sum(_yes(r['verified']) for r in rs)}/{n}",
            _spread([int(r["auditor_tokens"]) for r in rs]),
            _spread([int(r["fleet_tokens"]) for r in rs]),
            _spread([int(r["seconds"]) for r in rs]),
            _spread([int(r["loans"]) for r in rs]),
            f"{sum(usd):.2f}" if usd else "-",
            f"{sum(_yes(r['reserves_intact']) for r in rs)}/{n}",
            f"{sum(_yes(r['ledger_ok']) for r in rs)}/{n}",
        ]) + " |")
    return "\n".join(lines)


async def bench(out: Path, settings: dict[str, Any]) -> int:
    cases = load_cases()
    upstream, auth, budgets = UPSTREAM, settings["auth"], {}
    if settings["rehearsal"]:
        port = fleet.free_port()
        serve_in_thread(create_scripted_model(), port)
        upstream, auth, budgets = f"http://127.0.0.1:{port}", "api-key", dict(BUDGETS)
    todo = plan(settings, cases)
    done = {(r["case"], r["arm"], int(r["repeat"])) for r in read_rows(out)}
    errors = 0
    for i, (case, arm, repeat) in enumerate(todo, 1):
        if (case["name"], arm, repeat) in done:
            continue
        print(f"\n##### bench {settings['label']}: run {i}/{len(todo)}: {case['name']}, {arm}, repeat {repeat}",
              flush=True)
        try:
            # The command line's budgets are the stress setting, so they win over a case's own.
            s = await fleet.run_fleet(arm, {**budgets, **case.get("budgets", {}), **settings.get("budgets", {})},
                                      upstream, auth,
                                      target=case["target"], hint=settings["hint_tokens"])
        except Exception as e:  # one broken run should not cost the rest; --resume retries it
            print(f"##### run failed before it finished: {e!r}", flush=True)
            errors += 1
            continue
        if "aborted" in s:
            print(f"##### stopped: {s['aborted']}\n##### finish later with: python -m rebbi.bench --resume "
                  f"{out.relative_to(ROOT)}", flush=True)
            return 2
        append_row(out, row(settings["label"], case, arm, repeat, s))
        (out / "table.md").write_text(table(read_rows(out)) + "\n", encoding="utf-8")
    print("\n" + table(read_rows(out)) + f"\n\nsaved {(out / 'results.csv').relative_to(ROOT)}", flush=True)
    if errors:
        print(f"{errors} run(s) failed before they finished; --resume {out.relative_to(ROOT)} runs them again")
        return 1
    return 0


def main() -> None:
    cases = load_cases()
    p = argparse.ArgumentParser(prog="rebbi.bench")
    p.add_argument("--label", default="main", help="a name for this benchmark, used in its folder name")
    p.add_argument("--cases", help="comma-separated case names from config/bench.toml (default: all)")
    p.add_argument("--arms", help=f"comma-separated, from {', '.join(fleet.MODES)} (default: {', '.join(cases['arms'])})")
    p.add_argument("--repeats", type=int, default=cases["repeats"])
    p.add_argument("--hint-tokens", type=int, metavar="TOKENS",
                   help="what the auditor is told past audits cost, for every case; 0 tells it nothing")
    p.add_argument("--budget", action="append", default=[], metavar="AGENT=TOKENS",
                   help="override one agent's budget in every case, e.g. analyst-07=120000")
    p.add_argument("--auth", choices=("auto",) + fleet.AUTH_MODES, default="auto")
    p.add_argument("--rehearsal", action="store_true", help="the scripted model: plumbing only, never evidence")
    p.add_argument("--resume", type=Path, metavar="FOLDER", help="finish this benchmark with its own settings")
    args = p.parse_args()

    if args.resume:
        out = args.resume.resolve()
        settings = json.loads((out / "settings.json").read_text(encoding="utf-8"))
    else:
        names = [c["name"] for c in cases["cases"]]
        settings = {
            "label": args.label,
            "cases": args.cases.split(",") if args.cases else names,
            "arms": args.arms.split(",") if args.arms else cases["arms"],
            "repeats": args.repeats,
            "hint_tokens": args.hint_tokens,
            "budgets": fleet.parse_budgets(args.budget),
            "auth": args.auth,
            "rehearsal": args.rehearsal,
        }
        if unknown := [c for c in settings["cases"] if c not in names] + \
                [a for a in settings["arms"] if a not in fleet.MODES]:
            p.error(f"unknown case or arm: {', '.join(unknown)}")
        tag = "-rehearsal" if args.rehearsal else ""
        out = ROOT / "runs" / "bench" / f"{datetime.now(UTC):%Y%m%d-%H%M%S}-{args.label}{tag}"
        out.mkdir(parents=True)
        (out / "settings.json").write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        (out / "command.txt").write_text("python -m rebbi.bench " + " ".join(sys.argv[1:]) + "\n", encoding="utf-8")
    sys.exit(asyncio.run(bench(out, settings)))


if __name__ == "__main__":
    main()
