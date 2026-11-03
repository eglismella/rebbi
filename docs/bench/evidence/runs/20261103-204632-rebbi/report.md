## 1. Scope
- Repository: https://github.com/simonw/db-to-sqlite
- Commit: b7c95fcfe853ca5fc2236bfbf7e4a80ca9239969
- Manifest files read: `setup.py`. I found no other manifests (such as `requirements.txt` or `pyproject.toml`), but I did not run a search to confirm that.
- Source searched for imports: `db_to_sqlite/*.py`. Only `db_to_sqlite/cli.py` contains any imports.

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
- `sqlite-utils`, imported as `sqlite_utils`: `db_to_sqlite/cli.py`

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports: none. The only other imports are `itertools`, which is standard library, and the declared packages above.
- The database drivers (`mysqlclient`, `psycopg2`) are not imported directly. SQLAlchemy loads them at runtime, and they are declared as extras.

## 6. Version pinning
- `sqlalchemy` and `click` have no version constraint.

## 7. Risks and recommendations
- Unpinned `sqlalchemy` is the main risk. Its 1.x to 2.x API changes could break `create_engine`, `inspect` and `text` usage. Add a lower bound and an upper bound, for example `sqlalchemy>=1.4,<3`.
- `click` has no bound, so add a minimum version.
- `psycopg2` and `mysqlclient` need native build tooling. Consider documenting `psycopg2-binary` as an alternative.
- `python_requires>=3.7` is long past end of life. Review whether to raise it.

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