#!/usr/bin/env python3
"""Inject consolidated and annex filename markers into engine_config/locales.json."""

from __future__ import annotations

import json
from pathlib import Path

LOCALES_FILE = Path(__file__).resolve().parents[1] / "engine_config/locales.json"

CONFIG = {
    "en": {
        "consolidated_filename_markers": ["volume", "consolidated", "master", "executive"],
        "annex_filename_markers": ["annex", "technical_annex"],
    },
    "es": {
        "consolidated_filename_markers": ["tomo", "volumen", "consolidado", "diagnostico_asis"],
        "annex_filename_markers": ["anexo", "anexo_tecnico"],
    },
    "pt": {
        "consolidated_filename_markers": ["tomo", "volume", "consolidado", "diagnostico_asis"],
        "annex_filename_markers": ["anexo", "anexo_tecnico"],
    },
    "fr": {
        "consolidated_filename_markers": ["tome", "volume", "consolide", "consolidé", "diagnostic_asis"],
        "annex_filename_markers": ["annexe", "annexe_technique"],
    },
    "ja": {
        "consolidated_filename_markers": ["総合診断", "マスター", "ボリューム"],
        "annex_filename_markers": ["別紙", "技術別紙"],
    },
    "de": {
        "consolidated_filename_markers": ["band", "gesamtbericht", "konsolidiert", "gesamtdiagnose"],
        "annex_filename_markers": ["anhang", "technischer_anhang"],
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

    print(f"Updated locales.json with filename markers across {len(CONFIG)} locales.")


if __name__ == "__main__":
    main()
