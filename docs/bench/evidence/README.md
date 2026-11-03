# HW7 benchmark evidence

Every real run behind the HW7 report, copied out of the git-ignored `runs/` folder by
`scripts/package_evidence.py`. The plan, and what each benchmark showed, is in `../PLAN.md`.
All runs: Claude Sonnet 5.5 as the auditor, Claude Haiku 5.5 as the lenders, on a Claude plan login
(`--auth subscription`), Nov 3, 2026.

| Folder | What it is | Runs |
|---|---|---|
| `main/` | Every case, baseline / upfront / rebbi, 3 runs each, before the change | 51 |
| `wording-check/` | The cost hint's HW6 wording against the new one, rebbi on sqlite-utils-3.38, alternating | 10 |
| `retest-autoborrow/` | The rebbi arm again, every case, after the change (auto-borrow) | 18 |
| `stress-hint15k/` | Tuning cases, upfront / rebbi, the auditor told 15,000 instead of 60,000 | 12 |
| `stress-nohint/` | Tuning cases, upfront / rebbi, the auditor told nothing about cost | 12 |
| `stress-scarce/` | Tuning cases, upfront / rebbi, analyst-07 with 20,000 to spare instead of 80,000 | 12 |

Each benchmark folder holds `results.csv` (one row per run, naming its run folder), `table.md` (success
and costs per case and arm), `settings.json` and `command.txt` (the exact command).

`runs/<run>/` holds one run:

- `console.log`: everything the run printed: each model call's tokens, each Rebbi request and answer,
  each refusal, the verifier's checks, the ledger check.
- `report.md`: the auditor's report, as the verifier read it.
- `verify.txt`: the verifier's checks against the repository's answer key (`specs/answer-key-*.json`).
- `summary.json`: the outcome, the ledger's final balances, every loan and every broker decision.
- `scenario.json`: the budgets, reserves, rules and target the run used.
- `transcript-<agent>.jsonl`: every message each agent sent and received.

Left out: `claude-config/` (the agents' CLI settings folders) and `rebbi.db` (the run's SQLite ledger,
whose contents `summary.json` lists). No credentials are in any file here.

To check one row: open its `runs/<run>/verify.txt`, or run
`python -m rebbi.verify docs/bench/evidence/runs/<run>/report.md --key specs/answer-key-<target>.json`.
