"""Operator commands for the demo.

    python -m rebbi seed --reset     # fresh ledger from config/scenario.toml
    python -m rebbi status           # agents, loans and broker decisions
    python -m rebbi check            # ledger invariants; exit 1 if any is broken
    python -m rebbi fetch-target     # clone the audit repo at its pinned commit
    python -m rebbi fetch-target --all             # every repo in config/targets.toml
    python -m rebbi fetch-target --target llm-0.12
    rebbi init fleet                 # a fleet folder anywhere: fleet file, seeded ledger, HTTP tokens
    rebbi client-config --dir fleet --agent auditor-01   # the .mcp.json entry for one agent
"""

from __future__ import annotations

import argparse
import json
import secrets
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from rebbi import rules as lending
from rebbi import scenario
from rebbi.broker import utcnow
from rebbi.ledger import Ledger


def fetch(target: scenario.AuditTarget) -> int:
    dest = scenario.DEFAULT_SCENARIO.parent.parent / target.local_path
    if not dest.exists():
        dest.mkdir(parents=True)
        git = lambda *a: subprocess.run(["git", "-C", str(dest), *a], check=True)  # noqa: E731
        git("init", "-q")
        git("fetch", "-q", "--depth", "1", target.repo, target.commit)
        git("checkout", "-q", "FETCH_HEAD")
    head = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()
    if head != target.commit:
        print(f"{dest} is at {head}, not the pinned {target.commit}")
        return 1
    print(f"{dest} is at the pinned commit {head}")
    return 0


def init(folder: Path, force: bool) -> int:
    """A fleet that lives outside the repository: what an operator sets up for outside agents."""
    folder.mkdir(parents=True, exist_ok=True)
    fleet, db, tokens = folder / "scenario.toml", folder / "rebbi.db", folder / "tokens.toml"
    if db.exists() and not force:
        print(f"{db} already exists; pass --force to start the fleet over")
        return 1
    if not fleet.exists() or force:
        shutil.copyfile(scenario.STARTER_FLEET, fleet)
    for suffix in ("", "-wal", "-shm"):
        Path(str(db) + suffix).unlink(missing_ok=True)
    sc = scenario.load(fleet)
    scenario.seed(Ledger(db), sc, utcnow())
    lines = ["# Bearer tokens for `rebbi-mcp --http`: one per agent. Keep this file private.", "[tokens]"]
    lines += [f'"{a.id}" = "{secrets.token_urlsafe(24)}"' for a in sc.agents]
    tokens.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        tokens.chmod(0o600)
    except OSError:
        pass
    print(f"fleet file   {fleet}  (edit budgets, reserves and rules here, then `rebbi init {folder} --force`)")
    print(f"ledger       {db}  ({len(sc.agents)} agents: {', '.join(a.id for a in sc.agents)})")
    print(f"HTTP tokens  {tokens}")
    print(f"next: rebbi client-config --dir {folder} --agent {sc.agents[0].id}")
    return 0


def client_config(folder: Path, agent: str, trace: str | None, http_url: str | None) -> int:
    """Print an MCP client entry (the `mcpServers` shape Claude Code, Claude Desktop and others read)."""
    folder = folder.resolve()
    sc = scenario.load(folder / "scenario.toml")
    if agent not in {a.id for a in sc.agents}:
        print(f"no agent {agent!r} in {folder / 'scenario.toml'}", file=sys.stderr)
        return 1
    if http_url:
        data = tomllib.loads((folder / "tokens.toml").read_text(encoding="utf-8"))
        entry = {"type": "http", "url": http_url,
                 "headers": {"Authorization": f"Bearer {data['tokens'][agent]}"}}
    else:
        env = {"REBBI_AGENT_ID": agent, "REBBI_DB": str(folder / "rebbi.db"),
               "REBBI_SCENARIO": str(folder / "scenario.toml")}
        if trace:
            env["REBBI_TRACE"] = str(Path(trace).resolve())
        entry = {"type": "stdio", "command": sys.executable, "args": ["-m", "rebbi.mcp_server"], "env": env}
    print(json.dumps({"mcpServers": {"rebbi": entry}}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="rebbi")
    p.add_argument("--db", default="rebbi.db")
    p.add_argument("--scenario", default=str(scenario.DEFAULT_SCENARIO))
    sub = p.add_subparsers(dest="cmd", required=True)
    seed = sub.add_parser("seed", help="register the scenario's agents and grant their budgets")
    seed.add_argument("--reset", action="store_true", help="delete the existing ledger first")
    sub.add_parser("status", help="show agents, loans and decisions")
    sub.add_parser("check", help="check the ledger invariants")
    fetch_target = sub.add_parser("fetch-target", help="clone the audit repo at the commit pinned in the scenario")
    fetch_target.add_argument("--target", help="a repo from config/targets.toml instead of the scenario's")
    fetch_target.add_argument("--all", action="store_true", help="every repo in config/targets.toml")
    init_p = sub.add_parser("init", help="create a fleet folder: fleet file, seeded ledger and HTTP tokens")
    init_p.add_argument("folder", type=Path)
    init_p.add_argument("--force", action="store_true", help="start an existing fleet over")
    cc = sub.add_parser("client-config", help="print the MCP client entry for one agent of a fleet folder")
    cc.add_argument("--dir", type=Path, required=True, help="the folder `rebbi init` created")
    cc.add_argument("--agent", required=True)
    cc.add_argument("--trace", help="stdio: log every tool call to this JSONL file")
    cc.add_argument("--http", metavar="URL", help="connect to `rebbi-mcp --http` at this URL instead of stdio")
    args = p.parse_args(argv)

    if args.cmd == "init":
        return init(args.folder, args.force)
    if args.cmd == "client-config":
        return client_config(args.dir, args.agent, args.trace, args.http)

    if args.cmd == "fetch-target":
        known = scenario.targets()
        chosen = (list(known.values()) if args.all else [known[args.target]] if args.target
                  else [scenario.load(args.scenario).target])
        return max(fetch(t) for t in chosen)

    if args.cmd == "seed":
        if args.reset:
            for suffix in ("", "-wal", "-shm"):
                Path(args.db + suffix).unlink(missing_ok=True)
        sc = scenario.load(args.scenario)
        scenario.seed(Ledger(args.db), sc, utcnow())
        print(f"seeded {len(sc.agents)} agents into {args.db}")
        return 0

    ledger = Ledger(args.db)
    if args.cmd == "status":
        print(f"{'agent':<12} {'balance':>9} {'reserve':>9} {'demand':>9} {'lendable':>9}  lends")
        for a in ledger.agents():
            print(f"{a.agent_id:<12} {a.balance:>9} {a.reserve_tokens:>9} {a.expected_demand_tokens:>9} "
                  f"{lending.lendable(a):>9}  {'yes' if a.will_lend else 'no'}")
        for loan in ledger.loans():
            print(f"loan {loan['loan_id']}: {loan['lender']} -> {loan['borrower']} {loan['tokens']} tokens, "
                  f"{loan['status']}, returned {loan['returned_tokens']}")
        for d in ledger.decisions():
            r = d["response"]
            print(f"decision {d['decision_id']} at {d['at']}: {d['requester']} asked {r['requested']} -> "
                  f"{d['decision']} {r.get('tokens', '')} {r.get('from', r.get('blocker', ''))}")
        return 0

    problems = ledger.check_invariants(utcnow())
    for problem in problems:
        print("FAIL", problem)
    print("ledger invariants: " + ("FAIL" if problems else "PASS"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
