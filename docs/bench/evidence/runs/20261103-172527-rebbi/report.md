# dep-audit-v1: sqlite-utils

## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest files read: `setup.py`. `setup.cfg` is also present, but I did not read it. All dependency declarations come from `setup.py`.
- Import scan: top-level `import` and `from` statements in `sqlite_utils/*.py`. I matched statements that start with a word character, so relative imports such as `from .db import` would not appear in the results.

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
- Undeclared third-party imports. All of them are optional, because each sits inside `try` / `except ImportError`:
  - `pysqlite3`: `sqlite_utils/utils.py`. It is tried first, with a fallback to `sqlean`, then to the standard-library `sqlite3`.
  - `sqlean`: `sqlite_utils/utils.py`
  - `sqlite_dump`: `sqlite_utils/db.py`
  - `pandas`: `sqlite_utils/db.py`
  - `numpy`: `sqlite_utils/db.py`
- `trogon` is imported optionally in `sqlite_utils/cli.py`. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
Five of the six runtime dependencies have no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`. Only `click-default-group` is constrained (`>=1.2.3`), and it has no upper bound.

## 7. Risks and recommendations
- Unbounded runtime dependencies can pull in breaking major releases. `click` and `pluggy` are the most exposed. Recommend adding lower bounds, and upper bounds where compatibility is known.
- The optional imports (`pysqlite3`, `sqlean`, `sqlite_dump`, `pandas`, `numpy`) are not declared in any extra. Recommend adding extras for them, or documenting them, so the optional behaviour is reproducible.
- The `mypy` extra lists `data-science-types`, which is an old stub package. Recommend reviewing whether it is still needed.
- I did not read `setup.cfg`. Recommend checking that it holds no conflicting dependency metadata.

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
    {"module": "pysqlite3", "files": ["sqlite_utils/utils.py"], "optional": true},
    {"module": "sqlean", "files": ["sqlite_utils/utils.py"], "optional": true},
    {"module": "sqlite_dump", "files": ["sqlite_utils/db.py"], "optional": true},
    {"module": "pandas", "files": ["sqlite_utils/db.py"], "optional": true},
    {"module": "numpy", "files": ["sqlite_utils/db.py"], "optional": true}
  ],
  "unpinned": ["sqlite-fts4", "click", "tabulate", "python-dateutil", "pluggy"]
}
```