## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: fb8f495582f68d8d49f57b42d12a66802f9ac238
- Manifest files read: `setup.py`. I did not read `requirements*.txt`, `pyproject.toml` or `setup.cfg`.
- Imports were searched in `sqlite_utils/*.py`. I searched only for absolute `import x` and `from x import` lines, so relative imports (for example in `__init__.py`) were not covered.

## 2. Runtime dependencies
`install_requires` in `setup.py`:
- `sqlite-fts4`
- `click`
- `click-default-group-wheel`
- `tabulate`
- `python-dateutil`

None has a version constraint.

## 3. Optional dependency groups
- test: pytest, black, hypothesis, cogapp
- docs: furo, sphinx-autobuild, codespell, sphinx-copybutton, beanbag-docutils
- mypy: mypy, types-click, types-tabulate, types-python-dateutil, data-science-types
- flake8: flake8

## 4. Where runtime dependencies are used
- sqlite-fts4 (imported as `sqlite_fts4`): `sqlite_utils/db.py`
- click: `sqlite_utils/cli.py`, `sqlite_utils/utils.py`
- click-default-group-wheel (imported as `click_default_group`): `sqlite_utils/cli.py`
- tabulate: `sqlite_utils/cli.py`
- python-dateutil (imported as `dateutil`): `sqlite_utils/recipes.py`

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports, none of which appear in any extras group:
  - `pysqlite3`: `sqlite_utils/utils.py`. Optional, inside `try` / `except ImportError` with a fallback to `sqlite3`.
  - `pandas`: `sqlite_utils/db.py`. Optional, inside `try` / `except ImportError`.
  - `numpy`: `sqlite_utils/db.py`. Optional, inside `try` / `except ImportError`.

## 6. Version pinning
All five runtime dependencies have no version constraint: sqlite-fts4, click, click-default-group-wheel, tabulate, python-dateutil.

## 7. Risks and recommendations
- Unbounded runtime dependencies mean a breaking release of click or tabulate could break installs. Add lower bounds, and upper bounds where compatibility is known.
- `pysqlite3`, `pandas` and `numpy` are optional imports that no extras group declares. Add extras such as `pandas` and `pysqlite3` so users can install them in a supported way.
- The `mypy` extra includes `data-science-types`, which is an old stub package. Review whether it is still needed.
- `python_requires=">=3.6"` and the classifiers stop at Python 3.10. Review them against current Python versions.
- Only `setup.py` was checked, so any pins in other files such as CI requirements were not seen.

```json
{
  "commit": "fb8f495582f68d8d49f57b42d12a66802f9ac238",
  "runtime_dependencies": [
    {"name": "sqlite-fts4", "constraint": ""},
    {"name": "click", "constraint": ""},
    {"name": "click-default-group-wheel", "constraint": ""},
    {"name": "tabulate", "constraint": ""},
    {"name": "python-dateutil", "constraint": ""}
  ],
  "optional_groups": {
    "test": ["pytest", "black", "hypothesis", "cogapp"],
    "docs": ["furo", "sphinx-autobuild", "codespell", "sphinx-copybutton", "beanbag-docutils"],
    "mypy": ["mypy", "types-click", "types-tabulate", "types-python-dateutil", "data-science-types"],
    "flake8": ["flake8"]
  },
  "imports": {
    "sqlite-fts4": ["sqlite_utils/db.py"],
    "click": ["sqlite_utils/cli.py", "sqlite_utils/utils.py"],
    "click-default-group-wheel": ["sqlite_utils/cli.py"],
    "tabulate": ["sqlite_utils/cli.py"],
    "python-dateutil": ["sqlite_utils/recipes.py"]
  },
  "unused_dependencies": [],
  "undeclared_imports": [
    {"module": "pysqlite3", "files": ["sqlite_utils/utils.py"], "optional": true},
    {"module": "pandas", "files": ["sqlite_utils/db.py"], "optional": true},
    {"module": "numpy", "files": ["sqlite_utils/db.py"], "optional": true}
  ],
  "unpinned": ["sqlite-fts4", "click", "click-default-group-wheel", "tabulate", "python-dateutil"]
}
```