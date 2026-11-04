# HW7 benchmark plan

Written on Nov 3, 2026, **before any benchmark run**. The cases are in `config/bench.toml` and the
repositories in `config/targets.toml`. If anything here changes after the runs start, the change is
listed at the bottom with its reason.

## The claim

When an agent's own token budget is too small for its job, Rebbi lets it borrow spare budget from idle
agents, so the job finishes and passes an independent check, and no lender drops below its reserve.

## The job

`dep-audit-v1` (`specs/dep-audit-v1.md`): audit the Python dependencies of one repository at a pinned
commit, then write a 7-section report with a JSON appendix. One agent, `auditor-01` (Claude Sonnet 5.5),
does the job with Read, Grep and Glob only. Two other agents, `analyst-07` and `writer-03`, are the
possible lenders.

## How a run is judged (fixed before the runs)

A run **succeeds** only if all three hold:

1. **Verifier PASS.** `rebbi/verify.py` compares the report with the repository's answer key, 11 checks,
   and fails closed. The agent saying "done" does not count.
2. **Ledger PASS.** `python -m rebbi check`: no tokens created or lost, every loan closed.
3. **Reserves intact.** No loan left its lender below the reserve it published.

**Main number:** success rate per arm (successes out of runs).
**Costs, recorded for every run:** auditor tokens, fleet tokens (every agent, including what the lenders
spend talking to Rebbi), wall-clock seconds, the dollar cost the Claude CLI reports for the auditor, and
how many loans were made and how much went back.

## The three arms

Every arm runs the same job, the same repositories and the same fleet. The fleet's total budget is
the same in every arm.

| Arm | What happens |
|---|---|
| `baseline` | Rebbi is off. The auditor has only its own 7,000 tokens, enough for about one model call. |
| `upfront` | Rebbi is off. Before the job starts, the owner moves the job's expected cost (the same figure the auditor is told: 60,000 tokens) from the lender with the most spare room to the auditor. This is a manager who knew the cost in advance. Moved tokens are not given back. |
| `rebbi` | Rebbi is on. The auditor asks Rebbi for budget over MCP when it needs it, and gives back what it did not use. |

`baseline` shows the problem. `upfront` is the fair, simpler alternative: it tells us whether Rebbi
matches a well-informed manager, and what Rebbi costs on top.

## The cases

| Case | Kind | Split | Why it is here |
|---|---|---|---|
| sqlite-utils-3.38 | ordinary | tuning | The HW6 demo job |
| csvs-to-sqlite-1.3.1 | ordinary | tuning | Smallest package; one import name differs from its package name |
| sqlite-utils-3.30 | ordinary | fresh | Older release of the demo repo, with a different trap |
| db-to-sqlite-1.5 | ordinary | fresh | Simplest dependency picture |
| llm-0.12 | **hard** | fresh | Largest package; several name traps; `pip` is run but not imported |
| no-lender-room | **failure** | tuning | Nobody has spare budget; Rebbi must refuse cleanly |

**How the repositories were chosen:** small Python packages by one author, Simon Willison, whose
`setup.py` lists the dependencies plainly, because the answer-key script reads only that format. The
first five that worked were kept. datasette 0.65.1 was dropped because it bundles another library, so
its right answer is unclear. Every answer key was made by `scripts/make_answer_key.py` and then checked
by hand against the source.

**Runs:** 3 per case per arm, because the model is random. The arms take turns (case 1 × all arms,
then case 2, and so on), and the whole list repeats 3 times. That is 5 × 3 × 3 + 1 × 2 × 3 = 51 runs.

## Find a limit, change one thing, retest

1. **Stress, on the tuning cases only.** Change one thing at a time:
   - a wrong cost hint: the auditor is told 15,000 tokens instead of 60,000
   - no cost hint at all
   - a scarce lender: `analyst-07` has only 20,000 tokens to spare
2. **Change one thing** in Rebbi, chosen from what broke in step 1. The change and its reason will be
   written here before the retest.
3. **Retest** the stress setting that broke, with the same number of runs, on the tuning cases (did the
   fix work where we looked?) and on the fresh cases (does it hold where we did not look?).

## How to repeat this

```bash
.venv/Scripts/python -m pip install -e ".[test]"
.venv/Scripts/python -m rebbi fetch-target --all
.venv/Scripts/python -m rebbi.bench --label main
```

Each run writes `runs/<time>-<arm>/`. The benchmark writes `runs/bench/<time>-<label>/` with
`results.csv` (one row per run), `table.md` (the summary) and `command.txt`.

## Changes after the runs started

**Nov 3, main run** (`runs/bench/20261103-171109-main`, 51 runs). Success: baseline 0/15, upfront 15/15,
rebbi 4/15 on the ordinary and hard cases; no reserve broke and every ledger check passed. In all 11
failed rebbi runs the auditor started the audit before asking Rebbi. Its first call cost about 5,500 of
its 7,000 tokens; the low-budget warning came after that call, and the next call, the one that would
have carried the request, needed more input than was left, so it was refused. Every rebbi run that
asked first passed.

**Not in this plan before the run:** while adding the new repositories, the cost hint changed from
"Past runs of dep-audit-v1 on this commit used up to 60,000 tokens" (HW6) to "Past runs of dep-audit-v1
used up to 60,000 tokens", because the four new repositories were never measured. A check afterwards on
sqlite-utils-3.38 (10 real runs, the two wordings alternating) found: HW6 wording, borrowed first 5/5 and
passed 5/5; new wording, borrowed first 1/5 and passed 1/5. So whether Rebbi helps here hangs on whether
the agent decides to ask first, and a few words in the prompt flip that decision. Runs:
`runs/20261103-172327-rebbi` to `runs/20261103-172730-rebbi` (`scripts/wording_check.py`).

**The one change, chosen Nov 3 before the retest: auto-borrow.** When a model call's input is more than
the auditor's balance, the harness (or, with an API key, the gateway) asks Rebbi for a loan on the
auditor's behalf before refusing the call. It asks for what the job is still expected to need (the hint
minus what is already used), and at least enough for this call and one more of its size. The usual rules
apply: the most-room lender first, the loan cap, no lender below its reserve, unspent tokens go back when
the job ends. Nothing else changes: same prompt (the new wording, the one that failed), same budgets,
same cases. Reason: borrowing should not depend on the model choosing to ask before its first call.

The change was designed from the tuning cases: the failed sqlite-utils-3.38 runs and the wording check
on sqlite-utils-3.38. One fresh-case log was opened while diagnosing (a passing llm-0.12 run, to see what
asking first looks like); no fresh-case failure was studied.

**Retest:** the rebbi arm only, since the change touches nothing in baseline or upfront: all 6 cases,
3 runs each (18 runs), compared with the main run's rebbi and upfront arms. Tuning cases show whether the
fix works where it was designed; fresh cases show whether it holds where it was not.

**Nov 3, retest** (`runs/bench/20261103-204142-retest-autoborrow`, 18 runs). Rebbi with auto-borrow passed
15/15 ordinary and hard runs (tuning 6/6, fresh 9/9), up from 4/15 in the main run; no-lender-room still
0/3, refused cleanly. No reserve broke and every ledger check passed. Auto-borrow fired in 11 of the 15
runs; in the other 4 (llm-0.12 three times, sqlite-utils-3.38 once) the agent asked first on its own.
(Corrected Nov 4: this line first said "12 of the 15" and "the other 3"; the `auto_requests` column of
`results.csv` shows 11.)

Cost, against the main run's upfront arm (medians): auditor 25,704 tokens against 17,317; fleet 34,430
against 17,317; 31 s against 17 s. Two causes. (1) Rebbi's fixed overhead: the two lenders spend about
8,700 tokens publishing their reserves. (2) A side effect of the change: the old low-budget warning is
added to the conversation after the first call, auto-borrow then lends before the model reads it, and
the model, reading a warning that is no longer true, spends one more call (about 7,700 tokens) asking
for a loan it does not need. Fixing that would be a second change, so it is left as a known limit.

**Nov 3, stress runs** (36 runs). Order changed from the plan: the stress runs came after the change,
because the main run had already shown the limit, so they test the system as it now stands (with
auto-borrow). As planned, tuning cases only (sqlite-utils-3.38, csvs-to-sqlite-1.3.1), upfront against
rebbi, 3 runs each; one setting changed at a time.

| Setting | Folder | upfront | rebbi |
|---|---|---|---|
| Wrong hint: told 15,000 | `runs/bench/20261103-205606-stress-hint15k` | 4/6 | 6/6 |
| No hint | `runs/bench/20261103-221726-stress-nohint` | 0/6 | 6/6 |
| Scarce lender: analyst-07 has 20,000 spare | `runs/bench/20261103-222149-stress-scarce` | 6/6 | 3/6 |

- With a wrong or missing hint, upfront moves too little (15,000) or nothing, and fails when the job costs
  more. Rebbi does not need the number: auto-borrow asks when a call cannot be covered.
- With a scarce lender, Rebbi loses (all 3 failures on sqlite-utils-3.38). analyst-07 spent about 4,400
  of its 20,000 spare tokens publishing its reserve, so Rebbi could lend only 15,636; the auditor then
  spent one call (about 9,400 tokens) on the stale-warning request, and ended about 2,200 tokens short.
  Upfront moved the whole 20,000 with no overhead and passed. Both costs named in the retest are what
  lost these runs, and each abandoned job used up 15,636 of the lender's tokens.
- One upfront run (`runs/20261103-205842-upfront`, wrong hint) took 4,527 s: a single model call took
  74 minutes to return. That is the model service, not Rebbi (Rebbi was off), and it failed on budget
  like the other wrong-hint upfront failure; the tables report medians and ranges, so it shows only in
  the time range.
