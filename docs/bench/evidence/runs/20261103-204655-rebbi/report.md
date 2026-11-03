# dep-audit-v1 report: simonw/llm

## 1. Scope
- Repository: https://github.com/simonw/llm
- Commit: e9a6998ca38946cfef75bdb7535d8bdc652ef381
- Manifest files read: `setup.py`. The only other manifests are `docs/requirements.txt` and `docs/plugins/llm-markov/pyproject.toml`. I did not read them because they are docs and example-plugin files, not part of the package.
- Source scanned for imports: every `.py` file under `llm/`.

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
- pydantic: `llm/cli.py`, `llm/templates.py`, `llm/models.py`, `llm/default_plugins/openai_models.py`
- PyYAML: `llm/cli.py`, `llm/default_plugins/openai_models.py`
- pluggy: `llm/hookspecs.py`, `llm/plugins.py`
- python-ulid: `llm/models.py`
- setuptools: `llm/plugins.py`. It imports `pkg_resources`, which setuptools provides.
- pip: no file imports it. `llm/cli.py` runs it with `run_module("pip", ...)` at lines 1028 and 1037.

## 5. Unused and undeclared
- **Unused (no import):** `pip`. It is used at runtime through `runpy.run_module("pip")`, so it is a needed dependency rather than dead weight.
- **Undeclared imports:** `requests`, in `llm/default_plugins/openai_models.py`. It is a plain top-level import, not optional. The declared `requests-mock` is a different package and is only a test extra.
- `numpy` is declared only in the test extra, and no file in `llm/` imports it.

## 6. Version pinning
Runtime dependencies with no version constraint: `click`, `PyYAML`, `pluggy`, `python-ulid`, `setuptools`, `pip`.

## 7. Risks and recommendations
- Add `requests` to `install_requires`. It is currently only available because `openai<1.0` happens to depend on it, so the code breaks if that transitive dependency changes.
- `pkg_resources` is deprecated and is removed in newer setuptools releases. Move to `importlib.metadata`, and set a lower or upper bound on `setuptools`.
- `openai<1.0` is a pin to an old major version with no lower bound. Plan a migration to the 1.x API.
- Add loose lower bounds to the unconstrained packages (`click`, `pluggy`, `PyYAML`, `python-ulid`) for reproducible installs.
- Document that `pip` is invoked via `run_module`, or replace it with a `subprocess` call to `sys.executable -m pip`.
- The `llm` package imports `pydantic` in a `try/except ImportError` to handle both v1 and v2. Test against both versions, since the `>=1.10.2` constraint allows either.

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
    "pydantic": ["llm/cli.py", "llm/templates.py", "llm/models.py", "llm/default_plugins/openai_models.py"],
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