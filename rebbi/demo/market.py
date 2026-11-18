"""Scenario 4, the open market: lending earns a claim, borrowing draws it down.

Each agent decides its own shareable % every window. Tokens a lender's loan actually supplies (the part the
borrower spent; the unspent part is returned) earn the lender a claim of consumed x 1.05 on the pool. The
borrower's claim falls by the consumed tokens. A borrower may go into debt up to one window of its own budget;
an agent at 0% shareable cannot borrow.
"""

from __future__ import annotations

RATE = 1.05


def reserve_for(budget: int, shareable_pct: float) -> int:
    """Shareable % of budget maps onto Rebbi as the reserve: reserve = (1 - shareable) x budget."""
    return round((1 - max(0.0, min(100.0, shareable_pct)) / 100) * budget)


class Market:
    def __init__(self, budgets: dict[str, int]):
        self.budgets = dict(budgets)
        self.claims = {a: 0.0 for a in budgets}

    def borrow_limit(self, agent: str, shareable_pct: float, outstanding: int) -> int:
        """Most tokens the agent may still borrow now: claim plus one window of its budget, minus open loans."""
        if shareable_pct <= 0:
            return 0
        return max(0, int(self.claims[agent] + self.budgets[agent] - outstanding))

    def settle(self, lender: str, borrower: str, consumed: int) -> None:
        self.claims[lender] += RATE * consumed
        self.claims[borrower] -= consumed
