import os
import sys
from pathlib import Path

# Asegurar que usamos el src de este proyecto específicamente
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from assessment_engine.application.tools.context_tools import (
    search_google_vertex_sovereign,
)


def mini_test_sovereign():
    print("\n🚀 Iniciando MINI-TEST de Búsqueda Soberana (Vertex AI Search)...")

    # Cargar .env manualmente
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

    # Cargar credenciales adicionales si faltan
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
            "/home/jsanchhi/.secrets/sa-key.json"
        )

    os.environ["GOOGLE_CLOUD_PROJECT"] = "sub403o4u0q5"

    query = "Redeia lineas de negocio Hispasat Reintel"
    domains = ["redeia.com"]

    print(f"  -> Consultando Vertex AI Search para: '{query}'")

    try:
        # Probamos la función directamente
        results = search_google_vertex_sovereign(query, authority_domains=domains)

        print("\n✅ RESPUESTA DEL MOTOR SOBERANO:")
        print("-" * 60)
        print(results)
        print("-" * 60)

        if "RESULTADOS SOBERANOS VERTEX AI SEARCH" in results:
            print("\n🎉 ¡ÉXITO! Vertex AI Search está configurado y respondiendo.")
        elif "RESULTADOS OFICIALES GOOGLE SEARCH" in results:
            print("\nℹ️ Nota: Cayó en el fallback de Google Search API, pero funcionó.")
        else:
            print("\n⚠️ Resultados inesperados. Revisa el log.")

    except Exception as e:
        print(f"\n❌ ERROR EN LA PRUEBA: {str(e)}")


if __name__ == "__main__":
    mini_test_sovereign()
