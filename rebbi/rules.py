"""Lending rules: who can lend, how much, and who is asked first.

These are stand-ins until Pietro's spec lands (task 3). The numbers live in
config/scenario.toml; this module only holds the logic that uses them.
"""

from __future__ import annotations

from dataclasses import dataclass

from rebbi.ledger import AgentState


@dataclass(frozen=True)
class LendingRules:
    max_loan_tokens: int  # cap on any single loan
    min_loan_tokens: int  # smaller offers are not worth booking
    loan_ttl_s: int  # a loan's extra allowance stops after this long


@dataclass(frozen=True)
class Offer:
    lender: str
    tokens: int


def lendable(agent: AgentState) -> int:
    """Tokens an agent can lend without touching its reserve, the demand its owner declared, or tokens it borrowed."""
    if not agent.will_lend:
        return 0
    # Borrowed tokens are never lent on: a borrower that also lends could otherwise pass a loan
    # along (found by the HW9 review). The agent's own tokens stay lendable above its reserve.
    return max(0, agent.balance - agent.borrowed_tokens - agent.reserve_tokens - agent.expected_demand_tokens)


def rank_lenders(
    candidates: list[AgentState], needed: int, rules: LendingRules
) -> tuple[list[Offer], list[dict[str, object]]]:
    """Offers in the order to try them (most room first), plus why each candidate was or was not picked."""
    offers: list[Offer] = []
    considered: list[dict[str, object]] = []
    for agent in sorted(candidates, key=lendable, reverse=True):
        room = lendable(agent)
        if not agent.will_lend:
            reason = "refuses to lend"
        elif room == 0:
            reason = "no room above its reserve"
        elif room < rules.min_loan_tokens:
            reason = f"only {room} tokens above its reserve, under the {rules.min_loan_tokens} minimum"
        else:
            tokens = min(needed, room, rules.max_loan_tokens)
            offers.append(Offer(agent.agent_id, tokens))
            reason = f"can lend {tokens}"
        considered.append({"agent": agent.agent_id, "lendable": room, "reason": reason})
    return offers, considered
