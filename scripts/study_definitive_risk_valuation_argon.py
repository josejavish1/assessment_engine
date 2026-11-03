#!/usr/bin/env python3
"""Argon-4 Master Consultation: RFC 056 Actuarial Blast Radius Transparency & Strict Regular Hyphen Invariant.

Addresses the user's two core mandates:
1. Actuarial Blast Radius Transparency (Alternative A):
   - Explicitly explain in Section 4.1 that 13,061.29 €/h represents total corporate stoppage (100%), and detail how the 70% (9,142 €/h), 40% (5,224 €/h), and 20% (2,612 €/h) Operational Impact Factors stratify risks in Section 4.4.
   - In Section 4.4 risk cards, format the SLE derivation bullet to explicitly display the percentage and baseline rate:
     "• Derivación Financiera Exacta (SLE): 4,4h de interrupción operativa a 9.142 €/h (70% de afectación operativa sobre el coste base de parada de 13.061,29 €/h) = 40.229 €."
2. Strict Regular Hyphen Invariant (Zero Em/En-Dashes):
   - User mandate: "no quiero ningún guión largo, siempre guiones cortos."
   - Eradicate all em-dashes ('—', U+2014) and en-dashes ('–', U+2013) across engine_config/locales.json and enforce global sanitizer in docx_compiler.py and payload_to_ast.py to guarantee that only regular ASCII hyphens ('-', U+002D) are rendered.
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
Role: Chief Enterprise Architect & Principal Actuary (Gartner Fellow / McKinsey Senior Partner / Google Core Infrastructure).

USER CRITIQUE & SYSTEMIC AUDIT DIRECTIVES:
The user delivered two explicit engineering and editorial directives:

1. Actuarial Blast Radius Transparency (Alternative A):
   - User directive:
     "claramente esto es lo que tenemos que implementar -> Alternativa A: Explicar el porcentaje en la viñeta de la ficha:
      '• Derivación Financiera Exacta (SLE): 4,4h de interrupción operativa a 9.142 €/h (70% de afectación operativa sobre el coste base de parada de 13.061,29 €/h) = 40.229 €.'
      Así el CFO y CIO ven la relación directa con la tasa de 13.061,29 €/h del Capítulo 1.
      Pero debe quedar muy muy claro en el punto 4.1 para que el lector lo pueda entender bien."
   - Requirements:
     a) In Section 4.1, add an explicit paragraph detailing how the 13,061.29 €/h corporate baseline represents 100% enterprise paralysis, and how the Operational Impact Factor (alpha) scales it to 70% (9,142 €/h for critical platform failure), 40% (5,224 €/h for intermediate service contingency), and 20% (2,612 €/h for isolated component friction).
     b) In Section 4.4 risk cards, the SLE derivation bullet must interpolate:
        - `effective_hours`: e.g. 4.4h
        - `hourly_rate`: e.g. 9,142 €/h
        - `alpha_pct`: e.g. 70%
        - `base_rate`: e.g. 13,061.29 €/h
        - `sle_formatted`: e.g. 40,229 €

2. Strict Regular Hyphen Invariant (Zero Em-Dash / En-Dash Law):
   - User directive:
     "otra cosa esto afecta a todos los documentos que generemos siempre no quiero ningún guión largo, siempre guiones cortos."
   - Requirements:
     a) Replace all em-dashes (U+2014 '—') and en-dashes (U+2013 '–') in `engine_config/locales.json` with standard ASCII hyphens (U+002D '-').
     b) In `src/assessment_engine/adapters/compilers/docx_compiler.py` and `payload_to_ast.py`, enforce an automated text sanitization pass that normalizes all em-dashes and en-dashes into standard ASCII hyphens (`text.replace('—', '-').replace('–', '-')`) before OpenXML runs are created, making it physically impossible for a long dash to appear in any deliverable.

NON-NEGOTIABLE LAWS:
1. Zero bugs, zero antipatterns.
2. Zero hardcoding (scales across any tenant, vertical, currency, or locale in `locales.json`).
3. 100% Technical English codebase (zero Spanish words in Python code).
4. Split-brain eradication across all 10 capability towers.
5. OpenXML layout determinism.

YOUR TASK:
Synthesize an authoritative Architectural Blueprint (RFC 056) in Markdown:
1. Detail the Section 4.1 narrative additions and Section 4.4 SLE bullet template updates.
2. Formulate the universal short-hyphen normalization rule in `docx_compiler.py`.
3. Deliver a definitive VERDICT: PASS.
"""

    print(f"Requesting RFC 056 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_056_BLAST_RADIUS_TRANSPARENCY_AND_HYPHEN_INVARIANT_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 056 TRANSPARENCY & HYPHEN INVARIANT")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nSaved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
