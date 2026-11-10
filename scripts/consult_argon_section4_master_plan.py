#!/usr/bin/env python3
"""Consult gemini-4-argon to architect a phased, zero-defect Master Plan for Section 4 Polymorphic Decoupling."""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Principal Enterprise Architect, Supreme Actuarial Arbiter, and Master of Design Patterns.

USER DIRECTIVE & ARCHITECTURAL CHALLENGE:
"Lo único es antes de ponernos a programar hay que pensar bien cómo lo vamos a abordar y en cuántas fases para garantizar que queda sin errores y que vamos a ser #1 mundial, de cualquier vertical, en cualquier idioma, y el código debe estar 100% en ingles nada de español ni una sola palabra... aumentar la calidad de los entregables al 100% y quiero lo piense gemini-4-argon que lo haga sin bugs, problemas o antipatrones, no quiero nada hardcodeado recuerda que el objetivo es que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial. Pídeselo a gemini-4-argon en inglés."

THE PROBLEM TO SOLVE:
Currently, the AST compiler `src/assessment_engine/adapters/compilers/payload_to_ast.py` renders Section 4 (Actuarial Quantification) of the Specialist Annexes using a single, monolithic "Hourly Downtime" narrative template for all 10 technology domains. This is a severe anti-pattern because Cybersecurity (T6), FinOps (T8), and Workplace (T9) do not fail via "server downtime"; they fail via Regulatory Fines, Capital Waste, and Human Toil, respectively.

YOUR MANDATE:
Design a definitive, zero-defect Master Plan to refactor Section 4 into a canonical GoF Strategy Pattern mapping to the 4 Open FAIR Economic Receptors:
1. AVAILABILITY_OUTAGE (T1..T5, T10)
2. CAPITAL_INEFFICIENCY (T8)
3. PRODUCTIVITY_TOIL (T7, T9)
4. REGULATORY_AND_BREACH (T6)

SPECIFIC DESIGN DIMENSIONS:
1. **Zero Hardcoding & I18N Independence**: How will the text components (Section titles, formulae strings, dynamic bullet points) be abstracted away from Python code into `engine_config/locales.json` across 6 languages?
2. **Polymorphic AST Construction**: How will `payload_to_ast.py` delegate the node construction (`_build_chapter_4_actuarial_modeling` and `_build_chapter_4_2_prioritization`) to specific strategy classes or functions?
3. **Mathematical Identity Conservation**: How do we ensure that regardless of the strategy, the 3 underlying loss components (e.g., Forensics + Ransom + Fine) sum EXACTLY to the calibrated ALE (`total_fair_ale`)?
4. **Phased Execution Roadmap**: Break down the implementation into strict, verifiable phases (Phase 1: Schemas/Locales, Phase 2: Core Refactor, Phase 3: Tests).

Constraints:
- 100% Technical English for the response and proposed code constructs.
- No code implementation yet; provide the detailed, step-by-step Master Plan and architectural specifications.
- Must be globally universal for ANY company, ANY vertical, and ANY currency/language.

Deliver your architectural plan now.
"""

def main() -> None:
    print(f"Submitting Section 4 Master Plan request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    plan_report = response.text
    out_file = REPO_ROOT / "docs" / "architecture" / "ARGON_SECTION4_DECOUPLING_MASTER_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(plan_report, encoding="utf-8")

    print(f"\nMaster Plan written to: {out_file}\n")
    print("=" * 80)
    print(plan_report[:3500])
    if len(plan_report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
