## 1. Scope
- Repository: https://github.com/simonw/sqlite-utils
- Commit: 9d7da0606e98713896bbc9fc885a5b0cd54ac2fd
- Manifest file read: `setup.py`. It is version 3.38, with `python_requires>=3.8`.
- Source searched: all `.py` files under `sqlite_utils/`, using a grep for import and try/except lines.

## 2. Runtime dependencies
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
- sqlite-fts4 (imported as `sqlite_fts4`): `sqlite_utils/db.py`
- click: `sqlite_utils/cli.py`, `sqlite_utils/utils.py`
- click-default-group (imported as `click_default_group`): `sqlite_utils/cli.py`
- tabulate: `sqlite_utils/cli.py`
- python-dateutil (imported as `dateutil`): `sqlite_utils/recipes.py`
- pluggy: `sqlite_utils/plugins.py`, `sqlite_utils/hookspecs.py`

## 5. Unused and undeclared
Unused runtime dependencies: none.

Undeclared third-party imports. None of these appear in any extras group:
- `sqlite_dump`: `sqlite_utils/db.py`. Optional, inside `try`/`except ImportError`.
- `pandas`: `sqlite_utils/db.py`. Optional, inside `try`/`except ImportError`.
- `numpy`: `sqlite_utils/db.py`. Optional, inside `try`/`except ImportError`.
- `pysqlite3`: `sqlite_utils/utils.py`. Optional, inside `try`/`except ImportError`.
- `sqlean`: `sqlite_utils/utils.py`. Optional, inside a nested `try`/`except ImportError`.

`trogon` is imported optionally in `sqlite_utils/cli.py`. It is declared in the `tui` extra, so it is not undeclared.

## 6. Version pinning
No version constraint at all: `sqlite-fts4`, `click`, `tabulate`, `python-dateutil`, `pluggy`.

## 7. Risks and recommendations
- Five of the six runtime dependencies have no version constraint. A breaking upstream release could break installs. Consider lower bounds, and upper bounds where an API is known to be unstable.
- The optional imports (`sqlite_dump`, `pandas`, `numpy`, `pysqlite3`, `sqlean`) are not declared in any extras group. Users can't discover or install them in a supported way. Consider adding extras such as `pandas`, `numpy`, `dump` and `sqlean`.
- The `mypy` extra includes `data-science-types`, which looks unmaintained. Review whether it is still needed.
- `click` is used in `utils.py`, so the library, not only the CLI, needs it at runtime. This is a coupling to be aware of.
- I read only `setup.py`. I did not check for other manifests such as `pyproject.toml` or requirements files.

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