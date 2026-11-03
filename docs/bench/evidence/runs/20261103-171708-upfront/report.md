## 1. Scope
- Repository: https://github.com/simonw/db-to-sqlite
- Commit: b7c95fcfe853ca5fc2236bfbf7e4a80ca9239969
- Manifest files read: `setup.py`. The repository has no `requirements*.txt`, `pyproject.toml` or `setup.cfg`.
- Source files checked for imports: `db_to_sqlite/cli.py` and `db_to_sqlite/__init__.py`. The `__init__.py` has no imports.
- The tests were also scanned, but they are not part of the package.

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
- `sqlalchemy`: `db_to_sqlite/cli.py`. It imports `create_engine`, `inspect` and `text`.
- `sqlite-utils`: `db_to_sqlite/cli.py`. It imports the module as `sqlite_utils` (`from sqlite_utils import Database`).
- `click`: `db_to_sqlite/cli.py`

## 5. Unused and undeclared
- Unused runtime dependencies: none.
- Undeclared third-party imports in the package: none. The only other import in `cli.py` is `itertools`, which is in the standard library.
- Outside the package, the tests import `MySQLdb` and `psycopg2` inside `try`/`except ImportError`. These come from the declared `mysqlclient` and `psycopg2` extras, so they are not undeclared. The tests also import `pytest`, which is declared in the `test` extras.

## 6. Version pinning
Runtime dependencies with no version constraint: `sqlalchemy` and `click`.

## 7. Risks and recommendations
- **Unbounded SQLAlchemy:** `sqlalchemy` has no constraint. The code uses `create_engine`, `inspect` and `text`, and SQLAlchemy 2.x changed several APIs. Add a tested lower bound and consider an upper bound, for example `sqlalchemy>=1.4,<3`.
- **Unconstrained click:** `click` has no constraint. Add a minimum version that has been tested.
- **Loose sqlite-utils bound:** `sqlite-utils>=2.9.1` has no upper bound. Consider testing against current releases and capping the major version.
- **Duplicate extras:** `test_mysql` and `test_postgresql` repeat `pytest`. This is harmless, but you could factor the shared test dependencies out.
- **Unpinned psycopg2:** the `postgresql` extra uses `psycopg2`, which needs build tools. Consider `psycopg2-binary` for easier installs.

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
    "sqlalchemy": ["db_to_sqlite/cli.py"],
    "sqlite-utils": ["db_to_sqlite/cli.py"],
    "click": ["db_to_sqlite/cli.py"]
  },
  "unused_dependencies": [],
  "undeclared_imports": [],
  "unpinned": ["sqlalchemy", "click"]
}
```