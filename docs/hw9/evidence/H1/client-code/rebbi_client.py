import asyncio, json, sys, httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8765/mcp"
TOKEN = json.load(open(".mcp.json"))["mcpServers"]["rebbi"]["headers"]["Authorization"]

async def call(tool, args):
    http = httpx2.AsyncClient(headers={"Authorization": TOKEN})
    async with Client(streamable_http_client(URL, http_client=http)) as c:
        r = await c.call_tool(tool, args)
        return r.is_error, r.structured_content or [getattr(x, "text", str(x)) for x in r.content]

if __name__ == "__main__":
    print(json.dumps(asyncio.run(call(sys.argv[1], json.loads(sys.argv[2] if len(sys.argv) > 2 else "{}"))), indent=1))
