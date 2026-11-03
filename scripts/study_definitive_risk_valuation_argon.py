#!/usr/bin/env python3
"""Argon-4 Master Consultation: Eradication of the Diacritic Dictionary Antipattern.

The user firmly identified an architectural antipattern:
"oye pero que dice de '5. Restauración del 100% de Tildes RAE en las Fichas del Punto 4.4... esto es un antipatrón no debería existir ningún documento con tildes de palabra la forma de solucionarlo ya l habiamos hablado anteriormente y la solución era mucho más elegante, recuerda que no quiero nada hardcodeado recuerda que el objetivo es que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial, de cualquier vertical, en cualquier idioma, y el código debe estar 100% en ingles nada de español ni una sola palabra, el español solo es el idioma que hablamos tu y yo y uno de los idiomas de la salida de los entregables."

Mandate for Argon-4:
1. Explain why post-processing word-replacement dictionaries (orthographic_restoration_map) and language-specific regexes in the compiler layer are an engineering anti-pattern.
2. Define the elegant, pure architecture:
   - Compilers MUST NOT act as spell checkers or maintain word-by-word replacement tables.
   - The payload itself (generated upstream by AI orchestrators or input fixtures) must be natively well-formed UTF-8 in the target language.
   - Upstream generation prompts enforce native orthographic compliance at generation time.
3. Formulate the cleanup plan:
   - Remove the `orthographic_restoration_map` dictionary from `locales.json`.
   - Remove language-specific regexes from `localization.py` and `payload_to_ast.py`.
   - Ensure `working/molins/T1` and `T2` payloads contain clean, native UTF-8 Spanish text directly in their finding strings.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    prompt = """
Role: Chief Systems Architect & Principal Software Engineer (Google Core Infrastructure / Tier-1 Management Consulting).

USER'S HARD REALITY CHECK & ARCHITECTURAL DIRECTIVE:
The user strongly challenged the previous implementation:
"oye pero que dice de '5. Restauración del 100% de Tildes RAE en las Fichas del Punto 4.4... esto es un antipatrón no debería existir ningún documento con tildes de palabra la forma de solucionarlo ya la habíamos hablado anteriormente y la solución era mucho más elegante, recuerda que no quiero nada hardcodeado recuerda que el objetivo es que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial, de cualquier vertical, en cualquier idioma, y el código debe estar 100% en ingles nada de español ni una sola palabra, el español solo es el idioma que hablamos tu y yo y uno de los idiomas de la salida de los entregables."

CRITICAL ANALYSIS REQUIRED:
1. Why is maintaining an `orthographic_restoration_map` (a list of hundreds of Spanish words to patch missing accents) or language-specific regexes (`cion`/`sion`) in the AST compiler/localization layer a severe engineering anti-pattern?
   - Architectural Layer Violation: Compilers and AST translators should compile data structures, not act as a runtime spell-checker or NLP dictionary.
   - Scalability Failure: Does not scale to German (umlauts), French (accents/cedillas), Japanese, Portuguese, etc. It is brittle, incomplete, and creates massive configuration debt.
   - Hardcoding Violation: Law #2 (Zero Hardcoding) is breached by hardcoding language-specific word mappings.
   - Codebase Purity: Law #3 (100% Technical English Codebase) is compromised if Spanish morphology or rules pollute Python modules.

2. What is the canonical, elegant solution previously agreed upon (and documented in RFC 029)?
   - Clean Payloads at the Source (Upstream Governance): The data payload (`blueprint_payload.json`) must be natively well-formed UTF-8 in the target language at generation time.
   - The compiler takes the payload's text as authoritative and renders it faithfully without intrusive runtime string mutations or hardcoded dictionaries.
   - Sanitize the payload fixtures directly once at rest, and govern upstream AI prompts so generated text is natively accented.

3. Step-by-Step Eradication & Refactoring Plan:
   - Purge `orthographic_restoration_map` from `engine_config/locales.json`.
   - Revert `restore_locale_diacritics` to a transparent pass-through or clean no-op, removing Spanish morphological regexes.
   - Remove diacritic restoration monkey-patches from `payload_to_ast.py`.
   - Ensure the fixture payloads (`working/molins/T1/` and `T2/`) have clean, native UTF-8 Spanish text in their findings and titles.

YOUR TASK:
Synthesize an authoritative Architectural Cleanup Report in Markdown:
1. Ratify the user's critique with uncompromising technical rigor.
2. Define the exact refactoring specifications for `locales.json`, `localization.py`, and `payload_to_ast.py`.
3. Deliver a definitive VERDICT: PASS.
"""

    print(f"Requesting architectural cleanup blueprint from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/ARCHITECTURAL_CLEANUP_DIACRITICS_ANTIPATTERN_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: ARCHITECTURAL CLEANUP ON DIACRITICS ANTIPATTERN")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nBlueprint saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
