## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03
- Manifest files read: `setup.py`. No `requirements.txt` or `pyproject.toml` was read.
- Source files checked for imports: `csvs_to_sqlite/utils.py` and `csvs_to_sqlite/cli.py`. I searched import lines in the whole `csvs_to_sqlite` package directory.

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
- py-lru-cache: `csvs_to_sqlite/utils.py`, imported as `lru`
- six: `csvs_to_sqlite/utils.py`, including `six.moves`

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports: `numpy`, imported in `csvs_to_sqlite/utils.py` (`import numpy as np`). The import is not optional, because it is not inside `try` / `except ImportError`. numpy is only available indirectly, as a dependency of pandas.
- The other imports (`os`, `fnmatch`, `hashlib`, `re`, `sqlite3`) are standard library.

## 6. Version pinning
- Runtime dependencies with no version constraint: `six`.

## 7. Risks and recommendations
- Declare `numpy` in `install_requires`, or stop importing it directly. At the moment the package relies on pandas to pull it in.
- Put an upper bound or compatible-release constraint on `six`, or drop it. The package is Python 3 only per its classifiers, so `six.moves.urllib.parse` could be replaced with `urllib.parse`.
- `click>=7.0`, `dateparser>=1.0` and `pandas>=1.0` have no upper bounds, so a major release could break the package. Consider adding bounds or testing against newer versions.
- `py-lru-cache~=0.1.4` is a small, niche package. Check that it is still maintained.
- This audit searched only import lines (`import` / `from`) in the `csvs_to_sqlite` package. Dynamic imports would not appear in that search.

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