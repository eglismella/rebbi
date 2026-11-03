# dep-audit-v1 report: simonw/sqlite-utils

## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: fb8f495582f68d8d49f57b42d12a66802f9ac238
- Manifest files read: `setup.py`. There is no requirements file or `pyproject.toml` in the files I searched.
- Source files searched for imports: `sqlite_utils/*.py` (`cli.py`, `db.py`, `utils.py`, `recipes.py`).
- Limits of the check: I searched `sqlite_utils/` with one top-of-line import pattern and read only the `try`/`except` blocks listed below. Other files and indented imports outside those blocks were not read individually.

## 2. Runtime dependencies
- `sqlite-fts4` (no constraint)
- `click` (no constraint)
- `click-default-group-wheel` (no constraint)
- `tabulate` (no constraint)
- `python-dateutil` (no constraint)

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
  - `pysqlite3`: `sqlite_utils/utils.py`. Optional: the import is in a `try`/`except ImportError` that falls back to the standard-library `sqlite3`.
  - `pandas`: `sqlite_utils/db.py`. Optional: the import is in a `try`/`except ImportError`, and `pd` is set to `None` on failure.
  - `numpy`: `sqlite_utils/db.py`. Optional: the import is in a `try`/`except ImportError`, and `np` is set to `None` on failure.

## 6. Version pinning
None of the five runtime dependencies has a version constraint: `sqlite-fts4`, `click`, `click-default-group-wheel`, `tabulate` and `python-dateutil`.

## 7. Risks and recommendations
- **Unbounded dependencies.** All five runtime dependencies are unpinned, so a breaking release of any of them could break installs. Add lower bounds for the APIs actually used, for example a minimum `click` version, and consider upper bounds on major versions.
- **Undeclared optional imports.** `pysqlite3`, `pandas` and `numpy` are used but declared in no group. Add an extras group such as `pandas` or `full` so users can install them deliberately.
- **Third-party distribution.** `click-default-group-wheel` is a repackaged fork of `click-default-group`. Check that it is maintained, or move to the upstream package.
- **Outdated type stub.** The `mypy` extra includes `data-science-types`, which is deprecated. Consider replacing it with `pandas-stubs` and `numpy` typing.

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