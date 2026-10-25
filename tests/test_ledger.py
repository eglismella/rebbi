import sqlite3
import threading
from datetime import timedelta

import pytest

from rebbi.ledger import InsufficientHeadroom, Ledger, LedgerError
from rebbi.rules import lendable


def register(ledger, clock, agent_id, budget, reserve=0, demand=0, will_lend=True):
    return ledger.register_agent(agent_id, "team", budget, reserve, demand, will_lend, clock())


def book(ledger, clock, lender, borrower, tokens):
    return ledger.book_loan(lender, borrower, tokens, clock(), clock() + timedelta(minutes=15), lendable)


def test_balance_is_grants_minus_usage(ledger, clock):
    register(ledger, clock, "a", 1000)
    ledger.record_usage("a", 300, clock())
    assert ledger.balance("a") == 700
    assert ledger.check_invariants(clock()) == []


def test_agent_cannot_be_registered_twice(ledger, clock):
    register(ledger, clock, "a", 1000)
    with pytest.raises(LedgerError):
        register(ledger, clock, "a", 1000)


def test_loan_moves_tokens_and_records_lender_reserve(ledger, clock):
    register(ledger, clock, "lender", 1000, reserve=600)
    register(ledger, clock, "borrower", 0)
    loan = book(ledger, clock, "lender", "borrower", 400)
    assert ledger.balance("lender") == 600
    assert ledger.balance("borrower") == 400
    assert loan["lender_balance_after"] == 600 and loan["lender_reserve"] == 600


def test_loan_that_would_dip_into_reserve_is_refused(ledger, clock):
    register(ledger, clock, "lender", 1000, reserve=600)
    register(ledger, clock, "borrower", 0)
    with pytest.raises(InsufficientHeadroom):
        book(ledger, clock, "lender", "borrower", 401)
    assert ledger.balance("lender") == 1000


def test_closing_returns_only_what_the_borrower_has_not_spent(ledger, clock):
    register(ledger, clock, "lender", 1000)
    register(ledger, clock, "borrower", 100)
    loan = book(ledger, clock, "lender", "borrower", 500)
    ledger.record_usage("borrower", 250, clock())  # spends its own 100 first, then 150 of the loan
    closed = ledger.close_loan(loan["loan_id"], "settled", clock())
    assert closed["returned_tokens"] == 350
    assert ledger.balance("lender") == 850
    assert ledger.balance("borrower") == 0
    assert ledger.check_invariants(clock()) == []


def test_a_loan_closes_only_once(ledger, clock):
    register(ledger, clock, "lender", 1000)
    register(ledger, clock, "borrower", 0)
    loan = book(ledger, clock, "lender", "borrower", 100)
    ledger.close_loan(loan["loan_id"], "settled", clock())
    with pytest.raises(LedgerError):
        ledger.close_loan(loan["loan_id"], "expired", clock())


def test_loans_expire(ledger, clock):
    register(ledger, clock, "lender", 1000)
    register(ledger, clock, "borrower", 0)
    book(ledger, clock, "lender", "borrower", 100)
    clock.advance(14 * 60)
    assert ledger.expire_loans(clock()) == []
    clock.advance(60)
    [expired] = ledger.expire_loans(clock())
    assert expired["status"] == "expired" and expired["returned_tokens"] == 100
    assert ledger.check_invariants(clock()) == []


def test_two_processes_cannot_book_the_same_capacity(db_path, clock):
    setup = Ledger(db_path)
    register(setup, clock, "lender", 100_000, reserve=40_000)  # 60k lendable
    register(setup, clock, "b1", 0)
    register(setup, clock, "b2", 0)

    barrier = threading.Barrier(2)
    outcomes = []

    def borrow(borrower):
        own = Ledger(db_path)  # separate connection, as a separate MCP server process would have
        barrier.wait()
        try:
            book(own, clock, "lender", borrower, 50_000)
            outcomes.append("booked")
        except InsufficientHeadroom:
            outcomes.append("refused")
        own.close()

    threads = [threading.Thread(target=borrow, args=(b,)) for b in ("b1", "b2")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(outcomes) == ["booked", "refused"]
    assert setup.balance("lender") == 50_000
    assert setup.check_invariants(clock()) == []


def test_invariant_check_catches_tampering(ledger, clock, db_path):
    register(ledger, clock, "lender", 1000, reserve=600)
    register(ledger, clock, "borrower", 0)
    book(ledger, clock, "lender", "borrower", 400)
    raw = sqlite3.connect(db_path)
    raw.execute("INSERT INTO entries (agent_id, kind, tokens, loan_id, at) VALUES ('borrower', 'loan_in', 500, 1, 'x')")
    raw.execute("UPDATE loans SET lender_balance_after = 100")
    raw.commit()
    raw.close()
    problems = ledger.check_invariants(clock())
    assert any("fleet total" in p for p in problems)
    assert any("do not cancel" in p for p in problems)
    assert any("below its reserve" in p for p in problems)
