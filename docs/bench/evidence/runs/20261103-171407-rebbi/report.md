# dep-audit-v1 report: simonw/llm

## 1. Scope
- Repository: https://github.com/simonw/llm
- Commit: `e9a6998ca38946cfef75bdb7535d8bdc652ef381`
- Manifest files read: `setup.py`. It is the only manifest in the repository. I found no `setup.cfg`, `pyproject.toml` or `requirements*.txt`.
- Package imports were checked in all `llm/**/*.py` files.

## 2. Runtime dependencies
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
- pluggy: `llm/hookspecs.py`, `llm/plugins.py`
- python-ulid: `llm/models.py`
- setuptools: `llm/plugins.py`, which imports `pkg_resources`. That module is shipped by setuptools.
- pip: no file imports it.

## 5. Unused and undeclared
- **Unused:** `pip`. No file imports it. It may be declared so that plugin installation can call `pip`, but I did not check for that.
- **Undeclared:** `requests`, imported in `llm/default_plugins/openai_models.py`.
  - The import is unconditional, not inside `try` / `except ImportError`, so it is not optional.
  - `requests` is not declared in `install_requires` or in any extra. The `test` extra lists only `requests-mock` and `types-requests`.
  - It currently arrives only as a transitive dependency, probably through `openai`.
- The `try` / `except ImportError` block in `openai_models.py` only switches between pydantic v1 and v2 imports. Both are from the declared `pydantic`.

## 6. Version pinning
Runtime dependencies with no version constraint: `click`, `PyYAML`, `pluggy`, `python-ulid`, `setuptools`, `pip`.

## 7. Risks and recommendations
- Declare `requests` in `install_requires`. The package imports it directly and relies on a transitive install.
- `openai<1.0` is capped below the 1.x API, so the package cannot use current openai releases until it is migrated.
- Add lower bounds to `click`, `pluggy`, `PyYAML` and `python-ulid`.
- `pkg_resources` is deprecated and removed in newer setuptools releases. Consider moving to `importlib.metadata` and dropping the runtime `setuptools` dependency.
- Confirm that `pip` is needed at runtime. If it is not, drop it from `install_requires`.

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
    "pluggy": ["llm/hookspecs.py", "llm/plugins.py"],
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