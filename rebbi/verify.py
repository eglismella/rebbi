"""The verifier: checks an audit report against the job template's answer key.

It fails closed: a missing section, a missing or unparsable JSON appendix, or
any value that differs from the key is a FAIL. A confident but wrong report is
worse than one that visibly stopped, so nothing is graded on partial credit.

    python -m rebbi.verify runs/<run>/report.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_KEY = Path(__file__).resolve().parent.parent / "specs" / "answer-key-sqlite-utils-3.38.json"
SECTIONS = range(1, 8)
HEADING = re.compile(r"^##\s*(\d+)\.", re.M)
JSON_BLOCK = re.compile(r"```json\s*\n(.*?)\n\s*```", re.S)


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str = ""


def _dist(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def _package(requirement: str) -> str:
    """The package a requirement names: 'black>=24.1.1' is black. Optional groups list packages, not versions."""
    return _dist(re.split(r"[\s\[<>=!~;@(]", requirement.strip(), maxsplit=1)[0])


def _path(p: str) -> str:
    return p.strip().replace("\\", "/").removeprefix("./")


def _diff(expected: set, found: set) -> str:
    parts = []
    if missing := expected - found:
        parts.append(f"missing {sorted(missing)}")
    if extra := found - expected:
        parts.append(f"unexpected {sorted(extra)}")
    return "; ".join(parts)


def _same(name: str, expected: set, found: set) -> Check:
    return Check(name, expected == found, _diff(expected, found))


def sections(report: str) -> dict[int, str]:
    marks = list(HEADING.finditer(report))
    bodies = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(report)
        bodies[int(m.group(1))] = report[m.end():end].strip()
    return bodies


def verify_report(report: str, key: dict[str, Any]) -> list[Check]:
    found = sections(report)
    empty = [n for n in SECTIONS if not found.get(n)]
    checks = [Check("seven numbered sections", not empty, f"missing or empty: {empty}" if empty else "")]

    blocks = JSON_BLOCK.findall(report)
    try:
        data = json.loads(blocks[-1])
        if not isinstance(data, dict):
            raise ValueError("not an object")
    except (IndexError, ValueError) as e:
        reason = "no JSON appendix" if not blocks else f"JSON appendix does not parse: {e}"
        return checks + [Check("JSON appendix", False, reason)]
    checks.append(Check("JSON appendix", True))

    try:
        checks += [
            _same("runtime dependencies",
                  {(_dist(d["name"]), d["constraint"].strip()) for d in key["runtime_dependencies"]},
                  {(_dist(d["name"]), str(d.get("constraint") or "").strip())
                   for d in data["runtime_dependencies"]}),
            _same("optional groups",
                  {(g, _dist(p)) for g, ps in key["optional_groups"].items() for p in ps},
                  {(g, _package(p)) for g, ps in data["optional_groups"].items() for p in ps}),
            _same("imports per runtime dependency",
                  {(_dist(d), _path(f)) for d, fs in key["imports"].items() for f in fs},
                  {(_dist(d), _path(f)) for d, fs in data["imports"].items() for f in fs}),
            _same("unused dependencies",
                  {_dist(d) for d in key["unused_dependencies"]},
                  {_dist(d) for d in data["unused_dependencies"]}),
            _same("undeclared imports",
                  {(u["module"], _path(f), bool(u["optional"])) for u in key["undeclared_imports"] for f in u["files"]},
                  {(u["module"], _path(f), bool(u.get("optional"))) for u in data["undeclared_imports"]
                   for f in u["files"]}),
            _same("unpinned dependencies", {_dist(d) for d in key["unpinned"]}, {_dist(d) for d in data["unpinned"]}),
        ]
    except (KeyError, TypeError, AttributeError) as e:
        checks.append(Check("JSON appendix fields", False, f"missing or malformed field: {e}"))
    return checks


def passed(checks: list[Check]) -> bool:
    return bool(checks) and all(c.ok for c in checks)


def render(checks: list[Check]) -> str:
    lines = [f"{'PASS' if c.ok else 'FAIL'}  {c.name}" + (f": {c.detail}" if c.detail else "") for c in checks]
    lines.append(f"VERIFIER: {'PASS' if passed(checks) else 'FAIL'}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="rebbi.verify")
    p.add_argument("report", type=Path)
    p.add_argument("--key", type=Path, default=DEFAULT_KEY)
    args = p.parse_args(argv)
    report = args.report.read_text(encoding="utf-8") if args.report.exists() else ""
    checks = verify_report(report, json.loads(args.key.read_text(encoding="utf-8")))
    print(render(checks))
    return 0 if passed(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
