"""The gateway: every model call an agent makes passes through here.

Each agent's harness sets ANTHROPIC_BASE_URL to this gateway and gives the
agent a stand-in key, `rebbi-<agent_id>`; the real API key never leaves this
process. Before a model call the gateway refuses it if the agent's budget in
the ledger is spent; after it, the gateway debits the tokens the call really
used, as the API reported them.

    python -m rebbi.gateway --db rebbi.db --port 8701
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import threading
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import httpx
import uvicorn
from dotenv import dotenv_values
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from rebbi.broker import utcnow
from rebbi.ledger import Ledger, UnknownAgent

log = logging.getLogger("rebbi.gateway")

KEY_PREFIX = "rebbi-"
UPSTREAM = "https://api.anthropic.com"
# Budget spent. Not 429: clients retry that, and this budget will not refill by waiting.
BUDGET_SPENT_STATUS = 402
USAGE_FIELDS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
DROP_REQUEST_HEADERS = {"host", "content-length", "x-api-key", "authorization", "accept-encoding", "connection"}
DROP_RESPONSE_HEADERS = {"content-length", "content-encoding", "transfer-encoding", "connection"}


def agent_key(agent_id: str) -> str:
    return KEY_PREFIX + agent_id


class UsageMeter:
    """Reads token usage out of a Messages API response, streamed (SSE) or not."""

    def __init__(self, streamed: bool):
        self.streamed = streamed
        self.buffer = b""
        self.usage: dict[str, int] = {}
        self.model = ""

    def feed(self, chunk: bytes) -> None:
        self.buffer += chunk
        if self.streamed:
            *lines, self.buffer = self.buffer.split(b"\n")
            for line in lines:
                self._event(line)

    def finish(self) -> int:
        if self.streamed:
            self._event(self.buffer)
        else:
            try:
                body = json.loads(self.buffer or b"{}")
            except ValueError:
                body = {}
            self._take(body.get("usage"), body.get("model"))
        return sum(self.usage.values())

    def breakdown(self) -> str:
        short = {"input_tokens": "in", "cache_creation_input_tokens": "cache_write",
                 "cache_read_input_tokens": "cache_read", "output_tokens": "out"}
        return " ".join(f"{short[k]}={self.usage.get(k, 0)}" for k in USAGE_FIELDS)

    def _event(self, line: bytes) -> None:
        if not line.startswith(b"data:"):
            return
        try:
            data = json.loads(line[5:])
        except ValueError:
            return
        if data.get("type") == "message_start":
            message = data.get("message", {})
            self._take(message.get("usage"), message.get("model"))
        elif data.get("type") == "message_delta":
            self._take(data.get("usage"), None)  # cumulative counts: later values replace earlier ones

    def _take(self, usage: dict | None, model: str | None) -> None:
        self.model = model or self.model
        for k in USAGE_FIELDS:
            if usage and isinstance(usage.get(k), int):
                self.usage[k] = usage[k]


def _api_error(status: int, kind: str, message: str) -> JSONResponse:
    return JSONResponse({"type": "error", "error": {"type": kind, "message": message}}, status_code=status)


def create_gateway(
    ledger: Ledger,
    api_key: str,
    upstream: str = UPSTREAM,
    now: Callable[[], datetime] = utcnow,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    app = FastAPI(title="Rebbi gateway")
    client = httpx.AsyncClient(base_url=upstream, transport=transport, timeout=httpx.Timeout(600, connect=15))

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def proxy(path: str, request: Request) -> Response:
        presented = request.headers.get("x-api-key") or request.headers.get("authorization", "").removeprefix("Bearer ")
        if not presented.startswith(KEY_PREFIX):
            return _api_error(401, "authentication_error", "Rebbi gateway: unknown key")
        agent_id = presented.removeprefix(KEY_PREFIX)
        try:
            ledger.agent(agent_id)
        except UnknownAgent:
            return _api_error(401, "authentication_error", f"Rebbi gateway: unknown agent {agent_id}")

        metered = request.method == "POST" and path.rstrip("/") == "v1/messages"
        if metered:
            ledger.expire_loans(now())
            balance = ledger.balance(agent_id)
            if balance <= 0:
                log.warning("%s refused: budget spent (balance %d)", agent_id, balance)
                return _api_error(BUDGET_SPENT_STATUS, "budget_exhausted",
                                  f"Rebbi: {agent_id} has no token budget left (balance {balance}).")

        headers = {k: v for k, v in request.headers.items() if k.lower() not in DROP_REQUEST_HEADERS}
        headers.update({"x-api-key": api_key, "accept-encoding": "identity"})
        upstream_request = client.build_request(
            request.method, "/" + path, params=request.query_params, headers=headers, content=await request.body()
        )
        response = await client.send(upstream_request, stream=True)
        response_headers = {k: v for k, v in response.headers.items() if k.lower() not in DROP_RESPONSE_HEADERS}
        meter = UsageMeter(streamed=response.headers.get("content-type", "").startswith("text/event-stream"))

        async def relay():
            try:
                async for chunk in response.aiter_bytes():  # decoded, matching the dropped content-encoding
                    if metered:
                        meter.feed(chunk)
                    yield chunk
            finally:
                await response.aclose()
                if metered and response.status_code < 400:
                    tokens = meter.finish()
                    if tokens:
                        state = ledger.record_usage(agent_id, tokens, now(), f"{meter.model} {meter.breakdown()}")
                        log.info("%s used %d tokens (%s), %d left", agent_id, tokens, meter.breakdown(),
                                 state.balance)

        return StreamingResponse(relay(), status_code=response.status_code, headers=response_headers)

    return app


def real_api_key(env_file: Path) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY") or dotenv_values(env_file).get("ANTHROPIC_API_KEY")
    if not key or key.startswith(KEY_PREFIX):
        raise SystemExit(f"No ANTHROPIC_API_KEY in the environment or in {env_file}")
    return key


def serve_in_thread(app: FastAPI, port: int) -> uvicorn.Server:
    """Run the gateway beside the agent harness, in the same process."""
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    deadline = time.monotonic() + 15
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError(f"gateway did not start on port {port}")
        time.sleep(0.05)
    return server


def main() -> None:
    p = argparse.ArgumentParser(prog="rebbi.gateway")
    p.add_argument("--db", default="rebbi.db")
    p.add_argument("--port", type=int, default=8701)
    p.add_argument("--env-file", type=Path, default=Path(".env"))
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    app = create_gateway(Ledger(args.db), real_api_key(args.env_file))
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
