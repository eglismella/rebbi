"""Copy the HW7 benchmark evidence out of the git-ignored runs/ folder into docs/bench/evidence/.

Copies each benchmark's results files, and the text files of every run they name (never claude-config/
or the SQLite ledger). Builds a results.csv for the hint-wording check, whose runs were not a benchmark.

    python -I scripts/package_evidence.py .
"""

import csv
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
RUNS, OUT = ROOT / "runs", ROOT / "docs" / "bench" / "evidence"
BENCHES = {"main": "20261103-171109-main", "retest-autoborrow": "20261103-204142-retest-autoborrow",
           "stress-hint15k": "20261103-205606-stress-hint15k", "stress-nohint": "20261103-221726-stress-nohint",
           "stress-scarce": "20261103-222149-stress-scarce"}
# scripts/wording_check.py alternates the wordings, HW6's first; this is the order it printed.
WORDING = ["20261103-172327-rebbi", "20261103-172400-rebbi", "20261103-172418-rebbi", "20261103-172453-rebbi",
           "20261103-172527-rebbi", "20261103-172559-rebbi", "20261103-172612-rebbi", "20261103-172639-rebbi",
           "20261103-172658-rebbi", "20261103-172730-rebbi"]
RUN_FILES = ["console.log", "report.md", "verify.txt", "summary.json", "scenario.json"]

run_names = set(WORDING)
for name, folder in BENCHES.items():
    dest = OUT / name
    dest.mkdir(parents=True, exist_ok=True)
    for f in ("results.csv", "table.md", "settings.json", "command.txt"):
        shutil.copy2(RUNS / "bench" / folder / f, dest / f)
    with open(dest / "results.csv", newline="", encoding="utf-8") as fh:
        run_names |= {r["run"] for r in csv.DictReader(fh)}

rows = []
for i, run in enumerate(WORDING):
    s = json.loads((RUNS / run / "summary.json").read_text(encoding="utf-8"))
    rows.append({"wording": "hw6: on this commit" if i % 2 == 0 else "new: job-level", "run": run,
                 "borrowed": bool(s["loans"]), "verified": s["verified"], "ledger_ok": s["ledger_ok"],
                 "auditor_tokens": next(a["used"] for a in s["agents"] if a["agent_id"] == "auditor-01")})
(OUT / "wording-check").mkdir(parents=True, exist_ok=True)
with open(OUT / "wording-check" / "results.csv", "w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

for run in sorted(run_names):
    dest = OUT / "runs" / run
    dest.mkdir(parents=True, exist_ok=True)
    for f in RUN_FILES + sorted(p.name for p in (RUNS / run).glob("transcript-*.jsonl")):
        shutil.copy2(RUNS / run / f, dest / f)
print(f"{len(run_names)} run folders, {len(BENCHES)} benchmarks, wording check {len(rows)} runs")
