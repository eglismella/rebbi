## 1. Scope
- Repository: https://github.com/simonw/llm
- Commit: e9a6998ca38946cfef75bdb7535d8bdc652ef381
- Manifest files read: `setup.py`.
- Other manifests exist but were not read: `docs/requirements.txt` and `docs/plugins/llm-markov/pyproject.toml`. Neither belongs to the `llm` package.
- Imports were checked by searching `llm/**/*.py` with Grep. I read only the relevant lines of `llm/embeddings.py`, not whole files.

## 2. Runtime dependencies
Declared in `install_requires`:
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
Only the `test` group is declared:
- pytest
- numpy
- requests-mock
- cogapp
- mypy
- black
- ruff
- types-click
- types-PyYAML
- types-requests
- types-setuptools

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
- setuptools: `llm/plugins.py`, which does `import pkg_resources`. That module is provided by setuptools.
- pip: no file imports it.

## 5. Unused and undeclared
- **Unused:** `pip`. No file in the package imports it.
- **Undeclared:** `requests`, imported in `llm/default_plugins/openai_models.py`. The import is not optional, because it is a top-level import and not inside `try`/`except ImportError`. It is not in `install_requires` or in any extras group. It is only available transitively through `openai`. The `requests-mock` and `types-requests` packages in the test group do not count as declaring it.
- The `try`/`except ImportError` block in `openai_models.py` only switches between pydantic v1 and v2 imports. pydantic is declared.

## 6. Version pinning
These runtime dependencies have no version constraint:
- click
- PyYAML
- pluggy
- python-ulid
- setuptools
- pip

## 7. Risks and recommendations
- **Undeclared `requests`:** the package depends on it only through `openai`. If `openai` stops requiring it, the import breaks. Add `requests` to `install_requires`.
- **Unused `pip`:** nothing imports it, so remove it from `install_requires` unless it is needed at runtime for plugin installation. If it is needed, document that.
- **`openai<1.0` ceiling:** this blocks the current openai SDK. Plan a migration.
- **`setuptools` and `pkg_resources`:** `pkg_resources` is deprecated. Consider moving to `importlib.metadata`.
- **Unconstrained dependencies:** add lower bounds to the six dependencies listed in section 6. `pydantic` and `sqlite-migrate` already have lower bounds, and the code supports both pydantic v1 and v2.
- **`numpy` in the test group:** the extras do not show how the package uses it, so I did not check. No import of `numpy` was found in `llm/`.

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