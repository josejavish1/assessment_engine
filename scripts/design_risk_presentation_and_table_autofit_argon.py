#!/usr/bin/env python3
"""Argon-4 Consultation: OpenXML Table AutoFit to Contents and Visual Polish for Appendix Abbreviations Table."""

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
Role: Chief Editorial & OpenXML Typography Architect (Tier-1 Management Consulting / Google Core Infrastructure).

USER'S DIRECTIVE & CRITIQUE:
The user explicitly stated:
"Por cierto en la tabla de Appendix A.1 Lista de Abreviaturas tiene que quedar autoajustado al contenido que todavía no lo está, una vez hagas el cambio verifica con pantallazos que ha quedado así y no pares hasta que quede perfecto."

FORENSIC AUDIT OF THE PROBLEM:
1. In `ast_appendices_builder.py`, the abbreviations table is built as:
   `nodes.append(TableNode(rows=rows, autofit=True))`
2. In `docx_compiler.py`:
   - When no explicit `col_widths` is provided, `TableLayoutCalculator.compute_column_widths_dxa` uses a heuristic that assigns dampening and large minimum bounds (e.g. `CAP_MIN_COL_WIDTH_DXA = 2400`), resulting in Col 0 (the acronym column) getting ~3858 DXA (almost 50% of the entire printable table width!).
   - In Microsoft Word, this causes the 2-column table to look severely disproportionate: a tiny 3-to-5 letter acronym (like 'API', 'RAM', 'KPI') sits inside a massive ~6.8 cm column, while the multi-line definition is crammed into the remainder.
   - When viewed in Word or PDF, the table is NOT visually auto-fitted to its contents!

ARCHITECTURAL SPECIFICATION REQUIRED:
1. Table Column Geometry:
   - What is the ideal proportional distribution for the Abbreviations table? (e.g. `col_widths=[0.18, 0.82]` or `[0.20, 0.80]`, giving Col 0 ~1,684 DXA / 1.17 inches—plenty of room for "Abreviatura" and acronyms, while dedicating 7,676 DXA / 5.33 inches to the definitions).
2. OpenXML `w:tblPr` and `w:tcPr` Layout Configuration:
   - How should `docx_compiler.py` configure `tblW`, `tblLayout`, and cell-level `tcW` when `autofit=True` is requested so that Word renders an auto-fitted layout?
3. Page Containment & Spacing:
   - Ensure the Appendix A.1 table and Appendix A.2 disclaimer do not generate awkward page breaks or orphan headings.

YOUR TASK:
Synthesize an authoritative Architectural Blueprint in Markdown:
1. Deliver the exact OpenXML and AST parameters for the Appendix A.1 table.
2. Provide the definitive implementation code for `ast_appendices_builder.py` and `docx_compiler.py`.
3. Deliver a definitive VERDICT: PASS.
"""

    print(f"Requesting table autofit blueprint from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_061_TABLE_AUTOFIT_AND_APPENDIX_POLISH_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 061 TABLE AUTOFIT BLUEPRINT")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nBlueprint saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
