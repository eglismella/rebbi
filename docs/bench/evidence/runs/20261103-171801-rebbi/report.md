## 1. Scope
- Repository: https://github.com/simonw/llm
- Commit: e9a6998ca38946cfef75bdb7535d8bdc652ef381
- Manifest files read: `setup.py`. The repository also contains `docs/requirements.txt` and `docs/plugins/llm-markov/pyproject.toml`. I did not read either one, because they are docs and example-plugin files and not the package's own manifest.
- Imports were searched across all `llm/**/*.py`.

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
- `click`: `llm/cli.py`, `llm/__init__.py`, `llm/default_plugins/openai_models.py`
- `openai`: `llm/default_plugins/openai_models.py`
- `click-default-group`: `llm/cli.py`
- `sqlite-utils`: `llm/cli.py`, `llm/embeddings.py`
- `sqlite-migrate`: `llm/embeddings_migrations.py`
- `pydantic`: `llm/models.py`, `llm/templates.py`, `llm/cli.py`, `llm/default_plugins/openai_models.py`
- `PyYAML`: `llm/cli.py`, `llm/default_plugins/openai_models.py`
- `pluggy`: `llm/hookspecs.py`, `llm/plugins.py`
- `python-ulid`: `llm/models.py`
- `setuptools`: `llm/plugins.py`, which imports `pkg_resources` from setuptools.
- `pip`: no file imports it.

## 5. Unused and undeclared
- **Unused:** `pip`. It is never imported. `llm/cli.py` only invokes it through `run_module("pip", ...)` and a `["pip", "install"]` argument list, so it is needed at runtime but not as an import.
- **Undeclared:** `requests` is imported in `llm/default_plugins/openai_models.py` and is not optional, since the import sits outside any `try`/`except ImportError`. It is not in `install_requires`. Only `requests-mock` and `types-requests` appear in the `test` extra, and neither provides `requests` itself. It currently arrives only as a transitive dependency of `openai<1.0`.
- `numpy` is declared only in the `test` extra, and I found no imports of it in `llm/`.

## 6. Version pinning
Runtime dependencies with no version constraint: `click`, `PyYAML`, `pluggy`, `python-ulid`, `setuptools`, `pip`.

## 7. Risks and recommendations
- Declare `requests` in `install_requires`. It is imported unconditionally, so the package depends on `openai` pulling it in transitively.
- `llm/plugins.py` uses `pkg_resources`, which is deprecated and is removed in newer setuptools releases. Move to `importlib.metadata` and consider bounding `setuptools`.
- Six runtime dependencies are unbounded, which risks breakage when upstream releases change. Add at least lower bounds.
- `openai<1.0` pins to the legacy API. This blocks upgrades and is a maintenance risk.
- `pip` is needed only because of `run_module`. Document that, or call `sys.executable -m pip` instead.
- `sqlite-migrate>=0.1a2` allows a pre-release version. Consider requiring a stable release.

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
    "pydantic": ["llm/models.py", "llm/templates.py", "llm/cli.py", "llm/default_plugins/openai_models.py"],
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