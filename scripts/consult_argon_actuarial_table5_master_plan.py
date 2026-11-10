#!/usr/bin/env python3
"""Consult gemini-4-argon to architect the phased Master Plan for the Canonical Open FAIR Table 5 Engine."""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Principal Enterprise Architect, Supreme Actuarial Arbiter, and Chief Forensic Auditor.

USER MANDATE & VISION:
The user has reviewed and enthusiastically validated our canonical Open FAIR Table 5 architecture:
"Lo único es que antes de ponernos a programar hay que pensar bien cómo lo vamos a abordar y en cuántas fases para garantizar que queda sin errores y que vamos a ser #1 mundial, de cualquier vertical, en cualquier idioma.
El código debe estar 100% en inglés, nada de español ni una sola palabra. Aumentar la calidad de los entregables al 100% y que gemini-4-argon lo piense para que sea sin bugs, problemas o antipatrones, CERO HARDCODING. Que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial. Pídeselo a gemini-4-argon en inglés."

THE APPROVED CANONICAL TABLE 5 ARCHITECTURE:
| Technology Domain | CMMI Maturity | Standalone Bottom-Up ALE | Overlap & Absorption Adjustment | Net Portfolio Contribution (Euler ALE) | % of Total Risk |
| :--- | :---: | ---: | ---: | ---: | ---: |
| T1 - Physical Facilities | 2.61 | €62,093 | -€8,540 | €53,553 | 7.9% |
| T2 - Compute & Platforms | 1.89 | €104,190 | -€14,331 | €89,859 | 13.2% |
| T3 - Networks | 2.56 | €64,640 | -€8,891 | €55,749 | 8.2% |
| T4 - Storage & Data | 3.26 | €104,537 | -€14,378 | €90,159 | 13.3% |
| T5 - Operational Resilience | 2.20 | €84,650 | -€11,643 | €73,007 | 10.7% |
| T6 - Security (NIS2/GDPR) | 2.82 | €250,167 | -€34,408 | €215,759 | 31.8% |
| T7 - ITSM & Support Toil | 2.43 | €25,498 | -€3,507 | €21,991 | 3.2% |
| T8 - FinOps & Licensing | 2.45 | €175,129 | -€24,088 | €151,041 | 22.2% |
| T9 - Digital Workplace | 3.19 | €17,929 | -€2,466 | €15,463 | 2.3% |
| T10 - Core Systems / Plant | 2.40 | €73,182 | -€10,065 | €63,117 | 9.3% |
| **SUBTOTAL GROSS UNDIVERSIFIED** | **2.58** | **€962,015** | **—** | **—** | **—** |
| **ACTUARIAL ADJUSTMENT (COPULA)**| **—** | **-€142,617** | **[-14.8% Copula Overlap]** | **—** | **—** |
| **TOTAL NET CONSOLIDATED RISK** | **2.58** | **€819,398** | **-€142,617** | **€819,398** | **100.0%** |

YOUR MISSION:
Deliver a master engineering implementation plan structured in sequential, verifiable phases:
1. PHASE 1: Mathematical Engine & Copula Co-Expectation (Euler Allocation in `src/assessment_engine/domain/actuarial/`).
   - How to compute Standalone ALE bottom-up per tower.
   - How to compute the joint copula convolution and derive the exact Euler marginal contribution and diversification delta.
2. PHASE 2: Data Contracts & Locale Agnosticism (`engine_config/locales.json` & schemas).
   - How Table 5 column headers, subtotal labels, and diversification bridge text will be localized across all supported languages (en, es, pt, fr, de, ja) with ZERO hardcoding.
3. PHASE 3: AST Compiler Integration (`tomo_asis_ast_compiler.py`).
   - How `_build_chapter_3_actuarial_modeling` will render this exact table structure cleanly into OpenXML DOCX.
   - Handling scoped assessments (e.g., 6 active towers for Starling Bank vs 10 active towers for Molins/Geodis).
4. PHASE 4: Automated Verification & CI/CD Quality Gates.
   - Strict `pytest` test suites: mathematical identity tests (Rows sum to Gross Subtotal, Subtotal - Adjustment = Total, Euler column sums to Total, percentages sum to 100.0%).
   - Monotonicity and boundary assertions.

Constraints:
- 100% Technical English.
- No code implementation yet; provide the detailed, step-by-step Master Plan and architectural specifications.
- Must be globally universal for ANY company, ANY vertical, and ANY currency/language.

Deliver your architectural plan now.
"""

def main() -> None:
    print(f"Submitting Table 5 Master Plan request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    plan_report = response.text
    out_file = REPO_ROOT / "docs" / "architecture" / "ARGON_TABLE5_OPEN_FAIR_MASTER_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(plan_report, encoding="utf-8")

    print(f"\nMaster Plan written to: {out_file}\n")
    print("=" * 80)
    print(plan_report[:3500])
    if len(plan_report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
