# HW7 task for Pietro: check our results, from raw logs to report

**Time:** about 1 hour. **Send your result to Eglis by 9pm tonight** (HW7 is due at 11:59pm).
**You need:** our project files (this repo on GitHub, branch `hw7-benchmark`, or the zip `rebbi-hw7.zip` from Eglis), and Excel, Google Sheets or Python. No Claude login, no cost.

## Why this matters

The rubric gives 4 of the 10 points for "checkable evidence". Our report's numbers go through two
steps: each run's log becomes a row in a results file, and the results files become the report's
tables. You will check both steps on your own, as a second person.

**What the PDF will say about you:** "Pietro Bertone: independent check of the results: recomputed
every number in the results tables from the raw results files, and traced sampled runs from their
logs to those files."

## What you get

All paths start from the top of the project (on GitHub, or the `rebbi/` folder inside the zip).

- The report: `docs/bench/HW7-Rebbi-benchmark.pdf`. The tables are in sections 3, 4 and 5.
- The results files, one row per run, under `docs/bench/evidence/`:

| File | Feeds |
|---|---|
| `main/results.csv` | section 3 table, plus the "rebbi before" and "upfront" columns in section 4 |
| `retest-autoborrow/results.csv` | section 4 table: "rebbi after" and the three "after" columns |
| `stress-hint15k/results.csv`, `stress-nohint/results.csv`, `stress-scarce/results.csv` | section 5 table, one row each |

- The raw logs: `docs/bench/evidence/runs/<run>/console.log`, one folder per run. The `run` column
  of a results file names the folder.

## Part 1: from logs to results files (about 15 minutes)

Pick 5 rows at random from `main/results.csv`, from different arms. For each row, open its run's
`console.log`. The last line looks like this:

    RESULT rebbi: job finished, verifier PASS, ledger PASS, auditor-01 used 43749 tokens, 2 loan(s), 33s

Check that it matches the row's columns: `arm`, `finished` (finished = True, STOPPED = False),
`verified` (PASS = True), `ledger_ok`, `auditor_tokens`, `loans` and `seconds`.

## Part 2: from results files to the report's tables (about 45 minutes)

The columns you need:

| Column | Values |
|---|---|
| `case` | the repository tested, e.g. `llm-0.12`, or `no-lender-room` |
| `kind` | `ordinary`, `hard` or `failure` |
| `split` | `tuning` or `fresh` |
| `arm` | `baseline`, `upfront` or `rebbi` |
| `success` | `True` or `False` |
| `auditor_tokens`, `fleet_tokens`, `seconds` | the costs |

How each number is computed:

- **Success, like "4/15":** rows with `success` = True, out of all rows in the group.
- **"ordinary + hard":** rows where `kind` is `ordinary` or `hard`. Leave out `no-lender-room`.
- **Median tokens or seconds:** the median over all rows in the group, both passed and failed runs.
- **Section 4, "tuning" and "fresh" rows:** group by `split`, ordinary and hard rows only.
- **Section 5:** each file is one row in the table, with both repositories together, per arm.

## What to send Eglis

1. The 5 run names from Part 1, and whether each one matched.
2. Either "I checked every number in the 3 tables, all match", or a short list of what doesn't:

| Table (section) | Row and column | PDF says | I got |
|---|---|---|---|

Don't change any file. Just report what you find.
