## 1. Scope
- Repository: https://github.com/simonw/csvs-to-sqlite
- Commit: 33b79ed80a688ceae4486ebdcca28ae689f54c03
- Manifest files read: `setup.py`. The repository has no other manifest that I read.
- Source searched for imports: `csvs_to_sqlite/` (`cli.py`, `utils.py`). I used one grep for `import` and `from` lines, so I did not read every file in full.

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
- Undeclared third-party imports: `numpy`, imported in `csvs_to_sqlite/utils.py` (`import numpy as np`). It is not optional, because it is not inside a `try`/`except ImportError`. It is only available because pandas pulls it in.
- The other imports are standard library: `os`, `sqlite3`, `fnmatch`, `hashlib`, `re`.

## 6. Version pinning
- `six` has no version constraint.

## 7. Risks and recommendations
- Declare `numpy` explicitly in `install_requires`, since the code imports it directly.
- Add a version constraint for `six`. Consider dropping it, because the package only uses `six.moves.urllib.parse` and Python 3 has `urllib.parse`.
- `py-lru-cache~=0.1.4` is a small, little-maintained package. Consider replacing it with `functools.lru_cache`.
- `setup.py` lists Python 3.6–3.9 classifiers, and these are old. Review them against the Python versions the pinned `pandas` and `dateparser` constraints support.

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