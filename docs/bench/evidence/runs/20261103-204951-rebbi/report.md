# dep-audit-v1: db-to-sqlite

## 1. Scope
- Repository: https://github.com/simonw/db-to-sqlite
- Commit: b7c95fcfe853ca5fc2236bfbf7e4a80ca9239969
- Manifest files read: `setup.py`. The repository has no `pyproject.toml`, `setup.cfg` or requirements file.
- Source files searched for imports: `db_to_sqlite/cli.py` and `db_to_sqlite/__init__.py`.

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
- Undeclared third-party imports: none. The only other imports in the package are the standard-library `itertools`. The `try`/`except` blocks in `cli.py` catch `StopIteration` and `NotImplementedError`, not `ImportError`.

## 6. Version pinning
- `sqlalchemy` and `click` have no version constraint.

## 7. Risks and recommendations
- Unconstrained `sqlalchemy` is a risk. The code uses `create_engine`, `inspect` and `text`, and SQLAlchemy 2.x changed parts of that API. Add a lower bound and a tested upper bound, for example `sqlalchemy>=1.4,<3`.
- Add a lower bound for `click`, for example `click>=7`.
- `psycopg2` and `mysqlclient` are optional drivers that need system libraries to build. Document this, or consider `psycopg2-binary` for the `postgresql` extra.
- `sqlite-utils` has a lower bound but no upper bound.

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