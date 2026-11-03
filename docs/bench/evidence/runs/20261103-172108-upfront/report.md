## 1. Scope
- Repository: https://github.com/simonw/llm
- Commit: e9a6998ca38946cfef75bdb7535d8bdc652ef381
- Manifest files read: `setup.py`. The Glob found no `setup.cfg`, `pyproject.toml` or `requirements*.txt`.
- Source scanned: all `.py` files under `llm/`.

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
- `test`: pytest, numpy, requests-mock, cogapp, mypy, black, ruff, types-click, types-pyyaml, types-requests, types-setuptools

## 4. Where runtime dependencies are used
- click: `llm/cli.py`, `llm/__init__.py`, `llm/default_plugins/openai_models.py`
- openai: `llm/default_plugins/openai_models.py`
- click-default-group: `llm/cli.py`
- sqlite-utils: `llm/cli.py`, `llm/embeddings.py`
- sqlite-migrate: `llm/embeddings_migrations.py`
- pydantic: `llm/cli.py`, `llm/models.py`, `llm/templates.py`, `llm/default_plugins/openai_models.py`
- pyyaml: `llm/cli.py`, `llm/default_plugins/openai_models.py`
- pluggy: `llm/hookspecs.py`, `llm/plugins.py`
- python-ulid: `llm/models.py`
- setuptools: `llm/plugins.py`. It imports `pkg_resources`, which setuptools provides.
- pip: no imports.

## 5. Unused and undeclared
- **Unused:** `pip`. No file imports it. It may be declared so that the `llm install` command can run pip, but I did not check that.
- **Undeclared:** `requests`, imported in `llm/default_plugins/openai_models.py`.
  - The import is not optional. It is a plain top-level `import requests`.
  - `requests` is not in `install_requires`.
  - The `test` extra lists only `requests-mock` and `types-requests`. Neither one declares `requests` as a dependency here.
  - It is probably installed indirectly through `openai`, but `setup.py` does not declare it.
- The `try`/`except ImportError` in `openai_models.py` only switches between pydantic v2 and v1 import paths. Pydantic is declared, so this is not an undeclared import.

## 6. Version pinning
Runtime dependencies with no version constraint: click, PyYAML, pluggy, python-ulid, setuptools, pip.

## 7. Risks and recommendations
- Declare `requests` in `install_requires`. It is imported unconditionally but not declared.
- `openai<1.0` is a hard cap on an old major version. It blocks upgrades and may leave the project on unmaintained or vulnerable releases.
- Add lower bounds to the unconstrained dependencies, especially `click`, `pluggy` and `setuptools`.
- `pkg_resources` is deprecated and removed from newer setuptools releases. Move to `importlib.metadata`.
- Review whether `pip` needs to be a runtime dependency. No code imports it.
- `numpy` appears only in the test extra. Nothing in `llm/` imports it. Tests may use it, but I did not check.

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