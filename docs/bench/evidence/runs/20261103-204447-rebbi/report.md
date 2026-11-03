# dep-audit-v1: sqlite-utils

## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest files read: `setup.py`. I found no other manifest in the repository. I did not search for `pyproject.toml` or `requirements*.txt`.
- Imports were checked with a Grep over `sqlite_utils/*.py`: `utils.py`, `recipes.py`, `db.py`, `hookspecs.py`, `plugins.py` and `cli.py`.

## 2. Runtime dependencies
- `sqlite-fts4`
- `click`
- `click-default-group>=1.2.3`
- `tabulate`
- `python-dateutil`
- `pluggy`

## 3. Optional dependency groups
- test: pytest, black, hypothesis, cogapp
- docs: furo, sphinx-autobuild, codespell, sphinx-copybutton, beanbag-docutils, pygments-csv-lexer
- mypy: mypy, types-click, types-tabulate, types-python-dateutil, types-pluggy, data-science-types
- flake8: flake8
- tui: trogon

## 4. Where runtime dependencies are used
- sqlite-fts4 (imported as `sqlite_fts4`): `sqlite_utils/db.py`
- click: `sqlite_utils/cli.py`, `sqlite_utils/utils.py`
- click-default-group (imported as `click_default_group`): `sqlite_utils/cli.py`
- tabulate: `sqlite_utils/cli.py`
- python-dateutil (imported as `dateutil`): `sqlite_utils/recipes.py`
- pluggy: `sqlite_utils/plugins.py`, `sqlite_utils/hookspecs.py`

## 5. Unused and undeclared
- **Unused runtime dependencies:** none.
- **Undeclared third-party imports.** All of these are optional, meaning they sit inside `try` / `except ImportError`:
  - `sqlite_dump` in `sqlite_utils/db.py`
  - `pandas` in `sqlite_utils/db.py`
  - `numpy` in `sqlite_utils/db.py`
  - `pysqlite3` in `sqlite_utils/utils.py`
  - `sqlean` in `sqlite_utils/utils.py`
- `trogon` is imported optionally in `sqlite_utils/cli.py`. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
Five runtime dependencies have no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`.

## 7. Risks and recommendations
- **Unbounded dependencies:** the five unconstrained packages can pull in breaking major releases. Add lower bounds for the APIs the package uses, and consider upper bounds for `click` and `pluggy`.
- **Undeclared optional imports:** `sqlite_dump`, `pandas`, `numpy`, `pysqlite3` and `sqlean` are not declared in any group. Add an extra, such as `sqlite-dump` or `pysqlite3`, so users can see which optional features exist.
- **Stale mypy extra:** `data-science-types` is an old, unmaintained package. Consider replacing it.
- **Limits of this check:** I only read `setup.py` and the imports in the package source. I did not check for dynamic imports or for how the code uses each module.

```json
{
  "commit": "9d7da0606e98713896bbc9fc885a5b0cd54ac2fd",
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
    "sqlite-fts4": ["sqlite_utils/db.py"],
    "click": ["sqlite_utils/cli.py", "sqlite_utils/utils.py"],
    "click-default-group": ["sqlite_utils/cli.py"],
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