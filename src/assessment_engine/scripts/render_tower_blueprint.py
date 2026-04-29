"""
Módulo render_tower_blueprint.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import json
import sys
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement, ns

from assessment_engine.schemas.blueprint import BlueprintPayload, PillarBlueprintDraft
from assessment_engine.scripts.lib.text_utils import clean_text_for_word
from assessment_engine.scripts.lib.contract_utils import robust_load_payload
from assessment_engine.scripts.render_tower_annex_from_template import (
    add_body_paragraph as _orig_add_body_paragraph,
    add_heading_paragraph,
    autofit_table_to_contents,
    clear_paragraph,
    finalize_table,
    set_cell_text,
    shade_cell,
)

BASE_TEXT_COLOR = RGBColor(46, 64, 77)
ROOT = Path(__file__).resolve().parents[3]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_client_intelligence(client_name: str):
    path = ROOT / "working" / client_name.lower().replace(" ", "_") / "client_intelligence.json"
    if path.exists():
        return load_json(path)
    return {}


def add_spacer(doc, points=12):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(points)


def clean_text_for_render(text):
    if isinstance(text, dict):
        if "name" in text and "description" in text:
            return f"{text['name']}: {text['description']}"
        return " - ".join(str(v) for v in text.values())
    return clean_text_for_word(text)


def add_body_paragraph(doc, text, color_rgb=BASE_TEXT_COLOR):
    text = clean_text_for_render(text)
    p = _orig_add_body_paragraph(
        doc, text, space_after=12, color_rgb=color_rgb, justify=True
    )
    return p


def add_bullet_p(container, text, color_rgb=BASE_TEXT_COLOR):
    text = clean_text_for_render(text)
    p = container.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(12)

    try:
        p.style = "List Bullet"
    except KeyError:
        p.paragraph_format.left_indent = Pt(20)
        p.paragraph_format.first_line_indent = Pt(-15)
        run_b = p.add_run("• ")
        run_b.font.size = Pt(10.5)
        if color_rgb:
            run_b.font.color.rgb = color_rgb

    if ":" in text:
        parts = text.split(":", 1)
        run_bold = p.add_run(parts[0] + ":")
        run_bold.bold = True
        run_bold.font.size = Pt(10.5)
        if color_rgb:
            run_bold.font.color.rgb = color_rgb

        run_normal = p.add_run(parts[1])
        run_normal.font.size = Pt(10.5)
        if color_rgb:
            run_normal.font.color.rgb = color_rgb
    else:
        run = p.add_run(text)
        run.font.size = Pt(10.5)
        if color_rgb:
            run.font.color.rgb = color_rgb
    return p


def create_page_number_footer(section):
    section.different_first_page_header_footer = True
    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
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


def render_cover(doc, payload: BlueprintPayload):
    meta = payload.document_meta
    doc.add_paragraph().paragraph_format.space_after = Pt(60)
    title_p = doc.add_paragraph()
    run = title_p.add_run(f"{meta.tower_name}\nInforme de Madurez Tecnológica")
    run.font.size = Pt(34)
    run.font.name = "Georgia"
    run.font.color.rgb = RGBColor(0, 114, 188)
    add_spacer(doc, 30)

    client_p = doc.add_paragraph()
    client_run = client_p.add_run(meta.client_name.upper())
    client_run.font.size = Pt(24)
    client_run.font.name = "Arial"
    client_run.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(100)
    v_p = doc.add_paragraph()
    v_text = f"Torre Técnica: {meta.tower_code}\nHorizonte: {meta.transformation_horizon}"
    v_run = v_p.add_run(v_text)
    v_run.font.size = Pt(14)
    v_run.font.name = "Arial"
    v_run.font.color.rgb = RGBColor(127, 127, 127)

    add_spacer(doc, 150)
    disc_p = doc.add_paragraph()
    disc_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r_dt = disc_p.add_run("Confidencialidad: ")
    r_dt.bold = True
    r_dt.font.size = Pt(8)
    r_dt.font.color.rgb = RGBColor(127, 127, 127)
    r_d = disc_p.add_run(
        "Este documento técnico es propiedad de NTT DATA y el cliente. Contiene información estratégica y de arquitectura sujeta a acuerdos de confidencialidad."
    )
    r_d.font.size = Pt(8)
    r_d.font.color.rgb = RGBColor(127, 127, 127)
    doc.add_page_break()


def render_snapshot_page(doc, payload: BlueprintPayload):
    meta = payload.document_meta
    snap = payload.executive_snapshot
    client_intelligence = load_client_intelligence(meta.client_name)

    client_name = meta.client_name.lower().replace(" ", "_")
    tower_id = meta.tower_code.lower()
    short_payload_path = (
        ROOT
        / "working"
        / client_name
        / tower_id.upper()
        / f"approved_annex_{tower_id}.template_payload.json"
    )

    # Calculate average score directly from the blueprint if we need to mock it,
    # but we will just set a default or use the short payload
    avg_score = 0.0
    # Current Blueprint analysis doesn't carry scores inside Pydantic PillarBlueprintDraft yet, 
    # but let's default it or read from the short payload.
    global_score_val = "N/A"
    global_band_val = "N/A"
    target_score_val = "N/A"

    if short_payload_path.exists():
        short_data = load_json(short_payload_path)
        exec_sum = short_data.get("executive_summary", {})
        global_score_val = exec_sum.get("global_score", global_score_val)
        global_band_val = exec_sum.get("global_band", global_band_val)
        target_score_val = exec_sum.get("target_maturity", target_score_val)

    add_heading_paragraph(doc, "1. Resumen ejecutivo", level=1)

    table = doc.add_table(rows=2, cols=3)
    finalize_table(table)
    headers = ["SCORE ACTUAL", "NIVEL DE MADUREZ", "MADUREZ OBJETIVO"]
    values = [global_score_val, global_band_val, target_score_val]

    for i, h in enumerate(headers):
        set_cell_text(
            table.rows[0].cells[i],
            h,
            bold=True,
            font_size=10,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(table.rows[0].cells[i], "0072BC")
        for r in table.rows[0].cells[i].paragraphs[0].runs:
            r.font.color.rgb = RGBColor(255, 255, 255)
        set_cell_text(
            table.rows[1].cells[i],
            values[i],
            font_size=14,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )

    table.autofit = False
    tbl = table._tbl
    tblPr = tbl.tblPr
    if tblPr is not None:
        tblW = tblPr.xpath("w:tblW")
        if not tblW:
            tblW = OxmlElement("w:tblW")
            tblPr.append(tblW)
        else:
            tblW = tblW[0]
        tblW.set(ns.qn("w:type"), "pct")
        tblW.set(ns.qn("w:w"), "5000")

    add_spacer(doc, 15)

    add_body_paragraph(doc, snap.bottom_line, color_rgb=BASE_TEXT_COLOR)

    business_angles = []
    ceo_agenda = clean_text_for_render(client_intelligence.get("ceo_agenda", ""))
    if ceo_agenda:
        business_angles.append(
            "Agenda de negocio prioritaria: " + ceo_agenda
        )
    regulatory = client_intelligence.get("regulatory_frameworks", []) or []
    if regulatory:
        business_angles.append(
            "Presión regulatoria material: " + ", ".join(regulatory)
        )
    drivers = client_intelligence.get("technological_drivers", []) or []
    for text in drivers:
        lowered = str(text).lower()
        if any(token in lowered for token in ["adquis", "m&a", "expansi", "ia", "pacient", "eficien"]):
            business_angles.append(clean_text_for_render(text))
    if business_angles:
        add_heading_paragraph(doc, "Por qué importa al negocio", level=2)
        for item in business_angles[:4]:
            add_bullet_p(doc, item)

    if snap.structural_risks:
        add_heading_paragraph(doc, "Riesgos de negocio más materiales", level=2)
        for r_risk in snap.structural_risks:
            add_bullet_p(doc, r_risk)

    add_heading_paragraph(doc, "Coste de Inacción (Do Nothing)", level=2)
    add_body_paragraph(
        doc, snap.cost_of_inaction, color_rgb=BASE_TEXT_COLOR
    )

    if snap.business_impact:
        add_heading_paragraph(doc, "Impacto Esperado en Negocio", level=2)
        add_body_paragraph(
            doc, snap.business_impact, color_rgb=BASE_TEXT_COLOR
        )

    if snap.operational_benefits:
        add_heading_paragraph(doc, "Beneficios Operativos Target", level=2)
        for ob in snap.operational_benefits:
            add_bullet_p(doc, ob)

    if snap.transformation_complexity:
        add_heading_paragraph(doc, "Complejidad de la Transformación", level=2)
        add_body_paragraph(
            doc, snap.transformation_complexity, color_rgb=BASE_TEXT_COLOR
        )

    add_heading_paragraph(doc, "Decisiones prioritarias", level=2)
    for dec in snap.decisions:
        add_bullet_p(doc, dec)


def render_cross_capabilities_analysis(doc, payload: BlueprintPayload):
    cca = payload.cross_capabilities_analysis
    if not cca:
        return

    add_heading_paragraph(doc, "Análisis Transversal de Capacidades", level=1)

    add_heading_paragraph(doc, "El Paradigma de Transformación", level=2)
    add_body_paragraph(
        doc, cca.transformation_paradigm, color_rgb=BASE_TEXT_COLOR
    )

    add_heading_paragraph(doc, "Deuda Técnica Crítica", level=2)
    add_body_paragraph(
        doc, cca.critical_technical_debt, color_rgb=BASE_TEXT_COLOR
    )

    add_heading_paragraph(doc, "Patrones Comunes de Deficiencia", level=2)
    for p_def in cca.common_deficiency_patterns:
        add_bullet_p(doc, p_def)


def render_pilar_detail(doc, pilar: PillarBlueprintDraft):

    add_heading_paragraph(doc, f"Capacidad: {pilar.pilar_name}", level=1)

    add_heading_paragraph(doc, "A. Health Check Técnico (AS-IS)", level=2)
    table = doc.add_table(rows=1, cols=3)
    finalize_table(table)
    headers = ["Capacidad Técnica", "Hallazgo / Evidencia", "Riesgo de Negocio"]
    for i, h in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], h, bold=True, font_size=10)
        shade_cell(table.rows[0].cells[i], "D9EAF7")

    for row_data in pilar.health_check_asis:
        row = table.add_row()
        set_cell_text(row.cells[0], row_data.target_state, bold=True, font_size=10)
        set_cell_text(row.cells[1], row_data.risk_observed, font_size=10)
        set_cell_text(row.cells[2], row_data.impact, font_size=10)
        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.color.rgb = BASE_TEXT_COLOR
    autofit_table_to_contents(table)
    add_spacer(doc, 10)

    add_heading_paragraph(doc, "B. Arquitectura Objetivo (TO-BE)", level=2)
    add_body_paragraph(
        doc,
        pilar.target_architecture_tobe.vision,
        color_rgb=BASE_TEXT_COLOR,
    )
    p_pr = doc.add_paragraph()
    r_pr = p_pr.add_run("Principios de Diseño:")
    r_pr.bold = True
    r_pr.font.size = Pt(10)
    r_pr.font.color.rgb = BASE_TEXT_COLOR
    for pr in pilar.target_architecture_tobe.design_principles:
        add_bullet_p(doc, pr)

    add_heading_paragraph(doc, "C. Transformation Backlog (Iniciativas TO-DO)", level=2)
    for proj in pilar.projects_todo:
        p_table = doc.add_table(rows=5, cols=2)
        finalize_table(p_table)
        merged = p_table.rows[0].cells[0].merge(p_table.rows[0].cells[1])
        set_cell_text(merged, proj.initiative.upper(), bold=True, font_size=11)
        shade_cell(merged, "0072BC")
        for r in merged.paragraphs[0].runs:
            r.font.color.rgb = RGBColor(255, 255, 255)

        proj_rows = [
            ("Business Rationale", proj.expected_outcome),
            ("Objetivo Técnico", proj.objective),
            (
                "Entregables (DoD)",
                "\n".join([f"• {d}" for d in proj.deliverables]),
            ),
            (
                "Sizing & Duración",
                f"Complejidad: {proj.sizing} | Estimación: {proj.duration}",
            ),
        ]
        for idx, (lab, val) in enumerate(proj_rows, 1):
            set_cell_text(p_table.rows[idx].cells[0], lab, bold=True, font_size=9)
            shade_cell(p_table.rows[idx].cells[0], "F2F2F2")
            set_cell_text(p_table.rows[idx].cells[1], val, font_size=9.5)
            for r in p_table.rows[idx].cells[1].paragraphs[0].runs:
                r.font.color.rgb = BASE_TEXT_COLOR
        autofit_table_to_contents(p_table)
        add_spacer(doc, 10)


def render_roadmap_page(doc, payload: BlueprintPayload):
    add_heading_paragraph(doc, "4. Strategic Roadmap & Dependencies", level=1)

    for wave in payload.roadmap:
        add_heading_paragraph(doc, wave.wave, level=2)
        for proj in wave.projects:
            add_bullet_p(doc, proj)

    add_heading_paragraph(doc, "Matriz de Sinergias Cruzadas", level=2)
    table = doc.add_table(rows=1, cols=3)
    finalize_table(table)
    headers = ["Iniciativa", "Dependencia / Habilita a", "Razón Técnica"]
    for i, h in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], h, bold=True, font_size=10)
        shade_cell(table.rows[0].cells[i], "D9EAF7")

    for dep in payload.external_dependencies:
        row = table.add_row()
        set_cell_text(row.cells[0], dep.project, bold=True, font_size=9.5)
        set_cell_text(row.cells[1], dep.depends_on, font_size=9.5)
        set_cell_text(row.cells[2], dep.reason, font_size=9.5)
        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.color.rgb = BASE_TEXT_COLOR
    autofit_table_to_contents(table)


def render_maturity_profile(doc, payload: BlueprintPayload):
    meta = payload.document_meta
    client_name = meta.client_name.lower().replace(" ", "_")
    tower_id = meta.tower_code.lower()

    # Buscar el payload del informe corto para extraer el perfil detallado
    short_payload_path = (
        ROOT
        / "working"
        / client_name
        / tower_id.upper()
        / f"approved_annex_{tower_id}.template_payload.json"
    )

    add_heading_paragraph(doc, "Perfil de madurez por pilar", level=1)

    if not short_payload_path.exists():
        add_body_paragraph(
            doc,
            "No se ha encontrado el perfil de madurez detallado para esta torre.",
            color_rgb=BASE_TEXT_COLOR,
        )
        return

    short_data = load_json(short_payload_path)
    profile = short_data.get("pillar_score_profile", {})
    asis = short_data.get("sections", {}).get("asis", {})

    add_body_paragraph(doc, profile.get("profile_intro", ""), color_rgb=BASE_TEXT_COLOR)
    p_note = add_body_paragraph(
        doc, profile.get("scoring_method_note", ""), color_rgb=BASE_TEXT_COLOR
    )
    if p_note:
        for r in p_note.runs:
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(127, 127, 127)

    radar_path = profile.get("radar_chart", "")
    if radar_path and Path(radar_path).exists():
        add_heading_paragraph(doc, "Gráfico radial", level=2)
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.add_run().add_picture(radar_path, width=Inches(4.35))
        add_spacer(doc, 10)

    add_heading_paragraph(doc, "Detalle compacto por pilar", level=2)
    pillars = profile.get("pillars", [])
    if pillars:
        table = doc.add_table(rows=1, cols=4)
        finalize_table(table)
        headers = ["Pilar", "Score", "Nivel", "Lectura ejecutiva"]
        for i, h in enumerate(headers):
            set_cell_text(table.rows[0].cells[i], h, bold=True, font_size=10)
            shade_cell(table.rows[0].cells[i], "D9EAF7")

        for pil in pillars:
            row = table.add_row()
            set_cell_text(
                row.cells[0], pil.get("pillar_label", ""), bold=True, font_size=9.5
            )
            set_cell_text(
                row.cells[1],
                pil.get("score_display", ""),
                font_size=9.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            set_cell_text(row.cells[2], pil.get("maturity_band", ""), font_size=9.5)
            set_cell_text(row.cells[3], pil.get("executive_reading", ""), font_size=9.5)
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.font.color.rgb = BASE_TEXT_COLOR
        autofit_table_to_contents(table)
        add_spacer(doc, 10)

    add_heading_paragraph(doc, "AS-IS resumido", level=2)
    add_body_paragraph(doc, asis.get("narrative", ""), color_rgb=BASE_TEXT_COLOR)

    strengths = asis.get("strengths", [])
    gaps = asis.get("gaps", [])
    if strengths or gaps:
        sg_table = doc.add_table(rows=2, cols=2)
        finalize_table(sg_table)
        set_cell_text(
            sg_table.rows[0].cells[0], "Fortalezas clave", bold=True, font_size=10
        )
        shade_cell(sg_table.rows[0].cells[0], "D9EAF7")
        set_cell_text(
            sg_table.rows[0].cells[1], "Brechas clave", bold=True, font_size=10
        )
        shade_cell(sg_table.rows[0].cells[1], "D9EAF7")

        cell_s = sg_table.rows[1].cells[0]
        cell_s.text = ""
        for s in strengths:
            p = cell_s.add_paragraph(f"• {s}")
            p.paragraph_format.left_indent = Pt(10)
            p.paragraph_format.first_line_indent = Pt(-10)
            p.paragraph_format.space_after = Pt(4)
            for r in p.runs:
                r.font.size = Pt(9.5)
                r.font.color.rgb = BASE_TEXT_COLOR

        cell_g = sg_table.rows[1].cells[1]
        cell_g.text = ""
        for g in gaps:
            p = cell_g.add_paragraph(f"• {g}")
            p.paragraph_format.left_indent = Pt(10)
            p.paragraph_format.first_line_indent = Pt(-10)
            p.paragraph_format.space_after = Pt(4)
            for r in p.runs:
                r.font.size = Pt(9.5)
                r.font.color.rgb = BASE_TEXT_COLOR

        autofit_table_to_contents(sg_table)
        add_spacer(doc, 10)

    impacts = asis.get("operational_impacts", [])
    if impacts:
        add_heading_paragraph(doc, "Implicaciones operativas clave", level=2)
        for imp in impacts:
            p = doc.add_paragraph(f"• {imp}")
            p.paragraph_format.left_indent = Pt(20)
            p.paragraph_format.first_line_indent = Pt(-10)
            for r in p.runs:
                r.font.color.rgb = BASE_TEXT_COLOR


def render_conclusion(doc, payload: BlueprintPayload):
    meta = payload.document_meta
    client_name = meta.client_name.lower().replace(" ", "_")
    tower_id = meta.tower_code.lower()

    short_payload_path = (
        ROOT
        / "working"
        / client_name
        / tower_id.upper()
        / f"approved_annex_{tower_id}.template_payload.json"
    )

    add_heading_paragraph(doc, "5. Conclusión", level=1)

    if not short_payload_path.exists():
        add_body_paragraph(
            doc,
            "No se ha encontrado información de conclusión para esta torre.",
            color_rgb=BASE_TEXT_COLOR,
        )
        return

    short_data = load_json(short_payload_path)
    conclusion = short_data.get("sections", {}).get("conclusion", {})

    if conclusion.get("final_assessment"):
        add_heading_paragraph(doc, "Evaluación final", level=2)
        add_body_paragraph(
            doc, conclusion.get("final_assessment"), color_rgb=BASE_TEXT_COLOR
        )

    if conclusion.get("executive_message"):
        add_heading_paragraph(doc, "Mensaje para el responsable técnico", level=2)
        add_body_paragraph(
            doc, conclusion.get("executive_message"), color_rgb=BASE_TEXT_COLOR
        )

    priority_areas = conclusion.get("priority_focus_areas", [])
    if priority_areas:
        add_heading_paragraph(doc, "Áreas de foco prioritarias", level=2)
        for area in priority_areas:
            p = doc.add_paragraph(f"• {area}")
            p.paragraph_format.left_indent = Pt(20)
            p.paragraph_format.first_line_indent = Pt(-10)
            for r in p.runs:
                r.font.color.rgb = BASE_TEXT_COLOR

    if conclusion.get("closing_statement"):
        add_heading_paragraph(doc, "Próximos pasos", level=2)
        add_body_paragraph(
            doc, conclusion.get("closing_statement"), color_rgb=BASE_TEXT_COLOR
        )


def trim_annex_payload_for_executive_blueprint(meta):
    client_name = meta.client_name.lower().replace(" ", "_")
    tower_id = meta.tower_code.lower()
    short_payload_path = (
        ROOT
        / "working"
        / client_name
        / tower_id.upper()
        / f"approved_annex_{tower_id}.template_payload.json"
    )
    if not short_payload_path.exists():
        return None
    return load_json(short_payload_path)


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) != 3:
        sys.exit(1)
    payload_path = Path((argv if argv is not None else sys.argv)[1])
    
    # 1. Cargamos y validamos el JSON de forma robusta
    payload = robust_load_payload(payload_path, BlueprintPayload, "Blueprint")
    payload_dict = payload.model_dump(by_alias=True)

    output_path = Path((argv if argv is not None else sys.argv)[2])
    template_path = (
        ROOT / "templates" / "Template_Documento_Anexos_Alpha_v06_Tower_Annex_v2_6.docx"
    )
    doc = Document(str(template_path))

    body = doc._body._element
    for child in list(body):
        if (
            child.tag
            != "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sectPr"
        ):
            body.remove(child)

    if doc.sections:
        create_page_number_footer(doc.sections[0])
        
    render_cover(doc, payload)
    render_snapshot_page(doc, payload)
    render_maturity_profile(doc, payload)
    render_cross_capabilities_analysis(doc, payload)
    
    for pilar in payload.pillars_analysis:
        render_pilar_detail(doc, pilar)
        
    render_roadmap_page(doc, payload)
    render_conclusion(doc, payload)
    
    doc.save(str(output_path))
    print(f"Blueprint de Torre renderizado: {output_path}")


if __name__ == "__main__":
    main()
