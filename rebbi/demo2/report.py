"""Export finished runs as small JSON bundles (committed to git), and build the results page from all machines.

  python -m rebbi.demo2 export   -> results/demo2/<machine>/<run_id>.json  (one per finished run, plus cal-A/B)
  python -m rebbi.demo2 report   -> results/demo2/results.csv, results/demo2/data.json, docs/demo2/results.html

The page is docs/demo2/page/template.html (the "Rebbi Demo of Demo" layout) with the data inlined, so the HTML
file is self-contained and can be published as it is.
"""

from __future__ import annotations

import csv
import json
import os
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any

from rebbi.demo2.runner import NAMES, ROOT, SCENARIOS, Ctx, load_config, read_jsonl, write_json
from rebbi.demo2.team import PHASES, ROLES

ROLE_IDS = ["PL", "RS", "CD", "EV", "RV"]
ROLE_JOBS = ["Orders the open exercises", "Writes notes from instructions and tests", "Writes the solution; tests run",
             "Reports each test run", "Approves or rewrites"]
MODEL_LABEL = {"claude-haiku-5-5": "Claude Haiku 5.5", "claude-sonnet-5-5": "Claude Sonnet 5.5"}
KEY = {"1": "s1", "2": "s2", "3": "s3", "3-on-B": "s3onB", "3b": "s3b", "4": "s4", "cal": "cal"}
COLUMNS = ["machine", "run_id", "scenario", "exercise", "repeat", "model", "T", "budgets", "shareable_pct", "summit",
           "windows", "windows_to_summit", "final_score", "tokens_issued", "tokens_used", "tokens_expired",
           "interruptions", "cut_offs", "loans_count", "tokens_moved", "ledger_check", "wall_seconds", "started_at",
           "ended_at"]


def why(denied: str | None) -> str:
    if not denied:
        return ""
    if "0%" in denied:
        return "share"
    if "claim" in denied or "debt" in denied:
        return "debt"
    return "pool"


def bundle(run_dir: Path) -> dict[str, Any]:
    cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    rows = read_jsonl(run_dir / "windows.jsonl")
    idx = {r: i for i, r in enumerate(ROLES)}
    frames = []
    for w in rows:
        a = [w["agents"][r] for r in ROLES]
        frames.append({
            "t": w["window"], "phase": w["team"]["phase"], "score": w["team"]["score"],
            "stages": w["team"]["stages"],
            "B": [x["budget"] for x in a], "afs": [round(x["shareable_pct"] / 100, 3) for x in a],
            "used": [x["used"] for x in a], "lent": [x["lent"] for x in a], "borrowed": [x["borrowed"] for x in a],
            "expired": [x["expired"] for x in a], "unmet": [x["unmet"] for x in a],
            "D": [x["used"] + x["unmet"] for x in a], "blocked": [bool(x["interrupted"]) for x in a],
            "cut": [bool(x.get("cut_off")) for x in a], "denied": [bool(x.get("denied")) for x in a],
            "why": [why(x.get("denied")) for x in a], "q": [x.get("queue", 0) for x in a],
            "done": [x.get("done", 0) for x in a], "credit": [x.get("claim_balance", 0) for x in a],
            "loans": [{"from": idx.get(l["from"], -1), "to": idx.get(l["to"], -1), "amt": l["tokens"]}
                      for l in w["team"]["loans"] if l.get("tokens")],
        })
    calls = [{k: c[k] for k in ("window", "role", "kind", "slug", "total", "stopped")}
             for c in read_jsonl(run_dir / "calls.jsonl")] if cfg["scenario"] == "cal" else []
    tests = [e for e in read_jsonl(run_dir / "events.jsonl") if e["kind"] == "tests"] if cfg["scenario"] == "cal" else []
    return {"config": cfg, "summary": summary, "frames": frames, "calls": calls, "tests": tests}


def export(ctx: Ctx, machine: str | None = None, out_root: Path = ROOT / "results" / "demo2") -> list[Path]:
    machine = machine or os.environ.get("REBBI_MACHINE", "pietro")
    out = out_root / machine
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for d in sorted(ctx.base.iterdir()) if ctx.base.exists() else []:
        if d.is_dir() and (d / "summary.json").exists() and not d.name.endswith(".partial"):
            p = out / f"{d.name}.json"
            write_json(p, bundle(d))
            written.append(p)
    return written


def load_bundles(root: Path) -> list[dict[str, Any]]:
    out = []
    for p in sorted(root.glob("*/*.json")):
        b = json.loads(p.read_text(encoding="utf-8"))
        b["machine"] = p.parent.name
        out.append(b)
    return out


def run_entry(b: dict[str, Any]) -> dict[str, Any]:
    c, s, fr = b["config"], b["summary"], b["frames"]
    summit = c.get("summit") or 100.0
    done = s["windows_to_summit"] if isinstance(s["windows_to_summit"], int) else None
    prev = 0.0
    out_frames = []
    for f in fr:
        p = min(100.0, 100.0 * f["score"] / summit) if summit else 0.0
        ms = [m for m in (25, 50, 75, 100) if prev < m <= p]
        out_frames.append({**f, "p0": prev, "p": round(p, 2), "ms": ms})
        prev = p
    return {"id": c["run_id"], "sc": KEY[c["scenario"]], "scenario": c["scenario"], "ex": c["exercise"],
            "rep": c["repeat"], "machine": b["machine"], "budgets": [c["budgets"][r] for r in ROLES],
            "afs": [round(c.get("shareable_pct", {}).get(r, 0) / 100, 3) for r in ROLES], "summit": summit,
            "done": done, "status": s["windows_to_summit"], "windows": len(fr), "final_score": s["final_score"],
            "tot": {"issued": s["tokens_issued"], "used": s["tokens_used"], "expired": s["tokens_expired"],
                    "blocks": s["interruptions"], "cutoffs": s["cut_offs"], "moved": s["tokens_moved"],
                    "loans": s["loans_count"]},
            "wall_seconds": s.get("wall_seconds"), "frames": out_frames}


def aggregate(runs: list[dict[str, Any]], cap: int) -> dict[str, Any]:
    agg = {}
    for sc, ex, key in SCENARIOS:
        rs = [r for r in runs if r["sc"] == key]
        if not rs:
            continue
        w = [r["done"] if r["done"] else cap + 1 for r in rs]
        e = [r["tot"]["expired"] / r["tot"]["issued"] if r["tot"]["issued"] else 0 for r in rs]
        agg[key] = {"n": len(rs), "windows": sorted(w), "median_windows": statistics.median(w),
                    "reached": sum(1 for r in rs if r["done"]), "median_expired_share": statistics.median(e),
                    "median_interruptions": statistics.median(r["tot"]["blocks"] for r in rs),
                    "median_moved": statistics.median(r["tot"]["moved"] for r in rs)}
    return agg


def build(root: Path = ROOT, ctx: Ctx | None = None, results_root: Path | None = None,
          template: Path | None = None, page_out: Path | None = None) -> dict[str, Any]:
    results_root = results_root or root / "results" / "demo2"
    bundles = load_bundles(results_root)
    cal = {b["config"]["exercise"]: b for b in bundles if b["config"]["scenario"] == "cal" and b["machine"] != "rehearsal"}
    runs = [run_entry(b) for b in bundles if b["config"]["scenario"] != "cal"]
    runs.sort(key=lambda r: (r["rep"], [k for _, _, k in SCENARIOS].index(r["sc"])))
    conf = load_config(ctx) if ctx else {}
    if not conf:
        p = root / "config" / "demo2.toml"
        if p.exists():
            import tomllib
            conf = tomllib.loads(p.read_text(encoding="utf-8"))
    from rebbi.demo2 import suite
    sets = {}
    for name in ("A", "B"):
        try:
            exs = suite.load_set(name, ctx.exercises_root if ctx else suite.EXERCISES)
            sets[name] = {"n_ex": len(exs), "n_tests": sum(e.ntests for e in exs)}
        except Exception:  # noqa: BLE001
            sets[name] = {}
    cap = max([r["windows"] for r in runs] + [60])
    cal_demand = {}
    for ex, b in cal.items():
        per = {r: [] for r in ROLES}
        for f in b["frames"]:
            for i, r in enumerate(ROLES):
                per[r].append(f["used"][i])
        cal_demand[ex] = {r: round(statistics.mean(v)) if v else 0 for r, v in per.items()}
    data = {
        "meta": {"generated_at": datetime.now().isoformat(timespec="seconds"), "design": conf.get("design"),
                 "model": MODEL_LABEL.get(conf.get("model"), conf.get("model")), "T": conf.get("calibration", {}).get("T"), "cap": 60,
                 "summit": {"A": conf.get("calibration", {}).get("summit_A"),
                            "B": conf.get("calibration", {}).get("summit_B")},
                 "cal_score": {"A": conf.get("calibration", {}).get("cal_score_A"),
                               "B": conf.get("calibration", {}).get("cal_score_B")},
                 "floors": conf.get("floors"), "manager": conf.get("manager"), "gate": conf.get("gate"),
                 "sets": sets, "machines": sorted({r["machine"] for r in runs}),
                 "repeats": sorted({r["rep"] for r in runs}), "frozen_at": conf.get("frozen_at")},
        "roles": [{"id": i, "name": r.capitalize(), "job": j} for r, i, j in zip(ROLES, ROLE_IDS, ROLE_JOBS)],
        "phases": PHASES, "names": NAMES, "runs": runs, "aggregate": aggregate(runs, 60),
        "cal_demand": cal_demand,
    }
    write_json(results_root / "data.json", data)
    with open(results_root / "results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLUMNS, extrasaction="ignore")
        w.writeheader()
        for b in bundles:
            w.writerow({**b["summary"], "machine": b["machine"]})
    template = template or root / "docs" / "demo2" / "page" / "template.html"
    page_out = page_out or root / "docs" / "demo2" / "results.html"
    if template.exists():
        html = template.read_text(encoding="utf-8")
        payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
        page_out.write_text(html.replace("/*__DATA__*/null", payload), encoding="utf-8")
    return data
