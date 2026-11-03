# csvs-to-sqlite dependency audit (dep-audit-v1)

## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03 (version 1.3.1)
- Manifest files read: `setup.py`. `setup.cfg` is present but I did not read it. No `requirements*.txt` or `pyproject.toml` exists.
- Source files scanned for imports: `csvs_to_sqlite/cli.py`, `csvs_to_sqlite/utils.py`, `csvs_to_sqlite/__init__.py`.

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
  - `numpy` is imported in `csvs_to_sqlite/utils.py` (`import numpy as np`). The import is not optional. It is not inside a `try` / `except ImportError`. numpy only arrives transitively through pandas.
- The other imports are standard library (`os`, `sqlite3`, `fnmatch`, `hashlib`, `re`, `__future__`).

## 6. Version pinning
- Runtime dependencies with no version constraint: `six`.

## 7. Risks and recommendations
- Declare `numpy` explicitly in `install_requires`. The code imports it directly, so it currently depends on pandas pulling it in.
- Add a version constraint to `six`, or drop it. The `six.moves.urllib.parse` imports are unnecessary on Python 3, and the classifiers list only 3.6–3.9.
- `py-lru-cache~=0.1.4` is a small, old package. Consider replacing it with `functools.lru_cache` or pinning it more carefully.
- I did not check upper bounds. `pandas>=1.0` and `click>=7.0` have no upper bound, so future major releases could break the package.
- I did not read `setup.cfg`, so I did not check it for extra dependency declarations.

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