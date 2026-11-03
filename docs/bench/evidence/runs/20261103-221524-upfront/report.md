# sqlite-utils dependency audit (job dep-audit-v1)

## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest files read: `setup.py`. I did not look for other manifests such as `pyproject.toml` or `requirements*.txt`.
- Source files checked for imports: all `*.py` files under `sqlite_utils/`, using a grep of import and `try`/`except` lines. Relative imports such as `from .db import` would not show up in that grep.

## 2. Runtime dependencies
`install_requires` in `setup.py` declares:
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
- `sqlite-fts4` is imported as `sqlite_fts4` in `sqlite_utils/db.py`.
- `click` is imported in `sqlite_utils/cli.py` and `sqlite_utils/utils.py`.
- `click-default-group` is imported as `click_default_group` in `sqlite_utils/cli.py`.
- `tabulate` is imported in `sqlite_utils/cli.py`.
- `python-dateutil` is imported as `dateutil` in `sqlite_utils/recipes.py`.
- `pluggy` is imported in `sqlite_utils/plugins.py` and `sqlite_utils/hookspecs.py`.

## 5. Unused and undeclared
**Unused runtime dependencies:** none.

**Undeclared third-party imports.** None of these appear in `install_requires` or `extras_require`. All are optional, because each is guarded by `try`/`except ImportError`.

| Module | Files | Optional |
|---|---|---|
| `sqlite_dump` | `sqlite_utils/db.py` | yes |
| `pandas` | `sqlite_utils/db.py` | yes |
| `numpy` | `sqlite_utils/db.py` | yes |
| `pysqlite3` | `sqlite_utils/utils.py` | yes, falls back to `sqlean`, then to stdlib `sqlite3` |
| `sqlean` | `sqlite_utils/utils.py` | yes |

`trogon` is imported optionally in `sqlite_utils/cli.py`. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
Runtime dependencies with no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`.

## 7. Risks and recommendations
- **Unbounded dependencies.** Five of the six runtime dependencies have no version constraint. A breaking release of any of them could break installs. Add lower bounds, and consider upper bounds for `click` and `pluggy`.
- **Undeclared optional modules.** `sqlite_dump`, `pandas`, `numpy`, `pysqlite3` and `sqlean` are used but declared nowhere. Add extras for them, for example `sqlite-dump`, `pandas` and `numpy`. This makes the optional features discoverable and the versions testable.
- **Dev tooling in extras.** `data-science-types` in the `mypy` extra is old and unmaintained. Review whether it is still needed.
- **Manifest coverage.** I read only `setup.py`. Confirm there is no other manifest that overrides or supplements it.

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