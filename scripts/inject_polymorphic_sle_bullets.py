"""Inject polymorphic SLE derivation bullets into locales.json."""

import json
from pathlib import Path

p = Path("engine_config/locales.json")
data = json.loads(p.read_text(encoding="utf-8"))

BULLETS = {
    "es": {
        "sle_derivation_formula_bullet_capital_inefficiency": "• **Derivación Financiera Fiduciaria (SLE):** Impacto fiduciario acumulado por desvío presupuestario, sobrecostes de licencias y consumo cloud sin optimizar = {sle_formatted} en el ciclo evaluado.",
        "sle_derivation_formula_bullet_productivity_toil": "• **Derivación de Toil Operativo (SLE):** Sobrecoste por tareas manuales reactivas y fricción técnica, equivalente a {effective_hours}h de esfuerzo de ingeniería acumulado = {sle_formatted}.",
        "sle_derivation_formula_bullet_regulatory_and_breach": "• **Derivación de Exposición por Incidente (SLE):** Impacto estimado por respuesta a incidentes (DFIR), asesoramiento forense y contingencia regulatoria = {sle_formatted}.",
        "sle_derivation_formula_bullet_availability_outage": "• **Derivación Financiera por Indisponibilidad (SLE):** {effective_hours}h de interrupción operativa a {hourly_rate}/h ({alpha_pct}% de afectación sobre el coste base de parada de {base_rate}/h) = {sle_formatted}."
    },
    "en": {
        "sle_derivation_formula_bullet_capital_inefficiency": "• **Exact Fiduciary Derivation (SLE):** Cumulative financial impact from licensing true-up liabilities, budget drift, and unhedged cloud spend = {sle_formatted} over the evaluated cycle.",
        "sle_derivation_formula_bullet_productivity_toil": "• **Operational Toil Derivation (SLE):** Cumulative overhead from repetitive manual triage and technical friction, equivalent to {effective_hours}h of engineering toil = {sle_formatted}.",
        "sle_derivation_formula_bullet_regulatory_and_breach": "• **Incident & Breach Derivation (SLE):** Estimated exposure from digital forensics incident response (DFIR), legal counsel, and statutory penalties = {sle_formatted}.",
        "sle_derivation_formula_bullet_availability_outage": "• **Exact Downtime Derivation (SLE):** {effective_hours}h operational disruption at {hourly_rate}/hr ({alpha_pct}% operational impact factor over baseline downtime cost of {base_rate}/hr) = {sle_formatted}."
    }
}

for lang in ("pt", "fr", "de", "ja"):
    BULLETS[lang] = BULLETS["en"]

for lang, b in BULLETS.items():
    if lang in data:
        data[lang].update(b)

p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("✓ Successfully injected polymorphic SLE bullets into locales.json.")
