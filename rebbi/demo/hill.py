"""The hill: place n disjoint circles in the unit square to maximize the sum of their radii.

The evaluator is fixed and never edited by agents. It runs the candidate's solve.py in a subprocess
(60 s wall limit, fixed seeds), then validates the returned arrays itself and scores them.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

TOL = 1e-9
TIME_LIMIT_S = 60
EXERCISES = {"A": 26, "B": 32}
# Published best-known values, for the chart only. They are not results of this experiment.
REFERENCE = {
    "A": [{"value": 2.635, "source": "AlphaEvolve"}, {"value": 2.63598, "source": "ThetaEvolve, arXiv 2511.23473"}],
    "B": [{"value": 2.937, "source": "AlphaEvolve"}, {"value": 2.93957, "source": "arXiv 2605.04850"}],
}
ALLOWED = {"numpy", "scipy"}

RUNNER = """
import json, random, sys
import numpy
numpy.random.seed(0)
random.seed(0)
sys.path.insert(0, sys.argv[1])
import solve
centers, radii = solve.pack()
c = numpy.asarray(centers, dtype=float).tolist()
r = numpy.asarray(radii, dtype=float).tolist()
with open(sys.argv[2], "w") as f:
    json.dump({"centers": c, "radii": r}, f)
"""

START_SOLVE = '''"""Start: one circle in the centre and two rings, then shrink all radii by one factor until valid."""
import numpy as np

N = {n}


def pack():
    pts = [(0.5, 0.5)]
    inner = 8
    outer = N - 1 - inner
    for k in range(inner):
        a = 2 * np.pi * k / inner
        pts.append((0.5 + 0.2 * np.cos(a), 0.5 + 0.2 * np.sin(a)))
    for k in range(outer):
        a = 2 * np.pi * (k + 0.5) / outer
        pts.append((0.5 + 0.4 * np.cos(a), 0.5 + 0.4 * np.sin(a)))
    c = np.array(pts)
    r = np.minimum.reduce([c[:, 0], c[:, 1], 1 - c[:, 0], 1 - c[:, 1]])
    scale = 1.0
    for i in range(N):
        for j in range(i + 1, N):
            d = np.hypot(*(c[i] - c[j]))
            scale = min(scale, d / (r[i] + r[j]))
    return c, r * scale * 0.8  # 20% margin so no pair touches
'''


@dataclass
class Evaluation:
    score: float
    valid: bool
    reason: str
    centers: list | None = None
    radii: list | None = None
    seconds: float = 0.0

    def as_dict(self) -> dict:
        return {"score": self.score, "valid": self.valid, "reason": self.reason}


def start_solve(n: int) -> str:
    return START_SOLVE.format(n=n)


def check_imports(code: str, forbid_scipy: bool = False) -> str | None:
    """The first disallowed import, as a reason, or None."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"syntax error: {e.msg} (line {e.lineno})"
    stdlib = set(sys.stdlib_module_names)
    allowed = (ALLOWED - {"scipy"}) if forbid_scipy else ALLOWED
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        for full in names:
            top = full.split(".")[0]
            if top not in stdlib and top not in allowed:
                return f"forbidden import: {top}"
    return None


def validate(centers, radii, n: int) -> str | None:
    """The first violated check, or None if the packing is valid."""
    try:
        c = np.asarray(centers, dtype=float)
        r = np.asarray(radii, dtype=float)
    except (TypeError, ValueError):
        return "centers or radii are not numeric arrays"
    if c.shape != (n, 2):
        return f"centers shape {c.shape}, expected ({n}, 2)"
    if r.shape != (n,):
        return f"radii shape {r.shape}, expected ({n},)"
    if not (np.isfinite(c).all() and np.isfinite(r).all()):
        return "non-finite value"
    if not (r > 0).all():
        return "a radius is not positive"
    x, y = c[:, 0], c[:, 1]
    if ((x - r < -TOL) | (x + r > 1 + TOL) | (y - r < -TOL) | (y + r > 1 + TOL)).any():
        i = int(np.argmax((x - r < -TOL) | (x + r > 1 + TOL) | (y - r < -TOL) | (y + r > 1 + TOL)))
        return f"circle {i} sticks out of the unit square"
    dist = np.hypot(x[:, None] - x[None, :], y[:, None] - y[None, :])
    bad = dist < r[:, None] + r[None, :] - TOL
    np.fill_diagonal(bad, False)
    if bad.any():
        i, j = (int(v) for v in np.argwhere(bad)[0])
        return f"circles {i} and {j} overlap"
    return None


def evaluate(code: str, n: int, forbid_scipy: bool = False, time_limit: float = TIME_LIMIT_S) -> Evaluation:
    """Run `code` (a solve.py) and score the arrays it returns. Score 0 with a reason if anything fails."""
    import time

    t0 = time.monotonic()
    fail = lambda why: Evaluation(0.0, False, why, seconds=round(time.monotonic() - t0, 2))  # noqa: E731
    if (why := check_imports(code, forbid_scipy)) is not None:
        return fail(why)
    with tempfile.TemporaryDirectory(prefix="hill-") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "solve.py").write_text(code, encoding="utf-8")
        (tmp_path / "runner.py").write_text(RUNNER, encoding="utf-8")
        out = tmp_path / "out.json"
        try:
            proc = subprocess.run([sys.executable, str(tmp_path / "runner.py"), str(tmp_path), str(out)],
                                  capture_output=True, text=True, timeout=time_limit, cwd=tmp)
        except subprocess.TimeoutExpired:
            return fail(f"timeout after {time_limit:g} s")
        if proc.returncode != 0:
            last = (proc.stderr.strip().splitlines() or ["no message"])[-1][:200]
            return fail(f"solve.py crashed: {last}")
        try:
            data = json.loads(out.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return fail("pack() returned values that are not numbers")
    if (why := validate(data["centers"], data["radii"], n)) is not None:
        return fail(why)
    score = float(np.sum(data["radii"]))
    return Evaluation(score, True, "valid", data["centers"], data["radii"], round(time.monotonic() - t0, 2))
