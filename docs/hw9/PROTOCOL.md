# HW9 cold-start protocol (written and committed before any run)

**Question.** Can an agent that was not configured around our demo use Rebbi from its
documentation alone?

**Interface under test.** [`docs/AGENT_INTERFACE.md`](../AGENT_INTERFACE.md) at the commit that
adds this file. Rebbi is installed from a built wheel into a fresh virtual environment, not
run from the repository checkout.

## Who the client is (disclosed)

**Self-run.** Each client is a fresh Claude Sonnet 5.5 agent session started by the team's
Claude Opus 5.5 working session (the one that wrote the interface doc), through its sub-agent
tool. The fresh session gets no context from the working session: only the prompt below and the
files in its folder. It has a shell and file tools. It does not get Rebbi as built-in MCP tools,
so it has to connect as any outside builder's agent would: read the doc and write or run an MCP
client. It runs in the same Linux container as the repository. Its prompt tells it to use only
its folder and the installed environment; the container cannot enforce that, and the write-up
reports whatever its work log shows. No one passes messages to the client during a run, and no
call sequence or expected answer is given.

## Set-up per run (operator, before the client starts)

1. Fresh fleet: `rebbi init <run>/fleet --force` (starter fleet: auditor-01 7,000 tokens;
   analyst-07 can lend 80,000; writer-03 has no room; loan cap 60,000).
2. Client folder `<run>/client/` with only: `AGENT_INTERFACE.md`, `dep-audit-v1.md`
   (job template), `target/` (sqlite-utils at the pinned commit `9d7da06`, no `.git`), and
   `.mcp.json` from `rebbi client-config --dir <run>/fleet --agent auditor-01 --trace <run>/fleet/trace.jsonl`
   (for the HTTP run: `--http <url>`, with the server started by the operator).
3. After the client stops: copy `budget.json`, `report.md`, the client's notes and code into the
   run folder, then `python scripts/check_cold_start.py <run> --mode ... --needed ...`.

## Runs

| Run | When | Transport | Prompt | `--mode` | `--needed` |
| --- | --- | --- | --- | --- | --- |
| R1 cold start | before any fix | stdio | P1 | full | 60000 |
| R2 boundary | before any fix | stdio | P2 | budget-only | 100000 |
| H1 remote | before any fix | HTTP + bearer token | P3 | budget-only | 30000 |
| R3 boundary rerun | after the fix | stdio | P2, unchanged | budget-only | 100000 |
| R4 cold-start rerun | after the fix | stdio | P1, unchanged | full | 60000 |

Each run is one sample. R2, H1 and R3 stop before the job itself, to keep the runs short; the
boundary and the remote connection concern the budget step only.

## Prompts (verbatim; `{folder}` and `{python}` are filled in per run)

**P1.**

> You are auditor-01, an agent in a small fleet of AI agents. Your working folder is {folder}. Work only with the files in that folder and the Python environment at {python}; do not look elsewhere on this machine.
>
> Your job: write a dependency audit of the repository in ./target, following ./dep-audit-v1.md exactly, saved as ./report.md.
>
> Your own token budget is 7,000 tokens, which will not cover this job. Past audits of this repository took up to 60,000 tokens. Your fleet shares spare budget through a service called Rebbi. Its documentation is ./AGENT_INTERFACE.md, and ./.mcp.json is the connection your operator set up for you. Do not read or change Rebbi's ledger file directly; use Rebbi's interface.
>
> Secure enough budget before you start the audit, and start it only if you secured enough. When you finish or give up, close out with Rebbi so unused budget goes back.
>
> At the end, write ./budget.json with what you asked for, what you got, from whom, the loan id or ids, the expiry, and how you closed it. Also keep ./worklog.md: each command you ran and what it showed you, briefly. Leave any code you wrote in the folder.

**P2.** P1 with two changes: "Past audits of this repository took up to **100,000** tokens", and the paragraph starting "Secure enough budget" replaced by:

> Secure the budget this job needs, write ./budget.json, close out with Rebbi so the budget goes back, and stop: do not start the audit itself.

**P3.** P2 with "up to **30,000** tokens", and the connection sentence replaced by:

> Your fleet shares spare budget through a service called Rebbi, which runs on another machine. Its documentation is ./AGENT_INTERFACE.md; ./.mcp.json holds its address and your access token.

## Success criteria (scored by `scripts/check_cold_start.py`, then read by a person)

| # | Criterion | Evidence |
| --- | --- | --- |
| C1 | The client found and called Rebbi from the doc alone | `post_handoff` in Rebbi's trace |
| C2 | One loan per request: no double booking from a resend | ledger decisions, loans, request_ids |
| C3 | Result use: `budget.json` carries each loan's id, tokens and lender exactly as the ledger has them | budget.json vs ledger |
| C4 | Every loan the client received is settled | loan status |
| C5 | Ledger invariants hold | `rebbi check` |
| C6 | R1 and R4 only: the audit passes the verifier | `rebbi.verify` against the answer key |
| C7 | `budget.json` never claims more tokens than the ledger lent | number fields vs ledger total |
| C8 | When the stated need exceeds what was lent: the client says so, or asks again | budget.json wording or a second request |

**Useful result:** C1 to C5 and C7 pass in every run, C8 where it applies, and C6 in R1 and R4.
C6 measures the client's audit, not Rebbi: a C6 failure with C1 to C5 passing is a task failure.

**What we expect R2 to show (stated before the run).** The 60,000 cap gives a `LEND` for 60,000
against a request for 100,000, and the reply does not say the loan is partial. We expect the
client may treat the loan as full (C7 or C8 fails), or work out the shortfall only by comparing
`tokens` with `requested`. Other candidate problems, noted before any run: error replies carry no
reason (`Error executing tool <name>`), and `requires_tools` is accepted and ignored without
notice.

## Classifying failures

- **Project or interface:** caused by Rebbi's doc, replies, rules or errors.
- **Test set-up:** caused by our harness, paths, the container, the client's own audit
  mistakes, or a missing file in the client folder.

The improvement after R1, R2 and H1 addresses the most serious project or interface problem
the runs show. R3 and R4 are the comparable reruns, with prompts unchanged, plus focused
regression tests.
