# Outcome: H1

mode budget-only, need stated in the prompt 30000

| Criterion | Result | Evidence |
| --- | --- | --- |
| C1 found and called Rebbi from the doc alone | PASS | 4 tool calls in the trace: get_budget, post_handoff, settle, get_budget |
| C2 one loan per request, no double booking | PASS | 1 decisions (1 LEND), 1 loans booked, request_ids ['auditor-01-depaudit-1'] |
| C3 result use: budget.json matches the ledger | PASS | every loan's id, tokens and lender found |
| C7 claims no more than the ledger lent | PASS | ledger lent 25000; no over-claim |
| C4 settled every loan it received | PASS | statuses: 1=settled |
| C5 ledger invariants hold | PASS | PASS |
