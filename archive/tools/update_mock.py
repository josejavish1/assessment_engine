import json

path = "working/smoke_moeve/commercial_report_payload.json"
with open(path, "r", encoding="utf-8-sig") as f:
    data = json.load(f)

data["commercial_summary"] = {
  "deal_flash": {
    "purchase_driver": "Incumplimiento normativo (DORA/NIS2) y riesgo operativo crítico.",
    "ntt_win_theme": "Financiación de la transformación mediante ahorros OPEX en Redes."
  },
  "why_now_bullets": [
    "Riesgo Legal y de Continuidad: Puntuación crítica en Resiliencia (2.0) y Seguridad (1.8).",
    "Parálisis Tecnológica: El legacy impide lanzar nuevos productos al ritmo del mercado."
  ],
  "how_we_win_bullets": [
    "Vector de Entrada (Wedge): Assessment de ciberseguridad rápido para materializar el riesgo ante el Board.",
    "Lock-in: Servicios gestionados integrales financiados por la modernización previa."
  ],
  "estimated_tam": "900.000€ - 2.500.000€"
}

with open(path, "w", encoding="utf-8-sig") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("JSON mocked successfully.")
