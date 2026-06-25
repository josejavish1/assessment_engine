from pathlib import Path

from googleapiclient.discovery import build


def diagnostic_google_official():
    print("\n🔍 DIAGNÓSTICO OFICIAL GOOGLE API CLIENT")

    # 1. Cargar claves del .env
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

                print("  -> Proyecto: sub403o4u0q5")

    print(f"  -> API Key: {'***' + api_key[-4:] if api_key else 'Missing'}")
    print(f"  -> CSE ID: {cse_id if cse_id else 'Missing'}")

    try:
        # Intentar construir el servicio de búsqueda
        # Si la API no está bien habilitada, esto fallará aquí
        service = build("customsearch", "v1", developerKey=api_key)

        print("\n📡 Lanzando búsqueda oficial...")
        res = service.cse().list(q="Redeia", cx=cse_id).execute()

        print("\n✅ ¡BRUTAL! La conexión ha funcionado.")
        print(f"  -> Encontrados {len(res.get('items', []))} resultados.")
        for i, item in enumerate(res.get("items", [])[:2], 1):
            print(f"     {i}. {item['title']} -> {item['link']}")

    except Exception as e:
        print("\n❌ EL ERROR REAL ES:")
        print("-" * 50)
        print(str(e))
        print("-" * 50)

        if "403" in str(e):
            print("\n💡 ANÁLISIS DEL ARQUITECTO:")
            if (
                "not enabled" in str(e).lower()
                or "not have the access" in str(e).lower()
            ):
                print(
                    "El error persiste: Google insiste en que la API no está habilitada para ESTA clave."
                )
                print(
                    "Probablemente la API Key se creó en un proyecto distinto a 'sub403o4u0q5'."
                )
            elif "billing" in str(e).lower():
                print("Es un problema de Facturación (Billing).")
            else:
                print(
                    "Es un bloqueo de política de organización. Necesitamos usar OAuth2 puro."
                )


if __name__ == "__main__":
    diagnostic_google_official()
