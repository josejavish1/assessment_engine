#!/usr/bin/env python3
"""Argon-4 Master Consultation: RFC 045 Dynamic Findings Cardinality & Pure AS-IS Synthesis.

Eradicates the 'Rule of 3' hardcoding antipattern where Paragraph 2 assumed exactly 3 vulnerabilities.
Enforces dynamic cardinality (0, 1, 2, or N findings) with natural language enumeration and grammar,
coupled with the pure AS-IS diagnostic verdict in Paragraph 4.
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
Role: Chief Enterprise Systems Architect & Principal Enterprise Compiler Fellow (Google Tier-1 Core Infrastructure / Anthropic Core Staff).

CONTEXT & USER CRITIQUE (ELIMINATING THE 'RULE OF 3' ANTIPATTERN):
The user observed:
"solo una duda en el párrafo, ¿por qué 3 vulnerabilidades? Depende del cliente y la torre esto ¿no puede variar? No quiero ningún antipatrón."

ARCHITECTURAL ANALYSIS:
The user is 100% right. Hardcoding that every tower and every enterprise in the world has "tres problemas prioritarios" is a blatant antipattern.
1. A small firm or highly mature tower may have 0 or 1 critical vulnerability.
2. An intermediate tower may have 2 distinct findings.
3. A heavily burdened domain may have 4, 5, or more findings.
4. Forcing a static "three vulnerabilities" sentence:
   - Produces awkward grammar when len(findings) < 3 (filling with blanks or falling back awkwardly).
   - Artificially truncates real risks when len(findings) > 3.
   - Violates Law 2 (Zero Hardcoding / Universal Global Enterprise Readiness).

METHODOLOGICAL REQUIREMENTS FOR RFC 045:
1. Dynamic Findings Cardinality & Natural Language Enumeration:
   - The engine must inspect `len(findings_briefs)` dynamically:
     * `0 findings`: Positive diagnostic confirming operational hygiene and absence of active critical failure points.
     * `1 finding`: Singular grammatical construct focusing directly on the single identified constraint.
     * `2 findings`: Dual grammatical construct linking the two interrelated vectors.
     * `N >= 3 findings`: Pluralized construct stating the verified count and enumerating the top prioritized items naturally.
   - Zero hardcoded numbers ("tres", "three") in locale templates.
2. Pure AS-IS Diagnostic Verdict for Paragraph 4 (from RFC 044):
   - Zero TO-BE roadmap promises ("12 to 24 months").
   - Zero TO-BE target scores ("4.1 out of 5.0").
   - Instead: True diagnostic closure — Apparent vs. Structural Stability, Primary Systemic Bottleneck, and the Concrete Cost of Status-Quo Inertia.
3. 100% Technical English Codebase:
   - All Python code, helper functions, variables, identifiers, docstrings, comments, logs, and exceptions must be 100% Technical English.
   - All localized strings isolated in `engine_config/locales.json`.
4. OpenXML Layout Determinism:
   - Guarantees clean pagination and single-page executive containment.

YOUR TASK:
Synthesize an authoritative Architectural Blueprint (RFC 045) in Markdown:
1. Dynamic Findings Enumeration Architecture: Show the exact algorithm and linguistic grammar rules for 0, 1, 2, and N findings in both Spanish and English.
2. Pure AS-IS Paragraph 4 Template Structure: Formulate the definitive diagnostic verdict without TO-BE/TO-DO contamination.
3. Complete bilingual additions for `engine_config/locales.json`.
4. Production-ready Python code modifications for `payload_to_ast.py` in 100% Technical English.
"""

    print(f"Requesting RFC 045 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_045_DYNAMIC_CARDINALITY_AND_PURE_ASIS_SYNTHESIS_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 045 DYNAMIC CARDINALITY & PURE AS-IS SYNTHESIS")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nBlueprint saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
