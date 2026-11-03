## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest files read: `setup.py`. The only other manifest-like files found were `setup.cfg` and `MANIFEST.in`, and I did not read them.
- Source searched: all files under `sqlite_utils/`, for import statements.

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
- Undeclared third-party imports, all optional:
  - `sqlite_dump`: `sqlite_utils/db.py`. Optional, in `try`/`except ImportError`.
  - `pandas`: `sqlite_utils/db.py`. Optional, in `try`/`except ImportError`.
  - `numpy`: `sqlite_utils/db.py`. Optional, in `try`/`except ImportError`.
  - `pysqlite3`: `sqlite_utils/utils.py`. Optional, tried first, with fallback.
  - `sqlean`: `sqlite_utils/utils.py`. Optional, tried second, with fallback to stdlib `sqlite3`.
- `trogon` is imported in `sqlite_utils/cli.py` inside `try`/`except ImportError`. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
Runtime dependencies with no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`.

## 7. Risks and recommendations
- Five of the six runtime dependencies have no constraint, so a breaking upstream release could break installs. Recommendation: add lower bounds, and upper bounds where an API is known to be unstable.
- Several optional imports (`sqlite_dump`, `pandas`, `numpy`, `pysqlite3`, `sqlean`) are in no extras group. Recommendation: add extras groups for them, or document them, so users know which packages enable which features.
- The `mypy` extra includes `data-science-types`, which is an old package. Recommendation: review whether it is still needed.
- `types-pluggy` is a stubs package for `pluggy`. Recommendation: check whether it is still needed, since `pluggy` ships its own type hints.
- I only searched import lines, so I would not have caught dynamic imports such as `importlib`.

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