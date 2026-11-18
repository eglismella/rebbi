# Demo Day experiment v2: design, fixed before the first run

Status: pre-registered on Nov 18 2026, before any v2 run. Every number below is either fixed here or set by a
rule written here from the calibration runs. Nothing changes after `prepare` freezes `config/demo2.toml`.

## Question

Five agents share a fixed token budget per window. Does the way the budget is distributed change how fast the
team finishes, how many tokens expire unused, and how often an agent runs out with work waiting? Six setups:
equal budgets, a manager's split, the manager's split plus Rebbi loans, the same on a sibling task, Rebbi
learning from scenario 3's data, and an open market.

## Why the pilot (Nov 18, 00:00 to 04:30) is not the answer

1. The hill (circle packing) was solved in one window once the Coder had about 10,000 tokens: runs measured
   whether one Coder turn fit its budget, not a climb.
2. Equal budgets (4,600 each) were below one Coder call (median 14,084), so scenario 1 could never finish.
3. Three repeats with outcomes as spread as "window 1, window 3, never" cannot separate scenarios 2, 3 and 4.
4. The budget rule changed mid-run (protocol 2 at 01:10).
The pilot is kept as a pilot (branch demo-scenarios) and is not mixed with v2 data.

## Task: the test-suite climb

- Two sets of 55 Exercism Python practice exercises (MIT licence), A and B, matched by difficulty
  (`exercises/demo2/MANIFEST.json` gives the selection rule; A has 801 tests, B 833).
- Score = percent of the set's test cases passing in shipped exercises. Tests run with pytest in a temporary
  folder, 60 s limit, in the harness (not by an agent).
- Pipeline per exercise: Researcher (notes from instructions and tests) -> Coder (writes the file; tests run)
  -> Evaluator (test report or diagnosis) -> Reviewer (approves if all tests pass, else rewrites; tests run).
  Up to 2 rewrites, then the exercise ships with what it passes. When nothing else is open, partly passing
  exercises reopen, up to 5 rewrites in total. Shipped tests are never lost.
- The Planner orders the open exercises once per window.
- Hand-offs land at the next window: work passed on becomes available to the next role at the next refill.
  The pipeline therefore fills (Researcher busy, others idle) and drains (Evaluator and Reviewer busy, others
  idle). Phase label for the page: Explore while at least a third of the exercises are untouched, Polish once
  no exercise waits for the Researcher or the Coder, Build in between.

## Budgets and rules

- Each agent is a text-only Claude Agent SDK session on Claude Haiku 5.5 with empty memory per call (no tools),
  output capped at 3,000 tokens. Tokens are metered from the stream (whole cost of each call).
- Before each item an agent checks that its balance covers the expected cost of the call (the run's mean for
  that role and kind of call after 2 calls, the calibration median before). If not, in scenarios 3, 3-on-B, 3b
  and 4 it asks Rebbi for the difference; if it still cannot cover it, it stops and its queue waits
  (an interruption). A call costing more than the balance is cut off and its output lost (pilot protocol 2).
- Unused tokens expire at the refill. Rebbi lends only from the shareable part of a budget
  (reserve = (1 - shareable %) x budget). Unspent borrowed tokens go back to the lender when the borrower's turn ends.
- Scenario 4: each call ends with the agent's shareable %; agents start at 50%; lending earns a claim of
  1.05 x tokens consumed; an agent may owe at most one window of its own budget; 0% shareable means no borrowing.

## Numbers set from calibration (`python -m rebbi.demo2 prepare`)

- Calibration: one unconstrained team (400,000 tokens per agent per window, never binding) ships set A and set
  B once each, at most 15 windows.
- Floors: each role's budget is at least 1.1 x its largest call in calibration (rounded up to 500, at least
  1,500), in every scenario. The manager's split is raised to the floors (the excess taken proportionally from
  roles above their floor). Equal split T/5 must cover the largest floor.
- T (tokens per window for the team) = max(5 x largest floor, calibration tokens on set A / 18, rounded up to
  1,000).
- Summit = 92% of the calibration team's final score on that set, rounded down to 0.5.
- Manager: asked once for budget percentages and once for shareable percentages from the role descriptions;
  the answers are frozen and reused in every repeat and on every machine. Scenario 3b: the manager is asked per
  repeat with that repeat's scenario 3 usage summary.
- Replay gate (zero usage): every scenario is replayed 3 times with costs and test results resampled from
  calibration. Required: every scenario's median windows to summit <= 45, and the fastest >= 12. If the first
  fails, T rises 15%; if the second fails, T falls 13% (never below 5 x largest floor); at most 8 tries. If the
  first still fails, nothing runs.
- Calibration below 60% of tests on either set stops everything (the task would be too hard as set up).

## Runs

- Scenarios 1, 2, 3, 4 on set A; 3-on-B and 3b on set B. Cap 60 windows; a run stops at the summit.
- Repeats 1-3 on Pietro's machine, 4-6 on Eglis's machine, same frozen config. Three lanes per machine run in
  parallel; each run has its own ledger. A run counts only if its ledger check passes.
- A plan-limit stop waits 20 minutes and reruns that run from the start. A run that fails three times is marked
  failed and reported.

## Outputs and analysis (fixed now)

- Per run: windows to summit (or ">60"), tokens expired as a share of tokens issued, interruptions
  (agent-windows ending with work waiting for lack of budget), cut-off calls, tokens moved by Rebbi.
- Per scenario: median and every value over all repeats; the page states medians and shows each repeat. No
  significance test is claimed; differences of one or two windows are read as noise.
- The results page (`docs/demo2/results.html`) keeps the layout of the "Rebbi Demo of Demo" preview: scenario
  tabs, the climb, the token flow, the per-agent ledger, the race and a results table, with recorded windows in
  place of the toy model, plus an all-repeats table.

## Known limits

One model family and one task family; hand-offs at the refill are a design choice; repeats are few; the team
that built Rebbi runs the experiment; replay estimates in the gate are only a check of feasibility.
