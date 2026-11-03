## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest files read: `setup.py`. I did not read any other manifest, such as `requirements*.txt`, `pyproject.toml` or `setup.cfg`.
- Imports were checked with a grep of the top-level `import` and `from` statements in `sqlite_utils/*.py`.

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
- pluggy: `sqlite_utils/hookspecs.py`, `sqlite_utils/plugins.py`

## 5. Unused and undeclared
**Unused runtime dependencies:** none.

**Undeclared third-party imports.** All of these are optional, because each sits inside a `try` / `except ImportError`.

| Module | Files | Optional |
|---|---|---|
| `sqlite_dump` | `sqlite_utils/db.py` | yes |
| `pandas` | `sqlite_utils/db.py` | yes |
| `numpy` | `sqlite_utils/db.py` | yes |
| `pysqlite3` | `sqlite_utils/utils.py` | yes |
| `sqlean` | `sqlite_utils/utils.py` | yes |

`trogon` is imported optionally in `cli.py`. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
These runtime dependencies have no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`.

## 7. Risks and recommendations
- Five of the six runtime dependencies have no lower or upper bound. A breaking release of any of them could break installs. This matters most for `click` and `pluggy`, which the package uses heavily.
- Recommendation: add tested minimum versions for the unpinned runtime dependencies. Consider upper bounds or a CI job that tests against the latest releases.
- `sqlite_dump`, `pandas`, `numpy`, `pysqlite3` and `sqlean` are optional imports that no extra declares. Recommendation: add an extra such as `pandas` or `sqlean`, or document them, so users know which versions are supported.
- The `mypy` extra includes `data-science-types`, which is old and unmaintained. Recommendation: review whether it is still needed.
- I read only `setup.py`. Other manifests or tests could change the picture.

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