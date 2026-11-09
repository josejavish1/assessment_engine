#!/usr/bin/env python3
"""Inject universal Tri-Modal scorecard commentary templates into locales.json."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
loc_path = REPO_ROOT / "engine_config/locales.json"

with open(loc_path, "r", encoding="utf-8") as f:
    locales = json.load(f)

templates_es = {
    "scorecard_commentary_low": "Con una calificación técnica de {score_val} sobre 5,0 ({maturity_tier_label}), el dominio de {tower_name} en {client_name} se sitúa en un nivel de exposición operativa severa. La falta de formalización técnica y automatización se concentra críticamente en el vector de {weakest_pillar_name} ({weakest_pillar_score}/5,0), lo que condiciona la resiliencia del dominio y exige priorizar su remediación estructural.",
    "scorecard_commentary_mid": "Evaluado en {score_val} sobre 5,0 ({maturity_tier_label}), el dominio de {tower_name} en {client_name} sostiene la operativa cotidiana sobre procedimientos eminentemente artesanales y reactivos. La mayor área de atención técnica recae en el vector de {weakest_pillar_name} ({weakest_pillar_score}/5,0), marcando la prioridad de estandarización para evitar que el crecimiento de la actividad desborde la capacidad del equipo.",
    "scorecard_commentary_high": "Con una valoración técnica consolidada de {score_val} sobre 5,0 ({maturity_tier_label}), el dominio de {tower_name} en {client_name} cuenta con una base tecnológica sólida y procedimentada. El reto estratégico del área no radica en la estabilidad básica, sino en maximizar la eficiencia y optimizar el vector de {weakest_pillar_name} ({weakest_pillar_score}/5,0) para habilitar servicios avanzados de valor al negocio."
}

templates_en = {
    "scorecard_commentary_low": "Scoring a technical maturity of {score_val} out of 5.0 ({maturity_tier_label}), the {tower_name} domain across {client_name} operates under acute operational exposure. Gaps in engineering formalization and automation are critically concentrated within {weakest_pillar_name} ({weakest_pillar_score}/5.0), constraining overall domain resilience and mandating prioritized structural remediation.",
    "scorecard_commentary_mid": "Evaluated at {score_val} out of 5.0 ({maturity_tier_label}), the {tower_name} domain across {client_name} sustains baseline operations through largely manual and reactive procedures. The primary technical bottleneck lies within {weakest_pillar_name} ({weakest_pillar_score}/5.0), representing the core standardization priority to prevent operational scaling from outstripping team capacity.",
    "scorecard_commentary_high": "With a consolidated technical maturity of {score_val} out of 5.0 ({maturity_tier_label}), the {tower_name} domain across {client_name} operates upon a dependable, structured engineering baseline. The primary strategic challenge is not basic survival, but maximizing efficiency and optimizing {weakest_pillar_name} ({weakest_pillar_score}/5.0) to deliver high-velocity business capabilities."
}

locales["es"].update(templates_es)
locales["en"].update(templates_en)

# Symmetrize pt, fr, de, ja
base_keys = set(locales["en"].keys())
for lang in ["pt", "fr", "de", "ja"]:
    if lang in locales:
        for k in base_keys:
            if k not in locales[lang] or isinstance(locales[lang][k], dict):
                locales[lang][k] = locales["en"][k]

with open(loc_path, "w", encoding="utf-8") as f:
    json.dump(locales, f, indent=2, ensure_ascii=False)

print(f"Successfully injected universal Tri-Modal scorecard templates into {loc_path}!")
