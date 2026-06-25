import asyncio
import os
import sys
from pathlib import Path

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

# Asegurar que usamos el src de este proyecto específicamente
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from application.tools.context_tools import search_google_vertex_sovereign


async def test_adk_grounding():
    print("\n🚀 Probando ADK Agent con Búsqueda Soberana...")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/jsanchhi/.secrets/sa-key.json"

    agent = Agent(
        name="test_agent",
        model="gemini-2.5-pro",
        instruction="Responde a la pregunta usando la herramienta de búsqueda proporcionada.",
        tools=[search_google_vertex_sovereign],
    )

    app = AdkApp(agent=agent)

    prompt = "Dime las 3 lineas de negocio de Redeia (Hispasat, Reintel, REE) y sus ingresos en 2023."

    print(f"  -> Preguntando al agente: '{prompt}'")

    try:
        async for event in app.async_stream_query(user_id="test_user", message=prompt):
            # Extraer texto de la respuesta si es posible
            if hasattr(event, "text"):
                print(event.text, end="", flush=True)
            else:
                # Si es un evento complejo, lo imprimimos simplificado
                pass
        print("\n\n✅ FIN DE LA RESPUESTA")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_adk_grounding())
