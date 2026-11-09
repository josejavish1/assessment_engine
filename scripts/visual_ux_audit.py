#!/usr/bin/env python3
"""Audit visual layout, typography, and UX formatting of generated deliverables."""

from __future__ import annotations

from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

REPO_ROOT = Path(__file__).resolve().parents[1]
T1_DOCX = REPO_ROOT / "working/out/molins/T1/Molins_202610_Anexo_01_Data_Center_ASIS.docx"
TOMO1_DOCX = REPO_ROOT / "Molins_202610_Tomo_1_Diagnostico_ASIS.docx"


def audit_document_visuals(doc_path: Path) -> dict:
    doc = Document(str(doc_path))

    # 1. Page Margins
    sections_info = []
    for s in doc.sections:
        sections_info.append({
            "top_margin_in": round(s.top_margin.inches, 2),
            "bottom_margin_in": round(s.bottom_margin.inches, 2),
            "left_margin_in": round(s.left_margin.inches, 2),
            "right_margin_in": round(s.right_margin.inches, 2),
            "orientation": str(s.orientation),
        })

    # 2. Typography & Heading styles
    heading_samples = []
    for p in doc.paragraphs:
        if p.style and p.style.name.startswith("Heading"):
            font_name = None
            font_size = None
            color = None
            if p.runs:
                font_name = p.runs[0].font.name
                font_size = p.runs[0].font.size.pt if p.runs[0].font.size else None
                color = str(p.runs[0].font.color.rgb) if p.runs[0].font.color else None
            heading_samples.append({
                "style": p.style.name,
                "text": p.text[:50],
                "font": font_name or p.style.font.name,
                "size_pt": font_size or (p.style.font.size.pt if p.style.font.size else None),
                "keep_with_next": p.paragraph_format.keep_with_next,
            })

    # 3. Table Visuals & Styling
    tables_info = []
    for t_idx, t in enumerate(doc.tables[:10]):
        header_row = t.rows[0]
        col_count = len(header_row.cells)
        sample_headers = [c.text.strip().replace("\n", " ")[:30] for c in header_row.cells]
        has_cant_split = getattr(header_row, "_tr", None) is not None
        tables_info.append({
            "table_index": t_idx,
            "row_count": len(t.rows),
            "col_count": col_count,
            "sample_headers": sample_headers,
            "style_name": t.style.name if t.style else "None",
        })

    # 4. Spacing & Visual Rhythms
    empty_paragraphs = sum(1 for p in doc.paragraphs if not p.text.strip())
    total_paragraphs = len(doc.paragraphs)

    return {
        "doc_name": doc_path.name,
        "sections": sections_info,
        "headings_count": len(heading_samples),
        "heading_samples": heading_samples[:8],
        "tables_count": len(doc.tables),
        "table_samples": tables_info[:5],
        "total_paragraphs": total_paragraphs,
        "empty_spacer_paragraphs": empty_paragraphs,
    }


def main() -> None:
    print("=" * 80)
    print("VISUAL LAYOUT & UX FORMATTING AUDIT (HUMAN EYE PERSPECTIVE)")
    print("=" * 80)

    for p in [T1_DOCX, TOMO1_DOCX]:
        if not p.exists():
            continue
        info = audit_document_visuals(p)
        print(f"\n--- Document: {info['doc_name']} ---")
        print(f"Margins: {info['sections'][0]}")
        print(f"Total Paragraphs: {info['total_paragraphs']} (Spacer lines: {info['empty_spacer_paragraphs']})")
        print(f"Total Tables: {info['tables_count']}")
        print(f"Sample Headings ({info['headings_count']} total):")
        for h in info["heading_samples"][:5]:
            print(f"  [{h['style']}] '{h['text']}' | font={h['font']}, size={h['size_pt']}pt, keep_with_next={h['keep_with_next']}")
        print(f"Sample Tables:")
        for t in info["table_samples"][:4]:
            print(f"  Table #{t['table_index']}: {t['row_count']} rows x {t['col_count']} cols | style={t['style_name']} | headers={t['sample_headers'][:3]}")


if __name__ == "__main__":
    main()
