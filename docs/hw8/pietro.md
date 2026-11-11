# Pietro: Demo Day presentation, live demo and the HW8 slide

**Demo Day is tomorrow, Thursday Nov 12.** This page gives you the story, the numbers, and three
demos ordered from safest to riskiest. Eglis shares the one-pager "Rebbi: infrastructure and
capabilities" with you; it has the diagram and every number below.

## The story in three lines

1. **Problem.** Each AI agent gets a fixed token budget. Too small, and a job dies halfway while
   other agents sit on unused budget.
2. **Rebbi.** The agent borrows spare budget from an idle agent over MCP, finishes, and gives back
   what it didn't use. No lender ever drops below the reserve it publishes.
3. **Proof.** Jobs that failed 0 of 15 times on their own budget passed 15 of 15 with Rebbi, with no
   reserve broken. Testing inside Nanda Town found a real bug (two loans for one request), which we fixed.

## Numbers you can quote

| Claim | Number | Source |
| --- | --- | --- |
| Jobs that run out of budget without Rebbi | 0/15 pass | HW7 main run, real Claude agents |
| The same jobs with Rebbi and auto-borrow | 15/15 pass | HW7 retest |
| Cost estimate wrong or missing | Rebbi 12/12, budget moved up front 4/12 | HW7 stress runs |
| Reserves broken, ledger checks failed | none, in every run | HW7 and HW8 |
| Nanda Town after the fix | 4/4 scenarios pass | HW8 |

Be ready for these two questions:
- **What does it cost?** About twice the fleet tokens of a manager who knows the job's cost in
  advance: lenders spend tokens publishing their reserves. That manager rarely exists, and with a
  wrong estimate it failed 8 of 12 jobs.
- **Real agents?** HW7 used real Claude agents doing a code audit. In Nanda Town the agents are
  scripts, but Rebbi itself runs for real.

## Set up once (about 20 minutes)

Do steps 0 to 3 of [Nitya's page](nitya.md): both repositories, both virtual environments. No API key needed.

## Demo A: Nanda Town finds a bug, and the fix (no key, about 10 seconds a run)

This is the safest live demo: it's free, and it gives the same result every time. From the `nandatown` folder:

```bash
.venv/bin/python examples/rebbi/run.py --project ../rebbi --case lost-reply --out runs/demo
```

What to say: Town drops Rebbi's answer on purpose, and the agent asks again. Since the fix, the retry
gets the same loan back (`retry_gets_original: passed`), and the ledger at the bottom shows exactly one loan.

To show the bug itself, open the saved run from before the fix:
`examples/rebbi/evidence/before-fix-lost-reply/report.md`. Its `one_loan_per_request` failed with
"booked loans [1, 2]". To rerun it live instead, use step 6 of Nitya's page.

For a picture, Town can draw a run as a page with agents on a map and messages on a timeline:

```bash
.venv/bin/nandatown visualize examples/rebbi/evidence/after-fix-lost-reply --output runs/town.html
```

Then open `runs/town.html` in your browser. Try it while you prepare, not for the first time on stage.

## Demo B: the fleet, before and after Rebbi (no key, about 15 seconds)

From the `rebbi` folder:

```bash
.venv/bin/python -m rebbi.demo --rehearsal
```

It runs the same job twice, first without Rebbi (stopped, verifier FAIL), then with Rebbi (one loan,
verifier PASS), and prints a side-by-side table. **Say that it is scripted:** the model is a stand-in,
and the output says so. It shows how the pieces work together, not how well Claude does the job.

## Demo C: real Claude agents (needs a key, costs money, about 1 to 2 minutes)

Only if Eglis gives you a key for `.env` (see the "Run the demo" section of Rebbi's README). From the `rebbi` folder:

```bash
.venv/bin/python -m rebbi fetch-target
.venv/bin/python -m rebbi.demo
```

Models are random and the network can be slow, so **record it beforehand** and play the recording.
Backup: `docs/demo/real-run-3.txt` is a real run from Oct 27 that you can show as text.

## The HW8 slide (2 points, due tonight)

One slide in the shared Fall 2026 Demo Day deck. **Duplicate the blank project template, add exactly
one slide, and leave the template slide untouched.** Then tell Eglis the exact title on the slide:
every one of us must type it into Canvas.

Suggested text:

- **Title:** Rebbi: spare token budget, lent between AI agents
- **What we are building:** a broker that lets an AI agent about to run out of tokens mid-job borrow
  spare budget from idle agents in its fleet, then return what it didn't use. One ledger; no lender
  ever drops below its reserve.
- **Which agents use it:** any agent that speaks MCP in a fleet with per-agent budgets. We test with
  Claude agents doing code audits, and with Nanda Town's agents.
- **Why it matters:** fixed budgets either waste money or kill jobs halfway. With Rebbi, 15 of 15
  jobs that failed on their own budget finished, with every reserve intact.
