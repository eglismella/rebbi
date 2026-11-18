# Dependency audit: sqlite-utils 3.38

## 1. Scope
- Repository: `./target` (sqlite-utils, version 3.38 per `setup.py`)
- Commit: `9d7da0606e98713896bbc9fc885a5b0cd54ac2fd`
- Manifest files read: `setup.py` (the `install_requires` and `extras_require` lists). `setup.cfg` was present but not needed for the dependency lists. All `.py` files under `sqlite_utils/` were scanned with an AST import scan (`scan_imports.py`).

## 2. Runtime dependencies
Declared in `install_requires`, exactly as written:
- `sqlite-fts4`
- `click`
- `click-default-group>=1.2.3`
- `tabulate`
- `python-dateutil`
- `pluggy`

## 3. Optional dependency groups
- `test`: pytest, black, hypothesis, cogapp
- `docs`: furo, sphinx-autobuild, codespell, sphinx-copybutton, beanbag-docutils, pygments-csv-lexer
- `mypy`: mypy, types-click, types-tabulate, types-python-dateutil, types-pluggy, data-science-types
- `flake8`: flake8
- `tui`: trogon

## 4. Where runtime dependencies are used
- `sqlite-fts4`: `sqlite_utils/db.py`
- `click`: `sqlite_utils/cli.py`, `sqlite_utils/utils.py`
- `click-default-group`: `sqlite_utils/cli.py`
- `tabulate`: `sqlite_utils/cli.py`
- `python-dateutil`: `sqlite_utils/recipes.py` (imported as `dateutil`)
- `pluggy`: `sqlite_utils/hookspecs.py`, `sqlite_utils/plugins.py`

## 5. Unused and undeclared
Unused runtime dependencies: none. Every declared runtime dependency is imported by at least one file.

Undeclared third-party imports (declared neither as runtime nor optional). All are optional, guarded by `try` / `except ImportError`:
- `numpy`: `sqlite_utils/db.py` (optional)
- `pandas`: `sqlite_utils/db.py` (optional)
- `pysqlite3`: `sqlite_utils/utils.py` (optional)
- `sqlean`: `sqlite_utils/utils.py` (optional)
- `sqlite_dump`: `sqlite_utils/db.py` (optional)

Note: `trogon` is imported optionally in `sqlite_utils/cli.py` but is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
Runtime dependencies with no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`. Only `click-default-group` has a constraint (`>=1.2.3`).

## 7. Risks and recommendations
- Five of six runtime dependencies are unconstrained, so a breaking upstream release (notably `click`, `pluggy`) can break installs. Recommend at least lower bounds, and consider upper bounds on majors for `click` and `pluggy`.
- `numpy`, `pandas`, `sqlite_dump`, `pysqlite3` and `sqlean` are used but declared nowhere. Recommend documenting them, or adding extras (e.g. a `pandas` extra, a `sqlite-dump` extra) so users can discover and pin them.
- `sqlite_utils/utils.py` uses `__import__` on user-supplied import names in the `--import` / code-evaluation helper, so those modules are dynamic and not visible to static audits. Document this.
- The `mypy` extra includes `data-science-types`, which is unmaintained; consider removing it.

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
    {"module": "numpy", "files": ["sqlite_utils/db.py"], "optional": true},
    {"module": "pandas", "files": ["sqlite_utils/db.py"], "optional": true},
    {"module": "pysqlite3", "files": ["sqlite_utils/utils.py"], "optional": true},
    {"module": "sqlean", "files": ["sqlite_utils/utils.py"], "optional": true},
    {"module": "sqlite_dump", "files": ["sqlite_utils/db.py"], "optional": true}
  ],
  "unpinned": ["sqlite-fts4", "click", "tabulate", "python-dateutil", "pluggy"]
}
```
