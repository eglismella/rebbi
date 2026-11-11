# Nitya: install Rebbi and rerun the HW8 checks on your own computer

**Why this matters.** Our HW8 pull request says the Nanda Town checks are reproducible. So far they
have run only on Eglis's laptop. A second person getting the same results on another computer is the
strongest evidence we can add, and Town's own testing guide asks for exactly that.

**Time:** about 30 minutes, most of it installing. **No API key is needed, and nothing costs money.**

**Send Eglis:** your operating system, your Python version (`python3 --version`), and the result lines
marked "you should see" below. If any step prints something else, send the last 20 lines it printed.

## 0. Before you start

- Python 3.11 or newer, and git.
- Access to `github.com/eglismella/rebbi`. The repository is private: Eglis adds you as a collaborator,
  and you accept the email invite.
- On Windows, run everything in **Git Bash**, and wherever a command says `.venv/bin/python`, type
  `.venv/Scripts/python` instead. If `python3` opens the Microsoft Store, type `python`.

## 1. Get both repositories side by side

```bash
mkdir hw8-check && cd hw8-check
git clone https://github.com/eglismella/rebbi.git rebbi
git clone --branch integration/rebbi-lending https://github.com/eglismella/nandatown.git nandatown
git -C rebbi log --oneline -1
git -C nandatown log --oneline -1
```

You should see one line per repository; the Town one starts with
`4803f9d Rebbi: add token-lending MCP integration`.

## 2. Install and test Rebbi

`fetch-target` downloads the small repository the agents audit in Rebbi's own tests, pinned to one commit.

```bash
cd rebbi
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
.venv/bin/python -m rebbi fetch-target
.venv/bin/python -m pytest -q
cd ..
```

You should see `72 passed` (about 40 seconds).

## 3. Install Nanda Town

```bash
cd nandatown
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## 4. Run the four Rebbi cases live

```bash
.venv/bin/python examples/rebbi/run.py --project ../rebbi --case all --out runs/rebbi
```

You should see four lines like `lend: PASSED`, one for each case (`lend`, `lost-reply`, `duplicate`,
`no-room`), each followed by its stages. Every stage should say `passed`, except `privacy`, which
says `not_tested`.

## 5. Check the saved evidence and the test

```bash
.venv/bin/python examples/rebbi/run.py --verify examples/rebbi/evidence
REBBI_PROJECT=../rebbi .venv/bin/python -m pytest -q tests/test_example_rebbi.py
```

You should see six lines ending in `verified`, then `21 passed`.

## 6. Reproduce the bug Town found

This switches Rebbi back to the version from before the fix, runs the two failing cases, and switches back.

```bash
git -C ../rebbi checkout 3db016d
.venv/bin/python examples/rebbi/run.py --project ../rebbi --case lost-reply --out runs/before
.venv/bin/python examples/rebbi/run.py --project ../rebbi --case duplicate --out runs/before
git -C ../rebbi checkout main
```

You should see `lost-reply: FAILED` and `duplicate: FAILED`. In both, `one_loan_per_request` failed with
`booked loans [1, 2]`, and `rebbi_invariants` still passed. That is the bug: two loans for one request,
which Rebbi's own check could not see.

## If something goes wrong

- `pip install` fails: check `python3 --version` (3.11 or newer), then send the error.
- `run.py` says a session failed to start: check that `../rebbi/.venv` exists (step 2).
- `rebbi_version_pinned` failed: the Rebbi folder has changes. Run `git -C ../rebbi status` and send what it prints.
