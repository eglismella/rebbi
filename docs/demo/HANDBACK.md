# Hand-back for Pietro

## What ran
- Claude Haiku 5.5 for all five agents, Claude Pro subscription mode, Nov 18 2026 (calibration started 00:38 ET, last run ended 04:29 ET).
- Calibration (Exercise A, 10 windows) plus 18 scenario runs: 3 repeats of each of 6 scenarios. All 18 complete, ledger check PASS.
- T = 23,000 tokens per window. Targets (99.5% of the calibration best, 2.635983): A 2.6228, B 2.9234.
- Protocol 2 applies (budgets bind on a call's whole cost). Protocol-1 runs are in runs/demo-stale/ and not counted.

## Headline numbers (median over 3 repeats; range in brackets)
| Scenario | Exercise | Best score | Runs reaching target | Windows to target (runs that reached) |
| --- | --- | --- | --- | --- |
| 1 Equal budgets | A | 1.4268 (1.0245 to 1.4268) | 0 of 3 | none |
| 2 Manager budgets | A | 2.6305 (2.5917 to 2.6358) | 2 of 3 | 1, 3 |
| 3 Manager + Rebbi | A | 2.6340 (2.6288 to 2.6360) | 3 of 3 | 1, 2, 7 |
| 3-on-B | B | 2.9187 (2.0162 to 2.9261) | 1 of 3 | 4 |
| 3b Rebbi learns | B | 2.9276 (2.8261 to 2.9315) | 2 of 3 | 2, 8 |
| 4 Open market | A | 2.6279 (2.6235 to 2.6360) | 3 of 3 | 1, 5, 9 |

Interruptions per run: scenario 1 had 18 to 20 in every run; scenario 2 had 0, 2 and 23; scenario 3 had 0, 2 and 0.
Calibration best score 2.635983 (the published A record, 2.635; reference values are labelled as published, not ours).

## Checks
- results.html embedded data equals runs/demo/artifact_data.json; all 18 run summaries match results.csv (0 differences).

## Caveats
- Three repeats per scenario; ranges are wide (for example 3-on-B ranges from 2.0162 to 2.9261), so the ordering of scenarios 2, 3 and 4 is not settled by this data.
- Runs stop when the target is reached, so tokens issued differ between runs.
- The manager's budgets for scenarios 2, 3, 3-on-B and 4 were frozen from one call; 3b's budgets differ per repeat.
- The calibration needed one rerun (flat-hill guard fired, scipy forbidden); attempt 1 is kept in runs/demo/cal-attempt1.

## Not run / failed
- Nothing pending in the manifest; no run failed or was aborted_external in the final manifest.
- Git push: see the last line of this file.

## Next step
In a new chat in the AI Studio project, attach docs/demo/results.html and runs/demo/artifact_data.json and ask Claude to build the Rebbi Demo artifact from them.
