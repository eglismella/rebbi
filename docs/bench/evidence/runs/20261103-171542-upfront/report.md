## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03. The working directory is named csvs-to-sqlite-1.3.1, and `setup.py` declares version 1.3.1.
- Manifest file read: `setup.py`.
- `setup.cfg` exists, but I did not read it. There is no `requirements*.txt` or `pyproject.toml`.
- Source files searched for imports: `csvs_to_sqlite/__init__.py`, `csvs_to_sqlite/cli.py` and `csvs_to_sqlite/utils.py`.

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
- py-lru-cache: `csvs_to_sqlite/utils.py`. It is imported as `lru`, which I take to be the module this distribution provides. I did not check that against the package itself.
- six: `csvs_to_sqlite/utils.py`, including `six.moves.urllib.parse`

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports:
  - `numpy` is imported in `csvs_to_sqlite/utils.py` as `import numpy as np`. It is a top-level import, not inside `try`/`except ImportError`, so it is not optional.
  - numpy is probably installed as a dependency of pandas, but it is not declared in this package.
- The other imports (`os`, `fnmatch`, `hashlib`, `re`, `sqlite3`) are standard library.

## 6. Version pinning
- `six` has no version constraint.

## 7. Risks and recommendations
- **Undeclared numpy:** the package relies on pandas to pull in numpy. Add `numpy` to `install_requires`, or remove the direct import.
- **Unpinned six:** add a minimum version to `six`. Better still, drop it, since the classifiers list only Python 3.6 to 3.9 and none of them need it.
- **Loose lower bounds:** `py-lru-cache~=0.1.4` allows only 0.1.x, which is tight for an obscure package. The other constraints have no upper bound, so a future major release could break the package.
- **Test group:** the `test` extra has no version constraints. Consider pinning it for reproducible CI.

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