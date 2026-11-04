# Hand-offs for Pietro and Nitya

**HW7 (due Nov 4, 11:59pm): one check each, results to Eglis by 9pm.**
Pietro: [check our results, from raw logs to report](bench/tasks/pietro.md).
Nitya: [check the answer key for the hardest repository](bench/tasks/nitya.md).
The rest of this page is the HW6 hand-off.

What the code already does, what each of you decides, and where it goes. Times and owners follow
the work plan's task tracker. Nothing here needs you to run code; edit the files on GitHub or send
the change to Eglis.

## Nitya: verification (task 5) and the written submission (tasks 8, 11, 16, 17)

**Review two drafts.** Both were generated from the pinned repo, sqlite-utils 3.38 (commit `9d7da06`).

- `specs/dep-audit-v1.md` is the job template: the seven sections a finished audit must contain, and
  the pass criteria. The agent's prompt is built from it, so a change here changes what the agent is asked.
- `specs/answer-key-sqlite-utils-3.38.json` is what the verifier checks against. Spot-check it against
  `setup.py` and the imports in `sqlite_utils/` on GitHub:
  - 6 runtime dependencies; only `click-default-group` has a version constraint (`>=1.2.3`).
  - 5 optional groups: test, docs, mypy, flake8, tui.
  - Which files import each dependency (for example `pluggy`: `hookspecs.py` and `plugins.py`).
  - 5 undeclared imports (numpy, pandas, pysqlite3, sqlean, sqlite_dump), all inside
    `try / except ImportError`, so optional. This is the trap: an agent that calls them required, or
    misses them, fails. `trogon` is not on the list because the `tui` extra declares it.

The verifier fails closed: a missing section, a missing JSON appendix or any wrong value is a FAIL.

**Your review is applied** (Oct 27). The verifier now also checks the commit (the full hash or at least
7 characters of it), the optional group names on their own (a made-up empty group failed nothing
before), and the dependency names in `imports` (a made-up dependency with no files likewise). The
template now asks for the commit in the JSON appendix, package names only in section 3, undeclared
modules exactly as imported in section 5, and at least one recommendation in section 7. One thing
kept on top of your suggestion: optional-group packages are compared by name, so `black>=24.1.1` still
counts as `black` if the model adds the version anyway; runtime dependencies are still checked with
their constraints. There are now 11 checks, and real reports pass all of them.

**Facts for the paragraph and the script.**

- Agent-facing capability: an agent whose token budget will not cover its job calls Rebbi's MCP tool
  `post_handoff` itself; Rebbi books a loan from an agent with spare capacity above its published
  reserve, and the agent does the job. What it does not spend goes back to the lender when the job ends.
  Lenders publish their own reserve with `report_headroom`.
- What the real runs show (`docs/demo/real-run-3.txt`, Claude Sonnet 5.5, Oct 27, current settings):
  auditor-01 has 7,000 tokens and is told past audits took up to 60,000. Without Rebbi it makes one
  call, then its next call (10,237 tokens of input) is refused, and the verifier FAILs: no report. With
  Rebbi it asks for 60,000 before starting, analyst-07 lends it (writer-03 is skipped: no room above
  its reserve), it finishes in about 35 seconds, the verifier PASSes all 11 checks, and 32,484 unspent
  tokens go back to analyst-07. In `real-run-2.txt` the first loan ran low mid-job, the harness warned
  auditor-01, and it borrowed a second time on its own. All three saved runs went as designed.
- The check: the same job on the same budgets, without and with Rebbi. A second check confirms the
  ledger: no tokens created or lost, no lender below its reserve, every loan closed.
- Current limitation (pick one for the video): Rebbi only lends. A job blocked by a missing tool or
  permission still fails, because hand-off is not built yet. Other true limitations: three agents on
  one machine; the budget numbers are calibrated for this one job; auditor-01 knows how much to ask
  because we tell it what past audits cost (there is no forecasting yet); budgets are enforced per
  model call, so a call whose input is covered may overdraw by its output.

## Pietro: lending rules (task 3) and numbers (task 4), then the video (tasks 7, 9, 12, 15)

**The rules as built** (`rebbi/rules.py`, `rebbi/ledger.py`). Confirm or change each:

1. Lendable = balance − reserve − the demand the owner declared for this window. Never below zero.
2. The lender with the most room is asked first; if its capacity is taken in the meantime, the next one.
3. One loan is capped at `max_loan_tokens`; offers under `min_loan_tokens` are not booked.
4. A loan stops after `loan_ttl_s` seconds.
5. Partial loans: asking above the cap returns the cap, not a refusal.
6. Repayment: when a loan closes, what the borrower has not spent goes back, up to the loan amount.
   The borrower's own tokens count as spent first, which favours the lender.
7. Enforcement, added after the first real runs: a model call goes ahead only if the agent's balance
   covers the call's input. Its output is not known in advance, so it may overdraw by that much.

**The numbers** all live in `config/scenario.toml`, now calibrated from real runs; its header says
why each one is what it is. What the measurements showed: the real audit is only 2 to 5 model calls,
17,000 to 50,505 tokens in all, because each call re-sends the whole conversation and the model runs
several searches at once. So a "stalls halfway" budget cannot work: the auditor's second call costs the
same whether it borrows or writes the whole report, and no budget allows one and stops the other.
auditor-01 therefore gets 7,000 tokens, enough for the one call in which it asks Rebbi, not enough
for a second, and is told past audits took up to 50,000 so it asks for enough. A mid-job warning still
fires if a loan runs low. analyst-07 has 180,000 and writer-03 exactly its reserve plus declared
demand. `python -m rebbi.calibrate runs/<run>` proposes numbers from any measurement run.

**The video.** `python -m rebbi.demo` runs the baseline, then Rebbi, then prints a side-by-side
table. Every line in the footage is also saved in each run's `console.log`. Shot by shot:

| Seconds | Show | Lines to look for in `console.log` |
| --- | --- | --- |
| 0–8 | The fleet and budgets | the first `fleet run ...` line |
| 8–18 | Baseline stops | `refused: next call needs 10237 input tokens, 2808 left`, `stopped mid-job`, then `VERIFIER: FAIL` |
| 18–40 | Rebbi on: ask, loan, finish, repay | `-> rebbi.post_handoff {... "budget_tokens": 60000 ...}`, `<- LEND 60000 from analyst-07 (...; writer-03: no room above its reserve)`, `says: ## 1. Scope`, `settled loan 1: ... 32484 returned to analyst-07` |
| 40–52 | The check | `verifier PASS` lines, `ledger invariants PASS`, and the demo's final table |
| 52–60 | The limitation | a title card |

The whole demo takes about 45 seconds: the baseline about 5, Rebbi about 35, mostly the model
writing the report. `docs/demo/real-run-3.txt` is the full output of a real run on the current
settings, so the rough cut, captions and timing can be built from it now; the numbers quoted above come
from it. Eglis's screen capture of the same command is the footage. Each real run differs a little
(how much it borrows, how much goes back, sometimes a second loan), so match captions to the run
actually recorded.
