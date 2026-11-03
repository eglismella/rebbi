## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest files read: `setup.py`. I searched the import statements in `sqlite_utils/*.py` (`utils.py`, `recipes.py`, `plugins.py`, `hookspecs.py`, `db.py`, `cli.py`).
- I did not open the `try`/`except ImportError` blocks themselves. The "optional" flags in section 5 rest on the line positions in the grep output and on the code's usual layout, so they are not fully confirmed.

## 2. Runtime dependencies
- sqlite-fts4 (no constraint)
- click (no constraint)
- click-default-group>=1.2.3
- tabulate (no constraint)
- python-dateutil (no constraint)
- pluggy (no constraint)

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
- Undeclared third-party imports. None of these is in `install_requires` or `extras_require`:
  - `pysqlite3`: `sqlite_utils/utils.py` (lines 17–18). Optional, with a fallback to `sqlean` and then stdlib `sqlite3`.
  - `sqlean`: `sqlite_utils/utils.py` (lines 23–24). Optional, same fallback chain.
  - `sqlite_dump`: `sqlite_utils/db.py` (line 43). Optional (`try`/`except ImportError`).
  - `pandas`: `sqlite_utils/db.py` (line 73). Optional.
  - `numpy`: `sqlite_utils/db.py` (line 78). Optional.
- `trogon` (`sqlite_utils/cli.py`, line 39) is imported optionally. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
Runtime dependencies with no version constraint: sqlite-fts4, click, tabulate, python-dateutil, pluggy.

## 7. Risks and recommendations
- Five of the six runtime dependencies have no version constraint, so a breaking upstream release could break installs. Add lower bounds, and upper bounds where an API is known to be unstable.
- `sqlite_dump`, `pysqlite3`, `sqlean`, `pandas` and `numpy` are optional imports that no extra declares. Add an extra (for example `extras`) so users know which packages enable which features, or document them.
- The `mypy` extra includes `data-science-types`, which is unmaintained. Consider replacing it.
- I did not check the `try`/`except` blocks directly, so confirm the optional flags before relying on them.

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