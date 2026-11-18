# HW9 results: can an agent we did not configure use Rebbi from its documentation?

**Short answer: yes, on every interface criterion in 5 of 5 runs.** Fresh agent sessions got the
interface doc, a connection file, the job template, the target repository and a task. In every
run, the client found Rebbi's tools, borrowed, reported each loan exactly as the ledger recorded
it, and settled it. The ledger checks passed every time (C1 to C5 and C7 in all five runs).
**The pre-registered "useful result" was not met in full:**
- R1 failed C6. Its audit missed 1 of the verifier's 11 checks, the commit, because our set-up
  removed the target's `.git`.
- H1 failed C8 as originally written, a criterion we then changed (see Disclosure).

R4, the rerun with the fix and the set-up corrected, passed all 11 checks.

The runs exposed problems in Rebbi's interface: every client had to write its own MCP client,
partial loans were not flagged, refusals carried no reason, and `requires_tools` was ignored
without notice. We fixed them and reran with unchanged prompts.

- Interface documentation: [`docs/AGENT_INTERFACE.md`](../AGENT_INTERFACE.md)
- Protocol, prompts and success criteria, committed before the first run:
  [`docs/hw9/PROTOCOL.md`](PROTOCOL.md) (commit `7dc957d`, 03:56:58 UTC; the first trace entry is
  03:58:15 UTC, 77 seconds later)
- Raw evidence per run: [`docs/hw9/evidence/`](evidence/)

## Disclosure

- **Self-run.** Each client was a fresh Claude Sonnet 5.5 session, started by the Claude Opus
  5.5 session that wrote Rebbi's HW9 changes, through its sub-agent tool. A fresh session sees no
  earlier context: only its prompt (verbatim in each run's `prompt.txt`) and its folder. It did
  not get Rebbi as built-in tools, so it had to connect as an outside builder's agent would.
- **No manual help during runs.** Nobody passed messages to a client, and no client got a call
  sequence or an expected answer.
- **Same machine.** Clients ran in the same Linux container as the repository. Their prompts told
  them to use only their folder and the installed environment; their work logs are consistent
  with that, but the container could not enforce it. H1's "remote" server ran on the same
  machine, reached over HTTP with a bearer token.
- **Rebbi was installed from a built wheel** into a fresh virtual environment, not run from the
  checkout. The wheel for R1, R2 and H1 was built at 22:57:37 ET, 15 seconds before its code was
  committed as `08e8410` (no code change in between; the commit added only the set-up script).
  R3 and R4 used the code of `3697444`.
- **Criterion C8 was changed after H1.** As pre-registered, C8 applies "when the stated need
  exceeds what was lent". H1's prompt stated a 30,000 need and its own budget was 7,000. It asked
  for and got 25,000, so the original C8 scores it FAIL: no second ask, no shortfall stated. We
  judged the agent right (7,000 + 25,000 covers 30,000) and changed C8 to compare the need with
  the loans plus the agent's own budget. Under that version C8 does not apply to H1. R2 and R3
  pass C8 under both versions. This was a change of criterion, not a bug fix.
- **One real checker bug, fixed after H1:** the collect step copied the SQLite ledger without its
  write-ahead log, so the first score of H1 read an empty ledger. All runs were scored after the
  fix.
- **R4 deviates from the protocol's set-up** (`evidence/R4/SETUP_NOTE.md`): the target kept its
  `.git`, and the doc was the fixed version.
- **Self-reported steps.** That R1 and R4 started their audits only after the loan rests on the
  order of their work logs; Rebbi's trace shows the loan and the settle, not the audit. From LEND
  to settle took 28 s (R1) and 25 s (R4).

## Runs

| Run | Code | Transport | Task | Asked → got | What the client did with the result | Interface criteria | C6 job |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 cold start | before fix | stdio | full audit, need 60,000 | 60,000 → 60,000 | did the audit; settled `done`; budget.json matches the ledger | C1 to C5, C7 pass | **FAIL**: 10 of 11 checks; commit "unknown" (our set-up) |
| R2 boundary | before fix | stdio | budget only, need 100,000 | 60,000 → 60,000; 33,000 → 20,000 | stated the 13,000 shortfall and why; settled both `abandoned` | all pass | n/a |
| H1 remote | before fix | HTTP + token | budget only, need 30,000 | 25,000 → 25,000 | settled; repeated the doc's warning that errors carry no reason | C1 to C5, C7 pass; C8 FAIL as written, n/a as changed | n/a |
| R3 boundary rerun | after fix | stdio | P2, unchanged | 93,000 → 60,000 (`partial`, `loan cap`); 33,000 → 20,000 (`partial`, `lender room`) | stated the 13,000 shortfall, quoting the reasons from the replies; settled both | all pass | n/a |
| R4 cold-start rerun | after fix | stdio | P1, unchanged | 55,000 → 55,000 | did the audit; settled `done`; budget.json matches the ledger | all pass | **PASS**: 11 of 11 |

Each run's `outcome.md` has the criterion-by-criterion evidence (scored with the changed C8).
Re-score any run with
`python scripts/check_cold_start.py docs/hw9/evidence/<run> --mode <full|budget-only> --needed <n>`
using the values in its `run.json`. Client session sizes and times: `evidence/client-usage.md`.

### R1 in detail: requests, replies, and how the agent used them

From `evidence/R1/trace.jsonl`, Rebbi's own record of each call:

| Time (UTC) | Agent's call | Rebbi's reply | What the agent did with it |
| --- | --- | --- | --- |
| 03:58:15, 03:58:19 | `get_budget` (twice) | balance 7,000, no loans | Saw it could not cover a 60,000 job |
| 03:58:23 | `post_handoff` 60,000, `request_id auditor-01-audit-1` | `LEND`, loan 1, 60,000 from analyst-07, expires 04:13:23 | Did the audit (the prompt: start only if you secured enough) |
| 03:58:51 | `settle` loan 1, `done` | settled, 60,000 returned | Wrote `budget.json` with loan id, tokens, lender and expiry, all matching the ledger |

The audit missed one of the verifier's 11 checks: the commit. Our set-up copied the target
without `.git`. The agent wrote "unknown" instead of inventing a hash, and said so in its final
report. We class this as a **test set-up problem**. In R4 the target kept `.git`; the agent read
the commit and the audit passed all 11 checks.

## What the runs exposed

| # | Observation | Seen in | Class |
| --- | --- | --- | --- |
| 1 | Every client wrote its own MCP client before its first call (`rebbi_call.py`, `rebbi_client.py`); R1's first attempt had a bug (`isError` vs `is_error`) | R1, R2, H1 | Interface |
| 2 | Refusals came back as `Error executing tool <name>` with no reason. No client hit a refusal; H1 repeated the doc's warning about it; the probe shows it | H1 (doc), probe | Interface |
| 3 | A partial loan was not flagged. R2's work log shows it read the 60,000 cap in the doc and split its ask at 60,000; its second loan (20,000 against 33,000) came back with nothing saying why except the `considered` list | R2, probe | Interface |
| 4 | `requires_tools` was accepted and ignored without notice | probe | Interface |
| 5 | A loan expires after 900 seconds and cannot be extended; H1 noted the audit must finish inside that window | H1 | Project limitation, not fixed |
| 6 | Rebbi does not meter an outside client's own model calls, so every settle returned the whole loan (the clients used 87,205 to 97,790 tokens each, `evidence/client-usage.md`) | all | Project limitation, documented; metering exists only in Rebbi's harness and gateway |
| 7 | Audit commit unknown | R1 | Test set-up |
| 8 | Checker read an empty ledger | H1 | Test set-up (our scoring) |

**What we predicted for R2, before the run** (PROTOCOL.md): the client "may treat the loan as
full" or "work out the shortfall only by comparing `tokens` with `requested`". The second
happened. R2 never sent a request above the cap: it split its ask in advance.

## Boundary, improvement and rerun

**Boundary tested.** By the agents: asks above the 60,000 cap (R3) and above what any lender has
left (R2, R3). By `scripts/hw9_probe.py`, scripted over MCP: the same two, a request when nothing
is left, `settle` on a loan that does not exist, a reused `request_id`, and `requires_tools`
(`evidence/probe-before.txt`, `evidence/probe-after.txt`).

**Improvement 1: every reply says why** (commit `3697444`).
- `LEND` replies carry `partial` and `shortfall_tokens`. When the loan is partial they also carry
  `limit_reason` (`"loan cap"` or `"lender room"`) and a `next_step`.
- `post_handoff` replies carry `limits` (cap, lender minimum, expiry), so an agent can plan its
  asks. So do `get_budget` and `report_headroom`, and since `dc06b28` (below) so does a
  non-positive ask.
- Refusals carry their reason: `Error executing tool settle: settle refused: no loan 999`.
- `requires_tools` and `requires_scopes`, when sent, come back as `ignored_fields` with a note.

**Improvement 2: `rebbi call`.** One tool call from a shell through the `.mcp.json` connection,
printing JSON, so an agent without MCP tools writes no client code.

**Reruns, prompts unchanged** (R4's set-up differs, see Disclosure).
- R3 asked for its whole remaining need, 93,000, in one request. The reply said `partial`,
  `loan cap`, shortfall 33,000. Its next request, for 33,000, came back `partial`, `lender room`.
  R3's work log quotes both reasons. Before the fix, R2 got the same 80,000 by splitting its ask
  in advance. R3 got the reasons from the replies; R2 got the cap from the doc and inferred the
  second shortfall from the `considered` list. R3's doc still stated the cap, and its work log
  shows it read it.
- R3 and R4 wrote no Rebbi client code; both used `rebbi call`. R4's only code was an import
  scanner for the audit.
- R4 asked for 55,000, under the cap, so it never received a partial reply. It completed the job:
  verifier PASS on 11 of 11 checks.

**Regression tests** (`tests/test_self_explaining_replies.py`, 14 tests): partial by cap, partial
by lender room, full loan not partial, limits in every reply, ignored fields named, replay still
returns the first decision, refusal reasons over MCP, the partial flag over MCP, `rebbi call` from
a shell, and five tests for the fixes the review found (below). Full suite: 94 passed, three times
in a row (72 before HW9).

**Existing integration still works.** Nanda Town's four live Rebbi cases (HW8; fork
`eglismella/nandatown` at `4803f9d`), run against Rebbi `dc06b28`: all four PASSED, every stage
(`evidence/town-regression.txt`). Town reads only `decision`, `loan_id`, `tokens`, `replayed`,
`blocker` and `considered` from Rebbi's replies; HW9 added fields and changed none.

## Independent review, and the fixes it led to

A separate agent session that had not seen the work checked this write-up and the interface doc
against the evidence and the code. It reproduced every run's score and every number in the run
tables, and confirmed the protocol predates the runs. It also found problems, fixed in `dc06b28`,
after the runs (none of them was exercised by a client):
- `rebbi init --force` overwrote the operator's edited fleet file and reissued every HTTP token.
  It now keeps both (`--new-tokens` reissues tokens).
- A non-positive ask and `report_headroom` lacked `limits`.
- `settle` on a loan past its expiry closed it as settled; it now reports `expired`.
- `rebbi call` printed a traceback when the server was unreachable; it now prints JSON.
- A pre-HW9 flaky test: two harness runs started in the same second collided on one folder name.
- Doc corrections: the operator HTTP API includes unauthenticated metering endpoints (localhost
  only); `REBBI_SCENARIO` silently falls back to the starter rules if unset; the 5,000 minimum
  applies to lenders, not asks; expired loans close at the next call; the HTTP client entry
  format is Claude Code's.

It also corrected this write-up's framing: the headline, the C8 change, R4's set-up and what H1
observed.

## What improved, what did not, what is unproven

- **Improved:** agents get the cap, the shortfall and its reason from the reply itself; refusals
  explain themselves; shell agents need no code (3 of 3 clients wrote one before, 0 of 2 after).
- **Did not change:** the outcome of the boundary runs. R2 and R3 both ended with 80,000 lent and
  a stated 13,000 shortfall against a 93,000 need. We did not observe a failure that the fix
  prevents; it removes inference the clients had to do.
- **Unproven:** one sample per run; all clients were the same model family, self-run, on one
  machine; no client was an MCP-native host (for example Claude Code with Rebbi as built-in
  tools); the HTTP mode ran only on localhost, not behind TLS on a real network; loans cannot be
  extended past 900 seconds; outside clients are not metered.

## Repeat the test

```bash
git clone https://github.com/eglismella/rebbi && cd rebbi
python -m venv .venv && .venv/bin/pip install -e ".[test]"
.venv/bin/python -m rebbi fetch-target          # the audit target at its pinned commit
.venv/bin/pip wheel --no-deps -w /tmp/wheel . && python -m venv /tmp/clientenv && /tmp/clientenv/bin/pip install /tmp/wheel/rebbi-*.whl
.venv/bin/python scripts/hw9_run.py setup /tmp/hw9/R1 --prompt P1 --python /tmp/clientenv/bin/python
# give a fresh agent session the text of /tmp/hw9/R1/prompt.txt and nothing else; wait for it to stop
.venv/bin/python scripts/hw9_run.py collect /tmp/hw9/R1      # writes outcome.md; exit 0 if every criterion passes
```

Add `--keep-git` for the R4 set-up, use `--prompt P2` for the boundary run, and
`--prompt P3 --http-port 8765` for the HTTP run. `python scripts/hw9_probe.py` prints the scripted
boundary calls; `pytest` runs the regression tests.

## Team (Pietro to confirm before submission)

- **Pietro Bertone:** set HW9's scope and product direction (outside-agent access, the fixes
  above), directed and reviewed the work, owns the slides and demo video.
- **Eglis Mella:** built Rebbi's ledger, broker, MCP server, harness and the HW8 Nanda Town
  integration (HW6 to HW8), on which HW9 builds; repository owner.
- **Nitya Maddineni:** reviewed the job template and the answer keys the verifier uses (HW6,
  HW7) and was assigned the second-person reproduction of the HW8 checks.
- **AI assistance (disclosed):** the HW9 code, docs, runs and this write-up were produced by
  Claude Opus 5.5 working in Pietro's Claude account, with fresh Claude Sonnet 5.5 sessions as
  the test clients and a separate Claude session as the reviewer.
