#!/usr/bin/env python3
"""Harmonize tomo_ch4_t10_title across all 6 locales."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = REPO_ROOT / "engine_config" / "locales.json"

T10_TITLES = {
    "es": "4.10. Sistemas Críticos de Expedición y Operaciones Locales (T10)",
    "en": "4.10. Mission-Critical Plant Operations & Local Infrastructure (T10)",
    "pt": "4.10. Sistemas Críticos de Expedição e Operações Locais (T10)",
    "fr": "4.10. Systèmes Critiques d'Expédition et Opérations Locales (T10)",
    "de": "4.10. Kritische Versandsysteme und Lokale Infrastruktur (T10)",
    "ja": "4.10. 重要出荷システムおよびローカルインフラ（T10）",
}


def main() -> None:
    with open(LOCALES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for loc, title in T10_TITLES.items():
        if loc in data:
            data[loc]["tomo_ch4_t10_title"] = title

    with open(LOCALES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Successfully harmonized tomo_ch4_t10_title across all 6 locales!")


if __name__ == "__main__":
    main()
