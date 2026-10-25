# Rebbi

Lends spare token budget between AI agents in one fleet. An agent about to run
out mid-job calls `post_handoff` over MCP; the broker finds an agent with
capacity above its reserve, books the loan atomically in the ledger, and
replies `LEND` (or `CANNOT_MOVE` with the reason each candidate gave).

HW6 MVP scope: lending only. Hand-off, WAIT and forecasting come later.

## Run it

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[test]"
.venv/Scripts/python -m rebbi fetch-target       # the repo auditor-01 audits, at its pinned commit
.venv/Scripts/python -m rebbi seed --reset       # fresh ledger from config/scenario.toml
.venv/Scripts/python scripts/smoke_mcp.py        # auditor-01 asks for 30k tokens over MCP
.venv/Scripts/python -m rebbi status             # agents, loans, broker decisions
.venv/Scripts/python -m rebbi check              # ledger invariants: PASS or FAIL
.venv/Scripts/python -m pytest
```

The HTTP side (for the gateway and for watching the demo):

```bash
REBBI_DB=rebbi.db .venv/Scripts/uvicorn rebbi.api:app_from_env --factory --port 8700
```

## Layout

| Path | What it holds |
| --- | --- |
| `config/scenario.toml` | Every number: budgets, reserves, declared demand, loan cap and expiry, the audit target. Stand-ins until Pietro's spec. |
| `rebbi/ledger.py` | SQLite ledger, the one home for balances, reserves, loans, usage and decisions. Append-only entries; balances are sums. |
| `rebbi/rules.py` | Who can lend and how much: `lendable = balance - reserve - declared demand`, capped per loan. |
| `rebbi/broker.py` | `post_handoff`, `report_headroom`, `settle`, `budget`. Expires loans before every decision. |
| `rebbi/mcp_server.py` | Agent-facing MCP server, one stdio process per agent; identity comes from `REBBI_AGENT_ID`, never from a tool argument. |
| `rebbi/api.py` | FastAPI: `/gateway/check`, `/gateway/usage`, and read-only `/agents`, `/loans`, `/decisions`, `/invariants`. |

## Ledger invariants

`python -m rebbi check` fails if any of these breaks:

- The fleet total equals budgets granted minus tokens used: loans never create or lose tokens.
- Each loan's lender and borrower entries cancel out.
- No loan left its lender below the reserve it had published.
- No loan is still active after its expiry, and none returned more than it lent.
