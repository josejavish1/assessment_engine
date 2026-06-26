
import asyncio
import os
from google.adk.agents import Agent
from google.adk.tools import google_search
from vertexai.agent_engines import AdkApp
from src.infrastructure.ai_client import run_agent

async def test_search():
    print(f"Using Vertex AI: {os.environ.get('GOOGLE_GENAI_USE_VERTEXAI')}")
    agent = Agent(
        name="test_search_agent",
        model="gemini-2.5-flash",
        tools=[google_search],
        instruction="Eres un investigador. Usa la herramienta de búsqueda para encontrar quién ganó la Eurocopa 2024.",
    )
    app = AdkApp(agent=agent)
    
    try:
        result = await run_agent(
            app=app,
            user_id="test",
            message="¿Quién ganó la Eurocopa 2024? Dime la fuente.",
        )
        print("RESULTADO:", result)
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(test_search())
