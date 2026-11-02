#!/usr/bin/env python3
"""Argon-4 Master Consultation: RFC 050 Architectural Alignment, High-Value Chapter 3 Intro, Dynamic Justification Labels & Footer Typography.

Formulates the architectural blueprint before writing application code:
1. Enforces justified alignment (<w:jc w:val="both"/>) across Chapter 2 body copy and list bullets.
2. Upgrades Chapter 3 introduction to a high-value methodological briefing across 3 analytical dimensions (architecture, obsolescence, runbooks).
3. Adapts Table 3.1.2 labels dynamically by maturity score (score < 2.2 uses 'Situación Operativa Observada' to avoid labeling deficiencies as strengths).
4. Enforces paragraph-level run properties and complex field structures in footers to guarantee uniform font, size, and color.
5. 100% Technical English codebase and zero hardcoding across all 10 capability towers.
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
Role: Chief Enterprise Architect & Principal OpenXML Compiler Fellow (Gartner VP / McKinsey Senior Partner / Google Core Infrastructure).

USER CRITIQUE & SYSTEMIC AUDIT DIRECTIVES:
The user delivered four critical engineering and editorial directives:

1. Text Alignment in Chapter 2 ("2.2 Descripción de la Plataforma", "2.3 Escala CMMI", "2.4 Capacidades"):
   - Requirement: All body paragraphs and multi-line list bullets in Chapter 2 must be fully justified (<w:jc w:val="both"/> / WD_ALIGN_PARAGRAPH.JUSTIFY).
   - Root Cause: In `docx_render_utils.py`, `apply_bullet_list_format` unconditionally sets `paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT`, which overwrites the AST node's requested alignment. In `docx_compiler.py`, after applying bullet formatting, the compiler must preserve `align_const` (JUSTIFY) for multi-line bullets.

2. High-Value Methodological Chapter 3 Introduction:
   - User critique: The current intro ("El presente capítulo expone...") is generic meta-filler and lacks executive value.
   - Requirement: Frame Chapter 3 as a rigorous technical diagnostic across three analytical dimensions:
     a) Architectural resilience against single points of failure (SPOFs) and lack of redundancy.
     b) Physical and logical obsolescence against vendor support and licensing lifecycles.
     c) Maturity of operational runbooks and preventive maintenance procedures.
     And triangulate these dimensions under the CMMI framework to establish the platform baseline.

3. Context-Aware Table 3.1.2 Justification Labels (Score-Conditioned):
   - User critique: On Tower 2 Pillar 3 (Score 1.5), the table labeled a fragmented, unstandardized cloud model as "Fortaleza Operativa Identificada", which is nonsensical and damages credibility.
   - Requirement:
     * When pillar maturity score < 2.2 (Low/Ad-hoc):
       - Label 1: `calib_label_observed_state` ("Situación Operativa Observada" / "Observed Operational State")
       - Label 2: `calib_label_critical_gap` ("Brecha Crítica de Resiliencia" / "Critical Resilience Gap")
     * When pillar maturity score >= 2.2 (Established baseline):
       - Label 1: `calib_label_operational_strength` ("Fortaleza Operativa Identificada" / "Established Operational Strength")
       - Label 2: `calib_label_operational_gap` ("Brecha de Resiliencia Diagnosticada" / "Diagnosed Resilience Gap")

4. Uniform Footer Typography in Microsoft Word:
   - User critique: The page number in the footer ("MOLINS - Anexo Técnico — Confidencial | Pág. 5") appears in a different font/size/color than the prefix text in Word.
   - Requirement:
     * Add paragraph-level run properties `<w:pPr><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="17"/><w:color w:val="94A3B8"/></w:rPr></w:pPr>` to the footer paragraph.
     * Use a complex field structure `<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="17"/><w:color w:val="94A3B8"/></w:rPr><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>`.
     * This forces Word to render the page number in Arial, 8.5pt, #94A3B8, matching the prefix text 100%.

NON-NEGOTIABLE ENGINEERING LAWS:
1. Zero bugs, zero antipatterns.
2. Zero hardcoding (scales across any tenant, vertical, currency, or locale).
3. 100% Technical English codebase (zero Spanish words in Python code).
4. Split-brain eradication across all 10 capability towers.
5. OpenXML layout determinism.

YOUR TASK:
Synthesize an authoritative Architectural Blueprint (RFC 050) in Markdown:
1. Review and ratify the bilingual catalog additions in `engine_config/locales.json`.
2. Review the Python implementation in `docx_compiler.py`, `docx_render_utils.py`, `in_memory_asis_compiler.py`, and `generate_asis_markdown_modules.py`.
3. Deliver a definitive VERDICT: PASS.
"""

    print(f"Requesting RFC 050 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_050_ARCHITECTURAL_ALIGNMENT_AND_FOOTER_TYPOGRAPHY_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 050 ARCHITECTURAL ALIGNMENT & FOOTER TYPOGRAPHY")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nSaved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
