# Progress (BUILD phase)

## Done
- Set-up: branch demo-scenarios, .venv, check_api.py reports subscription mode.
- Pre-existing: 8 of 97 tests fail on this machine (tests/test_fleet_offline.py x7, one self-explaining test) because
  the audit target repo `targets/sqlite-utils` is not cloned (gitignored); not related to the demo. Not fixed.
- rebbi/demo.py moved to rebbi/video_demo.py so rebbi/demo can be a package (README refs updated).
- rebbi/demo/hill.py: evaluator + starting solve.py (scores 1.02 for n=26, 1.18 for n=32). Ledger.grant added.
- backend.py (SDK + scripted), market.py, team.py (window loop, gate, Rebbi top-up, calibration math) written; smoke OK.

## Next
runner (manifest, calibration, manager, run-all, results), report, tests, rehearsal, BUILD_DONE.
