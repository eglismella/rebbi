# TASK: run the Rebbi Demo Day experiment, autonomously, on Pietro's Claude Pro plan

You are Claude Code in Pietro Bertone's terminal (Windows, PowerShell), at the root of a clone
of `github.com/eglismella/rebbi`. Pietro owns the demo and presentation of team Rebbi (MIT AI
Studio MAS.665, Fall 2026; teammates Eglis Mella, repo owner, and Nitya Maddineni). **Demo Day is
Thu Dec 3, 2026. Target: one complete repeat of every scenario and the results page by Wed Nov 25.**

Your job: build the experiment, run it within Pietro's Pro usage limits, and deliver
`docs/demo/results.html`, `runs/demo/results.csv` and a PR. Work autonomously. Pietro wrote this
file so that he does not have to relay context: everything you need is here or in the repo. When
something is ambiguous, pick the simplest option that keeps the comparison fair, record it in
`docs/demo/DECISIONS.md`, and continue. Stop and ask Pietro only at the points marked **ASK**.

## 0. Rules

- **Pietro's hands are needed only for:** the one-time setup in section 1 (token, `.env`),
  answering the ASK points, resuming you after a plan-limit reset (`claude --continue`), and
  approving the final push. Everything else is yours.
- **Never** ask Pietro to paste a token into chat, and never print, log or commit one. The token
  lives only in `.env` (git-ignored; check before the first commit). Before every commit, check
  the diff for `sk-ant`, `CLAUDE_CODE_OAUTH_TOKEN=` followed by a value, and `Bearer `.
- **No API key, no paid spend.** Subscription mode only (`.env` holds `CLAUDE_CODE_OAUTH_TOKEN`).
- **Never invent, estimate or round up a result.** Every number on the results page comes from a
  file a completed run wrote. Missing cells say "not run".
- **Save your own usage:** your session and the experiment agents draw on the same Pro limits.
  Read files in parts, do not re-read, do not paste long logs, and never run the long experiment
  inside your own tool calls (section 3 says how runs execute).
- **Writing style** for anything Pietro or the class reads (page copy, PR text, docs): no em
  dashes; plain verbs; numbers over adjectives; no "not X but Y" constructions; say
  "Shareable (% of budget)", never "share line".
- Work on branch `demo-scenarios`, created from the current `main`. Commit in small steps.

## 1. One-time setup (Pietro, about 15 minutes; guide him through it, one step at a time)

1. Python 3.11+ and Git for Windows installed (`python --version`, `git --version`).
2. Claude Code installed and logged in with his Pro account (he is talking to you, so this is
   done). Recommended start command, from the repo root:
   `claude --permission-mode auto`. If auto mode is not available on his plan, use
   `claude --permission-mode acceptEdits` and create `.claude/settings.local.json` (git-ignored by
   Claude Code) with allow rules so routine commands do not prompt:
   ```json
   {"permissions": {"allow": [
     "PowerShell(.venv\\Scripts\\python *)", "PowerShell(python *)", "PowerShell(git status*)",
     "PowerShell(git diff*)", "PowerShell(git add *)", "PowerShell(git commit *)",
     "PowerShell(git checkout *)", "PowerShell(Start-Process *)",
     "Bash(.venv/Scripts/python *)", "Bash(python *)", "Bash(git status*)", "Bash(git diff*)",
     "Bash(git add *)", "Bash(git commit *)", "Bash(git checkout *)"],
     "ask": ["PowerShell(git push*)", "Bash(git push*)"]}}
   ```
3. In a separate PowerShell window: `claude setup-token`. It prints a long-lived token for his
   Pro subscription. He opens `.env` at the repo root in Notepad (`notepad .env`) and adds one line
   `CLAUDE_CODE_OAUTH_TOKEN=<the token>`. He tells you "done", never the token.
4. You run, and fix anything that fails:
   ```powershell
   git checkout -b demo-scenarios
   python -m venv .venv
   .venv\Scripts\python -m pip install -e ".[test]"
   .venv\Scripts\python -m pytest -q            # expect 97 passed
   .venv\Scripts\python scripts\check_api.py    # must report subscription mode
   .venv\Scripts\python -m rebbi fetch-target
   ```

## 2. What Rebbi is (read README.md in parts for detail)

- Rebbi lends spare token budget between AI agents in one fleet. An agent short of budget calls
  `post_handoff`; the broker finds an agent with room above its reserve, books the loan atomically
  in a SQLite ledger, and replies `LEND` (with `partial`, `shortfall_tokens`, `limit_reason` when
  it covers less than asked) or `CANNOT_MOVE`. `settle` returns unspent tokens.
- Files you will reuse: `rebbi/ledger.py` (append-only ledger; balances are sums),
  `rebbi/rules.py` (`lendable = balance - reserve - declared demand`, capped per loan),
  `rebbi/broker.py`, `rebbi/mcp_server.py` (MCP over stdio or HTTP; `REBBI_TRACE` logs every call),
  `rebbi/fleet.py` (Claude Agent SDK harness; in subscription mode it meters every call from the
  stream and stops an agent at the first call its balance cannot cover), `rebbi/bench.py`
  (benchmark pattern: cases x arms x repeats, `--resume`), `rebbi/calibrate.py`,
  `rebbi/scripted_model.py` (zero-usage stand-in model), `config/scenario.toml` (numbers).
- `python -m rebbi --db <ledger> check` verifies the ledger: totals conserved, each loan's
  entries cancel, no lender below its reserve, no loan active past expiry.
- `docs/AGENT_INTERFACE.md` is the full tool reference. `docs/hw9/RESULTS.md` is the latest
  evidence (HW9). HW7: on a dependency audit, upfront allocation was cheaper with a right estimate
  but failed 8 of 12 with a wrong or missing one; Rebbi passed 12 of 12.
- Product thesis (Pietro): organizations give each agent a fixed budget; some agents hit the cap
  with work unfinished while others let tokens expire. Each agent marks a Shareable (% of budget);
  Rebbi lends shareable tokens to agents that run short; over time Rebbi helps set budgets and
  shareable % from usage data.

## 3. The experiment

### 3.1 The hill (fixed across scenarios)
- One hill-climbing exercise with a numeric score per step. First choice: an AlgoTune task
  (arXiv 2507.15887; find its code repository from the paper page). Each task has a reference
  solver, a correctness check and a timed speedup score. Score = speedup of the team's best
  correct solution over the reference.
- Pick two sibling tasks that install and score in seconds on Windows with pure
  Python/NumPy/SciPy: **Exercise A** and **Exercise B**.
- If AlgoTune does not install or score reliably on Windows within about an hour of effort, write
  a self-contained hill instead: a reference numeric routine, a timing harness and correctness
  tests, in two variants for A and B. Record the switch in DECISIONS.md.
- **Summit** = a target speedup set in the pilot so a well-run team reaches it in about 8 to 15
  windows. Cap every run (for example 20 windows); a run that hits the cap records "not reached"
  and its best speedup.

### 3.2 The team (fixed across scenarios)
Five agents with their own role prompts, all on the cheapest model available in subscription
mode (Claude Haiku 5.5), unless the pilot shows it cannot make progress; then Claude Sonnet 5.5
for the Coder only, recorded in DECISIONS.md. Planner (picks the next idea), Researcher (reads the
task, docs and prior attempts), Coder (writes each candidate), Evaluator (runs the scorer, reports
speedup and correctness), Reviewer (checks correctness before a candidate becomes the new best).
Every run starts with empty memory. Shared state is only what the orchestrator passes: task text,
current best code and score, a short attempt log.

### 3.3 Time and budgets
- A **window** = one orchestrator round: every agent gets one turn, bounded to a few model calls.
  Budgets refill at the end of each window; unused tokens **expire** at the refill.
- The org issues the same total per window, **T**, in every scenario. Set T in the pilot near the
  team's average unconstrained demand per window, so the total is roughly enough and the split is
  what matters. Freeze T.
- An **interruption** = an agent's call refused because its balance (plus loans) cannot cover it;
  that turn's work is lost and the agent waits for the next window.
- Shareable % maps onto Rebbi as the reserve: `reserve = (1 - shareable %) x budget`, so
  `lendable = min(unused this window, shareable % x budget)` falls out of the existing rules.
  `rebbi check` must pass after every run.

### 3.4 Scenarios
1. **Equal fixed budgets.** T/5 each, no Rebbi. How most organizations set agent limits today.
2. **Manager sets budgets.** A manager agent (one model call before the climb) gets T, the five
   role descriptions and the task, and returns a JSON split of T. No Rebbi. Freeze its output and
   reuse the same budgets in scenarios 3 and 4.
3. **Manager + Rebbi.** Same budgets. The manager also returns each agent's Shareable (% of
   budget) by role importance (one more call, frozen). Rebbi routes loans from other agents'
   unused shareable tokens; it can move at most T minus the unused non-shareable tokens.
3b. **Rebbi learns, on Exercise B.** Rebbi gives the manager per-role usage from scenario 3 (mean
   and spread of demand per window; tokens lent, borrowed, expired). The manager returns new
   budgets and shareable % (one call, frozen). Fair comparison: **3-on-B**, scenario 3's settings
   run unchanged on Exercise B. Never compare 3b with scenario 1: different exercises.
4. **Open market.** Manager's starting budgets. Each window each agent sets its own shareable %
   (a field in its normal turn output, no extra call). Tokens lent earn a claim on the pool of
   lent x (1 + r), r = 5%. An agent at 0% shareable cannot borrow. Borrowing draws down the claim,
   down to a debt limit of one window of the agent's own budget. Log every choice and claim.

### 3.5 Metrics (one row per run in results.csv)
run_id, scenario, exercise, repeat, model(s), T, budgets, shareable %, windows_to_summit (or not
reached), best_speedup, speedup per window, tokens_issued, tokens_used, tokens_expired,
interruptions, loans_count, tokens_moved, per-agent per-window used/lent/borrowed/expired/unmet,
ledger_check, status, wall time, start and end timestamps. A run counts only if
status = complete and ledger_check = PASS.

## 4. Running safely within Pro limits (required design)

- **One run at a time.** Unit = one run (scenario x exercise x repeat). Commands:
  `python -m rebbi.demo next` (runs the next pending run from `runs/demo/manifest.csv`, then
  exits), `python -m rebbi.demo status`, `python -m rebbi.demo retry <run_id>`, and
  `python -m rebbi.demo run-all` (loops `next` until nothing is pending or an external abort).
- **Atomic results.** A run writes into `runs/demo/<run_id>.partial/`; only after it finishes and
  `rebbi check` passes is the folder renamed and a row appended to results.csv.
- **Plan limit: stop at once.** Any usage-limit, rate-limit, 429, overloaded or auth error from an
  agent is an external abort: stop all agents, mark the run `aborted_external` with the error text,
  keep the partial folder, exit with a clear message. An aborted run is rerun from scratch, never
  stitched. Keep this distinct from a Rebbi budget interruption, which is part of the experiment.
- **Repeat-major order:** repeat 1 of every scenario (1, 2, 3, 3-on-B, 3b, 4) before any repeat 2.
- **Runs execute outside your session.** Start `run-all` in its own window so it survives your
  session: `Start-Process powershell -ArgumentList '-NoExit','-Command','.venv\Scripts\python -m rebbi.demo run-all *>> runs\demo\run-all.log'`.
  Check progress with `status` and the log tail, sparingly. If the plan limit stops both the
  runner and you, Pietro waits for the reset, runs `claude --continue`, and types "resume": you
  then `retry` the aborted run and start `run-all` again.

## 5. Order of work

1. **Setup** (section 1).
2. **Plan.** Read only what you need. Write `docs/demo/PLAN.md` (one page: design, files you add
   or change, how each scenario maps onto Rebbi, the abort design, what the pilot measures). Commit.
3. **Build** under `rebbi/demo/` (orchestrator, roles, scenarios, manager, market, runner,
   manifest) with config in `config/demo.toml`. Reuse ledger, broker, rules and metering; do not
   break the HW7 bench or any test. Tests: manifest state machine, atomic finish, abort
   classification, market claim math, shareable % to reserve mapping, ledger invariants after a
   scripted multi-agent run. A `--rehearsal` mode with a scripted model runs everything at zero
   plan usage, labels its output as scripted, and never writes to results.csv.
4. **Rehearsal** of the full scenario set. Fix bugs.
5. **Pilot (real, small).** One unconstrained calibration run on Exercise A (budgets too large to
   bind) to measure demand per role per window and steps to a good speedup; set T, the summit and
   the window cap; then one real run each of scenarios 1 and 3. Report per run: tokens, wall time,
   windows, speedup, and a projection of runs per 5-hour block and per week. **ASK** Pietro to
   glance at `/usage` once after the pilot, then **ASK** how many repeats to run (target 3,
   minimum 1 full repeat).
6. **Full runs** with `run-all`, repeat-major. Commit results after each completed repeat.
7. **Results page** `docs/demo/results.html` (section 6), built from results.csv and run folders
   only.
8. **PR.** **ASK** Pietro to approve the push, then push and open a PR to main titled
   "Demo Day: five budget scenarios, measured": what was built, how to reproduce (rehearsal and
   real), results table, limitations (model, repeats, task, Windows timing noise, aborted runs),
   links to the page and DECISIONS.md. Use `gh pr create` if available, else give him the GitHub
   compare link.
9. **Hand-back.** `docs/demo/README.md` (reproduce in 10 lines), and a short message to Pietro:
   what ran, the headline numbers with run counts, and the next step in section 6.

## 6. The results page

- `docs/demo/preview_toy.html` is the toy preview Pietro showed in class ("Rebbi Demo of Demo",
  synthetic data). Reuse its layout, style tokens, light and dark themes and components: setup
  strip, scenario tabs with rules and a budget table (Agent, Budget / window, Shareable (% of
  budget) shown as "35% · 6k", Avg new work / window), replay controls, the hill with milestone
  flags, the token-flow diagram (Rebbi hub, loans as moving dots, expired tokens to a bin),
  per-agent budget bars, event log, race chart, results table. Do not change preview_toy.html.
- Replace the simulation with the real per-window data embedded as JSON (no external fetch; one
  self-contained file that opens by double-click). Where real data lacks a field the toy showed,
  drop that element rather than fake it.
- Title "Rebbi Demo". A measured-results banner states complete runs per scenario, model(s), task
  names, dates and "Measured on Claude Pro in subscription mode". Keep a limitations section.
  Missing cells say "not run". With more than one repeat, show the median and the range.
- **Next step for Pietro** (put it in your hand-back message): open claude.ai, start a new chat in
  the AI Studio project, attach `docs/demo/results.html` and `runs/demo/results.csv`, and ask
  Claude to publish the results as an artifact. The HTML file also opens locally as a backup.

## 7. Done means

- Branch `demo-scenarios` pushed, PR open, all tests passing, `rebbi check` PASS on every counted
  run.
- `runs/demo/manifest.csv`, `results.csv` and `table.md` committed; no transcripts with secrets;
  no token anywhere in the diff.
- `docs/demo/results.html`, `PLAN.md`, `DECISIONS.md`, `README.md` committed.
