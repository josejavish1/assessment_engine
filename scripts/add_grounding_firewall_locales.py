#!/usr/bin/env python3
"""Inject speculative artifact regexes and clause prefixes into engine_config/locales.json."""

from __future__ import annotations

import json
from pathlib import Path

LOCALES_FILE = Path(__file__).resolve().parents[1] / "engine_config/locales.json"

DATA_BY_LOCALE = {
    "es": {
        "speculative_artifact_regexes": [
            "pinzas?\\s+amperim[eé]tricas?",
            "c[aá]maras?\\s+t[eé]rmicas?",
            "mult[ií]metros?",
            "placas?\\s+de\\s+fabricante",
            "especificaciones?\\s+de\\s+placa",
            "formularios?\\s+impresos?",
            "firmas?\\s+manuscritas?",
            "libretas?\\s+f[ií]sicas?",
        ],
        "speculative_clause_prefix_regex": r"(?:mediante|a trav[eé]s de|utilizando|usando|basado en|recurriendo a)\s+[^,\.;]*",
    },
    "en": {
        "speculative_artifact_regexes": [
            "clamp\\s+meters?",
            "thermal\\s+cameras?",
            "multimeters?",
            "nameplates?",
            "manufacturer\\s+plates?",
            "printed\\s+forms?",
            "handwritten\\s+signatures?",
            "physical\\s+logbooks?",
            "paper\\s+forms?",
        ],
        "speculative_clause_prefix_regex": r"(?:by means of|via|utilizing|using|based on|relying on)\s+[^,\.;]*",
    },
    "pt": {
        "speculative_artifact_regexes": [
            "alicates?\\s+amperim[eé]tricos?",
            "c[aâ]meras?\\s+t[eé]rmicas?",
            "mult[ií]metros?",
            "placas?\\s+do\\s+fabricante",
            "especifica[cç][oõ]es?\\s+da\\s+placa",
            "formul[aá]rios?\\s+impressos?",
            "assinaturas?\\s+manuscritas?",
            "cadernos?\\s+f[ií]sicos?",
        ],
        "speculative_clause_prefix_regex": r"(?:por meio de|atrav[eé]s de|utilizando|usando|com base em)\s+[^,\.;]*",
    },
    "fr": {
        "speculative_artifact_regexes": [
            "pinces?\\s+amp[eè]rem[eè]triques?",
            "cam[eé]ras?\\s+thermiques?",
            "multim[eè]tres?",
            "plaques?\\s+signal[eé]tiques?",
            "sp[eé]cifications?\\s+de\\s+plaque",
            "formulaires?\\s+imprim[eé]s?",
            "signatures?\\s+manuscrites?",
            "registres?\\s+papiers?",
        ],
        "speculative_clause_prefix_regex": r"(?:au moyen de|a travers|en utilisant|bas[eé] sur)\s+[^,\.;]*",
    },
    "ja": {
        "speculative_artifact_regexes": [
            "クランプメーター",
            "サーモグラフィ",
            "テスター",
            "銘板仕様",
            "印刷された用紙",
            "手書き署名",
            "紙の台帳",
        ],
        "speculative_clause_prefix_regex": r"(?:を用いて|を使用して|に基づいて)\s*",
    },
    "de": {
        "speculative_artifact_regexes": [
            "stromzangen?",
            "w[aä]rmebildkameras?",
            "multimetern?",
            "typenschildern?",
            "gedruckte\\s+formulare?",
            "handschriftliche\\s+unterschriften?",
            "physische\\s+protokollb[uü]cher?",
        ],
        "speculative_clause_prefix_regex": r"(?:mittels|durch|unter verwendung von|basierend auf)\s+[^,\.;]*",
    },
}


def main() -> None:
    with open(LOCALES_FILE, "r", encoding="utf-8") as f:
        locales = json.load(f)

    for lang, data in DATA_BY_LOCALE.items():
        if lang in locales:
            locales[lang]["speculative_artifact_regexes"] = data[
                "speculative_artifact_regexes"
            ]
            locales[lang]["speculative_clause_prefix_regex"] = data[
                "speculative_clause_prefix_regex"
            ]

    with open(LOCALES_FILE, "w", encoding="utf-8") as f:
        json.dump(locales, f, ensure_ascii=False, indent=2)

    print(f"Updated engine_config/locales.json with grounding firewall rules across {len(DATA_BY_LOCALE)} locales.")


if __name__ == "__main__":
    main()
