## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: `9d7da0606e98713896bbc9fc885a5b0cd54ac2fd`
- Manifest files read: `setup.py`. I found no other manifest in the search. I did not check for `pyproject.toml` or requirements files.
- Source files searched for imports: all `.py` files under `sqlite_utils/`.

## 2. Runtime dependencies
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

Undeclared third-party imports. `trogon` is imported in `cli.py` inside a `try`/`except ImportError`, but it is declared in the `tui` extra, so it is not listed here.

| Module | Files | Optional (`try`/`except ImportError`) |
|---|---|---|
| `sqlite_dump` | `sqlite_utils/db.py` | yes |
| `pandas` | `sqlite_utils/db.py` | yes |
| `numpy` | `sqlite_utils/db.py` | yes |
| `pysqlite3` | `sqlite_utils/utils.py` | yes |
| `sqlean` | `sqlite_utils/utils.py` | yes |

## 6. Version pinning
Runtime dependencies with no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`.

## 7. Risks and recommendations
- Five of the six runtime dependencies have no version bounds. A breaking upstream release could break installs. Add minimum versions, and upper bounds where the risk is real.
- The optional imports (`sqlite_dump`, `pandas`, `numpy`, `pysqlite3`, `sqlean`) are declared in no extra. Users cannot install them through the package's own extras. Add extras such as `pandas` and `sqlite-dump`, or document them.
- The `mypy` extra includes `data-science-types`, which I believe is an unmaintained package. Review whether it is still needed.
- `python_requires>=3.8` is declared, and Python 3.8 is end-of-life. Consider raising the minimum.

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