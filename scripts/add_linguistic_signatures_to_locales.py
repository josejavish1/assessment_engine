#!/usr/bin/env python3
"""Inject linguistic signature tokens into engine_config/locales.json across all 6 locales."""

from __future__ import annotations

import json
from pathlib import Path

LOCALES_FILE = Path(__file__).resolve().parents[1] / "engine_config/locales.json"

SIGNATURES = {
    "es": [" de ", " en ", " el ", " la ", " y ", " del ", " por ", " para "],
    "en": [" the ", " in ", " of ", " and ", " to ", " a ", " for ", " with "],
    "pt": [" do ", " da ", " em ", " e ", " para ", " com ", " os ", " as "],
    "fr": [" le ", " la ", " et ", " dans ", " pour ", " avec ", " des ", " les "],
    "de": [" der ", " die ", " das ", " und ", " im ", " fuer ", " mit ", " von "],
    "ja": ["の", "に", "は", "を", "が", "で", "と", "して"],
}


def main() -> None:
    with open(LOCALES_FILE, "r", encoding="utf-8") as f:
        locales = json.load(f)

    for lang, tokens in SIGNATURES.items():
        if lang in locales:
            locales[lang]["linguistic_signature_tokens"] = tokens

    with open(LOCALES_FILE, "w", encoding="utf-8") as f:
        json.dump(locales, f, ensure_ascii=False, indent=2)

    print(f"Added linguistic_signature_tokens across {len(SIGNATURES)} locales.")


if __name__ == "__main__":
    main()
