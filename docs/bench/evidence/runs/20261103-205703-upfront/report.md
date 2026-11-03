## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite
- Commit: `33b79ed80a688ceae4486ebdcca28ae689f54c03`
- Manifest files read: `setup.py`. `setup.cfg` exists but I did not read it.
- Source searched for imports: `csvs_to_sqlite/cli.py` and `csvs_to_sqlite/utils.py`. I did not read `csvs_to_sqlite/__init__.py`, so any imports in it are unchecked.
- Tests were not scanned.

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
- Undeclared third-party imports:
  - `numpy` is imported in `csvs_to_sqlite/utils.py` (`import numpy as np`). The import is not optional, because it is not inside `try`/`except ImportError`. pandas pulls numpy in transitively, but the package does not declare it.
- Imports such as `os`, `re`, `sqlite3`, `hashlib` and `fnmatch` are standard library, so I did not count them.

## 6. Version pinning
- `six` has no version constraint.

## 7. Risks and recommendations
- Declare `numpy` explicitly in `install_requires`, since `utils.py` imports it directly. Otherwise the package relies on pandas to supply it.
- Pin `six` with a lower bound, or drop it. `six` only supports Python 2/3 compatibility, and the classifiers list Python 3.6 to 3.9 only.
- `py-lru-cache~=0.1.4` is an obscure, unmaintained-looking package, so consider replacing it with `functools.lru_cache` or another maintained option.
- Consider adding upper bounds or a lock file for `pandas` and `dateparser`, which are open-ended (`>=`) and could break on new major versions.

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