## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03
- Manifest files read: `setup.py`. I did not look for other manifests such as `requirements.txt`, `setup.cfg` or `pyproject.toml`.
- Source files checked: a Grep for `import` and `from` lines across `csvs_to_sqlite/` matched only `cli.py` and `utils.py`.

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
- Undeclared third-party imports: `numpy`, imported in `csvs_to_sqlite/utils.py` (`import numpy as np`). The import is not optional, because it is not inside a `try` / `except ImportError`. pandas installs numpy, so it is available transitively.
- The other imports are standard library: `os`, `fnmatch`, `hashlib`, `re`, `sqlite3`.

## 6. Version pinning
- `six` has no version constraint.

## 7. Risks and recommendations
- Declare `numpy` explicitly in `install_requires`, since it is imported directly and currently relies on pandas to supply it.
- Add a version constraint for `six`, or drop it. It is only used for `six.moves.urllib.parse`, and the classifiers list only Python 3, so `urllib.parse` can replace it.
- `py-lru-cache~=0.1.4` is an obscure, tightly pinned package. Consider replacing it with `functools.lru_cache` or vendoring it.
- The `pandas>=1.0` and `dateparser>=1.0` constraints have no upper bound, so a future major release could break the package.

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