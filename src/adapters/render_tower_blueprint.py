"""
Módulo render_tower_blueprint.py.
Renderiza el blueprint DOCX de una torre a partir de su payload JSON.
"""

import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, ns
from docx.shared import Inches, Pt, RGBColor

from domain.maturity_band import (
    ANNEX_MATURITY_BANDS,
    resolve_maturity_band,
)
from domain.schemas.blueprint import BlueprintPayload, PillarBlueprintDraft
from infrastructure.client_intelligence import (
    load_client_intelligence_legacy_view,
)
from infrastructure.docx_render_utils import (
    add_body_paragraph as _orig_add_body_paragraph,
)
from infrastructure.docx_render_utils import (
    add_heading_paragraph,
    autofit_table_to_contents,
    clear_paragraph,
    finalize_table,
    set_cell_text,
    shade_cell,
)
from infrastructure.runtime_paths import (
    resolve_tower_annex_template_path,
)
from infrastructure.text_utils import clean_text_for_word

BASE_TEXT_COLOR = RGBColor(46, 64, 77)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TEMPLATE_PATH = resolve_tower_annex_template_path()


from typing import Any, cast


def load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


def add_spacer(doc, points=12) -> Any:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(points)


def clean_text_for_render(text) -> Any:
    if isinstance(text, dict):
        if "name" in text and "description" in text:
            return f"{text['name']}: {text['description']}"
        return " - ".join(str(v) for v in text.values())
    return clean_text_for_word(text)


def _safe_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).split()[0].replace(",", "."))
    except (TypeError, ValueError):
        return None


def _resolve_annex_band(value: object) -> str:
    score = _safe_float(value)
    if score is None:
        return ""
    return resolve_maturity_band(score, ANNEX_MATURITY_BANDS)["label"]


def add_body_paragraph(doc, text, color_rgb=BASE_TEXT_COLOR) -> Any:
    text = clean_text_for_render(text)
    return _orig_add_body_paragraph(
        doc,
        text,
        space_after=12,
        color_rgb=color_rgb,
        justify=True,
    )


def add_bullet_p(container, text, color_rgb=BASE_TEXT_COLOR) -> Any:
    text = clean_text_for_render(text)
    p = container.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(12)

    try:
        p.style = "List Bullet"
    except KeyError:
        p.paragraph_format.left_indent = Pt(20)
        p.paragraph_format.first_line_indent = Pt(-15)
        bullet = p.add_run("• ")
        bullet.font.size = Pt(10.5)
        if color_rgb:
            bullet.font.color.rgb = color_rgb

    if ":" in text:
        prefix, rest = text.split(":", 1)
        prefix_run = p.add_run(prefix + ":")
        prefix_run.bold = True
        prefix_run.font.size = Pt(10.5)
        if color_rgb:
            prefix_run.font.color.rgb = color_rgb

        rest_run = p.add_run(rest)
        rest_run.font.size = Pt(10.5)
        if color_rgb:
            rest_run.font.color.rgb = color_rgb
    else:
        run = p.add_run(text)
        run.font.size = Pt(10.5)
        if color_rgb:
            run.font.color.rgb = color_rgb
    return p


def create_page_number_footer(section) -> Any:
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
        fld_char_begin = OxmlElement("w:fldChar")
        fld_char_begin.set(ns.qn("w:fldCharType"), "begin")
        run._r.append(fld_char_begin)
        instr_text = OxmlElement("w:instrText")
        instr_text.set(ns.qn("xml:space"), "preserve")
        instr_text.text = field_code
        run._r.append(instr_text)
        fld_char_sep = OxmlElement("w:fldChar")
        fld_char_sep.set(ns.qn("w:fldCharType"), "separate")
        run._r.append(fld_char_sep)
        text = OxmlElement("w:t")
        text.text = "0"
        run._r.append(text)
        fld_char_end = OxmlElement("w:fldChar")
        fld_char_end.set(ns.qn("w:fldCharType"), "end")
        run._r.append(fld_char_end)

    prefix = paragraph.add_run("Página ")
    prefix.font.size = Pt(9)
    prefix.font.name = "Arial"
    prefix.font.color.rgb = RGBColor(127, 127, 127)
    add_field(paragraph, "PAGE")
    middle = paragraph.add_run(" de ")
    middle.font.size = Pt(9)
    middle.font.name = "Arial"
    middle.font.color.rgb = RGBColor(127, 127, 127)
    add_field(paragraph, "NUMPAGES")


def clear_document_body(doc) -> None:
    body = doc._body._element
    for child in list(body):
        if (
            child.tag
            != "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sectPr"
        ):
            body.remove(child)


def resolve_client_dir(payload_path: Path, payload_data: dict) -> Path:
    # Always trust the physical directory structure since payload_path is like working/redeia_v3/T2/payload.json
    return payload_path.parents[1]


def load_client_intelligence(client_dir: Path) -> dict:
    path = client_dir / "client_intelligence.json"
    return load_client_intelligence_legacy_view(path)


def load_annex_data(client_dir: Path, tower_code: str) -> dict:
    tower_dir = client_dir / tower_code.upper()
    path = tower_dir / f"approved_annex_{tower_code.lower()}.template_payload.json"
    if path.exists():
        return load_json(path)
    return {}


def _list_or_default(value, default=None) -> Any:
    if isinstance(value, list):
        return value
    return default or []


def _string_or_default(value, default="") -> Any:
    if isinstance(value, str):
        return value
    return default


def _derive_executive_snapshot(data: dict, annex_data: dict) -> dict:
    snapshot = data.get("executive_snapshot") or {}
    annex_summary = annex_data.get("executive_summary", {})
    annex_sections = annex_data.get("sections", {})
    risks = annex_sections.get("risks", {}).get("risks", [])
    todo_items = annex_sections.get("todo", {}).get("priority_initiatives", [])
    target_capabilities = annex_sections.get("tobe", {}).get("target_capabilities", [])

    if isinstance(annex_summary.get("summary_body"), list):
        summary_body = " ".join(str(x) for x in annex_summary.get("summary_body", []))
    else:
        summary_body = _string_or_default(annex_summary.get("summary_body"))

    return {
        "bottom_line": _string_or_default(snapshot.get("bottom_line"))
        or summary_body
        or _string_or_default(annex_summary.get("headline"))
        or "La torre requiere una transformación priorizada para reducir riesgo y habilitar el negocio.",
        "decisions": _list_or_default(snapshot.get("decisions"))
        or [
            clean_text_for_render(item.get("initiative", ""))
            for item in todo_items[:4]
            if item.get("initiative")
        ]
        or ["Validar el backlog priorizado y su secuencia de ejecución."],
        "cost_of_inaction": _string_or_default(snapshot.get("cost_of_inaction"))
        or "Mantener el estado actual prolonga el riesgo operativo, la deuda técnica y la incapacidad de escalar con control.",
        "structural_risks": _list_or_default(snapshot.get("structural_risks"))
        or [
            clean_text_for_render(item.get("risk", ""))
            for item in risks[:4]
            if item.get("risk")
        ],
        "business_impact": _string_or_default(snapshot.get("business_impact"))
        or "La modernización de la torre reduce exposición al riesgo y mejora la capacidad de ejecución del negocio.",
        "operational_benefits": _list_or_default(snapshot.get("operational_benefits"))
        or [clean_text_for_render(item) for item in target_capabilities[:4]],
        "transformation_complexity": _string_or_default(
            snapshot.get("transformation_complexity")
        )
        or "La transformación exige coordinación de arquitectura, operación y gobierno, pero es abordable por fases.",
    }


def _derive_cross_capabilities_analysis(data: dict) -> dict:
    cca = data.get("cross_capabilities_analysis") or {}
    pillars = _list_or_default(data.get("pillars_analysis"))
    low_score_pillars = [
        p.get("pilar_name", "") for p in pillars if float(p.get("score", 0) or 0) < 3.0
    ]

    if cca:
        return {
            "common_deficiency_patterns": _list_or_default(
                cca.get("common_deficiency_patterns")
            ),
            "transformation_paradigm": _string_or_default(
                cca.get("transformation_paradigm")
            )
            or "La torre requiere una evolución por dominios, priorizando estabilización, gobierno y posterior industrialización.",
            "critical_technical_debt": _string_or_default(
                cca.get("critical_technical_debt")
            )
            or "La deuda técnica limita la resiliencia y la capacidad de operar con consistencia.",
        }

    deficiency_patterns = []
    if low_score_pillars:
        deficiency_patterns.append(
            "Las mayores brechas se concentran en: "
            + ", ".join(low_score_pillars)
            + "."
        )

    return {
        "common_deficiency_patterns": deficiency_patterns
        or [
            "Persisten carencias repetidas en estandarización, automatización y gobierno técnico."
        ],
        "transformation_paradigm": "La transformación debe ejecutarse de forma incremental, combinando quick wins con capacidades fundacionales de largo recorrido.",
        "critical_technical_debt": "La deuda técnica acumulada incrementa el riesgo operativo y reduce la velocidad de adopción de nuevos servicios.",
    }


def _derive_roadmap(data: dict) -> list[dict]:
    roadmap = _list_or_default(data.get("roadmap"))
    if roadmap:
        return roadmap

    initiatives = []
    for pillar in _list_or_default(data.get("pillars_analysis")):
        for project in _list_or_default(pillar.get("projects_todo")):
            name = clean_text_for_render(project.get("name", ""))
            sizing = str(project.get("sizing", "")).lower()
            initiatives.append((name, sizing))

    quick_wins = [name for name, sizing in initiatives if name and "s" in sizing][:4]
    medium_term = [name for name, sizing in initiatives if name and "m" in sizing][:4]
    strategic = [name for name, sizing in initiatives if name and "l" in sizing][:4]

    fallback = [name for name, _ in initiatives[:4] if name]

    waves = [
        {"wave": "Wave 1", "projects": quick_wins or fallback[:2]},
        {"wave": "Wave 2", "projects": medium_term or fallback[2:4]},
        {"wave": "Wave 3", "projects": strategic or fallback[:2]},
    ]
    return [wave for wave in waves if wave["projects"]]


def normalize_blueprint_payload_dict(data: dict, annex_data: dict) -> dict:
    normalized = dict(data)
    normalized["executive_snapshot"] = _derive_executive_snapshot(data, annex_data)
    normalized["cross_capabilities_analysis"] = _derive_cross_capabilities_analysis(
        data
    )
    normalized["roadmap"] = _derive_roadmap(data)
    normalized["external_dependencies"] = _list_or_default(
        data.get("external_dependencies")
    )
    normalized["pillars_analysis"] = _list_or_default(data.get("pillars_analysis"))
    return normalized


def load_payload(
    payload_path: Path, annex_data: dict | None = None
) -> BlueprintPayload:
    raw_data = load_json(payload_path)
    normalized_data = normalize_blueprint_payload_dict(raw_data, annex_data or {})
    return BlueprintPayload.model_validate(normalized_data)


def render_cover(doc, payload: BlueprintPayload) -> Any:
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
    version_p = doc.add_paragraph()
    version_text = (
        f"Torre Técnica: {meta.tower_code}\nHorizonte: {meta.transformation_horizon}"
    )
    version_run = version_p.add_run(version_text)
    version_run.font.size = Pt(14)
    version_run.font.name = "Arial"
    version_run.font.color.rgb = RGBColor(127, 127, 127)

    add_spacer(doc, 150)
    disclaimer = doc.add_paragraph()
    disclaimer.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    title_run = disclaimer.add_run("Confidencialidad: ")
    title_run.bold = True
    title_run.font.size = Pt(8)
    title_run.font.color.rgb = RGBColor(127, 127, 127)
    text_run = disclaimer.add_run(
        "Este documento técnico es propiedad de NTT DATA y el cliente. Contiene "
        "información estratégica y de arquitectura sujeta a acuerdos de confidencialidad."
    )
    text_run.font.size = Pt(8)
    text_run.font.color.rgb = RGBColor(127, 127, 127)
    doc.add_page_break()


def render_snapshot_page(
    doc,
    payload: BlueprintPayload,
    client_intelligence: dict,
    annex_data: dict,
):
    snap = payload.executive_snapshot
    exec_sum = annex_data.get("executive_summary", {})
    global_score_val = exec_sum.get("global_score", "N/A")
    global_band_val = exec_sum.get("global_band") or _resolve_annex_band(
        global_score_val
    )
    target_score_val = exec_sum.get("target_maturity", "N/A")

    add_heading_paragraph(doc, "1. Executive Snapshot (Resumen ejecutivo)", level=1)

    table = doc.add_table(rows=2, cols=3)
    finalize_table(table)
    headers = ["SCORE ACTUAL", "NIVEL DE MADUREZ", "MADUREZ OBJETIVO"]
    values = [global_score_val, global_band_val or "N/A", target_score_val]

    for i, header in enumerate(headers):
        set_cell_text(
            table.rows[0].cells[i],
            header,
            bold=True,
            font_size=10,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(table.rows[0].cells[i], "0072BC")
        for run in table.rows[0].cells[i].paragraphs[0].runs:
            run.font.color.rgb = RGBColor(255, 255, 255)
        set_cell_text(
            table.rows[1].cells[i],
            values[i],
            font_size=14,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )

    table.autofit = False
    tbl_pr = table._tbl.tblPr
    if tbl_pr is not None:
        widths = tbl_pr.xpath("w:tblW")
        tbl_w = widths[0] if widths else OxmlElement("w:tblW")
        if not widths:
            tbl_pr.append(tbl_w)
        tbl_w.set(ns.qn("w:type"), "pct")
        tbl_w.set(ns.qn("w:w"), "5000")

    add_spacer(doc, 15)
    add_body_paragraph(doc, snap.bottom_line, color_rgb=BASE_TEXT_COLOR)

    business_angles = []
    ceo_agenda = clean_text_for_render(client_intelligence.get("ceo_agenda", ""))
    if ceo_agenda:
        business_angles.append("Agenda de negocio prioritaria: " + ceo_agenda)
    regulatory = client_intelligence.get("regulatory_frameworks", []) or []
    if regulatory:
        business_angles.append(
            "Presión regulatoria material: " + ", ".join(str(x) for x in regulatory)
        )
    drivers = client_intelligence.get("technological_drivers", []) or []
    for text in drivers:
        lowered = str(text).lower()
        if any(
            token in lowered
            for token in ["adquis", "m&a", "expansi", "ia", "pacient", "eficien"]
        ):
            business_angles.append(clean_text_for_render(text))

    if not business_angles:
        business_angles.append(
            "La transformación tecnológica propuesta asegura la competitividad, fortalece la resiliencia operativa y garantiza el cumplimiento normativo."
        )

    add_heading_paragraph(doc, "Por qué importa al negocio", level=2)
    for item in business_angles[:4]:
        add_bullet_p(doc, item)

    if snap.structural_risks:
        add_heading_paragraph(doc, "Riesgos de negocio más materiales", level=2)
        for risk in snap.structural_risks:
            add_bullet_p(doc, risk)

    add_heading_paragraph(doc, "Coste de Inacción (Do Nothing)", level=2)
    add_body_paragraph(doc, snap.cost_of_inaction, color_rgb=BASE_TEXT_COLOR)

    if snap.business_impact:
        add_heading_paragraph(doc, "Impacto Esperado en Negocio", level=2)
        add_body_paragraph(doc, snap.business_impact, color_rgb=BASE_TEXT_COLOR)

    if snap.operational_benefits:
        add_heading_paragraph(doc, "Beneficios Operativos Target", level=2)
        for benefit in snap.operational_benefits:
            add_bullet_p(doc, benefit)

    if snap.transformation_complexity:
        add_heading_paragraph(doc, "Complejidad de la Transformación", level=2)
        add_body_paragraph(
            doc,
            snap.transformation_complexity,
            color_rgb=BASE_TEXT_COLOR,
        )

    add_heading_paragraph(doc, "Decisiones prioritarias", level=2)
    for decision in snap.decisions:
        add_bullet_p(doc, decision)


def render_cross_capabilities_analysis(doc, payload: BlueprintPayload) -> Any:
    cca = payload.cross_capabilities_analysis
    if not cca:
        return

    add_heading_paragraph(doc, "Análisis Transversal de Capacidades", level=1)
    add_heading_paragraph(doc, "El Paradigma de Transformación", level=2)
    add_body_paragraph(doc, cca.transformation_paradigm, color_rgb=BASE_TEXT_COLOR)

    add_heading_paragraph(doc, "Deuda Técnica Crítica", level=2)
    add_body_paragraph(doc, cca.critical_technical_debt, color_rgb=BASE_TEXT_COLOR)

    add_heading_paragraph(doc, "Patrones Comunes de Deficiencia", level=2)
    for item in cca.common_deficiency_patterns:
        add_bullet_p(doc, item)


def render_consolidated_asis(doc, payload: BlueprintPayload) -> Any:
    add_heading_paragraph(doc, "Diagnóstico Tecnológico Consolidado (AS-IS)", level=1)
    
    for pilar in payload.pillars_analysis:
        add_heading_paragraph(doc, f"Capacidad: {pilar.pilar_name}", level=2)
        
        table = doc.add_table(rows=1, cols=3)
        finalize_table(table)
        headers = ["Capacidad Técnica", "Hallazgo / Evidencia", "Riesgo de Negocio"]
        for i, header in enumerate(headers):
            set_cell_text(table.rows[0].cells[i], header, bold=True, font_size=10)
            shade_cell(table.rows[0].cells[i], "D9EAF7")

        for row_data in pilar.health_check_asis:
            row = table.add_row()
            set_cell_text(row.cells[0], row_data.target_state, bold=True, font_size=10)
            set_cell_text(row.cells[1], row_data.risk_observed, font_size=10)
            
            # Risk coloring logic
            impact_text = row_data.impact
            impact_lower = impact_text.lower()
            if any(k in impact_lower for k in ["crítico", "alto", "crítica", "alta", "severo", "material"]):
                shade_cell(row.cells[2], "FADBD8") # Light red
            elif any(k in impact_lower for k in ["medio", "moderado"]):
                shade_cell(row.cells[2], "FCF3CF") # Light amber
                
            set_cell_text(row.cells[2], impact_text, font_size=10)
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.color.rgb = BASE_TEXT_COLOR
        autofit_table_to_contents(table)
        add_spacer(doc, 10)


def render_fair_risk_heatmap(doc, payload: BlueprintPayload) -> Any:
    add_heading_paragraph(doc, "Matriz de Riesgo Cuantitativa (FAIR)", level=1)
    add_body_paragraph(
        doc,
        "La siguiente matriz consolida la expectativa de pérdida anualizada (ALE) de las vulnerabilidades detectadas en el estado actual, basada en factores de frecuencia de la amenaza (TEF) y magnitud de pérdida (LM). "
        "Nota: La métrica ALE representa la exposición aislada de cada riesgo. Varios riesgos pueden compartir la misma causa raíz, por lo que su sumatorio refleja el volumen total de amenaza bajo gestión, no un impacto simultáneo garantizado.",
        color_rgb=BASE_TEXT_COLOR
    )
    
    # 5x5 Matrix initialization: rows are TEF (Frequency, 5 to 1), cols are LM (Magnitude, 1 to 5)
    matrix = {r: {c: [] for c in range(1, 6)} for r in range(5, 0, -1)}
    
    has_fair_data = False
    risk_details = []
    risk_counter = 1
    
    for pilar in payload.pillars_analysis:
        for finding in pilar.health_check_asis:
            tef = getattr(finding, "threat_event_frequency", 0)
            lm = getattr(finding, "loss_magnitude", 0)
            ale = getattr(finding, "fair_ale_score", 0.0)
            if tef > 0 and lm > 0:
                has_fair_data = True
                r_id = f"R{risk_counter:02d}"
                risk_counter += 1
                matrix[tef][lm].append(r_id)
                risk_details.append({
                    "id": r_id,
                    "pilar": pilar.pilar_name,
                    "finding": finding.risk_observed,
                    "target_state": finding.target_state,
                    "tef": tef,
                    "lm": lm,
                    "ale": ale,
                    "risk_score": tef * lm
                })
                
    if not has_fair_data:
        add_body_paragraph(doc, "No hay datos cuantitativos FAIR suficientes para renderizar el mapa de calor.", color_rgb=BASE_TEXT_COLOR)
        return
        
    table = doc.add_table(rows=6, cols=6)
    finalize_table(table)
    
    # Headers
    set_cell_text(table.rows[0].cells[0], "Frecuencia \\ Impacto", bold=True, font_size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    for c in range(1, 6):
        set_cell_text(table.rows[0].cells[c], f"Nivel {c}", bold=True, font_size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        shade_cell(table.rows[0].cells[c], "F2F2F2")
        
    for r_idx, r in enumerate(range(5, 0, -1), 1):
        set_cell_text(table.rows[r_idx].cells[0], f"Freq {r}", bold=True, font_size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        shade_cell(table.rows[r_idx].cells[0], "F2F2F2")
        for c in range(1, 6):
            cell = table.rows[r_idx].cells[c]
            risk_score = r * c
            color = "D9F2D9" # Green
            if risk_score >= 20: color = "C00000" # Dark Red
            elif risk_score >= 15: color = "FF0000" # Red
            elif risk_score >= 10: color = "FFC000" # Amber
            elif risk_score >= 5: color = "FFFF00" # Yellow
            
            shade_cell(cell, color)
            
            items = matrix[r][c]
            if items:
                set_cell_text(cell, ", ".join(items), font_size=9, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
                if risk_score >= 15: # Red or Dark Red, white text
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.color.rgb = RGBColor(255, 255, 255)
            else:
                set_cell_text(cell, "", font_size=8)

    autofit_table_to_contents(table)
    add_spacer(doc, 15)

    # Detailed Risk Table
    # Sort by ALE descending
    risk_details.sort(key=lambda x: x["ale"], reverse=True)
    
    add_heading_paragraph(doc, "Detalle de Exposición al Riesgo (FAIR)", level=2)
    risk_table = doc.add_table(rows=1, cols=5)
    finalize_table(risk_table)
    headers = ["ID", "Dominio", "Hallazgo / Brecha", "Coordenadas (Freq x Imp)", "Exposición de Riesgo (ALE)"]
    for i, header in enumerate(headers):
        set_cell_text(risk_table.rows[0].cells[i], header, bold=True, font_size=9)
        shade_cell(risk_table.rows[0].cells[i], "D9EAF7")
        
    for detail in risk_details:
        row = risk_table.add_row()
        set_cell_text(row.cells[0], detail["id"], font_size=8, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_text(row.cells[1], detail["pilar"], font_size=8)
        set_cell_text(row.cells[2], f"{detail['target_state']}: {detail['finding']}", font_size=8)
        set_cell_text(row.cells[3], f"TEF: {detail['tef']} | LM: {detail['lm']}", font_size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        
        # Risk level color for ALE
        risk_score = detail["risk_score"]
        color = "D9F2D9" # Green
        if risk_score >= 20: color = "C00000" # Dark Red
        elif risk_score >= 15: color = "FF0000" # Red
        elif risk_score >= 10: color = "FFC000" # Amber
        elif risk_score >= 5: color = "FFFF00" # Yellow
        
        ale_val = detail["ale"]
        set_cell_text(row.cells[4], f"{ale_val:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), font_size=8, align=WD_ALIGN_PARAGRAPH.RIGHT)
        shade_cell(row.cells[4], color)
        if risk_score >= 15: # Red or Dark Red, white text
            for paragraph in row.cells[4].paragraphs:
                for run in paragraph.runs:
                    run.font.color.rgb = RGBColor(255, 255, 255)
                            
    autofit_table_to_contents(risk_table)
    add_spacer(doc, 15)

def render_consolidated_tobe(doc, payload: BlueprintPayload) -> Any:
    add_heading_paragraph(doc, "Arquitectura Objetivo y Visión Soberana (TO-BE)", level=1)
    
    if payload.cross_capabilities_analysis:
        add_body_paragraph(doc, payload.cross_capabilities_analysis.transformation_paradigm, color_rgb=BASE_TEXT_COLOR)

    add_body_paragraph(
        doc,
        "La arquitectura objetivo propuesta se rige por un modelo soberano agnóstico, evitando el vendor lock-in e integrando las infraestructuras críticas con los ecosistemas Cloud de mayor innovación tecnológica (e.g. AWS).",
        color_rgb=BASE_TEXT_COLOR
    )
    
    if hasattr(payload, "design_principles") and payload.design_principles:
        add_heading_paragraph(doc, "Principios de Diseño Unificados", level=2)
        for principle in payload.design_principles:
            add_bullet_p(doc, principle)


def render_deep_project_charters(doc, payload: BlueprintPayload) -> Any:
    doc.add_page_break()
    add_heading_paragraph(doc, "Anexo Técnico: Fichas Profundas de Proyectos (Charters)", level=1)
    
    # 1. Extract and group all projects by transformation typology
    from collections import defaultdict
    grouped_projects = defaultdict(list)
    
    for pilar in payload.pillars_analysis:
        for project in pilar.projects_todo:
            typology = getattr(project, "transformation_typology", "Iniciativas Core")
            grouped_projects[typology].append((pilar.pilar_name, project))
            
    # 2. Render groups
    project_idx = 1
    for typology, projects_in_group in grouped_projects.items():
        add_heading_paragraph(doc, f"Vector de Transformación: {typology}", level=2)
        add_spacer(doc, 10)
        
        for pilar_name, project in projects_in_group:
            add_heading_paragraph(doc, f"Iniciativa {project_idx}: {project.initiative}", level=3)
            
            deps = [d.depends_on for d in payload.external_dependencies if d.project == project.initiative]
            deps_text = " • ".join(deps) if deps else "Independiente (Habilitador Fase 0)"

            # Resolve mitigated risk text
            mitigated_risk_text = "N/A"
            if getattr(project, "mitigates_risk_id", None):
                for p_ana in payload.pillars_analysis:
                    for hc in p_ana.health_check_asis:
                        if hc.node_id == project.mitigates_risk_id:
                            mitigated_risk_text = f"[{hc.target_state}] {hc.risk_observed}"
                            break

            # Resolve FinOps (Hiding internal margins from the client)
            capex = getattr(project, "capex_estimate", "N/A")
            opex = getattr(project, "opex_estimate", "N/A")
            
            # Sanitize OPEX to remove internal margin calculations if present
            # We want to keep just the final sell price
            clean_opex = opex
            if "(Margen" in opex:
                clean_opex = opex.split("(Margen")[0].strip()
            
            finops_text = f"Inversión de Implantación: {clean_opex}\nInversión de Licencias/Hardware: {capex}"

            # Resolve WBS
            wbs_items = getattr(project, "wbs_breakdown", [])
            wbs_text = "Desglose no disponible."
            if wbs_items:
                try:
                    wbs_text = "\n".join([f"• {w.task_name} (Perfil: {w.required_profile})" for w in wbs_items])
                except Exception:
                    # In case of parsing dicts vs objects
                    wbs_text = "\n".join([f"• {w.get('task_name')} (Perfil: {w.get('required_profile')})" for w in wbs_items if isinstance(w, dict)])

            # Resolve new fields
            proj_desc = getattr(project, "project_description", "N/A") or "N/A"
            smart_obj = getattr(project, "smart_objectives", "N/A") or "N/A"
            in_scope_list = getattr(project, "in_scope", []) or []
            out_scope_list = getattr(project, "out_of_scope", []) or []
            gov_roles_list = getattr(project, "governance_roles", []) or []
            crit_risks_list = getattr(project, "critical_risks", []) or []
            
            in_scope = "\n".join([f"• {item}" for item in in_scope_list]) or "N/A"
            out_scope = "\n".join([f"• {item}" for item in out_scope_list]) or "N/A"
            gov_roles = "\n".join([f"• {item}" for item in gov_roles_list]) or "N/A"
            crit_risks = "\n".join([f"• {item}" for item in crit_risks_list]) or "N/A"
            roi_just = getattr(project, "roi_justification", "N/A") or "N/A"

            rows = [
                ("Dominio Arquitectónico", pilar_name),
                ("Descripción Ejecutiva", proj_desc),
                ("Objetivo SMART", smart_obj),
                ("Riesgo AS-IS Mitigado (Trazabilidad)", mitigated_risk_text),
                ("Alcance (In-Scope)", in_scope),
                ("Fuera de Alcance (Out-of-Scope)", out_scope),
                ("Dependencias Técnicas (Predecesores)", deps_text),
                (
                    "Entregables Técnicos Duros (DoD)",
                    "\n".join([f"• {item}" for item in project.deliverables]),
                ),
                (
                    "Work Breakdown Structure (LLD Fases)",
                    wbs_text
                ),
                (
                    "Sizing & Cronograma",
                    f"Complejidad Técnica: {project.sizing}\nHorizonte de Ejecución: {project.duration}",
                ),
                ("Estimación FinOps & TCO (3 Años)", finops_text),
                ("Justificación de ROI & Valor", roi_just),
                ("Perfiles y Gobernanza (RACI)", gov_roles),
                ("Riesgos de Ejecución y Mitigación", crit_risks),
            ]
            
            project_table = doc.add_table(rows=len(rows)+1, cols=2)
            finalize_table(project_table)
            
            merged = project_table.rows[0].cells[0].merge(project_table.rows[0].cells[1])
            set_cell_text(merged, "FICHA TÉCNICA DE PROYECTO DE INGENIERÍA", bold=True, font_size=11)
            shade_cell(merged, "0072BC")
            for run in merged.paragraphs[0].runs:
                run.font.color.rgb = RGBColor(255, 255, 255)

            for idx, (label, value) in enumerate(rows, 1):
                set_cell_text(
                    project_table.rows[idx].cells[0], label, bold=True, font_size=9
                )
                shade_cell(project_table.rows[idx].cells[0], "F2F2F2")
                set_cell_text(project_table.rows[idx].cells[1], value, font_size=9.5)
                for run in project_table.rows[idx].cells[1].paragraphs[0].runs:
                    run.font.color.rgb = BASE_TEXT_COLOR
            
            autofit_table_to_contents(project_table)
            add_spacer(doc, 15)
            project_idx += 1


def render_roadmap_page(doc, payload: BlueprintPayload, output_path: Path) -> Any:
    add_heading_paragraph(doc, "Roadmap Estratégico y Matriz de Dependencias (SOTA)", level=1)
    
    add_body_paragraph(
        doc,
        "La siguiente matriz establece la ruta crítica de ejecución (Gantt). Las iniciativas no son compartimentos estancos; su secuenciación matemática garantiza que los habilitadores técnicos (dependencias) se desplieguen antes de la construcción de las capas superiores.",
        color_rgb=BASE_TEXT_COLOR
    )
    
    # Try to generate Mermaid Gantt
    from application.generate_mermaid_gantt import generate_mermaid_gantt
    import tempfile
    import os
    
    payload_path = output_path.parent / f"blueprint_{payload.document_meta.tower_code.lower()}_payload.json"
    png_path = Path(tempfile.gettempdir()) / f"gantt_{payload_path.name}.png"
    if payload_path.exists() and generate_mermaid_gantt(payload_path, png_path):
        doc.add_picture(str(png_path), width=Inches(6.5))
        add_spacer(doc, 10)
        try:
            os.remove(png_path)
        except OSError:
            pass

    table = doc.add_table(rows=1, cols=3)
    finalize_table(table)
    headers = ["Horizonte / Fase", "Iniciativa de Ingeniería", "Dependencias Técnicas (Predecesores)"]
    for i, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], header, bold=True, font_size=10)
        shade_cell(table.rows[0].cells[i], "D9EAF7")

    # Gather all internal projects for quick lookup
    internal_projects = set()
    for pilar in payload.pillars_analysis:
        for proj in pilar.projects_todo:
            internal_projects.add(proj.initiative)

    for wave in payload.roadmap:
        for project_name in wave.projects:
            # Find dependencies specifically for this project
            deps = []
            for d in payload.external_dependencies:
                if d.project == project_name:
                    dep_name = d.depends_on
                    tag = "[Interna]" if dep_name in internal_projects else "[Cross-Tower]"
                    deps.append(f"{tag} {dep_name}")
            
            deps_text = " • ".join(deps) if deps else "Independiente (Habilitador Fase 0)"
            
            row = table.add_row()
            set_cell_text(row.cells[0], wave.wave, bold=True, font_size=9.5)
            set_cell_text(row.cells[1], project_name, font_size=9.5)
            set_cell_text(row.cells[2], deps_text, font_size=9)
            
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.color.rgb = BASE_TEXT_COLOR
                        if "[Cross-Tower]" in run.text:
                            run.font.color.rgb = RGBColor(192, 0, 0) # Dark red for cross-tower
                        elif "[Interna]" in run.text:
                            run.font.color.rgb = RGBColor(0, 112, 192) # Blue for internal
                        
    autofit_table_to_contents(table)
    add_spacer(doc, 15)


def render_maturity_profile(doc, annex_data: dict) -> Any:
    add_heading_paragraph(doc, "Perfil de madurez por pilar", level=1)

    if not annex_data:
        add_body_paragraph(
            doc,
            "No se ha encontrado el perfil de madurez detallado para esta torre.",
            color_rgb=BASE_TEXT_COLOR,
        )
        return

    profile = annex_data.get("pillar_score_profile", {})
    asis = annex_data.get("sections", {}).get("asis", {})

    add_body_paragraph(doc, profile.get("profile_intro", ""), color_rgb=BASE_TEXT_COLOR)
    note = add_body_paragraph(
        doc,
        profile.get("scoring_method_note", ""),
        color_rgb=BASE_TEXT_COLOR,
    )
    if note:
        for run in note.runs:
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(127, 127, 127)

    radar_path = profile.get("radar_chart", "")
    if radar_path and Path(radar_path).exists():
        add_heading_paragraph(doc, "Gráfico radial", level=2)
        image_paragraph = doc.add_paragraph()
        image_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        image_paragraph.add_run().add_picture(radar_path, width=Inches(4.35))
        add_spacer(doc, 10)

    pillars = profile.get("pillars", [])
    add_heading_paragraph(doc, "Detalle compacto por pilar", level=2)
    if pillars:
        table = doc.add_table(rows=1, cols=4)
        finalize_table(table)
        headers = ["Pilar", "Score", "Nivel", "Lectura ejecutiva"]
        for i, header in enumerate(headers):
            set_cell_text(table.rows[0].cells[i], header, bold=True, font_size=10)
            shade_cell(table.rows[0].cells[i], "D9EAF7")

        for pillar in pillars:
            row = table.add_row()
            maturity_band = pillar.get("maturity_band") or _resolve_annex_band(
                pillar.get("score_display")
            )
            set_cell_text(
                row.cells[0], pillar.get("pillar_label", ""), bold=True, font_size=9.5
            )
            set_cell_text(
                row.cells[1],
                pillar.get("score_display", ""),
                font_size=9.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            set_cell_text(row.cells[2], maturity_band, font_size=9.5)
            set_cell_text(
                row.cells[3], pillar.get("executive_reading", ""), font_size=9.5
            )
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.color.rgb = BASE_TEXT_COLOR
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

        strengths_cell = sg_table.rows[1].cells[0]
        strengths_cell.text = ""
        for item in strengths:
            p = strengths_cell.add_paragraph(f"• {item}")
            p.paragraph_format.left_indent = Pt(10)
            p.paragraph_format.first_line_indent = Pt(-10)
            p.paragraph_format.space_after = Pt(4)
            for run in p.runs:
                run.font.size = Pt(9.5)
                run.font.color.rgb = BASE_TEXT_COLOR

        gaps_cell = sg_table.rows[1].cells[1]
        gaps_cell.text = ""
        for item in gaps:
            p = gaps_cell.add_paragraph(f"• {item}")
            p.paragraph_format.left_indent = Pt(10)
            p.paragraph_format.first_line_indent = Pt(-10)
            p.paragraph_format.space_after = Pt(4)
            for run in p.runs:
                run.font.size = Pt(9.5)
                run.font.color.rgb = BASE_TEXT_COLOR

        autofit_table_to_contents(sg_table)
        add_spacer(doc, 10)

    impacts = asis.get("operational_impacts", [])
    if impacts:
        add_heading_paragraph(doc, "Implicaciones operativas clave", level=2)
        for impact in impacts:
            p = doc.add_paragraph(f"• {impact}")
            p.paragraph_format.left_indent = Pt(20)
            p.paragraph_format.first_line_indent = Pt(-10)
            for run in p.runs:
                run.font.color.rgb = BASE_TEXT_COLOR


def render_conclusion(doc, annex_data: dict) -> Any:
    add_heading_paragraph(doc, "5. Conclusión", level=1)

    if not annex_data:
        add_body_paragraph(
            doc,
            "No se ha encontrado información de conclusión para esta torre.",
            color_rgb=BASE_TEXT_COLOR,
        )
        return

    conclusion = annex_data.get("sections", {}).get("conclusion", {})

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
            for run in p.runs:
                run.font.color.rgb = BASE_TEXT_COLOR

    if conclusion.get("closing_statement"):
        add_heading_paragraph(doc, "Próximos pasos", level=2)
        add_body_paragraph(
            doc, conclusion.get("closing_statement"), color_rgb=BASE_TEXT_COLOR
        )


def render_blueprint(
    payload: BlueprintPayload,
    output_path: Path,
    client_dir: Path,
    template_path: Path = DEFAULT_TEMPLATE_PATH,
) -> Path:
    annex_data = load_annex_data(client_dir, payload.document_meta.tower_code)
    client_intelligence = load_client_intelligence(client_dir)

    doc = Document(str(template_path))
    clear_document_body(doc)
    if doc.sections:
        create_page_number_footer(doc.sections[0])

    render_cover(doc, payload)
    render_snapshot_page(doc, payload, client_intelligence, annex_data)
    render_maturity_profile(doc, annex_data)
    render_cross_capabilities_analysis(doc, payload)

    render_consolidated_asis(doc, payload)
    render_fair_risk_heatmap(doc, payload)
    render_consolidated_tobe(doc, payload)
    render_roadmap_page(doc, payload, output_path)
    render_deep_project_charters(doc, payload)

    render_conclusion(doc, annex_data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    return output_path


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) != 3:
        sys.exit(1)

    payload_path = Path((argv if argv is not None else sys.argv)[1])
    output_path = Path((argv if argv is not None else sys.argv)[2])
    client_dir = resolve_client_dir(payload_path, load_json(payload_path))
    annex_data = load_annex_data(client_dir, payload_path.parent.name)
    payload = load_payload(payload_path, annex_data=annex_data)

    render_blueprint(
        payload=payload,
        output_path=output_path,
        client_dir=client_dir,
    )
    print(f"Blueprint de Torre renderizado: {output_path}")


if __name__ == "__main__":
    main()
