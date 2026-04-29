"""
Módulo render_tower_annex_from_template.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import json
import sys
import base64
import tempfile
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.table import Table
from docx.text.paragraph import Paragraph

from assessment_engine.scripts.lib.text_utils import clean_text_for_word
from assessment_engine.scripts.lib.contract_utils import robust_load_payload

from assessment_engine.schemas.annex_synthesis import AnnexPayload
from pydantic import ValidationError

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def clean_brackets_and_consultant_notes(doc, payload: AnnexPayload):
    meta = payload.document_meta
    intro = payload.domain_introduction

    client_name = meta.get("client_name", "CLIENTE")
    tower_name = meta.get("tower_name", "TORRE")
    tower_code = meta.get("tower_code", "TX")

    # 1. Definir los reemplazos en línea
    replacements = {
        "[Nombre del Cliente]": client_name,
        "[número]": "los",
        "[número de pilares]": "varios",
        "-[Lista de torres evaluadas]": f"• {tower_name}",
        "[Lista de torres evaluadas]": tower_name,
        "T[X]": tower_code,
        "[Nombre de la Torre]": tower_name,
        "[Código]": tower_code,
        "[Nombre de la torre]": tower_name,
        "[descripción del dominio]": intro.domain_objective,
        "descripción del dominio tecnológico": intro.technological_domain,
        "Nivel de madurez obtenido: [Nivel de madurez de la torre]": "",
        "El resultado de [X.X] sitúa la torre en Nivel [X] – [Descripción].": "",
        "Nivel objetivo:\n[Nivel objetivo recomendado]": "",
        "[INSTRUCCIÓN PARA EL AGENTE:Hazlo extenso y bien estructurado mediante bullets]": "",
        "El análisis del estado actual del dominio Resilience & Continuity permite concluir que la infraestructura presenta un nivel de madurez [nivel de madurez], caracterizado por:": "",
        "[fortaleza identificada]": "",
        "[limitación identificada]": "",
        "[riesgo identificado]": "",
        "Pilar [Nombre del pilar]": "",
        "[Descripción del estado actual basada en las respuestas del cuestionario. Hazla extensa y estructurada por bullets]": "",
        "[capacidad objetivo]": "",
        "[línea de evolución]": "",
        "[Fecha]": meta.get("date", "2026")
    }

    # 2. Eliminar párrafos con notas de consultor completas o marcadores inútiles
    paragraphs_to_remove = []
    for p in doc.paragraphs:
        # Si es un prompt de consultor ("Teniendo en cuenta el resumen de...")
        if "[Teniendo en cuenta el resumen de" in p.text or "[Teniendo en cuenta el Resumen ejecutivo" in p.text:
            paragraphs_to_remove.append(p)
            if "Resumen ejecutivo del documento de contexto" in p.text:
                p.insert_paragraph_before(intro.introduction_paragraph)
            continue
            
        if "[Generar un gráfico" in p.text:
            paragraphs_to_remove.append(p)
            continue
            
        if "[capacidad tecnológica evaluada]" in p.text or "[infraestructura evaluada]" in p.text or "[plataformas tecnológicas incluidas]" in p.text or "[alcance específico del assessment]" in p.text:
            paragraphs_to_remove.append(p)
            continue
            
        if "[P1]" in p.text or "[P2]" in p.text or "[P3]" in p.text or "[P4]" in p.text or "[P5]" in p.text:
            paragraphs_to_remove.append(p)
            continue

        if p.text.strip().startswith("| [Torre]"):
            paragraphs_to_remove.append(p)
            continue
            
        # Reemplazos de texto en línea
        for old, new in replacements.items():
            if old in p.text:
                p.text = p.text.replace(old, new)
                
    for p in paragraphs_to_remove:
        try:
            p._element.getparent().remove(p._element)
        except Exception:
            pass

    # 3. Limpiar Tablas de Plantilla (borrar filas vacías que contienen corchetes de ejemplo)
    for table in doc.tables:
        rows_to_remove = []
        for row in table.rows:
            row_has_bracket = False
            for cell in row.cells:
                for p in cell.paragraphs:
                    if "[" in p.text and "]" in p.text:
                        # Si es solo la fecha, la reemplazamos, si no, marcamos la fila para borrar
                        if "[Fecha]" in p.text:
                            p.text = p.text.replace("[Fecha]", replacements["[Fecha]"])
                        else:
                            row_has_bracket = True
                            break
                if row_has_bracket:
                    break
            if row_has_bracket:
                rows_to_remove.append(row)
        
        # Eliminar las filas
        for row in rows_to_remove:
            try:
                table._tbl.remove(row._tr)
            except Exception:
                pass


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
    for p in doc.paragraphs:
        yield p
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p


def find_first_paragraph(doc, placeholder):
    for p in iter_paragraphs(doc):
        if placeholder in p.text:
            return p
    return None


def clear_paragraph(paragraph):
    p = paragraph._element
    for child in list(p):
        if child.tag != qn("w:pPr"):
            p.remove(child)


def remove_paragraph(paragraph):
    p = paragraph._element
    parent = p.getparent()
    if parent is not None:
        parent.remove(p)


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
    for p in iter_paragraphs(doc):
        if placeholder in p.text:
            text = p.text.replace(placeholder, clean_text(value))
            clear_paragraph(p)
            run = p.add_run(text)
            if font_size:
                run.font.size = Pt(font_size)
            if bold is not None:
                run.bold = bold
            if align:
                p.alignment = align
            p.paragraph_format.space_before = Pt(0)
            if placeholder != "{{SCORING_METHOD_NOTE}}":
                p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.05


def render_multi_paragraph_block(doc, placeholder, texts):
    p = find_first_paragraph(doc, placeholder)
    if not p:
        return
    texts = clean_paragraph_list(texts)
    if not texts:
        remove_paragraph(p)
        return

    clear_paragraph(p)
    add_run(p, texts[0], font_size=10.5)
    apply_body_format(p, justify=True, space_after=6)
    anchor = p

    for text in texts[1:]:
        new_p = insert_paragraph_after_block(anchor)
        add_run(new_p, text, font_size=10.5)
        apply_body_format(new_p, justify=True, space_after=6)
        anchor = new_p


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
    p = find_first_paragraph(doc, placeholder)
    if not p:
        return
    items = [clean_text(x) for x in items if clean_text(x)]
    if not items:
        remove_paragraph(p)
        return

    clear_paragraph(p)
    strip_numbering_and_indents(p)
    if hasattr(p._parent, "vertical_alignment"):
        p._parent.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    anchor = p

    for idx, item in enumerate(items):
        para = anchor if idx == 0 else insert_paragraph_after_block(anchor)
        clear_paragraph(para)
        strip_numbering_and_indents(para)
        if hasattr(para._parent, "vertical_alignment"):
            para._parent.vertical_alignment = WD_ALIGN_VERTICAL.TOP
        bullet = para.add_run("• ")
        bullet.font.size = Pt(10.5)
        content = para.add_run(item)
        content.font.size = Pt(10.5)
        anchor = para


def move_table_after_paragraph(paragraph, table):
    tbl = table._tbl
    paragraph._p.addnext(tbl)


def shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


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
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run(clean_text(text))
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

    # elimina el grid fijo de columnas que Word usa al crear la tabla
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
                tag = child.tag.split("}")[-1]
                if tag == "tcW":
                    tcPr.remove(child)
            tcW = OxmlElement("w:tcW")
            tcW.set(qn("w:type"), "auto")
            tcW.set(qn("w:w"), "0")
            tcPr.append(tcW)


def render_note_box(doc, placeholder, text):
    p = find_first_paragraph(doc, placeholder)
    if not p:
        return
    text = clean_text(text)
    if not text:
        remove_paragraph(p)
        return

    table = doc.add_table(rows=1, cols=1)
    finalize_table(table)
    move_table_after_paragraph(p, table)
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
    remove_paragraph(p)


def render_pillar_score_table(doc, placeholder, rows):
    p = find_first_paragraph(doc, placeholder)
    if not p:
        return

    table = doc.add_table(rows=1, cols=4)
    finalize_table(table)
    move_table_after_paragraph(p, table)

    headers = ["Pilar", "Score", "Nivel", "Lectura ejecutiva"]
    for i, h in enumerate(headers):
        set_cell_text(
            table.rows[0].cells[i],
            h,
            bold=True,
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
            space_after=0,
        )
        shade_cell(table.rows[0].cells[i], "D9EAF7")
    set_repeat_table_header(table.rows[0])

    for item in rows:
        row = table.add_row()
        prevent_row_break(row)
        set_cell_text(
            row.cells[0],
            item.get("pillar_label", ""),
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10.2,
            vertical=WD_ALIGN_VERTICAL.CENTER,
        )
        set_cell_text(
            row.cells[1],
            item.get("score_display", ""),
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10.2,
            vertical=WD_ALIGN_VERTICAL.CENTER,
        )
        set_cell_text(
            row.cells[2],
            item.get("maturity_band", ""),
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10.2,
            vertical=WD_ALIGN_VERTICAL.CENTER,
        )
        set_cell_text(
            row.cells[3],
            item.get("executive_reading", ""),
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10.2,
            vertical=WD_ALIGN_VERTICAL.CENTER,
        )

    autofit_table_to_contents(table)
    remove_paragraph(p)


def render_risks_table(doc, placeholder, rows):
    p = find_first_paragraph(doc, placeholder)
    if not p:
        return

    table = doc.add_table(rows=1, cols=4)
    finalize_table(table)
    move_table_after_paragraph(p, table)

    headers = ["Riesgo", "Impacto", "Probabilidad", "Mitigación resumida"]
    for i, h in enumerate(headers):
        set_cell_text(
            table.rows[0].cells[i],
            h,
            bold=True,
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
            space_after=0,
        )
        shade_cell(table.rows[0].cells[i], "D9EAF7")
    set_repeat_table_header(table.rows[0])

    for item in rows:
        row = table.add_row()
        prevent_row_break(row)
        set_cell_text(
            row.cells[0],
            item.get("risk", ""),
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
        )
        set_cell_text(
            row.cells[1],
            item.get("impact", ""),
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
        )
        set_cell_text(
            row.cells[2],
            item.get("probability", ""),
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
        )
        set_cell_text(
            row.cells[3],
            item.get("mitigation_summary", ""),
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
        )

    autofit_table_to_contents(table)
    remove_paragraph(p)


def render_gap_table(doc, placeholder, rows):
    p = find_first_paragraph(doc, placeholder)
    if not p:
        return

    table = doc.add_table(rows=1, cols=4)
    finalize_table(table)
    move_table_after_paragraph(p, table)

    headers = ["Pilar", "Situación actual", "Estado objetivo", "Brecha clave"]
    for i, h in enumerate(headers):
        set_cell_text(
            table.rows[0].cells[i],
            h,
            bold=True,
            align=WD_ALIGN_PARAGRAPH.CENTER,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
            space_after=0,
        )
        shade_cell(table.rows[0].cells[i], "D9EAF7")
    set_repeat_table_header(table.rows[0])

    for item in rows:
        row = table.add_row()
        prevent_row_break(row)
        set_cell_text(
            row.cells[0],
            item.get("pillar", ""),
            align=WD_ALIGN_PARAGRAPH.CENTER,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
        )
        set_cell_text(
            row.cells[1],
            item.get("as_is_summary", ""),
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
        )
        set_cell_text(
            row.cells[2],
            item.get("target_state", ""),
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
        )
        set_cell_text(
            row.cells[3],
            item.get("key_gap", ""),
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
        )

    autofit_table_to_contents(table)
    remove_paragraph(p)


def render_initiative_cards(doc, placeholder, cards):
    p = find_first_paragraph(doc, placeholder)
    if not p:
        return
    if not cards:
        remove_paragraph(p)
        return

    anchor = p
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
        for r in range(4):
            row = table.rows[r + 1]
            set_cell_text(
                row.cells[0],
                labels[r],
                bold=True,
                align=WD_ALIGN_PARAGRAPH.LEFT,
                font_size=10,
                vertical=WD_ALIGN_VERTICAL.CENTER,
                space_after=0,
            )
            shade_cell(row.cells[0], "D9EAF7")
            set_cell_text(
                row.cells[1],
                values[r],
                align=WD_ALIGN_PARAGRAPH.LEFT,
                font_size=10,
                vertical=WD_ALIGN_VERTICAL.CENTER,
            )
            prevent_row_break(row)

        autofit_table_to_contents(table)

        spacer = insert_paragraph_after_block(table)
        spacer.paragraph_format.space_after = Pt(6)
        add_run(spacer, "", font_size=1)
        anchor = spacer

    remove_paragraph(p)


def render_radar_chart(doc, placeholder, image_path):
    p = find_first_paragraph(doc, placeholder)
    if not p:
        return

    path = resolve_radar_chart_image(image_path)
    if path is None:
        remove_paragraph(p)
        return

    clear_paragraph(p)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(path), width=Inches(4.35))
    p.paragraph_format.space_after = Pt(6)


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
        for r in paragraph.runs:
            r.font.color.rgb = color_rgb
    return paragraph


def add_bullet_list(doc, items):
    items = [clean_text(item) for item in items if clean_text(item)]
    for item in items:
        paragraph = doc.add_paragraph()
        strip_numbering_and_indents(paragraph)
        bullet = paragraph.add_run("• ")
        bullet.font.size = Pt(10.5)
        text = paragraph.add_run(item)
        text.font.size = Pt(10.5)


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
        set_cell_text(
            row.cells[0],
            label,
            bold=True,
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
            space_after=0,
        )
        shade_cell(row.cells[0], "EEF5FB")
        set_cell_text(
            row.cells[1],
            value,
            align=WD_ALIGN_PARAGRAPH.LEFT,
            font_size=10,
            vertical=WD_ALIGN_VERTICAL.CENTER,
        )
        prevent_row_break(row)

    autofit_table_to_contents(table)
    return table


def render_extended_variant(doc, payload):
    extended = payload.get("extended_sections") or {}
    if not extended:
        return

    doc.add_page_break()
    add_heading_paragraph(doc, "Desarrollo ampliado", level=1)
    add_body_paragraph(
        doc,
        "Esta versión desarrolla con más detalle el diagnóstico, el estado objetivo, las brechas y las iniciativas prioritarias de la torre.",
    )

    asis = extended.get("asis", {})
    add_heading_paragraph(doc, "1. AS-IS detallado", level=1)
    add_body_paragraph(doc, asis.get("executive_narrative", ""))
    add_label_value_paragraph(
        doc, "Madurez actual", asis.get("current_maturity_band", "")
    )
    add_label_value_paragraph(
        doc, "Referencia de score", asis.get("current_score_reference", "")
    )
    if asis.get("strengths"):
        add_heading_paragraph(doc, "Fortalezas observadas", level=2)
        add_bullet_list(doc, asis.get("strengths", []))
    if asis.get("gaps"):
        add_heading_paragraph(doc, "Brechas observadas", level=2)
        add_bullet_list(doc, asis.get("gaps", []))
    if asis.get("operational_impacts"):
        add_heading_paragraph(doc, "Implicaciones operativas", level=2)
        add_bullet_list(doc, asis.get("operational_impacts", []))

    risks = extended.get("risks", {})
    add_heading_paragraph(doc, "2. Riesgos detallados", level=1)
    add_body_paragraph(doc, risks.get("introduction", ""))
    for idx, item in enumerate(risks.get("risk_details", []), start=1):
        add_long_detail_table(
            doc,
            f"Riesgo {idx}. {item.get('risk', '')}",
            [
                ("Causa", item.get("cause", "")),
                ("Impacto", item.get("impact", "")),
                ("Probabilidad", item.get("probability", "")),
                ("Mitigación", item.get("mitigation_summary", "")),
                ("Pilares afectados", item.get("affected_pillars_display", "")),
            ],
        )
        add_body_paragraph(doc, "", space_after=2)
    add_body_paragraph(doc, risks.get("closing_summary", ""))

    tobe = extended.get("tobe", {})
    add_heading_paragraph(doc, "3. Estado objetivo detallado", level=1)
    add_body_paragraph(doc, tobe.get("introduction", ""))
    add_label_value_paragraph(
        doc, "Madurez objetivo recomendada", tobe.get("target_maturity_level", "")
    )
    add_label_value_paragraph(
        doc, "Referencia de score objetivo", tobe.get("target_score_reference", "")
    )
    add_body_paragraph(doc, tobe.get("target_maturity_justification", ""))
    for pillar in tobe.get("target_capabilities_by_pillar", []):
        add_heading_paragraph(doc, pillar.get("pillar", ""), level=2)
        add_bullet_list(doc, pillar.get("target_capabilities", []))
    if tobe.get("architecture_principles"):
        add_heading_paragraph(doc, "Principios de arquitectura y operación", level=2)
        add_bullet_list(doc, tobe.get("architecture_principles", []))
    if tobe.get("operating_model_implications"):
        add_heading_paragraph(doc, "Implicaciones para el modelo operativo", level=2)
        add_bullet_list(doc, tobe.get("operating_model_implications", []))

    gap = extended.get("gap", {})
    add_heading_paragraph(doc, "4. Brechas detalladas", level=1)
    add_body_paragraph(doc, gap.get("introduction", ""))
    if gap.get("cross_cutting_gap_summary"):
        add_heading_paragraph(doc, "Lectura transversal de gaps", level=2)
        add_bullet_list(doc, gap.get("cross_cutting_gap_summary", []))
    for idx, item in enumerate(gap.get("gap_items", []), start=1):
        add_long_detail_table(
            doc,
            f"Gap {idx}. {item.get('pillar', '')}",
            [
                ("Situación actual", item.get("as_is_summary", "")),
                ("Estado objetivo", item.get("target_state", "")),
                ("Brecha clave", item.get("key_gap", "")),
                ("Implicación operativa", item.get("operational_implication", "")),
            ],
        )
        add_body_paragraph(doc, "", space_after=2)

    todo = extended.get("todo", {})
    add_heading_paragraph(doc, "5. Iniciativas priorizadas detalladas", level=1)
    add_body_paragraph(doc, todo.get("introduction", ""))
    for item in todo.get("todo_items", []):
        add_long_detail_table(
            doc,
            f"{item.get('sequence', '')}. {item.get('initiative', '')}",
            [
                ("Objetivo", item.get("objective", "")),
                ("Prioridad", item.get("priority", "")),
                ("Pilares relacionados", item.get("related_pillars_display", "")),
                ("Resultado esperado", item.get("expected_outcome", "")),
                ("Dependencias", item.get("dependencies_display", "")),
            ],
        )
        add_body_paragraph(doc, "", space_after=2)
    add_body_paragraph(doc, todo.get("closing_summary", ""))

    conclusion = extended.get("conclusion", {})
    add_heading_paragraph(doc, "6. Cierre ampliado", level=1)
    add_body_paragraph(doc, conclusion.get("final_assessment", ""))
    add_body_paragraph(doc, conclusion.get("executive_message", ""))
    if conclusion.get("priority_focus_areas"):
        add_heading_paragraph(doc, "Áreas de foco prioritarias", level=2)
        add_bullet_list(doc, conclusion.get("priority_focus_areas", []))
    add_body_paragraph(doc, conclusion.get("closing_statement", ""))


def remove_page_break_only_paragraphs(doc):
    to_remove = []
    for p in doc.paragraphs:
        has_text = bool(clean_text(p.text))
        has_page_break = False
        for run in p.runs:
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
            to_remove.append(p)
    for p in to_remove:
        remove_paragraph(p)


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) != 4:
        raise SystemExit(
            "Uso: python -m scripts.render_tower_annex_from_template <payload_json> <template_docx> <output_docx>"
        )

    payload_path = Path((argv if argv is not None else sys.argv)[1]).resolve()
    template_path = Path((argv if argv is not None else sys.argv)[2]).resolve()
    output_path = Path((argv if argv is not None else sys.argv)[3]).resolve()

    # Cargar y validar contrato de forma robusta
    payload = robust_load_payload(payload_path, AnnexPayload, "Annex")
    payload_dict = payload.model_dump(by_alias=True)
        
    doc = Document(str(template_path))
    remove_page_break_only_paragraphs(doc)
    clean_brackets_and_consultant_notes(doc, payload)

    meta = payload.document_meta
    exec_summary = payload.executive_summary
    profile = payload.pillar_score_profile
    sections = payload.sections
    variant = clean_text(meta.get("report_variant", "short")).lower()
    subtitle_suffix = " · Versión Extendida" if variant == "long" else ""

    replace_simple_placeholder(
        doc,
        "{{ANNEX_TITLE}}",
        f"ANEXO {meta['tower_code']} – {meta['tower_name']}",
        font_size=15,
        bold=True,
    )
    replace_simple_placeholder(doc, "{{TOWER_CODE}}", meta["tower_code"], font_size=15)
    replace_simple_placeholder(doc, "{{TOWER_NAME}}", meta["tower_name"], font_size=15)
    replace_simple_placeholder(
        doc,
        "{{ANNEX_SUBTITLE}}",
        f"{meta['client_name']} · Fast Infrastructure Assessment{subtitle_suffix}",
        font_size=11,
    )
    replace_simple_placeholder(
        doc, "{{CLIENT_NAME}}", meta["client_name"], font_size=11
    )

    replace_simple_placeholder(
        doc,
        "{{GLOBAL_SCORE}}",
        exec_summary.global_score,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        font_size=13,
    )
    replace_simple_placeholder(
        doc,
        "{{GLOBAL_BAND}}",
        exec_summary.global_band,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        font_size=13,
    )
    replace_simple_placeholder(
        doc,
        "{{TARGET_MATURITY}}",
        exec_summary.target_maturity,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        font_size=13,
    )

    render_multi_paragraph_block(
        doc, "{{EXEC_SUMMARY_BODY}}", exec_summary.summary_body
    )
    replace_simple_placeholder(
        doc, "{{MSG_STRENGTH_VALUE}}", exec_summary.message_strength, font_size=10.5
    )
    replace_simple_placeholder(
        doc, "{{MSG_GAP_VALUE}}", exec_summary.message_gap, font_size=10.5
    )
    replace_simple_placeholder(
        doc,
        "{{MSG_BOTTLENECK_VALUE}}",
        exec_summary.message_bottleneck,
        font_size=10.5,
    )

    replace_simple_placeholder(
        doc, "{{PILLAR_PROFILE_INTRO}}", profile.profile_intro, font_size=10.5
    )
    render_note_box(doc, "{{SCORING_METHOD_NOTE}}", profile.scoring_method_note)
    render_radar_chart(doc, "{{RADAR_CHART_BLOCK}}", profile.radar_chart)
    render_pillar_score_table(doc, "{{PILLAR_SCORE_TABLE}}", profile.pillars)

    replace_simple_placeholder(
        doc, "{{ASIS_NARRATIVE}}", sections.asis.narrative, font_size=10.5
    )
    render_list_at_placeholder(
        doc, "{{ASIS_STRENGTHS_LIST}}", sections.asis.strengths
    )
    render_list_at_placeholder(doc, "{{ASIS_GAPS_LIST}}", sections.asis.gaps)
    render_list_at_placeholder(
        doc,
        "{{ASIS_OPERATIONAL_IMPACTS_LIST}}",
        sections.asis.operational_impacts,
    )

    replace_simple_placeholder(
        doc, "{{RISKS_INTRO}}", sections.risks.introduction, font_size=10.5
    )
    render_risks_table(
        doc, "{{RISKS_TABLE}}", [r.model_dump() for r in sections.risks.risks]
    )
    replace_simple_placeholder(
        doc, "{{RISKS_CLOSING}}", sections.risks.closing_summary, font_size=10.5
    )

    replace_simple_placeholder(
        doc,
        "{{TOBE_INTRO}}",
        sections.tobe.vision or sections.gap.introduction,
        font_size=10.5,
    )
    render_list_at_placeholder(
        doc,
        "{{TARGET_CAPABILITIES_LIST}}",
        sections.gap.target_capabilities or sections.tobe.design_principles,
    )
    render_gap_table(
        doc, "{{GAP_TABLE}}", [g.model_dump() for g in sections.gap.gap_rows]
    )

    replace_simple_placeholder(
        doc, "{{TODO_INTRO}}", sections.todo.introduction, font_size=10.5
    )
    render_initiative_cards(
        doc, "{{PRIORITY_INITIATIVES_CARDS}}", [i.model_dump() for i in sections.todo.priority_initiatives]
    )

    replace_simple_placeholder(
        doc,
        "{{FINAL_ASSESSMENT}}",
        sections.conclusion.final_assessment,
        font_size=10.5,
    )
    replace_simple_placeholder(
        doc,
        "{{EXECUTIVE_MESSAGE}}",
        sections.conclusion.executive_message,
        font_size=10.5,
    )
    render_list_at_placeholder(
        doc, "{{PRIORITY_AREAS_LIST}}", sections.conclusion.priority_focus_areas
    )
    replace_simple_placeholder(
        doc,
        "{{CLOSING_STATEMENT}}",
        sections.conclusion.closing_statement,
        font_size=10.5,
    )

    if variant == "long":
        render_extended_variant(doc, payload_dict)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print("Documento renderizado en:", output_path)


if __name__ == "__main__":
    main()
