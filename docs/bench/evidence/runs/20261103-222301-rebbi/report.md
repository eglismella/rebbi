# dep-audit-v1: csvs-to-sqlite

## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03
- Manifest files read: `setup.py`. No `requirements.txt`, `setup.cfg` or `pyproject.toml` was read.
- Source files checked for imports: `csvs_to_sqlite/cli.py` and `csvs_to_sqlite/utils.py`. These come from one grep of import lines. I did not read the files in full or list the package's other modules.
- Rebbi could not lend extra budget, so this audit is limited by the 7,000-token allowance.

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
- six: `csvs_to_sqlite/utils.py`, including `six.moves.urllib.parse`

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports: `numpy`, imported as `import numpy as np` in `csvs_to_sqlite/utils.py`. The import is not optional, because it is not inside `try` / `except ImportError`. numpy is only available through pandas.
- Standard-library imports such as `os`, `sqlite3`, `re`, `hashlib` and `fnmatch` are ignored.

## 6. Version pinning
- `six` has no version constraint.

## 7. Risks and recommendations
- Declare `numpy` explicitly in `install_requires`. It is imported directly, so the package currently relies on pandas pulling it in.
- Add a version constraint to `six`, or drop it. The code is Python 3 only per the classifiers, but `six.moves` is still used for `urlparse`, which `urllib.parse` provides directly.
- `py-lru-cache~=0.1.4` is a small, old package pinned to a narrow range. Consider replacing it with `functools.lru_cache`, or confirm it is still maintained.
- The audit is partial. I read only the import lines in two files, so imports in other modules, if any exist, would be missed.

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
  "undeclared_imports": [{"module": "numpy", "files": ["csvs_to_sqlite/utils.py"], "optional": false}],
  "unpinned": ["six"]
}
```