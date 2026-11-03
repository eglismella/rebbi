## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest files read: `setup.py`. `setup.cfg` is also present but I did not read it. There is no `pyproject.toml` or `requirements*.txt`.
- Source scanned: all `*.py` files under `sqlite_utils/`, searched for import and try/except lines.

## 2. Runtime dependencies
`install_requires` in `setup.py`:
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
- pluggy: `sqlite_utils/hookspecs.py`, `sqlite_utils/plugins.py`

## 5. Unused and undeclared
- **Unused runtime dependencies:** none. Every declared runtime dependency is imported by at least one file.
- **Undeclared third-party imports.** All of these are optional, meaning they sit inside `try` / `except ImportError`:
  - `sqlite_dump`: `sqlite_utils/db.py`. It falls back when missing.
  - `pandas`: `sqlite_utils/db.py`
  - `numpy`: `sqlite_utils/db.py`
  - `pysqlite3`: `sqlite_utils/utils.py`. It is tried first, and the code falls back to `sqlean`, then to stdlib `sqlite3`.
  - `sqlean`: `sqlite_utils/utils.py`
- `trogon` is imported optionally in `sqlite_utils/cli.py`. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
Runtime dependencies with no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`.

## 7. Risks and recommendations
- Five of the six runtime dependencies have no version constraint. A breaking upstream release, for example in `click`, `pluggy` or `tabulate`, could break installs. Add lower bounds, and upper bounds where appropriate.
- The optional imports (`sqlite_dump`, `pandas`, `numpy`, `pysqlite3`, `sqlean`) are not in any extras group. Add extras such as `pandas`, `numpy` and `sqlite-dump`, or document them, so users know which packages enable which features.
- The `mypy` extra includes `data-science-types`, a stub package for numpy/pandas that is no longer maintained. Consider replacing it.
- I did not read `setup.cfg`, so I cannot rule out extra configuration there.

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