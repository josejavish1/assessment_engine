from google.oauth2 import service_account
from googleapiclient.discovery import build


def diagnostic_google_no_key():
    print(
        "\n🔍 DIAGNÓSTICO MAESTRO - AUTENTICACIÓN POR CUENTA DE SERVICIO (SIN API KEY)"
    )

    # 1. Cargar CSE_ID del .env
    cse_id = "02ec5ea2411d24516"  # Usamos el que me pasaste

    sa_path = "/home/jsanchhi/.secrets/sa-key.json"

    print(f"  -> Usando Cuenta de Servicio: {sa_path}")
    print(f"  -> CSE ID: {cse_id}")

    try:
        # 2. Obtener credenciales de la SA con scopes extendidos
        scopes = [
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/cse",
        ]
        creds = service_account.Credentials.from_service_account_file(
            sa_path, scopes=scopes
        )

        # 3. Construir el servicio USANDO LAS CREDENCIALES, NO LA API KEY
        service = build("customsearch", "v1", credentials=creds)

        print("\n📡 Lanzando búsqueda estratégica (Sovereign Mode)...")
        res = service.cse().list(q="Redeia", cx=cse_id).execute()

        print("\n✅ ¡LO LOGRAMOS! La cuenta de servicio ha saltado el bloqueo.")
        print(f"  -> Encontrados {len(res.get('items', []))} resultados.")

    except Exception as e:
        print("\n❌ FALLO DEFINITIVO:")
        print("-" * 50)
        print(str(e))
        print("-" * 50)
        print(
            "\nSi esto falla con un 403, significa que la API 'Custom Search API' NO está habilitada"
        )
        print(
            "en el proyecto 'sub403o4u0q5'. Por favor, revisa el selector de proyectos en la consola."
        )


if __name__ == "__main__":
    diagnostic_google_no_key()
