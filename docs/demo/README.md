# Rebbi Demo: reproduce

1. `git checkout demo-scenarios`
2. `python -m venv .venv` then `.venv\Scripts\python -m pip install -e ".[test]"`
3. Put `CLAUDE_CODE_OAUTH_TOKEN=<token>` in `.env` at the repo root (subscription mode, no API key).
4. `.venv\Scripts\python scripts\check_api.py` (must report subscription mode).
5. `.venv\Scripts\python -m pytest -q` (tests, including `tests/test_demo.py`).
6. `.venv\Scripts\python -m rebbi.demo rehearsal` (scripted model, zero plan usage, writes `runs/demo-rehearsal/`).
7. `.venv\Scripts\python -m rebbi.demo run-all --stop-new-runs-at 2026-11-18T21:00` (calibration, then 3 repeats of 6 scenarios; resumable; exit code 3 means plan limit, rerun later).
8. `.venv\Scripts\python -m rebbi.demo status` shows manifest progress.
9. `.venv\Scripts\python -m rebbi.demo report` rebuilds `docs/demo/results.html`, `runs/demo/results.csv`, `table.md` and `artifact_data.json`.
10. Open `docs/demo/results.html` by double-click.
