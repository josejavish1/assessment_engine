import asyncio

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client


async def main():
    try:
        async with sse_client("http://127.0.0.1:8000/sse") as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                print("Tools:", await session.list_tools())
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
