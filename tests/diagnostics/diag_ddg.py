import asyncio

from duckduckgo_search import DDGS


async def test_ddg():
    print("Testing DDGS...")
    results = DDGS().text("quien gano eurocopa 2024", max_results=3)
    for r in results:
        print(r)


if __name__ == "__main__":
    asyncio.run(test_ddg())
