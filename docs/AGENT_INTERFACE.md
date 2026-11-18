# Rebbi agent interface

Rebbi lends spare token budget between AI agents in one fleet. An agent that will run out
of tokens before it finishes a job asks Rebbi for more. Rebbi finds another agent in the
fleet with unused budget above that agent's reserve, moves the tokens in a shared ledger,
and replies at once. When the job ends, the borrower settles the loan and whatever it did
not spend goes back to the lender.

This page is everything an agent, or the person wiring one up, needs to use Rebbi. It
covers what Rebbi offers, how to connect, each tool's inputs and outputs, the limits, a
shell command for agents without MCP tools, and one worked example. It describes Rebbi as of the commit you are reading.

## 1. What Rebbi offers, and what it does not

| Rebbi does | Rebbi does not (yet) |
| --- | --- |
| Lend tokens from agents with spare budget to an agent that is short | Move a job to another agent (hand-off), or queue a request to wait |
| Keep every balance, loan and decision in one ledger that never creates or loses tokens | Meter your model calls by itself: see section 5, "Metering" |
| Protect each lender's published reserve and declared demand | Check that an agent has the tools or scopes a job needs |
| Return a resent request's first answer instead of booking twice | Forecast how many tokens a job needs |

## 2. Connect

Rebbi is a [Model Context Protocol](https://modelcontextprotocol.io) server. It runs two ways,
and the four tools are the same in both.

**stdio (one server process per agent).** The client launches `rebbi-mcp` (or
`python -m rebbi.mcp_server`) with the agent's identity in its environment. No tool takes an
agent id, so an agent can only ever act as itself.

| Variable | Required | Meaning |
| --- | --- | --- |
| `REBBI_AGENT_ID` | yes | The agent this process speaks for. It must exist in the ledger. |
| `REBBI_DB` | yes | Path of the fleet's ledger (SQLite). Every agent of a fleet points at the same file. |
| `REBBI_SCENARIO` | yes, outside the repository | Path of the fleet file that holds the lending rules (section 5). |
| `REBBI_TRACE` | no | Append one JSON line per tool call (arguments, reply or error) to this file. |

**Streamable HTTP (one server for the whole fleet).** For agents on other machines, or
clients that cannot launch a local process. Each agent sends its own bearer token, and the
token decides which agent the request speaks for.

```bash
rebbi-mcp --http --host 127.0.0.1 --port 8765 \
  --db fleet/rebbi.db --scenario fleet/scenario.toml --tokens fleet/tokens.toml
# endpoint: http://127.0.0.1:8765/mcp   header: Authorization: Bearer <agent's token>
```

A request without a valid token gets HTTP 401 and never reaches the ledger. Use
`--host 0.0.0.0` only behind TLS (a reverse proxy) on a network you trust: tokens travel in
the header.

## 3. Set up a fleet (operator, once)

Python 3.11 or newer.

```bash
python -m venv .venv
.venv/bin/pip install "git+https://github.com/eglismella/rebbi"   # Windows: .venv/Scripts/pip
.venv/bin/rebbi init fleet          # fleet/scenario.toml, fleet/rebbi.db (seeded), fleet/tokens.toml
.venv/bin/rebbi client-config --dir fleet --agent auditor-01                # stdio entry
.venv/bin/rebbi client-config --dir fleet --agent auditor-01 --http http://127.0.0.1:8765/mcp
```

`client-config` prints an `mcpServers` block with absolute paths. Claude Code reads it from
`.mcp.json` in the project folder (or `claude --mcp-config <file>`); Claude Desktop and most
other MCP clients read the same shape.

The starter fleet has three agents. Edit `fleet/scenario.toml` to change agents, budgets,
reserves or rules, then `rebbi init fleet --force` (this starts the ledger over).

| Agent | Budget | Reserve | Declared demand | Lends | Role in the starter fleet |
| --- | ---: | ---: | ---: | --- | --- |
| auditor-01 | 7,000 | 0 | 0 | no | Short of budget for its job |
| analyst-07 | 180,000 | 80,000 | 20,000 | yes | Idle; can lend 80,000 |
| writer-03 | 100,000 | 70,000 | 30,000 | yes | Busy; nothing above its reserve |

Operator commands: `rebbi --db fleet/rebbi.db status` (agents, loans, decisions) and
`rebbi --db fleet/rebbi.db check` (ledger invariants, exit 1 on failure).

## 4. Tools

All replies are JSON objects (MCP structured content). Token counts are integers.

### `get_budget()`

Your own state. No inputs.

| Field | Meaning |
| --- | --- |
| `agent_id`, `owner` | Who you are, and who owns you |
| `balance` | Tokens you can spend now, loans included |
| `reserve_tokens` | What you will never lend |
| `expected_demand_tokens` | What your owner declared you need this window; also never lent |
| `will_lend` | Whether you lend at all |
| `lendable` | What others could borrow from you now: `max(0, balance - reserve - declared demand)`, or 0 if you do not lend |
| `borrowed`, `lent` | Your active loans: `loan_id`, `lender`, `borrower`, `tokens`, `status`, `expires_at`, `returned_tokens` |
| `limits` | The fleet's rules: `max_loan_tokens`, `min_loan_tokens`, `loan_ttl_s` (section 5) |

### `post_handoff(goal, budget_tokens, ...)`

Ask for tokens. The name comes from the planned hand-off feature; today it only lends.

| Input | Type | Default | Meaning |
| --- | --- | --- | --- |
| `goal` | string | required | What the tokens are for; logged with the decision |
| `budget_tokens` | int | required | Tokens you ask for; must be positive |
| `request_id` | string, up to 128 chars | `""` | Your id for this request; see idempotency below |
| `job_template`, `source_commit`, `context_ref` | string | `""` | Logged only |
| `requires_tools`, `requires_scopes` | list of strings | `[]` | Logged only: Rebbi does not check them |
| `deadline_s` | int | 0 | Logged only |

Reply when Rebbi lends:

| Field | Meaning |
| --- | --- |
| `decision` | `"LEND"`: the tokens are already in your balance |
| `loan_id` | Pass it to `settle` |
| `tokens` | What you got. It can be less than you asked: see `partial` |
| `partial` | `true` when `tokens` is less than `requested` |
| `shortfall_tokens` | `requested - tokens` (0 for a full loan) |
| `limit_reason` | Only when partial: `"loan cap"` (one loan cannot exceed `max_loan_tokens`) or `"lender room"` (the best lender had no more above its reserve) |
| `next_step` | Only when partial: what to do about the shortfall |
| `requested` | What you asked for |
| `from` | The lender |
| `expires_at` | UTC time when the loan's extra allowance stops |
| `lender_reserve_intact` | Always true: a loan never takes a lender below its reserve |
| `considered` | Every other agent, with `lendable` and the reason it was or was not used |
| `limits` | The fleet's rules, as in `get_budget` |
| `ignored_fields`, `note` | Only when you sent `requires_tools` or `requires_scopes`: Rebbi records them but does not check them |
| `decision_id` | The decision's id in the ledger |

Reply when it cannot: `decision: "CANNOT_MOVE"`, `requested`, `blocker` (why), `next_step`,
`considered`, `limits`, `decision_id` (and `ignored_fields`, `note` as above). Nothing is booked.

**Idempotency.** Resend a request with the same `request_id` and the same arguments, and you
get the first reply again with `replayed: true` (and the loan's current `loan_status`): never
a second loan. Use this when a reply was lost. The same `request_id` with different arguments
is an error. To ask again on purpose, use a new `request_id`. Without a `request_id`, every
call is a new request.

### `settle(loan_id, outcome="done")`

Close a loan you borrowed, once the job is done or abandoned (`outcome` is `"done"` or
`"abandoned"`). Unspent tokens go back to the lender, up to the loan amount: your own tokens
count as spent first. Reply: the loan (`loan_id`, `lender`, `borrower`, `tokens`, `status:
"settled"`, `expires_at`, `returned_tokens`) plus `outcome`. Settling a loan that is already
closed returns it with `already_closed: true`, so a resend is safe.

### `report_headroom(reserve_tokens, will_lend=true)`

For lenders: publish the reserve you will never lend, and whether you lend at all. Reply: your
`get_budget` fields without the loan lists.

### Errors

A refused call comes back as an MCP tool error (`isError: true`). Causes: an unknown agent; a
`request_id` over 128 characters or reused for a different request; `settle` on a loan that
does not exist or is not yours; an `outcome` other than `done` or `abandoned`. The error text
gives the reason, for example `Error executing tool settle: settle refused: no loan 999`.
Arguments of the wrong type are rejected with a validation message that names the field.

## 5. Permissions and limits

Values are those of the starter fleet (`[rules]` in the fleet file).

- **Identity.** stdio: fixed by `REBBI_AGENT_ID`. HTTP: fixed by the bearer token. An agent
  can read only its own budget and settle only its own loans.
- **Loan cap: 60,000 tokens per loan** (`max_loan_tokens`). Asking for more returns a `LEND`
  for at most the cap, or for what the best lender has room for, marked `partial: true` with
  the shortfall and the reason. Ask again with a new `request_id` for the rest.
- **Minimum loan: 5,000** (`min_loan_tokens`). A lender with less room than that is skipped.
- **Loan expiry: 900 seconds** (`loan_ttl_s`). After that the loan closes itself and any
  unspent part goes back; settle before then.
- **Lender protection.** Only `balance - reserve - declared demand` can be lent. The lender
  with the most room is asked first.
- **Metering.** Rebbi's ledger balance is what Rebbi enforces when your model calls go
  through Rebbi's gateway or harness (`rebbi.gateway`, `rebbi.fleet`). An outside client that
  calls its model directly is not metered by Rebbi: its balance changes only through loans.
  Lending, settling and the ledger checks work the same either way.
- **Scale.** One ledger file, one machine, SQLite with writes serialised. Fine for a fleet of
  tens of agents; not built for many fleets or high request rates.

## 6. Calling Rebbi from a shell

An agent without built-in MCP tools does not need to write a client. `rebbi call` makes one
call through the connection in `./.mcp.json` (stdio or HTTP) and prints the reply as JSON; a
refused call prints `{"error": "..."}` and exits 1.

```bash
rebbi call get_budget
rebbi call post_handoff '{"goal": "finish dependency audit", "budget_tokens": 30000, "request_id": "audit-42"}'
rebbi call settle '{"loan_id": 1}'
rebbi call get_budget --config /path/to/.mcp.json
```

If `rebbi` is not on your PATH, use `<python> -m rebbi call ...` with the Python that has Rebbi installed.

## 7. Example

A fresh starter fleet, as auditor-01 (replies trimmed only where marked).

```text
get_budget {}
-> {"agent_id": "auditor-01", "balance": 7000, "reserve_tokens": 0, "will_lend": false,
    "lendable": 0, "borrowed": [], "lent": [], ...}

post_handoff {"goal": "finish dependency audit", "budget_tokens": 30000, "request_id": "audit-42"}
-> {"decision": "LEND", "loan_id": 1, "tokens": 30000, "requested": 30000, "from": "analyst-07",
    "expires_at": "2026-11-18T04:08:28+00:00", "lender_reserve_intact": true,
    "considered": [{"agent": "analyst-07", "lendable": 80000, "reason": "can lend 30000"},
                   {"agent": "writer-03", "lendable": 0, "reason": "no room above its reserve"}],
    "partial": false, "shortfall_tokens": 0,
    "limits": {"max_loan_tokens": 60000, "min_loan_tokens": 5000, "loan_ttl_s": 900},
    "decision_id": 1}

post_handoff {"goal": "finish dependency audit", "budget_tokens": 100000, "request_id": "audit-43"}
-> {"decision": "LEND", "loan_id": 2, "tokens": 50000, "requested": 100000, "from": "analyst-07",
    "partial": true, "shortfall_tokens": 50000, "limit_reason": "lender room",
    "next_step": "This loan covers 50000 of the 100000 tokens you asked for: that is all the best
    lender has above its reserve. Ask again with a new request_id for the rest, or plan the job
    around the shortfall.", ...}

settle {"loan_id": 1, "outcome": "done"}
-> {"loan_id": 1, "lender": "analyst-07", "borrower": "auditor-01", "tokens": 30000,
    "status": "settled", "returned_tokens": 30000, "outcome": "done", ...}
```

The same calls from Python, with the `mcp` package Rebbi installs:

```python
import asyncio
from mcp import Client, StdioServerParameters

params = StdioServerParameters(command="rebbi-mcp", env={
    "REBBI_AGENT_ID": "auditor-01", "REBBI_DB": "fleet/rebbi.db", "REBBI_SCENARIO": "fleet/scenario.toml"})

async def main():
    async with Client(params) as rebbi:
        reply = (await rebbi.call_tool("post_handoff", {"goal": "audit", "budget_tokens": 30000,
                                                         "request_id": "audit-42"})).structured_content
        if reply["decision"] == "LEND":
            ...  # do the job, then:
            await rebbi.call_tool("settle", {"loan_id": reply["loan_id"]})

asyncio.run(main())
```

Over HTTP, replace `params` with
`streamable_http_client("http://127.0.0.1:8765/mcp", http_client=httpx2.AsyncClient(headers={"Authorization": "Bearer <token>"}))`
from `mcp.client.streamable_http` (and `import httpx2`).

## 8. Read-only HTTP views (operators)

`REBBI_DB=fleet/rebbi.db REBBI_SCENARIO=fleet/scenario.toml uvicorn rebbi.api:app_from_env --factory --port 8700`
serves `/agents`, `/loans`, `/decisions` and `/invariants` as JSON. It has no authentication:
keep it on localhost.
