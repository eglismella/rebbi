# HW9 results: can an agent we did not configure use Rebbi from its documentation?

**Short answer: yes, in 5 of 5 runs.** Fresh agent sessions got only the interface doc, a
connection file and a task. Each found Rebbi's tools, borrowed, used the loan to decide
whether to start the job, reported the loan exactly as the ledger recorded it, and settled
it. The ledger checks passed every time. One run also did the full job, and its audit passed
the verifier on all 11 checks after we fixed a mistake in our own test set-up. The runs
exposed three interface problems. We fixed them, and the reruns show the agents relying on
Rebbi's replies instead of on warnings in the doc.

- Interface documentation: [`docs/AGENT_INTERFACE.md`](../AGENT_INTERFACE.md)
- Protocol, prompts and success criteria, committed before the first run:
  [`docs/hw9/PROTOCOL.md`](PROTOCOL.md) (commit `7dc957d`, 2026-11-17 22:56:58 ET; first run
  started 22:58 ET)
- Raw evidence per run: [`docs/hw9/evidence/`](evidence/)

## Disclosure

- **Self-run.** Each client was a fresh Claude Sonnet 5.5 session, started by the Claude Opus
  5.5 session that wrote Rebbi's HW9 changes, through its sub-agent tool. A fresh session sees
  no earlier context: only its prompt (verbatim in each run's `prompt.txt`) and its folder.
  It was not given Rebbi as built-in tools, so it connected the way any outside builder's
  agent would.
- **No manual help during runs.** Nobody passed messages to a client, and no client got a
  call sequence or an expected answer.
- **Same machine.** Clients ran in the same Linux container as the repository. Their prompts
  told them to use only their folder and the installed environment. Their work logs show they
  did; the container could not enforce it. H1's "remote" server was on the same machine,
  reached over HTTP with a bearer token.
- **Rebbi was installed from a built wheel** into a fresh virtual environment, not run from
  the checkout. R1, R2 and H1 used the code at `08e8410`; R3 and R4 used `3697444`.
- **Two checker corrections after H1**, both in our own scoring script, not in Rebbi. The
  collect step copied the SQLite ledger without its write-ahead log, so the first score read an
  empty ledger. C8 ignored the agent's own 7,000-token budget: H1 asked for 25,000 against a
  30,000 job, which is correct. Both fixes are commented in `scripts/` and applied to every run.

## Runs

| Run | Code | Transport | Task | Asked → got | Result use | C1 to C5, C7, C8 | C6 job |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 cold start | before fix | stdio | full audit, need 60k | 60,000 → 60,000 | started the audit only after LEND; settled `done` | all pass | FAIL: commit "unknown" (set-up, see below) |
| R2 boundary | before fix | stdio | budget only, need 100k | 60,000 → 60,000; 33,000 → 20,000 | stated the 13,000 shortfall; settled both `abandoned` | all pass | n/a |
| H1 remote | before fix | HTTP + token | budget only, need 30k | 25,000 → 25,000 | settled; flagged that errors carry no reason | all pass | n/a |
| R3 boundary rerun | after fix | stdio | P2 unchanged | 93,000 → 60,000 (partial, loan cap); 33,000 → 20,000 (partial, lender room) | stated the 13,000 shortfall; settled both | all pass | n/a |
| R4 cold-start rerun | after fix | stdio | P1 unchanged | 55,000 → 55,000 | started the audit only after LEND; settled `done` | all pass | **PASS, 11 of 11** |

Each run's `outcome.md` has the criterion-by-criterion evidence. Re-score any run with
`python scripts/check_cold_start.py docs/hw9/evidence/<run> --mode <full|budget-only> --needed <n>`.

### R1 in detail: requests, replies, and how the agent used them

From `evidence/R1/trace.jsonl`, Rebbi's own record of each call:

| Time (UTC) | Agent's call | Rebbi's reply | What the agent did with it |
| --- | --- | --- | --- |
| 03:58:15, 03:58:19 | `get_budget` (twice) | balance 7,000, no loans | Saw it could not cover a 60,000 job |
| 03:58:23 | `post_handoff` 60,000, `request_id auditor-01-audit-1` | `LEND`, loan 1, 60,000 from analyst-07, expires 04:13:23 | Started the audit (the prompt said: only if you secured enough) |
| 03:58:51 | `settle` loan 1, `done` | settled, 60,000 returned | Wrote `budget.json` with loan id, tokens, lender and expiry, all matching the ledger |

The audit failed one of the verifier's 11 checks: the commit. Our set-up copied the target
repository without `.git`, so the commit could not be found. The agent wrote "unknown"
instead of inventing a hash, and said so in its report. This is a **test set-up problem**. R4
kept `.git`, found the commit, and passed all 11.

## What the runs exposed

| # | Observation | Run(s) | Class |
| --- | --- | --- | --- |
| 1 | Every client had to write its own MCP client before its first call (`rebbi_call.py`, `rebbi_client.py`); R1's first attempt had a bug (`isError` vs `is_error`) | R1, R2, H1 | Interface: no way to call Rebbi without code |
| 2 | Refusals came back as `Error executing tool <name>` with no reason; H1 flagged this unprompted | H1, probe | Interface |
| 3 | A partial loan was not flagged. R2 handled it only because the doc warned: it split its ask at the 60,000 cap in advance, then compared `tokens` with `requested` | R2, probe | Interface |
| 4 | `requires_tools` was accepted and silently ignored | probe | Interface |
| 5 | A loan expires after 900 seconds and cannot be extended; H1 noted the audit must finish inside that window | H1 | Project limitation, not fixed |
| 6 | Rebbi does not meter an outside client's own model calls, so every settle returned the whole loan. The clients used 87,000 to 98,000 tokens each, by the sub-agent tool's count | all | Project limitation, documented; metering exists only in Rebbi's own harness and gateway |
| 7 | Audit commit unknown | R1 | Test set-up |
| 8 | Checker read an empty ledger; C8 ignored the agent's own budget | H1 | Test set-up (our scoring) |

We expected R2 to over-claim (count a 60,000 loan as 100,000). It did not: the doc's warning
was enough. The problem was real but hidden, because the doc was carrying information the
reply should carry.

## Boundary, improvement and rerun

**Boundary tested.** A request over the 60,000 loan cap, then a request larger than what any
lender has left, then refused calls (unknown loan, reused `request_id`), then a request asking
for a tool check Rebbi does not do. Exercised by R2 and R3 (agents) and by
`scripts/hw9_probe.py` (scripted; `evidence/probe-before.txt` and `evidence/probe-after.txt`).

**Improvement 1: every reply says why** (commit `3697444`).
- `LEND` replies carry `partial`, `shortfall_tokens` and, when partial, `limit_reason`
  (`"loan cap"` or `"lender room"`) and a `next_step`.
- Every `post_handoff` reply and `get_budget` carry `limits` (cap, minimum, expiry), so an
  agent can plan its asks.
- Refusals carry their reason: `Error executing tool settle: settle refused: no loan 999`.
- `requires_tools` and `requires_scopes`, when sent, come back as `ignored_fields` with a note.

**Improvement 2: `rebbi call`.** One tool call from a shell through the `.mcp.json`
connection, printing JSON, so an agent without MCP tools writes no client code.

**Reruns, prompts unchanged.**
- R3 asked for its whole need (93,000) in one request. The reply said partial, loan cap,
  shortfall 33,000. The next request said partial, lender room. R3's work log quotes those
  reasons. R2 had to know the cap from the doc and split its ask in advance to get the same
  result.
- R3 and R4 wrote no Rebbi client code; both used `rebbi call`. R4's only code was an import
  scanner for the audit itself.
- R4 completed the job: verifier PASS on 11 of 11 checks.

**Regression tests** (`tests/test_self_explaining_replies.py`, 9 tests): partial by cap,
partial by lender room, full loan not partial, limits in every reply, ignored fields named,
replay still returns the first decision, refusal reasons over MCP, the partial flag over MCP,
and `rebbi call` from a shell. Full suite: 89 passed (72 before HW9).

**Existing integration still works.** Nanda Town's four live Rebbi cases (HW8, fork
`eglismella/nandatown` at `4803f9d`), run against the new Rebbi: every functional stage passed
in all four (lend, lost-reply, duplicate, no-room). The only failure was `rebbi_version_pinned`,
which by design fails when Rebbi is not at the commit Town pinned. The new reply fields are
additions; Town reads only `decision`, `loan_id`, `tokens`, `replayed` and `considered`.

## What improved, what did not, what is unproven

- **Improved:** agents learn the cap, the shortfall and the reason from the reply itself;
  refusals explain themselves; shell agents need no code.
- **Did not change:** the outcome of the boundary runs. R2 and R3 both ended with 80,000 of a
  93,000 ask and stated the shortfall. The fix makes that outcome depend on the reply instead
  of the doc; we did not observe a failure that it prevents.
- **Unproven:** one sample per run; all clients were the same model family, self-run, on one
  machine; no client was an MCP-native host (for example Claude Code or Claude Desktop with
  Rebbi as built-in tools); the HTTP mode has run only on localhost, not behind TLS on a real
  network; loans cannot be extended past 900 seconds; outside clients are not metered.

## Repeat the test

```bash
git clone https://github.com/eglismella/rebbi && cd rebbi
python -m venv .venv && .venv/bin/pip install -e ".[test]"
.venv/bin/python -m rebbi fetch-target          # the audit target at its pinned commit
.venv/bin/pip wheel --no-deps -w /tmp/wheel . && python -m venv /tmp/clientenv && /tmp/clientenv/bin/pip install /tmp/wheel/rebbi-*.whl
.venv/bin/python scripts/hw9_run.py setup /tmp/hw9/R1 --prompt P1 --python /tmp/clientenv/bin/python --keep-git
# give a fresh agent session the text of /tmp/hw9/R1/prompt.txt and nothing else; wait for it to stop
.venv/bin/python scripts/hw9_run.py collect /tmp/hw9/R1      # writes outcome.md, exit 0 if every criterion passes
```

Use `--prompt P2` for the boundary run, and `--prompt P3 --http-port 8765` for the HTTP run.
`python scripts/hw9_probe.py` prints the scripted boundary calls. `pytest` runs the regression
tests.

## Team (Pietro to confirm before submission)

- **Pietro Bertone:** set HW9's scope and product direction (outside-agent access, the fixes
  above), directed and reviewed the work, owns the slides and demo video.
- **Eglis Mella:** built Rebbi's ledger, broker, MCP server, harness and the HW8 Nanda Town
  integration (HW6 to HW8), on which HW9 builds; repository owner.
- **Nitya Maddineni:** reviewed the job template and the answer keys the verifier uses (HW6,
  HW7) and was assigned the second-person reproduction of the HW8 checks.
- **AI assistance (disclosed):** the HW9 code, docs, runs and this write-up were produced by
  Claude Opus 5.5 working in Pietro's Claude account, with fresh Claude Sonnet 5.5 sessions as
  the test clients.
