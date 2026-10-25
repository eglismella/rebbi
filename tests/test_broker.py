import pytest

from rebbi.broker import HandoffRequest
from rebbi.ledger import LedgerError

AUDIT = dict(goal="finish dependency audit, sections 4-7", job_template="dep-audit-v1")


def ask(broker, tokens, requester="auditor-01"):
    return broker.post_handoff(requester, HandoffRequest(budget_tokens=tokens, **AUDIT))


def reasons(response):
    return {c["agent"]: c["reason"] for c in response["considered"]}


def test_lends_from_the_agent_with_room_and_skips_the_one_without(broker):
    r = ask(broker, 30_000)
    assert r["decision"] == "LEND"
    assert (r["from"], r["tokens"]) == ("analyst-07", 30_000)
    assert r["lender_reserve_intact"] is True
    assert reasons(r)["writer-03"] == "no room above its reserve"
    assert broker.ledger.balance("auditor-01") == 70_000
    assert broker.ledger.balance("analyst-07") == 170_000


def test_a_single_loan_is_capped(broker):
    r = ask(broker, 180_000)
    assert r["decision"] == "LEND"
    assert (r["tokens"], r["requested"]) == (60_000, 180_000)


def test_cannot_move_when_every_lender_refuses(broker):
    broker.report_headroom("analyst-07", reserve_tokens=80_000, will_lend=False)
    r = ask(broker, 30_000)
    assert r["decision"] == "CANNOT_MOVE"
    assert reasons(r) == {"analyst-07": "refuses to lend", "writer-03": "no room above its reserve"}
    assert broker.ledger.balance("auditor-01") == 40_000


def test_repeated_asks_never_reach_a_reserve(broker):
    lent = 0
    for _ in range(10):
        r = ask(broker, 30_000)
        if r["decision"] != "LEND":
            break
        lent += r["tokens"]
    analyst = broker.ledger.agent("analyst-07")
    # 200k budget - 80k reserve - 20k declared demand leaves 100k to lend, and no more.
    assert lent == 100_000
    assert analyst.balance == analyst.reserve_tokens + analyst.expected_demand_tokens
    assert r["decision"] == "CANNOT_MOVE"
    assert broker.ledger.check_invariants(broker.now()) == []


def test_raising_the_reserve_shrinks_what_can_be_lent(broker):
    broker.report_headroom("analyst-07", reserve_tokens=170_000)
    r = ask(broker, 30_000)
    assert (r["decision"], r["tokens"]) == ("LEND", 10_000)


def test_settle_returns_unspent_tokens(broker, clock):
    r = ask(broker, 30_000)
    broker.ledger.record_usage("auditor-01", 55_000, clock())  # its own 40k, then 15k of the loan
    s = broker.settle("auditor-01", r["loan_id"])
    assert s["returned_tokens"] == 15_000
    assert broker.ledger.balance("analyst-07") == 185_000
    assert broker.ledger.check_invariants(clock()) == []


def test_only_the_borrower_can_settle(broker):
    r = ask(broker, 30_000)
    with pytest.raises(LedgerError):
        broker.settle("writer-03", r["loan_id"])


def test_an_expired_loan_stops_the_extra_allowance(broker, clock):
    ask(broker, 30_000)
    clock.advance(broker.rules.loan_ttl_s)
    budget = broker.budget("auditor-01")
    assert budget["balance"] == 40_000 and budget["borrowed"] == []
    assert broker.ledger.check_invariants(clock()) == []


def test_every_decision_is_logged(broker):
    ask(broker, 30_000)
    ask(broker, 0)
    logged = broker.ledger.decisions()
    assert [d["decision"] for d in logged] == ["LEND", "CANNOT_MOVE"]
    assert logged[0]["request"]["goal"] == AUDIT["goal"]


def test_unknown_agents_are_refused(broker):
    with pytest.raises(LedgerError):
        ask(broker, 30_000, requester="intruder-99")
    assert broker.ledger.decisions() == []
