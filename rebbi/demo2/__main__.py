"""python -m rebbi.demo2 preflight | rehearsal | prepare | run | status | export | report

  preflight [--smoke]   reference solutions pass their own tests (writes exercises/demo2/denominators.json);
                        --smoke also makes one real model call per role (a few thousand tokens)
  rehearsal             the whole pipeline with the scripted model in runs/demo2-rehearsal (zero plan usage)
  prepare               calibration A and B, T, floors, summits, manager, replay gate -> config/demo2.toml (frozen)
  run --repeats 1-3     one lane: runs pending scenario runs until none is left (start several lanes in parallel)
  status / export / report
  autopilot --machine pietro --repeats 1-3   every phase unattended (what scripts/autopilot2.ps1 starts)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path

from rebbi.demo2 import report, runner, suite
from rebbi.demo2.backends import ScriptedBackend


def preflight(smoke: bool, root: Path = suite.EXERCISES) -> int:
    bad, counts = [], {}
    for name in ("A", "B"):
        for ex in suite.load_set(name, root):
            ref = (root / "_reference" / f"{ex.slug}.py").read_text(encoding="utf-8")
            res = suite.run_tests(ex, ref)
            n_cases = res.passed + len(res.failing)
            if not res.all_pass or n_cases == 0:
                bad.append(f"{name}/{ex.slug}: {res.passed}/{n_cases} {res.output[-300:]!r}")
            counts[ex.slug] = n_cases or ex.ntests
    (root / "denominators.json").write_text(json.dumps(counts, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"reference solutions: {len(counts) - len(bad)}/{len(counts)} pass all their tests")
    for b in bad:
        print("  FAIL", b)
    if bad:
        return 1
    if smoke:
        ctx = runner.make_ctx()
        ex = suite.load_set("A", root)[0]
        gate = runner.CountGate()
        for role in ("planner", "researcher", "coder", "evaluator", "reviewer"):
            before = gate.tokens
            out = asyncio.run(ctx.backend.turn(role, runner.HAIKU, "Be brief.",
                                               f"Exercise `{ex.slug}`. Stub:\n```python\n{ex.stub}\n```\nWrite the "
                                               "complete file in one ```python block.", gate, 0))
            print(f"  smoke {role}: {gate.tokens - before} tokens, code block: {'```' in out.text}")
        print(f"smoke total: {gate.tokens} tokens")
    return 0


def rehearsal(root: Path | None = None, exercises_root: Path | None = None) -> int:
    base = (root or runner.ROOT) / "runs" / "demo2-rehearsal"
    if base.exists():
        shutil.rmtree(base)
    ex_root = exercises_root or suite.EXERCISES
    ctx = runner.make_ctx(rehearsal=True, base=base, backend=ScriptedBackend(reference=ex_root / "_reference"))
    ctx.exercises_root = ex_root
    conf = asyncio.run(runner.prepare(ctx))
    print("rehearsal: config frozen with T =", conf["calibration"]["T"], "gate", conf["gate"]["median_windows"])
    code = runner.lane(ctx, [1])
    print(runner.status_text(ctx, [1]))
    out = base / "results"
    report.export(ctx, "rehearsal", out)
    data = report.build(runner.ROOT, ctx, out, page_out=base / "results.html")
    done = [r for r in data["runs"] if r["rep"] == 1]
    if code != 0 or len(done) != len(runner.SCENARIOS):
        print(f"REHEARSAL FAILED: lane exit {code}, {len(done)} of {len(runner.SCENARIOS)} runs")
        return 1
    print(f"REHEARSAL OK (scripted, zero plan usage). Page: {base / 'results.html'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="rebbi.demo2")
    sub = p.add_subparsers(dest="cmd", required=True)
    pf = sub.add_parser("preflight")
    pf.add_argument("--smoke", action="store_true")
    sub.add_parser("rehearsal")
    sub.add_parser("prepare")
    r = sub.add_parser("run")
    r.add_argument("--repeats", default="1-3")
    r.add_argument("--stop-new-runs-at")
    s = sub.add_parser("status")
    s.add_argument("--repeats", default="1-3")
    e = sub.add_parser("export")
    e.add_argument("--machine", default=os.environ.get("REBBI_MACHINE", "pietro"))
    sub.add_parser("report")
    a = sub.add_parser("autopilot", help="every phase, unattended (see rebbi/demo2/autopilot.py)")
    a.add_argument("--machine", choices=["pietro", "eglis"], default="pietro")
    a.add_argument("--repeats", default="1-3")
    a.add_argument("--lanes", type=int, default=3)
    a.add_argument("--stop-new-runs-at", default="2026-11-22T12:00:00")
    args = p.parse_args(argv)
    try:
        if args.cmd == "preflight":
            return preflight(args.smoke)
        if args.cmd == "rehearsal":
            return rehearsal()
        if args.cmd == "prepare":
            conf = asyncio.run(runner.prepare(runner.make_ctx()))
            print("frozen:", json.dumps(conf["calibration"]), json.dumps(conf["gate"]["median_windows"]))
            return 0
        if args.cmd == "run":
            stop = datetime.fromisoformat(args.stop_new_runs_at) if args.stop_new_runs_at else None
            return runner.lane(runner.make_ctx(), runner.parse_repeats(args.repeats), stop)
        if args.cmd == "status":
            print(runner.status_text(runner.make_ctx(backend=ScriptedBackend()), runner.parse_repeats(args.repeats)))
            return 0
        if args.cmd == "export":
            paths = report.export(runner.make_ctx(backend=ScriptedBackend()), args.machine)
            print(f"exported {len(paths)} runs to results/demo2/{args.machine}/")
            return 0
        if args.cmd == "autopilot":
            from rebbi.demo2.autopilot import Autopilot
            return Autopilot(args.machine, args.repeats, args.lanes, args.stop_new_runs_at).main()
        if args.cmd == "report":
            data = report.build(runner.ROOT, runner.make_ctx(backend=ScriptedBackend()))
            print(f"report: {len(data['runs'])} runs -> docs/demo2/results.html, results/demo2/data.json")
            return 0
    except KeyboardInterrupt:
        return 1
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
