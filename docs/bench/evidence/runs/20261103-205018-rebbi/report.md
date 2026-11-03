# dep-audit-v1: simonw/llm

## 1. Scope
- Repository: https://github.com/simonw/llm
- Commit: e9a6998ca38946cfef75bdb7535d8bdc652ef381
- Manifest files read: `setup.py`. The repository has no `setup.cfg`, `pyproject.toml` or `requirements*.txt` at the root.
- Package files searched for imports: all `.py` files under `llm/`.

## 2. Runtime dependencies
These are the `install_requires` entries from `setup.py`, as declared:
- `click`
- `openai<1.0`
- `click-default-group>=1.2.3`
- `sqlite-utils>=3.35.0`
- `sqlite-migrate>=0.1a2`
- `pydantic>=1.10.2`
- `PyYAML`
- `pluggy`
- `python-ulid`
- `setuptools`
- `pip`

## 3. Optional dependency groups
- `test`: pytest, numpy, requests-mock, cogapp, mypy, black, ruff, types-click, types-PyYAML, types-requests, types-setuptools

## 4. Where runtime dependencies are used
- click: `llm/cli.py`, `llm/__init__.py`, `llm/default_plugins/openai_models.py`
- openai: `llm/default_plugins/openai_models.py`
- click-default-group: `llm/cli.py`
- sqlite-utils: `llm/cli.py`, `llm/embeddings.py`
- sqlite-migrate: `llm/embeddings_migrations.py`
- pydantic: `llm/cli.py`, `llm/models.py`, `llm/templates.py`, `llm/default_plugins/openai_models.py`
- PyYAML: `llm/cli.py`, `llm/default_plugins/openai_models.py`
- pluggy: `llm/plugins.py`, `llm/hookspecs.py`
- python-ulid: `llm/models.py`
- setuptools: `llm/plugins.py`, which imports `pkg_resources`, a module shipped by setuptools.
- pip: not imported anywhere.

## 5. Unused and undeclared
- **Unused runtime dependency:** `pip`. No file imports it.
- **Undeclared third-party imports:**
  - `requests` is imported in `llm/default_plugins/openai_models.py`. The import is not optional. `requests` appears only in the `test` group as `requests-mock` and `types-requests`, and it is not a runtime dependency. It probably arrives only as a transitive dependency of `openai`.
- `numpy` is declared only in the `test` extra. The package does not import it.

## 6. Version pinning
Runtime dependencies with no version constraint: `click`, `PyYAML`, `pluggy`, `python-ulid`, `setuptools`, `pip`.

## 7. Risks and recommendations
- Declare `requests` in `install_requires`. It is imported unconditionally, and relying on `openai` to pull it in is fragile.
- Remove `pip` from `install_requires` if nothing uses it. I only checked for imports, not for subprocess calls. If it is needed, document why.
- `llm/plugins.py` imports `pkg_resources`, which is deprecated and removed from newer setuptools releases. Migrate to `importlib.metadata`, or at least put a lower or upper bound on `setuptools`.
- `openai<1.0` is capped at an old major version. Plan a migration to the 1.x API.
- Add lower bounds to the unconstrained dependencies, at least `pluggy`, `python-ulid` and `click`.
- `llm/default_plugins/openai_models.py` falls back to the pydantic v1 API inside `try/except ImportError`. Both pydantic v1 and v2 are supported by the declared `>=1.10.2`. Test against both.

```json
{
  "commit": "e9a6998ca38946cfef75bdb7535d8bdc652ef381",
  "runtime_dependencies": [
    {"name": "click", "constraint": ""},
    {"name": "openai", "constraint": "<1.0"},
    {"name": "click-default-group", "constraint": ">=1.2.3"},
    {"name": "sqlite-utils", "constraint": ">=3.35.0"},
    {"name": "sqlite-migrate", "constraint": ">=0.1a2"},
    {"name": "pydantic", "constraint": ">=1.10.2"},
    {"name": "pyyaml", "constraint": ""},
    {"name": "pluggy", "constraint": ""},
    {"name": "python-ulid", "constraint": ""},
    {"name": "setuptools", "constraint": ""},
    {"name": "pip", "constraint": ""}
  ],
  "optional_groups": {
    "test": ["pytest", "numpy", "requests-mock", "cogapp", "mypy", "black", "ruff", "types-click", "types-pyyaml", "types-requests", "types-setuptools"]
  },
  "imports": {
    "click": ["llm/cli.py", "llm/__init__.py", "llm/default_plugins/openai_models.py"],
    "openai": ["llm/default_plugins/openai_models.py"],
    "click-default-group": ["llm/cli.py"],
    "sqlite-utils": ["llm/cli.py", "llm/embeddings.py"],
    "sqlite-migrate": ["llm/embeddings_migrations.py"],
    "pydantic": ["llm/cli.py", "llm/models.py", "llm/templates.py", "llm/default_plugins/openai_models.py"],
    "pyyaml": ["llm/cli.py", "llm/default_plugins/openai_models.py"],
    "pluggy": ["llm/plugins.py", "llm/hookspecs.py"],
    "python-ulid": ["llm/models.py"],
    "setuptools": ["llm/plugins.py"],
    "pip": []
  },
  "unused_dependencies": ["pip"],
  "undeclared_imports": [
    {"module": "requests", "files": ["llm/default_plugins/openai_models.py"], "optional": false}
  ],
  "unpinned": ["click", "pyyaml", "pluggy", "python-ulid", "setuptools", "pip"]
}
```