## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest files read: `setup.py`. `setup.cfg` is also present, but I did not read it. `setup.py` holds the dependency declarations.
- Source searched for imports: all `.py` files under `sqlite_utils/`. These are `cli.py`, `db.py`, `utils.py`, `plugins.py`, `hookspecs.py` and `recipes.py`.
- Not covered: I searched import statements only for `import x` and `from x import` forms. I did not search for relative imports or dynamic imports.

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
- Undeclared third-party imports. None of these is declared in `install_requires` or `extras_require`, and all of them are optional (wrapped in `try` / `except ImportError`):
  - `sqlite_dump`: `sqlite_utils/db.py`.
  - `pandas`: `sqlite_utils/db.py`.
  - `numpy`: `sqlite_utils/db.py`.
  - `pysqlite3`: `sqlite_utils/utils.py`. If it is missing, the code falls back to `sqlean`.
  - `sqlean`: `sqlite_utils/utils.py`. If it is missing, the code falls back to the standard-library `sqlite3`.
- `trogon` is imported optionally in `sqlite_utils/cli.py`. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
Five of the six runtime dependencies have no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil` and `pluggy`. Only `click-default-group` has one (`>=1.2.3`).

## 7. Risks and recommendations
- Risk: unconstrained dependencies can pull in breaking major releases of `click`, `pluggy` and the others.
  - Recommendation: add lower bounds, and upper bounds where appropriate, to the five unpinned runtime dependencies.
- Risk: `sqlite_dump`, `pandas`, `numpy`, `pysqlite3` and `sqlean` are used optionally but declared nowhere, so users have no declared way to install them.
  - Recommendation: add an extras group such as `extras_require["optional"]` that lists them.
- Risk: `mypy` lists `types-pluggy` and `data-science-types`, which may be obsolete.
  - Recommendation: review those two stub packages and remove them if they are no longer needed.

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