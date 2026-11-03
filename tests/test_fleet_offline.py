"""The whole harness, run against a scripted stand-in for the model (rebbi/scripted_model.py).

These start the real agent CLI, the gateway and the MCP servers, so they take tens of seconds.
Skip them with `pytest -m "not integration"`.
"""

import asyncio

import pytest

from rebbi import fleet
from rebbi.gateway import serve_in_thread
from rebbi.scripted_model import BUDGETS, create_scripted_model

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def fake_upstream():
    port = fleet.free_port()
    serve_in_thread(create_scripted_model(), port)
    return f"http://127.0.0.1:{port}"


STOPPED_BY = {"api-key": "gateway refused its next call: budget too low",
              "subscription": "harness refused its next call: budget too low"}


@pytest.mark.parametrize("auth", fleet.AUTH_MODES)
def test_baseline_stops_when_the_budget_is_spent(fake_upstream, auth):
    s = asyncio.run(fleet.run_fleet("baseline", BUDGETS, fake_upstream, auth))
    assert s["finished"] is False
    assert s["stopped_by"] == STOPPED_BY[auth]
    assert s["verified"] is False
    assert s["loans"] == [] and s["decisions"] == []
    assert s["ledger_ok"] is True


def test_upfront_moves_the_expected_cost_first_and_the_job_finishes(fake_upstream):
    s = asyncio.run(fleet.run_fleet("upfront", BUDGETS, fake_upstream, "subscription"))
    assert s["upfront"] == {"from": "analyst-07", "tokens": s["hint_tokens"]}
    assert s["finished"] is True and s["verified"] is True and s["ledger_ok"] is True
    assert s["loans"] == [] and s["decisions"] == []
    budgets = {a["agent_id"]: a["balance"] + a["used"] for a in s["agents"]}
    assert budgets["auditor-01"] == BUDGETS["auditor-01"] + s["hint_tokens"]


@pytest.mark.parametrize("auth", fleet.AUTH_MODES)
def test_auto_borrow_lends_before_refusing_a_call_the_agent_did_not_ask_for(fake_upstream, auth):
    # 7,000 covers the scripted auditor's first 6,050-token call and not its second, as in the real
    # failures: the call that would carry the agent's own request is the one auto-borrow lets through.
    # The scripted audit costs 78,650 in all, more than analyst-07 has spare at 180,000, so it gets more.
    budgets = {**BUDGETS, "auditor-01": 7000, "analyst-07": 250000}
    s = asyncio.run(fleet.run_fleet("rebbi", budgets, fake_upstream, auth))
    assert s["finished"] is True and s["verified"] is True and s["ledger_ok"] is True
    first = s["decisions"][0]
    assert first["request"]["goal"].startswith(fleet.AUTO_GOAL) and first["decision"] == "LEND"
    assert all(loan["status"] == "settled" for loan in s["loans"])
    assert all(loan["lender_balance_after"] >= loan["lender_reserve"] for loan in s["loans"])


@pytest.mark.parametrize("auth", fleet.AUTH_MODES)
def test_rebbi_lends_and_the_job_finishes_and_verifies(fake_upstream, auth):
    s = asyncio.run(fleet.run_fleet("rebbi", BUDGETS, fake_upstream, auth))
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
