"""The v2 hill: ship a set of Exercism Python exercises. Score = share of the set's test cases passing.

An exercise counts toward the score only once it is shipped (the Reviewer approved it, or it ran out of fix
attempts). The test runner copies the candidate and the exercise's own test file into a fresh temporary folder
and runs pytest there with a time limit. In replay mode no code runs: the candidate carries its result as a
marker line written by the replay backend.
"""

from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EXERCISES = ROOT / "exercises" / "demo2"
TIME_LIMIT_S = 60
DOCS_CHARS = 6000  # what the Researcher sees of the instructions
TESTS_CHARS = 7000  # what the Researcher sees of the test file
REPLAY = re.compile(r"^# replay-result: (\d+)/(\d+)$", re.M)


@dataclass
class Exercise:
    slug: str
    difficulty: int
    folder: Path
    solution_file: str
    test_file: str
    ntests: int

    @property
    def instructions(self) -> str:
        return (self.folder / "instructions.md").read_text(encoding="utf-8")

    @property
    def stub(self) -> str:
        return (self.folder / self.solution_file).read_text(encoding="utf-8")

    @property
    def tests(self) -> str:
        return (self.folder / self.test_file).read_text(encoding="utf-8")

    def test_source(self, names: list[str], limit: int = 2500) -> str:
        """Source of the named test methods (parsed, not run), up to `limit` characters."""
        src = self.tests
        try:
            tree = ast.parse(src)
        except SyntaxError:
            return ""
        want, parts = set(names), []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in want:
                seg = ast.get_source_segment(src, node)
                if seg:
                    parts.append(seg)
        return "\n\n".join(parts)[:limit]


@dataclass
class TestResult:
    passed: int
    total: int
    failing: list[str] = field(default_factory=list)
    output: str = ""

    @property
    def all_pass(self) -> bool:
        return self.total > 0 and self.passed >= self.total


def load_set(name: str, root: Path = EXERCISES) -> list[Exercise]:
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    denominators = {}
    dpath = root / "denominators.json"
    if dpath.exists():  # written by the preflight: test cases pytest collected with the reference solution
        denominators = json.loads(dpath.read_text(encoding="utf-8"))
    out = []
    for slug in manifest["sets"][name]["exercises"]:
        meta = json.loads((root / name / slug / "meta.json").read_text(encoding="utf-8"))
        out.append(Exercise(slug, int(meta["difficulty"]), root / name / slug, meta["solution_file"],
                            meta["test_file"], int(denominators.get(slug, meta["ntests"]))))
    return out


def run_tests(ex: Exercise, code: str, replay: bool = False) -> TestResult:
    if replay or REPLAY.search(code or ""):
        m = REPLAY.search(code or "")
        if not m:
            return TestResult(0, ex.ntests, [], "replay: no result marker")
        p, t = int(m.group(1)), int(m.group(2))
        return TestResult(min(p, ex.ntests), ex.ntests, [f"test_{i}" for i in range(ex.ntests - min(p, ex.ntests))],
                          f"replay {p}/{t}")
    with tempfile.TemporaryDirectory(prefix="rebbi-v2-") as tmp:
        d = Path(tmp)
        shutil.copy(ex.folder / ex.test_file, d / ex.test_file)
        (d / ex.solution_file).write_text(code, encoding="utf-8")
        xml = d / "report.xml"
        try:
            proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                   f"--junitxml={xml}", ex.test_file], cwd=d, capture_output=True, text=True,
                                  timeout=TIME_LIMIT_S)
            output = (proc.stdout + proc.stderr)[-6000:]
        except subprocess.TimeoutExpired:
            return TestResult(0, ex.ntests, [], f"timeout after {TIME_LIMIT_S} s")
        return parse_junit(xml, ex.ntests, output)


def parse_junit(xml: Path, ntests: int, output: str) -> TestResult:
    if not xml.exists():
        return TestResult(0, ntests, [], output)
    try:
        root = ET.parse(xml).getroot()
    except ET.ParseError:
        return TestResult(0, ntests, [], output)
    cases = root.iter("testcase")
    passed, failing = 0, []
    for c in cases:
        bad = any(ch.tag in ("failure", "error", "skipped") for ch in c)
        if bad:
            failing.append(c.get("name", "?"))
        else:
            passed += 1
    # A collection error (syntax error, wrong names) yields no test cases: count every test as failing.
    return TestResult(min(passed, ntests), ntests, failing, output)


def failure_excerpt(res: TestResult, limit: int = 3000) -> str:
    text = res.output
    i = text.find("FAILURES")
    if i < 0:
        i = text.find("ERROR")
    return (text[i:] if i >= 0 else text)[:limit]


def score(shipped: dict[str, int], exercises: list[Exercise]) -> float:
    """Percent of the set's test cases passing in shipped exercises."""
    total = sum(e.ntests for e in exercises)
    return 100.0 * sum(shipped.values()) / total if total else 0.0
