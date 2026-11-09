#!/usr/bin/env python3
"""Inject conjunctions, bare severity enum tokens, and chapter 2 probes into engine_config/locales.json."""

from __future__ import annotations

import json
from pathlib import Path

LOCALES_FILE = Path(__file__).resolve().parents[1] / "engine_config/locales.json"

CONFIG = {
    "en": {
        "coordinating_conjunction_regex": r"(?:and|or)",
        "bare_severity_enum_tokens": [
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
            "MODERATE",
            "SEVERE",
            "ELEVATED",
        ],
        "section_ch2_probe_tokens": [
            "methodological framework",
            "methodology",
            "objective and scope",
        ],
    },
    "es": {
        "coordinating_conjunction_regex": r"(?:y|o|e|u)",
        "bare_severity_enum_tokens": [
            "BAJO",
            "MEDIO",
            "ALTO",
            "CRITICO",
            "CRÍTICO",
            "MODERADO",
            "ELEVADO",
            "SEVERO",
        ],
        "section_ch2_probe_tokens": [
            "marco metodologico",
            "marco metodológico",
            "objetivo, alcance y marco",
        ],
    },
    "pt": {
        "coordinating_conjunction_regex": r"(?:e|ou)",
        "bare_severity_enum_tokens": [
            "BAIXO",
            "MEDIO",
            "MÉDIO",
            "ALTO",
            "CRITICO",
            "CRÍTICO",
            "MODERADO",
            "ELEVADO",
            "SEVERO",
        ],
        "section_ch2_probe_tokens": [
            "quadro metodologico",
            "quadro metodológico",
            "objetivo, escopo e metodologia",
        ],
    },
    "fr": {
        "coordinating_conjunction_regex": r"(?:et|ou)",
        "bare_severity_enum_tokens": [
            "FAIBLE",
            "MOYEN",
            "ELEVE",
            "ÉLEVÉ",
            "CRITIQUE",
            "MODERE",
            "MODÉRÉ",
            "SEVERE",
            "SÉVÈRE",
        ],
        "section_ch2_probe_tokens": [
            "cadre methodologique",
            "cadre méthodologique",
            "objectif, portee et cadre",
        ],
    },
    "ja": {
        "coordinating_conjunction_regex": r"(?:および|または|並びに)",
        "bare_severity_enum_tokens": [
            "低",
            "中",
            "高",
            "重大",
            "緊急",
            "警告",
        ],
        "section_ch2_probe_tokens": [
            "方法論の枠組み",
            "方法論",
            "目的、範囲および方法論",
        ],
    },
    "de": {
        "coordinating_conjunction_regex": r"(?:und|oder)",
        "bare_severity_enum_tokens": [
            "NIEDRIG",
            "MITTEL",
            "HOCH",
            "KRITISCH",
            "MODERAT",
            "SCHWER",
        ],
        "section_ch2_probe_tokens": [
            "methodischer rahmen",
            "methodik",
            "ziel, geltungsbereich und methodik",
        ],
    },
}


def main() -> None:
    with open(LOCALES_FILE, "r", encoding="utf-8") as f:
        locales = json.load(f)

    for lang, data in CONFIG.items():
        if lang in locales:
            for k, v in data.items():
                locales[lang][k] = v

    with open(LOCALES_FILE, "w", encoding="utf-8") as f:
        json.dump(locales, f, ensure_ascii=False, indent=2)

    print(f"Updated locales.json with conjunctions, bare enums, and ch2 probes across {len(CONFIG)} locales.")


if __name__ == "__main__":
    main()
