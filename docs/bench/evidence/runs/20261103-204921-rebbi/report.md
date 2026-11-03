## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: fb8f495582f68d8d49f57b42d12a66802f9ac238
- Manifest files read: `setup.py`. I read no other manifest files, such as `requirements.txt` or `pyproject.toml`.
- Source files searched for imports: `sqlite_utils/cli.py`, `sqlite_utils/db.py`, `sqlite_utils/utils.py` and `sqlite_utils/recipes.py`. I searched them with a grep for import statements and did not read them in full.

## 2. Runtime dependencies
`install_requires` in `setup.py` declares five entries. None has a version constraint.
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
- `sqlite-fts4` is imported as `sqlite_fts4` in `sqlite_utils/db.py`.
- `click` is imported in `sqlite_utils/cli.py` and `sqlite_utils/utils.py`.
- `click-default-group-wheel` is imported as `click_default_group` in `sqlite_utils/cli.py`.
- `tabulate` is imported in `sqlite_utils/cli.py`.
- `python-dateutil` is imported as `dateutil` in `sqlite_utils/recipes.py`.

## 5. Unused and undeclared
- **Unused:** none. Every runtime dependency is imported by at least one file.
- **Undeclared:** the three modules below are imported but not declared in `install_requires` or `extras_require`.
  - `pysqlite3`: `sqlite_utils/utils.py`. I read this import as optional, with a fallback to `sqlite3` at lines 17-23. I did not read the surrounding `try` block, so this is inferred from the grep output.
  - `pandas`: `sqlite_utils/db.py`, line 66. I read this import as optional. I did not read the surrounding `try` block, so this is inferred from the indentation.
  - `numpy`: `sqlite_utils/db.py`, line 71. I read this import as optional, on the same basis as `pandas`.

## 6. Version pinning
All five runtime dependencies have no version constraint: `sqlite-fts4`, `click`, `click-default-group-wheel`, `tabulate` and `python-dateutil`.

## 7. Risks and recommendations
- **Unbounded dependencies:** with no constraints at all, a breaking upstream release can break installs. Add at least lower bounds, and upper bounds for `click` where needed.
- **Undeclared optional imports:** `pandas`, `numpy` and `pysqlite3` are used but declared nowhere. Add an extras group for them, or document them as optional.
- **Name mismatch:** the declared distribution `click-default-group-wheel` is imported as `click_default_group`. Keep this documented so audit tools do not flag it as unused.
- **Outdated type stubs:** the mypy extra includes `data-science-types`, which is old and unmaintained. Consider replacing it.
- **Limits of this audit:** it relied on a grep for import statements. Imports that are not at the start of a line, or are made dynamically, would not appear.

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