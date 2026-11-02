#!/usr/bin/env python3
"""Argon-4 Master Comprehensive Audit: End-to-End Architectural Verification of RFC 041-043 and 10-Tower Differentiated Prose.

Audits:
1. Complete elimination of robotic copy-paste introductory paragraphs across all 10 towers.
2. Dynamic injection of domain-specific operational missions and impact clauses from configuration catalogs.
3. Universal epistemic modesty ("all numbers as estimates") across Chapters 1, 2, and 4.
4. Formal mathematical lineage table in Chapter 4 reconciling to R_hourly to the exact cent.
5. Capping of P90 physical outage hours via asymptotic saturation curve (OperationalTailRiskEngine).
6. 100% Technical English codebase, zero hardcoded tenant names or magic numbers, zero bugs.
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
Role: Chief Quality Gate Judge & Principal Enterprise Systems Auditor (Google Tier-1 Infrastructure / Anthropic Core Staff).

USER DIRECTIVE & STRATEGIC MANDATE:
The user explicitly asked:
"Estas seguro de que ya has implementado todos los cambios y has revisado que todo esté bien, por favor, que gemini-4-argon haga una revisión completa y si encuentra algo que lo cambie y garantice que lo tiene todo perfecto, quiero que hayamos implementado todo lo que dijimos que ibamos a implementar y por otro lado, una vez acabe que haga esto: 'quiero que le digas a gemini-4-argon que haga una revisión completa de lo que acabas de programar y busque bugs, problemas o antipatrones, no quiero nada hardcodeado recuerda que el objetivo es que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial, de cualquier vertical, en cualquier idioma, y el código debe estar 100% en ingles nada de español ni una sola palabra, el español solo es el idioma que hablamos tu y yo y uno de los idiomas de la salida de los entregables.'"

AUDIT SCOPE:
1. Check `engine_config/locales.json`:
   - Are the 10 capability towers (T1..T10) provided with distinct operational missions, domain roles, and vulnerability impact clauses so Paragraph 1 in Chapter 1 NEVER sounds like a cookie-cutter robot?
   - Does `p2_architectural_dilemma` have tower-aware opening variations?
   - Are all numbers throughout Chapter 1 and Chapter 4 qualified with epistemic modesty (e.g. estimated / projected)?
   - Is European currency postfix formatting (11.428,60 €/h) fully enforced in Spanish and prefix ($11,428.60/hr) in English?

2. Check `src/assessment_engine/adapters/compilers/payload_to_ast.py`:
   - Does `synthesize_chapter_one_paragraphs` dynamically weave the tower operational mission from `locales.json`?
   - Does Chapter 4 feature Section 4.1 with the formal Actuarial Lineage Table (Table 4.1), Section 4.2 Heatmap, Section 4.3 Three Investment Portfolios table, and Section 4.4 Bow-Tie Risk Cards?
   - Are all residual magic numbers (e.g. `10000.0` or `11428.60`) completely eradicated?
   - Is all Python code, variables, method names, comments, docstrings, and log messages 100% in Technical English?

3. Check `src/assessment_engine/domain/actuarial/downtime_calibrator.py`:
   - Does `OperationalTailRiskEngine.decompose_tail_risk` provide safe boundary handling for zero or negative inputs, while capping P90 physical outage hours at the operational ceiling (e.g. 21-24h)?

NON-NEGOTIABLE LAWS TO ENFORCE:
- Law 1: Zero bugs, zero antipatterns, zero unhandled exceptions.
- Law 2: Zero hardcoding (scales to any enterprise from 50M€ to 50B€, any vertical, any currency, any locale).
- Law 3: 100% Technical English codebase (zero Spanish in Python code).
- Law 4: Split-brain eradication across all 10 towers.
- Law 5: OpenXML ISO/IEC 29500 layout determinism (Page 3 single-page containment, TOC synchronization).

YOUR AUDIT REPORT MUST:
1. Provide a rigorous forensic evaluation of the codebase against all 5 laws and the user's explicit mandates.
2. If ANY gap, bug, or hardcoding exists (especially regarding 10-tower differentiated prose in Paragraph 1 & 2), provide the exact mandatory code and configuration changes in 100% Technical English.
3. Deliver a definitive VERDICT: PASS or FAIL.
"""

    print(f"Requesting comprehensive adversarial audit from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: COMPREHENSIVE SESSION AUDIT REPORT")
    print("=" * 80)
    print(response.text)
    print("=" * 80)

    out_file = REPO_ROOT / "docs/architecture/COMPREHENSIVE_RECENT_AUDIT_ARGON.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Audit report saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
