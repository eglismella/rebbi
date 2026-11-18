"""Manifest, calibration, manager calls, run-all, results files. Resumable and plan-limit safe."""

from __future__ import annotations

import asyncio
import csv
import json
import shutil
import statistics
import subprocess
import tomllib
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from rebbi.demo import hill
from rebbi.demo.backend import Backend, PlanLimit, ScriptedBackend, parse_json
from rebbi.demo.team import (HAIKU, ROLE_TEXT, ROLES, SONNET, RunConfig, Team, calibration_numbers, flat_hill,
                             summarize)

ROOT = Path(__file__).resolve().parent.parent.parent
T0 = 2_000_000  # calibration: each agent gets 5 x T0 tokens per window, too large to bind
SCENARIOS = [("1", "A", "s1"), ("2", "A", "s2"), ("3", "A", "s3"), ("3-on-B", "B", "s3onB"), ("3b", "B", "s3b"),
             ("4", "A", "s4")]
SCENARIO_NAMES = {"cal": "Calibration", "1": "Equal fixed budgets", "2": "Manager sets budgets",
                  "3": "Manager + Rebbi", "3-on-B": "Manager + Rebbi, Exercise B", "3b": "Rebbi learns (Exercise B)",
                  "4": "Open market"}
RESULT_COLUMNS = ["run_id", "scenario", "exercise", "repeat", "models", "T", "budgets", "shareable_pct",
                  "windows_to_summit", "best_score", "tokens_issued", "tokens_used", "tokens_expired",
                  "interruptions", "loans_count", "tokens_moved", "ledger_check", "status", "wall_seconds",
                  "started_at", "ended_at"]
MANIFEST_COLUMNS = ["run_id", "scenario", "exercise", "repeat", "status", "error", "updated_at"]
PENDING_STATES = ("pending", "running", "aborted_external", "failed")


@dataclass
class Ctx:
    base: Path  # runs/demo or runs/demo-rehearsal
    config_path: Path
    state_dir: Path
    report_path: Path
    backend: Backend
    rehearsal: bool = False
    repeats: int = 3

    @property
    def manifest(self) -> Path:
        return self.base / "manifest.csv"


def make_ctx(rehearsal: bool = False, root: Path = ROOT, backend: Backend | None = None, repeats: int | None = None) -> Ctx:
    if rehearsal:
        base = root / "runs" / "demo-rehearsal"
        return Ctx(base, base / "demo.toml", base / "state", base / "results.html", backend or ScriptedBackend(),
                   True, repeats or 1)
    return Ctx(root / "runs" / "demo", root / "config" / "demo.toml", root / "docs" / "demo" / "state",
               root / "docs" / "demo" / "results.html", backend or real_backend(root), False, repeats or 3)


def real_backend(root: Path) -> Backend:
    from rebbi import fleet
    from rebbi.demo.backend import SdkBackend
    token = fleet.oauth_token(root / ".env")
    if not token:
        raise SystemExit("CLAUDE_CODE_OAUTH_TOKEN is missing (environment or .env)")
    fleet.isolate_from_host()
    return SdkBackend(token, root / "runs" / "demo" / "claude-config")


# -- tiny TOML writer for the frozen config ---------------------------------------------------------------

def dump_toml(d: dict[str, Any], prefix: str = "") -> str:
    scalars = {k: v for k, v in d.items() if not isinstance(v, dict)}
    tables = {k: v for k, v in d.items() if isinstance(v, dict)}
    out = [f"[{prefix}]"] if prefix and scalars else []
    for k, v in scalars.items():
        out.append(f"{k} = {json.dumps(v)}")
    text = "\n".join(out) + ("\n\n" if out else "")
    for k, v in tables.items():
        text += dump_toml(v, f"{prefix}.{k}" if prefix else k)
    return text


def load_config(ctx: Ctx) -> dict[str, Any]:
    return tomllib.loads(ctx.config_path.read_text(encoding="utf-8")) if ctx.config_path.exists() else {}


def save_config(ctx: Ctx, cfg: dict[str, Any]) -> None:
    ctx.config_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = ctx.config_path.with_suffix(".tmp")
    tmp.write_text("# Written by python -m rebbi.demo: calibration and frozen manager outputs.\n" + dump_toml(cfg),
                   encoding="utf-8")
    tmp.replace(ctx.config_path)


# -- manifest -----------------------------------------------------------------------------------------------

def plan(repeats: int) -> list[dict[str, Any]]:
    rows = [{"run_id": "cal", "scenario": "cal", "exercise": "A", "repeat": 0}]
    for rep in range(1, repeats + 1):
        rows += [{"run_id": f"{slug}-r{rep}", "scenario": sc, "exercise": ex, "repeat": rep}
                 for sc, ex, slug in SCENARIOS]
    return rows


def now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_manifest(ctx: Ctx) -> list[dict[str, str]]:
    if not ctx.manifest.exists():
        return []
    with open(ctx.manifest, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_manifest(ctx: Ctx, rows: list[dict[str, Any]]) -> None:
    ctx.base.mkdir(parents=True, exist_ok=True)
    tmp = ctx.manifest.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, MANIFEST_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(ctx.manifest)


def ensure_manifest(ctx: Ctx) -> list[dict[str, str]]:
    """Load the manifest, add rows for planned runs it lacks, and reset a run a killed process left `running`."""
    rows = read_manifest(ctx)
    known = {r["run_id"] for r in rows}
    rows += [{**p, "status": "pending", "error": "", "updated_at": now_text()} for p in plan(ctx.repeats)
             if p["run_id"] not in known]
    for r in rows:
        if r["status"] == "running":
            r["status"] = "pending"
            r["error"] = "reset: the process that was running it ended"
    write_manifest(ctx, rows)
    return rows


def set_status(ctx: Ctx, run_id: str, status: str, error: str = "") -> None:
    rows = read_manifest(ctx)
    for r in rows:
        if r["run_id"] == run_id:
            r.update(status=status, error=error[:500], updated_at=now_text())
    write_manifest(ctx, rows)


def next_pending(rows: list[dict[str, str]]) -> dict[str, str] | None:
    """Repeat-major order is the order of the plan; a run is retried while it is pending, aborted or failed."""
    return next((r for r in rows if r["status"] in PENDING_STATES), None)


# -- manager ---------------------------------------------------------------------------------------------------

class CountGate:
    def __init__(self) -> None:
        self.tokens = 0

    def before(self, input_tokens: int) -> bool:
        return True

    def after(self, total_tokens: int, note: str) -> None:
        self.tokens += total_tokens


def normalize_budgets(raw: dict, T: int) -> dict[str, int]:
    """The manager's split, scaled to add up to exactly T; every role gets something."""
    vals = {r: max(float(raw.get(r, 0) or 0), 0.0) for r in ROLES}
    total = sum(vals.values())
    if total <= 0:
        vals, total = {r: 1.0 for r in ROLES}, float(len(ROLES))
    out = {r: max(1, int(T * v / total)) for r, v in vals.items()}
    out["coder"] += T - sum(out.values())
    return out


def clamp_pct(raw: dict) -> dict[str, float]:
    return {r: float(min(100, max(0, raw.get(r, 0) or 0))) for r in ROLES}


async def ask_manager(ctx: Ctx, kind: str, T: int, task: str, budgets: dict | None = None,
                      usage: str = "") -> tuple[dict[str, Any], int]:
    roles = "\n".join(f"- {r}: {t}" for r, t in ROLE_TEXT.items())
    head = f"You are the manager of a team of five AI agents. TOTAL={T} tokens are issued to the team every window.\n{task}\nRoles:\n{roles}\n"
    shape = ('Reply with one JSON object only: {"budgets": {"planner": int, "researcher": int, "coder": int, '
             '"evaluator": int, "reviewer": int}} with budgets that add up to TOTAL.')
    share = ('Reply with one JSON object only: {"shareable_pct": {"planner": 0-100, ...}} for the five roles: the share of '
             "each agent's budget that other agents may borrow when they run short.")
    both = ('Reply with one JSON object only: {"budgets": {...}, "shareable_pct": {...}} for the five roles: new budgets '
            "adding up to TOTAL, and each agent's shareable % (0-100) of its budget.")
    prompt = {"budgets": head + shape,
              "shareable": head + f"Budgets per window: {json.dumps(budgets)}\n" + share,
              "learned": head + f"Budgets last time: {json.dumps(budgets)}\nUsage per role from the previous experiment:\n"
                         f"{usage}\n" + both}[kind]
    gate = CountGate()
    for _ in range(2):
        out = await ctx.backend.turn("manager", HAIKU, "You split a token budget between agents.", prompt, gate, 0)
        data = parse_json(out.text)
        if data and (("budgets" in data) if kind != "shareable" else ("shareable_pct" in data)):
            return data, gate.tokens
    return {}, gate.tokens  # unusable twice: the caller falls back to an equal split and says so


# -- one run -----------------------------------------------------------------------------------------------------

def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT,
                              timeout=10).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def usage_text(run_dir: Path) -> str:
    rows = [json.loads(line) for line in (run_dir / "windows.jsonl").read_text(encoding="utf-8").splitlines()]
    lines = []
    for r in ROLES:
        used = [w["agents"][r]["used"] for w in rows]
        lines.append(f"- {r}: used per window mean {statistics.mean(used):.0f}, spread (stdev) "
                     f"{statistics.pstdev(used):.0f}; lent {sum(w['agents'][r]['lent'] for w in rows)}, borrowed "
                     f"{sum(w['agents'][r]['borrowed'] for w in rows)}, expired {sum(w['agents'][r]['expired'] for w in rows)} "
                     f"tokens in total; interruptions {sum(w['agents'][r]['interrupted'] for w in rows)}")
    return "\n".join(lines)


def models_for(conf: dict) -> dict[str, str]:
    return {r: (conf.get("coder_model", HAIKU) if r == "coder" else HAIKU) for r in ROLES}


async def build_config(ctx: Ctx, row: dict[str, str], conf: dict) -> RunConfig:
    """Settings for a run; asks the manager (and freezes the answer in config/demo.toml) when needed."""
    sc, ex, rep = row["scenario"], row["exercise"], int(row["repeat"])
    cal = conf.get("calibration", {})
    T = int(cal.get("T", 0))
    summit = cal["summit_A"] if ex == "A" else cal["summit_B"]
    base = dict(run_id=row["run_id"], scenario=sc, exercise=ex, repeat=rep, models=models_for(conf), T=T,
                summit=summit, forbid_scipy=bool(conf.get("forbid_scipy", False)))
    task = f"Task: pack circles in the unit square to maximize the sum of radii (n = {hill.EXERCISES[ex]})."
    equal = {r: T // len(ROLES) for r in ROLES}
    equal["coder"] += T - sum(equal.values())
    if sc == "1":
        return RunConfig(**base, budgets=equal)
    mgr = conf.setdefault("manager", {})
    if "budgets" not in mgr and sc in ("2", "3", "3-on-B", "4"):
        data, toks = await ask_manager(ctx, "budgets", T, task)
        mgr["budgets"] = normalize_budgets(data.get("budgets", {}), T)
        mgr["fallback_equal_split"] = not data
        mgr["manager_tokens"] = toks
        save_config(ctx, conf)
    budgets = mgr.get("budgets", equal)
    if sc == "2":
        return RunConfig(**base, budgets=budgets, settings={"manager": mgr})
    if sc in ("3", "3-on-B", "4") and "shareable_pct" not in mgr:
        data, toks = await ask_manager(ctx, "shareable", T, task, budgets)
        mgr["shareable_pct"] = clamp_pct(data.get("shareable_pct", {r: 20 for r in ROLES}))
        mgr["shareable_tokens"] = toks
        save_config(ctx, conf)
    if sc in ("3", "3-on-B"):
        return RunConfig(**base, budgets=budgets, shareable_pct=mgr["shareable_pct"], rebbi=True,
                         settings={"manager": mgr})
    if sc == "4":
        return RunConfig(**base, budgets=budgets, rebbi=True, market=True, settings={"manager": mgr})
    if sc == "3b":
        learned = conf.setdefault("learned", {}).setdefault(f"r{rep}", {})
        if "budgets" not in learned:
            s3 = ctx.base / f"s3-r{rep}"
            data, toks = await ask_manager(ctx, "learned", T, task, budgets, usage_text(s3))
            learned["budgets"] = normalize_budgets(data.get("budgets", {}), T)
            learned["shareable_pct"] = clamp_pct(data.get("shareable_pct", mgr["shareable_pct"]))
            learned["manager_tokens"] = toks
            save_config(ctx, conf)
        return RunConfig(**base, budgets=learned["budgets"], shareable_pct=learned["shareable_pct"], rebbi=True,
                         settings={"learned": learned, "from_run": f"s3-r{rep}"})
    raise ValueError(f"unknown scenario {sc}")


def calibration_config(conf: dict, forbid_scipy: bool, coder_model: str) -> RunConfig:
    return RunConfig("cal", "cal", "A", 0, {r: (coder_model if r == "coder" else HAIKU) for r in ROLES},
                     {r: 5 * T0 for r in ROLES}, T0, max_windows=10, forbid_scipy=forbid_scipy)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


async def execute(ctx: Ctx, cfg: RunConfig, folder: str) -> tuple[Path, dict[str, Any], Any]:
    """Run into <folder>.partial; return (partial dir, summary row, RunResult) without renaming."""
    partial = ctx.base / f"{folder}.partial"
    if partial.exists():
        shutil.rmtree(partial)
    partial.mkdir(parents=True)
    write_json(partial / "config.json", {**asdict(cfg), "commit": git_commit(), "scripted": ctx.backend.scripted})
    started = datetime.now()
    team = Team(cfg, ctx.backend, partial)
    try:
        res = await team.run()
    finally:
        team.ledger.close()  # an open database would block deleting the partial folder on Windows
    ended = datetime.now()
    summary = summarize(cfg, res, started, ended)
    summary["wall_seconds"] = round((ended - started).total_seconds())
    write_json(partial / "summary.json", summary)
    return partial, summary, res


def finish(ctx: Ctx, partial: Path, summary: dict[str, Any], folder: str) -> None:
    """Atomic finish: rename the folder, append the results row, regenerate the consolidated files."""
    final = ctx.base / folder
    if final.exists():
        shutil.rmtree(final)
    partial.rename(final)
    results = ctx.base / "results.csv"
    new = not results.exists()
    with open(results, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, RESULT_COLUMNS, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow(summary)
    from rebbi.demo import report
    try:
        report.build_all(ctx)
    except Exception as e:  # noqa: BLE001  a report problem never costs a finished run
        print(f"report failed: {e!r}", flush=True)


async def run_calibration(ctx: Ctx) -> None:
    conf = load_config(ctx)
    forbid, coder = bool(conf.get("forbid_scipy", False)), conf.get("coder_model", HAIKU)
    notes: list[str] = []
    for attempt in range(1, 4):
        cfg = calibration_config(conf, forbid, coder)
        partial, summary, res = await execute(ctx, cfg, f"cal-a{attempt}")
        first3_valid = any(w["team"]["candidate_reason"] == "valid" for w in res.windows[:3])
        if attempt < 3 and not first3_valid and coder == HAIKU:
            coder = SONNET
            notes.append(f"attempt {attempt}: the Coder produced no valid candidate in 3 windows; Sonnet for the Coder")
        elif attempt < 3 and not forbid and flat_hill(res.windows):
            forbid = True
            notes.append(f"attempt {attempt}: flat-hill guard fired (window 2 score >= 98% of window 8); scipy forbidden")
        else:
            break
        partial.rename(ctx.base / f"cal-attempt{attempt}")  # kept as evidence, not counted
    nums = calibration_numbers(res.windows)
    conf.update(forbid_scipy=forbid, coder_model=coder)
    conf["calibration"] = {**{k: v for k, v in nums.items() if k != "per_role_demand"}, "notes": notes}
    conf["demand_per_window"] = nums["per_role_demand"]
    conf.pop("manager", None)  # budgets depend on T, so any earlier manager answer is stale
    save_config(ctx, conf)
    if summary["ledger_check"] != "PASS":
        set_status(ctx, "cal", "failed", "ledger check failed")
        return
    finish(ctx, partial, summary, "cal")
    set_status(ctx, "cal", "complete")


async def run_one(ctx: Ctx, row: dict[str, str]) -> None:
    run_id = row["run_id"]
    set_status(ctx, run_id, "running")
    try:
        if run_id == "cal":
            await run_calibration(ctx)
            return
        conf = load_config(ctx)
        cfg = await build_config(ctx, row, conf)
        partial, summary, res = await execute(ctx, cfg, run_id)
    except PlanLimit as e:
        set_status(ctx, run_id, "aborted_external", str(e))
        raise
    except Exception as e:  # noqa: BLE001
        set_status(ctx, run_id, "failed", repr(e))
        raise
    if summary["ledger_check"] == "PASS":
        finish(ctx, partial, summary, run_id)
        set_status(ctx, run_id, "complete")
    else:
        set_status(ctx, run_id, "failed", "ledger check failed: " + "; ".join(res.ledger_problems)[:300])


def run_all(ctx: Ctx, stop_at: datetime | None) -> int:
    """0: nothing pending or the stop time passed. 3: plan limit (caller waits and calls again). Else raises."""
    rows = ensure_manifest(ctx)
    while True:
        rows = read_manifest(ctx)
        row = next_pending(rows)
        past = stop_at is not None and datetime.now() > stop_at
        if row is None or past:
            ctx.state_dir.mkdir(parents=True, exist_ok=True)
            if not ctx.rehearsal:
                (ctx.state_dir / "RUNS_DONE").write_text(now_text(), encoding="utf-8")
            print("run-all: nothing pending" if row is None else "run-all: stop time passed", flush=True)
            return 0
        print(f"run-all: starting {row['run_id']}", flush=True)
        try:
            asyncio.run(run_one(ctx, row))
        except PlanLimit as e:
            print(f"run-all: plan limit on {row['run_id']}: {e}", flush=True)
            return 3
        if row["run_id"] == "cal" and read_manifest(ctx)[0]["status"] != "complete":
            raise RuntimeError("calibration did not complete")


def status_text(ctx: Ctx) -> str:
    rows = read_manifest(ctx)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    lines = [f"runs: {counts or 'no manifest yet'}"]
    lines += [f"  {r['run_id']:<10} {r['status']:<17} {r['error'][:80]}" for r in rows]
    return "\n".join(lines)
