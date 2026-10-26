"""The whole harness, run against a scripted stand-in for the model (tests/fake_model.py).

These start the real agent CLI, the gateway and the MCP servers, so they take tens of seconds.
Skip them with `pytest -m "not integration"`.
"""

import asyncio

import pytest
from fake_model import create_fake_model

from rebbi import fleet
from rebbi.gateway import serve_in_thread

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def fake_upstream():
    port = fleet.free_port()
    serve_in_thread(create_fake_model(), port)
    return f"http://127.0.0.1:{port}"


def test_baseline_stops_when_the_budget_is_spent(fake_upstream):
    s = asyncio.run(fleet.run_fleet("baseline", {}, fake_upstream))
    assert s["finished"] is False
    assert s["stopped_by"] == "gateway refused: budget spent"
    assert s["verified"] is False
    assert s["loans"] == [] and s["decisions"] == []
    assert s["ledger_ok"] is True


def test_rebbi_lends_and_the_job_finishes_and_verifies(fake_upstream):
    s = asyncio.run(fleet.run_fleet("rebbi", {}, fake_upstream))
    assert s["finished"] is True
    assert s["verified"] is True
    assert s["ledger_ok"] is True

    [decision] = s["decisions"]
    assert decision["requester"] == "auditor-01" and decision["decision"] == "LEND"
    reasons = {c["agent"]: c["reason"] for c in decision["response"]["considered"]}
    assert reasons["writer-03"] == "no room above its reserve"

    [loan] = s["loans"]
    assert (loan["lender"], loan["status"]) == ("analyst-07", "settled")
    assert loan["lender_balance_after"] >= loan["lender_reserve"]
    assert 0 < loan["returned_tokens"] < loan["tokens"]  # it used part of the loan and gave the rest back
