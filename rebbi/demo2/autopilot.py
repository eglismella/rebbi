"""The v2 autopilot, in Python so it is tested: preflight, freeze (or wait for it), parallel lanes, export, report.

    python -m rebbi.demo2 autopilot --machine pietro --repeats 1-3
    python -m rebbi.demo2 autopilot --machine eglis  --repeats 4-6

Phases are marked by files in docs/demo2/state/<machine>/ so a restart resumes where it stopped. Progress for
the monitoring chat: logs/demo2/<machine>/autopilot.log and status.txt (rewritten every 10 minutes).
A failure that code must fix starts one headless Claude Code session under docs/demo2/TASK.md, then resumes.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from rebbi.demo2.runner import ROOT

CLAUDE_ALLOWED = ["Bash", "PowerShell", "Read", "Edit", "Write", "Glob", "Grep", "TodoWrite"]


class Autopilot:
    def __init__(self, machine: str, repeats: str, lanes: int = 3, stop_at: str = "2026-11-22T12:00:00",
                 root: Path = ROOT, py: str = sys.executable, claude: str = "claude", git: str = "git",
                 sleep=time.sleep, poll_s: int = 60, limit_wait_s: int = 20 * 60, max_fixes: int = 8):
        self.machine, self.repeats, self.lanes, self.stop_at = machine, repeats, lanes, stop_at
        self.root, self.py, self.claude, self.git = root, py, claude, git
        self.sleep, self.poll_s, self.limit_wait_s, self.max_fixes = sleep, poll_s, limit_wait_s, max_fixes
        self.state = root / "docs" / "demo2" / "state" / machine
        self.logs = root / "logs" / "demo2" / machine
        self.state.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        self.branch = "demo-v2" if machine == "pietro" else "demo-v2-eglis"
        self.fixes = 0
        self.env = {**os.environ, "REBBI_MACHINE": machine, "PYTHONIOENCODING": "utf-8", "GIT_TERMINAL_PROMPT": "0"}
        self.env.pop("ANTHROPIC_API_KEY", None)
        token = read_token(root / ".env")
        if token:
            self.env["CLAUDE_CODE_OAUTH_TOKEN"] = token
        self.claude_args = ["--permission-mode", "auto"]

    # -- helpers -------------------------------------------------------------------------------------

    def log(self, msg: str) -> None:
        line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
        print(line, flush=True)
        with open(self.logs / "autopilot.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def done(self, name: str) -> bool:
        return (self.state / name).exists()

    def mark(self, name: str) -> None:
        (self.state / name).write_text(datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
        self.log(f"phase {name} done")

    def run(self, tag: str, args: list[str], timeout: int | None = None) -> int:
        with open(self.logs / f"{tag}.log", "a", encoding="utf-8") as f:
            f.write(f"\n=== {datetime.now():%Y-%m-%d %H:%M:%S} {' '.join(args)}\n")
            f.flush()
            try:
                return subprocess.run(args, cwd=self.root, env=self.env, stdout=f, stderr=subprocess.STDOUT,
                                      timeout=timeout).returncode
            except (OSError, subprocess.TimeoutExpired) as e:
                f.write(f"{e!r}\n")
                return 99

    def pym(self, tag: str, *args: str, timeout: int | None = None) -> int:
        return self.run(tag, [self.py, "-m", *args], timeout)

    def git_(self, *args: str) -> int:
        return self.run("git", [self.git, *args], timeout=300)

    def status(self) -> None:
        with open(self.logs / "status.txt", "w", encoding="utf-8") as f:
            subprocess.run([self.py, "-m", "rebbi.demo2", "status", "--repeats", self.repeats], cwd=self.root,
                           env=self.env, stdout=f, stderr=subprocess.STDOUT, timeout=120)
            f.write(f"\nupdated {datetime.now():%Y-%m-%d %H:%M:%S}\n")

    def push_results(self) -> None:
        self.pym("export", "rebbi.demo2", "export", "--machine", self.machine)
        self.git_("add", "-f", f"results/demo2/{self.machine}")
        self.git_("commit", "-m", f"demo2: results from {self.machine} ({datetime.now():%Y-%m-%d %H:%M})")
        code = self.git_("push", "origin", f"HEAD:{self.branch}")
        self.log(f"results pushed to {self.branch}" if code == 0 else f"push to {self.branch} failed (see git.log)")

    def check_claude(self) -> bool:
        def ask(extra: list[str]) -> bool:
            try:
                r = subprocess.run([self.claude, "-p", "Reply with the word ready.", *extra, "--output-format", "text"],
                                   cwd=self.root, env=self.env, capture_output=True, text=True, timeout=180)
            except (OSError, subprocess.TimeoutExpired):
                return False
            return r.returncode == 0 and "ready" in r.stdout.lower()
        if not ask([]):
            return False
        if not ask(["--permission-mode", "auto"]):
            self.claude_args = ["--permission-mode", "acceptEdits", "--allowedTools", *CLAUDE_ALLOWED]
        return True

    def fix(self, what: str, log_file: Path) -> None:
        self.fixes += 1
        if self.fixes > self.max_fixes:
            self.log("too many fix sessions; stopping")
            raise SystemExit(2)
        prompt = (f"Work autonomously: nobody will answer questions. Machine: {self.machine}. Read docs/demo2/TASK.md "
                  f"(rules) and docs/demo2/DESIGN.md (the frozen design). Problem: {what}. Read the end of {log_file}. "
                  "Find the cause, fix it with a test, run python -m pytest -q tests/test_demo2.py, commit locally. "
                  "Follow TASK.md 'Fix rules' exactly. Stop when the fix is committed.")
        out = self.logs / f"claude-fix-{self.fixes:02d}.jsonl"
        self.log(f"fix session {self.fixes}: {what} -> {out.name}")
        with open(out, "w", encoding="utf-8") as f:
            try:
                code = subprocess.run([self.claude, "-p", prompt, *self.claude_args, "--output-format", "stream-json",
                                       "--verbose"], cwd=self.root, env=self.env, stdout=f, stderr=subprocess.STDOUT,
                                      timeout=3 * 3600).returncode
            except (OSError, subprocess.TimeoutExpired) as e:
                f.write(repr(e))
                code = 99
        if code != 0:
            self.log(f"fix session ended with exit {code}; waiting {self.limit_wait_s // 60} min")
            self.sleep(self.limit_wait_s)
        if (self.root / "docs" / "demo2" / "BLOCKED.md").exists():
            self.log("BLOCKED: docs/demo2/BLOCKED.md needs a decision from Pietro; stopping")
            raise SystemExit(3)

    # -- phases ----------------------------------------------------------------------------------------

    def preflight(self) -> None:
        c1 = self.pym("preflight", "rebbi.demo2", "preflight")
        c2 = self.pym("unit-tests", "pytest", "-q", "tests/test_demo2.py")
        c3 = self.pym("rehearsal", "rebbi.demo2", "rehearsal")
        if (c1, c2, c3) == (0, 0, 0):
            self.mark("PREFLIGHT_DONE")
            return
        self.log(f"preflight failed (reference solutions {c1}, unit tests {c2}, rehearsal {c3})")
        bad = "preflight" if c1 else "unit-tests" if c2 else "rehearsal"
        self.fix(f"the preflight failed: reference solutions exit {c1}, unit tests exit {c2}, rehearsal exit {c3}",
                 self.logs / f"{bad}.log")

    def prepare(self) -> None:
        conf = self.root / "config" / "demo2.toml"
        if self.machine == "pietro":
            code = self.pym("prepare", "rebbi.demo2", "prepare")
            if code != 0:
                self.fix(f"python -m rebbi.demo2 prepare failed (exit {code})", self.logs / "prepare.log")
                return
            self.git_("add", str(conf.relative_to(self.root)), "exercises/demo2/denominators.json")
            self.git_("commit", "-m", "demo2: frozen config (calibration, T, floors, summits, manager, gate)")
            code = self.git_("push", "origin", "HEAD:demo-v2")
            self.log(f"frozen config pushed to demo-v2 (exit {code}): {frozen_line(conf)}")
            self.mark("PREPARED")
            return
        (self.root / "exercises" / "demo2" / "denominators.json").unlink(missing_ok=True)
        self.git_("pull", "--ff-only", "origin", "demo-v2")
        if is_frozen(conf):
            self.log(f"frozen config received: {frozen_line(conf)}")
            self.mark("PREPARED")
            return
        self.log("waiting for the frozen config from Pietro's machine; next check in 10 min")
        self.sleep(600)

    def runs(self) -> None:
        shutil.rmtree(self.root / "runs" / "demo2" / "_locks", ignore_errors=True)  # no lane runs now
        procs = []
        for i in range(1, self.lanes + 1):
            out = open(self.logs / f"lane{i}-{datetime.now():%m%d-%H%M%S}.log", "w", encoding="utf-8")
            p = subprocess.Popen([self.py, "-m", "rebbi.demo2", "run", "--repeats", self.repeats, "--stop-new-runs-at",
                                  self.stop_at], cwd=self.root, env=self.env, stdout=out, stderr=subprocess.STDOUT)
            procs.append((p, out))
            self.log(f"lane {i} started (pid {p.pid})")
            self.sleep(min(30, self.poll_s))
        last_status = last_push = time.time()
        while any(p.poll() is None for p, _ in procs):
            self.sleep(self.poll_s)
            if time.time() - last_status >= 600:
                self.status()
                last_status = time.time()
            if time.time() - last_push >= 900:
                self.push_results()
                last_push = time.time()
        for _, out in procs:
            out.close()
        codes = [p.returncode for p, _ in procs]
        self.log(f"lanes ended with exit codes {codes}")
        self.push_results()
        if 4 in codes:
            lane_logs = sorted(self.logs.glob("lane*.log"), key=lambda q: q.stat().st_mtime)
            self.fix("a scenario run failed three times (lane exit 4); runs/demo2/_status has the errors", lane_logs[-1])
            for st in (self.root / "runs" / "demo2" / "_status").glob("*.json"):
                d = json.loads(st.read_text(encoding="utf-8"))
                if d.get("state") == "failed":
                    d.update(state="pending", attempts=0)
                    st.write_text(json.dumps(d, indent=1), encoding="utf-8")
            return
        if any(c != 0 for c in codes):
            self.log("a lane stopped unexpectedly; restarting lanes in 2 min")
            self.sleep(120)
            return
        self.mark("RUNS_DONE")

    def final(self) -> None:
        self.push_results()
        if self.machine == "pietro":
            if self.git_("fetch", "origin", "demo-v2-eglis") == 0:
                self.git_("checkout", "origin/demo-v2-eglis", "--", "results/demo2/eglis")
            code = self.pym("report", "rebbi.demo2", "report")
            self.git_("add", "-f", "results/demo2", "docs/demo2/results.html")
            self.git_("commit", "-m", "demo2: report")
            self.git_("push", "origin", "HEAD:demo-v2")
            self.log(f"report built (exit {code}): docs/demo2/results.html")
        self.mark("FINAL_DONE")

    def main(self) -> int:
        if not read_token(self.root / ".env"):
            self.log("no CLAUDE_CODE_OAUTH_TOKEN in .env: run claude setup-token and add the line, then restart")
            return 1
        if not self.check_claude():
            self.log("Claude Code cannot sign in with the token in .env: run claude setup-token again, replace the "
                     "line in .env, restart")
            return 1
        self.log(f"autopilot started: machine {self.machine}, repeats {self.repeats}, lanes {self.lanes}")
        try:
            while not self.done("FINAL_DONE"):
                self.status()
                if not self.done("PREFLIGHT_DONE"):
                    self.preflight()
                elif not self.done("PREPARED"):
                    self.prepare()
                elif not self.done("RUNS_DONE"):
                    self.runs()
                else:
                    self.final()
        except SystemExit as e:
            return int(e.code or 0)
        self.log("all phases done; page: docs/demo2/results.html")
        return 0


def read_token(env_file: Path) -> str:
    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        return os.environ["CLAUDE_CODE_OAUTH_TOKEN"]
    if not env_file.exists():
        return ""
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        k, sep, v = line.partition("=")
        if sep and k.strip() == "CLAUDE_CODE_OAUTH_TOKEN":
            return v.strip().strip('"').strip("'")
    return ""


def is_frozen(conf: Path) -> bool:
    return conf.exists() and any(line.strip() == "frozen = true" for line in conf.read_text(encoding="utf-8").splitlines())


def frozen_line(conf: Path) -> str:
    if not conf.exists():
        return ""
    keep = [line.strip() for line in conf.read_text(encoding="utf-8").splitlines()
            if line.startswith(("T = ", "summit_A", "summit_B", "cal_score_A", "cal_score_B"))]
    return ", ".join(keep)
