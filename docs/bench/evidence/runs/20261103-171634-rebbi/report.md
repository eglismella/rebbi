# Dependency audit dep-audit-v1: sqlite-utils

## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: `fb8f495582f68d8d49f57b42d12a66802f9ac238`
- Manifest file read: `setup.py`. It declares version 3.30 and `python_requires>=3.6`.
- Source searched for imports: every `*.py` file under `sqlite_utils/`. Only `db.py`, `utils.py`, `cli.py` and `recipes.py` contain third-party imports.

## 2. Runtime dependencies
These are the `install_requires` entries. None has a version constraint.
- `sqlite-fts4`
- `click`
- `click-default-group-wheel`
- `tabulate`
- `python-dateutil`

## 3. Optional dependency groups
- `test`: pytest, black, hypothesis, cogapp
- `docs`: furo, sphinx-autobuild, codespell, sphinx-copybutton, beanbag-docutils
- `mypy`: mypy, types-click, types-tabulate, types-python-dateutil, data-science-types
- `flake8`: flake8

## 4. Where runtime dependencies are used
- `sqlite-fts4` (imported as `sqlite_fts4`): `sqlite_utils/db.py`
- `click`: `sqlite_utils/cli.py`, `sqlite_utils/utils.py`
- `click-default-group-wheel` (imported as `click_default_group`): `sqlite_utils/cli.py`
- `tabulate`: `sqlite_utils/cli.py`
- `python-dateutil` (imported as `dateutil`): `sqlite_utils/recipes.py`

## 5. Unused and undeclared
- **Unused runtime dependencies:** none.
- **Undeclared third-party imports**, none of which appear in `install_requires` or `extras_require`:
  - `pandas` is imported in `sqlite_utils/db.py` inside `try/except ImportError`, so it is optional.
  - `numpy` is imported in `sqlite_utils/db.py` inside `try/except ImportError`, so it is optional.
  - `pysqlite3` is imported in `sqlite_utils/utils.py` inside `try/except ImportError`, with a fallback to the standard-library `sqlite3`. It is optional.

## 6. Version pinning
All five runtime dependencies have no version constraint: `sqlite-fts4`, `click`, `click-default-group-wheel`, `tabulate` and `python-dateutil`.

## 7. Risks and recommendations
- With no lower or upper bounds, a new major release of any dependency, especially `click`, could break installs.
  - Recommendation: add minimum versions for the APIs the code actually uses, and consider upper bounds for `click`.
- `pandas`, `numpy` and `pysqlite3` are used when present but are not declared anywhere.
  - Recommendation: add an optional extras group such as `pandas`, so users know these features exist.
- The `mypy` extra includes `data-science-types`, which is old and unmaintained.
  - Recommendation: review whether it is still needed.
- `click-default-group-wheel` is a third-party repackaging of `click-default-group`, so it carries some supply-chain risk.
  - Recommendation: verify the package and consider moving to the upstream distribution.

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
    {"module": "pandas", "files": ["sqlite_utils/db.py"], "optional": true},
    {"module": "numpy", "files": ["sqlite_utils/db.py"], "optional": true},
    {"module": "pysqlite3", "files": ["sqlite_utils/utils.py"], "optional": true}
  ],
  "unpinned": ["sqlite-fts4", "click", "click-default-group-wheel", "tabulate", "python-dateutil"]
}
```