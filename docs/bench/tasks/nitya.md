# HW7 task for Nitya: check the answer key for the hardest repository

**Time:** about 45 minutes. **Send your result to Eglis by 9pm tonight** (HW7 is due at 11:59pm).
**You need:** our project files (this repo on GitHub, branch `hw7-benchmark`, or the zip `rebbi-hw7.zip` from Eglis), a web browser and a code editor. No Claude login, no cost.

## Why this matters

Our success check compares each agent's report with an answer key: the right answer for that
repository. If a key is wrong, every result for that repository is wrong. The report lists this as a
risk ("Our answer keys, though hand-checked, could hold an error"). You will check the key for the
hardest repository, `llm` version 0.12, on your own.

**What the PDF will say about you:** "Nitya Maddineni: independent check of the ground truth:
re-derived the answer key for the hardest repository (llm 0.12) from its source code and compared it
with ours."

## What you get

All paths start from the top of the project (on GitHub, or the `rebbi/` folder inside the zip):

- The key to check: `specs/answer-key-llm-0.12.json`
- What each field in the key means: `specs/dep-audit-v1.md`, section "What the report must contain"

## The source to check it against (public, no login)

- On GitHub: https://github.com/simonw/llm/tree/e9a6998ca38946cfef75bdb7535d8bdc652ef381
- Easier to search, as a zip: https://github.com/simonw/llm/archive/e9a6998ca38946cfef75bdb7535d8bdc652ef381.zip

Use exactly this commit. Newer versions of `llm` have different dependencies.

## What to check, one field at a time

1. **`runtime_dependencies`**: same names and version limits as `install_requires` in `setup.py`?
2. **`optional_groups`**: same groups and packages as `extras_require` in `setup.py`?
3. **`imports`**: for each runtime dependency, the files in `llm/` that import it. Watch out: the
   name you import can differ from the package name (`pyyaml` is imported as `yaml`, and there are
   others).
4. **`unused_dependencies`**: declared in `setup.py`, but no file imports it.
5. **`undeclared_imports`**: third-party modules a file in `llm/` imports, but `setup.py` doesn't
   declare. Skip Python's standard library and `llm`'s own modules.
6. **`unpinned`**: runtime dependencies with no version limit at all.

Tip: search the unzipped source for lines starting with `import ` or `from `.

## What to send Eglis

Either "the key matches the source", or a short list of differences:

| Field | The key says | The source says (file and line) |
|---|---|---|

If you finish early, do the same for `specs/answer-key-sqlite-utils-3.30.json` at
https://github.com/simonw/sqlite-utils/tree/fb8f495582f68d8d49f57b42d12a66802f9ac238 (optional).

Don't change any file. Just report what you find.
