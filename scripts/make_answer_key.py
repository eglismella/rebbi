"""Draft the answer key for dep-audit-v1 from the pinned audit target.

Reads setup.py and every module under the package with `ast`; nothing in the
target is imported or executed. Nitya reviews the output by hand (task 5).

    python -I scripts/make_answer_key.py targets/sqlite-utils sqlite_utils https://github.com/simonw/sqlite-utils \
        > specs/answer-key-sqlite-utils-3.38.json
"""

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

# Distribution name -> the module name code imports. Only the ones that differ.
# setuptools ships pkg_resources, which is what these packages import from it.
IMPORT_NAMES = {"python-dateutil": "dateutil", "pyyaml": "yaml", "python-ulid": "ulid", "py-lru-cache": "lru",
                "click-default-group-wheel": "click_default_group", "setuptools": "pkg_resources",
                "beautifulsoup4": "bs4"}


def setup_kwargs(setup_py: Path) -> dict:
    tree = ast.parse(setup_py.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "setup":
            return {kw.arg: ast.literal_eval(kw.value) for kw in node.keywords
                    if kw.arg in ("install_requires", "extras_require")}
    raise SystemExit("no setup() call found")


def split_requirement(req: str) -> tuple[str, str]:
    m = re.match(r"^([A-Za-z0-9_.\-]+)\s*(.*)$", req.strip())
    return m.group(1).lower(), m.group(2).strip()


def import_name(dist: str) -> str:
    return IMPORT_NAMES.get(dist, dist.replace("-", "_"))


def guarded_nodes(tree: ast.AST) -> set[int]:
    """Ids of import nodes inside a `try` whose handler catches ImportError: optional imports."""
    guarded: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Try) and any(
            getattr(h.type, "id", None) in ("ImportError", "ModuleNotFoundError") for h in node.handlers
        ):
            for stmt in node.body + [s for h in node.handlers for s in h.body]:
                guarded.update(id(n) for n in ast.walk(stmt))
    return guarded


def imports_by_file(package_dir: Path, root: Path) -> tuple[dict[str, set[str]], dict[str, bool]]:
    """Top-level module -> files importing it, and whether every one of those imports is optional."""
    found: dict[str, set[str]] = {}
    always_guarded: dict[str, bool] = {}
    for path in sorted(package_dir.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        guarded = guarded_nodes(tree)
        rel = path.relative_to(root).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                found.setdefault(top, set()).add(rel)
                always_guarded[top] = always_guarded.get(top, True) and id(node) in guarded
    return found, always_guarded


def main(repo: str, package: str, url: str) -> None:
    root = Path(repo)
    kw = setup_kwargs(root / "setup.py")
    runtime = [split_requirement(r) for r in kw["install_requires"]]
    used, guarded = imports_by_file(root / package, root)
    optional = [split_requirement(r)[0] for reqs in kw["extras_require"].values() for r in reqs]
    declared = {import_name(name) for name in [n for n, _ in runtime] + optional}
    third_party = {m for m in used if m not in sys.stdlib_module_names and m != package}

    key = {
        "job_template": "dep-audit-v1",
        "repo": url,
        "commit": subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True,
                                 check=True).stdout.strip(),
        "manifest": "setup.py",
        "runtime_dependencies": [{"name": n, "constraint": c} for n, c in runtime],
        "optional_groups": {g: sorted(split_requirement(r)[0] for r in reqs)
                            for g, reqs in kw["extras_require"].items()},
        "imports": {n: sorted(used.get(import_name(n), ())) for n, _ in runtime},
        "unpinned": sorted(n for n, c in runtime if not c),
        "unused_dependencies": sorted(n for n, _ in runtime if import_name(n) not in used),
        "undeclared_imports": [
            {"module": m, "files": sorted(used[m]), "optional": guarded[m]} for m in sorted(third_party - declared)
        ],
    }
    json.dump(key, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
