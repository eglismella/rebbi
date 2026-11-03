# db-to-sqlite dependency audit (dep-audit-v1)

## 1. Scope
- Repository: https://github.com/simonw/db-to-sqlite
- Commit: b7c95fcfe853ca5fc2236bfbf7e4a80ca9239969
- Manifest files read: `setup.py`. I found no other manifest in my searches. I did not look for `requirements*.txt`, `pyproject.toml` or `setup.cfg`.
- Source scanned for imports: `db_to_sqlite/*.py`. Only `db_to_sqlite/cli.py` contained imports.

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
- `sqlalchemy`: `db_to_sqlite/cli.py` (imports `create_engine`, `inspect`, `text`)
- `sqlite-utils`, imported as `sqlite_utils`: `db_to_sqlite/cli.py` (imports `Database`)

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports: none. The only other import is `itertools`, which is in the standard library.
- `mysqlclient` and `psycopg2` are declared as extras only. They are database drivers that SQLAlchemy loads at runtime, so no file imports them.

## 6. Version pinning
- `sqlalchemy` and `click` have no version constraint.

## 7. Risks and recommendations
- Risk: `sqlalchemy` is unpinned and the code uses `create_engine`, `inspect` and `text`. A future major release could break these calls. SQLAlchemy 2.0 changed the `text` and engine execution APIs, among others.
- Risk: `click` is unpinned.
- Risk: `psycopg2` and `mysqlclient` build from source on some platforms, which can make installs fail.
- Recommendation: add lower and upper bounds, for example `sqlalchemy>=1.4,<3` and `click>=7`. Choose the actual bounds after testing against those versions.
- Recommendation: consider `psycopg2-binary` for the PostgreSQL extra, or document the build requirements.
- Recommendation: consider moving to `pyproject.toml` and running a periodic dependency check in CI.

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