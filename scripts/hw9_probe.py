"""The HW9 boundary cases, called directly over MCP so before and after the fix can be compared.

    python scripts/hw9_probe.py > docs/hw9/evidence/probe-<before|after>.txt

A fresh starter fleet in a temporary folder; auditor-01 then:
  1. asks for 100,000 (over the 60,000 loan cap),
  2. asks for 100,000 again with a new request_id (only 20,000 left above analyst-07's reserve),
  3. asks again (nothing left anywhere),
  4. settles a loan that does not exist,
  5. reuses request_id "a" for a different request,
  6. asks with requires_tools set (a field Rebbi records but does not check).
"""

import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from mcp import Client, StdioServerParameters

CALLS = [
    ("get_budget", {}),
    ("post_handoff", {"goal": "audit", "budget_tokens": 100_000, "request_id": "a"}),
    ("post_handoff", {"goal": "audit", "budget_tokens": 100_000, "request_id": "b"}),
    ("post_handoff", {"goal": "audit", "budget_tokens": 10_000, "request_id": "c"}),
    ("settle", {"loan_id": 999}),
    ("post_handoff", {"goal": "something else", "budget_tokens": 5_000, "request_id": "a"}),
    ("post_handoff", {"goal": "hand this job to an agent with sql.read", "budget_tokens": 5_000,
                      "requires_tools": ["sql.read"], "request_id": "d"}),
]


async def run(fleet: Path) -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "rebbi.mcp_server"],
                                   env={"REBBI_AGENT_ID": "auditor-01", "REBBI_DB": str(fleet / "rebbi.db"),
                                        "REBBI_SCENARIO": str(fleet / "scenario.toml")})
    async with Client(params) as client:
        for tool, args in CALLS:
            result = await client.call_tool(tool, args)
            print(f"\n>>> {tool} {json.dumps(args)}")
            if result.is_error:
                print("ERROR:", " ".join(c.text for c in result.content if hasattr(c, "text")))
            else:
                reply = dict(result.structured_content)
                reply.pop("considered", None)  # the same lender list every time; trimmed for reading
                print(json.dumps(reply, indent=2))


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fleet = Path(tmp) / "fleet"
        subprocess.run([sys.executable, "-m", "rebbi", "init", str(fleet)], check=True, capture_output=True)
        asyncio.run(run(fleet))


if __name__ == "__main__":
    main()
