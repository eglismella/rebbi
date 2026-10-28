"""A scripted stand-in for the Claude Messages API: the harness's wiring, run without a model.

It is NOT evidence and NOT the demo: every reply is hard-coded, including the report, which is built
from the answer key. It exists so the agent CLI, the gateway, the MCP server, the low-budget hook and
the verifier can run end to end without credits: in the offline tests, and in
`python -m rebbi.demo --rehearsal`, which labels every run it makes as scripted.

The auditor script reads, then greps until the harness's budget warning shows up in the conversation,
asks Rebbi for tokens, and answers with a report built from the answer key. Each call reports
CALL_TOKENS of input, so budgets drain at a known rate.
"""

from __future__ import annotations

import json
import re
from itertools import count

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from rebbi.verify import DEFAULT_KEY

CALL_TOKENS = 6_000
# The scripted auditor makes 13 calls of 6,050 tokens, so it needs its own budget: this one runs out partway.
BUDGETS = {"auditor-01": 40_000}
_ids = count(1)


def _report() -> str:
    key = json.loads(DEFAULT_KEY.read_text(encoding="utf-8"))
    sections = "\n\n".join(f"## {n}. Section {n}\n\nScripted findings." for n in range(1, 8))
    appendix = {k: key[k] for k in ("runtime_dependencies", "optional_groups", "imports", "unused_dependencies",
                                     "undeclared_imports", "unpinned")}
    return f"# Dependency audit\n\n{sections}\n\n```json\n{json.dumps(appendix)}\n```"


def _next_step(body: dict) -> tuple[str, dict | str]:
    """('tool', {name, input}) or ('text', str) for this point in the conversation."""
    system = json.dumps(body.get("system", ""))
    messages = body.get("messages", [])
    history = json.dumps(messages)
    # Everything since the model last spoke: tool results, plus the context the CLI and hooks add after them.
    since = max((i for i, m in enumerate(messages) if m.get("role") == "assistant"), default=-1)
    last = json.dumps(messages[since + 1:])
    tool_names = {t.get("name") for t in body.get("tools", [])}

    if "auditor-01" not in system:  # a lender: publish once, then say so
        if "mcp__rebbi__report_headroom" in tool_names and '"tool_result"' not in last:
            reserve = re.search(r"reserve of (\d+)", history)
            return "tool", {"name": "mcp__rebbi__report_headroom",
                            "input": {"reserve_tokens": int(reserve.group(1)) if reserve else 0, "will_lend": True}}
        return "text", "Published my reserve to Rebbi."

    if "Rebbi budget warning" in last and "mcp__rebbi__post_handoff" in tool_names:
        return "tool", {"name": "mcp__rebbi__post_handoff",
                        "input": {"goal": "finish dependency audit", "budget_tokens": 60_000,
                                  "job_template": "dep-audit-v1", "requires_tools": ["repo.read"]}}
    calls = history.count('"tool_use"')
    if calls == 0:
        return "tool", {"name": "Read", "input": {"file_path": "setup.py"}}
    if calls < 12:
        return "tool", {"name": "Grep", "input": {"pattern": "^import|^from", "glob": "*.py"}}
    return "text", _report()


def _events(model: str, kind: str, payload: dict | str):
    msg_id = f"msg_fake_{next(_ids)}"
    yield {"type": "message_start", "message": {
        "id": msg_id, "type": "message", "role": "assistant", "model": model, "content": [],
        "stop_reason": None, "stop_sequence": None, "usage": {"input_tokens": CALL_TOKENS, "output_tokens": 1}}}
    if kind == "tool":
        yield {"type": "content_block_start", "index": 0, "content_block": {
            "type": "tool_use", "id": f"toolu_fake_{next(_ids)}", "name": payload["name"], "input": {}}}
        yield {"type": "content_block_delta", "index": 0,
               "delta": {"type": "input_json_delta", "partial_json": json.dumps(payload["input"])}}
    else:
        yield {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}
        yield {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": payload}}
    yield {"type": "content_block_stop", "index": 0}
    yield {"type": "message_delta", "delta": {"stop_reason": "tool_use" if kind == "tool" else "end_turn",
                                              "stop_sequence": None}, "usage": {"output_tokens": 50}}
    yield {"type": "message_stop"}


def create_scripted_model(seen: list | None = None) -> FastAPI:
    app = FastAPI()

    @app.post("/v1/messages")
    async def messages(request: Request):
        body = await request.json()
        if seen is not None:
            seen.append(body)
        kind, payload = _next_step(body)
        events = list(_events(body.get("model", "fake"), kind, payload))
        if body.get("stream"):
            sse = "".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events)
            return StreamingResponse(iter([sse.encode()]), media_type="text/event-stream")
        content = ([{"type": "tool_use", "id": events[1]["content_block"]["id"], "name": payload["name"],
                     "input": payload["input"]}] if kind == "tool" else [{"type": "text", "text": payload}])
        return JSONResponse({**events[0]["message"], "content": content,
                             "stop_reason": "tool_use" if kind == "tool" else "end_turn",
                             "usage": {"input_tokens": CALL_TOKENS, "output_tokens": 50}})

    @app.post("/v1/messages/count_tokens")
    async def count_tokens():
        return {"input_tokens": CALL_TOKENS}

    return app
