# Decisions made without asking

- Hill: circle packing, n = 26 (A) and n = 32 (B), as chosen in TASK.md 3.1. Score is deterministic NumPy,
  no Docker, no timing noise.
- rebbi/demo.py (the video demo) renamed to rebbi/video_demo.py so `python -m rebbi.demo` can be the new package.
- numpy and scipy added as dependencies (the evaluator and candidates need them).
- 8 existing tests need the cloned audit target and fail on this PC; left as is.
- Agents have no tools: each turn is one text call (the cap of 6 model calls still applies). The harness asks
  Rebbi for a loan on the agent's behalf when a call's input exceeds its balance (auto-borrow, as in fleet.py)
  instead of giving agents MCP tools; fewer moving parts for 100+ unattended turns.
- The Evaluator agent receives the evaluator's result (run by the harness) and writes the report; the Reviewer
  agent writes a verdict line, while acceptance (valid and better) is decided by the harness rule.
- The rehearsal uses an in-process scripted backend (no CLI, no network), at zero plan usage.
- Scenario 4 claims accrue on the part of a loan the borrower actually spent (consumed x 1.05), not on tokens that
  were returned unspent. The borrower's claim falls by the consumed tokens; the debt limit is one window of budget.
- Unspent borrowed tokens go back to the lender when the borrower's turn ends (settle), so they can be lent again.
- A refused call's input is debited (as in fleet.py: the request reached Anthropic), which can overdraw a balance;
  the overdraft is forgiven at the refill and recorded as `overdraft` in windows.jsonl.
- A candidate is accepted only if it is valid, better, and both the Evaluator and Reviewer ran that window.
- Calibration reruns (up to two): Sonnet for the Coder if no valid candidate in three windows; scipy forbidden if
  the flat-hill guard fires. Earlier attempts are kept as runs/demo/cal-attemptN, not counted.
- Runs stop early when the best score reaches the summit (windows_to_summit). Other runs go to the 20-window cap.
- Run ids: cal, s1-r1, s2-r1, s3-r1, s3onB-r1, s3b-r1, s4-r1 (then r2, r3). The manager's scenario-2 budgets and
  scenario-3 shareable % are frozen in config/demo.toml and reused across repeats; 3b's answer is frozen per repeat.
- Cloned targets/sqlite-utils (gitignored) so the older fleet tests run here; fixed `rebbi init` leaving its ledger open.
- Protocol 2 (operator, Nov 18 01:10 ET). Budgets bind on a call's whole cost: if a finished call cost more than
  the agent's balance (after a Rebbi loan where the scenario allows one), it counts as cut off when the balance ran
  out; the balance is spent, the excess is recorded as unmet, and the call's output is lost (a cut-off reply would be
  incomplete). Protocol 1 checked only the input, so budgets never bound. The summit is 99.5% of the calibration
  best at window 8 (2.6228 for A, 2.9234 for B): that best equalled the published record, 2.635983, so a summit at
  the record would measure luck. Runs finished under protocol 1 are kept in runs/demo-stale/ and not counted.
