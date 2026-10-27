# Hand-offs for Pietro and Nitya

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

**Facts for the paragraph and the script.**

- Agent-facing capability: an agent about to run out of token budget mid-job calls Rebbi's MCP tool
  `post_handoff` itself; Rebbi books a loan from an agent with spare capacity above its published
  reserve, and the agent carries on. Lenders publish their own reserve with `report_headroom`.
- The check: the same job on the same budgets, without and with Rebbi. Without, the auditor stops and
  the verifier FAILs the report. With Rebbi, it borrows, finishes, and the verifier PASSes every check
  against the answer key. A second check confirms the ledger: no tokens created or lost, no lender
  below its reserve, every loan closed.
- Current limitation (pick one for the video): Rebbi only lends. A job blocked by a missing tool or
  permission still fails, because hand-off is not built yet. Other true limitations: three agents on
  one machine; the budget numbers are calibrated for this one job.

## Pietro: lending rules (task 3) and numbers (task 4), then the video (tasks 7, 9, 12, 15)

**The rules as built** (`rebbi/rules.py`, `rebbi/ledger.py`). Confirm or change each:

1. Lendable = balance − reserve − the demand the owner declared for this window. Never below zero.
2. The lender with the most room is asked first; if its capacity is taken in the meantime, the next one.
3. One loan is capped at `max_loan_tokens`; offers under `min_loan_tokens` are not booked.
4. A loan stops after `loan_ttl_s` seconds.
5. Partial loans: asking above the cap returns the cap, not a refusal.
6. Repayment: when a loan closes, what the borrower has not spent goes back, up to the loan amount.
   The borrower's own tokens count as spent first, which favours the lender.

**The numbers** all live in `config/scenario.toml`. The model spends more tokens than intuition says:
each call re-sends the whole conversation, so a call late in the job can cost tens of thousands of
tokens. Use the first measurement run: `python -m rebbi.calibrate runs/<run>` prints what the full
audit cost and proposes budgets so the auditor stalls about halfway, `analyst-07` can cover the rest,
and `writer-03` has nothing to lend. Lenders also spend part of their own budget publishing their
reserve, which leaves less to lend.

**The video.** `python -m rebbi.demo` runs the baseline, then Rebbi, then prints a side-by-side
table. Every line in the footage is also saved in each run's `console.log`. Shot by shot:

| Seconds | Show | Lines to look for in `console.log` |
| --- | --- | --- |
| 0–8 | The fleet and budgets | the first `fleet run ...` line |
| 8–18 | Baseline stops | `auditor-01 stopped mid-job`, then `verifier FAIL` |
| 18–40 | Rebbi on: warning, ask, loan, finish | `warning auditor-01`, `-> rebbi.post_handoff`, `<- LEND ... (writer-03: no room above its reserve)`, `settled loan` |
| 40–52 | The check | `verifier PASS` lines, `ledger invariants PASS`, and the demo's final table |
| 52–60 | The limitation | a title card |

The runs take minutes, so speed up the middle and cut to the lines above.

**Rough cut before the real run.** `docs/rehearsal/demo-output.txt` is the whole demo, run against a
scripted stand-in for the model because no working Claude credential exists yet. Every line in the
table above appears in it, in the same order, so the cut, captions and timing can be built now. It is
not footage for the submission: its replies are hard-coded and every banner says "REHEARSAL, scripted
model, not Claude". The rubric scores mockups and hard-coded results at zero, so swap in the real run's
output once Eglis records it. The real run's lines look the same except that the model's tool calls and
token counts vary, and it takes minutes rather than seconds.
