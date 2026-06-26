import os

from google import genai
from google.genai import types


def test_grounding_direct():
    print("\n🚀 Probando Grounding Directo (Sin CSE/API Key)...")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/jsanchhi/.secrets/sa-key.json"

    client = genai.Client(
        vertexai=True, project="sub403o4u0q5", location="europe-west1"
    )

    # Herramienta de búsqueda nativa de Google
    search_tool = types.Tool(google_search=types.GoogleSearch())

    prompt = "Busca el PDF oficial del 'Plan Estrategico Redeia 2021-2025' o el 'Informe de Sostenibilidad 2023'. Dame el link directo al archivo .pdf"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",  # El modelo que sabemos que funciona en tu proyecto
            contents=prompt,
            config=types.GenerateContentConfig(tools=[search_tool]),
        )

        print("\n✅ RESPUESTA:")
        print(response.text)

        if response.candidates[0].grounding_metadata:
            print("\n🛡️ FUENTES:")
            for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
                if chunk.web:
                    print(f"- {chunk.web.title}: {chunk.web.uri}")

    except Exception as e:
        print(f"\n❌ FALLO: {str(e)}")


if __name__ == "__main__":
    test_grounding_direct()
