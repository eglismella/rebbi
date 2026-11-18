"""Set up and collect one HW9 cold-start run (docs/hw9/PROTOCOL.md).

    python scripts/hw9_run.py setup RUN_DIR --prompt P1|P2|P3 --python VENV_PYTHON [--http-port 8765]
    (give the client RUN_DIR/prompt.txt, nothing else)
    python scripts/hw9_run.py collect RUN_DIR

setup makes RUN_DIR/fleet (fresh starter fleet), RUN_DIR/client (the only folder the client
works in) and RUN_DIR/prompt.txt. With --http-port it also starts `rebbi-mcp --http` for the
fleet and writes its pid to RUN_DIR/server.pid. collect stops that server, copies what the
client left into RUN_DIR, and scores the run with scripts/check_cold_start.py.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

P1 = """You are auditor-01, an agent in a small fleet of AI agents. Your working folder is {folder}. Work only with the files in that folder and the Python environment at {python}; do not look elsewhere on this machine.

Your job: write a dependency audit of the repository in ./target, following ./dep-audit-v1.md exactly, saved as ./report.md.

Your own token budget is 7,000 tokens, which will not cover this job. Past audits of this repository took up to 60,000 tokens. Your fleet shares spare budget through a service called Rebbi. Its documentation is ./AGENT_INTERFACE.md, and ./.mcp.json is the connection your operator set up for you. Do not read or change Rebbi's ledger file directly; use Rebbi's interface.

Secure enough budget before you start the audit, and start it only if you secured enough. When you finish or give up, close out with Rebbi so unused budget goes back.

At the end, write ./budget.json with what you asked for, what you got, from whom, the loan id or ids, the expiry, and how you closed it. Also keep ./worklog.md: each command you ran and what it showed you, briefly. Leave any code you wrote in the folder."""

P2 = (P1.replace("took up to 60,000 tokens", "took up to 100,000 tokens")
      .replace("Secure enough budget before you start the audit, and start it only if you secured enough. "
               "When you finish or give up, close out with Rebbi so unused budget goes back.",
               "Secure the budget this job needs, write ./budget.json, close out with Rebbi so the budget goes "
               "back, and stop: do not start the audit itself."))

P3 = (P2.replace("took up to 100,000 tokens", "took up to 30,000 tokens")
      .replace("Your fleet shares spare budget through a service called Rebbi. Its documentation is "
               "./AGENT_INTERFACE.md, and ./.mcp.json is the connection your operator set up for you.",
               "Your fleet shares spare budget through a service called Rebbi, which runs on another machine. "
               "Its documentation is ./AGENT_INTERFACE.md; ./.mcp.json holds its address and your access token."))

PROMPTS = {"P1": (P1, "full", 60_000), "P2": (P2, "budget-only", 100_000), "P3": (P3, "budget-only", 30_000)}
assert P2 != P1 and P3 != P2, "prompt substitutions did not apply"


def rebbi(python: str, *args: str) -> str:
    return subprocess.run([python, "-m", "rebbi", *args], check=True, capture_output=True, text=True,
                          cwd="/").stdout


def setup(run: Path, prompt: str, python: str, http_port: int | None) -> None:
    if run.exists():
        sys.exit(f"{run} exists; use a new run folder")
    fleet, client = run / "fleet", run / "client"
    client.mkdir(parents=True)
    rebbi(python, "init", str(fleet))
    shutil.copyfile(ROOT / "docs" / "AGENT_INTERFACE.md", client / "AGENT_INTERFACE.md")
    shutil.copyfile(ROOT / "specs" / "dep-audit-v1.md", client / "dep-audit-v1.md")
    shutil.copytree(ROOT / "targets" / "sqlite-utils", client / "target", ignore=shutil.ignore_patterns(".git"))
    if http_port:
        url = f"http://127.0.0.1:{http_port}/mcp"
        config = rebbi(python, "client-config", "--dir", str(fleet), "--agent", "auditor-01", "--http", url)
        log = (run / "server.log").open("w")
        proc = subprocess.Popen([str(Path(python).with_name("rebbi-mcp")), "--http", "--port", str(http_port),
                                 "--db", str(fleet / "rebbi.db"), "--scenario", str(fleet / "scenario.toml"),
                                 "--tokens", str(fleet / "tokens.toml"), "--trace", str(fleet / "trace.jsonl")],
                                stdout=log, stderr=log, cwd="/", start_new_session=True)
        (run / "server.pid").write_text(str(proc.pid))
        time.sleep(2)
    else:
        config = rebbi(python, "client-config", "--dir", str(fleet), "--agent", "auditor-01",
                       "--trace", str(fleet / "trace.jsonl"))
    (client / ".mcp.json").write_text(config, encoding="utf-8")
    text, mode, needed = PROMPTS[prompt]
    (run / "prompt.txt").write_text(text.format(folder=client, python=python) + "\n", encoding="utf-8")
    (run / "run.json").write_text(json.dumps({"prompt": prompt, "mode": mode, "needed": needed,
                                              "python": python, "http_port": http_port}, indent=2))
    print(f"set up {run}; give the client {run / 'prompt.txt'}")


def collect(run: Path) -> int:
    meta = json.loads((run / "run.json").read_text())
    pid_file = run / "server.pid"
    if pid_file.exists():
        try:
            os.killpg(int(pid_file.read_text()), signal.SIGTERM)
        except ProcessLookupError:
            pass
    for name in ("rebbi.db", "scenario.toml", "trace.jsonl"):
        if (run / "fleet" / name).exists():
            shutil.copyfile(run / "fleet" / name, run / name)
    for name in ("budget.json", "report.md", "worklog.md"):
        if (run / "client" / name).exists():
            shutil.copyfile(run / "client" / name, run / name)
    code = [p for p in (run / "client").glob("*.py")] + [p for p in (run / "client").glob("*.sh")]
    if code:
        (run / "client-code").mkdir(exist_ok=True)
        for p in code:
            shutil.copyfile(p, run / "client-code" / p.name)
    status = subprocess.run([sys.executable, "-m", "rebbi", "--db", str(run / "rebbi.db"), "status"],
                            capture_output=True, text=True, cwd=ROOT).stdout
    (run / "status.txt").write_text(status)
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "check_cold_start.py"), str(run),
                           "--mode", meta["mode"], "--needed", str(meta["needed"])], cwd=ROOT).returncode


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("setup")
    s.add_argument("run", type=Path)
    s.add_argument("--prompt", choices=sorted(PROMPTS), required=True)
    s.add_argument("--python", required=True, help="python of a venv with rebbi installed (not the checkout)")
    s.add_argument("--http-port", type=int)
    c = sub.add_parser("collect")
    c.add_argument("run", type=Path)
    args = p.parse_args()
    if args.cmd == "setup":
        setup(args.run.resolve(), args.prompt, args.python, args.http_port)
        return 0
    return collect(args.run.resolve())


if __name__ == "__main__":
    sys.exit(main())
