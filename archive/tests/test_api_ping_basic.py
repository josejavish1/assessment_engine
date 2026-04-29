import os
import json
from pathlib import Path
import vertexai
from vertexai.generative_models import GenerativeModel

ROOT = Path(".").resolve()
sa_path = ROOT / "gcp_service_account.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(sa_path)
with open(sa_path, 'r') as f:
    sa_data = json.load(f)
    os.environ["GOOGLE_CLOUD_PROJECT"] = sa_data.get("project_id")

try:
    print(f"Probando conexión básica con gemini-1.0-pro en {os.environ['GOOGLE_CLOUD_PROJECT']}...")
    vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"], location="us-central1")
    model = GenerativeModel("gemini-1.0-pro")
    response = model.generate_content("Di solo 'Hola'")
    print(f"✅ ¡ÉXITO! El modelo respondió: {response.text}")
except Exception as e:
    print(f"❌ FALLO también con el modelo básico. El problema es el Proyecto/Facturación/API:\n{e}")

