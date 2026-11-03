## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: fb8f495582f68d8d49f57b42d12a66802f9ac238
- Manifest files read: `setup.py`. `setup.cfg` and `MANIFEST.in` turned up in a glob but I did not read them. No `pyproject.toml` or requirements files were found at the repository root.
- Imports were searched in the `sqlite_utils/` package: `__init__.py`, `__main__.py`, `cli.py`, `db.py`, `recipes.py` and `utils.py`. I read only the `try`/`except` blocks in `utils.py` and `db.py`. The rest of the import data comes from search matches.

## 2. Runtime dependencies
`install_requires` entries, exactly as declared:
- `sqlite-fts4`
- `click`
- `click-default-group-wheel`
- `tabulate`
- `python-dateutil`

None of them has a version constraint.

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
- Undeclared third-party imports:
  - `pysqlite3` in `sqlite_utils/utils.py`. It is optional: the import sits in a `try` / `except ImportError` that falls back to the standard-library `sqlite3`.
  - `pandas` in `sqlite_utils/db.py`. It is optional: the import sits in a `try` / `except ImportError` that sets `pd = None`.
  - `numpy` in `sqlite_utils/db.py`. It is optional: the import sits in a `try` / `except ImportError` that sets `np = None`.

## 6. Version pinning
All five runtime dependencies have no version constraint: `sqlite-fts4`, `click`, `click-default-group-wheel`, `tabulate`, `python-dateutil`.

## 7. Risks and recommendations
- **Unbounded runtime dependencies.** A breaking release of any of the five could break installs. Add lower bounds, and upper bounds where practical, for example `click>=8`.
- **Third-party fork.** `click-default-group-wheel` is a repackaged fork of `click-default-group`, so you depend on a third-party package. Confirm it is still maintained, or consider the upstream package.
- **Undeclared optional modules.** `pysqlite3`, `pandas` and `numpy` are handled gracefully when missing. I recommend listing them in an extras group such as `extras_require["pandas"]` so users can find them.
- **Unreviewed stale-looking entries.** `data-science-types` in the `mypy` extra is an old stub package. I recommend reviewing it, but I did not check whether it is still maintained.
- **Metadata gaps.** `python_requires` is `>=3.6` and the classifiers stop at Python 3.10. I did not check whether this is still accurate.

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