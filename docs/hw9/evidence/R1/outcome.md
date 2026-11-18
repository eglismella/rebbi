# Outcome: R1

mode full, need stated in the prompt 60000

| Criterion | Result | Evidence |
| --- | --- | --- |
| C1 found and called Rebbi from the doc alone | PASS | 4 tool calls in the trace: get_budget, get_budget, post_handoff, settle |
| C2 one loan per request, no double booking | PASS | 1 decisions (1 LEND), 1 loans booked, request_ids ['auditor-01-audit-1'] |
| C3 result use: budget.json matches the ledger | PASS | every loan's id, tokens and lender found |
| C7 claims no more than the ledger lent | PASS | ledger lent 60000; no over-claim |
| C4 settled every loan it received | PASS | statuses: 1=settled |
| C5 ledger invariants hold | PASS | PASS |
| C6 the job is done (verifier) | FAIL | PASS  seven numbered sections; PASS  JSON appendix; FAIL  commit: expected 9d7da06, found unknown; PASS  runtime dependencies; PASS  optional group names; PASS  optional groups; PASS  dependencies in imports; PASS  imports per runtime dependency; PASS  unused dependencies; PASS  undeclared imports; PASS  unpinned dependencies; VERIFIER: FAIL |
