"""v2 runner: preflight, calibration, freeze (T, floors, summit, manager), the replay gate, and run lanes.

Every rule below is written in docs/demo2/DESIGN.md before any real run. State lives in files, so lanes
(separate processes) never write the same file:
  runs/demo2/<run_id>/summary.json   the run is complete (written last, after the ledger check)
  runs/demo2/<run_id>.partial/       a run in progress (deleted and rerun if the process dies)
  runs/demo2/_locks/<run_id>.lock    which lane owns a run; refreshed every window, stale after 30 minutes
  runs/demo2/_status/<run_id>.json   attempts and the last error
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import time
import tomllib
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any

from rebbi.demo.backend import Backend, PlanLimit, parse_json
from rebbi.demo2 import suite
from rebbi.demo2.backends import ReplayBackend, ScriptedBackend
from rebbi.demo2.team import HAIKU, MAX_WINDOWS, ROLE_TEXT, ROLES, RunConfig, Team, summarize

ROOT = Path(__file__).resolve().parent.parent.parent
DESIGN_VERSION = "v2.0"
CAL_BUDGET = 400_000  # per agent per window in calibration: never binds
CAL_WINDOWS = 15
SUMMIT_SHARE = 0.92  # summit = 92% of the calibration's final score, rounded down to 0.5
IDEAL_WINDOWS = 18  # T starts at calibration tokens / 18
GATE_MAX = 45  # replay: every scenario's median windows to summit must be <= 45 (cap 60)
GATE_MIN = 12  # replay: the fastest scenario's median must be >= 12 (the hill is not too short)
GATE_SEEDS = (1, 2, 3)
LIMIT_WAIT_S = 20 * 60
MAX_ATTEMPTS = 3
# A run whose three attempts all die on this error is left out (state "excluded"), not retried or treated as a cut-off.
EXCLUDE_MARKERS = ("exceeded the 3000 output token maximum",)
STALE_LOCK_S = 30 * 60
SCENARIOS = [("1", "A", "s1"), ("2", "A", "s2"), ("3", "A", "s3"), ("3-on-B", "B", "s3onB"), ("3b", "B", "s3b"),
             ("4", "A", "s4")]
NAMES = {"cal": "Calibration", "1": "Fixed equal budgets", "2": "Manager sets budgets", "3": "Manager + Rebbi",
         "3-on-B": "Scenario 3 setup on Exercise B", "3b": "Rebbi learns (Exercise B)", "4": "Open token market"}


@dataclass
class Ctx:
    base: Path
    config_path: Path
    backend: Backend
    rehearsal: bool = False
    exercises_root: Path = suite.EXERCISES

    def ex(self, name: str) -> list[suite.Exercise]:
        return suite.load_set(name, self.exercises_root)


def make_ctx(rehearsal: bool = False, root: Path = ROOT, backend: Backend | None = None, base: Path | None = None) -> Ctx:
    if rehearsal:
        b = base or root / "runs" / "demo2-rehearsal"
        return Ctx(b, b / "demo2.toml", backend or ScriptedBackend(), True)
    return Ctx(base or root / "runs" / "demo2", root / "config" / "demo2.toml", backend or real_backend(root))


def real_backend(root: Path) -> Backend:
    from rebbi import fleet
    from rebbi.demo.backend import SdkBackend
    token = fleet.oauth_token(root / ".env")
    if not token:
        raise SystemExit("CLAUDE_CODE_OAUTH_TOKEN is missing (environment or .env)")
    fleet.isolate_from_host()
    # One config folder per process: parallel lanes must not share Claude Code's state files.
    return SdkBackend(token, root / "runs" / "demo2-claude-config" / str(os.getpid()),
                      {"CLAUDE_CODE_MAX_OUTPUT_TOKENS": "3000"})


# -- config -----------------------------------------------------------------------------------------------

def load_config(ctx: Ctx) -> dict[str, Any]:
    return tomllib.loads(ctx.config_path.read_text(encoding="utf-8")) if ctx.config_path.exists() else {}


def save_config(ctx: Ctx, conf: dict[str, Any]) -> None:
    from rebbi.demo.runner import dump_toml
    ctx.config_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = ctx.config_path.with_suffix(".tmp")
    tmp.write_text("# Written by python -m rebbi.demo2 prepare. Frozen: every machine runs with these numbers.\n"
                   + dump_toml(conf), encoding="utf-8")
    tmp.replace(ctx.config_path)


def write_json(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")
    tmp.replace(path)


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT,
                              timeout=10).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


# -- budgets ----------------------------------------------------------------------------------------------

def ceil_to(x: float, step: int) -> int:
    return int(math.ceil(x / step) * step)


def equal_split(T: int) -> dict[str, int]:
    out = {r: T // len(ROLES) for r in ROLES}
    out["coder"] += T - sum(out.values())
    return out


def budgets_from_pct(pct: dict[str, float], T: int, floors: dict[str, int]) -> dict[str, int]:
    """Shares of T, then every role raised to its floor (its largest calibration call x 1.1); the excess is
    taken from the roles above their floors in proportion to what they have above it."""
    vals = {r: max(float(pct.get(r, 0) or 0), 0.0) for r in ROLES}
    tot = sum(vals.values()) or 1.0
    b = {r: T * vals[r] / tot for r in ROLES}
    for _ in range(10):
        low = [r for r in ROLES if b[r] < floors.get(r, 0)]
        if not low:
            break
        need = sum(floors[r] - b[r] for r in low)
        for r in low:
            b[r] = floors[r]
        room = {r: b[r] - floors.get(r, 0) for r in ROLES if r not in low and b[r] > floors.get(r, 0)}
        rt = sum(room.values())
        if rt <= 0:
            break
        for r, v in room.items():
            b[r] -= need * v / rt
    out = {r: int(b[r]) for r in ROLES}
    out[max(out, key=out.get)] += T - sum(out.values())
    return out


def clamp_pct(raw: dict) -> dict[str, float]:
    return {r: float(min(100, max(0, (raw or {}).get(r, 0) or 0))) for r in ROLES}


class CountGate:
    def __init__(self) -> None:
        self.tokens = 0

    def before(self, input_tokens: int) -> bool:
        return True

    def after(self, total_tokens: int, note: str) -> None:
        self.tokens += total_tokens


async def ask_manager(ctx: Ctx, kind: str, T: int, extra: str = "") -> tuple[dict[str, Any], int]:
    roles = "\n".join(f"- {r}: {t}" for r, t in ROLE_TEXT.items())
    head = (f"You are the manager of a team of five AI agents. TOTAL={T} tokens are issued to the team every budget "
            "window; unused tokens expire at the end of the window. The team ships 55 small Python exercises through a "
            "pipeline: the Researcher writes notes, the Coder writes the code, the Evaluator reports the test run, the "
            "Reviewer approves or rewrites. Work handed on reaches the next role at the next window.\n"
            f"Roles:\n{roles}\n{extra}")
    ask = {"budgets": 'Reply with one JSON object only: {"budget_pct": {"planner": n, "researcher": n, "coder": n, '
                      '"evaluator": n, "reviewer": n}} giving each role\'s percentage of TOTAL (adding up to 100).',
           "shareable": 'Reply with one JSON object only: {"shareable_pct": {"planner": 0-100, ...}} for the five roles: '
                        "the share of each agent's budget other agents may borrow when they run short.",
           "learned": 'Reply with one JSON object only: {"budget_pct": {...}, "shareable_pct": {...}} for the five roles: '
                      "new percentages of TOTAL (adding up to 100) and each agent's shareable % (0-100)."}[kind]
    gate = CountGate()
    key = "shareable_pct" if kind == "shareable" else "budget_pct"
    for _ in range(2):
        out = await ctx.backend.turn("manager", HAIKU, "You split a token budget between agents.", head + ask, gate, 0)
        data = parse_json(out.text)
        if data and key in data:
            return data, gate.tokens
    return {}, gate.tokens


# -- run folders, locks, status -------------------------------------------------------------------------

def run_ids(repeats: list[int]) -> list[tuple[str, str, str, int]]:
    return [(f"{slug}-r{rep}", sc, ex, rep) for rep in repeats for sc, ex, slug in SCENARIOS]


def excluded(ctx: Ctx, run_id: str) -> bool:
    return status(ctx, run_id).get("state") == "excluded"


def finished(ctx: Ctx, run_id: str) -> bool:
    """Complete or excluded: nothing more to run."""
    return complete(ctx, run_id) or excluded(ctx, run_id)


def complete(ctx: Ctx, run_id: str) -> bool:
    return (ctx.base / run_id / "summary.json").exists()


def status(ctx: Ctx, run_id: str) -> dict[str, Any]:
    p = ctx.base / "_status" / f"{run_id}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"attempts": 0, "state": "pending"}


def set_status(ctx: Ctx, run_id: str, **kw: Any) -> None:
    d = ctx.base / "_status"
    d.mkdir(parents=True, exist_ok=True)
    write_json(d / f"{run_id}.json", {**status(ctx, run_id), **kw, "updated_at": datetime.now().isoformat(timespec="seconds")})


def lock(ctx: Ctx, run_id: str) -> bool:
    d = ctx.base / "_locks"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{run_id}.lock"
    if p.exists() and time.time() - p.stat().st_mtime > STALE_LOCK_S:
        p.unlink(missing_ok=True)
    try:
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    os.write(fd, f"{os.getpid()} {datetime.now().isoformat(timespec='seconds')}".encode())
    os.close(fd)
    return True


def touch_lock(ctx: Ctx, run_id: str) -> None:
    p = ctx.base / "_locks" / f"{run_id}.lock"
    if p.exists():
        os.utime(p, None)


def unlock(ctx: Ctx, run_id: str) -> None:
    (ctx.base / "_locks" / f"{run_id}.lock").unlink(missing_ok=True)


# -- executing one run -----------------------------------------------------------------------------------

async def execute(ctx: Ctx, cfg: RunConfig, backend: Backend | None = None, on_window=None) -> dict[str, Any]:
    """Run into <id>.partial, check the ledger, then rename to <id> and write summary.json last."""
    partial = ctx.base / f"{cfg.run_id}.partial"
    if partial.exists():
        shutil.rmtree(partial)
    partial.mkdir(parents=True)
    be = backend or ctx.backend
    write_json(partial / "config.json", {**asdict(cfg), "design": DESIGN_VERSION, "commit": git_commit(),
                                         "scripted": bool(getattr(be, "scripted", False)),
                                         "machine": os.environ.get("REBBI_MACHINE", "pietro")})
    started = datetime.now()
    team = Team(cfg, be, partial, ctx.ex(cfg.exercise))
    if on_window:
        orig = team.run_window

        async def hooked():
            row = await orig()
            on_window(row)
            return row
        team.run_window = hooked  # type: ignore[method-assign]
    try:
        res = await team.run()
    finally:
        team.ledger.close()  # an open database blocks deleting the folder on Windows
    summary = summarize(cfg, res, started, datetime.now())
    summary["machine"] = os.environ.get("REBBI_MACHINE", "pietro")
    if summary["ledger_check"] != "PASS":
        raise RuntimeError("ledger check failed: " + "; ".join(res.ledger_problems)[:300])
    final = ctx.base / cfg.run_id
    if final.exists():
        shutil.rmtree(final)
    partial.rename(final)
    write_json(final / "summary.json", summary)
    return summary


def backend_for(ctx: Ctx, tag: str) -> Backend:
    """A copy of the backend with its own Claude config folder, for teams that run at the same time."""
    import copy
    be = ctx.backend
    if hasattr(be, "config_dir"):
        be = copy.copy(be)
        be.config_dir = be.config_dir / tag
        be.config_dir.mkdir(parents=True, exist_ok=True)
    return be


# -- calibration, freeze, gate ------------------------------------------------------------------------

def cal_config(ex: str) -> RunConfig:
    return RunConfig(f"cal-{ex}", "cal", ex, 0, {r: CAL_BUDGET for r in ROLES}, CAL_BUDGET * 5,
                     max_windows=CAL_WINDOWS, summit=None)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def cal_data(ctx: Ctx, ex: str) -> tuple[list[dict], list[dict], dict]:
    d = ctx.base / f"cal-{ex}"
    calls = read_jsonl(d / "calls.jsonl")
    tests = [e for e in read_jsonl(d / "events.jsonl") if e["kind"] == "tests"]
    return calls, tests, json.loads((d / "summary.json").read_text(encoding="utf-8"))


def numbers_from_calibration(ctx: Ctx) -> dict[str, Any]:
    calls = {ex: cal_data(ctx, ex)[0] for ex in ("A", "B")}
    sums = {ex: cal_data(ctx, ex)[2] for ex in ("A", "B")}
    pooled = [c for ex in ("A", "B") for c in calls[ex] if not c["stopped"]]
    floors = {r: max(1500, ceil_to(1.1 * max([c["total"] for c in pooled if c["role"] == r] or [1500]), 500))
              for r in ROLES}
    prior = {}
    for c in pooled:
        prior.setdefault(f"{c['role']}_{c['kind']}", []).append(c["total"])
    prior = {k: int(statistics.median(v)) for k, v in prior.items()}
    total_A = sum(c["total"] for c in calls["A"])
    T = max(5 * max(floors.values()), ceil_to(total_A / IDEAL_WINDOWS, 1000))
    summit = {ex: math.floor(SUMMIT_SHARE * sums[ex]["final_score"] * 2) / 2 for ex in ("A", "B")}
    return {"T": T, "floors": floors, "cost_prior": prior, "summit_A": summit["A"], "summit_B": summit["B"],
            "cal_score_A": sums["A"]["final_score"], "cal_score_B": sums["B"]["final_score"],
            "cal_tokens_A": total_A, "cal_tokens_B": sum(c["total"] for c in calls["B"])}


def scenario_config(conf: dict[str, Any], run_id: str, sc: str, ex: str, rep: int,
                    learned: dict[str, Any] | None = None) -> RunConfig:
    c = conf["calibration"]
    T, floors = int(c["T"]), {r: int(v) for r, v in conf["floors"].items()}
    base = dict(run_id=run_id, scenario=sc, exercise=ex, repeat=rep, T=T, summit=float(c[f"summit_{ex}"]),
                cost_prior={k: int(v) for k, v in conf.get("cost_prior", {}).items()})
    mgr = conf["manager"]
    budgets = budgets_from_pct(mgr["budget_pct"], T, floors)
    if sc == "1":
        return RunConfig(**base, budgets=equal_split(T))
    if sc == "2":
        return RunConfig(**base, budgets=budgets)
    if sc in ("3", "3-on-B"):
        return RunConfig(**base, budgets=budgets, shareable_pct=clamp_pct(mgr["shareable_pct"]), rebbi=True)
    if sc == "4":
        return RunConfig(**base, budgets=budgets, rebbi=True, market=True)
    if sc == "3b":
        lr = learned or {}
        return RunConfig(**base, budgets=budgets_from_pct(lr.get("budget_pct", mgr["budget_pct"]), T, floors),
                         shareable_pct=clamp_pct(lr.get("shareable_pct", mgr["shareable_pct"])), rebbi=True,
                         settings={"learned": lr})
    raise ValueError(sc)


def usage_text(run_dir: Path) -> str:
    rows = read_jsonl(run_dir / "windows.jsonl")
    lines = []
    for r in ROLES:
        demand = [w["agents"][r]["used"] + w["agents"][r]["unmet"] for w in rows]
        lines.append(f"- {r}: budget {rows[0]['agents'][r]['budget']}; demand per window (used + work left waiting) "
                     f"mean {statistics.mean(demand):.0f}, min {min(demand)}, max {max(demand)}; expired in total "
                     f"{sum(w['agents'][r]['expired'] for w in rows)}; lent {sum(w['agents'][r]['lent'] for w in rows)}; "
                     f"borrowed {sum(w['agents'][r]['borrowed'] for w in rows)}; windows with work left waiting "
                     f"{sum(1 for w in rows if w['agents'][r]['interrupted'])} of {len(rows)}")
    return "\n".join(lines)


def heuristic_learned(run_dir: Path) -> dict[str, Any]:
    """Replay stand-in for the 3b manager: budgets in proportion to measured demand, shareable 30%."""
    rows = read_jsonl(run_dir / "windows.jsonl")
    dem = {r: sum(w["agents"][r]["used"] + w["agents"][r]["unmet"] for w in rows) for r in ROLES}
    tot = sum(dem.values()) or 1
    return {"budget_pct": {r: 100 * v / tot for r, v in dem.items()}, "shareable_pct": {r: 30 for r in ROLES}}


async def replay_gate(ctx: Ctx, conf: dict[str, Any]) -> dict[str, Any]:
    """Zero-usage check of the frozen numbers: every scenario replayed with calibration costs and results."""
    data = {ex: cal_data(ctx, ex) for ex in ("A", "B")}
    gate_base = ctx.base / "_gate"
    results: dict[str, list[int]] = {}
    for seed in GATE_SEEDS:
        gctx = Ctx(gate_base / f"seed{seed}", ctx.config_path, ctx.backend, True, ctx.exercises_root)
        if gctx.base.exists():
            shutil.rmtree(gctx.base)
        for sc, ex, slug in SCENARIOS:
            learned = heuristic_learned(gctx.base / "s3-r1") if sc == "3b" else None
            cfg = replace(scenario_config(conf, f"{slug}-r1", sc, ex, 1, learned), replay=True)
            be = ReplayBackend(data[ex][0], data[ex][1], seed=seed * 101 + len(slug))
            s = await execute(gctx, cfg, be)
            w = s["windows_to_summit"]
            results.setdefault(slug, []).append(w if isinstance(w, int) else MAX_WINDOWS + 1)
    med = {k: statistics.median(v) for k, v in results.items()}
    return {"median_windows": med, "all": results, "ok_max": max(med.values()) <= GATE_MAX,
            "ok_min": min(med.values()) >= GATE_MIN}


async def prepare(ctx: Ctx) -> dict[str, Any]:
    """Calibrate A and B (in parallel), set T, floors and summits, ask the manager, pass the gate, freeze."""
    conf = load_config(ctx)
    if conf.get("frozen"):
        print("config already frozen:", ctx.config_path)
        return conf
    todo = [ex for ex in ("A", "B") if not complete(ctx, f"cal-{ex}")]
    if todo:
        await asyncio.gather(*(execute(ctx, cal_config(ex), backend_for(ctx, f"cal-{ex}")) for ex in todo))
    nums = numbers_from_calibration(ctx)
    notes = []
    for ex in ("A", "B"):
        if nums[f"cal_score_{ex}"] < 60:
            raise RuntimeError(f"calibration on {ex} reached only {nums[f'cal_score_{ex}']:.1f}% of tests: the task is "
                               "too hard for the model as set up; stop and fix before any scenario runs")
    conf = {"design": DESIGN_VERSION, "model": HAIKU, "frozen": False,
            "calibration": {k: v for k, v in nums.items() if k not in ("floors", "cost_prior")},
            "floors": nums["floors"], "cost_prior": nums["cost_prior"]}
    if "manager" not in conf:
        data, toks = await ask_manager(ctx, "budgets", nums["T"])
        share, toks2 = await ask_manager(ctx, "shareable", nums["T"])
        conf["manager"] = {"budget_pct": clamp_pct(data.get("budget_pct", {r: 20 for r in ROLES})),
                           "shareable_pct": clamp_pct(share.get("shareable_pct", {r: 20 for r in ROLES})),
                           "fallback": not data or not share, "manager_tokens": toks + toks2}
    T = nums["T"]
    min_T = 5 * max(nums["floors"].values())
    gate: dict[str, Any] = {}
    for i in range(8):
        conf["calibration"]["T"] = T
        gate = await replay_gate(ctx, conf)
        notes.append(f"gate try {i + 1}: T={T} medians={gate['median_windows']}")
        print(notes[-1], flush=True)
        if gate["ok_max"] and gate["ok_min"]:
            break
        if not gate["ok_max"]:
            T = ceil_to(T * 1.15, 1000)
        elif T * 0.87 >= min_T:
            T = max(min_T, ceil_to(T * 0.87, 1000))
        else:
            notes.append("hill shorter than the gate minimum at the smallest T the floors allow; kept")
            break
    conf["calibration"]["T"] = T
    conf["gate"] = {"median_windows": gate["median_windows"], "ok_max": gate["ok_max"], "ok_min": gate["ok_min"],
                    "notes": notes}
    if not gate["ok_max"]:
        save_config(ctx, conf)
        raise RuntimeError("replay gate failed: some scenario needs more than 45 windows even after raising T")
    conf["frozen"] = True
    conf["frozen_at"] = datetime.now().isoformat(timespec="seconds")
    save_config(ctx, conf)
    return conf


# -- lanes ---------------------------------------------------------------------------------------------

async def run_scenario(ctx: Ctx, run_id: str, sc: str, ex: str, rep: int) -> dict[str, Any]:
    conf = load_config(ctx)
    learned = None
    if sc == "3b":
        lp = ctx.base / f"_learned-r{rep}.json"
        if lp.exists():
            learned = json.loads(lp.read_text(encoding="utf-8"))
        else:
            T = int(conf["calibration"]["T"])
            data, toks = await ask_manager(ctx, "learned", T, "Usage per role in the same pipeline on a sibling set of "
                                           f"exercises (scenario 3):\n{usage_text(ctx.base / f's3-r{rep}')}\n")
            learned = {"budget_pct": clamp_pct(data.get("budget_pct", conf["manager"]["budget_pct"])),
                       "shareable_pct": clamp_pct(data.get("shareable_pct", conf["manager"]["shareable_pct"])),
                       "fallback": not data, "manager_tokens": toks}
            write_json(lp, learned)
    cfg = scenario_config(conf, run_id, sc, ex, rep, learned)
    return await execute(ctx, cfg, on_window=lambda row: touch_lock(ctx, run_id))


def next_run(ctx: Ctx, repeats: list[int]) -> tuple[str, str, str, int] | None:
    for run_id, sc, ex, rep in run_ids(repeats):
        if finished(ctx, run_id) or status(ctx, run_id).get("state") == "failed":
            continue
        if sc == "3b" and excluded(ctx, f"s3-r{rep}"):
            set_status(ctx, run_id, state="excluded", error=f"scenario 3 repeat {rep} was excluded; 3b needs its usage summary")
            continue
        if sc == "3b" and not complete(ctx, f"s3-r{rep}"):
            continue
        if lock(ctx, run_id):
            return run_id, sc, ex, rep
    return None


def lane(ctx: Ctx, repeats: list[int], stop_at: datetime | None = None, sleep=time.sleep) -> int:
    """Run pending runs until none is left. 0: done. 4: some run failed three times (needs a fix)."""
    conf = load_config(ctx)
    if not conf.get("frozen"):
        print("config/demo2.toml is not frozen yet: run prepare first (or pull it)", flush=True)
        return 5
    while True:
        if stop_at and datetime.now() > stop_at:
            print("lane: stop time passed", flush=True)
            return 0
        pick = next_run(ctx, repeats)
        if pick is None:
            waiting = [r for r, sc, ex, rep in run_ids(repeats) if not finished(ctx, r)
                       and status(ctx, r).get("state") != "failed"]
            if waiting and any((ctx.base / "_locks" / f"{r}.lock").exists() for r in waiting):
                sleep(60)  # another lane holds a run this lane may depend on (3b waits for 3)
                continue
            failed = [r for r, *_ in run_ids(repeats) if status(ctx, r).get("state") == "failed"]
            print(f"lane: nothing left; failed: {failed or 'none'}", flush=True)
            return 4 if failed else 0
        run_id, sc, ex, rep = pick
        st = status(ctx, run_id)
        set_status(ctx, run_id, state="running", attempts=st.get("attempts", 0) + 1, pid=os.getpid())
        print(f"lane {os.getpid()}: starting {run_id}", flush=True)
        try:
            s = asyncio.run(run_scenario(ctx, run_id, sc, ex, rep))
            set_status(ctx, run_id, state="complete", error="")
            print(f"lane: {run_id} complete, windows to summit {s['windows_to_summit']}", flush=True)
        except PlanLimit as e:
            set_status(ctx, run_id, state="pending", attempts=st.get("attempts", 0), error=f"plan limit: {e}"[:400])
            print(f"lane: plan limit on {run_id}; waiting {LIMIT_WAIT_S // 60} min", flush=True)
            unlock(ctx, run_id)
            sleep(LIMIT_WAIT_S)
            continue
        except Exception as e:  # noqa: BLE001
            att = st.get("attempts", 0) + 1
            last = "excluded" if any(m in str(e) for m in EXCLUDE_MARKERS) else "failed"
            set_status(ctx, run_id, state=last if att >= MAX_ATTEMPTS else "pending", error=repr(e)[:600])
            print(f"lane: {run_id} failed (attempt {att}): {e!r}", flush=True)
            if att >= MAX_ATTEMPTS and last == "excluded":
                print(f"lane: {run_id} excluded after {att} attempts", flush=True)
        finally:
            unlock(ctx, run_id)
            p = ctx.base / f"{run_id}.partial"
            if p.exists():
                shutil.rmtree(p, ignore_errors=True)


def status_text(ctx: Ctx, repeats: list[int]) -> str:
    conf = load_config(ctx)
    lines = [f"config frozen: {bool(conf.get('frozen'))}  T={conf.get('calibration', {}).get('T')}  "
             f"summit A={conf.get('calibration', {}).get('summit_A')} B={conf.get('calibration', {}).get('summit_B')}"]
    for ex in ("A", "B"):
        lines.append(f"  cal-{ex:<8} {'complete' if complete(ctx, f'cal-{ex}') else 'pending'}")
    for run_id, *_ in run_ids(repeats):
        if complete(ctx, run_id):
            s = json.loads((ctx.base / run_id / "summary.json").read_text(encoding="utf-8"))
            lines.append(f"  {run_id:<10} complete   summit at {s['windows_to_summit']}, windows {s['windows']}, "
                         f"expired {s['tokens_expired']}, interruptions {s['interruptions']}")
        elif excluded(ctx, run_id):
            lines.append(f"  {run_id:<10} excluded   {status(ctx, run_id).get('error', '')[:90]}")
        else:
            st = status(ctx, run_id)
            locked = (ctx.base / "_locks" / f"{run_id}.lock").exists()
            lines.append(f"  {run_id:<10} {('running' if locked else st.get('state', 'pending')):<10} "
                         f"attempts {st.get('attempts', 0)} {st.get('error', '')[:90]}")
    return "\n".join(lines)


def parse_repeats(text: str) -> list[int]:
    if "-" in text:
        a, b = text.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in text.split(",")]


_ = sys
