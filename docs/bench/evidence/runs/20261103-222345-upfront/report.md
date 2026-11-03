## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: `9d7da0606e98713896bbc9fc885a5b0cd54ac2fd`
- Manifest files read: `setup.py`. `setup.cfg` is also present but I did not read it. I found no `pyproject.toml` or `requirements*.txt`.
- Source files searched for imports: all of `sqlite_utils/*.py`, which are `__init__.py`, `__main__.py`, `cli.py`, `db.py`, `hookspecs.py`, `plugins.py`, `recipes.py` and `utils.py`.

## 2. Runtime dependencies
`install_requires` in `setup.py`:
- `sqlite-fts4` (no constraint)
- `click` (no constraint)
- `click-default-group>=1.2.3`
- `tabulate` (no constraint)
- `python-dateutil` (no constraint)
- `pluggy` (no constraint)

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
Unused runtime dependencies: none.

Undeclared third-party imports. All are optional, meaning they sit inside `try` / `except ImportError`:
- `sqlite_dump`: `sqlite_utils/db.py`, optional
- `pandas`: `sqlite_utils/db.py`, optional
- `numpy`: `sqlite_utils/db.py`, optional
- `pysqlite3`: `sqlite_utils/utils.py`, optional
- `sqlean`: `sqlite_utils/utils.py`, optional

`trogon` is imported in an optional block in `cli.py`, but it is declared in the `tui` extra, so it is not undeclared.

I did not open the `try` blocks in `utils.py` (lines 16–30). I judged `pysqlite3` and `sqlean` to be optional from the nested import fallbacks that the search output showed, ending in plain `sqlite3`.

## 6. Version pinning
Runtime dependencies with no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`.

## 7. Risks and recommendations
- Five of the six runtime dependencies have no lower or upper bound. A breaking release of any of them could break installs.
- Recommendation: add minimum versions for the APIs the package actually uses, for example `click` and `pluggy`. Consider upper bounds or a lock file for CI.
- `sqlite_dump`, `pandas`, `numpy`, `pysqlite3` and `sqlean` are optional imports that no extra declares. Recommendation: declare them in extras, such as a `tui`-style group, or document them so users know how to enable those features.
- The `mypy` extra includes `data-science-types`, which is an old, unmaintained package. Recommendation: review whether it is still needed.

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