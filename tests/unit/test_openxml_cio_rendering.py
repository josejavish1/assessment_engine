from __future__ import annotations

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from assessment_engine.adapters.compilers.docx_compiler import (
    safe_autofit_table_to_contents,
    safe_set_cell_text,
    set_run_font_comprehensive,
)
from assessment_engine.infrastructure.docx_render_utils import set_paragraph_numbering


def test_set_run_font_comprehensive_cjk_support():
    """Verify that set_run_font_comprehensive injects all 4 font quadrants (ASCII, hAnsi, CS, eastAsia)."""
    doc = docx.Document()
    p = doc.add_paragraph()
    run = p.add_run("テスト テキスト (Japanese Test Text)")

    set_run_font_comprehensive(run, font_name="Arial", east_asia_fallback="Meiryo")

    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    assert rFonts is not None
    assert rFonts.get(qn("w:ascii")) == "Arial"
    assert rFonts.get(qn("w:hAnsi")) == "Arial"
    assert rFonts.get(qn("w:cs")) == "Arial"
    assert rFonts.get(qn("w:eastAsia")) == "Meiryo"


def test_safe_set_cell_text_single_and_multiline():
    """Verify that safe_set_cell_text renders both single-line and multi-line content correctly."""
    doc = docx.Document()
    table = doc.add_table(rows=2, cols=2)

    # Test single-line cell (e.g. heatmap header or metric)
    cell_single = table.rows[0].cells[0]
    safe_set_cell_text(cell_single, "TEF \\ LM")
    assert "TEF \\ LM" in cell_single.text

    # Test single-line with label: description pattern
    cell_label = table.rows[0].cells[1]
    safe_set_cell_text(cell_label, "Disponibilidad: 99.95%")
    assert "Disponibilidad:" in cell_label.text
    assert "99.95%" in cell_label.text

    # Test multi-line list cell
    cell_multi = table.rows[1].cells[0]
    safe_set_cell_text(cell_multi, "• Punto A\n• Punto B")
    assert "Punto A" in cell_multi.text
    assert "Punto B" in cell_multi.text


def test_safe_autofit_table_to_contents_margin_boundary():
    """Verify that table width is bounded to margin percentage (w:type='pct') preventing C-Level overflow."""
    doc = docx.Document()
    table = doc.add_table(rows=2, cols=2)
    safe_autofit_table_to_contents(table)

    tblPr = table._tbl.tblPr
    tblW = tblPr.find(qn("w:tblW"))
    assert tblW is not None
    assert tblW.get(qn("w:type")) == "pct"
    assert tblW.get(qn("w:w")) == "5000"


def test_set_paragraph_numbering_xsd_ordering():
    """Verify that w:numPr is inserted before w:spacing and w:ind complying with OpenXML CT_PPr schema."""
    doc = docx.Document()
    p = doc.add_paragraph()

    # Pre-add spacing element to simulate existing paragraph layout
    pPr = p._p.get_or_add_pPr()
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:after"), "120")
    pPr.append(spacing)

    # Apply numbering
    success = set_paragraph_numbering(p, num_id=1, ilvl=0)
    assert success is True

    # Check child order: w:numPr must appear before w:spacing in CT_PPr
    tags = [child.tag.split("}")[-1] for child in pPr]
    assert "numPr" in tags
    assert "spacing" in tags
    num_idx = tags.index("numPr")
    spacing_idx = tags.index("spacing")
    assert num_idx < spacing_idx, f"numPr (index {num_idx}) must precede spacing (index {spacing_idx})"
