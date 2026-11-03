## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest files read: `setup.py`. A glob for `*.toml`, `*.cfg`, `*.txt` and `*.ini` also turned up `setup.cfg` and `mypy.ini`, but I did not open them. No `pyproject.toml` or `requirements*.txt` exists at the repository root.
- Source files searched for imports: `sqlite_utils/cli.py`, `db.py`, `utils.py`, `recipes.py`, `plugins.py` and `hookspecs.py`.

## 2. Runtime dependencies
From `install_requires` in `setup.py`:
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
- Undeclared third-party imports. All of them are optional, wrapped in `try` / `except ImportError`:
  - `sqlite_dump`: `sqlite_utils/db.py`, optional.
  - `pandas`: `sqlite_utils/db.py`, optional.
  - `numpy`: `sqlite_utils/db.py`, optional.
  - `pysqlite3`: `sqlite_utils/utils.py`, optional, with a fallback to `sqlean` and then stdlib `sqlite3`.
  - `sqlean`: `sqlite_utils/utils.py`, optional.
- `trogon` is imported optionally in `cli.py`. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
Runtime dependencies with no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`.

## 7. Risks and recommendations
- Five of the six runtime dependencies have no constraint at all. A breaking upstream release could break installs.
- Add lower bounds, and where sensible upper bounds, for the unpinned dependencies. The code uses `parser.ParserError` from dateutil and the pluggy hook markers, so `python-dateutil` and `pluggy` need versions that provide them.
- `sqlite_dump`, `pandas`, `numpy`, `pysqlite3` and `sqlean` are used but declared in no group. Add extras for them, for example `pandas`, `numpy` and `sqlite-dump`, or document them as optional.
- Two things need a check. The `mypy` extra includes `data-science-types`, which is old and unmaintained. The distribution name for `sqlite_dump` is probably `sqlite-dump`, but I did not verify it.
- Only `setup.py` was read for dependency declarations. I did not open `setup.cfg`, `mypy.ini` or the test files, and I did not check `__init__.py` or `__main__.py`.

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