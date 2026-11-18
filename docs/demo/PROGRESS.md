# Progress (BUILD phase)

## Done
- Set-up: branch demo-scenarios, .venv, check_api.py reports subscription mode.
- Pre-existing: 8 of 97 tests fail on this machine (tests/test_fleet_offline.py x7, one self-explaining test) because
  the audit target repo `targets/sqlite-utils` is not cloned (gitignored); not related to the demo. Not fixed.
- rebbi/demo.py moved to rebbi/video_demo.py so rebbi/demo can be a package (README refs updated).
- rebbi/demo/hill.py: evaluator + starting solve.py (scores 1.02 for n=26, 1.18 for n=32). Ledger.grant added.
- backend.py (SDK + scripted), market.py, team.py (window loop, gate, Rebbi top-up, calibration math) written; smoke OK.

## Next
tests (section 7), final checks, BUILD_DONE.
- runner.py (manifest, calibration with guards, manager calls, run-all, results), report.py (artifact_data.json, table.md,
  results.html with embedded data), __main__.py (run-all, status, report, rehearsal). `python -m rebbi.demo rehearsal`
  passes end to end (7 runs, scripted, zero usage); the report JS runs without error under a DOM stub.
- tests/test_demo.py added (24 tests). Cloned targets/sqlite-utils at the pinned commit (gitignored) so the 7 fleet
  tests run; fixed a Windows file-lock bug in `rebbi init` (ledger left open). Full suite: 121 passed.
- Rehearsal passes (7 runs, scripted); `status` and `report` work on an empty runs/demo.
- BUILD complete. Next phase: run-all (autopilot). The real SdkBackend has not run against Claude yet (by design:
  no experiment runs in the build session); if run-all fails on it, the FIX phase handles it.
