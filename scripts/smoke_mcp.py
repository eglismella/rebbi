"""Talk to Rebbi over MCP the way an agent harness will: one stdio server per agent.

    python -m rebbi seed --reset
    python scripts/smoke_mcp.py              # auditor-01 asks for 30k tokens
    python -m rebbi status && python -m rebbi check
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parent.parent


async def main(agent_id: str, tokens: int) -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "rebbi.mcp_server"],
        env={**os.environ, "REBBI_AGENT_ID": agent_id, "REBBI_DB": str(ROOT / "rebbi.db")},
        cwd=str(ROOT),
    )
    async with Client(params) as client:
        for name, args in [
            ("get_budget", {}),
            ("post_handoff", {"goal": "finish dependency audit, sections 4-7", "budget_tokens": tokens,
                              "job_template": "dep-audit-v1", "requires_tools": ["repo.read"]}),
            ("get_budget", {}),
        ]:
            result = await client.call_tool(name, args)
            print(f"\n{agent_id} -> {name}({json.dumps(args) if args else ''})")
            print(json.dumps(result.structured_content, indent=2))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "auditor-01",
                     int(sys.argv[2]) if len(sys.argv) > 2 else 30_000))
