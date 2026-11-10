"""The two front doors: the MCP server agents call, and the HTTP API the gateway calls."""

import asyncio
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from mcp import Client, StdioServerParameters

from rebbi import scenario
from rebbi.api import create_app
from rebbi.broker import HandoffRequest
from rebbi.ledger import Ledger
from rebbi.mcp_server import build_server

ROOT = Path(__file__).resolve().parent.parent


def test_mcp_tools_lend_and_settle_in_process(broker):
    async def run():
        async with Client(build_server(broker, "auditor-01")) as client:
            names = {t.name for t in (await client.list_tools()).tools}
            assert names == {"get_budget", "report_headroom", "post_handoff", "settle"}

            lent = await client.call_tool("post_handoff", {"goal": "finish audit", "budget_tokens": 30_000})
            assert not lent.is_error
            assert lent.structured_content["decision"] == "LEND"

            budget = await client.call_tool("get_budget", {})
            assert budget.structured_content["balance"] == 70_000

            settled = await client.call_tool("settle", {"loan_id": lent.structured_content["loan_id"]})
            assert settled.structured_content["status"] == "settled"

    asyncio.run(run())


def test_a_resent_post_handoff_over_mcp_gets_the_first_loan(broker):
    async def run():
        async with Client(build_server(broker, "auditor-01")) as client:
            tools = {t.name: t for t in (await client.list_tools()).tools}
            assert "request_id" in tools["post_handoff"].input_schema["properties"]
            ask = {"goal": "finish audit", "budget_tokens": 30_000, "request_id": "job-1/borrow-1"}
            first = (await client.call_tool("post_handoff", ask)).structured_content
            again = (await client.call_tool("post_handoff", ask)).structured_content
            return first, again

    first, again = asyncio.run(run())
    assert again["loan_id"] == first["loan_id"] and again["replayed"] is True
    assert len(broker.ledger.loans()) == 1


def test_an_agent_cannot_settle_someone_elses_loan(broker):
    loan_id = broker.post_handoff("auditor-01", HandoffRequest(goal="x", budget_tokens=10_000))["loan_id"]

    async def run():
        async with Client(build_server(broker, "writer-03")) as client:
            result = await client.call_tool("settle", {"loan_id": loan_id})
            assert result.is_error

    asyncio.run(run())


def test_mcp_server_runs_as_its_own_process(db_path, demo, scenario_path, clock):
    """What an agent harness does: launch the server over stdio with the agent's identity."""
    scenario.seed(Ledger(db_path), demo, clock())
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "rebbi.mcp_server"],
        env={**os.environ, "REBBI_AGENT_ID": "auditor-01", "REBBI_DB": str(db_path),
             "REBBI_SCENARIO": str(scenario_path)},
        cwd=str(ROOT),
    )

    async def run():
        async with Client(params) as client:
            r = await client.call_tool("post_handoff", {"goal": "finish audit", "budget_tokens": 30_000})
            return r.structured_content

    response = asyncio.run(run())
    assert (response["decision"], response["from"], response["tokens"]) == ("LEND", "analyst-07", 30_000)
    assert Ledger(db_path).balance("auditor-01") == 70_000


def test_gateway_check_and_debit(broker):
    http = TestClient(create_app(broker))
    assert http.get("/gateway/check/auditor-01").json() == {"agent_id": "auditor-01", "allowed": True,
                                                             "balance": 40_000}
    assert http.post("/gateway/usage", json={"agent_id": "auditor-01", "tokens": 40_000}).json()["balance"] == 0
    assert http.get("/gateway/check/auditor-01").json()["allowed"] is False
    assert http.get("/gateway/check/nobody").status_code == 404
    assert http.get("/invariants").json() == {"ok": True, "problems": []}
    assert {a["agent_id"] for a in http.get("/agents").json()} == {"auditor-01", "analyst-07", "writer-03"}
