# worklog
- ls, cat AGENT_INTERFACE.md, .mcp.json, head/tail dep-audit-v1.md: Rebbi HTTP at 127.0.0.1:8765/mcp, bearer token; loan cap 60k, ttl 900s; audit report is 7 sections + JSON.
- python -c "import mcp,httpx": mcp 2.3.0 and httpx2 available in venv.
- Wrote rebbi_client.py (calls Rebbi tools over HTTP using the token in .mcp.json).
- get_budget: balance 7000, no loans.
- post_handoff 25000 (request_id auditor-01-depaudit-1): LEND loan 1, 25000 from analyst-07, expires 2026-11-18T04:13:22Z. (Need ~23k more than 7k own for a 30k job.)
- settle loan 1 done: status settled, returned_tokens 25000.
- get_budget: balance 7000 again.
- Wrote budget.json. Did not start the audit; report.md not written.
