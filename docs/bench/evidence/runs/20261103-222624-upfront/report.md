## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03
- Manifest files read: `setup.py`.
- No `requirements*` files were found.
- I searched imports in the `csvs_to_sqlite` package, which contains `cli.py` and `utils.py`.

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
- py-lru-cache: `csvs_to_sqlite/utils.py`. It provides the module `lru`.
- six: `csvs_to_sqlite/utils.py`. It is imported directly and through `six.moves`.

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports: `numpy`, imported in `csvs_to_sqlite/utils.py` (`import numpy as np`). The import is not optional, because it is not inside a `try` / `except ImportError`. numpy is only available indirectly, as a dependency of pandas.
- The other imports are standard library modules: `os`, `fnmatch`, `hashlib`, `re`, `sqlite3`.

## 6. Version pinning
- `six` has no version constraint.

## 7. Risks and recommendations
- Declare `numpy` in `install_requires`. The package imports it directly, so it breaks if pandas ever stops pulling it in.
- Add a lower bound to `six`, or drop it. The code only uses `six.moves.urllib.parse`, and the `Programming Language` classifiers list only Python 3, where `urllib.parse` is available directly.
- `py-lru-cache~=0.1.4` is an obscure, old package. Consider replacing it with `functools.lru_cache` or another maintained option.
- The `Programming Language` classifiers stop at Python 3.9. Check that the declared lower bounds still work with current pandas and dateparser releases.
- Consider adding upper bounds or a lock file for reproducible installs.

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