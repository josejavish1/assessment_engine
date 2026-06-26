import asyncio

from google.adk.agents import Agent
from src.application.tools.context_tools import search_google_tier1
from src.infrastructure.ai_client import run_agent
from vertexai.agent_engines import AdkApp


async def test_search():
    print("Testing search_google_tier1...")
    res = search_google_tier1("quien gano eurocopa 2024")
    print(res)

    print("\nTesting agent with search_google_tier1...")
    agent = Agent(
        name="test_search_agent",
        model="gemini-2.5-flash",
        tools=[search_google_tier1],
        instruction="Eres un investigador. Usa la herramienta search_google_tier1 para buscar en internet quién ganó la Eurocopa 2024.",
    )
    app = AdkApp(agent=agent)

    try:
        result = await run_agent(
            app=app,
            user_id="test",
            message="¿Quién ganó la Eurocopa 2024?",
        )
        print("RESULTADO AGENTE:", result)
    except Exception as e:
        print("ERROR AGENTE:", e)


if __name__ == "__main__":
    asyncio.run(test_search())
