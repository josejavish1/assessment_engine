#!/usr/bin/env python3
"""Consult gemini-4-argon on canonical maturity model scale unification (RFC 068).

Eliminates the split-brain between Chapter 2 introduction ranges and the engine's
canonical 5-tier maturity model:
- Level 1 (Initial): 1.00 - 1.79
- Level 2 (Repeatable): 1.80 - 2.59
- Level 3 (Defined): 2.60 - 3.39
- Level 4 (Managed): 3.40 - 4.19
- Level 5 (Optimized): 4.20 - 5.00
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
Role: Principal Enterprise Systems Architect, Advisory Fellow at Gartner, and Lead Ontologist for IT Maturity Frameworks.

OBJECTIVE:
Formulate the definitive architectural and editorial specification (RFC 068) to unify the Capability Maturity Model across the Assessment Engine ecosystem, eradicating an antipattern and semantic split-brain identified in Chapter 2.

THE PROBLEM IDENTIFIED:
In Chapter 2 (`tomo_ch2_intro`), the current text states:
"La evaluación de capacidades de infraestructura y operaciones se rige por el estándar internacional CMMI... Nivel 1 (Inicial / Ad-Hoc: 1,0 - 1,9), Nivel 2 (Gestionado / Reactivo: 2,0 - 2,9), Nivel 3 (Definido / Proactivo: 3,0 - 3,9), Nivel 4 (Medido Cuantitativamente: 4,0 - 4,9) y Nivel 5 (Optimización Continua: 5,00)."

THIS IS AN ANTI-PATTERN AND CAUSES A SEVERE SPLIT-BRAIN:
1. The Assessment Engine's authoritative single-source-of-truth (SSOT) defined in `domain/maturity_band.py` (`ANNEX_MATURITY_BANDS`) and `engine_config/locales.json` (`cmmi_level_1_range` through `cmmi_level_5_range`) defines the 5 tiers as:
   - Level 1 (Initial / Inicial): 1.00 to 1.79
   - Level 2 (Repeatable / Repetible): 1.80 to 2.59
   - Level 3 (Defined / Definido): 2.60 to 3.39
   - Level 4 (Managed / Gestionado): 3.40 to 4.19
   - Level 5 (Optimized / Optimizado): 4.20 to 5.00
2. Under the erroneous text in `tomo_ch2_intro`:
   - Score 2.55 is labeled "Gestionado" in the intro, but "Repetible" in the Cockpit and all 20 annexes!
   - Score 2.60 (Tower 1) is labeled "Nivel 2" in the intro, but correctly classified as "Nivel 3 (Definido)" in Table 2!
   - The sector benchmark 3.50 is correctly classified as "Nivel 4 (Gestionado)", but the intro claimed Level 4 starts at 4.0!

NON-NEGOTIABLE LAWS:
- 100% Technical English Codebase: Zero Spanish in Python code, docstrings, or variables.
- Multi-Tenant & Multi-Locale: All natural language string updates must be symmetric across all 6 locales (es, en, pt, fr, de, ja).
- Zero Hardcoding: The compiler must bind band labels dynamically via `band_key` and `format_number`.

DELIVERABLES REQUIRED IN RFC 068:
1. Ontological Audit & Theoretical Justification of the 1.80 / 2.60 / 3.40 / 4.20 scale.
2. Canonical Text Rewrites for `tomo_ch2_intro` across all 6 locales (`es`, `en`, `pt`, `fr`, `de`, `ja`) matching the exact SSOT.
3. Chapter 1 & Chapter 2 Narrative Harmony: Ensure all executive narrative mentions of scores (e.g. 2.55 = Repetible, 2.60 = Definido, 3.50 = Gestionado / Benchmark) are 100% consistent across every paragraph and table.
4. Test Oracle: Verification assertions to certify that no document emits contradictory maturity level names or ranges.
"""

    print(f"Requesting RFC 068 maturity model specification from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_068_MATURITY_MODEL_SCALE_UNIFICATION_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Successfully generated RFC 068 specification: {out_file}")


if __name__ == "__main__":
    main()
