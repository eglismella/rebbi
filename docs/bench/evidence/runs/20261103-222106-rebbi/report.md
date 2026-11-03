## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite (version 1.3.1)
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03
- Manifest files read: `setup.py`. I searched the imports in `csvs_to_sqlite/cli.py` and `csvs_to_sqlite/utils.py`. These were the only files in the package that matched the import search.

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
- six: `csvs_to_sqlite/utils.py`

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports: `numpy`, imported in `csvs_to_sqlite/utils.py` (`import numpy as np`). It is a top-level import, so it is not optional. It is installed only indirectly, as a dependency of pandas.
- `os`, `sqlite3`, `fnmatch`, `hashlib` and `re` are standard library modules.

## 6. Version pinning
- `six` has no version constraint.

## 7. Risks and recommendations
- Declare `numpy` explicitly in `install_requires`, because the code imports it directly.
- Add a version constraint to `six`, or drop it if it is no longer needed. The classifiers list only Python 3, so `six` may be unnecessary.
- `py-lru-cache~=0.1.4` is a niche package with a narrow pin. Check that it is still maintained, or replace it with `functools.lru_cache`.
- All constraints are lower bounds, with no upper bounds. A future major release of pandas or click could break the package.

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