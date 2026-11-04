#!/usr/bin/env python3
"""Add default_risk_scenario_title across all 6 locales."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = REPO_ROOT / "engine_config" / "locales.json"

KEYS = {
    "es": "Escenario de Riesgo",
    "en": "Risk Scenario",
    "pt": "Cenário de Risco",
    "fr": "Scénario de Risque",
    "de": "Risikoszenario",
    "ja": "リスクシナリオ",
}


def main() -> None:
    with open(LOCALES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for loc, text in KEYS.items():
        if loc in data:
            data[loc]["default_risk_scenario_title"] = text

    with open(LOCALES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Successfully added default_risk_scenario_title across all 6 locales!")


if __name__ == "__main__":
    main()
