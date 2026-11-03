## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest files read: `setup.py`. I did not read any other manifest, such as `pyproject.toml` or requirements files.
- Imports were searched in all `.py` files under `sqlite_utils/`. Only `plugins.py`, `hookspecs.py`, `utils.py`, `recipes.py`, `cli.py` and `db.py` had matching import lines.
- I read the `try`/`except` blocks around the optional imports in `db.py`, `utils.py` and `cli.py`.

## 2. Runtime dependencies
- `sqlite-fts4`
- `click`
- `click-default-group>=1.2.3`
- `tabulate`
- `python-dateutil`
- `pluggy`

## 3. Optional dependency groups
- **test:** pytest, black, hypothesis, cogapp
- **docs:** furo, sphinx-autobuild, codespell, sphinx-copybutton, beanbag-docutils, pygments-csv-lexer
- **mypy:** mypy, types-click, types-tabulate, types-python-dateutil, types-pluggy, data-science-types
- **flake8:** flake8
- **tui:** trogon

## 4. Where runtime dependencies are used
- **sqlite-fts4** (imported as `sqlite_fts4`): `sqlite_utils/db.py`
- **click:** `sqlite_utils/cli.py`, `sqlite_utils/utils.py`
- **click-default-group** (imported as `click_default_group`): `sqlite_utils/cli.py`
- **tabulate:** `sqlite_utils/cli.py`
- **python-dateutil** (imported as `dateutil`): `sqlite_utils/recipes.py`
- **pluggy:** `sqlite_utils/plugins.py`, `sqlite_utils/hookspecs.py`

## 5. Unused and undeclared
- **Unused runtime dependencies:** none.
- **Undeclared third-party imports.** All are optional, meaning they sit inside `try`/`except ImportError`:
  - `pysqlite3`: `sqlite_utils/utils.py`. It is tried first as the sqlite3 implementation.
  - `sqlean`: `sqlite_utils/utils.py`. It is the fallback if `pysqlite3` is missing, and the standard `sqlite3` is the last fallback.
  - `sqlite_dump`: `sqlite_utils/db.py`. If it is missing, `iterdump` is set to `None`.
  - `pandas`: `sqlite_utils/db.py`
  - `numpy`: `sqlite_utils/db.py`
- `trogon` is imported optionally in `sqlite_utils/cli.py`. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
Five of the six runtime dependencies have no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil` and `pluggy`. Only `click-default-group` is constrained (`>=1.2.3`).

## 7. Risks and recommendations
- The unconstrained runtime dependencies can pick up breaking releases. Add lower bounds, and upper bounds where appropriate, at least for `click`, `pluggy` and `tabulate`.
- `pysqlite3`, `sqlean`, `sqlite_dump`, `pandas` and `numpy` are used but declared in no extra. Add extras such as `pandas` and `sqlite-dump`, or document them as optional features, so users know which packages enable which features.
- The `mypy` extra includes `data-science-types`. I did not check whether it is still maintained, so verify that before relying on it.
- `setup.py` declares `python_requires>=3.8`. I did not check whether the dependencies still support that Python version.

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
    {"module": "pysqlite3", "files": ["sqlite_utils/utils.py"], "optional": true},
    {"module": "sqlean", "files": ["sqlite_utils/utils.py"], "optional": true},
    {"module": "sqlite_dump", "files": ["sqlite_utils/db.py"], "optional": true},
    {"module": "pandas", "files": ["sqlite_utils/db.py"], "optional": true},
    {"module": "numpy", "files": ["sqlite_utils/db.py"], "optional": true}
  ],
  "unpinned": ["sqlite-fts4", "click", "tabulate", "python-dateutil", "pluggy"]
}
```