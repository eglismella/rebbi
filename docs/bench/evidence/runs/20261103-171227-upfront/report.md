## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: fb8f495582f68d8d49f57b42d12a66802f9ac238 (the working directory is named `sqlite-utils-3.30`, and `setup.py` declares version 3.30)
- Manifest files read: `setup.py`.
- `setup.cfg` and `MANIFEST.in` exist but I did not read them. The repository has no `pyproject.toml` or `requirements*.txt`.
- Source files checked for imports: every file under `sqlite_utils/`.

## 2. Runtime dependencies
`install_requires` in `setup.py` declares these five entries. None has a version constraint.
- `sqlite-fts4`
- `click`
- `click-default-group-wheel`
- `tabulate`
- `python-dateutil`

## 3. Optional dependency groups
- test: pytest, black, hypothesis, cogapp
- docs: furo, sphinx-autobuild, codespell, sphinx-copybutton, beanbag-docutils
- mypy: mypy, types-click, types-tabulate, types-python-dateutil, data-science-types
- flake8: flake8

## 4. Where runtime dependencies are used
- `sqlite-fts4` (imported as `sqlite_fts4`): `sqlite_utils/db.py`
- `click`: `sqlite_utils/cli.py`, `sqlite_utils/utils.py`
- `click-default-group-wheel` (imported as `click_default_group`): `sqlite_utils/cli.py`
- `tabulate`: `sqlite_utils/cli.py`
- `python-dateutil` (imported as `dateutil`): `sqlite_utils/recipes.py`

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports. All three are optional, wrapped in `try` / `except ImportError`:
  - `pysqlite3` in `sqlite_utils/utils.py`. If the import fails, the code falls back to the standard library `sqlite3`.
  - `pandas` in `sqlite_utils/db.py`. If the import fails, `pd` is set to `None`.
  - `numpy` in `sqlite_utils/db.py`. If the import fails, `np` is set to `None`.

## 6. Version pinning
All five runtime dependencies have no version constraint: `sqlite-fts4`, `click`, `click-default-group-wheel`, `tabulate`, `python-dateutil`.

## 7. Risks and recommendations
- **Unbounded dependencies.** Any new release of a dependency can be installed, including one with breaking changes. Add lower bounds at least, such as `click>=8`, and consider upper bounds for packages with a history of breaking changes.
- **Third-party wheel.** `click-default-group-wheel` is a repackaging of `click-default-group`. Confirm it is trusted and maintained, or switch to the upstream package.
- **Undeclared optional imports.** `pysqlite3`, `pandas` and `numpy` are used if present but are declared nowhere. Add an `extras_require` group for them, or document them, so users know which packages enable these behaviours.
- **Old Python floor.** `python_requires` is `>=3.6`, which is long past end of life. Raising it would allow newer dependency versions.
- **Mypy group.** The mypy group includes `data-science-types`, which is deprecated.

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