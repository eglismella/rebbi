## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest file read: `setup.py`. I did not look for other manifests such as `requirements.txt` or `pyproject.toml`.
- Import search covered `sqlite_utils/*.py`: `cli.py`, `db.py`, `utils.py`, `recipes.py`, `plugins.py` and `hookspecs.py`.

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
- Unused runtime dependencies: none.
- Undeclared third-party imports. All are optional, wrapped in `try` / `except ImportError`:
  - `sqlite_dump` in `sqlite_utils/db.py`
  - `pandas` in `sqlite_utils/db.py`
  - `numpy` in `sqlite_utils/db.py`
  - `pysqlite3` in `sqlite_utils/utils.py`
  - `sqlean` in `sqlite_utils/utils.py`
- `trogon` is imported optionally in `cli.py`. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
- No version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`.

## 7. Risks and recommendations
- Five of the six runtime dependencies have no lower or upper bound. A breaking release of any of them could break installs.
- Recommendation: add minimum versions, and consider upper bounds for `click` and `pluggy`.
- The optional imports (`sqlite_dump`, `pandas`, `numpy`, `pysqlite3`, `sqlean`) are in no extra. Recommendation: document them, or add extras for them.
- The `mypy` extra includes `data-science-types`. That package is old and unmaintained, so consider replacing it.
- I read only `setup.py` for declarations. The import search used line-start patterns, so it could miss imports that are indented or written another way.

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