#!/usr/bin/env python3
"""Add quality gate test probe tokens to engine_config/locales.json across all 6 locales."""

from __future__ import annotations

import json
from pathlib import Path

LOCALES_FILE = Path(__file__).resolve().parents[1] / "engine_config/locales.json"

PROBE_CONFIG = {
    "es": {
        "banned_placeholder_markers": [
            "no disponible",
            "not available",
            "sin datos",
            "modulo de introduccion",
            "placeholder",
            "to be determined",
            "undefined",
        ],
        "section_2_1_probe_tokens": ["objetivo y alcance", "alcance"],
        "section_2_2_probe_tokens": ["descripcion de la plataforma", "plataforma"],
        "section_cmmi_probe_tokens": ["escala analitica", "cmmi"],
        "section_ch3_probe_tokens": ["cuadro de mando", "diagnostico tecnico"],
        "table6_strength_probe_tokens": ["fortaleza", "identificada"],
    },
    "en": {
        "banned_placeholder_markers": [
            "not available",
            "no data",
            "introduction module",
            "placeholder",
            "to be determined",
            "undefined",
        ],
        "section_2_1_probe_tokens": ["objective and scope", "scope"],
        "section_2_2_probe_tokens": ["platform description", "platform"],
        "section_cmmi_probe_tokens": ["analytical scale", "cmmi"],
        "section_ch3_probe_tokens": ["dashboard", "technical diagnosis"],
        "table6_strength_probe_tokens": ["strength", "identified"],
    },
    "pt": {
        "banned_placeholder_markers": [
            "nao disponivel",
            "not available",
            "sem dados",
            "modulo de introducao",
            "placeholder",
            "to be determined",
            "undefined",
        ],
        "section_2_1_probe_tokens": ["objetivo e escopo", "escopo"],
        "section_2_2_probe_tokens": ["descricao da plataforma", "plataforma"],
        "section_cmmi_probe_tokens": ["escala analitica", "cmmi"],
        "section_ch3_probe_tokens": ["painel", "diagnostico tecnico"],
        "table6_strength_probe_tokens": ["fortaleza", "identificada"],
    },
    "fr": {
        "banned_placeholder_markers": [
            "non disponible",
            "not available",
            "sans donnees",
            "module d'introduction",
            "placeholder",
            "to be determined",
            "undefined",
        ],
        "section_2_1_probe_tokens": ["objectif et portee", "portee"],
        "section_2_2_probe_tokens": ["description de la plateforme", "plateforme"],
        "section_cmmi_probe_tokens": ["echelle analytique", "cmmi"],
        "section_ch3_probe_tokens": ["tableau de bord", "diagnostic technique"],
        "table6_strength_probe_tokens": ["force", "identifiee"],
    },
    "ja": {
        "banned_placeholder_markers": [
            "利用不可",
            "not available",
            "データなし",
            "導入モジュール",
            "placeholder",
            "to be determined",
            "undefined",
        ],
        "section_2_1_probe_tokens": ["目的と範囲", "範囲"],
        "section_2_2_probe_tokens": ["プラットフォームの説明", "プラットフォーム"],
        "section_cmmi_probe_tokens": ["分析スケール", "cmmi"],
        "section_ch3_probe_tokens": ["ダッシュボード", "技術診断"],
        "table6_strength_probe_tokens": ["強み", "特定"],
    },
    "de": {
        "banned_placeholder_markers": [
            "nicht verfuegbar",
            "not available",
            "keine daten",
            "einfuehrungsmodul",
            "placeholder",
            "to be determined",
            "undefined",
        ],
        "section_2_1_probe_tokens": ["ziel und geltungsbereich", "geltungsbereich"],
        "section_2_2_probe_tokens": ["plattformbeschreibung", "plattform"],
        "section_cmmi_probe_tokens": ["analytische skala", "cmmi"],
        "section_ch3_probe_tokens": ["dashboard", "technische diagnose"],
        "table6_strength_probe_tokens": ["staerke", "identifiziert"],
    },
}


def main() -> None:
    with open(LOCALES_FILE, "r", encoding="utf-8") as f:
        locales = json.load(f)

    for lang, probes in PROBE_CONFIG.items():
        if lang in locales:
            for k, v in probes.items():
                locales[lang][k] = v

    with open(LOCALES_FILE, "w", encoding="utf-8") as f:
        json.dump(locales, f, ensure_ascii=False, indent=2)

    print(f"Added quality gate probe tokens across {len(PROBE_CONFIG)} locales.")


if __name__ == "__main__":
    main()
