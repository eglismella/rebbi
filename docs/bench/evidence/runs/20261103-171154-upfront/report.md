## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03
- Manifest files read: `setup.py`. `setup.cfg` is present but I did not read it. It is not a dependency source here, because `setup.py` declares the dependencies.
- Package files searched for imports: `csvs_to_sqlite/cli.py` and `csvs_to_sqlite/utils.py`. I did not check `csvs_to_sqlite/__init__.py` for imports.

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
- six: `csvs_to_sqlite/utils.py`. It is used as `import six` and as `six.moves.urllib.parse`.

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports:
  - `numpy` is imported in `csvs_to_sqlite/utils.py` as `import numpy as np`. The import is not optional, because it is not in a `try`/`except ImportError`. It is only available indirectly, as a dependency of pandas.
- The other imports (`os`, `sqlite3`, `fnmatch`, `hashlib`, `re`) are standard library.

## 6. Version pinning
- Runtime dependencies with no version constraint: `six`

## 7. Risks and recommendations
- Declare `numpy` explicitly in `install_requires`, because it is imported directly but only arrives through pandas.
- Add a version constraint to `six`, or drop it. `six` is a Python 2/3 compatibility shim, and the classifiers list only Python 3.6–3.9. The only `six` usage found is `six.moves.urllib.parse`, which `urllib.parse` can replace.
- `py-lru-cache~=0.1.4` is an obscure, tightly pinned package. Consider replacing it with `functools.lru_cache`, or confirm that it is maintained.
- The `test` extra has no version constraints (pytest, cogapp), so test runs may not be reproducible.

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