#!/usr/bin/env python3
"""Update scorecard template in locales.json to ensure zero verbatim duplication with transversal patterns."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
loc_path = REPO_ROOT / "engine_config/locales.json"

with open(loc_path, "r", encoding="utf-8") as f:
    locales = json.load(f)

scorecard_tmpl_es = "Con una calificación técnica de {score_val} sobre 5,0 ({maturity_tier_label}), el dominio de {tower_name} en {client_name} opera bajo un régimen donde la estabilidad cotidiana contrasta con la necesidad de consolidar gobernanza y automatización técnica. La mayor área de atención se concentra en el vector de {weakest_pillar_name} ({weakest_pillar_score}/5,0), marcando la prioridad de modernización estructural del área."
scorecard_tmpl_en = "Achieving a technical maturity score of {score_val} out of 5.0 ({maturity_tier_label}), the {tower_name} domain across {client_name} exhibits an operational posture where baseline stability contrasts with the need to formalize engineering governance and automation. The primary capability requiring structural modernization is concentrated within {weakest_pillar_name} ({weakest_pillar_score}/5.0)."

locales["es"]["ch3_scorecard_by_tower"] = {f"T{i}": scorecard_tmpl_es for i in range(1, 11)}
locales["en"]["ch3_scorecard_by_tower"] = {f"T{i}": scorecard_tmpl_en for i in range(1, 11)}

base_keys = set(locales["en"].keys())
for lang in ["pt", "fr", "de", "ja"]:
    if lang in locales:
        for k in base_keys:
            if k not in locales[lang] or isinstance(locales[lang][k], dict):
                locales[lang][k] = locales["en"][k]

with open(loc_path, "w", encoding="utf-8") as f:
    json.dump(locales, f, indent=2, ensure_ascii=False)

print(f"Successfully updated scorecard template in {loc_path}!")
