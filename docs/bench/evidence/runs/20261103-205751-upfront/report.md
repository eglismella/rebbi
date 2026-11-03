## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest files read: `setup.py`. `setup.cfg` and `MANIFEST.in` exist but I did not read them. I found no `pyproject.toml` or `requirements*.txt`.
- Imports were found by searching every `.py` file under `sqlite_utils/` with a regex for `import` and `from` statements. The search pattern did not match relative imports such as `from .db import`. Those can't pull in third-party modules, so I ignored them.

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
- sqlite-fts4 (imported as `sqlite_fts4`): `sqlite_utils/db.py`
- click: `sqlite_utils/cli.py`, `sqlite_utils/utils.py`
- click-default-group (imported as `click_default_group`): `sqlite_utils/cli.py`
- tabulate: `sqlite_utils/cli.py`
- python-dateutil (imported as `dateutil`): `sqlite_utils/recipes.py`
- pluggy: `sqlite_utils/plugins.py`, `sqlite_utils/hookspecs.py`

## 5. Unused and undeclared
- **Unused runtime dependencies:** none.
- **Undeclared third-party imports.** All of these are optional, meaning they sit inside `try` / `except ImportError`:
  - `sqlite_dump`: `sqlite_utils/db.py`
  - `pandas`: `sqlite_utils/db.py`
  - `numpy`: `sqlite_utils/db.py`
  - `pysqlite3`: `sqlite_utils/utils.py`
  - `sqlean`: `sqlite_utils/utils.py`
- `trogon` is imported optionally in `sqlite_utils/cli.py`. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
Runtime dependencies with no version constraint: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`.

## 7. Risks and recommendations
- **Unbounded dependencies.** Five of the six runtime dependencies have no constraint. A breaking upstream release could break installs. Add at least lower bounds, and consider upper bounds for `click` and `pluggy`.
- **Undeclared optional modules.** `sqlite_dump`, `pandas`, `numpy`, `pysqlite3` and `sqlean` are not in any extra. Consider adding extras for them, such as `pandas`, `numpy` and `sqlean`, so users can discover and install them.
- **Typing extra.** The `mypy` extra includes `data-science-types`. That package looks unmaintained, so check whether it is still needed.
- **Python version.** `python_requires` is `>=3.8`, which is end-of-life. Review that floor.

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