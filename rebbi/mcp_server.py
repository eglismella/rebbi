"""Rebbi's agent-facing interface: an MCP server, one stdio process per agent.

The agent's harness launches it with REBBI_AGENT_ID set, so an agent always
speaks as itself: no tool takes an agent id, and none can act for another agent.

    REBBI_AGENT_ID=auditor-01 REBBI_DB=rebbi.db python -m rebbi.mcp_server
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer

from rebbi import scenario
from rebbi.broker import Broker, HandoffRequest
from rebbi.ledger import Ledger

INSTRUCTIONS = """Rebbi lends spare token budget between agents in your fleet.
Call get_budget to see what you have left. When you are about to run out in the
middle of a job, call post_handoff with the tokens you need to finish: a LEND
reply means the tokens are already in your budget, so carry on. When the job is
done, call settle with the loan_id so unspent tokens go back to the lender."""


def build_server(broker: Broker, agent_id: str) -> MCPServer:
    broker.ledger.agent(agent_id)  # fail at start-up, not on the first call
    server = MCPServer(name="rebbi", instructions=INSTRUCTIONS)

    @server.tool()
    def get_budget() -> dict[str, Any]:
        """Your remaining token budget, your published reserve, and the loans you hold or have given."""
        return broker.budget(agent_id)

    @server.tool()
    def report_headroom(reserve_tokens: int, will_lend: bool = True) -> dict[str, Any]:
        """Publish the reserve you will never lend, and whether you lend at all.

        Other agents can borrow only what sits above your reserve and above the
        demand your owner declared for this window.
        """
        return broker.report_headroom(agent_id, reserve_tokens, will_lend)

    @server.tool()
    def post_handoff(
        goal: str,
        budget_tokens: int,
        job_template: str = "",
        source_commit: str = "",
        requires_tools: list[str] | None = None,
        requires_scopes: list[str] | None = None,
        context_ref: str = "",
        deadline_s: int = 0,
    ) -> dict[str, Any]:
        """Ask for the tokens you need to finish a job you cannot finish within your budget.

        Returns decision LEND (the tokens are already added to your budget; keep
        working and call settle when done) or CANNOT_MOVE (with the blocker and
        what each possible lender said).
        """
        request = HandoffRequest(
            goal=goal,
            budget_tokens=budget_tokens,
            job_template=job_template,
            source_commit=source_commit,
            requires_tools=requires_tools or [],
            requires_scopes=requires_scopes or [],
            context_ref=context_ref,
            deadline_s=deadline_s,
        )
        return broker.post_handoff(agent_id, request)

    @server.tool()
    def settle(loan_id: int, outcome: Literal["done", "abandoned"] = "done") -> dict[str, Any]:
        """Close a loan you borrowed once the job is done or abandoned; unspent tokens go back to the lender."""
        return broker.settle(agent_id, loan_id, outcome)

    return server


def main() -> None:
    # stdout carries the MCP protocol, so logs go to stderr.
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    agent_id = os.environ.get("REBBI_AGENT_ID")
    if not agent_id:
        sys.exit("REBBI_AGENT_ID is not set: the harness must say which agent this server speaks for")
    sc = scenario.load(os.environ.get("REBBI_SCENARIO", scenario.DEFAULT_SCENARIO))
    broker = Broker(Ledger(os.environ.get("REBBI_DB", "rebbi.db")), sc.rules)
    build_server(broker, agent_id).run("stdio")


if __name__ == "__main__":
    main()
