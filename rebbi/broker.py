"""The broker: answers an agent that is running out of budget.

The MVP answers LEND or CANNOT_MOVE. Hand-off (moving the job to another
agent) and WAIT come after HW6, behind the measurement gate in the proposal.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from rebbi import rules as lending
from rebbi.ledger import InsufficientHeadroom, Ledger, LedgerError
from rebbi.rules import LendingRules

log = logging.getLogger("rebbi.broker")


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass
class HandoffRequest:
    """What a stalled agent's harness sends; the fields follow the HW5 proposal."""

    goal: str
    budget_tokens: int
    job_template: str = ""
    source_commit: str = ""
    requires_tools: list[str] = field(default_factory=list)
    requires_scopes: list[str] = field(default_factory=list)
    context_ref: str = ""
    deadline_s: int = 0
    # The requester's own id for this request. Resending the same id with the same request returns
    # the first decision instead of booking again; "" means every call is a new request.
    request_id: str = ""


MAX_REQUEST_ID = 128


class RequestConflict(LedgerError):
    """A request_id the requester already used for a different request."""


class Broker:
    def __init__(self, ledger: Ledger, rules: LendingRules, now: Callable[[], datetime] = utcnow):
        self.ledger = ledger
        self.rules = rules
        self.now = now

    def limits(self) -> dict[str, int]:
        """The fleet's lending rules, so an agent can plan its asks instead of discovering them."""
        return {"max_loan_tokens": self.rules.max_loan_tokens, "min_loan_tokens": self.rules.min_loan_tokens,
                "loan_ttl_s": self.rules.loan_ttl_s}

    def budget(self, agent_id: str) -> dict[str, Any]:
        self.ledger.expire_loans(self.now())
        state = self.ledger.agent(agent_id)
        loans = self.ledger.loans("active")
        return {
            **state.to_dict(),
            "lendable": lending.lendable(state),
            "borrowed": [_loan_view(loan) for loan in loans if loan["borrower"] == agent_id],
            "lent": [_loan_view(loan) for loan in loans if loan["lender"] == agent_id],
            "limits": self.limits(),
        }

    def report_headroom(self, agent_id: str, reserve_tokens: int, will_lend: bool = True) -> dict[str, Any]:
        state = self.ledger.set_headroom(agent_id, reserve_tokens, will_lend, self.now())
        log.info("%s reports reserve %d, will_lend=%s", agent_id, reserve_tokens, will_lend)
        return {**state.to_dict(), "lendable": lending.lendable(state)}

    def post_handoff(self, requester: str, request: HandoffRequest) -> dict[str, Any]:
        if len(request.request_id) > MAX_REQUEST_ID:
            raise LedgerError(f"request_id is longer than {MAX_REQUEST_ID} characters")
        # One write transaction from the replay check to the logged decision: two copies of one
        # request (a retry racing the original, or two server processes) cannot both book a loan.
        with self.ledger.atomic():
            return self._post_handoff(requester, request)

    def _post_handoff(self, requester: str, request: HandoffRequest) -> dict[str, Any]:
        now = self.now()
        self.ledger.expire_loans(now)
        self.ledger.agent(requester)  # unknown agents are refused before anything is logged

        if request.request_id:
            prior = self.ledger.decision_for(requester, request.request_id)
            if prior is not None:
                return self._replay(request, prior)

        if request.budget_tokens <= 0:
            response = _cannot_move(request, "budget_tokens must be a positive number of tokens", [])
            return self._decided(requester, request, response, now)

        candidates = [a for a in self.ledger.agents() if a.agent_id != requester]
        offers, considered = lending.rank_lenders(candidates, request.budget_tokens, self.rules)
        response = None
        for offer in offers:
            try:
                loan = self.ledger.book_loan(
                    lender=offer.lender,
                    borrower=requester,
                    tokens=offer.tokens,
                    now=now,
                    expires_at=now + timedelta(seconds=self.rules.loan_ttl_s),
                    lendable=lending.lendable,
                )
            except InsufficientHeadroom:
                # Another request booked this capacity between our read and our write.
                _mark(considered, offer.lender, "capacity taken by another request")
                continue
            response = {
                "decision": "LEND",
                "loan_id": loan["loan_id"],
                "tokens": loan["tokens"],
                "requested": request.budget_tokens,
                "from": loan["lender"],
                "expires_at": loan["expires_at"],
                "lender_reserve_intact": loan["lender_balance_after"] >= loan["lender_reserve"],
                "considered": considered,
                **self._partial(request.budget_tokens, loan["tokens"]),
            }
            break
        if response is None:
            response = _cannot_move(request, "no agent has spare capacity above its reserve", considered)
        response["limits"] = self.limits()
        if request.requires_tools or request.requires_scopes:
            response["ignored_fields"] = [f for f in ("requires_tools", "requires_scopes") if getattr(request, f)]
            response["note"] = ("Rebbi lends tokens only: requires_tools and requires_scopes are recorded with the "
                                "decision but not checked, and no job is moved to another agent.")
        return self._decided(requester, request, response, now)

    def _partial(self, requested: int, lent: int) -> dict[str, Any]:
        """Say plainly when a loan covers less than the ask, and why (found by the HW9 cold-start runs)."""
        if lent >= requested:
            return {"partial": False, "shortfall_tokens": 0}
        reason = "loan cap" if lent == self.rules.max_loan_tokens else "lender room"
        why = (f"one loan is capped at {self.rules.max_loan_tokens} tokens" if reason == "loan cap"
               else "that is all the best lender has above its reserve")
        return {
            "partial": True,
            "shortfall_tokens": requested - lent,
            "limit_reason": reason,
            "next_step": (f"This loan covers {lent} of the {requested} tokens you asked for: {why}. "
                          "Ask again with a new request_id for the rest, or plan the job around the shortfall."),
        }

    def settle(self, agent_id: str, loan_id: int, outcome: str = "done") -> dict[str, Any]:
        """The borrower closes its loan; whatever it did not spend goes back to the lender."""
        if outcome not in ("done", "abandoned"):
            raise LedgerError("outcome must be 'done' or 'abandoned'")
        with self.ledger.atomic():
            loan = self.ledger.loan(loan_id)
            if loan["borrower"] != agent_id:
                raise LedgerError(f"loan {loan_id} belongs to {loan['borrower']}, not {agent_id}")
            if loan["status"] != "active":
                # Settled or expired already: a settle resent after a lost reply gets the closed loan back.
                return {**_loan_view(loan), "outcome": outcome, "already_closed": True}
            closed = self.ledger.close_loan(loan_id, "settled", self.now())
        log.info("%s settled loan %d (%s): returned %d to %s", agent_id, loan_id, outcome,
                 closed["returned_tokens"], closed["lender"])
        return {**_loan_view(closed), "outcome": outcome}

    def _replay(self, request: HandoffRequest, prior: dict[str, Any]) -> dict[str, Any]:
        if prior["request"] != asdict(request):
            raise RequestConflict(f"request_id {request.request_id!r} was already used for a different request")
        response = {**prior["response"], "decision_id": prior["decision_id"], "replayed": True}
        if "loan_id" in response:
            response["loan_status"] = self.ledger.loan(response["loan_id"])["status"]
        log.info("post_handoff from %s: request %s already answered -> %s (replayed)",
                 prior["requester"], request.request_id, response["decision"])
        return response

    def _decided(self, requester: str, request: HandoffRequest, response: dict[str, Any], now: datetime):
        response["decision_id"] = self.ledger.log_decision(requester, asdict(request), response, now)
        log.info("post_handoff from %s for %d tokens -> %s", requester, request.budget_tokens, response["decision"])
        return response


def _cannot_move(request: HandoffRequest, blocker: str, considered: list[dict[str, object]]) -> dict[str, Any]:
    return {
        "decision": "CANNOT_MOVE",
        "requested": request.budget_tokens,
        "blocker": blocker,
        "next_step": "wait and ask again, or finish on a cheaper model",
        "considered": considered,
    }


def _mark(considered: list[dict[str, object]], agent_id: str, reason: str) -> None:
    for c in considered:
        if c["agent"] == agent_id:
            c["reason"] = reason


def _loan_view(loan: dict[str, Any]) -> dict[str, Any]:
    keys = ("loan_id", "lender", "borrower", "tokens", "status", "expires_at", "returned_tokens")
    return {k: loan[k] for k in keys}
