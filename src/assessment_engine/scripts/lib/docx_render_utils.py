"""Shared helpers for DOCX-based renderers."""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path

from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.table import Table
from docx.text.paragraph import Paragraph

from assessment_engine.scripts.lib.text_utils import clean_text_for_word

WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def find_style(doc, *candidates):
    styles = getattr(doc, "styles", None)
    if styles is None:
        return None

    normalized_candidates = [
        str(candidate).strip().lower() for candidate in candidates if candidate
    ]
    for wanted in normalized_candidates:
        for style in styles:
            style_id = str(getattr(style, "style_id", "") or "").strip().lower()
            style_name = str(getattr(style, "name", "") or "").strip().lower()
            if style_id == wanted or style_name == wanted:
                return style
    return None


def apply_paragraph_style(paragraph, *candidates):
    style = find_style(paragraph.part.document, *candidates)
    if style is None:
        return False
    paragraph.style = style
    return True


def apply_table_style(table, *candidates):
    style = find_style(table.part.document, *candidates)
    if style is None:
        return False
    table.style = style.name
    return True


def get_style_numbering(doc, *candidates):
    style = find_style(doc, *candidates)
    if style is None:
        return None, None

    current = style.element
    visited = set()
    while current is not None:
        style_id = current.get(qn("w:styleId"))
        if style_id in visited:
            break
        visited.add(style_id)

        num_id = current.find("./w:pPr/w:numPr/w:numId", WORD_NS)
        ilvl = current.find("./w:pPr/w:numPr/w:ilvl", WORD_NS)
        if num_id is not None:
            return (
                num_id.get(qn("w:val")),
                ilvl.get(qn("w:val")) if ilvl is not None else "0",
            )

        based_on = current.find("./w:basedOn", WORD_NS)
        if based_on is None:
            break
        parent_style_id = based_on.get(qn("w:val"))
        current = find_style(doc, parent_style_id)
        current = current.element if current is not None else None

    return None, None


def set_paragraph_numbering(paragraph, num_id, ilvl=0):
    if num_id is None:
        return False

    pPr = paragraph._p.get_or_add_pPr()
    for child in list(pPr):
        if child.tag.split("}")[-1] == "numPr":
            pPr.remove(child)

    numPr = OxmlElement("w:numPr")
    ilvl_el = OxmlElement("w:ilvl")
    ilvl_el.set(qn("w:val"), str(ilvl))
    numPr.append(ilvl_el)
    num_id_el = OxmlElement("w:numId")
    num_id_el.set(qn("w:val"), str(num_id))
    numPr.append(num_id_el)
    pPr.append(numPr)
    return True


def apply_bullet_list_format(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    for child in list(pPr):
        if child.tag.split("}")[-1] in {"numPr", "ind"}:
            pPr.remove(child)

    apply_paragraph_style(paragraph, "Bullet", "NTTFlushBullet1", "List Paragraph", "Prrafodelista")
    num_id, ilvl = get_style_numbering(
        paragraph.part.document,
        "Bullet",
        "NTTFlushBullet1",
        "List Paragraph",
        "Prrafodelista",
    )
    set_paragraph_numbering(paragraph, num_id, ilvl or 0)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.line_spacing = 1.05
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT


def enable_update_fields_on_open(doc):
    settings = doc.settings.element
    existing = settings.find(qn("w:updateFields"))
    if existing is None:
        existing = OxmlElement("w:updateFields")
        settings.append(existing)
    existing.set(qn("w:val"), "true")


def clean_text(value):
    return clean_text_for_word(value)


def clean_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [clean_text(item) for item in value if clean_text(item)]
    text = clean_text(value)
    return [text] if text else []


def clean_paragraph_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [clean_text(item) for item in value if clean_text(item)]
    text = clean_text(value)
    if not text:
        return []
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    return paragraphs or [text]


def resolve_radar_chart_image(image_path):
    image_path = clean_text(image_path)
    if not image_path:
        return None
    if image_path.startswith("data:image/") and ";base64," in image_path:
        try:
            _, encoded = image_path.split(";base64,", 1)
            raw = base64.b64decode(encoded)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            tmp.write(raw)
            tmp.close()
            return Path(tmp.name)
        except Exception:
            return None
    path = Path(image_path)
    if path.exists() and path.is_file():
        return path
    return None


def iter_paragraphs(doc):
    for paragraph in doc.paragraphs:
        yield paragraph
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    yield paragraph


def find_first_paragraph(doc, placeholder):
    for paragraph in iter_paragraphs(doc):
        if placeholder in paragraph.text:
            return paragraph
    return None


def clear_paragraph(paragraph):
    element = paragraph._element
    for child in list(element):
        if child.tag != qn("w:pPr"):
            element.remove(child)


def clear_paragraph_properties(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    for child in list(pPr):
        pPr.remove(child)


def remove_paragraph(paragraph):
    element = paragraph._element
    parent = element.getparent()
    if parent is not None:
        parent.remove(element)


def insert_paragraph_after_block(block):
    if isinstance(block, Paragraph):
        anchor = block._p
        parent = block._parent
    elif isinstance(block, Table):
        anchor = block._tbl
        parent = block._parent
    else:
        raise TypeError("Unsupported block type")

    new_p = OxmlElement("w:p")
    anchor.addnext(new_p)
    return Paragraph(new_p, parent)


def insert_field_paragraph_after_block(block, field_code, placeholder_text=""):
    paragraph = insert_paragraph_after_block(block)
    run = paragraph.add_run()

    fld_char_begin = OxmlElement("w:fldChar")
    fld_char_begin.set(qn("w:fldCharType"), "begin")
    fld_char_begin.set(qn("w:dirty"), "true")
    run._r.append(fld_char_begin)

    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = field_code
    run._r.append(instr_text)

    fld_char_sep = OxmlElement("w:fldChar")
    fld_char_sep.set(qn("w:fldCharType"), "separate")
    run._r.append(fld_char_sep)

    if placeholder_text:
        text = OxmlElement("w:t")
        text.text = placeholder_text
        run._r.append(text)

    fld_char_end = OxmlElement("w:fldChar")
    fld_char_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char_end)
    return paragraph


def add_run(paragraph, text, bold=False, font_size=10.5):
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.size = Pt(font_size)
    return run


def apply_body_format(paragraph, justify=True, space_after=6, font_size=10.5):
    paragraph.alignment = (
        WD_ALIGN_PARAGRAPH.JUSTIFY if justify else WD_ALIGN_PARAGRAPH.LEFT
    )
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.line_spacing = 1.05
    for run in paragraph.runs:
        run.font.size = Pt(font_size)


def replace_simple_placeholder(
    doc, placeholder, value, align=None, font_size=None, bold=None
):
    for paragraph in iter_paragraphs(doc):
        if placeholder in paragraph.text:
            text = paragraph.text.replace(placeholder, clean_text(value))
            clear_paragraph(paragraph)
            run = paragraph.add_run(text)
            if font_size:
                run.font.size = Pt(font_size)
            if bold is not None:
                run.bold = bold
            if align:
                paragraph.alignment = align
            paragraph.paragraph_format.space_before = Pt(0)
            if placeholder != "{{SCORING_METHOD_NOTE}}":
                paragraph.paragraph_format.space_after = Pt(6)
            paragraph.paragraph_format.line_spacing = 1.05


def render_multi_paragraph_block(doc, placeholder, texts):
    paragraph = find_first_paragraph(doc, placeholder)
    if not paragraph:
        return
    texts = clean_paragraph_list(texts)
    if not texts:
        remove_paragraph(paragraph)
        return

    clear_paragraph(paragraph)
    add_run(paragraph, texts[0], font_size=10.5)
    apply_body_format(paragraph, justify=True, space_after=6)
    anchor = paragraph

    for text in texts[1:]:
        new_paragraph = insert_paragraph_after_block(anchor)
        add_run(new_paragraph, text, font_size=10.5)
        apply_body_format(new_paragraph, justify=True, space_after=6)
        anchor = new_paragraph


def strip_numbering_and_indents(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    for child in list(pPr):
        tag = child.tag.split("}")[-1]
        if tag in {"numPr", "ind"}:
            pPr.remove(child)
    paragraph.paragraph_format.left_indent = Pt(0)
    paragraph.paragraph_format.first_line_indent = Pt(0)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.line_spacing = 1.05
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT


def render_list_at_placeholder(doc, placeholder, items):
    paragraph = find_first_paragraph(doc, placeholder)
    if not paragraph:
        return
    items = [clean_text(x) for x in items if clean_text(x)]
    if not items:
        remove_paragraph(paragraph)
        return

    clear_paragraph(paragraph)
    strip_numbering_and_indents(paragraph)
    if hasattr(paragraph._parent, "vertical_alignment"):
        paragraph._parent.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    anchor = paragraph

    for idx, item in enumerate(items):
        current = anchor if idx == 0 else insert_paragraph_after_block(anchor)
        clear_paragraph(current)
        strip_numbering_and_indents(current)
        if hasattr(current._parent, "vertical_alignment"):
            current._parent.vertical_alignment = WD_ALIGN_VERTICAL.TOP
        apply_bullet_list_format(current)
        content = current.add_run(item)
        content.font.size = Pt(10)
        anchor = current


def move_table_after_paragraph(paragraph, table):
    table_element = table._tbl
    paragraph._p.addnext(table_element)


def shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def clear_cell_shading(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    for child in list(tcPr):
        if child.tag.split("}")[-1] == "shd":
            tcPr.remove(child)


def set_cell_text(
    cell,
    text,
    bold=False,
    align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    font_size=10.5,
    vertical=WD_ALIGN_VERTICAL.CENTER,
    space_after=2,
):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = align
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.line_spacing = 1.0
    run = paragraph.add_run(clean_text(text))
    run.bold = bold
    run.font.size = Pt(font_size)
    cell.vertical_alignment = vertical


def set_repeat_table_header(row):
    trPr = row._tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader")
    tblHeader.set(qn("w:val"), "true")
    trPr.append(tblHeader)


def prevent_row_break(row):
    trPr = row._tr.get_or_add_trPr()
    cantSplit = OxmlElement("w:cantSplit")
    trPr.append(cantSplit)


def finalize_table(table):
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = True


def autofit_table_to_contents(table):
    table.autofit = True
    tbl = table._tbl

    for child in list(tbl):
        if child.tag.split("}")[-1] == "tblGrid":
            tbl.remove(child)

    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)

    for child in list(tblPr):
        tag = child.tag.split("}")[-1]
        if tag in {"tblW", "tblLayout"}:
            tblPr.remove(child)

    tblW = OxmlElement("w:tblW")
    tblW.set(qn("w:type"), "auto")
    tblW.set(qn("w:w"), "0")
    tblPr.append(tblW)

    tblLayout = OxmlElement("w:tblLayout")
    tblLayout.set(qn("w:type"), "autofit")
    tblPr.append(tblLayout)

    for row in table.rows:
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            for child in list(tcPr):
                if child.tag.split("}")[-1] == "tcW":
                    tcPr.remove(child)
            tcW = OxmlElement("w:tcW")
            tcW.set(qn("w:type"), "auto")
            tcW.set(qn("w:w"), "0")
            tcPr.append(tcW)


def render_note_box(doc, placeholder, text):
    paragraph = find_first_paragraph(doc, placeholder)
    if not paragraph:
        return
    text = clean_text(text)
    if not text:
        remove_paragraph(paragraph)
        return

    table = doc.add_table(rows=1, cols=1)
    finalize_table(table)
    move_table_after_paragraph(paragraph, table)
    cell = table.cell(0, 0)
    set_cell_text(
        cell,
        text,
        align=WD_ALIGN_PARAGRAPH.LEFT,
        font_size=9.5,
        vertical=WD_ALIGN_VERTICAL.CENTER,
        space_after=0,
    )
    shade_cell(cell, "F2F6FA")
    autofit_table_to_contents(table)
    remove_paragraph(paragraph)


def render_pillar_score_table(doc, placeholder, rows):
    paragraph = find_first_paragraph(doc, placeholder)
    if not paragraph:
        return

    table = doc.add_table(rows=1, cols=4)
    finalize_table(table)
    move_table_after_paragraph(paragraph, table)

    headers = ["Pilar", "Score", "Nivel", "Lectura ejecutiva"]
    for idx, header in enumerate(headers):
        set_cell_text(
            table.rows[0].cells[idx],
            header,
            bold=True,
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
            space_after=0,
        )
        shade_cell(table.rows[0].cells[idx], "D9EAF7")
    set_repeat_table_header(table.rows[0])

    for item in rows:
        row = table.add_row()
        prevent_row_break(row)
        set_cell_text(row.cells[0], item.get("pillar_label", ""), align=WD_ALIGN_PARAGRAPH.LEFT, font_size=10.2, vertical=WD_ALIGN_VERTICAL.CENTER)
        set_cell_text(row.cells[1], item.get("score_display", ""), align=WD_ALIGN_PARAGRAPH.LEFT, font_size=10.2, vertical=WD_ALIGN_VERTICAL.CENTER)
        set_cell_text(row.cells[2], item.get("maturity_band", ""), align=WD_ALIGN_PARAGRAPH.LEFT, font_size=10.2, vertical=WD_ALIGN_VERTICAL.CENTER)
        set_cell_text(row.cells[3], item.get("executive_reading", ""), align=WD_ALIGN_PARAGRAPH.LEFT, font_size=10.2, vertical=WD_ALIGN_VERTICAL.CENTER)

    autofit_table_to_contents(table)
    remove_paragraph(paragraph)


def render_risks_table(doc, placeholder, rows):
    paragraph = find_first_paragraph(doc, placeholder)
    if not paragraph:
        return

    table = doc.add_table(rows=1, cols=4)
    finalize_table(table)
    move_table_after_paragraph(paragraph, table)

    headers = ["Riesgo", "Impacto", "Probabilidad", "Mitigación resumida"]
    for idx, header in enumerate(headers):
        set_cell_text(
            table.rows[0].cells[idx],
            header,
            bold=True,
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
            space_after=0,
        )
        shade_cell(table.rows[0].cells[idx], "D9EAF7")
    set_repeat_table_header(table.rows[0])

    for item in rows:
        row = table.add_row()
        prevent_row_break(row)
        set_cell_text(row.cells[0], item.get("risk", ""), align=WD_ALIGN_PARAGRAPH.LEFT, font_size=10, vertical=WD_ALIGN_VERTICAL.CENTER)
        set_cell_text(row.cells[1], item.get("impact", ""), align=WD_ALIGN_PARAGRAPH.LEFT, font_size=10, vertical=WD_ALIGN_VERTICAL.CENTER)
        set_cell_text(row.cells[2], item.get("probability", ""), align=WD_ALIGN_PARAGRAPH.LEFT, font_size=10, vertical=WD_ALIGN_VERTICAL.CENTER)
        set_cell_text(row.cells[3], item.get("mitigation_summary", ""), align=WD_ALIGN_PARAGRAPH.LEFT, font_size=10, vertical=WD_ALIGN_VERTICAL.CENTER)

    autofit_table_to_contents(table)
    remove_paragraph(paragraph)


def render_gap_table(doc, placeholder, rows):
    paragraph = find_first_paragraph(doc, placeholder)
    if not paragraph:
        return

    table = doc.add_table(rows=1, cols=4)
    finalize_table(table)
    move_table_after_paragraph(paragraph, table)

    headers = ["Pilar", "Situación actual", "Estado objetivo", "Brecha clave"]
    for idx, header in enumerate(headers):
        set_cell_text(
            table.rows[0].cells[idx],
            header,
            bold=True,
            align=WD_ALIGN_PARAGRAPH.CENTER,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
            space_after=0,
        )
        shade_cell(table.rows[0].cells[idx], "D9EAF7")
    set_repeat_table_header(table.rows[0])

    for item in rows:
        row = table.add_row()
        prevent_row_break(row)
        set_cell_text(row.cells[0], item.get("pillar", ""), align=WD_ALIGN_PARAGRAPH.CENTER, font_size=10, vertical=WD_ALIGN_VERTICAL.CENTER)
        set_cell_text(row.cells[1], item.get("as_is_summary", ""), align=WD_ALIGN_PARAGRAPH.LEFT, font_size=10, vertical=WD_ALIGN_VERTICAL.CENTER)
        set_cell_text(row.cells[2], item.get("target_state", ""), align=WD_ALIGN_PARAGRAPH.LEFT, font_size=10, vertical=WD_ALIGN_VERTICAL.CENTER)
        set_cell_text(row.cells[3], item.get("key_gap", ""), align=WD_ALIGN_PARAGRAPH.LEFT, font_size=10, vertical=WD_ALIGN_VERTICAL.CENTER)

    autofit_table_to_contents(table)
    remove_paragraph(paragraph)


def render_initiative_cards(doc, placeholder, cards):
    paragraph = find_first_paragraph(doc, placeholder)
    if not paragraph:
        return
    if not cards:
        remove_paragraph(paragraph)
        return

    anchor = paragraph
    for idx, item in enumerate(cards, start=1):
        table = doc.add_table(rows=5, cols=2)
        finalize_table(table)
        move_table_after_paragraph(anchor, table)

        title_row = table.rows[0]
        merged = title_row.cells[0].merge(title_row.cells[1])
        set_cell_text(
            merged,
            f"{item.get('sequence', idx)}. {item.get('initiative', '')}",
            bold=True,
            font_size=11,
            align=WD_ALIGN_PARAGRAPH.LEFT,
            vertical=WD_ALIGN_VERTICAL.CENTER,
            space_after=0,
        )
        shade_cell(merged, "D9EAF7")
        prevent_row_break(title_row)

        labels = ["Objetivo", "Prioridad", "Resultado esperado", "Dependencias"]
        values = [
            item.get("objective", ""),
            item.get("priority", ""),
            item.get("expected_outcome", ""),
            item.get("dependencies_display", ""),
        ]
        for row_idx in range(4):
            row = table.rows[row_idx + 1]
            set_cell_text(row.cells[0], labels[row_idx], bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, font_size=10, vertical=WD_ALIGN_VERTICAL.CENTER, space_after=0)
            shade_cell(row.cells[0], "D9EAF7")
            set_cell_text(row.cells[1], values[row_idx], align=WD_ALIGN_PARAGRAPH.LEFT, font_size=10, vertical=WD_ALIGN_VERTICAL.CENTER)
            prevent_row_break(row)

        autofit_table_to_contents(table)
        spacer = insert_paragraph_after_block(table)
        spacer.paragraph_format.space_after = Pt(6)
        add_run(spacer, "", font_size=1)
        anchor = spacer

    remove_paragraph(paragraph)


def render_radar_chart(doc, placeholder, image_path):
    paragraph = find_first_paragraph(doc, placeholder)
    if not paragraph:
        return

    path = resolve_radar_chart_image(image_path)
    if path is None:
        remove_paragraph(paragraph)
        return

    clear_paragraph(paragraph)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    run.add_picture(str(path), width=Inches(4.35))
    paragraph.paragraph_format.space_after = Pt(6)


def add_heading_paragraph(doc, text, level=1):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = paragraph.add_run(clean_text(text))

    if level == 1:
        run.bold = False
        paragraph.paragraph_format.space_before = Pt(18)
        paragraph.paragraph_format.space_after = Pt(18)
        paragraph.paragraph_format.page_break_before = False
        run.font.name = "Georgia"
        run.font.size = Pt(20)
        run.font.color.rgb = RGBColor(0, 114, 188)
    elif level == 2:
        run.bold = False
        paragraph.paragraph_format.space_before = Pt(12)
        paragraph.paragraph_format.space_after = Pt(12)
        run.font.name = "Georgia"
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(0, 114, 188)
    else:
        run.bold = True
        paragraph.paragraph_format.space_before = Pt(3)
        paragraph.paragraph_format.space_after = Pt(4)
        run.font.size = Pt(11.5)

    return paragraph


def add_body_paragraph(doc, text, justify=True, space_after=6, color_rgb=None):
    text = clean_text(text)
    if not text:
        return None
    paragraph = doc.add_paragraph()
    add_run(paragraph, text, font_size=10.5)
    apply_body_format(paragraph, justify=justify, space_after=space_after)
    if color_rgb:
        for run in paragraph.runs:
            run.font.color.rgb = color_rgb
    return paragraph


def add_bullet_list(doc, items):
    items = [clean_text(item) for item in items if clean_text(item)]
    for item in items:
        paragraph = doc.add_paragraph()
        strip_numbering_and_indents(paragraph)
        apply_bullet_list_format(paragraph)
        text = paragraph.add_run(item)
        text.font.size = Pt(10)


def add_label_value_paragraph(doc, label, value):
    value = clean_text(value)
    if not value:
        return None
    paragraph = doc.add_paragraph()
    label_run = paragraph.add_run(f"{label}: ")
    label_run.bold = True
    label_run.font.size = Pt(10.5)
    value_run = paragraph.add_run(value)
    value_run.font.size = Pt(10.5)
    apply_body_format(paragraph, justify=False, space_after=4)
    return paragraph


def add_long_detail_table(doc, title, rows):
    rows = [
        (clean_text(label), clean_text(value))
        for label, value in rows
        if clean_text(value)
    ]
    if not rows:
        return None

    table = doc.add_table(rows=len(rows) + 1, cols=2)
    finalize_table(table)

    header = table.rows[0]
    merged = header.cells[0].merge(header.cells[1])
    set_cell_text(
        merged,
        title,
        bold=True,
        font_size=11,
        align=WD_ALIGN_PARAGRAPH.LEFT,
        vertical=WD_ALIGN_VERTICAL.CENTER,
        space_after=0,
    )
    shade_cell(merged, "D9EAF7")
    prevent_row_break(header)

    for idx, (label, value) in enumerate(rows, start=1):
        row = table.rows[idx]
        set_cell_text(row.cells[0], label, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, font_size=10, vertical=WD_ALIGN_VERTICAL.CENTER, space_after=0)
        shade_cell(row.cells[0], "EEF5FB")
        set_cell_text(row.cells[1], value, align=WD_ALIGN_PARAGRAPH.LEFT, font_size=10, vertical=WD_ALIGN_VERTICAL.CENTER)
        prevent_row_break(row)

    autofit_table_to_contents(table)
    return table


def remove_page_break_only_paragraphs(doc):
    to_remove = []
    for paragraph in doc.paragraphs:
        has_text = bool(clean_text(paragraph.text))
        has_page_break = False
        for run in paragraph.runs:
            for br in run._r.findall(
                ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}br"
            ):
                if (
                    br.get(
                        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type"
                    )
                    == "page"
                ):
                    has_page_break = True
        if has_page_break and not has_text:
            to_remove.append(paragraph)
    for paragraph in to_remove:
        remove_paragraph(paragraph)
