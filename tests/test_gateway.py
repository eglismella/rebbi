import json

import httpx
from fastapi.testclient import TestClient

from rebbi.gateway import BUDGET_SPENT_STATUS, agent_key, create_gateway

USAGE = {"input_tokens": 100, "cache_creation_input_tokens": 20, "cache_read_input_tokens": 300, "output_tokens": 50}


def sse(*events):
    return "".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events).encode()


class Upstream:
    """Stands in for api.anthropic.com and records what reached it."""

    def __init__(self, respond):
        self.respond = respond
        self.seen: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.seen.append(request)
        return self.respond(request)


def gateway(broker, respond):
    upstream = Upstream(respond)
    app = create_gateway(broker.ledger, "sk-real", now=broker.now, transport=httpx.MockTransport(upstream))
    return TestClient(app), upstream


def call(http, agent="auditor-01", path="/v1/messages", stream=False):
    body = {"model": "claude-sonnet-5-5", "max_tokens": 10, "stream": stream, "messages": []}
    return http.post(path, headers={"x-api-key": agent_key(agent)}, json=body)


def test_debits_what_a_plain_call_used_and_hides_the_real_key(broker):
    http, upstream = gateway(broker, lambda r: httpx.Response(200, json={"model": "m", "usage": USAGE}))
    assert call(http).status_code == 200
    assert broker.ledger.balance("auditor-01") == 40_000 - 470
    assert {r.headers["x-api-key"] for r in upstream.seen} == {"sk-real"}


def test_debits_what_a_streamed_call_used(broker):
    events = sse(
        {"type": "message_start", "message": {"model": "m", "usage": {**USAGE, "output_tokens": 1}}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "hi"}},
        {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 50}},
        {"type": "message_stop"},
    )
    http, _ = gateway(broker, lambda r: httpx.Response(200, content=events,
                                                        headers={"content-type": "text/event-stream"}))
    response = call(http, stream=True)
    assert response.content == events
    assert broker.ledger.balance("auditor-01") == 40_000 - 470


def test_refuses_once_the_budget_is_spent_without_calling_upstream(broker, clock):
    broker.ledger.record_usage("auditor-01", 40_000, clock())
    http, upstream = gateway(broker, lambda r: httpx.Response(200, json={"usage": USAGE}))
    response = call(http)
    assert response.status_code == BUDGET_SPENT_STATUS
    assert response.json()["error"]["type"] == "budget_exhausted"
    assert upstream.seen == []


def test_refuses_a_call_whose_input_the_balance_cannot_cover(broker, clock):
    broker.ledger.record_usage("auditor-01", 36_000, clock())  # 4,000 left

    def respond(request):
        if request.url.path.endswith("count_tokens"):
            assert set(json.loads(request.content)) == {"model", "messages"}  # max_tokens and stream stripped
            return httpx.Response(200, json={"input_tokens": 5_000})
        return httpx.Response(200, json={"usage": USAGE})

    http, upstream = gateway(broker, respond)
    response = call(http)
    assert response.status_code == BUDGET_SPENT_STATUS
    assert "5000 input tokens" in response.json()["error"]["message"]
    assert [r.url.path for r in upstream.seen] == ["/v1/messages/count_tokens"]


def test_a_loan_reopens_the_gate(broker, clock):
    from rebbi.broker import HandoffRequest

    broker.ledger.record_usage("auditor-01", 40_000, clock())
    broker.post_handoff("auditor-01", HandoffRequest(goal="finish", budget_tokens=10_000))
    http, _ = gateway(broker, lambda r: httpx.Response(200, json={"usage": USAGE}))
    assert call(http).status_code == 200


def test_unknown_keys_are_refused(broker):
    http, upstream = gateway(broker, lambda r: httpx.Response(200, json={}))
    assert http.post("/v1/messages", headers={"x-api-key": "sk-ant-anything"}, json={}).status_code == 401
    assert call(http, agent="intruder-99").status_code == 401
    assert upstream.seen == []


def test_upstream_errors_and_other_endpoints_are_not_debited(broker):
    http, _ = gateway(broker, lambda r: httpx.Response(400, json={"type": "error", "usage": USAGE}))
    assert call(http).status_code == 400
    http, _ = gateway(broker, lambda r: httpx.Response(200, json={"input_tokens": 999}))
    assert call(http, path="/v1/messages/count_tokens").status_code == 200
    assert broker.ledger.balance("auditor-01") == 40_000
