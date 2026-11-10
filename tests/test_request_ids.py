"""Retries are safe: a request_id makes post_handoff answer once, and settle can be resent.

Found by the Nanda Town integration (HW8): when Town dropped Rebbi's reply and the agent resent
its request, or delivered the same request twice, Rebbi booked a second loan for one job, and
nothing settled it. `rebbi check` still passed, because each loan on its own was sound.
"""

import sqlite3
import threading

import pytest

from rebbi.broker import Broker, HandoffRequest, RequestConflict
from rebbi.ledger import Ledger, LedgerError

AUDIT = dict(goal="finish dependency audit, sections 4-7", job_template="dep-audit-v1")


def ask(broker, tokens, request_id="", requester="auditor-01", **extra):
    request = HandoffRequest(budget_tokens=tokens, request_id=request_id, **{**AUDIT, **extra})
    return broker.post_handoff(requester, request)


def test_a_resent_request_gets_the_first_loan_back(broker):
    first = ask(broker, 30_000, "job-1/borrow-1")
    again = ask(broker, 30_000, "job-1/borrow-1")
    assert first["decision"] == again["decision"] == "LEND"
    assert again["loan_id"] == first["loan_id"]
    assert again["replayed"] is True and "replayed" not in first
    assert again["loan_status"] == "active"
    assert len(broker.ledger.loans()) == 1
    assert broker.ledger.balance("auditor-01") == 70_000
    assert len(broker.ledger.decisions()) == 1


def test_a_replay_reports_what_became_of_the_loan(broker):
    first = ask(broker, 30_000, "r-1")
    broker.settle("auditor-01", first["loan_id"])
    again = ask(broker, 30_000, "r-1")
    assert (again["loan_id"], again["loan_status"]) == (first["loan_id"], "settled")
    assert len(broker.ledger.loans()) == 1


def test_a_resent_refusal_is_replayed_and_a_new_attempt_needs_a_new_id(broker):
    broker.report_headroom("analyst-07", reserve_tokens=80_000, will_lend=False)
    assert ask(broker, 30_000, "r-1")["decision"] == "CANNOT_MOVE"
    broker.report_headroom("analyst-07", reserve_tokens=80_000, will_lend=True)
    again = ask(broker, 30_000, "r-1")
    assert (again["decision"], again["replayed"]) == ("CANNOT_MOVE", True)
    assert ask(broker, 30_000, "r-2")["decision"] == "LEND"


def test_the_same_id_with_a_different_request_is_refused(broker):
    ask(broker, 30_000, "r-1")
    with pytest.raises(RequestConflict):
        ask(broker, 40_000, "r-1")
    assert len(broker.ledger.loans()) == 1
    assert len(broker.ledger.decisions()) == 1


def test_request_ids_are_per_requester(broker):
    a = ask(broker, 30_000, "r-1", requester="auditor-01")
    b = ask(broker, 30_000, "r-1", requester="writer-03")
    assert a["loan_id"] != b["loan_id"]
    assert "replayed" not in b


def test_without_a_request_id_every_call_is_a_new_request(broker):
    assert ask(broker, 30_000)["loan_id"] != ask(broker, 30_000)["loan_id"]


def test_an_overlong_request_id_is_refused(broker):
    with pytest.raises(LedgerError):
        ask(broker, 30_000, "x" * 129)
    assert broker.ledger.decisions() == []


def test_concurrent_copies_of_one_request_book_one_loan(db_path, broker, demo, clock):
    """Two MCP server processes are two connections to one SQLite file."""
    brokers = [broker] + [Broker(Ledger(db_path), demo.rules, now=clock) for _ in range(3)]
    start = threading.Barrier(len(brokers))
    answers = []

    def run(b):
        start.wait()
        answers.append(ask(b, 30_000, "job-1/borrow-1"))

    threads = [threading.Thread(target=run, args=(b,)) for b in brokers]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len({a["loan_id"] for a in answers}) == 1
    assert len(broker.ledger.loans()) == 1
    assert sum(a.get("replayed", False) for a in answers) == len(brokers) - 1


def test_settling_twice_returns_the_closed_loan(broker, clock):
    loan_id = ask(broker, 30_000)["loan_id"]
    first = broker.settle("auditor-01", loan_id)
    again = broker.settle("auditor-01", loan_id)
    assert again["already_closed"] is True and "already_closed" not in first
    assert (again["status"], again["returned_tokens"]) == ("settled", first["returned_tokens"])
    assert broker.ledger.balance("analyst-07") == 200_000
    assert broker.ledger.check_invariants(clock()) == []


def test_only_the_borrower_can_resend_a_settle(broker):
    loan_id = ask(broker, 30_000)["loan_id"]
    broker.settle("auditor-01", loan_id)
    with pytest.raises(LedgerError):
        broker.settle("writer-03", loan_id)


def test_a_ledger_from_before_request_ids_is_migrated(db_path, broker):
    ask(broker, 30_000)
    broker.ledger.close()
    old = sqlite3.connect(db_path)
    old.executescript("DROP INDEX decisions_by_request; ALTER TABLE decisions DROP COLUMN request_id;")
    old.close()
    reopened = Broker(Ledger(db_path), broker.rules, now=broker.now)
    assert reopened.ledger.decisions()[0]["request_id"] is None
    first = ask(reopened, 30_000, "r-1")
    assert ask(reopened, 30_000, "r-1")["loan_id"] == first["loan_id"]
