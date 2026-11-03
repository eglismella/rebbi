## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03. The `.git/objects` directory contains an object with this hash, but I did not verify that it is the checked-out HEAD.
- Manifest files read: `setup.py`.
- `setup.cfg` is present but I did not read it. There is no `requirements*.txt` or `pyproject.toml`.
- Source files searched: `csvs_to_sqlite/cli.py` and `csvs_to_sqlite/utils.py`. `__init__.py` was included in the search and had no matching import lines.

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
- six: `csvs_to_sqlite/utils.py`

## 5. Unused and undeclared
- Unused dependencies: none.
- Undeclared imports:
  - `numpy` is imported in `csvs_to_sqlite/utils.py` (`import numpy as np`). It is not optional, because the import is not inside a `try` / `except ImportError`. It is probably pulled in transitively by pandas.
- The other imports (`os`, `sqlite3`, `fnmatch`, `hashlib`, `re`) are standard library.

## 6. Version pinning
- `six` has no version constraint.

## 7. Risks and recommendations
- Declare `numpy` in `install_requires`. It is imported directly but relies on pandas installing it.
- Add a version constraint to `six`, or remove it. The code only uses `six.moves.urllib.parse`, which Python 3 provides natively. The classifiers list only Python 3.6 to 3.9.
- `py-lru-cache~=0.1.4` is an old, obscure package. Consider replacing it with `functools.lru_cache` or another maintained alternative.
- The dependencies have lower bounds only, so future major releases of pandas or click could break the package. Consider testing against upper bounds.

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