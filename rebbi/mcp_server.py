"""Rebbi's agent-facing interface: an MCP server.

Two ways to run it; the tools and their replies are the same in both.

stdio, one process per agent. The harness sets REBBI_AGENT_ID, so an agent always
speaks as itself: no tool takes an agent id, and none can act for another agent.

    REBBI_AGENT_ID=auditor-01 REBBI_DB=rebbi.db rebbi-mcp

Streamable HTTP, one process for the whole fleet, for agents on other machines or
clients that cannot launch a local process. Each agent sends its own bearer token;
the token file maps tokens to agent ids (`rebbi init` writes one).

    rebbi-mcp --http --port 8765 --db fleet/rebbi.db --tokens fleet/tokens.toml

REBBI_TRACE=<path> appends one JSON line per tool call (arguments and reply, or the
error) in either mode, so an operator can see exactly what an agent asked and got.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import tomllib
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from rebbi import scenario
from rebbi.broker import Broker, HandoffRequest
from rebbi.ledger import Ledger, LedgerError, UnknownAgent

log = logging.getLogger("rebbi.mcp")

INSTRUCTIONS = """Rebbi lends spare token budget between agents in your fleet.
Call get_budget to see what you have left. When you are about to run out in the
middle of a job, call post_handoff with the tokens you need to finish: a LEND
reply means the tokens are already in your budget, so carry on. When the job is
done, call settle with the loan_id so unspent tokens go back to the lender.
Give each post_handoff a request_id of your own; if you never saw the answer,
resend it with the same request_id and you get the first answer back, never a
second loan. Ask again later with a new request_id."""


class Tracer:
    """Appends one JSON line per tool call. Off when no path is given."""

    def __init__(self, path: str | os.PathLike[str] | None):
        self.path = Path(path) if path else None

    def __call__(self, agent_id: str, tool: str, arguments: dict[str, Any], fn: Callable[[], Any]) -> Any:
        entry: dict[str, Any] = {"at": datetime.now(UTC).isoformat(timespec="milliseconds"),
                                 "agent_id": agent_id, "tool": tool, "arguments": arguments}
        try:
            result = fn()
        except LedgerError as exc:
            # A refusal the agent can act on: send the reason, not the SDK's bare "Error executing tool".
            # (Before HW9's fix the reason never reached the agent.)
            entry["error"] = {"type": type(exc).__name__, "message": str(exc)}
            if self.path is not None:
                self._write(entry)
            raise ToolError(f"{tool} refused: {exc}") from exc
        except Exception as exc:
            entry["error"] = {"type": type(exc).__name__, "message": str(exc)}
            if self.path is not None:
                self._write(entry)
            raise
        if self.path is None:
            return result
        entry["result"] = result
        self._write(entry)
        return result

    def _write(self, entry: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")


def build_server(
    broker: Broker,
    agent_id: str | None = None,
    *,
    identity: Callable[[], str] | None = None,
    tracer: Tracer | None = None,
    **server_kwargs: Any,
) -> MCPServer:
    """An MCP server whose tools act for one agent.

    Pass agent_id for a stdio server that speaks for one agent, or identity, a function
    that names the agent behind the current request (HTTP mode: from its bearer token).
    """
    if (agent_id is None) == (identity is None):
        raise ValueError("pass exactly one of agent_id or identity")
    if agent_id is not None:
        broker.ledger.agent(agent_id)  # fail at start-up, not on the first call
        fixed = agent_id
        identity = lambda: fixed  # noqa: E731
    who = identity
    trace = tracer or Tracer(None)
    server = MCPServer(name="rebbi", instructions=INSTRUCTIONS, **server_kwargs)

    @server.tool()
    def get_budget() -> dict[str, Any]:
        """Your remaining token budget, your published reserve, and the loans you hold or have given."""
        me = who()
        return trace(me, "get_budget", {}, lambda: broker.budget(me))

    @server.tool()
    def report_headroom(reserve_tokens: int, will_lend: bool = True) -> dict[str, Any]:
        """Publish the reserve you will never lend, and whether you lend at all.

        Other agents can borrow only what sits above your reserve and above the
        demand your owner declared for this window.
        """
        me = who()
        args = {"reserve_tokens": reserve_tokens, "will_lend": will_lend}
        return trace(me, "report_headroom", args, lambda: broker.report_headroom(me, reserve_tokens, will_lend))

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
        request_id: str = "",
    ) -> dict[str, Any]:
        """Ask for the tokens you need to finish a job you cannot finish within your budget.

        Returns decision LEND (the tokens are already added to your budget; keep
        working and call settle when done) or CANNOT_MOVE (with the blocker and
        what each possible lender said).

        request_id is your own id for this request, up to 128 characters. Resending
        the same request with the same id returns the first decision, marked
        replayed, instead of booking a second loan; the same id with a different
        request is an error. Without one, every call is a new request.
        """
        me = who()
        request = HandoffRequest(
            goal=goal,
            budget_tokens=budget_tokens,
            job_template=job_template,
            source_commit=source_commit,
            requires_tools=requires_tools or [],
            requires_scopes=requires_scopes or [],
            context_ref=context_ref,
            deadline_s=deadline_s,
            request_id=request_id,
        )
        args = {k: v for k, v in request.__dict__.items()}
        return trace(me, "post_handoff", args, lambda: broker.post_handoff(me, request))

    @server.tool()
    def settle(loan_id: int, outcome: Literal["done", "abandoned"] = "done") -> dict[str, Any]:
        """Close a loan you borrowed once the job is done or abandoned; unspent tokens go back to the lender.

        Safe to resend: a loan that is already closed comes back as it is, marked already_closed.
        """
        me = who()
        args = {"loan_id": loan_id, "outcome": outcome}
        return trace(me, "settle", args, lambda: broker.settle(me, loan_id, outcome))

    return server


def load_tokens(path: str | os.PathLike[str], ledger: Ledger) -> dict[str, str]:
    """token -> agent_id, from a TOML file of `agent_id = "token"` lines. Every agent must exist."""
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    tokens = data.get("tokens", data)
    mapping: dict[str, str] = {}
    for agent_id, token in tokens.items():
        if not isinstance(token, str) or len(token) < 16:
            raise ValueError(f"token for {agent_id} must be a string of at least 16 characters")
        if token in mapping:
            raise ValueError(f"{agent_id} and {mapping[token]} share a token")
        ledger.agent(agent_id)  # UnknownAgent if the token file names an agent the ledger lacks
        mapping[token] = agent_id
    if not mapping:
        raise ValueError(f"{path} holds no tokens")
    return mapping


def http_server(broker: Broker, tokens: dict[str, str], host: str, port: int, tracer: Tracer) -> MCPServer:
    """One server for the fleet; the bearer token decides which agent each request speaks for."""
    from mcp.server.auth.middleware.auth_context import get_access_token
    from mcp.server.auth.provider import AccessToken
    from mcp.server.auth.settings import AuthSettings

    class StaticTokens:
        async def verify_token(self, token: str) -> AccessToken | None:
            agent = tokens.get(token)
            return AccessToken(token=token, client_id=agent, scopes=[]) if agent else None

    def identity() -> str:
        access = get_access_token()
        if access is None:  # the auth middleware refuses unauthenticated requests before this
            raise PermissionError("no bearer token")
        return access.client_id

    base = f"http://{host}:{port}"
    auth = AuthSettings(issuer_url=base, resource_server_url=f"{base}/mcp", validate_token_resource=False)
    return build_server(broker, identity=identity, tracer=tracer, token_verifier=StaticTokens(), auth=auth)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="rebbi-mcp", description="Rebbi's MCP server (stdio by default).")
    p.add_argument("--http", action="store_true", help="serve streamable HTTP for the whole fleet")
    p.add_argument("--host", default="127.0.0.1", help="HTTP: interface to listen on (default 127.0.0.1)")
    p.add_argument("--port", type=int, default=8765, help="HTTP: port (default 8765)")
    p.add_argument("--tokens", default=os.environ.get("REBBI_TOKENS"), help="HTTP: token file (or REBBI_TOKENS)")
    p.add_argument("--db", default=os.environ.get("REBBI_DB", "rebbi.db"), help="ledger file (or REBBI_DB)")
    p.add_argument("--scenario", default=os.environ.get("REBBI_SCENARIO", str(scenario.DEFAULT_SCENARIO)),
                   help="fleet file with the lending rules (or REBBI_SCENARIO)")
    p.add_argument("--trace", default=os.environ.get("REBBI_TRACE"), help="append a JSON line per tool call")
    args = p.parse_args(argv)

    # stdout carries the MCP protocol in stdio mode, so logs go to stderr.
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    if not Path(args.db).exists():
        sys.exit(f"no ledger at {args.db}: create one with `rebbi init <folder>` or `rebbi --db {args.db} seed`")
    sc = scenario.load(args.scenario)
    broker = Broker(Ledger(args.db), sc.rules)
    tracer = Tracer(args.trace)

    if args.http:
        if not args.tokens:
            sys.exit("--http needs a token file: --tokens <path> or REBBI_TOKENS (rebbi init writes one)")
        server = http_server(broker, load_tokens(args.tokens, broker.ledger), args.host, args.port, tracer)
        log.info("serving streamable HTTP at http://%s:%d/mcp", args.host, args.port)
        server.run("streamable-http", host=args.host, port=args.port)
        return

    agent_id = os.environ.get("REBBI_AGENT_ID")
    if not agent_id:
        sys.exit("REBBI_AGENT_ID is not set: the harness must say which agent this server speaks for")
    try:
        server = build_server(broker, agent_id, tracer=tracer)
    except UnknownAgent:
        sys.exit(f"agent {agent_id!r} is not in the ledger {args.db}")
    server.run("stdio")


if __name__ == "__main__":
    main()
