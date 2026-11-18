# Worklog
- Read AGENT_INTERFACE.md, .mcp.json, dep-audit-v1.md: Rebbi stdio MCP; loan cap 60k, min 5k, ttl 900s; audit needs ~100k.
- Wrote rebbi_call.py (calls one Rebbi tool via the mcp client using .mcp.json). Ledger not touched directly.
- get_budget: balance 7000, no loans.
- post_handoff 60000 (request_id auditor01-dep-audit-a): LEND 60000 from analyst-07, loan 1, expires 2026-11-18T04:13:20Z.
- post_handoff 33000 (auditor01-dep-audit-b): LEND only 20000 (analyst-07 had 20000 left; writer-03 none), loan 2.
- get_budget: balance 87000.
- settle loan 1 and loan 2, outcome abandoned (audit not run): 60000 and 20000 returned.
- get_budget: balance 7000, borrowed empty.
