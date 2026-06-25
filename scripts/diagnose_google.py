import json
from pathlib import Path

import requests


def diagnostic_google_search():
    print("\n🔍 INICIANDO DIAGNÓSTICO PROFUNDO - GOOGLE CUSTOM SEARCH")

    # Leer claves del .env
    env_path = Path(__file__).resolve().parents[1] / ".env"
    api_key = None
    cse_id = None
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                if k.strip() == "GOOGLE_SEARCH_API_KEY":
                    api_key = v.strip()
                if k.strip() == "GOOGLE_CSE_ID":
                    cse_id = v.strip()

    print(
        f"  -> API Key detectada: {'***' + api_key[-4:] if api_key else 'NO ENCONTRADA'}"
    )
    print(f"  -> CSE ID detectado: {cse_id if cse_id else 'NO ENCONTRADO'}")

    if not api_key or not cse_id:
        print("❌ Faltan claves en el .env")
        return

    url = "https://www.googleapis.com/customsearch/v1"
    params = {"q": "Redeia", "key": api_key, "cx": cse_id}

    print("\n📡 Lanzando petición a Google...")
    try:
        response = requests.get(url, params=params)
        print(f"  -> Código de Estado HTTP: {response.status_code}")

        error_data = response.json()
        print("\n📄 RESPUESTA COMPLETA DE GOOGLE:")
        print(json.dumps(error_data, indent=2))

        if response.status_code == 200:
            print("\n✅ ¡ÉXITO! La conexión funciona.")
        else:
            reason = error_data.get("error", {}).get("message", "Desconocido")
            status = error_data.get("error", {}).get("status", "Desconocido")
            print("\n❌ FALLO DETECTADO:")
            print(f"   Motivo: {reason}")
            print(f"   Status: {status}")

    except Exception as e:
        print(f"❌ Error en la ejecución del script: {str(e)}")


if __name__ == "__main__":
    diagnostic_google_search()
