## 1. Scope
- Repository: https://github.com/simonw/llm
- Commit: e9a6998ca38946cfef75bdb7535d8bdc652ef381
- Manifest files read: `setup.py`.
- Other manifests found but not read: `docs/requirements.txt` and `docs/plugins/llm-markov/pyproject.toml`. Neither is part of the `llm` package.
- Imports were checked in every `.py` file under `llm/`.

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
- click: `llm/__init__.py`, `llm/cli.py`, `llm/default_plugins/openai_models.py`
- openai: `llm/default_plugins/openai_models.py`
- click-default-group: `llm/cli.py`
- sqlite-utils: `llm/cli.py`, `llm/embeddings.py`
- sqlite-migrate: `llm/embeddings_migrations.py`
- pydantic: `llm/cli.py`, `llm/models.py`, `llm/templates.py`, `llm/default_plugins/openai_models.py`
- PyYAML: `llm/cli.py`, `llm/default_plugins/openai_models.py`
- pluggy: `llm/hookspecs.py`, `llm/plugins.py`
- python-ulid: `llm/models.py`
- setuptools: `llm/plugins.py`. It imports `pkg_resources`, which setuptools provides.
- pip: no file imports it.

## 5. Unused and undeclared
- **Unused:** `pip`. `llm/cli.py` imports `run_module` from `runpy`, which suggests pip is run as a module. I did not read that code, so I did not confirm it. No file has an `import pip` statement.
- **Undeclared:**
  - `requests` is imported in `llm/default_plugins/openai_models.py` at module level. It is not optional. It is not declared as a runtime or optional dependency. Only `requests-mock` and `types-requests` appear in the `test` group.
  - `numpy` is not imported by the package. It appears only in the `test` group.

## 6. Version pinning
Runtime dependencies with no version constraint: `click`, `PyYAML`, `pluggy`, `python-ulid`, `setuptools`, `pip`.

## 7. Risks and recommendations
- Declare `requests` in `install_requires`. It is currently only available through a transitive dependency of `openai`.
- `pip` looks unused as an import. Confirm whether `llm/cli.py` runs it through `run_module`. If it does not, remove it.
- `pkg_resources` is deprecated and is removed in newer setuptools releases. Move `llm/plugins.py` to `importlib.metadata`.
- Six dependencies have no constraint at all, including `click` and `pluggy`. Add lower bounds.
- `openai<1.0` caps the dependency at the old API. Plan a migration to a newer `openai` release.
- `python_requires=">=3.7"` is old. Check it against the dependency versions.

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
    "click": ["llm/__init__.py", "llm/cli.py", "llm/default_plugins/openai_models.py"],
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