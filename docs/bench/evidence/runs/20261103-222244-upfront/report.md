# dep-audit-v1: csvs-to-sqlite

## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03
- Manifest files read: `setup.py`. `setup.cfg` exists, but I did not read it. There is no `requirements*.txt` or `pyproject.toml`.
- Source files searched for imports: `csvs_to_sqlite/cli.py` and `csvs_to_sqlite/utils.py`. I searched `__init__.py` as well and it has no imports.

## 2. Runtime dependencies
- `click>=7.0`
- `dateparser>=1.0`
- `pandas>=1.0`
- `py-lru-cache~=0.1.4`
- `six`

## 3. Optional dependency groups
- `test`: pytest, cogapp

## 4. Where runtime dependencies are used
- click: `csvs_to_sqlite/cli.py`, `csvs_to_sqlite/utils.py`
- dateparser: `csvs_to_sqlite/utils.py`
- pandas: `csvs_to_sqlite/utils.py`
- py-lru-cache: `csvs_to_sqlite/utils.py`. It is imported as the module `lru`.
- six: `csvs_to_sqlite/utils.py`, including `six.moves.urllib.parse`.

## 5. Unused and undeclared
- Unused dependencies: none.
- Undeclared third-party imports:
  - `numpy` is imported in `csvs_to_sqlite/utils.py` as `import numpy as np`. The import is not optional, because it is not inside `try`/`except ImportError`. It is only available transitively through pandas.
- The other imports (`os`, `sqlite3`, `fnmatch`, `hashlib`, `re`) are standard library.

## 6. Version pinning
- `six` has no version constraint.

## 7. Risks and recommendations
- Declare `numpy` explicitly in `install_requires`. The package imports it directly but relies on pandas to install it.
- Add a version constraint to `six`, or drop it. It is a Python 2/3 compatibility shim and is only used in `utils.py`. Python 3 is the only target (the classifiers list 3.6–3.9), so `urllib.parse` could replace it.
- `py-lru-cache~=0.1.4` is an obscure, unmaintained-looking package, so its maintenance status needs checking. Consider replacing it with `functools.lru_cache` or another maintained alternative.
- The lower bounds `click>=7.0`, `dateparser>=1.0` and `pandas>=1.0` have no upper bounds. Major releases could break the package, so test against them in CI.

```json
{
  "commit": "33b79ed80a688ceae4486ebdcca28ae689f54c03",
  "runtime_dependencies": [
    {"name": "click", "constraint": ">=7.0"},
    {"name": "dateparser", "constraint": ">=1.0"},
    {"name": "pandas", "constraint": ">=1.0"},
    {"name": "py-lru-cache", "constraint": "~=0.1.4"},
    {"name": "six", "constraint": ""}
  ],
  "optional_groups": {"test": ["pytest", "cogapp"]},
  "imports": {
    "click": ["csvs_to_sqlite/cli.py", "csvs_to_sqlite/utils.py"],
    "dateparser": ["csvs_to_sqlite/utils.py"],
    "pandas": ["csvs_to_sqlite/utils.py"],
    "py-lru-cache": ["csvs_to_sqlite/utils.py"],
    "six": ["csvs_to_sqlite/utils.py"]
  },
  "unused_dependencies": [],
  "undeclared_imports": [
    {"module": "numpy", "files": ["csvs_to_sqlite/utils.py"], "optional": false}
  ],
  "unpinned": ["six"]
}
```