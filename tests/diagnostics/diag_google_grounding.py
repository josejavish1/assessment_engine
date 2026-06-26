import os
from pathlib import Path

from google import genai
from google.genai import types


def test_vertex_search_grounding():
    print("\n🚀 Probando Búsqueda Nativa de Google (Vertex AI Grounding)...")

    # Usar la cuenta de servicio existente
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(
        Path.home() / ".secrets" / "sa-key.json"
    )

    project_id = "sub403o4u0q5"  # El de tu assessment_env.sh
    location = "europe-west1"  # Your official region

    try:
        client = genai.Client(vertexai=True, project=project_id, location=location)

        # Configure the Google search tool
        google_search_tool = types.Tool(google_search=types.GoogleSearch())

        prompt = "Dime las últimas 3 noticias estratégicas de Redeia de esta semana y su impacto financiero."

        print(f"  -> Consultando a Google Search: '{prompt}'")

        response = client.models.generate_content(
            model="gemini-1.5-flash",  # Modelo estable en Vertex
            contents=prompt,
            config=types.GenerateContentConfig(tools=[google_search_tool]),
        )

        print("\n✅ RESPUESTA RECIBIDA:")
        print(response.text)

        if response.candidates[0].grounding_metadata:
            print("\n🛡️ FUENTES DE VERDAD DETECTADAS:")
            for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
                if chunk.web:
                    print(f"- {chunk.web.title}: {chunk.web.uri}")
        else:
            print(
                "\n⚠️ No se detectaron metadatos de búsqueda. Es posible que el proyecto no tenga habilitado el Grounding."
            )

    except Exception as e:
        print(f"\n❌ ERROR DE CONEXIÓN: {str(e)}")


if __name__ == "__main__":
    test_vertex_search_grounding()
