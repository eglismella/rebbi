# dep-audit-v1: sqlite-utils

## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest files read: `setup.py`. I did not look for `pyproject.toml` or requirements files.
- Source files searched for imports: all `*.py` files in `sqlite_utils/`. Imports were found in `db.py`, `cli.py`, `utils.py`, `plugins.py`, `hookspecs.py` and `recipes.py`.
- Method: a grep of import lines, plus reads of the `try`/`except` blocks in `db.py` and `utils.py`. I did not read every file in full.

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
- `pluggy`: `sqlite_utils/plugins.py`, `sqlite_utils/hookspecs.py`

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports. All of them are optional, each inside a `try` / `except ImportError`:
  - `sqlite_dump`: `sqlite_utils/db.py`. If missing, `iterdump` is set to `None`.
  - `pandas`: `sqlite_utils/db.py`. If missing, `pd` is set to `None`.
  - `numpy`: `sqlite_utils/db.py`. If missing, `np` is set to `None`.
  - `pysqlite3`: `sqlite_utils/utils.py`. Falls back to `sqlean`, then to the standard `sqlite3`.
  - `sqlean`: `sqlite_utils/utils.py`. Same fallback chain.
- `trogon` is imported in `sqlite_utils/cli.py` (line 39, inside an optional-import block that I did not read). It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
Runtime dependencies with no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`.

## 7. Risks and recommendations
- Five of the six runtime dependencies have no lower or upper bound, so a breaking release of any of them could break installs. Recommendation: add at least lower bounds, and consider upper bounds for `click` and `pluggy`.
- `sqlite_dump`, `pandas`, `numpy`, `pysqlite3` and `sqlean` are used when present but declared nowhere. Recommendation: add an extras group for the ones you want to support, or document them as optional.
- The `mypy` extra includes `data-science-types`, which is an old stub package. Recommendation: check whether it is still needed.
- The version of `black` in the `test` extra is pinned with a lower bound only, and `beanbag-docutils` in the `docs` extra likewise. Recommendation: consider a lock file or CI constraints to keep these reproducible.

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