# dep-audit-v1: csvs-to-sqlite

## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03
- Manifest files read: `setup.py`. It is the only manifest I read. I did not look for `requirements*.txt`, `pyproject.toml` or `setup.cfg`.
- Source files searched for imports: all files under `csvs_to_sqlite/`. Only `cli.py` and `utils.py` have import lines that matched my search.

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
- py-lru-cache (imported as `lru`): `csvs_to_sqlite/utils.py`
- six: `csvs_to_sqlite/utils.py`

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports: `numpy` in `csvs_to_sqlite/utils.py` (`import numpy as np`). This import is not optional because it is not inside a `try` / `except ImportError`. numpy is only available because pandas pulls it in.
- The other imports are standard library: os, fnmatch, hashlib, re, sqlite3.

## 6. Version pinning
- Runtime dependencies with no version constraint: `six`.

## 7. Risks and recommendations
- Declare `numpy` in `install_requires`. It is imported directly and currently relies on pandas installing it.
- Pin or constrain `six`. Better still, drop it: the package targets Python 3 only, and `six.moves.urllib.parse` can be replaced with `urllib.parse`.
- `py-lru-cache~=0.1.4` is a small, old package, and its constraint is tight. Check that it is still maintained, or replace it with `functools.lru_cache`.
- The upper bounds are open on click, pandas and dateparser. Test against new major versions in CI.

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