# TASK: build and run the Rebbi Demo Day experiment, fully unattended

You are Claude Code running **headless** on Pietro Bertone's Windows PC, at the root of a clone of
`github.com/eglismella/rebbi`, started by `scripts/autopilot.ps1`. Pietro owns the demo of team
Rebbi (MIT AI Studio MAS.665, Fall 2026). **Nobody will answer questions.** Never ask; decide,
record the decision in `docs/demo/DECISIONS.md`, and continue.

Each of your sessions starts with no memory. `docs/demo/PROGRESS.md` is your memory: read it
first, update it after every step (what is done, what is next, any problem), and commit locally
after every step. Never push except in the FINAL phase.

The autopilot runs these phases, each ended by a marker file in `docs/demo/state/`:

| Phase | Who | Ends with |
| --- | --- | --- |
| BUILD | you (one or more sessions) | `BUILD_DONE`: everything in sections 3 to 7 built, tests pass, rehearsal passes |
| RUNS | `python -m rebbi.demo run-all` (no Claude session) | `RUNS_DONE`: calibration plus as many scenario runs as fit before the stop time |
| FIX | you, only if run-all crashed | the cause fixed and committed; then run-all resumes |
| FINAL | you | `FINAL_DONE`: report checked, hand-back written, committed (section 8) |

**Clock.** The runs must leave usable results by **Wed Nov 18, 21:00 ET**. The autopilot passes
`--stop-new-runs-at`; no new run starts after it, and the report always reflects every completed
run. Keep the BUILD phase lean: working and tested beats elaborate.

## 0. Rules

- **Subscription mode only.** `.env` at the repo root holds `CLAUDE_CODE_OAUTH_TOKEN` (Pietro put
  it there). No API key, no paid spend. Never print, log or commit the token; before every commit
  check the staged diff for `sk-ant`, `CLAUDE_CODE_OAUTH_TOKEN=` followed by a value, and `Bearer `.
- **Never invent, estimate or round up a result.** Every number in the report comes from a file a
  completed run wrote. Missing cells say "not run".
- **Do not run experiment runs inside your own session** (they belong to run-all, outside you).
  You may run the zero-usage rehearsal and the test suite.
- Writing style for anything people read (report, docs): no em dashes; plain verbs; numbers over
  adjectives; no "not X but Y" constructions; "Shareable (% of budget)", never "share line".
- Branch `demo-scenarios` (create it from the current `main` if absent). Small local commits.

## 1. Set-up (first BUILD session)

```powershell
git checkout -B demo-scenarios
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[test]"
.venv\Scripts\python -m pytest -q            # expect 97 passed
.venv\Scripts\python scripts\check_api.py    # must report subscription mode
```

If `check_api.py` fails, write the reason in PROGRESS.md and DECISIONS.md, stop the session, and
do not create BUILD_DONE (the autopilot will retry later). Also read `scripts/autopilot.ps1`:
`run-all` must use the flags and exit codes it expects (section 4).

## 2. What Rebbi is

- Rebbi lends spare token budget between AI agents in one fleet. An agent short of budget calls
  `post_handoff`; the broker finds an agent with room above its reserve, books the loan
  atomically in a SQLite ledger, and replies `LEND` (with `partial`, `shortfall_tokens`,
  `limit_reason` when it covers less than asked) or `CANNOT_MOVE`. `settle` returns what is unspent.
- Reuse: `rebbi/ledger.py` (append-only; balances are sums), `rebbi/rules.py`
  (`lendable = balance - borrowed - reserve - declared demand`, capped per loan), `rebbi/broker.py`,
  `rebbi/mcp_server.py`, `rebbi/fleet.py` (Claude Agent SDK harness: in subscription mode it meters
  every call from the stream and stops an agent at the first call its balance cannot cover; read
  how it builds `ClaudeAgentOptions` and isolates agents), `rebbi/scripted_model.py` (zero-usage
  stand-in model), `rebbi/bench.py` (resume pattern). `docs/AGENT_INTERFACE.md` is the tool reference.
- `python -m rebbi --db <ledger> check` verifies the ledger invariants. Every counted run must pass.
- Product thesis: organizations give each agent a fixed budget; some agents hit the cap with work
  unfinished while others let tokens expire. Each agent marks a Shareable (% of budget); Rebbi
  lends shareable tokens to agents that run short; over time Rebbi helps set budgets and
  shareable % from usage data.

## 3. The experiment

### 3.1 The hill: circle packing in a unit square (chosen Nov 17 after research)

**Task.** Place n disjoint circles inside the unit square to maximize the sum of their radii.
**Exercise A: n = 26. Exercise B: n = 32** (a sibling: same rules, different size).
Reference values for the chart, labeled as published best-known, never as our results: n = 26
about 2.635 (AlphaEvolve 2.635; later 2.63598, ThetaEvolve paper); n = 32 about 2.937 (AlphaEvolve;
later 2.93957, arXiv 2605.04850).

**Why this hill** (record in DECISIONS.md):
- The score is deterministic and computed in milliseconds with NumPy, so it runs on Windows with no
  Docker and no timing noise. AlgoTune's score is a measured speedup, and timing on a laptop is
  noisy; ALE-Bench needs Docker images and a Rust scorer.
- It climbs in steps that suit windows: OpenEvolve's run went from 0.96 (a simple ring
  construction) to 1.80 at generation 10, 2.20 at generation 100, and 2.634 at generation 460,
  with an optimizer as the late breakthrough.
- It has known traps, which the evaluator below closes: lenient overlap tolerances (pipelines
  differ: 1e-6, 1e-7, or zero) and reward hacking of weak verifiers.

**Evaluator** (`rebbi/demo/hill.py`, fixed, never edited by agents):
- The team's candidate is one file, `solve.py`, defining `pack() -> (centers, radii)`. The
  evaluator runs it in a subprocess with a 60-second wall limit and a fixed seed
  (`numpy.random.seed(0)`, `random.seed(0)`), reads the arrays, and validates them itself:
  shapes exactly (n, 2) and (n,), finite values, radii > 0, every circle inside the square
  (`x - r >= -1e-9`, `x + r <= 1 + 1e-9`, same for y), every pair `dist >= ri + rj - 1e-9`.
- Score = sum of radii if valid, else 0 with the first violated check as the reason. The
  evaluator scores the returned coordinates, never a number the candidate prints.
- Allowed imports in `solve.py`: Python standard library, `numpy`, `scipy`. The starting
  `solve.py` (write your own; do not copy OpenEvolve's) places one circle in the centre and two
  rings, then shrinks radii until valid: it must score between 0.8 and 1.2.

**Flat-hill guard (automatic, in the calibration run).** If the calibration team's score at the
end of window 2 is already at least 98% of its score at the end of window 8, the hill is too short
for budgets to matter (the model likely recalls a one-shot optimizer). Then forbid `scipy` in
`solve.py` (the evaluator rejects the import), record it in DECISIONS.md, and calibrate again once.

### 3.2 The team (fixed across scenarios)

Five agents, each a Claude Agent SDK session with its own role prompt, all on Claude Haiku 5.5 in
subscription mode. If the calibration run shows the Coder cannot produce a valid candidate in
three windows, use Claude Sonnet 5.5 for the Coder only, in every scenario, and record it.
Turn order each window: **Planner** (picks the next idea from the attempt log), **Researcher**
(reads the current best code and past attempts, writes notes on what to try), **Coder** (writes a
new `solve.py`), **Evaluator** (runs the evaluator, reports score and reason), **Reviewer** (accepts
the candidate as the new best only if valid and better; otherwise keeps the old best). Each agent
turn is capped at 6 model calls. Every run starts with empty agent memory. Shared state is only
what the orchestrator passes: task text, current best `solve.py` and score, the attempt log.

### 3.3 Windows and budgets

- A **window** = one round of the five turns. Budgets refill at the end of each window; unused
  tokens **expire** at the refill. Cap: 20 windows per run.
- The org issues the same total per window, **T**, in every scenario.
- An **interruption** = an agent's call refused because its balance (plus loans) cannot cover it;
  that agent's turn ends; later agents in the window work with what exists.
- Shareable % maps onto Rebbi as the reserve: `reserve = (1 - shareable %) x budget`.

**Calibration (automatic, first thing run-all does).** One run on Exercise A with budgets too large
to bind (5 x T0, T0 = 2,000,000 tokens per window), 10 windows, no Rebbi. From it:
- **T** = the median over windows of total team tokens used per window, rounded to the nearest
  1,000. This makes the total roughly enough, so the split is what matters.
- **Summit_A** = the calibration team's best score at the end of window 8. **Summit_B** = Summit_A
  x (2.937 / 2.635), the same relative height on Exercise B.
- Write T, the summits, per-role demand per window and the guard outcome to `config/demo.toml`
  and `runs/demo/calibration/`. Calibration is shown in the report but is not a scenario.

### 3.4 Scenarios

1. **Equal fixed budgets.** T/5 each, no Rebbi. How most organizations set agent limits today.
2. **Manager sets budgets.** A manager agent (one model call before the climb) gets T, the five
   role descriptions and the task, and returns a JSON split of T. No Rebbi. Freeze its output
   (`config/demo.toml`) and reuse those budgets in scenarios 3 and 4.
3. **Manager + Rebbi.** Same budgets. The manager also returns each agent's Shareable (% of
   budget) by role importance (one more call, frozen). An agent that runs short asks Rebbi; Rebbi
   lends other agents' unused shareable tokens.
3b. **Rebbi learns, on Exercise B.** The manager gets per-role usage from scenario 3 of the same
   repeat (mean and spread of demand per window; tokens lent, borrowed, expired) and returns new
   budgets and shareable % (one call, frozen). Fair comparison: **3-on-B** (scenario 3's settings,
   unchanged, on Exercise B). Never compare 3b with scenario 1.
4. **Open market.** Manager's starting budgets. Each window each agent sets its own shareable %
   (a field in its turn output, no extra call). Tokens lent earn a claim of lent x 1.05 on the
   pool. An agent at 0% cannot borrow. Borrowing draws the claim down to a debt limit of one
   window of the agent's own budget.

Order within a repeat: 1, 2, 3, 3-on-B, 3b, 4. Repeat-major: every scenario of repeat 1 before
any of repeat 2. After repeat 1, continue with repeats 2 and 3 until the stop time.

### 3.5 Metrics

One row per run in `runs/demo/results.csv`: run_id, scenario, exercise, repeat, models, T,
budgets, shareable %, windows_to_summit (or "not reached"), best_score, tokens_issued,
tokens_used, tokens_expired, interruptions, loans_count, tokens_moved, ledger_check, status,
wall_seconds, started_at, ended_at. A run counts only if status = complete and ledger_check = PASS.

## 4. run-all: unattended, resumable, limit-safe

Commands (all in `rebbi/demo/`):
- `python -m rebbi.demo run-all --stop-new-runs-at <ISO local time>`: calibration if not done,
  then the next pending runs, one at a time, until none is pending or the stop time passes.
- `python -m rebbi.demo status`, `python -m rebbi.demo report`, `python -m rebbi.demo rehearsal`.

Required behavior:
- **Manifest** `runs/demo/manifest.csv`: one row per planned run with status pending, running,
  complete, aborted_external or failed. A run left `running` by a killed process is reset to
  pending at start-up.
- **Atomic finish.** A run writes into `runs/demo/<run_id>.partial/`. Only after it ends and the
  ledger check passes is the folder renamed to `runs/demo/<run_id>/`, its row appended to
  results.csv, and the report regenerated. A crash leaves only a `.partial` folder (deleted when
  that run is retried).
- **Plan limit.** Any usage-limit, rate-limit, 429, overloaded or authentication error from an
  agent stops all agents at once, marks the run aborted_external with the error text, and makes
  run-all **exit with code 3**. The autopilot waits and restarts run-all, which retries that run
  from scratch (never stitched). This is distinct from a Rebbi budget interruption, which is part
  of the experiment.
- **Exit codes:** 0 when nothing is pending or the stop time has passed (then write
  `docs/demo/state/RUNS_DONE`); 3 on a plan limit; 1 on any other error, with a traceback in the log.
- **Rehearsal** runs the whole pipeline (calibration, all six scenarios, report) against the
  scripted model in a separate folder `runs/demo-rehearsal/`, at zero plan usage, labels
  everything "scripted", and never touches `runs/demo/`.

## 5. Data to collect (everything the final artifact needs)

Per run folder `runs/demo/<run_id>/`:
- `config.json`: scenario, exercise, repeat, models, T, budgets, shareable %, summit, settings
  frozen from the manager, commit of the code.
- `windows.jsonl`: one line per window with, for each agent, budget, shareable %, reserve, used,
  lent, borrowed, expired, unmet (tokens refused), interrupted (bool), claim balance (scenario 4);
  for the team, candidate score and reason, accepted (bool), best score so far, and the best
  packing (`centers`, `radii`) so the artifact can draw the circles.
- `events.jsonl`: every loan (from, to, tokens, window, decision, partial, limit_reason), settle,
  interruption and acceptance, with a timestamp.
- `rebbi.db`, `ledger_check.txt`, `solve_best.py`, and agent transcripts with any secret removed.

Consolidated after every completed run: `runs/demo/results.csv`, `runs/demo/table.md`, and
**`runs/demo/artifact_data.json`**: one JSON object with setup (models, T, summits, exercises,
reference values and their sources), calibration, and every completed run's config, windows and
events. This file is what Pietro will attach in the chat that builds the final artifact, so keep it
self-describing (field names in plain words, units in the names, `null` for missing).

## 6. The report: `docs/demo/results.html`

`python -m rebbi.demo report` builds it from `runs/demo/artifact_data.json` only, and run-all calls
it after every completed run, so a usable page always exists.
- One self-contained HTML file (data embedded as JSON, no external fetch) that opens by
  double-click. Reuse the layout, style tokens, light and dark themes and components of
  `docs/demo/preview_toy.html` (the toy preview shown in class; do not change that file): setup
  strip, scenario tabs with rules and a budget table (Agent, Budget / window, Shareable (% of
  budget) as "35% · 6k", Avg new work / window), replay of recorded windows, the hill with
  milestone flags and the summit line, the token-flow diagram, per-agent budget bars, event log,
  race chart, results table. Add the best packing drawn as circles in the unit square per window.
- Title "Rebbi Demo". A banner states complete runs per scenario, model(s), exercises, dates and
  "Measured on Claude Pro in subscription mode". A limitations section. "not run" for missing
  cells; with more than one repeat, the median and the range.
- Where real data lacks a field the toy page showed, drop that element rather than fake it.

## 7. Tests (BUILD phase)

Manifest state machine (including a run left `running`), atomic finish, plan-limit
classification and exit code 3, the evaluator (valid packing, overlap, outside the square, wrong
shape, forbidden import, timeout), calibration arithmetic, shareable % to reserve, the market claim
math, ledger invariants after a scripted multi-agent run, and the report building from a tiny
`artifact_data.json`. The full suite (97 existing tests plus yours) must pass before BUILD_DONE.

## 8. FINAL phase

1. `python -m rebbi.demo report`; check the numbers in results.html against results.csv.
2. Write `docs/demo/DECISIONS.md` (every choice made without asking), `docs/demo/README.md`
   (reproduce in 10 lines) and `docs/demo/HANDBACK.md` for Pietro: what ran (runs per scenario,
   models, dates), the headline numbers with run counts, what failed or was not run, and the next
   step: "In a new chat in the AI Studio project, attach docs/demo/results.html and
   runs/demo/artifact_data.json and ask Claude to build the Rebbi Demo artifact from them."
3. Check the diff for secrets, commit, then try `git push -u origin demo-scenarios` once; if it
   fails, note it in HANDBACK.md and move on. Create `docs/demo/state/FINAL_DONE`.

## Sources for section 3.1

- OpenEvolve circle packing example (score trajectory, two-phase set-up): github.com/algorithmicsuperintelligence/openevolve, examples/circle_packing
- ThetaEvolve, arXiv 2511.23473 (best-known n = 26, tolerance differences between pipelines)
- Out-of-the-Box Global Optimization for Packing Problems, arXiv 2605.04850 (n = 32, 2.93957)
- Hill Sampling for Test-Time Scaling, arXiv 2609.25510 (evaluator hardening against reward hacking)
- AlgoTune, arXiv 2507.15887; ALE-Bench, arXiv 2506.09050 and its Docker images (the alternatives considered)
