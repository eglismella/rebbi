import asyncio, json, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
cfg = json.load(open(".mcp.json"))["mcpServers"]["rebbi"]
params = StdioServerParameters(command=cfg["command"], args=cfg["args"], env=cfg["env"])
async def main(tool, args):
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool(tool, args)
            print(res.is_error, json.dumps(res.structured_content) if res.structured_content else [c.text for c in res.content])
asyncio.run(main(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}))
