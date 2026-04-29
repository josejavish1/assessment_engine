"""
Módulo generate_smoke_data.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import json
import random
from pathlib import Path

root = Path(".")
client = "smoke_ivirma"
client_dir = root / "working" / client
client_dir.mkdir(parents=True, exist_ok=True)

towers = ["T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9"]
responses_lines = []

# Asignamos rangos de madurez diferentes por torre para darle realismo
tower_targets = {
    "T2": (2.0, 3.0),  # Cómputo (Medio)
    "T3": (1.5, 2.5),  # Redes (Bajo)
    "T4": (2.5, 3.5),  # Datos (Medio-Alto)
    "T5": (1.0, 2.0),  # Resiliencia (Muy bajo - Riesgo crítico)
    "T6": (1.5, 2.5),  # Seguridad (Bajo - Riesgo normativo)
    "T7": (2.0, 3.0),  # ITSM (Medio)
    "T8": (3.0, 4.0),  # Cloud (Alto - Están en Azure)
    "T9": (2.5, 3.5),  # Workplace (Medio-Alto)
}

for t in towers:
    def_file = root / "engine_config" / "towers" / t / f"tower_definition_{t}.json"
    if def_file.exists():
        data = json.loads(def_file.read_text(encoding="utf-8"))
        min_s, max_s = tower_targets[t]
        for p in data.get("pillars", []):
            for k in p.get("kpis", []):
                score = round(random.uniform(min_s, max_s), 1)
                responses_lines.append(f"{k['kpi_id']}.PR1: {score}")

responses_path = client_dir / "responses.txt"
responses_path.write_text("\n".join(responses_lines), encoding="utf-8")

context_text = """
Notas de la reunión de Assessment Tecnológico de IVIRMA (Smoke Test).

Contexto de Negocio:
La compañía está en fase de expansión inorgánica internacional impulsada por KKR, con el objetivo de duplicar la facturación a 1.300M€.
La principal preocupación del CEO es asegurar la integración rápida de nuevas clínicas manteniendo el nivel de excelencia clínica y operativa.

Tecnología:
El proveedor estratégico cloud es Microsoft Azure. Sin embargo, el crecimiento ha fragmentado la red de comunicaciones.
El almacenamiento de imágenes médicas e historiales clínicos es el core absoluto del negocio, pero no existe una estrategia inmutable de recuperación (Vault).

Seguridad y Normativa:
El CISO está alarmado por el aumento de incidentes de ransomware en el sector salud. Además, son conscientes de que la inminente aplicación de la directiva NIS2 en Europa les afecta directamente como operadores esenciales de salud, y actualmente su infraestructura no garantiza el cumplimiento.

Operaciones:
El soporte a usuarios (médicos y embriólogos) es muy manual, con un ITSM básico. Faltan procesos industrializados y visibilidad de los activos (CMDB inexistente), lo que choca con la agilidad necesaria para la expansión.
"""
context_path = client_dir / "context.txt"
context_path.write_text(context_text.strip(), encoding="utf-8")
print(
    f"✅ Archivos de entrada (contexto y {len(responses_lines)} respuestas) generados."
)
