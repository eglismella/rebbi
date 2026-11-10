"""The ledger: the one home for budgets, reserves, loans and usage.

Balances are never stored; they are the sum of an append-only list of entries.
Every write runs in a `BEGIN IMMEDIATE` transaction, so the MCP server
processes (one per agent) and the gateway can share one SQLite file without
two of them booking the same spare capacity.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    agent_id               TEXT PRIMARY KEY,
    owner                  TEXT NOT NULL,
    reserve_tokens         INTEGER NOT NULL CHECK (reserve_tokens >= 0),
    expected_demand_tokens INTEGER NOT NULL CHECK (expected_demand_tokens >= 0),
    will_lend              INTEGER NOT NULL CHECK (will_lend IN (0, 1)),
    updated_at             TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS loans (
    loan_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    lender                TEXT NOT NULL REFERENCES agents(agent_id),
    borrower              TEXT NOT NULL REFERENCES agents(agent_id),
    tokens                INTEGER NOT NULL CHECK (tokens > 0),
    status                TEXT NOT NULL CHECK (status IN ('active', 'settled', 'expired')),
    lender_balance_after  INTEGER NOT NULL,
    lender_reserve        INTEGER NOT NULL,
    created_at            TEXT NOT NULL,
    expires_at            TEXT NOT NULL,
    closed_at             TEXT,
    returned_tokens       INTEGER,
    CHECK (lender <> borrower)
);

CREATE TABLE IF NOT EXISTS entries (
    entry_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id  TEXT NOT NULL REFERENCES agents(agent_id),
    kind      TEXT NOT NULL CHECK (kind IN ('grant', 'usage', 'loan_out', 'loan_in', 'return_out', 'return_in')),
    tokens    INTEGER NOT NULL,
    loan_id   INTEGER REFERENCES loans(loan_id),
    note      TEXT,
    at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS entries_by_agent ON entries(agent_id);

CREATE TABLE IF NOT EXISTS decisions (
    decision_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    requester     TEXT NOT NULL,
    decision      TEXT NOT NULL,
    request_json  TEXT NOT NULL,
    response_json TEXT NOT NULL,
    at            TEXT NOT NULL,
    request_id    TEXT  -- the requester's own id for a request it may resend; NULL if it gave none
);
"""

# Run after SCHEMA, so a ledger created before request ids gains the column first.
MIGRATIONS = """
CREATE UNIQUE INDEX IF NOT EXISTS decisions_by_request ON decisions(requester, request_id)
    WHERE request_id IS NOT NULL;
"""

LOAN_KINDS = ("loan_out", "loan_in", "return_out", "return_in")


class LedgerError(Exception):
    pass


class UnknownAgent(LedgerError):
    pass


class InsufficientHeadroom(LedgerError):
    """The lender no longer has the capacity: someone else booked it first."""


@dataclass(frozen=True)
class AgentState:
    agent_id: str
    owner: str
    balance: int
    reserve_tokens: int
    expected_demand_tokens: int
    will_lend: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stamp(t: datetime) -> str:
    """One timestamp format everywhere, so string order is time order."""
    return t.isoformat(timespec="seconds")


class Ledger:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, isolation_level=None, timeout=10, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(SCHEMA)
        columns = {r["name"] for r in self._conn.execute("PRAGMA table_info(decisions)")}
        if "request_id" not in columns:
            self._conn.execute("ALTER TABLE decisions ADD COLUMN request_id TEXT")
        self._conn.executescript(MIGRATIONS)
        self._in_tx = False

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            if self._in_tx:
                # Inside atomic(): the outer transaction commits or rolls back for both.
                yield self._conn
                return
            self._conn.execute("BEGIN IMMEDIATE")
            self._in_tx = True
            try:
                yield self._conn
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
            else:
                self._conn.execute("COMMIT")
            finally:
                self._in_tx = False

    def atomic(self) -> AbstractContextManager[sqlite3.Connection]:
        """One write transaction around several ledger calls, held against every other process."""
        return self._tx()

    def _read(self, sql: str, args: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, args).fetchall()

    # -- agents ---------------------------------------------------------------

    def register_agent(
        self,
        agent_id: str,
        owner: str,
        budget_tokens: int,
        reserve_tokens: int,
        expected_demand_tokens: int,
        will_lend: bool,
        now: datetime,
    ) -> AgentState:
        with self._tx() as c:
            if c.execute("SELECT 1 FROM agents WHERE agent_id = ?", (agent_id,)).fetchone():
                raise LedgerError(f"agent {agent_id} is already registered")
            c.execute(
                "INSERT INTO agents VALUES (?, ?, ?, ?, ?, ?)",
                (agent_id, owner, reserve_tokens, expected_demand_tokens, int(will_lend), stamp(now)),
            )
            c.execute(
                "INSERT INTO entries (agent_id, kind, tokens, note, at) VALUES (?, 'grant', ?, 'initial budget', ?)",
                (agent_id, budget_tokens, stamp(now)),
            )
            return self._agent(c, agent_id)

    def set_headroom(self, agent_id: str, reserve_tokens: int, will_lend: bool, now: datetime) -> AgentState:
        """What an agent publishes about itself: the reserve it never lends, and whether it lends at all."""
        if reserve_tokens < 0:
            raise LedgerError("reserve_tokens cannot be negative")
        with self._tx() as c:
            self._agent(c, agent_id)
            c.execute(
                "UPDATE agents SET reserve_tokens = ?, will_lend = ?, updated_at = ? WHERE agent_id = ?",
                (reserve_tokens, int(will_lend), stamp(now), agent_id),
            )
            return self._agent(c, agent_id)

    def agent(self, agent_id: str) -> AgentState:
        with self._lock:
            return self._agent(self._conn, agent_id)

    def agents(self) -> list[AgentState]:
        rows = self._read("SELECT agent_id FROM agents ORDER BY agent_id")
        return [self.agent(r["agent_id"]) for r in rows]

    def balance(self, agent_id: str) -> int:
        return self.agent(agent_id).balance

    def _agent(self, c: sqlite3.Connection, agent_id: str) -> AgentState:
        row = c.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,)).fetchone()
        if row is None:
            raise UnknownAgent(agent_id)
        balance = c.execute(
            "SELECT COALESCE(SUM(tokens), 0) FROM entries WHERE agent_id = ?", (agent_id,)
        ).fetchone()[0]
        return AgentState(
            agent_id=row["agent_id"],
            owner=row["owner"],
            balance=balance,
            reserve_tokens=row["reserve_tokens"],
            expected_demand_tokens=row["expected_demand_tokens"],
            will_lend=bool(row["will_lend"]),
        )

    # -- usage (written by the gateway) ---------------------------------------

    def record_usage(self, agent_id: str, tokens: int, now: datetime, note: str = "") -> AgentState:
        if tokens < 0:
            raise LedgerError("usage cannot be negative")
        with self._tx() as c:
            self._agent(c, agent_id)
            c.execute(
                "INSERT INTO entries (agent_id, kind, tokens, note, at) VALUES (?, 'usage', ?, ?, ?)",
                (agent_id, -tokens, note, stamp(now)),
            )
            return self._agent(c, agent_id)

    def last_usage(self, agent_id: str) -> int:
        """Tokens the agent's most recent model call used; 0 before its first call."""
        rows = self._read(
            "SELECT -tokens AS t FROM entries WHERE agent_id = ? AND kind = 'usage' ORDER BY entry_id DESC LIMIT 1",
            (agent_id,),
        )
        return rows[0]["t"] if rows else 0

    def used(self, agent_id: str) -> int:
        rows = self._read("SELECT COALESCE(-SUM(tokens), 0) AS t FROM entries WHERE agent_id = ? AND kind = 'usage'",
                          (agent_id,))
        return rows[0]["t"]

    # -- loans ----------------------------------------------------------------

    def book_loan(
        self,
        lender: str,
        borrower: str,
        tokens: int,
        now: datetime,
        expires_at: datetime,
        lendable: Callable[[AgentState], int],
    ) -> dict[str, Any]:
        """Move `tokens` from lender to borrower, re-checking the lender's headroom inside the transaction."""
        if tokens <= 0:
            raise LedgerError("a loan must be positive")
        with self._tx() as c:
            state = self._agent(c, lender)
            self._agent(c, borrower)
            if tokens > lendable(state):
                raise InsufficientHeadroom(f"{lender} can no longer lend {tokens} tokens")
            cur = c.execute(
                """INSERT INTO loans (lender, borrower, tokens, status, lender_balance_after, lender_reserve,
                                      created_at, expires_at)
                   VALUES (?, ?, ?, 'active', ?, ?, ?, ?)""",
                (lender, borrower, tokens, state.balance - tokens, state.reserve_tokens, stamp(now), stamp(expires_at)),
            )
            loan_id = cur.lastrowid
            c.executemany(
                "INSERT INTO entries (agent_id, kind, tokens, loan_id, at) VALUES (?, ?, ?, ?, ?)",
                [
                    (lender, "loan_out", -tokens, loan_id, stamp(now)),
                    (borrower, "loan_in", tokens, loan_id, stamp(now)),
                ],
            )
            return self._loan(c, loan_id)

    def close_loan(self, loan_id: int, status: str, now: datetime) -> dict[str, Any]:
        with self._tx() as c:
            return self._close(c, self._loan(c, loan_id), status, now)

    def expire_loans(self, now: datetime) -> list[dict[str, Any]]:
        """Stop the extra allowance of every loan past its expiry."""
        with self._tx() as c:
            due = c.execute(
                "SELECT loan_id FROM loans WHERE status = 'active' AND expires_at <= ?", (stamp(now),)
            ).fetchall()
            return [self._close(c, self._loan(c, r["loan_id"]), "expired", now) for r in due]

    def _close(self, c: sqlite3.Connection, loan: dict[str, Any], status: str, now: datetime) -> dict[str, Any]:
        if status not in ("settled", "expired"):
            raise LedgerError(f"cannot close a loan as {status!r}")
        if loan["status"] != "active":
            raise LedgerError(f"loan {loan['loan_id']} is already {loan['status']}")
        # Spent tokens are gone. What the borrower has not spent goes back, up to the loan amount.
        borrower_balance = self._agent(c, loan["borrower"]).balance
        returned = max(0, min(borrower_balance, loan["tokens"]))
        if returned:
            c.executemany(
                "INSERT INTO entries (agent_id, kind, tokens, loan_id, at) VALUES (?, ?, ?, ?, ?)",
                [
                    (loan["borrower"], "return_out", -returned, loan["loan_id"], stamp(now)),
                    (loan["lender"], "return_in", returned, loan["loan_id"], stamp(now)),
                ],
            )
        c.execute(
            "UPDATE loans SET status = ?, closed_at = ?, returned_tokens = ? WHERE loan_id = ?",
            (status, stamp(now), returned, loan["loan_id"]),
        )
        return self._loan(c, loan["loan_id"])

    def loan(self, loan_id: int) -> dict[str, Any]:
        with self._lock:
            return self._loan(self._conn, loan_id)

    def loans(self, status: str | None = None) -> list[dict[str, Any]]:
        if status is None:
            rows = self._read("SELECT * FROM loans ORDER BY loan_id")
        else:
            rows = self._read("SELECT * FROM loans WHERE status = ? ORDER BY loan_id", (status,))
        return [dict(r) for r in rows]

    def _loan(self, c: sqlite3.Connection, loan_id: int) -> dict[str, Any]:
        row = c.execute("SELECT * FROM loans WHERE loan_id = ?", (loan_id,)).fetchone()
        if row is None:
            raise LedgerError(f"no loan {loan_id}")
        return dict(row)

    # -- decisions (the broker's audit trail) ---------------------------------

    def log_decision(
        self, requester: str, request: dict[str, Any], response: dict[str, Any], now: datetime
    ) -> int:
        """A request that names a request_id can be logged once per requester; a second copy fails."""
        with self._tx() as c:
            cur = c.execute(
                """INSERT INTO decisions (requester, decision, request_json, response_json, at, request_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (requester, response["decision"], json.dumps(request), json.dumps(response), stamp(now),
                 request.get("request_id") or None),
            )
            return cur.lastrowid

    def decision_for(self, requester: str, request_id: str) -> dict[str, Any] | None:
        """The decision already logged for this requester's request_id, if any."""
        rows = self._read(
            "SELECT decision_id FROM decisions WHERE requester = ? AND request_id = ?", (requester, request_id)
        )
        if not rows:
            return None
        return next(d for d in self.decisions() if d["decision_id"] == rows[0]["decision_id"])

    def decisions(self) -> list[dict[str, Any]]:
        rows = self._read("SELECT * FROM decisions ORDER BY decision_id")
        return [
            {
                "decision_id": r["decision_id"],
                "requester": r["requester"],
                "request_id": r["request_id"],
                "decision": r["decision"],
                "request": json.loads(r["request_json"]),
                "response": json.loads(r["response_json"]),
                "at": r["at"],
            }
            for r in rows
        ]

    # -- invariants (checked after every demo run) ----------------------------

    def check_invariants(self, now: datetime) -> list[str]:
        """Return every broken rule; an empty list means the ledger is sound."""
        problems: list[str] = []
        q = lambda sql, args=(): self._read(sql, args)  # noqa: E731

        total = q("SELECT COALESCE(SUM(tokens), 0) AS t FROM entries")[0]["t"]
        granted = q("SELECT COALESCE(SUM(tokens), 0) AS t FROM entries WHERE kind = 'grant'")[0]["t"]
        used = q("SELECT COALESCE(SUM(tokens), 0) AS t FROM entries WHERE kind = 'usage'")[0]["t"]
        if total != granted + used:
            problems.append(f"fleet total {total} != granted {granted} minus used {-used}: loans created or lost tokens")

        kinds = ",".join(f"'{k}'" for k in LOAN_KINDS)
        for r in q(f"SELECT loan_id, SUM(tokens) AS net FROM entries WHERE kind IN ({kinds}) GROUP BY loan_id"):
            if r["net"] != 0:
                problems.append(f"loan {r['loan_id']}: lender and borrower entries do not cancel (net {r['net']})")

        for loan in self.loans():
            lid = loan["loan_id"]
            if loan["lender_balance_after"] < loan["lender_reserve"]:
                problems.append(
                    f"loan {lid}: left {loan['lender']} at {loan['lender_balance_after']}, "
                    f"below its reserve of {loan['lender_reserve']}"
                )
            if loan["status"] == "active" and loan["expires_at"] <= stamp(now):
                problems.append(f"loan {lid}: still active after it expired at {loan['expires_at']}")
            if loan["status"] != "active" and (loan["returned_tokens"] is None or loan["returned_tokens"] > loan["tokens"]):
                problems.append(f"loan {lid}: returned {loan['returned_tokens']} of {loan['tokens']} tokens")
        return problems
