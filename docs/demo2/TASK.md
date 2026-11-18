# Rules for Claude Code sessions on the v2 experiment

You are started headless by the autopilot (`rebbi/demo2/autopilot.py`, launched by `scripts/autopilot2.ps1`) only when something fails. Nobody will answer questions.
The design is fixed in `docs/demo2/DESIGN.md`; the code is in `rebbi/demo2/`; tests in `tests/test_demo2.py`.

## Fix rules

1. Find the cause in the log you were given, `runs/demo2/_status/*.json` and `logs/demo2/<machine>/`.
2. Fix code, never the design. Do not edit `config/demo2.toml` once it says `frozen = true`, do not change any
   constant listed in DESIGN.md (T, floors, summit rule, caps, gate thresholds, prompts' content), and do not
   delete or edit finished runs in `runs/demo2/<run_id>/` or `results/demo2/`.
3. If the only possible fix would change how a run behaves (prompts, budgets, the gate, stop rules), do not make
   it: write `docs/demo2/BLOCKED.md` with the cause and the options, commit, and stop. The monitoring chat
   will take it to Pietro.
4. If the bug made finished runs wrong (for example the ledger or the counts), move those run folders to
   `runs/demo2-invalid/`, explain it in `docs/demo2/DECISIONS.md`, and they will be rerun.
5. Add a test that fails without the fix, run `python -m pytest -q tests/test_demo2.py`, commit locally with a
   clear message. Do not push and do not start experiment runs yourself; the autopilot resumes.
6. Never print, log or commit the token in `.env`.

## Typical problems and what they mean

- Preflight: a reference solution fails its own tests on this machine. Usually a platform difference (path,
  encoding, line endings, Python version). Fix the runner, not the exercise. If one exercise cannot pass on
  Windows at all, write BLOCKED.md (dropping it changes the design).
- `prepare` stops with "calibration reached only N%": the model cannot do the task as set up. BLOCKED.md.
- `prepare` stops with "replay gate failed": BLOCKED.md with the gate numbers from config/demo2.toml.
- Lane exit 4: a run failed three times. Read its `_status` error. Plan or rate limits are handled already
  (the lane waits 20 minutes); anything else is a bug to fix under the rules above.
