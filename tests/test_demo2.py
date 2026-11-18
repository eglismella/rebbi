"""v2 harness: budgets, queues, Rebbi loans, replay gate, rehearsal end to end on a tiny synthetic suite."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from rebbi.demo2 import report, runner, suite
from rebbi.demo2.backends import ReplayBackend, ScriptedBackend
from rebbi.demo2.team import ROLES, RunConfig, Team

N_EX = 6


def make_suite(root: Path, n: int = N_EX) -> Path:
    """n tiny exercises per set: f(x) must return x + k. Stub returns None."""
    ref = root / "_reference"
    ref.mkdir(parents=True)
    sets = {}
    for name in ("A", "B"):
        slugs = []
        for i in range(n):
            slug = f"add-{name.lower()}{i}"
            mod = slug.replace("-", "_")
            d = root / name / slug
            d.mkdir(parents=True)
            (d / "instructions.md").write_text(f"Return x plus {i}.\n")
            (d / f"{mod}.py").write_text("def f(x):\n    pass\n")
            tests = "\n".join(f"    def test_{j}(self):\n        self.assertEqual(f({j}), {j + i})\n" for j in range(4))
            (d / f"{mod}_test.py").write_text(f"import unittest\nfrom {mod} import f\n\n\nclass T(unittest.TestCase):\n{tests}")
            (ref / f"{slug}.py").write_text(f"def f(x):\n    return x + {i}\n")
            (d / "meta.json").write_text(json.dumps({"slug": slug, "difficulty": 1 + i % 3, "solution_file": f"{mod}.py",
                                                     "test_file": f"{mod}_test.py", "ntests": 4}))
            slugs.append(slug)
        sets[name] = {"exercises": slugs}
    (root / "MANIFEST.json").write_text(json.dumps({"sets": sets}))
    return root


@pytest.fixture()
def exroot(tmp_path):
    return make_suite(tmp_path / "ex")


def test_tests_run_and_score(exroot):
    ex = suite.load_set("A", exroot)[1]
    good = (exroot / "_reference" / f"{ex.slug}.py").read_text()
    assert suite.run_tests(ex, good).all_pass
    bad = suite.run_tests(ex, ex.stub)
    assert bad.passed == 0 and len(bad.failing) == 4
    assert "def test_0" in ex.test_source(bad.failing)
    assert suite.run_tests(ex, "# replay-result: 3/4").passed == 3


def test_budget_floors():
    floors = {"planner": 2000, "researcher": 3000, "coder": 3000, "evaluator": 2000, "reviewer": 3000}
    b = runner.budgets_from_pct({"planner": 1, "researcher": 9, "coder": 80, "evaluator": 5, "reviewer": 5}, 30000, floors)
    assert sum(b.values()) == 30000
    assert all(b[r] >= floors[r] for r in ROLES)
    assert runner.equal_split(30001)["coder"] == 6001


def run_team(exroot, tmp_path, **kw):
    T = kw.pop("T", 10000)
    budgets = kw.pop("budgets", runner.equal_split(T))
    cfg = RunConfig("t", "x", "A", 1, budgets, T, max_windows=kw.pop("max_windows", 40), summit=kw.pop("summit", 99.0),
                    **kw)
    team = Team(cfg, ScriptedBackend(reference=exroot / "_reference"), tmp_path / "run", suite.load_set("A", exroot))
    try:
        return team, asyncio.run(team.run())
    finally:
        team.ledger.close()


def test_pipeline_fills_and_drains(exroot, tmp_path):
    team, res = run_team(exroot, tmp_path, T=50000)
    assert res.score >= 99 and not res.ledger_problems
    w1 = res.windows[0]["agents"]
    assert w1["researcher"]["done"] > 0 and w1["coder"]["queue"] == 0  # hand-offs land at the next window
    last = res.windows[-1]["agents"]
    assert last["researcher"]["queue"] == 0  # drained: upstream idle at the end
    assert res.windows[0]["team"]["phase"] == 0 and res.windows[-1]["team"]["phase"] == 2


def test_tight_budget_blocks_and_rebbi_lends(exroot, tmp_path):
    budgets = {"planner": 2000, "researcher": 3500, "coder": 2500, "evaluator": 1500, "reviewer": 2500}
    _, res = run_team(exroot, tmp_path / "a", T=12000, budgets=budgets)
    assert any(w["agents"]["researcher"]["interrupted"] for w in res.windows)
    assert all(w["agents"][r]["expired"] >= 0 for w in res.windows for r in ROLES)
    _, res2 = run_team(exroot, tmp_path / "b", T=12000, budgets=budgets, rebbi=True,
                       shareable_pct={r: 60 for r in ROLES})
    moved = sum(l["tokens"] for w in res2.windows for l in w["team"]["loans"])
    assert moved > 0 and not res2.ledger_problems
    assert len(res2.windows) <= len(res.windows)


def test_market_runs(exroot, tmp_path):
    _, res = run_team(exroot, tmp_path, T=12000, rebbi=True, market=True)
    assert not res.ledger_problems and res.score > 0


def test_rehearsal_end_to_end(exroot, tmp_path, monkeypatch):
    from rebbi.demo2 import __main__ as cli
    assert cli.rehearsal(tmp_path, exroot) == 0
    data = json.loads((tmp_path / "runs" / "demo2-rehearsal" / "results" / "data.json").read_text())
    assert {r["sc"] for r in data["runs"]} == {"s1", "s2", "s3", "s3onB", "s3b", "s4"}
    f = data["runs"][0]["frames"][0]
    assert len(f["B"]) == 5 and "p" in f and "loans" in f
    conf = runner.load_config(runner.make_ctx(rehearsal=True, base=tmp_path / "runs" / "demo2-rehearsal",
                                              backend=ScriptedBackend()))
    assert conf["frozen"] and conf["calibration"]["T"] >= 5 * max(conf["floors"].values())


def test_replay_backend_is_deterministic(exroot, tmp_path):
    calls = [{"role": r, "kind": k, "total": 1000 + 10 * i, "stopped": False}
             for i, (r, k) in enumerate([("planner", "plan"), ("researcher", "spec"), ("coder", "code"),
                                         ("evaluator", "report"), ("reviewer", "approve"), ("reviewer", "fix")])]
    tests = [{"slug": e.slug, "by": "coder", "passed": 2, "total": 4} for e in suite.load_set("A", exroot)]
    outs = []
    for _ in range(2):
        cfg = RunConfig("r", "x", "A", 1, runner.equal_split(10000), 10000, summit=90.0, replay=True)
        team = Team(cfg, ReplayBackend(calls, tests, seed=7), tmp_path / f"r{len(outs)}", suite.load_set("A", exroot))
        res = asyncio.run(team.run())
        team.ledger.close()
        outs.append([w["team"]["score"] for w in res.windows])
    assert outs[0] == outs[1]


def test_lane_locks(exroot, tmp_path):
    ctx = runner.make_ctx(rehearsal=True, base=tmp_path / "b", backend=ScriptedBackend())
    assert runner.lock(ctx, "s1-r1") and not runner.lock(ctx, "s1-r1")
    runner.unlock(ctx, "s1-r1")
    assert runner.lock(ctx, "s1-r1")


def _make_shim(tmp_path, fake):
    """Executable wrapper around the fake script: a .cmd on Windows (a #!/bin/sh file cannot be spawned there)."""
    import os
    import stat
    import sys as _sys
    if os.name == "nt":
        shim = tmp_path / "shim.cmd"
        shim.write_text(f'@echo off\r\n"{_sys.executable}" "{fake}" %*\r\n')
    else:
        shim = tmp_path / "shim"
        shim.write_text(f"#!/bin/sh\nexec {_sys.executable} {fake} \"$@\"\n")
        shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    return shim


def test_autopilot_default_claude_resolves_on_path(tmp_path, monkeypatch):
    """On Windows claude is claude.cmd; a bare 'claude' cannot be spawned, so the default must be the resolved path."""
    import importlib

    import rebbi.demo2.autopilot as ap_mod
    fake = tmp_path / "claude.cmd"
    fake.write_text("@echo off\r\n")
    monkeypatch.setattr("shutil.which", lambda name: str(fake) if name == "claude" else None)
    mod = importlib.reload(ap_mod)
    try:
        assert mod.Autopilot("pietro", "1-3", root=tmp_path).claude == str(fake)
    finally:
        monkeypatch.undo()
        importlib.reload(ap_mod)


def test_autopilot_walks_every_phase(tmp_path, monkeypatch):
    """Fake python, git and claude: the autopilot goes preflight -> prepare -> lanes -> final, and resumes."""
    import os
    monkeypatch.delenv("REBBI_MACHINE", raising=False)  # set when pytest runs under the real autopilot
    import stat
    import sys as _sys

    from rebbi.demo2.autopilot import Autopilot
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    (root / ".env").write_text("CLAUDE_CODE_OAUTH_TOKEN=tok\n")
    calls = tmp_path / "calls.txt"
    fake = tmp_path / "fake.py"
    fake.write_text(f"""import sys, pathlib
args = sys.argv[1:]
open({str(calls)!r}, 'a').write(' '.join(args) + '\\n')
if args[:3] == ['-m', 'rebbi.demo2', 'prepare']:
    pathlib.Path('config/demo2.toml').write_text('frozen = true\\nT = 30000\\n')
if args[:1] == ['-p']:
    print('ready')
""")
    shim = _make_shim(tmp_path, fake)
    ap = Autopilot("pietro", "1-3", lanes=2, root=root, py=str(shim), claude=str(shim), git=str(shim),
                   sleep=lambda s: None, poll_s=0)
    assert ap.main() == 0
    log = calls.read_text()
    for step in ("rebbi.demo2 preflight", "pytest -q tests/test_demo2.py", "rebbi.demo2 rehearsal",
                 "rebbi.demo2 prepare", "push origin HEAD:demo-v2", "rebbi.demo2 run --repeats 1-3",
                 "rebbi.demo2 export --machine pietro", "rebbi.demo2 report"):
        assert step in log, step
    assert log.count("rebbi.demo2 run --repeats") == 2
    for ph in ("PREFLIGHT_DONE", "PREPARED", "RUNS_DONE", "FINAL_DONE"):
        assert (root / "docs" / "demo2" / "state" / "pietro" / ph).exists()
    assert "tok" not in (root / "logs" / "demo2" / "pietro" / "autopilot.log").read_text()
    calls.write_text("")
    assert Autopilot("pietro", "1-3", root=root, py=str(shim), claude=str(shim), git=str(shim),
                     sleep=lambda s: None).main() == 0
    assert "rebbi.demo2 run" not in calls.read_text()  # resumed: everything was done
    assert os.environ.get("REBBI_MACHINE") is None


def test_autopilot_eglis_waits_for_frozen_config_and_fixes(tmp_path):
    import stat
    import sys as _sys

    from rebbi.demo2.autopilot import Autopilot
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    (root / ".env").write_text('CLAUDE_CODE_OAUTH_TOKEN="tok"\n')
    calls, flag = tmp_path / "calls.txt", tmp_path / "pulled"
    fake = tmp_path / "fake.py"
    fake.write_text(f"""import sys, pathlib
args = sys.argv[1:]
open({str(calls)!r}, 'a').write(' '.join(args) + '\\n')
if args[:1] == ['-p']:
    print('ready')
if args[:1] == ['pull']:
    n = pathlib.Path({str(flag)!r})
    if n.exists():
        pathlib.Path('config/demo2.toml').write_text('frozen = true\\n')
    n.write_text('1')
if args[:3] == ['-m', 'rebbi.demo2', 'rehearsal'] and not pathlib.Path('fixed').exists():
    pathlib.Path('fixed').write_text('1')
    sys.exit(1)
""")
    shim = _make_shim(tmp_path, fake)
    slept = []
    ap = Autopilot("eglis", "4-6", lanes=1, root=root, py=str(shim), claude=str(shim), git=str(shim),
                   sleep=slept.append, poll_s=0)
    assert ap.main() == 0
    log = calls.read_text()
    assert log.count("pull --ff-only origin demo-v2") == 2 and 600 in slept  # waited once for the frozen config
    assert "rebbi.demo2 prepare" not in log and "push origin HEAD:demo-v2-eglis" in log
    assert "rebbi.demo2 run --repeats 4-6" in log and ap.fixes == 1  # the failed rehearsal got one fix session


def test_run_failing_on_output_token_cap_is_excluded(tmp_path, monkeypatch):
    err = "coder failed: None API Error: Claude's response exceeded the 3000 output token maximum."
    ctx = runner.make_ctx(rehearsal=True, base=tmp_path / "b", backend=ScriptedBackend())
    monkeypatch.setattr(runner, "load_config", lambda c: {"frozen": True, "calibration": {}})
    done = {"s1-r1", "s2-r1", "s3-r1", "s3b-r1", "s4-r1"}
    for rid in done:
        (ctx.base / rid).mkdir(parents=True)
        (ctx.base / rid / "summary.json").write_text("{}")

    async def boom(c, run_id, sc, ex, rep):
        raise RuntimeError(err)

    monkeypatch.setattr(runner, "run_scenario", boom)
    assert runner.lane(ctx, [1], sleep=lambda s: None) == 0  # not 4: excluded counts as finished
    st = runner.status(ctx, "s3onB-r1")
    assert st["state"] == "excluded" and st["attempts"] == 3 and "3000 output token" in st["error"]
    for rid in done:
        (ctx.base / rid / "summary.json").write_text(json.dumps({"windows_to_summit": 1, "windows": 1, "tokens_expired": 0, "interruptions": 0}))
    assert "excluded" in runner.status_text(ctx, [1])

    # other errors still end as failed (exit 4)
    runner.set_status(ctx, "s3onB-r1", state="pending", attempts=0, error="")

    async def other(c, run_id, sc, ex, rep):
        raise RuntimeError("something else")

    monkeypatch.setattr(runner, "run_scenario", other)
    assert runner.lane(ctx, [1], sleep=lambda s: None) == 4


def test_report_counts_completed_repeats_and_lists_excluded():
    def run(i, w):
        return {"sc": "s3onB", "done": w, "tot": {"expired": 10, "issued": 100, "blocks": i, "moved": 0}}

    ex = [{"run_id": "s3onB-r2", "error": "boom", "machine": "pietro"}]
    agg = report.aggregate([run(1, 10), run(3, 20)], 60, ex)["s3onB"]
    assert agg["n"] == 2 and agg["windows"] == [10, 20] and agg["median_windows"] == 15
    assert agg["excluded"] == ["s3onB-r2"]
