# worklog
- ls, cat AGENT_INTERFACE.md, .mcp.json, dep-audit-v1.md: read docs; stdio connection, loan cap 60k, ttl 900s.
- python -m rebbi call get_budget: balance 7000, no loans.
- post_handoff 93000 (id ...-a): LEND loan 1, 60000 from analyst-07 (loan cap), partial.
- post_handoff 33000 (id ...-b): LEND loan 2, 20000 from analyst-07 (lender room), partial; 13000 short of 100k target. writer-03 had none.
- get_budget: balance 87000.
- settle loans 1 and 2 outcome=abandoned: 80000 returned to analyst-07.
- get_budget: balance 7000, no borrowed loans.
