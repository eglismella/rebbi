# dep-audit-v1 report: simonw/llm

## 1. Scope
- Repository: https://github.com/simonw/llm
- Commit: e9a6998ca38946cfef75bdb7535d8bdc652ef381
- Manifest files read: `setup.py`. The repository has no `setup.cfg`, `pyproject.toml` or `requirements*.txt`.
- Source scanned: all `.py` files under `llm/`, using Grep for import statements.

## 2. Runtime dependencies
These are the `install_requires` entries as declared:
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
`extras_require` has one group.
- `test`: pytest, numpy, requests-mock, cogapp, mypy, black, ruff, types-click, types-pyyaml, types-requests, types-setuptools

## 4. Where runtime dependencies are used
- click: `llm/__init__.py`, `llm/cli.py`, `llm/default_plugins/openai_models.py`
- openai: `llm/default_plugins/openai_models.py`
- click-default-group: `llm/cli.py`
- sqlite-utils: `llm/cli.py`, `llm/embeddings.py`
- sqlite-migrate: `llm/embeddings_migrations.py`
- pydantic: `llm/cli.py`, `llm/models.py`, `llm/templates.py`, `llm/default_plugins/openai_models.py`
- pyyaml: `llm/cli.py`, `llm/default_plugins/openai_models.py`
- pluggy: `llm/hookspecs.py`, `llm/plugins.py`
- python-ulid: `llm/models.py`
- setuptools: `llm/plugins.py`. It imports `pkg_resources`, which setuptools provides.
- pip: no file imports it.

## 5. Unused and undeclared
- **Unused:** `pip`. It is declared but never imported.
- **Undeclared:** `requests` is imported in `llm/default_plugins/openai_models.py`. The import is not optional, because it is a plain top-level `import requests`. `requests` is not declared in `install_requires` or in any extra. It is probably only available because `openai` depends on it. The test extra has `requests-mock` and `types-requests`, but not `requests` itself.
- The `try`/`except ImportError` in `openai_models.py` only covers pydantic v1 and v2 imports. Both are of the declared `pydantic`.

## 6. Version pinning
These runtime dependencies have no version constraint: click, pyyaml, pluggy, python-ulid, setuptools, pip.

## 7. Risks and recommendations
- Add `requests` to `install_requires`. The code imports it directly, and it is currently only a transitive dependency.
- Remove `pip` from `install_requires`, since nothing imports it.
- `pkg_resources` is deprecated and is being removed from newer setuptools releases. Move `llm/plugins.py` to `importlib.metadata`. Until then, constrain `setuptools`.
- `openai<1.0` pins an old major version. Plan a migration to the 1.x API.
- Several dependencies are unconstrained: click, pyyaml, pluggy and python-ulid. Add lower bounds, and upper bounds where appropriate.
- `pydantic>=1.10.2` allows both v1 and v2. The code handles this with a fallback import, so test against both versions.

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