"""`rebbi call`: one Rebbi tool call from a shell, through the connection in an .mcp.json file.

    rebbi call get_budget
    rebbi call post_handoff '{"goal": "audit", "budget_tokens": 30000, "request_id": "audit-42"}'
    rebbi call settle '{"loan_id": 1}' --config path/to/.mcp.json

Prints the reply as JSON. A refused call prints {"error": "..."} and exits 1. Added after HW9's
cold-start runs: all three fresh agents had to write their own MCP client before their first call.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp import Client, StdioServerParameters


def _transport(entry: dict[str, Any]):
    if entry.get("type") == "http" or "url" in entry:
        import httpx2
        from mcp.client.streamable_http import streamable_http_client

        http = httpx2.AsyncClient(headers=entry.get("headers", {}))
        return streamable_http_client(entry["url"], http_client=http), http
    return StdioServerParameters(command=entry["command"], args=entry.get("args", []),
                                 env={**os.environ, "REBBI_LOG_LEVEL": "WARNING", **entry.get("env", {})}), None


def call(tool: str, arguments: dict[str, Any], config: Path, server: str = "rebbi") -> tuple[bool, Any]:
    entry = json.loads(config.read_text(encoding="utf-8"))["mcpServers"][server]

    async def run():
        transport, http = _transport(entry)
        try:
            async with Client(transport) as client:
                result = await client.call_tool(tool, arguments)
        finally:
            if http is not None:
                await http.aclose()
        if result.is_error:
            return False, " ".join(getattr(c, "text", "") for c in result.content)
        return True, result.structured_content

    return asyncio.run(run())


def main(tool: str, raw_args: str | None, config: Path) -> int:
    try:
        arguments = json.loads(raw_args) if raw_args else {}
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"arguments are not valid JSON: {exc}"}))
        return 2
    if not config.exists():
        print(json.dumps({"error": f"no {config}: pass --config <path to .mcp.json>"}))
        return 2
    try:
        ok, reply = call(tool, arguments, config)
    except Exception as exc:  # server not reachable, bad config: one JSON line, not a traceback
        print(json.dumps({"error": f"could not reach Rebbi through {config}: {type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps(reply if ok else {"error": reply}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, Path(".mcp.json")))
