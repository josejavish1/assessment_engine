#!/usr/bin/env python3
"""Argon-4 Master Consultation: Elevating Consolidated Tomo 1 AS-IS to an Unquestionable 10/10 Masterpiece.

The user mandates:
"lo que quiero es que con gemini-4argon y luego revisnadolo como lo ve un humano hagas una revisiln del as is consolidado y me des tu diagnostico si lo lee el CIO y que pintuacion nos da y si en el documento contamos todo el valor de las torre sin antipatrones , sin bug, sin splt brain y al fibal del todo quiero tener un entregable que un CIO y un CTO valoren de 10 por su contenido, claridad, valor que aporta, es decir a mi me encantan como tenemos las torres, este documento debe resaltar ltodo el valor de las torres  inclsuo si hace falta con infografias o lo quesea necesario pero queoro que el no paremos jas ral el cio o ctto exigentes nos diga que es de 10 el entrege"
"""

from __future__ import annotations

import sys
from pathlib import Path
from docx import Document

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)


def extract_full_docx_text(file_path: Path) -> str:
    doc = Document(file_path)
    lines = []
    lines.append(f"=== DOCUMENT: {file_path.name} ===")
    for p in doc.paragraphs:
        txt = p.text.strip()
        if txt:
            lines.append(f"[{p.style.name}]: {txt}")
    for idx, tbl in enumerate(doc.tables):
        lines.append(f"\n--- TABLE {idx} ({len(tbl.rows)} rows, {len(tbl.columns)} cols) ---")
        for r_idx, row in enumerate(tbl.rows):
            row_txt = " | ".join(c.text.replace("\n", " ").strip() for c in row.cells)
            lines.append(f"Row {r_idx}: {row_txt[:160]}")
    return "\n".join(lines)


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    f_docx = REPO_ROOT / "working/out/Molins_Entrega_Oficial_Piramide_Tier1/01_TRIADA_ESTRATEGICA_TRANSVERSAL_CTO/Molins_202610_Tomo_1_Diagnostico_ASIS.docx"
    doc_text = extract_full_docx_text(f_docx)

    prompt = f"""
Role: You are an exceptionally demanding, world-class Chief Information Officer (CIO) and Chief Technology Officer (CTO) of a Global Tier-1 Industrial Enterprise (IBEX-35 / Fortune 500) and Gartner Research Fellow.

USER MANDATE:
"lo que quiero es que con gemini-4argon y luego revisnadolo como lo ve un humano hagas una revisiln del as is consolidado y me des tu diagnostico si lo lee el CIO y que pintuacion nos da y si en el documento contamos todo el valor de las torre sin antipatrones , sin bug, sin splt brain y al fibal del todo quiero tener un entregable que un CIO y un CTO valoren de 10 por su contenido, claridad, valor que aporta, es decir a mi me encantan como tenemos las torres, este documento debe resaltar ltodo el valor de las torres  inclsuo si hace falta con infografias o lo quesea necesario pero queoro que el no paremos jas ral el cio o ctto exigentes nos diga que es de 10 el entrege"

CURRENT STATE OF TOMO 1 AS-IS (COMPILED VIA DECLARATIVE AST ENGINE, 10 PAGES, 3,078 WORDS):
{doc_text}

YOUR MISSION:
1. Precise Current Score (0 to 10 and 0 to 100):
   - What exact score do you give this updated 10-page version?
   - What is your honest impression as a demanding CIO/CTO?

2. Forensic Gap Analysis to reach 10/10:
   - What specific elements are still missing compared to the individual tower annexes (which have rich visual infographics, radar charts, 5x5 risk heatmaps, 3-column KPI risk cards, exact SLE arithmetic, and pillar-level capability scores)?
   - How can we embed:
     a) The Global Radar Chart (`global_radar_chart.png`) in Chapter 2?
     b) An Aggregated 5x5 FAIR Heatmap in Chapter 3?
     c) 3-Column Mini-Infographic Risk Cards for the Top Transversal Systemic Risks in Chapter 4?
     d) 2-column forensic deep-dives for each of the 10 capability domains?

3. The "Human-Centric Review" (How an executive human perceives the document):
   - Executive flow, readability, cognitive ergonomics, emotional impact on the Board.

4. Definitive Blueprint for 10/10 Excellence:
   - Provide the complete, surgical plan for `tomo_asis_ast_compiler.py` and `locales.json` so that the final deliverable is unanimously rated 10/10 by any Fortune 500 CIO/CTO worldwide.
"""

    print(f"Requesting 10/10 perfection blueprint from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_064_TOMO_1_PERFECTION_10_OUT_OF_10_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: 10/10 BLUEPRINT ON CONSOLIDATED TOMO 1 AS-IS")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nBlueprint saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
