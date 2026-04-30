"""
Módulo render_global_report_from_template.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import json
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

from assessment_engine.scripts.lib.docx_render_utils import (
    add_body_paragraph,
    add_heading_paragraph,
    autofit_table_to_contents,
    clear_paragraph,
    finalize_table,
    set_cell_text,
    shade_cell,
)


from assessment_engine.schemas.global_report import GlobalReportPayload, ExecutiveSummaryDraft, BurningPlatformItem, TargetVisionDraft, ExecutionRoadmapDraft, ExecutiveDecisionsDraft
from pydantic import ValidationError

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))



def clean_t_codes(text):
    if not isinstance(text, str):
        return text
    text = re.sub(r"\(T\d{1,2}[^\)]*\)", "", text)
    text = re.sub(r"\bT\d{1,2}\b", "", text)
    # Strip any [[REF:...]] or [REF:...] tags
    text = re.sub(r"\[\[?REF:[^\]]*\]\]?", "", text)
    return text.strip()


def sanitize_client_name(text, client_name):
    if not isinstance(text, str) or not client_name:
        return text

    # Reemplazar nombre del cliente con guiones bajos (ej: smoke_moeve)
    clean_name = client_name.replace("_", " ")

    # 1. Eliminar "de [Cliente]" o "del [Cliente]"
    text = re.sub(
        rf"\s+del?\s+{re.escape(client_name)}\b", "", text, flags=re.IGNORECASE
    )
    text = re.sub(
        rf"\s+del?\s+{re.escape(clean_name)}\b", "", text, flags=re.IGNORECASE
    )

    # 2. Reemplazar menciones directas por "la organización"
    text = re.sub(
        rf"\b{re.escape(client_name)}\b", "la organización", text, flags=re.IGNORECASE
    )
    text = re.sub(
        rf"\b{re.escape(clean_name)}\b", "la organización", text, flags=re.IGNORECASE
    )

    return text


def clear_document_body(doc):
    body = doc._body._element
    for child in list(body):
        if (
            child.tag
            != "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sectPr"
        ):
            body.remove(child)


def add_spacer(doc, points=12):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(points)


def add_smart_bullet_list(container, items, color_rgb=None, bold_prefix=True):
    # Robustez: si nos llega un string en lugar de una lista, lo envolvemos para no iterar por caracteres
    if isinstance(items, str):
        items = [items]
    if not items:
        return

    for item in items:
        p = container.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        try:
            p.style = "List Bullet"
        except KeyError:
            # Fallback en caso de que el estilo no exista en la plantilla
            p.paragraph_format.left_indent = Pt(20)
            p.paragraph_format.first_line_indent = Pt(-15)
            b = p.add_run("• ")
            b.font.size = Pt(10.5)
            if color_rgb:
                b.font.color.rgb = color_rgb

        p.paragraph_format.space_after = Pt(6)
        text = clean_t_codes(str(item).strip())

        sep = ": " if ": " in text else (" - " if " - " in text else None)
        if sep:
            parts = text.split(sep, 1)
            r1 = p.add_run(parts[0] + sep)
            r1.bold = bold_prefix
            r1.font.size = Pt(10.5)
            r2 = p.add_run(parts[1])
            r2.font.size = Pt(10.5)
            if color_rgb:
                r1.font.color.rgb = color_rgb
                r2.font.color.rgb = color_rgb
        else:
            r = p.add_run(text)
            r.bold = bold_prefix
            r.font.size = Pt(10.5)
            if color_rgb:
                r.font.color.rgb = color_rgb


def render_cover(doc, payload: GlobalReportPayload):
    # Reducimos algo el margen superior inicial
    doc.add_paragraph().paragraph_format.space_after = Pt(60)
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    # Title Case excepto preposiciones
    run = title_p.add_run("Informe Estratégico de\nMadurez Tecnológica")
    run.font.size = Pt(34)
    run.font.name = "Georgia"
    run.font.color.rgb = RGBColor(0, 114, 188)
    run.bold = False

    # Menos espacio entre título y nombre del cliente
    add_spacer(doc, 30)

    client_p = doc.add_paragraph()
    client_run = client_p.add_run(
        payload.meta.client.upper()
    )
    client_run.font.size = Pt(24)
    client_run.font.name = "Arial"
    client_run.bold = True

    # Reducimos sustancialmente este bloque que empujaba la fecha muy abajo
    doc.add_paragraph().paragraph_format.space_after = Pt(100)

    version_p = doc.add_paragraph()
    v_text = f"Fecha: {payload.meta.date}\nReferencia: {payload.meta.version}"
    version_run = version_p.add_run(v_text)
    version_run.font.size = Pt(14)
    version_run.font.name = "Arial"
    version_run.font.color.rgb = RGBColor(127, 127, 127)

    # Espaciador ajustado (150pt) para que el aviso legal esté bajo pero no salte de página
    add_spacer(doc, 150)

    disclaimer_p1 = doc.add_paragraph()
    disclaimer_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    disclaimer_p1.paragraph_format.space_after = Pt(
        2
    )  # Espacio mínimo entre párrafos del aviso
    disclaimer_title_run = disclaimer_p1.add_run("Aviso Legal y Confidencialidad: ")
    disclaimer_title_run.font.size = Pt(8)
    disclaimer_title_run.font.name = "Arial"
    disclaimer_title_run.font.color.rgb = RGBColor(127, 127, 127)
    disclaimer_title_run.bold = True

    p1_text = "El presente documento constituye un informe de evaluación rápida (Fast Assessment) elaborado por NTT DATA basándose exclusivamente en la información, entrevistas y datos proporcionados por la organización, los cuales no han sido sometidos a una auditoría o verificación independiente por nuestra parte. Por tanto, NTT DATA no otorga ninguna garantía, expresa o implícita, sobre la exactitud, integridad o fiabilidad absoluta de dicha información base."
    r1 = disclaimer_p1.add_run(p1_text)
    r1.font.size = Pt(8)
    r1.font.name = "Arial"
    r1.font.color.rgb = RGBColor(127, 127, 127)

    disclaimer_p2 = doc.add_paragraph()
    disclaimer_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    disclaimer_p2.paragraph_format.space_after = Pt(2)
    p2_text = 'Las conclusiones, proyecciones (incluyendo el estado objetivo "TO-BE", los horizontes del roadmap y las estimaciones de impacto de negocio) y recomendaciones tienen un carácter puramente orientativo. Estas proyecciones constituyen estimaciones sujetas a incertidumbres operativas y de mercado, por lo que los resultados reales futuros podrían diferir de los planteados.'
    r2 = disclaimer_p2.add_run(p2_text)
    r2.font.size = Pt(8)
    r2.font.name = "Arial"
    r2.font.color.rgb = RGBColor(127, 127, 127)

    disclaimer_p3 = doc.add_paragraph()
    disclaimer_p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    disclaimer_p3.paragraph_format.space_after = Pt(2)
    p3_text = "Este informe tiene un propósito estrictamente técnico y estratégico. Toda decisión ejecutiva, operativa o de inversión que la organización tome basándose en este informe es de su exclusiva responsabilidad. NTT DATA y sus representantes no asumen obligación legal ni responsabilidad alguna por posibles daños directos, indirectos, especiales o consecuentes derivados del uso o dependencia de la información aquí contenida sin una validación posterior exhaustiva."
    r3 = disclaimer_p3.add_run(p3_text)
    r3.font.size = Pt(8)
    r3.font.name = "Arial"
    r3.font.color.rgb = RGBColor(127, 127, 127)

    disclaimer_p4 = doc.add_paragraph()
    disclaimer_p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    disclaimer_p4.paragraph_format.space_after = Pt(0)
    p4_text = "Finalmente, este documento y la información que contiene son confidenciales. Este material no podrá ser distribuido, reproducido, divulgado ni utilizado para ningún otro propósito, total o parcialmente, sin el consentimiento previo por escrito de NTT DATA."
    r4 = disclaimer_p4.add_run(p4_text)
    r4.font.size = Pt(8)
    r4.font.name = "Arial"
    r4.font.color.rgb = RGBColor(127, 127, 127)

    doc.add_page_break()


def render_executive_summary(doc, data: ExecutiveSummaryDraft, heatmap: list, visuals: dict, client_dir, client_name=""):
    BASE_TEXT_COLOR = RGBColor(46, 64, 77)  # #2E404D
    add_heading_paragraph(doc, "1. Resumen Ejecutivo", level=1)
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False

    # Configurar anchos: 35% (2.1") y 65% (3.9") aprox para A4
    table.columns[0].width = Inches(2.1)
    table.columns[1].width = Inches(3.9)

    score_cell = table.rows[0].cells[0]
    score_cell.width = Inches(2.1)
    score_val = "N/A"
    if heatmap:
        try:
            score_val = str(
                round(
                    sum(float(t.get("score", 0)) for t in heatmap) / len(heatmap),
                    1,
                )
            )
        except Exception:
            pass

    # Formato puntuación: [X] / 5, fondo #0072BC, tamaño 36, blanco
    set_cell_text(
        score_cell,
        f"{score_val} / 5",
        bold=True,
        font_size=36,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    shade_cell(score_cell, "0072BC")
    for r in score_cell.paragraphs[0].runs:
        r.font.color.rgb = RGBColor(255, 255, 255)

    desc_cell = table.rows[0].cells[1]
    desc_cell.width = Inches(3.9)
    desc_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    shade_cell(desc_cell, "F2F2F2")

    headline = sanitize_client_name(
        clean_t_codes(data.headline), client_name
    )

    # Formato de titular: solo negrita antes de los dos puntos
    clear_paragraph(desc_cell.paragraphs[0])
    p = desc_cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if ":" in headline:
        parts = headline.split(":", 1)
        r1 = p.add_run(parts[0] + ":")
        r1.bold = True
        r1.font.size = Pt(12)
        r1.font.name = "Arial"
        r2 = p.add_run(parts[1])
        r2.bold = False
        r2.font.size = Pt(12)
        r2.font.name = "Arial"
    else:
        r = p.add_run(headline)
        r.bold = False
        r.font.size = Pt(12)
        r.font.name = "Arial"

    add_spacer(doc, 15)

    # Narrativa y Bullets FUERA de la tabla para mejor legibilidad
    narrative = sanitize_client_name(
        clean_t_codes(data.narrative), client_name
    )
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚ])", narrative.strip())

    if sentences:
        # La primera frase actúa como el Bottom Line
        p_intro = doc.add_paragraph()
        p_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r_intro = p_intro.add_run(sentences[0])
        r_intro.font.size = Pt(10.5)
        r_intro.font.color.rgb = BASE_TEXT_COLOR
        p_intro.paragraph_format.space_before = Pt(12)
        p_intro.paragraph_format.space_after = Pt(6)

        # El resto de frases se presentan como bullets
        if len(sentences) > 1:
            add_smart_bullet_list(
                doc, sentences[1:], color_rgb=BASE_TEXT_COLOR, bold_prefix=False
            )

    add_spacer(doc, 15)

    # Tabla de Principales Impactos de Negocio
    impact_table = doc.add_table(rows=1, cols=1)
    finalize_table(impact_table)

    header_cell = impact_table.rows[0].cells[0]
    set_cell_text(
        header_cell,
        "Principales impactos de negocio",
        bold=True,
        font_size=10.5,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    shade_cell(header_cell, "0072BC")
    for r in header_cell.paragraphs[0].runs:
        r.font.color.rgb = RGBColor(255, 255, 255)

    impacts = [
        sanitize_client_name(i, client_name)
        for i in data.key_business_impacts
    ]
    for impact in impacts:
        row = impact_table.add_row()
        body_cell = row.cells[0]
        shade_cell(body_cell, "F2F2F2")

        # Escribir directamente en el párrafo 0 de la celda para evitar el "intro" extra
        p_bull = body_cell.paragraphs[0]
        clear_paragraph(p_bull)
        p_bull.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        try:
            p_bull.style = "List Bullet"
        except KeyError:
            p_bull.paragraph_format.left_indent = Pt(20)
            p_bull.paragraph_format.first_line_indent = Pt(-15)
            b_run = p_bull.add_run("• ")
            b_run.font.size = Pt(10.5)
            b_run.font.color.rgb = BASE_TEXT_COLOR

        p_bull.paragraph_format.space_before = Pt(4)
        p_bull.paragraph_format.space_after = Pt(4)

        text = clean_t_codes(str(impact).strip())
        r_text = p_bull.add_run(text)
        r_text.bold = False
        r_text.font.size = Pt(10.5)
        r_text.font.color.rgb = BASE_TEXT_COLOR

    radar_path = client_dir / visuals.get("radar_chart", "")
    if radar_path.exists():
        add_spacer(doc, 15)
        doc.add_picture(str(radar_path), width=Inches(6.8))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER


def render_burning_platform(doc, platform_risks: list[BurningPlatformItem], client_name=""):
    BASE_TEXT_COLOR = RGBColor(46, 64, 77)  # #2E404D
    add_heading_paragraph(doc, "2. Principales Amenazas Sistémicas", level=1)
    add_body_paragraph(
        doc,
        "Identificación de riesgos críticos que comprometen la viabilidad operativa y la agilidad de la organización.",
        color_rgb=BASE_TEXT_COLOR,
    )
    for i, risk in enumerate(platform_risks, start=1):
        table = doc.add_table(rows=3, cols=1)
        finalize_table(table)

        # Row 0: Header
        h_cell = table.rows[0].cells[0]
        theme = sanitize_client_name(clean_t_codes(risk.theme), client_name)
        theme = theme[0].upper() + theme[1:] if theme else ""
        set_cell_text(
            h_cell,
            f"Amenaza {i}: {theme}",
            bold=True,
            font_size=10.5,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(h_cell, "0072BC")
        for r in h_cell.paragraphs[0].runs:
            r.font.color.rgb = RGBColor(255, 255, 255)

        # Row 1: Riesgo de Negocio
        r_cell = table.rows[1].cells[0]
        shade_cell(r_cell, "F2F2F2")
        clear_paragraph(r_cell.paragraphs[0])
        p1 = r_cell.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r1_label = p1.add_run("Riesgo de Negocio: ")
        r1_label.bold = True
        r1_label.font.color.rgb = BASE_TEXT_COLOR
        r1_label.font.size = Pt(10.5)
        r1_text = p1.add_run(
            sanitize_client_name(
                clean_t_codes(risk.business_risk), client_name
            )
        )
        r1_text.bold = False
        r1_text.font.color.rgb = BASE_TEXT_COLOR
        r1_text.font.size = Pt(10.5)

        # Row 2: Causas Raíz
        c_cell = table.rows[2].cells[0]
        shade_cell(c_cell, "F2F2F2")
        clear_paragraph(c_cell.paragraphs[0])
        p2 = c_cell.paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r2_label = p2.add_run("Causas Raíz: ")
        r2_label.bold = True
        r2_label.font.color.rgb = BASE_TEXT_COLOR
        r2_label.font.size = Pt(10.5)
        causes_list = risk.root_causes
        sanitized_causes = [
            sanitize_client_name(clean_t_codes(c), client_name) for c in causes_list
        ]
        r2_text = p2.add_run("\n" + "\n".join([f"  • {c}" for c in sanitized_causes]))
        r2_text.bold = False
        r2_text.font.color.rgb = BASE_TEXT_COLOR
        r2_text.font.size = Pt(10.5)

        add_spacer(doc, 10)


def render_tower_bottom_lines(doc, heatmap: list, tower_texts: list[dict], client_name=""):
    BASE_TEXT_COLOR = RGBColor(46, 64, 77)  # #2E404D
    add_heading_paragraph(doc, "3. Diagnóstico por Área Tecnológica", level=1)
    table = doc.add_table(rows=1, cols=3)
    finalize_table(table)
    for i, h in enumerate(["Área", "Madurez", "Diagnóstico Ejecutivo"]):
        set_cell_text(
            table.rows[0].cells[i],
            h,
            bold=False,
            font_size=10.5,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(table.rows[0].cells[i], "0072BC")
        for r in table.rows[0].cells[i].paragraphs[0].runs:
            r.font.color.rgb = RGBColor(255, 255, 255)
    color_map = {"E06666": "F4CCCC", "FFD966": "FFF2CC", "93C47D": "D9EAD3"}
    for t in heatmap:
        # Re-calculamos el color de forma estricta para asegurar consistencia
        try:
            val = float(str(t.get("score", "0")).replace(",", "."))
        except Exception:
            val = 0.0

        strict_color = "E06666" if val < 2.6 else ("FFD966" if val < 3.4 else "93C47D")

        row = table.add_row()
        set_cell_text(
            row.cells[0],
            f"{t.get('id', '')}\n{t.get('name', '')}",
            bold=False,
            font_size=10.5,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        set_cell_text(
            row.cells[1],
            f"{t.get('score', '')}\n({t.get('band', '')})",
            align=WD_ALIGN_PARAGRAPH.CENTER,
            font_size=10.5,
            bold=False,
        )
        shade_cell(row.cells[1], color_map.get(strict_color, "FFFFFF"))
        
        # Recuperar texto
        tower_id = t.get('id', '')
        text_val = ""
        # tower_texts is now a list of dicts from pydantic dict dump or direct pydantic objects if we changed it.
        # Wait, the signature of GlobalReportPayload has tower_bottom_lines: list[TowerBottomLineItem]
        # But heatmap is raw dicts. We match by tower_id.
        for bottom_line_item in tower_texts:
            item_id = getattr(bottom_line_item, "id", None) or (bottom_line_item.get("id") if isinstance(bottom_line_item, dict) else None)
            if item_id == tower_id:
                text_val = getattr(bottom_line_item, "bottom_line", None) or (bottom_line_item.get("bottom_line") if isinstance(bottom_line_item, dict) else "")
                break
        
        if not text_val:
            text_val = t.get("executive_message", "")
            
        set_cell_text(
            row.cells[2],
            sanitize_client_name(clean_t_codes(str(text_val)), client_name),
            font_size=10.5,
        )
        # Apply base text color to cell content
        for p in row.cells[2].paragraphs:
            for r in p.runs:
                r.font.color.rgb = BASE_TEXT_COLOR
    autofit_table_to_contents(table)
    add_spacer(doc, 20)


def render_target_vision(doc, vision: TargetVisionDraft, client_name=""):
    BASE_TEXT_COLOR = RGBColor(46, 64, 77)  # #2E404D
    add_heading_paragraph(doc, "4. Visión de Estado Objetivo (To-Be)", level=1)

    table = doc.add_table(rows=2, cols=1)
    finalize_table(table)

    # Row 0: Header
    v_cell_header = table.rows[0].cells[0]
    set_cell_text(
        v_cell_header,
        "Propuesta de valor estratégica",
        bold=True,
        font_size=10.5,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    shade_cell(v_cell_header, "0072BC")
    for r in v_cell_header.paragraphs[0].runs:
        r.font.color.rgb = RGBColor(255, 255, 255)

    # Row 1: Body
    v_cell_body = table.rows[1].cells[0]
    shade_cell(v_cell_body, "F2F2F2")
    clear_paragraph(v_cell_body.paragraphs[0])
    p_body = v_cell_body.paragraphs[0]
    p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    prop = sanitize_client_name(
        clean_t_codes(vision.value_proposition), client_name
    )
    prop = prop[0].upper() + prop[1:] if prop else ""
    prop = prop.replace("─", "").replace("—", "").replace(";", ",")
    r_body = p_body.add_run(prop)
    r_body.font.color.rgb = BASE_TEXT_COLOR
    r_body.font.size = Pt(10.5)
    r_body.bold = False

    add_spacer(doc, 10)
    if vision.evolution_principles:
        add_heading_paragraph(doc, "Principios de Evolución de Madurez", level=2)
        p_list = [
            f"{p.principle}: {sanitize_client_name(p.description, client_name)}"
            for p in vision.evolution_principles
        ]
        add_smart_bullet_list(doc, p_list, color_rgb=BASE_TEXT_COLOR)
    add_heading_paragraph(doc, "Pilares Estratégicos Habilitadores", level=2)
    pillars = vision.strategic_pillars
    pillar_texts = []
    for p in pillars:
        p_name = sanitize_client_name(p.pillar, client_name)
        p_desc = sanitize_client_name(p.description, client_name)
        pillar_texts.append(f"{p_name}: {p_desc}")

    add_smart_bullet_list(
        doc, pillar_texts, color_rgb=BASE_TEXT_COLOR, bold_prefix=True
    )
    add_spacer(doc, 20)


def render_execution_roadmap(doc, roadmap: ExecutionRoadmapDraft, visuals: dict, client_dir, client_name=""):
    BASE_TEXT_COLOR = RGBColor(46, 64, 77)  # #2E404D
    add_heading_paragraph(
        doc, "5. Plan de Implementación y Horizontes Temporales", level=1
    )
    add_body_paragraph(
        doc,
        "La transformación tecnológica se articula en programas transversales ejecutados en cuatro horizontes temporales para asegurar la resiliencia y escalabilidad del negocio.",
        color_rgb=BASE_TEXT_COLOR,
    )
    table_p = doc.add_table(rows=1, cols=1)
    finalize_table(table_p)

    # Row 0: Header
    p_cell_header = table_p.rows[0].cells[0]
    set_cell_text(
        p_cell_header,
        "Programas transversales definidos",
        bold=True,
        font_size=10.5,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    shade_cell(p_cell_header, "0072BC")
    for r in p_cell_header.paragraphs[0].runs:
        r.font.color.rgb = RGBColor(255, 255, 255)

    # Program rows
    programs = roadmap.programs
    for p in programs:
        row = table_p.add_row()
        body_cell = row.cells[0]
        shade_cell(body_cell, "F2F2F2")

        p_bull = body_cell.paragraphs[0]
        clear_paragraph(p_bull)
        p_bull.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        try:
            p_bull.style = "List Bullet"
        except KeyError:
            p_bull.paragraph_format.left_indent = Pt(20)
            p_bull.paragraph_format.first_line_indent = Pt(-15)
            b_run = p_bull.add_run("• ")
            b_run.font.size = Pt(10.5)
            b_run.font.color.rgb = BASE_TEXT_COLOR

        p_bull.paragraph_format.space_before = Pt(6)
        p_bull.paragraph_format.space_after = Pt(6)

        program_name = clean_t_codes(p.name)
        program_desc = sanitize_client_name(
            clean_t_codes(p.description), client_name
        )

        r_name = p_bull.add_run(f"{program_name}: ")
        r_name.bold = True
        r_name.font.size = Pt(10.5)
        r_name.font.color.rgb = BASE_TEXT_COLOR

        r_desc = p_bull.add_run(program_desc)
        r_desc.bold = False
        r_desc.font.size = Pt(10.5)
        r_desc.font.color.rgb = BASE_TEXT_COLOR

    add_spacer(doc, 15)
    horizons = roadmap.horizons
    mapping = [
        ("Quick Wins (0-3 meses)", horizons.quick_wins_0_3_months),
        ("Año 1 (4-12 meses)", horizons.year_1_3_12_months),
        ("Año 2 (13-24 meses)", horizons.year_2_12_24_months),
        ("Año 3 (25-36 meses)", horizons.year_3_24_36_months),
    ]
    for title, initiatives in mapping:
        if not initiatives:
            continue
        add_heading_paragraph(doc, title, level=3)
        table = doc.add_table(rows=1, cols=5)
        finalize_table(table)
        headers = [
            "Programa",
            "Iniciativa",
            "Impacto / Business Case",
            "Inicio",
            "Dur.",
        ]
        for i, h in enumerate(headers):
            set_cell_text(
                table.rows[0].cells[i],
                h,
                bold=False,
                font_size=10.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            shade_cell(table.rows[0].cells[i], "0072BC")
            for r in table.rows[0].cells[i].paragraphs[0].runs:
                r.font.color.rgb = RGBColor(255, 255, 255)
        for init in initiatives:
            row = table.add_row()
            set_cell_text(
                row.cells[0],
                clean_t_codes(init.program),
                bold=False,
                font_size=10.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            set_cell_text(
                row.cells[1],
                sanitize_client_name(clean_t_codes(init.title), client_name),
                bold=False,
                font_size=10.5,
            )
            set_cell_text(
                row.cells[2],
                sanitize_client_name(
                    clean_t_codes(init.business_case), client_name
                ),
                font_size=10.5,
            )
            set_cell_text(
                row.cells[3],
                f"M{init.start_month}",
                font_size=10.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            set_cell_text(
                row.cells[4],
                f"{init.duration_months}m",
                font_size=10.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            # Apply base text color to non-header cells
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.font.color.rgb = BASE_TEXT_COLOR
        autofit_table_to_contents(table)
        add_spacer(doc, 15)


def render_executive_decisions(doc, decisions: ExecutiveDecisionsDraft, client_name=""):
    BASE_TEXT_COLOR = RGBColor(46, 64, 77)  # #2E404D
    add_heading_paragraph(doc, "6. Decisiones Ejecutivas Prioritarias", level=1)
    add_body_paragraph(
        doc,
        "Líneas de decisión requeridas por la Dirección para desbloquear la ejecución del programa y mitigar los riesgos identificados.",
        color_rgb=BASE_TEXT_COLOR,
    )
    table = doc.add_table(rows=1, cols=3)
    finalize_table(table)
    headers = ["Ámbito de Decisión", "Acción Requerida", "Impacto de Demora"]
    for i, h in enumerate(headers):
        set_cell_text(
            table.rows[0].cells[i],
            h,
            bold=True,
            font_size=10.5,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(table.rows[0].cells[i], "0072BC")
        for r in table.rows[0].cells[i].paragraphs[0].runs:
            r.font.color.rgb = RGBColor(255, 255, 255)
    for d in decisions.immediate_decisions:
        row = table.add_row()
        set_cell_text(
            row.cells[0],
            sanitize_client_name(
                clean_t_codes(d.decision_type), client_name
            ),
            bold=False,
            font_size=10.5,
        )
        set_cell_text(
            row.cells[1],
            sanitize_client_name(
                clean_t_codes(d.action_required), client_name
            ),
            font_size=10.5,
        )
        set_cell_text(
            row.cells[2],
            sanitize_client_name(
                clean_t_codes(d.impact_if_delayed), client_name
            ),
            font_size=10.5,
        )
        shade_cell(row.cells[2], "FFFFFF")
        # Apply base text color to non-header cells
        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.color.rgb = BASE_TEXT_COLOR
    autofit_table_to_contents(table)


from docx.oxml import OxmlElement, ns


def create_page_number_footer(section):
    # Activar pie de página diferente para la primera página
    section.different_first_page_header_footer = True

    # Asegurarnos de que el pie de página de la primera página (portada) esté vacío
    first_page_footer = section.first_page_footer
    for p in first_page_footer.paragraphs:
        clear_paragraph(p)

    # Configuramos el pie de página normal (el de las siguientes páginas)
    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Limpiar cualquier texto previo
    clear_paragraph(paragraph)

    def add_field(p, field_code):
        run = p.add_run()
        run.font.size = Pt(9)
        run.font.name = "Arial"
        run.font.color.rgb = RGBColor(127, 127, 127)

        fldChar1 = OxmlElement("w:fldChar")
        fldChar1.set(ns.qn("w:fldCharType"), "begin")
        run._r.append(fldChar1)

        instrText = OxmlElement("w:instrText")
        instrText.set(ns.qn("xml:space"), "preserve")
        instrText.text = field_code
        run._r.append(instrText)

        fldChar2 = OxmlElement("w:fldChar")
        fldChar2.set(ns.qn("w:fldCharType"), "separate")
        run._r.append(fldChar2)

        # Texto de respaldo
        t = OxmlElement("w:t")
        t.text = "0"
        run._r.append(t)

        fldChar3 = OxmlElement("w:fldChar")
        fldChar3.set(ns.qn("w:fldCharType"), "end")
        run._r.append(fldChar3)

    r = paragraph.add_run("Página ")
    r.font.size = Pt(9)
    r.font.name = "Arial"
    r.font.color.rgb = RGBColor(127, 127, 127)

    add_field(paragraph, "PAGE")

    r2 = paragraph.add_run(" de ")
    r2.font.size = Pt(9)
    r2.font.name = "Arial"
    r2.font.color.rgb = RGBColor(127, 127, 127)

    add_field(paragraph, "NUMPAGES")


def load_payload(payload_path: Path) -> GlobalReportPayload:
    payload_dict = load_json(payload_path)
    try:
        return GlobalReportPayload.model_validate(payload_dict)
    except ValidationError as e:
        print(f"❌ Error de validación Type-Safety en {payload_path}:")
        print(e)
        sys.exit(1)

def render_global_report(
    payload: GlobalReportPayload,
    template_path: Path,
    output_path: Path,
    client_dir: Path,
) -> Path:
    doc = Document(str(template_path))
    clear_document_body(doc)

    if doc.sections:
        create_page_number_footer(doc.sections[0])

    render_cover(doc, payload)
    client_name = payload.meta.client
    if payload.executive_summary:
        render_executive_summary(
            doc,
            payload.executive_summary,
            payload.heatmap,
            payload.visuals,
            client_dir,
            client_name=client_name,
        )
    if payload.burning_platform:
        render_burning_platform(
            doc, payload.burning_platform, client_name=client_name
        )
    if payload.tower_bottom_lines and payload.heatmap:
        render_tower_bottom_lines(
            doc, payload.heatmap, payload.tower_bottom_lines, client_name=client_name
        )
    if payload.target_vision:
        render_target_vision(doc, payload.target_vision, client_name=client_name)
    if payload.execution_roadmap:
        render_execution_roadmap(
            doc,
            payload.execution_roadmap,
            payload.visuals,
            client_dir,
            client_name=client_name,
        )
    if payload.executive_decisions:
        render_executive_decisions(
            doc, payload.executive_decisions, client_name=client_name
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print(f"Informe Global CIO-READY renderizado: {output_path}")
    return output_path


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) != 4:
        sys.exit(1)
    payload_path = Path((argv if argv is not None else sys.argv)[1])
    template_path = Path((argv if argv is not None else sys.argv)[2])
    output_path = Path((argv if argv is not None else sys.argv)[3])
    client_dir = payload_path.parent
    payload = load_payload(payload_path)
    render_global_report(payload, template_path, output_path, client_dir)


if __name__ == "__main__":
    main()
