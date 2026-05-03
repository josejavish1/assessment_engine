import os
import json
from pathlib import Path
import vertexai
from vertexai.generative_models import GenerativeModel

# 1. Configurar Auth
ROOT = Path(".").resolve()
sa_path = ROOT / "gcp_service_account.json"
if sa_path.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(sa_path)
    with open(sa_path, "r") as f:
        sa_data = json.load(f)
        os.environ["GOOGLE_CLOUD_PROJECT"] = sa_data.get("project_id")

# 2. Intentar en Región Europa con un modelo más estándar
try:
    print("🌍 Probando en región: europe-west1...")
    vertexai.init(
        project=os.environ.get("GOOGLE_CLOUD_PROJECT"), location="europe-west1"
    )
    model = GenerativeModel("gemini-1.5-pro")

    response = model.generate_content("Responde: OK")
    print(f"\n✅ Conexión EXITOSA en Europe: {response.text.strip()}")

except Exception as e:
    print(f"\n❌ FALLO en Europe: {e}")

    # 3. Último intento en US por si acaso con gemini-pro
    try:
        print("\n🇺🇸 Probando en región: us-central1 con gemini-1.5-pro...")
        vertexai.init(
            project=os.environ.get("GOOGLE_CLOUD_PROJECT"), location="us-central1"
        )
        model = GenerativeModel("gemini-1.5-pro")
        response = model.generate_content("Responde: OK")
        print(f"✅ Conexión EXITOSA en US: {response.text.strip()}")
    except Exception as e2:
        print(f"❌ FALLO definitivo: {e2}")
