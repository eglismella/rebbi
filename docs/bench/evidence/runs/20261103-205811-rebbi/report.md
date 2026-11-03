## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest files read: `setup.py`. I did not check for `pyproject.toml` or requirements files.
- Source searched: import statements in `sqlite_utils/*.py`.

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
- sqlite-fts4: `sqlite_utils/db.py`
- click: `sqlite_utils/cli.py`, `sqlite_utils/utils.py`
- click-default-group: `sqlite_utils/cli.py`
- tabulate: `sqlite_utils/cli.py`
- python-dateutil: `sqlite_utils/recipes.py`
- pluggy: `sqlite_utils/hookspecs.py`, `sqlite_utils/plugins.py`

## 5. Unused and undeclared
Unused runtime dependencies: none.

Undeclared third-party imports:

| Module | Files | Optional (try/except ImportError) |
|---|---|---|
| `sqlite_dump` | `sqlite_utils/db.py` | yes |
| `pandas` | `sqlite_utils/db.py` | yes |
| `numpy` | `sqlite_utils/db.py` | yes |
| `pysqlite3` | `sqlite_utils/utils.py` | yes |
| `sqlean` | `sqlite_utils/utils.py` | yes |

`trogon` is imported optionally in `cli.py`. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
Five of the six runtime dependencies have no version constraint: sqlite-fts4, click, tabulate, python-dateutil and pluggy. Only click-default-group has one.

## 7. Risks and recommendations
- Unconstrained runtime dependencies can pick up breaking releases, especially `click` and `pluggy`. Add lower bounds, and upper bounds where a major version has broken things before.
- `sqlite_dump`, `pandas`, `numpy`, `pysqlite3` and `sqlean` are optional imports that no extra declares. Add extras for them, or document them, so users know how to enable those features.
- The `mypy` extra includes `data-science-types`, which is unmaintained. Review whether it is still needed.
- This audit read only `setup.py`. Check for other manifests such as `pyproject.toml` or requirements files that could conflict with it.

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