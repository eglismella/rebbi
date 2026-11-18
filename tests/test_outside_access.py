"""What an agent outside our harness relies on: a fleet folder anywhere, client configs,
the HTTP server with per-agent tokens, and the call trace."""

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
import tomllib
from pathlib import Path

import httpx2
import pytest
from mcp import Client, StdioServerParameters
from mcp.client.streamable_http import streamable_http_client

from rebbi import scenario
from rebbi.__main__ import main as cli
from rebbi.ledger import Ledger
from rebbi.mcp_server import Tracer, build_server, load_tokens

ROOT = Path(__file__).resolve().parent.parent


def test_the_packaged_starter_fleet_matches_the_repo_scenario():
    """pip install from git ships rebbi/starter_fleet.toml; it must not drift from config/scenario.toml."""
    assert scenario.STARTER_FLEET.read_bytes() == (ROOT / "config" / "scenario.toml").read_bytes()


def test_init_creates_a_fleet_folder_with_unique_tokens(tmp_path, capsys):
    assert cli(["init", str(tmp_path / "fleet")]) == 0
    fleet = tmp_path / "fleet"
    agents = {a.agent_id for a in Ledger(fleet / "rebbi.db").agents()}
    assert agents == {"auditor-01", "analyst-07", "writer-03"}
    tokens = tomllib.loads((fleet / "tokens.toml").read_text())["tokens"]
    assert set(tokens) == agents and len(set(tokens.values())) == 3
    assert cli(["init", str(fleet)]) == 1  # will not wipe a live ledger by accident


def test_client_config_points_at_the_fleet(tmp_path, capsys):
    cli(["init", str(tmp_path / "fleet")])
    capsys.readouterr()
    assert cli(["client-config", "--dir", str(tmp_path / "fleet"), "--agent", "auditor-01"]) == 0
    entry = json.loads(capsys.readouterr().out)["mcpServers"]["rebbi"]
    assert entry["env"]["REBBI_AGENT_ID"] == "auditor-01"
    assert Path(entry["env"]["REBBI_DB"]).is_absolute()
    assert cli(["client-config", "--dir", str(tmp_path / "fleet"), "--agent", "nobody"]) == 1


def test_trace_records_calls_and_errors(broker, tmp_path):
    trace = tmp_path / "trace.jsonl"
    server = build_server(broker, "auditor-01", tracer=Tracer(trace))

    async def run():
        async with Client(server) as client:
            await client.call_tool("post_handoff", {"goal": "audit", "budget_tokens": 30_000, "request_id": "a"})
            await client.call_tool("settle", {"loan_id": 999})

    asyncio.run(run())
    lines = [json.loads(line) for line in trace.read_text().splitlines()]
    assert [(e["tool"], "error" in e) for e in lines] == [("post_handoff", False), ("settle", True)]
    assert lines[0]["result"]["decision"] == "LEND" and lines[0]["arguments"]["request_id"] == "a"


def test_no_trace_file_without_a_path(broker, tmp_path):
    server = build_server(broker, "auditor-01")

    async def run():
        async with Client(server) as client:
            await client.call_tool("get_budget", {})

    asyncio.run(run())
    assert not list(tmp_path.rglob("*.jsonl"))


def test_token_file_must_name_known_agents(broker, tmp_path):
    bad = tmp_path / "tokens.toml"
    bad.write_text('[tokens]\n"ghost-99" = "aaaaaaaaaaaaaaaaaaaa"\n')
    with pytest.raises(Exception):
        load_tokens(bad, broker.ledger)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def http_fleet(tmp_path):
    cli(["init", str(tmp_path / "fleet")])
    fleet = tmp_path / "fleet"
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "rebbi.mcp_server", "--http", "--port", str(port),
         "--db", str(fleet / "rebbi.db"), "--scenario", str(fleet / "scenario.toml"),
         "--tokens", str(fleet / "tokens.toml"), "--trace", str(fleet / "trace.jsonl")],
        cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ.copy())
    for _ in range(100):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    tokens = tomllib.loads((fleet / "tokens.toml").read_text())["tokens"]
    yield f"http://127.0.0.1:{port}/mcp", tokens, fleet
    proc.terminate()
    proc.wait(timeout=10)


def _call_over_http(url: str, token: str | None, tool: str, args: dict):
    async def run():
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with httpx2.AsyncClient(headers=headers) as http:
            async with Client(streamable_http_client(url, http_client=http)) as client:
                return (await client.call_tool(tool, args)).structured_content

    return asyncio.run(run())


def test_http_mode_speaks_for_the_token_holder(http_fleet):
    url, tokens, fleet = http_fleet
    lend = _call_over_http(url, tokens["auditor-01"], "post_handoff", {"goal": "audit", "budget_tokens": 30_000})
    assert (lend["decision"], lend["from"]) == ("LEND", "analyst-07")
    budget = _call_over_http(url, tokens["analyst-07"], "get_budget", {})
    assert budget["agent_id"] == "analyst-07" and budget["lent"][0]["borrower"] == "auditor-01"
    trace = [json.loads(line) for line in (fleet / "trace.jsonl").read_text().splitlines()]
    assert [e["agent_id"] for e in trace] == ["auditor-01", "analyst-07"]


def test_http_mode_refuses_a_missing_or_wrong_token(http_fleet):
    url, _, fleet = http_fleet
    for token in (None, "not-a-real-token-at-all"):
        with pytest.raises(Exception):
            _call_over_http(url, token, "get_budget", {})
    assert not (fleet / "trace.jsonl").exists()
