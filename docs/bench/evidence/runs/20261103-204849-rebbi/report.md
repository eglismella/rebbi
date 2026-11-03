## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03
- Manifest files read: `setup.py`. I found no other manifest files, and I did not search for `requirements.txt`, `pyproject.toml` or `setup.cfg`.
- Source files searched for imports: every file in `csvs_to_sqlite/`. Only `cli.py` and `utils.py` contain imports.

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
- py-lru-cache: `csvs_to_sqlite/utils.py`, imported as the module `lru`
- six: `csvs_to_sqlite/utils.py`, including `six.moves.urllib.parse`

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports:
  - `numpy` is imported in `csvs_to_sqlite/utils.py` (`import numpy as np`). It is not optional, because it is not inside a `try` / `except ImportError`. It is only available because pandas depends on it.
- The other imports are standard library: `os`, `fnmatch`, `hashlib`, `re`, `sqlite3`, `__future__`.

## 6. Version pinning
- Runtime dependencies with no version constraint: `six`.

## 7. Risks and recommendations
- Declare `numpy` in `install_requires`, since `utils.py` imports it directly. At present it works only through pandas' own dependency.
- Constrain `six`, at least with a lower bound. Consider dropping it, because the classifiers list only Python 3.6 and later, where `urllib.parse` is available directly.
- `py-lru-cache~=0.1.4` is an obscure, old package, and the `lru` module name differs from the distribution name. Consider replacing it with `functools.lru_cache` or pinning it carefully.
- None of the declared dependencies has an upper bound, so a major release of pandas or dateparser could break the package.

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