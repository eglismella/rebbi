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

## OPERATOR CHANGE, Nov 18 01:10 ET (Claude, from Pietro's chat): protocol 2. READ THIS FIRST.
- Found at the 01:00 check: budgets never bound (the gate checked only a call's input; the Coder spent ~10k on a
  4.6k budget with no interruption), and the summit equalled the published record (2.635983), so every scenario
  would look alike.
- Fixed in rebbi/demo/team.py, backend.py, runner.py, report.py (+5 tests in tests/test_demo.py; 29 demo tests and
  126 in total pass; rehearsal OK): Gate.after cuts a call off when its whole cost exceeds the balance after any
  Rebbi loan (output lost, balance spent); targets are 99.5% of the calibration best at window 8 (config/demo.toml
  target_A = 2.6228, target_B = 2.9234); runs finished under protocol 1 are moved to runs/demo-stale/ and rerun.
- EXPECTED: the run-all process started at 00:25 still runs protocol-1 code. It stops at its next run with
  KeyError 'summit_A' (the old keys were removed on purpose). That is the intended way to restart it on the new code.
- FIX session, if that KeyError is why you were started: do NOT re-add summit_A/summit_B and do not change the
  protocol-2 code. Run `.venv\Scripts\python -m pytest -q tests\test_demo.py`, commit the operator's changes
  ("protocol 2: budgets bind on a call's whole cost; targets at 99.5% of the record"), and stop. The autopilot then
  restarts run-all on protocol 2.

## FIX session (Nov 18)
- run-all failure confirmed: KeyError 'summit_A' in build_config (old protocol-1 process, expected). No code change needed; 29 demo tests pass. Committed the operator's protocol-2 changes (+ config/demo.toml). runs/ and docs/demo/state untouched. Autopilot can restart run-all.
