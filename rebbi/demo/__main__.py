"""python -m rebbi.demo run-all | status | report | rehearsal"""

from __future__ import annotations

import argparse
import sys
import traceback
from datetime import datetime

from rebbi.demo import runner


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="rebbi.demo")
    sub = p.add_subparsers(dest="cmd", required=True)
    ra = sub.add_parser("run-all", help="calibration if needed, then every pending run until the stop time")
    ra.add_argument("--stop-new-runs-at", help="ISO local time; no new run starts after it")
    ra.add_argument("--repeats", type=int, default=3)
    sub.add_parser("status")
    sub.add_parser("report", help="rebuild results.csv views, artifact_data.json and docs/demo/results.html")
    sub.add_parser("rehearsal", help="the whole pipeline against the scripted model, in runs/demo-rehearsal/")
    args = p.parse_args(argv)
    try:
        if args.cmd == "run-all":
            stop = datetime.fromisoformat(args.stop_new_runs_at) if args.stop_new_runs_at else None
            return runner.run_all(runner.make_ctx(repeats=args.repeats), stop)
        if args.cmd == "status":
            print(runner.status_text(runner.make_ctx(backend=runner.ScriptedBackend())))
            return 0
        if args.cmd == "report":
            from rebbi.demo import report
            report.build_all(runner.make_ctx(backend=runner.ScriptedBackend()))
            print("wrote docs/demo/results.html")
            return 0
        if args.cmd == "rehearsal":
            return rehearsal()
    except KeyboardInterrupt:
        return 1
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        return 1
    return 1


def rehearsal() -> int:
    import shutil
    ctx = runner.make_ctx(rehearsal=True)
    if ctx.base.exists():
        shutil.rmtree(ctx.base)
    code = runner.run_all(ctx, None)
    rows = runner.read_manifest(ctx)
    bad = [r["run_id"] for r in rows if r["status"] != "complete"]
    print(runner.status_text(ctx))
    if code != 0 or bad:
        print(f"REHEARSAL FAILED: {bad or code}")
        return 1
    print(f"REHEARSAL OK (scripted, zero plan usage). Report: {ctx.report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
