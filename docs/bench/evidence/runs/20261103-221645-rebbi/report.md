## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite (version 1.3.1)
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03
- Manifest files read: `setup.py`. No `requirements*.txt` or `pyproject.toml` was read.
- Source searched: the `csvs_to_sqlite/` package. Imports were found in `cli.py` and `utils.py`.

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
  - `numpy` is imported in `csvs_to_sqlite/utils.py` as `import numpy as np`. It is not optional, because the import is not inside a `try`/`except ImportError`. It is only available indirectly, as a dependency of pandas.
- All other imports (`os`, `sqlite3`, `fnmatch`, `hashlib`, `re`) are standard library.

## 6. Version pinning
- `six` has no version constraint.

## 7. Risks and recommendations
- Declare `numpy` explicitly in `install_requires`. It is imported directly but relies on pandas pulling it in.
- Add a version constraint to `six`, or drop it. It is only used for `six.moves.urllib`, and the declared classifiers list Python 3.6 and later only, so the standard `urllib.parse` would do.
- `py-lru-cache~=0.1.4` is an old, narrowly pinned package. Check that it is still maintained, and consider replacing it with `functools.lru_cache`.
- The lower bounds (`click>=7.0`, `pandas>=1.0`) have no upper bounds, so a future major release could break the package. Consider testing against newer versions.

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