import asyncio, json, sys, os
from mcp import Client, StdioServerParameters
cfg = json.load(open("/home/claude/hw9/R2/client/.mcp.json"))["mcpServers"]["rebbi"]
params = StdioServerParameters(command=cfg["command"], args=cfg["args"], env={**os.environ, **cfg["env"]})
async def main(tool, args):
    async with Client(params) as c:
        r = await c.call_tool(tool, args)
        print(json.dumps(r.structured_content if not r.is_error else {"error": str(r.content)}, indent=1))
asyncio.run(main(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}))
