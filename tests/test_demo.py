import asyncio
import json
from datetime import datetime, timedelta

import pytest

from rebbi.demo import hill, report, runner
from rebbi.demo.backend import PlanLimit, ScriptedBackend, classify_external, extract_code, parse_shareable
from rebbi.demo.market import RATE, Market, reserve_for
from rebbi.demo.team import ROLES, RunConfig, Team, calibration_numbers, flat_hill, summarize

SQUARE = ([[0.25, 0.25], [0.75, 0.75]], [0.2, 0.2])


def code_returning(centers, radii, n=2):
    return f"import numpy as np\nN = {n}\ndef pack():\n    return np.array({centers}), np.array({radii})\n"


# -- evaluator ------------------------------------------------------------------------------------------

def test_start_solve_is_valid_and_scores_between_0_8_and_1_2():
    for n in (26, 32):
        e = hill.evaluate(hill.start_solve(n), n)
        assert e.valid and 0.8 <= e.score <= 1.2


def test_valid_packing_scores_the_sum_of_radii():
    e = hill.evaluate(code_returning(*SQUARE), 2)
    assert e.valid and e.score == pytest.approx(0.4)


def test_overlap_is_zero_with_reason():
    e = hill.evaluate(code_returning([[0.5, 0.5], [0.55, 0.5]], [0.2, 0.2]), 2)
    assert (e.score, e.valid) == (0.0, False) and "overlap" in e.reason


def test_circle_outside_the_square_is_zero():
    e = hill.evaluate(code_returning([[0.05, 0.5], [0.75, 0.75]], [0.2, 0.1]), 2)
    assert e.score == 0.0 and "sticks out" in e.reason


def test_wrong_shape_is_zero():
    e = hill.evaluate(code_returning([[0.5, 0.5]], [0.2]), 2)
    assert e.score == 0.0 and "shape" in e.reason


def test_tolerance_is_one_e_minus_9():
    assert hill.evaluate(code_returning([[0.25, 0.5], [0.75, 0.5]], [0.25, 0.25]), 2).valid
    assert not hill.evaluate(code_returning([[0.25, 0.5], [0.7499, 0.5]], [0.25, 0.25]), 2).valid


def test_forbidden_import_and_scipy_flag():
    assert "forbidden import: requests" in hill.evaluate("import requests\n" + code_returning(*SQUARE), 2).reason
    code = "from scipy import optimize\n" + code_returning(*SQUARE)
    assert hill.evaluate(code, 2).valid
    assert "forbidden import: scipy" in hill.evaluate(code, 2, forbid_scipy=True).reason


def test_timeout_is_zero():
    e = hill.evaluate("import time\nN = 2\ndef pack():\n    time.sleep(30)\n", 2, time_limit=1.5)
    assert e.score == 0.0 and "timeout" in e.reason


def test_crash_and_nonfinite_are_zero():
    assert "crashed" in hill.evaluate("N = 2\ndef pack():\n    raise ValueError('x')\n", 2).reason
    nan = code_returning([[0.25, 0.25], [0.5, 0.5]], [0.2, 0.2]).replace("0.5, 0.5", "float('nan'), 0.5")
    assert "non-finite" in hill.evaluate(nan, 2).reason


# -- calibration, reserve, market -------------------------------------------------------------------------

def windows(used_by_window, best):
    return [{"window": i + 1, "team": {"tokens_used": u, "best_score": b},
             "agents": {r: {"used": u // 5} for r in ROLES}} for i, (u, b) in enumerate(zip(used_by_window, best))]


def test_calibration_arithmetic():
    ws = windows([100_400, 120_600, 99_000, 101_000, 110_000, 90_000, 95_000, 105_000, 1, 2],
                 [1, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3])
    n = calibration_numbers(ws)
    assert n["T"] == 100_000  # median of the ten is 99,700, rounded to the nearest 1,000
    assert n["summit_A"] == 2.1 and n["score_w2"] == 1.5
    assert n["summit_B"] == pytest.approx(2.1 * 2.937 / 2.635)
    assert not flat_hill(ws)
    assert flat_hill(windows([1] * 10, [2.0, 2.05, 2.05, 2.05, 2.05, 2.05, 2.05, 2.05, 2.05, 2.05]))


def test_shareable_percent_becomes_reserve():
    assert reserve_for(10_000, 35) == 6_500
    assert reserve_for(10_000, 0) == 10_000
    assert reserve_for(10_000, 100) == 0


def test_market_claims():
    m = Market({"a": 1000, "b": 2000})
    m.settle("a", "b", 400)
    assert m.claims["a"] == pytest.approx(400 * RATE) and m.claims["b"] == -400
    assert m.borrow_limit("b", 50, 0) == 1600  # debt limit: one window of its own budget, less the debt
    assert m.borrow_limit("b", 50, 100) == 1500
    assert m.borrow_limit("b", 0, 0) == 0  # at 0% an agent cannot borrow
    assert m.borrow_limit("a", 50, 0) == int(400 * RATE + 1000)


def test_plan_limit_classification():
    for text in ("You have hit your usage limit", "429 rate limit", "API overloaded", "authentication_error"):
        assert classify_external(text)
    assert classify_external("x", 429) and classify_external(None, 401)
    assert not classify_external("budget too low") and not classify_external("syntax error", 500)


def test_parsers():
    assert extract_code("hi\n```python\nx = 1\n```\n") == "x = 1\n"
    assert extract_code("no code") is None
    assert parse_shareable("ok. SHAREABLE: 35%") == 35 and parse_shareable("none") is None


# -- team runs and the ledger -------------------------------------------------------------------------------

def run_team(tmp_path, **kw):
    cfg = RunConfig(**{"run_id": "t", "scenario": "3", "exercise": "A", "repeat": 1,
                       "models": {r: "m" for r in ROLES}, "budgets": {r: 12_000 for r in ROLES}, "T": 60_000,
                       "shareable_pct": {r: 60 for r in ROLES}, "rebbi": True, "max_windows": 5, **kw})
    team = Team(cfg, ScriptedBackend(), tmp_path / cfg.run_id)
    return cfg, asyncio.run(team.run())


@pytest.mark.parametrize("extra", [{}, {"market": True, "shareable_pct": {}}, {"rebbi": False}])
def test_ledger_invariants_hold_after_a_multi_agent_run(tmp_path, extra):
    cfg, res = run_team(tmp_path, **extra)
    assert res.ledger_problems == []
    assert (tmp_path / "t" / "ledger_check.txt").read_text().startswith("PASS")
    assert len(res.windows) == 5
    summary = summarize(cfg, res, datetime.now(), datetime.now())
    assert summary["tokens_expired"] >= 0 and summary["ledger_check"] == "PASS"
    if cfg.rebbi:
        assert summary["loans_count"] > 0
    else:
        assert summary["loans_count"] == 0


def test_budgets_bind_without_rebbi_and_lenders_keep_their_reserve_with_it(tmp_path):
    _, res = run_team(tmp_path, rebbi=False, budgets={r: 6_000 for r in ROLES})
    assert any(e["kind"] == "interruption" for e in res.events)
    _, res = run_team(tmp_path / "b", shareable_pct={r: 100 for r in ROLES})
    loans = [e for e in res.events if e["kind"] == "loan" and e["decision"] == "LEND"]
    assert loans and res.ledger_problems == []


# -- manifest, atomic finish, run-all --------------------------------------------------------------------------

def ctx_for(tmp_path, backend=None, repeats=1):
    base = tmp_path / "runs"
    return runner.Ctx(base, base / "demo.toml", tmp_path / "state", tmp_path / "results.html",
                      backend or ScriptedBackend(), True, repeats)


def test_manifest_is_created_and_a_running_row_is_reset(tmp_path):
    ctx = ctx_for(tmp_path)
    rows = runner.ensure_manifest(ctx)
    assert [r["run_id"] for r in rows] == ["cal", "s1-r1", "s2-r1", "s3-r1", "s3onB-r1", "s3b-r1", "s4-r1"]
    assert {r["status"] for r in rows} == {"pending"}
    runner.set_status(ctx, "cal", "running")
    runner.set_status(ctx, "s1-r1", "complete")
    rows = runner.ensure_manifest(ctx)  # a new process starts: the run it left `running` is pending again
    assert [r["status"] for r in rows[:2]] == ["pending", "complete"]
    assert runner.next_pending(rows)["run_id"] == "cal"
    runner.set_status(ctx, "cal", "aborted_external", "429")
    assert runner.next_pending(runner.read_manifest(ctx))["run_id"] == "cal"  # retried from scratch
    runner.set_status(ctx, "cal", "complete")
    assert runner.next_pending(runner.read_manifest(ctx))["run_id"] == "s2-r1"


class LimitBackend:
    scripted = True

    async def turn(self, *a, **k):
        raise PlanLimit("You have hit your usage limit")


def test_plan_limit_exits_3_and_marks_the_run_aborted_external(tmp_path):
    ctx = ctx_for(tmp_path, LimitBackend())
    assert runner.run_all(ctx, None) == 3
    row = runner.read_manifest(ctx)[0]
    assert (row["run_id"], row["status"]) == ("cal", "aborted_external") and "usage limit" in row["error"]
    assert not (ctx.base / "cal").exists() and not (ctx.base / "results.csv").exists()


def test_a_crash_leaves_only_a_partial_folder_that_a_retry_deletes(tmp_path):
    ctx = ctx_for(tmp_path, LimitBackend())
    runner.run_all(ctx, None)
    ctx.backend = ScriptedBackend()
    assert runner.run_all(ctx, None) == 0
    assert not list(ctx.base.glob("*.partial")) and (ctx.base / "cal" / "summary.json").exists()


def test_stop_time_in_the_past_starts_nothing_and_exits_0(tmp_path):
    ctx = ctx_for(tmp_path)
    assert runner.run_all(ctx, datetime.now() - timedelta(minutes=1)) == 0
    assert not (ctx.base / "cal").exists()


def test_full_pipeline_counts_only_complete_runs_and_builds_the_report(tmp_path):
    ctx = ctx_for(tmp_path)
    assert runner.run_all(ctx, None) == 0
    rows = report.read_results(ctx.base)
    assert [r["scenario"] for r in rows] == ["cal", "1", "2", "3", "3-on-B", "3b", "4"]
    assert all(r["status"] == "complete" and r["ledger_check"] == "PASS" for r in rows)
    data = json.loads((ctx.base / "artifact_data.json").read_text())
    assert len(data["runs"]) == 6 and data["calibration"]["scenario"] == "cal" and data["scripted"]
    assert data["setup"]["tokens_per_window_T"] % 1000 == 0
    html = ctx.report_path.read_text(encoding="utf-8")
    assert "<title>Rebbi Demo</title>" in html and "Shareable (% of budget)" in html and "https://" not in html
    assert (ctx.base / "table.md").exists()


def test_report_builds_from_a_tiny_artifact(tmp_path):
    data = {"title": "Rebbi Demo", "generated_at": "now", "scripted": False,
            "measured_on": "Claude Pro in subscription mode",
            "setup": {"models": [], "coder_model": None, "tokens_per_window_T": None,
                      "summit_exercise_A_score": None, "summit_exercise_B_score": None, "scipy_forbidden": False,
                      "windows_cap": 20, "roles": [{"id": r, "description": r} for r in ROLES],
                      "exercises": {k: {"circles": n, "published_best_known": hill.REFERENCE[k]}
                                    for k, n in hill.EXERCISES.items()}},
            "calibration": None, "runs": [], "results_table": []}
    out = tmp_path / "r.html"
    report.build_html(data, out)
    assert "not run" in out.read_text(encoding="utf-8")
