## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest files read: `setup.py`. No other manifest file was read.
- Imports were searched in `sqlite_utils/*.py` with a line-start regex for `import` and `from`.

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
- `sqlite-fts4` (imported as `sqlite_fts4`): `sqlite_utils/db.py`
- `click`: `sqlite_utils/cli.py`, `sqlite_utils/utils.py`
- `click-default-group` (imported as `click_default_group`): `sqlite_utils/cli.py`
- `tabulate`: `sqlite_utils/cli.py`
- `python-dateutil` (imported as `dateutil`): `sqlite_utils/recipes.py`
- `pluggy`: `sqlite_utils/hookspecs.py`, `sqlite_utils/plugins.py`

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports. All are optional, wrapped in `try` / `except ImportError`:
  - `sqlite_dump`: `sqlite_utils/db.py`. The fallback is `iterdump = None`.
  - `pandas`: `sqlite_utils/db.py`.
  - `numpy`: `sqlite_utils/db.py`.
  - `pysqlite3`: `sqlite_utils/utils.py`. It falls back to `sqlean`, then to the stdlib `sqlite3`.
  - `sqlean`: `sqlite_utils/utils.py`.
- `trogon` is imported optionally in `sqlite_utils/cli.py`. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
Runtime dependencies with no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`.

## 7. Risks and recommendations
- Five of the six runtime dependencies have no constraint, so a breaking upstream release could break installs. Add lower bounds, and upper bounds where breaking changes are known.
- `sqlite_dump`, `pandas`, `numpy`, `pysqlite3` and `sqlean` are used optionally but declared nowhere. Add extras for them, or document them as optional features.
- The `mypy` extra includes `data-science-types`, which is an old stub package. Check whether it is still maintained.
- Only `setup.py` was inspected. Version constraints set elsewhere, such as in a lock file, were not checked.

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
    "pluggy": ["sqlite_utils/hookspecs.py", "sqlite_utils/plugins.py"]
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