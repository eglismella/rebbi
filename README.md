# Rebbi

**Agents and builders: start with [docs/AGENT_INTERFACE.md](docs/AGENT_INTERFACE.md).** It covers
connecting over MCP (stdio or HTTP with per-agent tokens), each tool's inputs and outputs, the
limits, and a worked example. Install: `pip install "git+https://github.com/eglismella/rebbi"`,
then `rebbi init fleet`.

Lends spare token budget between AI agents in one fleet. An agent about to run
out mid-job calls `post_handoff` over MCP; the broker finds an agent with
capacity above its reserve, books the loan atomically in the ledger, and
replies `LEND` (or `CANNOT_MOVE` with the reason each candidate gave).

HW6 MVP scope: lending only. Hand-off, WAIT and forecasting come later.

Auto-borrow (added in HW7, `docs/bench/PLAN.md`): with Rebbi on, a model call the auditor's balance
cannot cover no longer simply fails. The harness, or the gateway, first asks Rebbi for a loan on the
auditor's behalf, so borrowing no longer depends on the agent remembering to ask before it starts.

Retries (added in HW8): `post_handoff` takes an optional `request_id`. Resending the same request
with the same id returns the first decision, marked `replayed`, instead of booking a second loan; the
same id with a different request is refused. `settle` is safe to resend too. Testing Rebbi inside
Nanda Town found the gap: when Town dropped Rebbi's reply or delivered a request twice, Rebbi booked
two loans for one job and left one open, while `rebbi check` still passed.

Outside agents (added in HW9, `docs/hw9/RESULTS.md`): Rebbi installs from GitHub with a starter
fleet (`rebbi init`), serves MCP over stdio or over HTTP with one bearer token per agent, logs every
call with `REBBI_TRACE`, and has `rebbi call` for agents with only a shell. Replies now say when a
loan is partial and why, carry the fleet's limits, and refusals give their reason. Five cold-start
runs by fresh agent sessions, working from `docs/AGENT_INTERFACE.md` alone, all borrowed, used and
settled correctly.

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
.venv/Scripts/python -m rebbi.video_demo                  # baseline, then Rebbi, then the side-by-side check
.venv/Scripts/python -m rebbi.fleet --mode baseline # one run: no Rebbi, auditor-01 is refused once its budget runs short
.venv/Scripts/python -m rebbi.fleet --mode rebbi    # one run: auditor-01 borrows over MCP and finishes
```

`docs/demo/real-run-1.txt` to `-3.txt` are three real runs of `python -m rebbi.video_demo` on Oct 27. In the
first two the auditor was told past audits took up to 50,000 tokens; the third uses the current 60,000.

No credentials? `python -m rebbi.video_demo --rehearsal` runs the same harness, gateway, MCP server, ledger
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

## The HW7 benchmark

`docs/bench/PLAN.md` is the plan, written before any benchmark run: the claim, the arms, the cases and
what counts as success. Three arms run the same job on the same fleet: `baseline` (Rebbi off),
`upfront` (Rebbi off, but the job's expected cost is moved to the auditor before it starts) and `rebbi`.

```bash
.venv/Scripts/python -m rebbi fetch-target --all             # the five repos in config/targets.toml
.venv/Scripts/python -m rebbi.bench --label main             # every case in config/bench.toml, every arm, 3 runs each
.venv/Scripts/python -m rebbi.bench --resume runs/bench/<folder>   # finish one that stopped
.venv/Scripts/python -m rebbi.bench --rehearsal --repeats 1  # the scripted model: plumbing only, never evidence
.venv/Scripts/python -m rebbi.fleet --mode upfront --target llm-0.12 --hint-tokens 15000   # one run, by hand
```

A benchmark writes `runs/bench/<time>-<label>/`: `results.csv` (one row per run, naming its run folder),
`table.md` (success and costs per case and arm) and the exact command.

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
| `rebbi/mcp_server.py` | Agent-facing MCP server: one stdio process per agent (identity from `REBBI_AGENT_ID`), or one HTTP server per fleet (identity from the agent's bearer token); never from a tool argument. `REBBI_TRACE` logs every call. |
| `rebbi/call.py` | `rebbi call <tool> '<json>'`: one call through an `.mcp.json` connection, for agents without MCP tools. |
| `rebbi/starter_fleet.toml` | Copy of `config/scenario.toml` shipped in the package for `rebbi init`; a test keeps them identical. |
| `docs/AGENT_INTERFACE.md` | The interface doc for outside agents and builders. |
| `docs/hw9/` | HW9: pre-registered protocol, results, and evidence of the cold-start runs. |
| `rebbi/gateway.py` | Pass-through for Claude API calls. Refuses a call unless the agent's ledger balance covers its input (counted with count_tokens), after auto-borrow if Rebbi is on; debits the tokens each call really used (input, cache writes, cache reads, output). Holds the only real API key. |
| `rebbi/fleet.py` | The demo harness: three Claude Agent SDK agents, the gateway beside them (or harness metering in subscription mode), a low-budget warning hook, verification and the ledger check after each run. |
| `rebbi/video_demo.py` | Baseline then Rebbi on the same budgets, then a side-by-side table: the evidence shot for the video. |
| `rebbi/calibrate.py` | Proposes scenario numbers from a measurement run. |
| `rebbi/bench.py` | The HW7 benchmark: cases × arms × repeats, one results row per run. |
| `config/targets.toml` | The repositories the audit can run on, each pinned to a commit with its own answer key. |
| `config/bench.toml` | The benchmark cases: target, kind (ordinary, hard, failure), tuning or fresh, budget overrides. |
| `docs/bench/PLAN.md` | The benchmark plan, fixed before the runs. |
| `rebbi/scripted_model.py` | A hard-coded stand-in for the Claude API: the offline tests and `demo --rehearsal`. Never evidence. |
| `rebbi/verify.py` | Checks a report against the job template's answer key; fails closed. |
| `rebbi/api.py` | FastAPI read-only views: `/agents`, `/loans`, `/decisions`, `/invariants`. |
| `specs/dep-audit-v1.md` | The job template: what a finished audit must contain. Draft for Nitya. |
| `specs/answer-key-*.json` | One key per target, which the verifier checks against, drafted by `scripts/make_answer_key.py` from the pinned repo and checked by hand. |

## Ledger invariants

`python -m rebbi check` fails if any of these breaks:

- The fleet total equals budgets granted minus tokens used: loans never create or lose tokens.
- Each loan's lender and borrower entries cancel out.
- No loan left its lender below the reserve it had published.
- No loan is still active after its expiry, and none returned more than it lent.
