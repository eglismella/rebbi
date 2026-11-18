"""Regression tests for the HW9 fix: every reply says why (docs/hw9/RESULTS.md).

Before the fix a 100,000-token ask under a 60,000 cap came back as a plain LEND for 60,000,
refusals reached the agent as a bare "Error executing tool <name>", and requires_tools was
dropped without a word. The cold-start agents coped only because the doc warned them.
"""

import asyncio
import json

from mcp import Client

from rebbi.__main__ import main as cli
from rebbi.broker import HandoffRequest
from rebbi.mcp_server import build_server


def ask(broker, tokens, **extra):
    return broker.post_handoff("auditor-01", HandoffRequest(goal="audit", budget_tokens=tokens, **extra))


def test_an_over_cap_ask_is_flagged_partial_with_the_reason(broker):
    r = ask(broker, 100_000)
    assert (r["decision"], r["tokens"], r["partial"]) == ("LEND", 60_000, True)
    assert (r["shortfall_tokens"], r["limit_reason"]) == (40_000, "loan cap")
    assert "new request_id" in r["next_step"]


def test_a_loan_cut_by_lender_room_says_so(broker):
    ask(broker, 60_000, request_id="a")  # analyst-07 lendable 100,000 in the test fleet: 40,000 left
    r = ask(broker, 60_000, request_id="b")
    assert (r["tokens"], r["partial"], r["limit_reason"]) == (40_000, True, "lender room")
    assert r["shortfall_tokens"] == 20_000


def test_a_full_loan_is_not_partial(broker):
    r = ask(broker, 30_000)
    assert (r["partial"], r["shortfall_tokens"]) == (False, 0)
    assert "limit_reason" not in r and "next_step" not in r


def test_limits_are_in_every_reply_and_in_get_budget(broker):
    limits = {"max_loan_tokens": 60_000, "min_loan_tokens": 5_000, "loan_ttl_s": 900}
    assert ask(broker, 30_000)["limits"] == limits
    assert broker.budget("auditor-01")["limits"] == limits
    broker.report_headroom("analyst-07", 200_000)
    assert ask(broker, 30_000)["decision"] == "CANNOT_MOVE"
    assert ask(broker, 30_000)["limits"] == limits


def test_fields_rebbi_does_not_check_are_named(broker):
    r = ask(broker, 10_000, requires_tools=["sql.read"])
    assert r["ignored_fields"] == ["requires_tools"] and "not checked" in r["note"]
    assert "ignored_fields" not in ask(broker, 10_000)


def test_a_replay_still_returns_the_first_decision_with_the_new_fields(broker):
    first = ask(broker, 100_000, request_id="x")
    again = ask(broker, 100_000, request_id="x")
    assert again["replayed"] is True and again["loan_id"] == first["loan_id"]
    assert again["partial"] is True and len(broker.ledger.loans()) == 1


def _mcp(broker, *calls):
    server = build_server(broker, "auditor-01")

    async def run():
        async with Client(server) as client:
            return [await client.call_tool(tool, args) for tool, args in calls]

    return asyncio.run(run())


def test_refusals_reach_the_agent_with_their_reason(broker):
    (unknown,) = _mcp(broker, ("settle", {"loan_id": 999}))
    assert unknown.is_error and "no loan 999" in unknown.content[0].text
    first, conflict = _mcp(broker,
                           ("post_handoff", {"goal": "b", "budget_tokens": 5_000, "request_id": "dup"}),
                           ("post_handoff", {"goal": "c", "budget_tokens": 5_000, "request_id": "dup"}))
    assert not first.is_error
    assert conflict.is_error and "already used for a different request" in conflict.content[0].text


def test_the_partial_flag_arrives_over_mcp(broker):
    (r,) = _mcp(broker, ("post_handoff", {"goal": "audit", "budget_tokens": 100_000}))
    assert r.structured_content["partial"] is True


def test_rebbi_call_from_a_shell(tmp_path, capsys, monkeypatch):
    cli(["init", str(tmp_path / "fleet")])
    capsys.readouterr()
    cli(["client-config", "--dir", str(tmp_path / "fleet"), "--agent", "auditor-01"])
    (tmp_path / ".mcp.json").write_text(capsys.readouterr().out)
    monkeypatch.chdir(tmp_path)
    assert cli(["call", "post_handoff", '{"goal": "audit", "budget_tokens": 30000}']) == 0
    assert json.loads(capsys.readouterr().out)["decision"] == "LEND"
    assert cli(["call", "settle", '{"loan_id": 42}']) == 1
    assert "no loan 42" in json.loads(capsys.readouterr().out)["error"]


# Found by the independent review of the HW9 write-up (docs/hw9/RESULTS.md, "Review"), fixed after the runs.

def test_a_non_positive_ask_also_carries_limits(broker):
    r = ask(broker, 0)
    assert r["decision"] == "CANNOT_MOVE" and "limits" in r


def test_report_headroom_carries_limits(broker):
    assert "limits" in broker.report_headroom("analyst-07", 80_000)


def test_settling_an_expired_loan_says_it_expired(broker, clock):
    loan_id = ask(broker, 30_000)["loan_id"]
    clock.advance(10_000)  # past loan_ttl_s
    r = broker.settle("auditor-01", loan_id)
    assert (r["status"], r["already_closed"]) == ("expired", True)


def test_init_force_keeps_the_edited_fleet_file_and_tokens(tmp_path, capsys):
    fleet = tmp_path / "fleet"
    cli(["init", str(fleet)])
    edited = (fleet / "scenario.toml").read_text().replace("max_loan_tokens = 60000", "max_loan_tokens = 40000")
    (fleet / "scenario.toml").write_text(edited)
    before = (fleet / "tokens.toml").read_text()
    assert cli(["init", str(fleet), "--force"]) == 0
    assert "max_loan_tokens = 40000" in (fleet / "scenario.toml").read_text()
    assert (fleet / "tokens.toml").read_text() == before
    assert cli(["init", str(fleet), "--force", "--new-tokens"]) == 0
    assert (fleet / "tokens.toml").read_text() != before


def test_rebbi_call_reports_an_unreachable_server_as_json(tmp_path, capsys, monkeypatch):
    (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {"rebbi": {
        "type": "http", "url": "http://127.0.0.1:9/mcp", "headers": {}}}}))
    monkeypatch.chdir(tmp_path)
    assert cli(["call", "get_budget"]) == 2
    assert "could not reach Rebbi" in json.loads(capsys.readouterr().out)["error"]


def test_borrowed_tokens_are_never_lent_on(broker):
    ask(broker, 30_000)  # auditor-01: 40,000 own + 30,000 borrowed
    broker.report_headroom("auditor-01", reserve_tokens=0, will_lend=True)
    me = broker.budget("auditor-01")
    assert (me["borrowed_tokens"], me["lendable"]) == (30_000, 40_000)
    broker.report_headroom("analyst-07", 200_000)  # only auditor-01 is left as a lender
    r = broker.post_handoff("writer-03", HandoffRequest(goal="x", budget_tokens=60_000))
    assert (r["from"], r["tokens"]) == ("auditor-01", 40_000)


def test_the_fleet_file_next_to_the_ledger_is_used(tmp_path):
    from rebbi import scenario as sc

    cli(["init", str(tmp_path / "fleet")])
    path, why = sc.for_ledger(tmp_path / "fleet" / "rebbi.db")
    assert (path, why) == ((tmp_path / "fleet" / "scenario.toml").resolve(), "next to the ledger")
    assert sc.for_ledger(tmp_path / "fleet" / "rebbi.db", "/x/given.toml")[1] == "given"


def test_the_operator_api_needs_its_token(broker, monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from rebbi.api import app_from_env, create_app

    http = TestClient(create_app(broker, token="s3cret-operator-token"))
    assert http.post("/gateway/usage", json={"agent_id": "auditor-01", "tokens": 5}).status_code == 401
    ok = http.get("/agents", headers={"Authorization": "Bearer s3cret-operator-token"})
    assert ok.status_code == 200
    monkeypatch.delenv("REBBI_API_TOKEN", raising=False)
    monkeypatch.delenv("REBBI_API_NO_AUTH", raising=False)
    monkeypatch.setenv("REBBI_DB", str(tmp_path / "x.db"))
    import pytest
    with pytest.raises(RuntimeError):
        app_from_env()
