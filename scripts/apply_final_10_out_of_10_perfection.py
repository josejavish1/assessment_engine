#!/usr/bin/env python3
"""Apply the 3 micro-refinements to reach the 10.0/10.0 absolute benchmark."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# 1. Update locales.json for T1 and T3 scorecard alignment
loc_path = REPO_ROOT / "engine_config/locales.json"
with open(loc_path, "r", encoding="utf-8") as f:
    locales = json.load(f)

# T1: Fix cause alignment to Thermal/HVAC
locales["es"]["ch3_scorecard_by_tower"]["T1"] = (
    "Con una puntuación técnica de {score_val} sobre 5,0 ({maturity_tier_label}), las instalaciones de {client_name} se sitúan en el límite de tramo del Nivel 3. La solvencia de los sistemas de extinción y redundancia eléctrica ({strongest_pillar_name}, {strongest_pillar_score}/5,0) contrasta con la fragilidad térmica en salas de proceso ({weakest_pillar_name}, {weakest_pillar_score}/5,0), donde la ausencia de confinamiento de pasillos y el déficit de climatización de precisión en cuartos de planta amenazan la continuidad de los servidores expuestos a partículas fabriles."
)
locales["en"]["ch3_scorecard_by_tower"]["T1"] = (
    "Scoring a technical maturity of {score_val} out of 5.0 ({maturity_tier_label}), datacenter facilities across {client_name} sit at the threshold of Level 3. Solid electromechanical power and fire suppression defenses ({strongest_pillar_name}, {strongest_pillar_score}/5.0) contrast with thermal fragility in processing rooms ({weakest_pillar_name}, {weakest_pillar_score}/5.0), where absent aisle containment and lack of precision cooling in plant rooms threaten edge servers exposed to industrial dust."
)

# T3: Fix cause alignment to NetOps & Observability
locales["es"]["ch3_scorecard_by_tower"]["T3"] = (
    "La infraestructura de red alcanza una calificación de {score_val} sobre 5,0 ({maturity_tier_label}). La robustez del switching en sedes centrales ({strongest_pillar_name}, {strongest_pillar_score}/5,0) contrasta con el déficit de automatización y supervisión ({weakest_pillar_name}, {weakest_pillar_score}/5,0), donde la dependencia de configuraciones manuales por consola CLI y la ceguera de telemetría en la frontera IT/OT dificultan el diagnóstico ágil de anomalías en sedes remotas."
)
locales["en"]["ch3_scorecard_by_tower"]["T3"] = (
    "Network infrastructure achieves a technical score of {score_val} out of 5.0 ({maturity_tier_label}). Campus switching resilience across headquarters ({strongest_pillar_name}, {strongest_pillar_score}/5.0) contrasts with the gap in automation and observability ({weakest_pillar_name}, {weakest_pillar_score}/5.0), where manual CLI configuration workflows and telemetry blindness across the IT/OT boundary impede agile fault isolation across remote sites."
)

# Symmetrize pt, fr, de, ja
base_keys = set(locales["en"].keys())
for lang in ["pt", "fr", "de", "ja"]:
    if lang in locales:
        locales[lang]["ch3_scorecard_by_tower"] = locales["en"]["ch3_scorecard_by_tower"]

with open(loc_path, "w", encoding="utf-8") as f:
    json.dump(locales, f, indent=2, ensure_ascii=False)

print("Updated T1 and T3 scorecard alignment in locales.json!")

# 2. Fix T9 Bullet 1 (remove solution naming (Intune/Autopilot))
t9_path = REPO_ROOT / "working/molins/T9/blueprint_t9_payload.json"
with open(t9_path, "r", encoding="utf-8") as f:
    t9 = json.load(f)

t9["cross_capabilities_analysis"]["common_deficiency_patterns"][0] = (
    "Elevada carga de soporte manual en el ciclo de vida del puesto de trabajo corporativo: La preparación artesanal de portátiles mediante imágenes estáticas y sin flujos automatizados de aprovisionamiento directo al usuario final consume cientos de horas de técnicos y eleva los costes de gestión de incidencias de configuración."
)

with open(t9_path, "w", encoding="utf-8") as f:
    json.dump(t9, f, indent=2, ensure_ascii=False)

print("Updated T9 payload: purged solution telegraphing from pattern #1!")
