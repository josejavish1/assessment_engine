import os
import json
from pathlib import Path
import vertexai
from vertexai.generative_models import GenerativeModel

# 1. Configurar Auth (Simulando lo que hace el orquestador)
ROOT = Path(".").resolve()
sa_path = ROOT / "gcp_service_account.json"

if sa_path.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(sa_path)
    with open(sa_path, 'r') as f:
        sa_data = json.load(f)
        project_id = sa_data.get("project_id")
        if project_id:
            os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
            print(f"🔐 Autenticado con Service Account en proyecto: {project_id}")

# 2. Inicializar Vertex AI
try:
    vertexai.init(project=os.environ.get("GOOGLE_CLOUD_PROJECT"), location="us-central1")
    model = GenerativeModel("gemini-1.5-flash") # Usamos flash para un ping rápido
    
    print("📡 Enviando pulso a Vertex AI...")
    response = model.generate_content("Hola mundo, responde con un 'Conexión exitosa' y la fecha de hoy.")
    
    print("\n--- RESPUESTA DEL MODELO ---")
    print(response.text.strip())
    print("----------------------------")
    print("\n✅ ¡API operativa y credenciales validadas!")
    
except Exception as e:
    print(f"\n❌ ERROR DE CONEXIÓN: {e}")
    import traceback
    traceback.print_exc()

