import os
import sys
from pathlib import Path

# Asegurar que usamos el src de este proyecto específicamente
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from assessment_engine.application.tools.context_tools import search_google_tier1


def mini_test_search():
    print("\n🚀 Iniciando MINI-TEST de Búsqueda Google Tier 1...")

    # Cargar .env manualmente para evitar problemas de shell
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

    query = "Redeia resultados financieros 2024 oficial"
    domains = ["redeia.com", "cnmc.es"]

    print(f"  -> Buscando: '{query}' en dominios {domains}")

    try:
        results = search_google_tier1(query, authority_domains=domains)
        print("\n✅ RESULTADOS OBTENIDOS:")
        print("-" * 50)
        print(results)
        print("-" * 50)

        if "RESULTADOS OFICIALES GOOGLE SEARCH" in results:
            print("\n🎉 ¡ÉXITO! La API de Google está respondiendo correctamente.")
        else:
            print("\n⚠️ La respuesta no parece ser de Google Tier 1. Revisa las claves.")

    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {str(e)}")


if __name__ == "__main__":
    mini_test_search()
