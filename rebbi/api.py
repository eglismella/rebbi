"""HTTP side of the broker: the gateway's check-and-debit calls, plus read-only views for the demo.

    REBBI_DB=rebbi.db uvicorn rebbi.api:app_from_env --factory --port 8700
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from rebbi import rules as lending
from rebbi import scenario
from rebbi.broker import Broker
from rebbi.ledger import Ledger, UnknownAgent


class Usage(BaseModel):
    agent_id: str
    tokens: int = Field(ge=0)
    note: str = ""


def create_app(broker: Broker) -> FastAPI:
    app = FastAPI(title="Rebbi broker")
    ledger = broker.ledger

    def agent_or_404(agent_id: str):
        try:
            return ledger.agent(agent_id)
        except UnknownAgent:
            raise HTTPException(404, f"unknown agent {agent_id}") from None

    @app.get("/gateway/check/{agent_id}")
    def gateway_check(agent_id: str) -> dict:
        """Called before each model call: refuse it once the agent's budget is spent."""
        ledger.expire_loans(broker.now())
        state = agent_or_404(agent_id)
        return {"agent_id": agent_id, "allowed": state.balance > 0, "balance": state.balance}

    @app.post("/gateway/usage")
    def gateway_usage(usage: Usage) -> dict:
        """Called after each model call with the tokens it actually used."""
        agent_or_404(usage.agent_id)
        state = ledger.record_usage(usage.agent_id, usage.tokens, broker.now(), usage.note)
        return {"agent_id": state.agent_id, "balance": state.balance}

    @app.get("/agents")
    def agents() -> list[dict]:
        return [{**a.to_dict(), "lendable": lending.lendable(a)} for a in ledger.agents()]

    @app.get("/loans")
    def loans() -> list[dict]:
        return ledger.loans()

    @app.get("/decisions")
    def decisions() -> list[dict]:
        return ledger.decisions()

    @app.get("/invariants")
    def invariants() -> dict:
        problems = ledger.check_invariants(broker.now())
        return {"ok": not problems, "problems": problems}

    return app


def app_from_env() -> FastAPI:
    sc = scenario.load(os.environ.get("REBBI_SCENARIO", scenario.DEFAULT_SCENARIO))
    return create_app(Broker(Ledger(os.environ.get("REBBI_DB", "rebbi.db")), sc.rules))
