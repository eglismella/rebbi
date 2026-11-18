# Eglis: run repeats 4 to 6 of the v2 experiment in parallel

Pietro's machine runs calibration, freezes the config and runs repeats 1-3. Your machine runs repeats 4-6 with
the same frozen config, so together we get 6 repeats per scenario. Your script waits on its own until the
config is frozen (it pulls `demo-v2` every 10 minutes), then runs and pushes results to the branch
`demo-v2-eglis` every 15 minutes. Pietro's report merges them.

## One-time setup (about 10 minutes)

1. `git fetch origin && git checkout -B demo-v2 origin/demo-v2`
2. Python 3.11+: `python -m venv .venv`, then `.venv/bin/pip install -e ".[test]"`
   (Windows: `.venv\Scripts\pip install -e ".[test]"`).
3. Claude Code CLI installed and on PATH (`claude --version`). Then `claude setup-token` (your Claude plan, no
   API key) and put the token in `.env` at the repo root: `CLAUDE_CODE_OAUTH_TOKEN=<token>`. `.env` is gitignored.
4. Make sure the machine will not sleep for the next ~12 hours, and plug it in.

## Start

- macOS or Linux: `bash scripts/run_demo2.sh eglis 4-6`
- Windows: `powershell -ExecutionPolicy Bypass -File scripts\autopilot2.ps1 -Machine eglis -Repeats 4-6`

It first runs a zero-usage preflight (reference solutions pass their tests, unit tests, a scripted rehearsal),
then waits for the frozen config, then starts three lanes. Stop any time with Ctrl+C; run the same command to
resume (finished runs are kept).

## Where to look

- `logs/demo2/eglis/autopilot.log` and `logs/demo2/eglis/status.txt`
- `python -m rebbi.demo2 status --repeats 4-6`
- Results: `results/demo2/eglis/` on branch `demo-v2-eglis`

If something stops with an error, the log says which file to read; `docs/demo2/TASK.md` has the rules for
fixing without changing the design (`docs/demo2/DESIGN.md`).
