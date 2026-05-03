import os
from pathlib import Path
import vertexai
from vertexai.generative_models import GenerativeModel

# Forzar el uso del usuario real de gcloud, no service accounts
if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
    del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

try:
    print("Probando conexión con el usuario real de gcloud (ADC)...")
    # Usa el proyecto por defecto de gcloud
    vertexai.init(location="europe-west1")
    model = GenerativeModel("gemini-1.5-pro")
    response = model.generate_content("Responde 'Usuario de gcloud validado'.")
    print(f"✅ ¡ÉXITO! {response.text.strip()}")
except Exception as e:
    print(f"❌ FALLO con el usuario real: {e}")
    print(
        "\nSi falla, es probable que tu token haya caducado. Necesitas ejecutar en tu terminal: gcloud auth application-default login"
    )
