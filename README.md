# Rebbi

Lends spare token budget between AI agents in one fleet. An agent about to run
out mid-job calls `post_handoff` over MCP; the broker finds an agent with
capacity above its reserve, books the loan atomically in the ledger, and
replies `LEND` (or `CANNOT_MOVE` with the reason each candidate gave).

HW6 MVP scope: lending only. Hand-off, WAIT and forecasting come later.

## Run the demo

Put one credential in `.env` (git-ignored). The harness picks the mode from it, or force one with `--auth`:

| `.env` line | Mode | Who meters and enforces budgets |
| --- | --- | --- |
| `ANTHROPIC_API_KEY=...` (a Console key with credits) | `api-key` | The gateway. Each agent gets a stand-in key, `rebbi-<agent_id>`, that works only through it; only the gateway holds the real key. |
| `CLAUDE_CODE_OAUTH_TOKEN=...` (from `claude setup-token`, your own Claude plan) | `subscription` | The harness. Each agent's unmodified Claude Code binary signs in with your token and calls Anthropic directly; the harness meters every call from the stream and stops an agent at the first call its balance cannot cover. Rebbi never proxies these requests. |

`python scripts/check_api.py` says which mode works with what is in `.env`.

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[test]"
.venv/Scripts/python -m rebbi fetch-target          # the repo auditor-01 audits, at its pinned commit
.venv/Scripts/python -m rebbi.demo                  # baseline, then Rebbi, then the side-by-side check
.venv/Scripts/python -m rebbi.fleet --mode baseline # one run: no Rebbi, auditor-01 is refused once its budget runs short
.venv/Scripts/python -m rebbi.fleet --mode rebbi    # one run: auditor-01 borrows over MCP and finishes
```

`docs/demo/real-run-1.txt` to `-3.txt` are three real runs of `python -m rebbi.demo`, one after another.

No credentials? `python -m rebbi.demo --rehearsal` runs the same harness, gateway, MCP server, ledger
and verifier against `rebbi/scripted_model.py`, a stand-in whose replies and report are hard-coded.
Every line and run folder says it is scripted, and it is never evidence.

Each run writes `runs/<time>-<mode>/`: `console.log` (what the video shows), one transcript per agent,
`report.md`, `verify.txt`, the run's own `rebbi.db`, and `summary.json`. `--budget auditor-01=N`
overrides one agent's budget for a run.

To set the numbers from what the model really spends, measure once with a budget too big to run out,
then let the helper propose consistent values for `config/scenario.toml`:

```bash
.venv/Scripts/python -m rebbi.fleet --mode rebbi --budget auditor-01=3000000
.venv/Scripts/python -m rebbi.calibrate runs/<that run>
```

Without the model, for the ledger and MCP alone:

```bash
.venv/Scripts/python -m rebbi seed --reset          # fresh ledger from config/scenario.toml
.venv/Scripts/python scripts/smoke_mcp.py           # auditor-01 asks for 30k tokens over MCP
.venv/Scripts/python -m rebbi status                # agents, loans, broker decisions
.venv/Scripts/python -m rebbi check                 # ledger invariants: PASS or FAIL
.venv/Scripts/python -m rebbi.verify runs/<run>/report.md
.venv/Scripts/python -m pytest
```

## Layout

| Path | What it holds |
| --- | --- |
| `config/scenario.toml` | Every number: budgets, reserves, declared demand, loan cap and expiry, the audit target. Stand-ins until Pietro's spec. |
| `rebbi/ledger.py` | SQLite ledger, the one home for balances, reserves, loans, usage and decisions. Append-only entries; balances are sums. |
| `rebbi/rules.py` | Who can lend and how much: `lendable = balance - reserve - declared demand`, capped per loan. |
| `rebbi/broker.py` | `post_handoff`, `report_headroom`, `settle`, `budget`. Expires loans before every decision. |
| `rebbi/mcp_server.py` | Agent-facing MCP server, one stdio process per agent; identity comes from `REBBI_AGENT_ID`, never from a tool argument. |
| `rebbi/gateway.py` | Pass-through for Claude API calls. Refuses a call unless the agent's ledger balance covers its input (counted with count_tokens); debits the tokens each call really used (input, cache writes, cache reads, output). Holds the only real API key. |
| `rebbi/fleet.py` | The demo harness: three Claude Agent SDK agents, the gateway beside them (or harness metering in subscription mode), a low-budget warning hook, verification and the ledger check after each run. |
| `rebbi/demo.py` | Baseline then Rebbi on the same budgets, then a side-by-side table: the evidence shot for the video. |
| `rebbi/calibrate.py` | Proposes scenario numbers from a measurement run. |
| `rebbi/scripted_model.py` | A hard-coded stand-in for the Claude API: the offline tests and `demo --rehearsal`. Never evidence. |
| `rebbi/verify.py` | Checks a report against the job template's answer key; fails closed. |
| `rebbi/api.py` | FastAPI read-only views: `/agents`, `/loans`, `/decisions`, `/invariants`. |
| `specs/dep-audit-v1.md` | The job template: what a finished audit must contain. Draft for Nitya. |
| `specs/answer-key-sqlite-utils-3.38.json` | The key the verifier checks against, drafted by `scripts/make_answer_key.py` from the pinned repo. |

## Ledger invariants

`python -m rebbi check` fails if any of these breaks:

- The fleet total equals budgets granted minus tokens used: loans never create or lose tokens.
- Each loan's lender and borrower entries cancel out.
- No loan left its lender below the reserve it had published.
- No loan is still active after its expiry, and none returned more than it lent.
