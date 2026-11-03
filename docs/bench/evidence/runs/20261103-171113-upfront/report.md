## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest file read: `setup.py`. The repository also has `setup.cfg` and `MANIFEST.in`, which I did not read. I found no `pyproject.toml` or `requirements*.txt`.
- Source scanned: every `*.py` file under `sqlite_utils/`, by searching for import statements.

## 2. Runtime dependencies
These are the `install_requires` entries from `setup.py`:
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
**Unused runtime dependencies:** none. Every declared runtime dependency is imported by at least one file.

**Undeclared third-party imports.** None of these appear in `install_requires` or `extras_require`. All of them are optional, because each import sits in a `try` / `except ImportError`.

| Module | Files | Optional |
|---|---|---|
| `sqlite_dump` | `sqlite_utils/db.py` | yes |
| `pandas` | `sqlite_utils/db.py` | yes |
| `numpy` | `sqlite_utils/db.py` | yes |
| `pysqlite3` | `sqlite_utils/utils.py` | yes |
| `sqlean` | `sqlite_utils/utils.py` | yes |

`trogon` is imported optionally in `sqlite_utils/cli.py`. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
Runtime dependencies with no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`. Only `click-default-group` has a constraint.

## 7. Risks and recommendations
- **Unbounded dependencies:** five of the six runtime dependencies have no constraint, so a breaking upstream release could be installed silently. Add lower bounds, and upper bounds where an API is known to be unstable. `click` and `pluggy` are the most important to bound, because the CLI and plugin system depend on them directly.
- **Undeclared optional modules:** `sqlite_dump`, `pandas`, `numpy`, `pysqlite3` and `sqlean` are used but not declared in any extra. Their import guards make a missing package safe at runtime. Even so, the supported versions are undocumented and untested through the packaging metadata. Consider adding extras such as `pandas` and `sqlean` for them.
- **Stub package:** the `mypy` extra includes `data-science-types`. This is a stub package I did not look into any further, so check whether it is still maintained.
- **Manifests not read:** I did not read `setup.cfg`. Check it for any extra dependency or tool configuration.

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