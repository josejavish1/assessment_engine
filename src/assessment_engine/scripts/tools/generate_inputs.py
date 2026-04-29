"""
Módulo generate_inputs.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import json
import random
from pathlib import Path

root = Path(".")
client = "ivirma"
client_dir = root / "working" / client
client_dir.mkdir(parents=True, exist_ok=True)

towers = ["T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9"]
responses_lines = []

tower_targets = {
    "T2": (3.0, 4.0),
    "T3": (1.5, 2.5),
    "T4": (3.0, 4.0),
    "T5": (1.5, 2.5),
    "T6": (1.5, 2.5),
    "T7": (2.0, 3.0),
    "T8": (2.0, 3.0),
    "T9": (2.0, 3.0),
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

(client_dir / "respuestas_ivirma.txt").write_text(
    "\n".join(responses_lines), encoding="utf-8"
)

context_text = """
Notas de la reunión de Assessment Tecnológico de IVIRMA.
Mandato de KKR: duplicar facturación a 1.300M€. Fuerte M&A.
Stack: Microsoft Azure, SAP, Salesforce.
Riesgo: Fragmentación de red, datos de salud críticos, NIS2/RGPD.
"""
(client_dir / "contexto_ivirma.txt").write_text(context_text.strip(), encoding="utf-8")
