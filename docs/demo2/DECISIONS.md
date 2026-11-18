# Demo v2 decisions (Eglis's machine, repeats 4-6)

## 2026-11-18: s3onB-r5 moved to runs/demo2-invalid/ and rerun (TASK.md fix rule 4)

**What broke.** A lane treats a run's lock as stale after 30 minutes without a finished window
(`STALE_LOCK_S` in `rebbi/demo2/runner.py`). Lane 3 was running s3onB-r5 when lane 2 took its lock
as stale and started the same run. Before running a run, `execute()` deletes `<run_id>.partial`. That deleted
`config.json` and the logs of windows 1-6 under lane 3. `rebbi.db` survived because lane 3 had it open
(Windows does not delete open files). Lane 2's two attempts then failed with `PermissionError`, and lane 3
finished the run (summit at window 10, ledger check PASS).

**Why it is invalid.** The saved logs cover windows 7-10 only (`windows.jsonl` has 4 lines, `calls.jsonl` starts
at window 7) and `config.json` is missing. The ledger check reads `rebbi.db`, so PASS does not show the logs are
complete.

**Side effect.** `python -m rebbi.demo2 export` crashed on the folder (no `config.json`), so s4-r5, s3onB-r6 and
s4-r6 were not exported. They were exported one by one in commit b1dbead. Their logs start at window 1 and
their ledger checks pass.

**What was done.** The folder was moved to `runs/demo2-invalid/s3onB-r5` (kept, not deleted), its status was
reset to pending, and the run was repeated alone in one lane with the same frozen config. No design value was
changed.

**Result of the rerun.** 16:21 to 16:36 ET: summit at window 9, final score 96.3, 451,381 tokens used,
ledger check PASS, logs cover windows 1-9, `config.json` present. `export` now runs over all 18 runs without
error; the other 17 exported files did not change.

**Not fixed.** The lock bug is still in the code. A window that takes more than 30 minutes can let a second
lane restart a run in progress.
