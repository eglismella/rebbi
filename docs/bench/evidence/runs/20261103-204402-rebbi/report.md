## 1. Scope
- Repository: https://github.com/simonw/llm
- Commit: `e9a6998ca38946cfef75bdb7535d8bdc652ef381`
- Manifest files read: `setup.py`. The repository has no `setup.cfg`, `pyproject.toml` or `requirements*.txt`.
- Source scanned: every `.py` file under `llm/`, using import statements found by search. I did not read the files in full.

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
- pydantic: `llm/cli.py`, `llm/default_plugins/openai_models.py`, `llm/models.py`, `llm/templates.py`
- PyYAML: `llm/cli.py`, `llm/default_plugins/openai_models.py`
- pluggy: `llm/hookspecs.py`, `llm/plugins.py`
- python-ulid: `llm/models.py`
- setuptools: `llm/plugins.py`, which imports `pkg_resources`, a module provided by setuptools
- pip: no file imports it

## 5. Unused and undeclared
- **Unused:** `pip` is declared but never imported. It may be needed at runtime for the plugin install and uninstall commands, which I did not check.
- **Undeclared:**
  - `requests` is imported in `llm/default_plugins/openai_models.py`. The import is not optional, since it sits outside any `try`/`except ImportError`. Only `requests-mock` and `types-requests` are declared, in the `test` extra. `requests` probably arrives as a dependency of `openai`, but it is not declared.
- `numpy` is declared in the `test` extra but is not imported by the package.

## 6. Version pinning
Runtime dependencies with no version constraint: `click`, `PyYAML`, `pluggy`, `python-ulid`, `setuptools`, `pip`.

## 7. Risks and recommendations
- Declare `requests` in `install_requires`. It is imported unconditionally but never declared.
- `openai<1.0` pins to an old major version and will conflict with environments that need the newer OpenAI SDK. Plan a migration.
- `llm/plugins.py` imports `pkg_resources` from setuptools, which is deprecated. Move to `importlib.metadata`.
- Add lower bounds to the unpinned dependencies, at least `click`, `pluggy` and `PyYAML`, for reproducible installs.
- Confirm whether `pip` is needed at runtime. If it is only used through subprocess calls, document that. Otherwise remove it.
- `llm/default_plugins/openai_models.py` has a `try`/`except ImportError` that supports both pydantic v1 and v2. Keep the `pydantic>=1.10.2` constraint consistent with that.

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
    "pydantic": ["llm/cli.py", "llm/default_plugins/openai_models.py", "llm/models.py", "llm/templates.py"],
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