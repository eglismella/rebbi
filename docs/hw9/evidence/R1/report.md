# Dependency audit: sqlite-utils 3.38

## 1. Scope
Repository: sqlite-utils 3.38 (`./target`, version from `setup.py`). Commit: NOT DETERMINABLE. The folder has no `.git` metadata and no file records a commit hash, so none is stated rather than inventing one (the JSON uses `"unknown"`). Manifest files read: `setup.py` (the source of `install_requires` and `extras_require`). Package sources scanned: `sqlite_utils/*.py` (`__init__`, `__main__`, `cli`, `db`, `hookspecs`, `plugins`, `recipes`, `utils`).

## 2. Runtime dependencies
- sqlite-fts4
- click
- click-default-group>=1.2.3
- tabulate
- python-dateutil
- pluggy

## 3. Optional dependency groups
- test: pytest, black, hypothesis, cogapp
- docs: furo, sphinx-autobuild, codespell, sphinx-copybutton, beanbag-docutils, pygments-csv-lexer
- mypy: mypy, types-click, types-tabulate, types-python-dateutil, types-pluggy, data-science-types
- flake8: flake8
- tui: trogon

## 4. Where runtime dependencies are used
- click: sqlite_utils/cli.py, sqlite_utils/utils.py
- click-default-group (`click_default_group`): sqlite_utils/cli.py
- sqlite-fts4 (`sqlite_fts4`): sqlite_utils/db.py
- tabulate: sqlite_utils/cli.py
- python-dateutil (`dateutil`): sqlite_utils/recipes.py
- pluggy: sqlite_utils/plugins.py, sqlite_utils/hookspecs.py

## 5. Unused and undeclared
Unused runtime dependencies: none.

Undeclared third-party imports (declared neither as runtime nor optional):
- sqlite_dump: sqlite_utils/db.py, optional (try/except ImportError)
- pandas: sqlite_utils/db.py, optional
- numpy: sqlite_utils/db.py, optional
- pysqlite3: sqlite_utils/utils.py, optional
- sqlean: sqlite_utils/utils.py, optional

`trogon` (sqlite_utils/cli.py, optional) is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
No version constraint: sqlite-fts4, click, tabulate, python-dateutil, pluggy. Only click-default-group has one (>=1.2.3). No upper bounds anywhere.

## 7. Risks and recommendations
- Recommend adding minimum versions to the five unconstrained runtime dependencies, so installs are reproducible and break less on incompatible releases.
- Recommend declaring the optional imports (`sqlite-dump`, `pandas`, `numpy`, `pysqlite3`/`sqlean`) in an extras group so users can discover them.
- The `mypy` extra includes `data-science-types`, which is unmaintained; consider dropping it.
- The audit could not be pinned to a commit; record the hash with the repository snapshot.

```json
{
  "commit": "unknown",
  "runtime_dependencies": [
    {"name": "sqlite-fts4", "constraint": ""},
    {"name": "click", "constraint": ""},
    {"name": "click-default-group", "constraint": ">=1.2.3"},
    {"name": "tabulate", "constraint": ""},
    {"name": "python-dateutil", "constraint": ""},
    {"name": "pluggy", "constraint": ""}
  ],
  "optional_groups": {
    "test": ["pytest", "black", "hypothesis", "cogapp"],
    "docs": ["furo", "sphinx-autobuild", "codespell", "sphinx-copybutton", "beanbag-docutils", "pygments-csv-lexer"],
    "mypy": ["mypy", "types-click", "types-tabulate", "types-python-dateutil", "types-pluggy", "data-science-types"],
    "flake8": ["flake8"],
    "tui": ["trogon"]
  },
  "imports": {
    "click": ["sqlite_utils/cli.py", "sqlite_utils/utils.py"],
    "click-default-group": ["sqlite_utils/cli.py"],
    "sqlite-fts4": ["sqlite_utils/db.py"],
    "tabulate": ["sqlite_utils/cli.py"],
    "python-dateutil": ["sqlite_utils/recipes.py"],
    "pluggy": ["sqlite_utils/plugins.py", "sqlite_utils/hookspecs.py"]
  },
  "unused_dependencies": [],
  "undeclared_imports": [
    {"module": "sqlite_dump", "files": ["sqlite_utils/db.py"], "optional": true},
    {"module": "pandas", "files": ["sqlite_utils/db.py"], "optional": true},
    {"module": "numpy", "files": ["sqlite_utils/db.py"], "optional": true},
    {"module": "pysqlite3", "files": ["sqlite_utils/utils.py"], "optional": true},
    {"module": "sqlean", "files": ["sqlite_utils/utils.py"], "optional": true}
  ],
  "unpinned": ["sqlite-fts4", "click", "tabulate", "python-dateutil", "pluggy"]
}
```
