# db-to-sqlite dependency audit (dep-audit-v1)

## 1. Scope
- Repository: https://github.com/simonw/db-to-sqlite
- Commit: b7c95fcfe853ca5fc2236bfbf7e4a80ca9239969
- Manifest files read: `setup.py`. The repository has no `requirements*.txt`, `setup.cfg`, `pyproject.toml` or `.in` files.
- Package source searched: `db_to_sqlite/cli.py` and `db_to_sqlite/__init__.py`. The `__init__.py` file has no imports.

## 2. Runtime dependencies
- `sqlalchemy` (no constraint)
- `sqlite-utils>=2.9.1`
- `click` (no constraint)

## 3. Optional dependency groups
- `test`: pytest, pytest-timeout
- `test_mysql`: pytest, mysqlclient
- `test_postgresql`: pytest, psycopg2
- `mysql`: mysqlclient
- `postgresql`: psycopg2

## 4. Where runtime dependencies are used
- `click`: `db_to_sqlite/cli.py`
- `sqlalchemy`: `db_to_sqlite/cli.py`
- `sqlite-utils` (imported as `sqlite_utils`): `db_to_sqlite/cli.py`

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports: none. The only other import is `itertools`, which is in the standard library.
- `mysqlclient` and `psycopg2` are declared as extras. No file in the package imports them. SQLAlchemy loads them indirectly as database drivers.

## 6. Version pinning
- `sqlalchemy` and `click` have no version constraint.

## 7. Risks and recommendations
- Unpinned `sqlalchemy` is the main risk. SQLAlchemy 2.0 changed its API (for example `engine.execute` was removed and `text()` is required), so a major upgrade could break the tool. Add a lower bound and a tested upper bound, such as `sqlalchemy>=1.4,<3`, after checking compatibility.
- Add a lower bound for `click`, for example `click>=7`.
- `sqlite-utils` has only a lower bound. Consider an upper bound if its API changes.
- `psycopg2` in the extras requires a compiler and libpq headers to build. Consider offering `psycopg2-binary` as an alternative extra.
- The test groups repeat `pytest`. Consider one shared test group.

```json
{
  "commit": "b7c95fcfe853ca5fc2236bfbf7e4a80ca9239969",
  "runtime_dependencies": [
    {"name": "sqlalchemy", "constraint": ""},
    {"name": "sqlite-utils", "constraint": ">=2.9.1"},
    {"name": "click", "constraint": ""}
  ],
  "optional_groups": {
    "test": ["pytest", "pytest-timeout"],
    "test_mysql": ["pytest", "mysqlclient"],
    "test_postgresql": ["pytest", "psycopg2"],
    "mysql": ["mysqlclient"],
    "postgresql": ["psycopg2"]
  },
  "imports": {
    "click": ["db_to_sqlite/cli.py"],
    "sqlalchemy": ["db_to_sqlite/cli.py"],
    "sqlite-utils": ["db_to_sqlite/cli.py"]
  },
  "unused_dependencies": [],
  "undeclared_imports": [],
  "unpinned": ["sqlalchemy", "click"]
}
```