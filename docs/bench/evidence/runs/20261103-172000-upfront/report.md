## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: fb8f495582f68d8d49f57b42d12a66802f9ac238
- Manifest files read: `setup.py`. I found no other manifest files and did not look for any. I searched imports in `sqlite_utils/*.py`.

## 2. Runtime dependencies
- `sqlite-fts4`
- `click`
- `click-default-group-wheel`
- `tabulate`
- `python-dateutil`

None of these has a version constraint.

## 3. Optional dependency groups
- test: pytest, black, hypothesis, cogapp
- docs: furo, sphinx-autobuild, codespell, sphinx-copybutton, beanbag-docutils
- mypy: mypy, types-click, types-tabulate, types-python-dateutil, data-science-types
- flake8: flake8

## 4. Where runtime dependencies are used
- sqlite-fts4 is imported as `sqlite_fts4` in `sqlite_utils/db.py`.
- click is imported in `sqlite_utils/cli.py` and `sqlite_utils/utils.py`.
- click-default-group-wheel is imported as `click_default_group` in `sqlite_utils/cli.py`.
- tabulate is imported in `sqlite_utils/cli.py`.
- python-dateutil is imported as `dateutil` in `sqlite_utils/recipes.py`.

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports, all optional:
  - `pysqlite3` in `sqlite_utils/utils.py`. Lines 17–18 are in a `try`, and line 21 is `except ImportError` with a fallback to `sqlite3`. I did not read the `try:` line itself.
  - `pandas` in `sqlite_utils/db.py`, line 66, followed by `except ImportError` at line 67.
  - `numpy` in `sqlite_utils/db.py`, line 71, followed by `except ImportError` at line 72.
- I inferred that the `try:` blocks for `pandas` and `numpy` start just before the import lines. My search printed only the `except ImportError` lines.

## 6. Version pinning
All five runtime dependencies have no version constraint: sqlite-fts4, click, click-default-group-wheel, tabulate and python-dateutil.

## 7. Risks and recommendations
- Risk: unpinned runtime dependencies can pick up breaking releases, especially `click`, which the CLI relies on heavily.
- Recommendation: add minimum versions, and upper bounds where appropriate, for all five runtime dependencies.
- Risk: `pysqlite3`, `pandas` and `numpy` are optional but not declared in any extras group.
- Recommendation: add an extras group for them, or document them as optional.
- Risk: `data-science-types` in the `mypy` group is unmaintained.
- Recommendation: replace `data-science-types` with current type stubs.
- Risk: `python_requires` is `>=3.6`, and the classifiers stop at Python 3.10.
- Recommendation: review the supported Python range.

```json
{
  "commit": "fb8f495582f68d8d49f57b42d12a66802f9ac238",
  "runtime_dependencies": [
    {"name": "sqlite-fts4", "constraint": ""},
    {"name": "click", "constraint": ""},
    {"name": "click-default-group-wheel", "constraint": ""},
    {"name": "tabulate", "constraint": ""},
    {"name": "python-dateutil", "constraint": ""}
  ],
  "optional_groups": {
    "test": ["pytest", "black", "hypothesis", "cogapp"],
    "docs": ["furo", "sphinx-autobuild", "codespell", "sphinx-copybutton", "beanbag-docutils"],
    "mypy": ["mypy", "types-click", "types-tabulate", "types-python-dateutil", "data-science-types"],
    "flake8": ["flake8"]
  },
  "imports": {
    "sqlite-fts4": ["sqlite_utils/db.py"],
    "click": ["sqlite_utils/cli.py", "sqlite_utils/utils.py"],
    "click-default-group-wheel": ["sqlite_utils/cli.py"],
    "tabulate": ["sqlite_utils/cli.py"],
    "python-dateutil": ["sqlite_utils/recipes.py"]
  },
  "unused_dependencies": [],
  "undeclared_imports": [
    {"module": "pysqlite3", "files": ["sqlite_utils/utils.py"], "optional": true},
    {"module": "pandas", "files": ["sqlite_utils/db.py"], "optional": true},
    {"module": "numpy", "files": ["sqlite_utils/db.py"], "optional": true}
  ],
  "unpinned": ["sqlite-fts4", "click", "click-default-group-wheel", "tabulate", "python-dateutil"]
}
```