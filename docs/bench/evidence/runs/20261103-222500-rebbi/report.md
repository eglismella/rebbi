# dep-audit-v1: csvs-to-sqlite

## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03
- Manifest files read: `setup.py`. I found no other manifest, such as requirements files or `pyproject.toml`; I did not search for them.
- Source files searched for imports: every `.py` file under `csvs_to_sqlite/`. Only `cli.py` and `utils.py` contained imports.

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
  - `numpy`, imported in `csvs_to_sqlite/utils.py`. It is not optional, because the import is not inside a `try` / `except ImportError`. It is probably installed as a dependency of pandas.
- The other imports are standard library: `os`, `sqlite3`, `fnmatch`, `hashlib`, `re`, `__future__`.

## 6. Version pinning
- `six` has no version constraint.

## 7. Risks and recommendations
- Declare `numpy` explicitly in `install_requires`. The package currently relies on pandas to pull it in.
- Add a version constraint to `six`, or remove it. It is only used for `six.moves.urllib.parse`, and the classifiers list Python 3 only, so the standard library's `urllib.parse` would do.
- `py-lru-cache~=0.1.4` is an old, little-maintained package. Consider replacing it with `functools.lru_cache` or similar.
- The dependency lower bounds have no upper bounds, so future major releases could break the package.
- Caveat: no budget was left for the Rebbi handoff, which was refused (`CANNOT_MOVE`). I did not search for other manifest files. The import data comes from one regex grep and `setup.py`.

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