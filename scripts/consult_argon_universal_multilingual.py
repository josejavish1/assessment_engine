#!/usr/bin/env python3
"""Consult gemini-4-argon regarding true language-agnostic ontology resolution."""

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

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

AUDIT_PROMPT = """You are 'gemini-4-argon', Principal Enterprise Architect and Supreme Code Quality Arbiter for the Assessment Engine.

CRITICAL USER MANDATE & ARCHITECTURAL CRITIQUE:
The user has delivered a devastatingly accurate architectural critique regarding our approach to multilingualism:

"Pero, ¿qué ocurre si mañana es un idioma diferente a los 6 que tenemos? ¿Realmente, tal y como lo estás programando, es Top Tier 1 mundial? Recuerda, no quiero nada hardcodeado. El objetivo es que sirva para CUALQUIER empresa del mundo, desde mediana a Top Tier 1 mundial, de cualquier vertical, en CUALQUIER IDIOMA. El código debe estar 100% en inglés, nada de español. ¿Qué opinas de lo que te acabo de decir?"

THE FLAW:
We just spent time expanding `engine_config/taxonomy_multilingual.json` to hardcode translations for KPIs in exactly 6 locales (`en`, `es`, `pt`, `fr`, `de`, `ja`).
If a client requests a report in Italian (`it`), Arabic (`ar`), or Mandarin (`zh`) tomorrow, the system breaks. The AST compiler will hit `KeyError` or fall back to English because `taxonomy_multilingual.json` lacks those keys.
A true Tier-1 system in the generative AI era does not rely on static N-language dictionaries for domain taxonomy. It relies on a single canonical English ontology and performs zero-shot dynamic translation/resolution for ANY requested ISO language code.

YOUR MISSION:
Deliver a definitive architectural verdict on the user's critique and provide a multi-phase master plan to achieve TRUE Universal Multilingualism (Language Agnosticism).

The plan must address:
- PHASE 1: The Canonical Singularity. How to structure the engine so that ONLY English exists in definitions (`tower_definition_*.json`), completely deleting the need for `taxonomy_multilingual.json` for KPI names.
- PHASE 2: Dynamic Semantic Translation. How to inject a translation phase during the `build_client_delivery_suite.py` ingestion/synthesis process. The LLM should take the canonical English ontology and the target `doc_lang` (e.g., 'ar', 'it', 'ko') and synthesize the localized KPI names directly into the payload.
- PHASE 3: AST Compiler Agnosticism. How the AST compiler (`payload_to_ast.py`) should just read the already-localized strings from the `blueprint_payload.json` without ever looking up a taxonomy dictionary.

Constraints:
- Respond in 100% Technical English.
- Be brutally honest about the static dictionary anti-pattern.
- Do not provide code implementation yet; provide the rigorous Architectural Plan.

Deliver your verdict now.
"""

def main() -> None:
    print(f"Submitting universal multilingual request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    audit_report = response.text
    out_file = REPO_ROOT / "docs/architecture/ARGON_UNIVERSAL_MULTILINGUAL_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(audit_report, encoding="utf-8")
    print(f"\nArchitecture Plan generated successfully. Report written to: {out_file}\n")
    print("=" * 80)
    print(audit_report[:3500])

if __name__ == "__main__":
    main()
