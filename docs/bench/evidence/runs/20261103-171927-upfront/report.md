## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03
- Manifest files read: `setup.py` and `setup.cfg`. `setup.cfg` declares no dependencies. The repository has no `pyproject.toml` or requirements files.
- Source files searched for imports: `csvs_to_sqlite/cli.py` and `csvs_to_sqlite/utils.py`. I found imports only in these two files.

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
- Undeclared third-party imports: `numpy`, imported in `csvs_to_sqlite/utils.py` as `import numpy as np`. The import is not optional, because it is not inside a `try` / `except ImportError`. It is only available because pandas depends on it.
- The other imports are standard library: os, fnmatch, hashlib, re, sqlite3.

## 6. Version pinning
- Runtime dependencies with no version constraint: `six`.

## 7. Risks and recommendations
- `numpy` is imported directly but not declared. It depends on pandas pulling it in. Recommendation: add `numpy` to `install_requires`.
- `six` is unpinned. The classifiers list only Python 3, so it may no longer be needed. Recommendation: replace `six.moves.urllib.parse` with `urllib.parse` and drop `six`.
- `py-lru-cache~=0.1.4` is a niche package with a tight pin. Recommendation: check that it is still maintained, or replace it with `functools.lru_cache`.
- The `click`, `dateparser` and `pandas` constraints have no upper bounds. Recommendation: test against new major releases of each.
- I did not read the import lines of the two source files directly. They come from a grep that matched absolute imports only, so relative imports of local modules would not show up. These would not change the findings above.

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