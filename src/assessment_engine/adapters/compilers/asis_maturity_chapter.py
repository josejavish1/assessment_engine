"""Maturity profile, platform description, and systemic risk chapter builder for Word DOCX."""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

from assessment_engine.infrastructure.docx_render_utils import (
    autofit_table_to_contents,
    finalize_table,
    shade_cell,
)
from assessment_engine.infrastructure.localization import (
    format_currency,
    format_number,
    t,
)
from assessment_engine.adapters.compilers.asis_docx_primitives import (
    DocumentCompilationContext,
    _add_markdown_bullet,
    add_body_paragraph,
    add_callout_box,
    add_heading,
    add_spacer,
    extract_key_bullets_from_md,
    format_currency_custom,
    parse_and_append_markdown_section,
    set_cell_border_white,
    set_cell_text_custom,
)

logger = logging.getLogger(__name__)

def _compile_chapter_3_maturity_profile(doc: Any, ctx: DocumentCompilationContext) -> None:
    """Assemble and render Chapter 3: Maturity Profile and General Evaluation."""
    p_color_rgb = ctx["p_color_rgb"]
    text_color_rgb = ctx["text_color_rgb"]
    p_color_hex = ctx["p_color_hex"]
    alt_row_hex = ctx["alt_row_hex"]
    vocab = ctx["vocab"]
    modules_dir = ctx["modules_dir"]
    doc_lang = ctx["doc_lang"]
    global_score = ctx.get("global_score", 3.0)
    global_band = ctx.get("global_band", "Definido")
    global_reading = ctx.get("global_reading", "")
    client_name = ctx["client_name"]
    tower_name = ctx["tower_name"]
    custom_overview_intro = ctx.get("custom_overview_intro")
    b_data = ctx.get("b_data", {})
    payload_path = ctx["payload_path"]
    tower_dir_obj = ctx["tower_dir_obj"]
    intel_data = ctx.get("intel_data", {})
    tower_id = ctx.get("tower_id", "TXX")

    def add_markdown_bullet_local(text: str, space_after: int = 4) -> Any:
        return _add_markdown_bullet(doc, text, text_color_rgb, space_after)

    # Assemble and render Chapter 3: Maturity Profile and General Evaluation.
    #
    chapter_3_title = t(
        "chapter_3_title",
        locale=doc_lang,
        default=(
            "Evaluación y Madurez Tecnológica"
            if doc_lang == "es"
            else "Technology Maturity and Evaluation"
        ),
    )
    add_heading(doc, chapter_3_title, level=1, primary_color_rgb=p_color_rgb)

    # Assemble and render Section 3.1: Global Maturity Dashboard; centered, 2-column layout per requirement 2.
    add_heading(doc, vocab["dashboard_title"], level=2, primary_color_rgb=p_color_rgb)
    add_body_paragraph(doc, vocab["dashboard_intro"], text_color_rgb=text_color_rgb)

    dash_table = doc.add_table(rows=2, cols=2)
    dash_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    finalize_table(dash_table)

    # Data Sanitization: Ensure data integrity by dynamically resolving scores and qualitative bands from the canonical scoring output.
    formatted_global_score = format_number(
        global_score, locale=doc_lang, decimals=2
    )
    display_score_str = f"{formatted_global_score} / {format_number(5.0, locale=doc_lang, decimals=2)}"
    display_band_str = f"{global_band}"

    #
    for i, h_txt in enumerate([vocab["score_lbl"], vocab["maturity_lbl"]]):
        set_cell_text_custom(
            dash_table.rows[0].cells[i],
            h_txt,
            bold=True,
            font_size=9,
            color_rgb=RGBColor(255, 255, 255),
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(dash_table.rows[0].cells[i], p_color_hex)
        dash_table.rows[0].cells[i].width = Inches(3.25)  #

    set_cell_text_custom(
        dash_table.rows[1].cells[0],
        display_score_str,
        bold=True,
        font_size=16,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    set_cell_text_custom(
        dash_table.rows[1].cells[1],
        display_band_str,
        bold=True,
        font_size=12,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )

    # Apply conditional cell shading based on the final severity score. A score below 3.40 receives a yellow background.
    shade_cell(
        dash_table.rows[1].cells[0], "FFF3CD" if global_score < 3.4 else "D9F2D9"
    )
    shade_cell(
        dash_table.rows[1].cells[1], "FFF3CD" if global_score < 3.4 else "D9F2D9"
    )

    # Set data cells to expand to the full table width to maintain a fixed layout.
    dash_table.rows[1].cells[0].width = Inches(3.25)
    dash_table.rows[1].cells[1].width = Inches(3.25)  #

    # Disable the `autofit` property to enforce a fixed table width of 6.5 inches.
    dash_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    add_spacer(doc, 5)

    # Insert a structured, compact reference table detailing the maturity levels, with the client's current level highlighted dynamically.
    add_spacer(doc, 10)
    add_heading(
        doc,
        t("maturity_ref_framework_title", locale=doc_lang, default="Marco de Referencia de Niveles de Madurez"),
        level=3,
        primary_color_rgb=p_color_rgb,
    )

    p_ref_intro = add_body_paragraph(
        doc,
        t("cmmi_table_intro", locale=doc_lang, default="La evaluación del nivel de madurez de las capacidades técnicas se fundamenta en un marco de 5 estadios escalonados."),
        text_color_rgb=text_color_rgb
    )
    add_spacer(doc, 5)

    ref_table = doc.add_table(rows=1, cols=3)
    ref_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    ref_table.style = "Table Grid"
    
    headers_ref = [
        t("cmmi_table_header_level", locale=doc_lang, default="Nivel de Madurez"),
        t("cmmi_table_header_range", locale=doc_lang, default="Rango"),
        t("cmmi_table_header_desc", locale=doc_lang, default="Descripción de Estado de Prácticas"),
    ]
    for i, h_txt in enumerate(headers_ref):
        set_cell_text_custom(ref_table.rows[0].cells[i], h_txt, bold=True, font_size=8.5, color_rgb=RGBColor(255, 255, 255), align=WD_ALIGN_PARAGRAPH.CENTER)
        shade_cell(ref_table.rows[0].cells[i], p_color_hex)
        
    levels_data = [
        (t("cmmi_level_1_title", locale=doc_lang, default="Nivel 1 - Inicial"), t("cmmi_level_1_range", locale=doc_lang, default="1,00 a 1,79"), t("cmmi_level_1_desc", locale=doc_lang, default="Procesos ad-hoc...")),
        (t("cmmi_level_2_title", locale=doc_lang, default="Nivel 2 - Repetible"), t("cmmi_level_2_range", locale=doc_lang, default="1,80 a 2,59"), t("cmmi_level_2_desc", locale=doc_lang, default="Tareas básicas...")),
        (t("cmmi_level_3_title", locale=doc_lang, default="Nivel 3 - Definido"), t("cmmi_level_3_range", locale=doc_lang, default="2,60 a 3,39"), t("cmmi_level_3_desc", locale=doc_lang, default="Procesos formalizados...")),
        (t("cmmi_level_4_title", locale=doc_lang, default="Nivel 4 - Gestionado"), t("cmmi_level_4_range", locale=doc_lang, default="3,40 a 4,19"), t("cmmi_level_4_desc", locale=doc_lang, default="Monitorización continua...")),
        (t("cmmi_level_5_title", locale=doc_lang, default="Nivel 5 - Optimizado"), t("cmmi_level_5_range", locale=doc_lang, default="4,20 a 5,00"), t("cmmi_level_5_desc", locale=doc_lang, default="Mejora continua...")),
    ]
    
    try:
        gs_val = float(global_score)
    except Exception:
        gs_val = 3.0

    for l_idx, (lvl_name, lvl_range, lvl_desc) in enumerate(levels_data):
        row = ref_table.add_row()
        bg_col = alt_row_hex if l_idx % 2 == 1 else "FFFFFF"
        
        is_active_lvl = False
        if l_idx == 0 and 1.00 <= gs_val <= 1.79:
            is_active_lvl = True
        elif l_idx == 1 and 1.80 <= gs_val <= 2.59:
            is_active_lvl = True
        elif l_idx == 2 and 2.60 <= gs_val <= 3.39:
            is_active_lvl = True
        elif l_idx == 3 and 3.40 <= gs_val <= 4.19:
            is_active_lvl = True
        elif l_idx == 4 and 4.20 <= gs_val <= 5.00:
            is_active_lvl = True
            
        if is_active_lvl:
            # Highlight the active maturity level row to represent the current state dynamically
            row_bg_color = "FFF3CD" if gs_val < 3.4 else "D9F2D9"  # Dynamically synchronized with previous table score band color
            actual_badge = t("current_state_badge", locale=doc_lang, default="(ACTUAL)" if doc_lang == "es" else "(CURRENT)")
            set_cell_text_custom(row.cells[0], f"{lvl_name} {actual_badge}", bold=True, font_size=8, color_rgb=RGBColor(*p_color_rgb), align=WD_ALIGN_PARAGRAPH.LEFT)
            set_cell_text_custom(row.cells[1], lvl_range, bold=True, font_size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
            set_cell_text_custom(row.cells[2], lvl_desc, font_size=8, align=WD_ALIGN_PARAGRAPH.LEFT)
            for cell in row.cells:
                shade_cell(cell, row_bg_color)
        else:
            set_cell_text_custom(row.cells[0], lvl_name, bold=True, font_size=8, align=WD_ALIGN_PARAGRAPH.LEFT)
            shade_cell(row.cells[0], alt_row_hex)
            set_cell_text_custom(row.cells[1], lvl_range, font_size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
            shade_cell(row.cells[1], bg_col)
            set_cell_text_custom(row.cells[2], lvl_desc, font_size=8, align=WD_ALIGN_PARAGRAPH.LEFT)
            shade_cell(row.cells[2], bg_col)
            
    # Set explicit column widths to narrow 'Nivel de Madurez' and widen 'Rango' slightly
    ref_table.allow_autofit = False
    ref_table.autofit = False
    col_widths = [Inches(1.5), Inches(1.2), Inches(3.8)]
    for row in ref_table.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = w
            
    add_spacer(doc, 15)

    # Narrative explanation linking the score with the environment context
    score_formatted = f"{gs_val:.2f}".replace(".", ",") if doc_lang == "es" else f"{gs_val:.2f}"
    explanation_str = (
        f"La calificación cuantitativa obtenida de **{score_formatted} sobre 5,00** sitúa a la plataforma en la banda de **{global_band}**. "
        f"Este resultado consolida una situación donde {global_reading.strip()} "
        f"Para avanzar hacia el siguiente umbral de madurez, se requiere corregir de manera prioritaria "
        f"las brechas estructurales de control, los cuellos de botella y la deuda técnica, "
        f"los cuales se detallan analíticamente en los sub-dominios técnicos evaluados a continuación."
    )
    add_body_paragraph(doc, explanation_str, text_color_rgb=text_color_rgb)
    add_spacer(doc, 15)

    # Standard Diagnostic and Performance Matrix by Technical Domain
    health_title = t(
        "diagnosis_performance_matrix_title",
        locale=doc_lang,
        default=(
            "Matriz de Diagnóstico y Desempeño por Dominio Tecnológico"
            if doc_lang == "es"
            else "Diagnosis and Performance Matrix by Technology Domain"
        ),
    )
    add_heading(doc, health_title, level=2, primary_color_rgb=p_color_rgb)
    add_body_paragraph(
        doc,
        t(
            "diagnosis_performance_matrix_intro",
            locale=doc_lang,
            default=(
                "A continuación, se detalla el perfil de desempeño operativo y de gobierno para cada uno de los sub-dominios técnicos evaluados dentro de esta torre:"
            ),
        ),
        text_color_rgb=text_color_rgb,
    )
    add_spacer(doc, 5)

    health_table = doc.add_table(rows=1, cols=3)
    health_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    health_table.style = "Table Grid"

    for i, h_txt in enumerate(
        [
            t(
                "table_header_pillar_capacity",
                locale=doc_lang,
                default="Pilar / Capacidad Tecnológica Evaluada",
            ),
            t("table_header_score_asis", locale=doc_lang, default="Score AS-IS"),
            t(
                "table_header_maturity_level",
                locale=doc_lang,
                default="Nivel de Madurez",
            ),
        ]
    ):
        set_cell_text_custom(
            health_table.rows[0].cells[i],
            h_txt,
            bold=True,
            font_size=10,
            color_rgb=RGBColor(255, 255, 255),
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(health_table.rows[0].cells[i], p_color_hex)

    if b_data and "pillars_analysis" in b_data:
        from assessment_engine.domain.maturity_band import (
            ANNEX_MATURITY_BANDS,
            resolve_maturity_band,
        )

        for s_idx, p in enumerate(
            sorted(
                b_data.get("pillars_analysis", []),
                key=lambda item: item.get("score", 0.0),
            )
        ):
            bg = alt_row_hex if s_idx % 2 == 1 else "FFFFFF"
            p_name = p.get("pilar_name", "Pilar")
            p_score = float(p.get("score", 3.0))

            score_formatted = format_number(
                p_score, locale=doc_lang, decimals=2
            )
            p_status = resolve_maturity_band(
                p_score, ANNEX_MATURITY_BANDS, locale=doc_lang
            )["label"]

            # Map score to background color
            if p_score >= 4.20:
                p_bg_color = "D9F2D9"
            elif p_score >= 3.40:
                p_bg_color = "E2F0D9"
            elif p_score >= 2.60:
                p_bg_color = "FFF3CD"
            elif p_score >= 1.80:
                p_bg_color = "FCE4D6"
            else:
                p_bg_color = "F2D9D9"

            row = health_table.add_row()
            set_cell_text_custom(row.cells[0], p_name, bold=True, font_size=10)
            shade_cell(row.cells[0], alt_row_hex)
            
            set_cell_text_custom(row.cells[1], score_formatted, font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
            shade_cell(row.cells[1], bg)
            
            set_cell_text_custom(row.cells[2], p_status, bold=True, font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
            shade_cell(row.cells[2], p_bg_color)
            
    autofit_table_to_contents(health_table)
    add_spacer(doc, 20)

    # Assemble and render Section 3.2: Full-Page Radar Chart; custom dimensions per user request.
    add_heading(doc, vocab["radar_title"], level=2, primary_color_rgb=p_color_rgb)
    radar_path = tower_dir_obj / "pillar_radar_chart.generated.png"
    if not radar_path.exists() and b_data and "pillars_analysis" in b_data:
        try:
            from assessment_engine.application.generate_tower_radar_chart import generate_radar_chart_from_pillars
            chart_pillars = []
            for p in b_data.get("pillars_analysis", []):
                chart_pillars.append({
                    "pillar_label": p.get("pilar_name", p.get("pilar_id", "Pilar")),
                    "score_display": p.get("score", 0.0)
                })
            if chart_pillars:
                generate_radar_chart_from_pillars(chart_pillars, radar_path)
                logger.info(f"✅ Gráfico radial auto-generado con éxito en: {radar_path}")
        except Exception as ex:
            logger.info(f"⚠️ No se pudo auto-generar el gráfico radial: {ex}")

    if radar_path.exists():
        add_spacer(doc, 5)
        doc.add_picture(str(radar_path), width=Cm(11.11), height=Cm(9.18))  #
        p_img = doc.paragraphs[-1]
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_spacer(doc, 15)

    # RAGE Forensic Verification Injection
    snapshot_file = tower_dir_obj.parent / "benchmarks_snapshot.json"
    if snapshot_file.exists():
        try:
            with open(snapshot_file, "r", encoding="utf-8-sig") as sf:
                snap_data = json.load(sf)
            snapshots = snap_data.get("snapshots", {})
            if snapshots:
                # Silent Drop: Filter and find valid, verified benchmarks for the current tower
                valid_snapshots = []
                for t_id, t_snap in sorted(snapshots.items()):
                    if t_id != tower_id:
                        continue
                    verif_status = t_snap.get("verification_status", "failed")
                    quote = t_snap.get("evidence_quote", "")
                    if verif_status == "verified" and quote and "no se encontraron" not in quote.lower() and "no se ha encontrado" not in quote.lower():
                        valid_snapshots.append((t_id, t_snap))

                if valid_snapshots:
                    add_heading(doc, "Justificación de Estándares Sectoriales (Trazabilidad RAGE)", level=2, primary_color_rgb=p_color_rgb)
                    intro_text = (
                        "Los estándares de mercado del gráfico radial anterior se han calibrado y verificado en tiempo "
                        "de ejecución mediante el motor RAGE (Runtime Agentic Grounding & Evaluation). Cada benchmark "
                        "está respaldado por evidencias factoperativas y copias de seguridad de documentos oficiales:"
                    )
                    add_body_paragraph(doc, intro_text, text_color_rgb=text_color_rgb)
                    add_spacer(doc, 10)

                    for t_id, t_snap in valid_snapshots:
                        framework_name = t_snap.get("framework_name", "Estándar Sectorial")
                        score = t_snap.get("dynamic_score", 4.0)
                        quote = t_snap.get("evidence_quote", "")
                        url = t_snap.get("evidence_source_url", "")
                        local_path = t_snap.get("local_snapshot_path", "")

                        header_p = f"**Torre {t_id} ({framework_name}) - Estándar: {score:,.1f}**"
                        add_body_paragraph(doc, header_p, text_color_rgb=text_color_rgb)

                        quote_p = f"✓ Evidencia extraída: \"{quote}\""
                        add_body_paragraph(doc, quote_p, italic=True, text_color_rgb=text_color_rgb)

                        source_p = f"Referencia: {url}"
                        if local_path:
                            source_p += f" | Bóveda local: {local_path}"
                        add_body_paragraph(doc, source_p, text_color_rgb=RGBColor(120, 130, 140))
                        add_spacer(doc, 10)
        except Exception as ex:
            logger.info(f"⚠️  [RAGE] Failed to inject RAGE report into main document: {ex}")

    # Assemble and render Section 3.3: Score Justification Matrix; left-aligned, omits 'TO-BE Target' column.
    csv_mat_path = modules_dir / "04_matriz_madurez.csv"
    if csv_mat_path.exists():
        mat_table = doc.add_table(rows=1, cols=3)
        mat_table.alignment = WD_TABLE_ALIGNMENT.LEFT
        mat_table.style = "Table Grid"

        headers_mat = vocab["justification_table_headers"]
        for i, h_txt in enumerate(headers_mat):
            set_cell_text_custom(
                mat_table.rows[0].cells[i],
                h_txt,
                bold=True,
                font_size=9,
                color_rgb=RGBColor(255, 255, 255),
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            shade_cell(mat_table.rows[0].cells[i], p_color_hex)

        with open(csv_mat_path, "r", encoding="utf-8") as cf:
            reader = csv.reader(cf, delimiter=";")
            next(reader)  #

            for r_idx, row_data in enumerate(reader):
                row = mat_table.add_row()
                set_cell_text_custom(
                    row.cells[0], row_data[0], bold=True, font_size=8.5
                )
                set_cell_text_custom(
                    row.cells[1],
                    row_data[1],
                    font_size=8.5,
                    align=WD_ALIGN_PARAGRAPH.CENTER,
                )
                
                # Sanitize third column heading text to remove grade placeholders
                justification_cell_text = row_data[2]
                import re
                justification_cell_text = re.sub(
                    r"\*\*Justificación de la Nota\s*\(\d+[,.]\d+\):\*\*",
                    "**Justificación de la Nota:**",
                    justification_cell_text
                )
                justification_cell_text = re.sub(
                    r"Justificación de la Nota\s*\(\d+[,.]\d+\):",
                    "Justificación de la Nota:",
                    justification_cell_text
                )
                
                set_cell_text_custom(
                    row.cells[2],
                    justification_cell_text,
                    font_size=8.5,
                    align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                )

                if r_idx % 2 == 1:
                    for cell in row.cells:
                        shade_cell(cell, alt_row_hex)

        autofit_table_to_contents(mat_table)
        add_spacer(doc, 20)

    transversal_title = "Análisis Transversal de Deuda Tecnológica y Patrones de Riesgo Estructural" if doc_lang == "es" else "Cross-Cutting Analysis of Technological Debt and Structural Risk Patterns"
    add_heading(doc, transversal_title, level=2, primary_color_rgb=p_color_rgb)
    parse_and_append_markdown_section(
        doc,
        modules_dir / "05_transversal.md",
        p_color_rgb,
        text_color_rgb,
        skip_level_1=True,
    )

    # 3.5 Structural Risk Indicators and Decision Context
    if intel_data:
        try:
            overrides = intel_data.get("tower_overrides", {}).get(tower_id, {})
            metrics = overrides.get("metrics", {}) if isinstance(overrides, dict) else {}
            business_criticality = metrics.get("business_criticality") if isinstance(metrics, dict) else None
            regulatory_compliance = metrics.get("regulatory_compliance") if isinstance(metrics, dict) else None
            implementation_feasibility = metrics.get("implementation_feasibility") if isinstance(metrics, dict) else None
            
            sensitivity = overrides.get("sensitivity_analysis", {}) if isinstance(overrides, dict) else {}
            dii_03 = None
            if isinstance(sensitivity, dict):
                dii_03 = sensitivity.get("decision_instability_indices", {}).get("dii_threshold_03_pct")
            
            epistemic = intel_data.get("epistemic_graph", {}) if isinstance(intel_data, dict) else {}
            audits = epistemic.get("audits", {}) if isinstance(epistemic, dict) else {}
            erc_dict = audits.get("eigenvector_risk_centrality", {}) if isinstance(audits, dict) else {}
            erc = erc_dict.get(tower_id) if isinstance(erc_dict, dict) else None
            
            spof_by_cascade = audits.get("single_point_of_failure_by_cascade", "") if isinstance(audits, dict) else ""
            spof_by_centrality = audits.get("single_point_of_failure_by_centrality", "") if isinstance(audits, dict) else ""
            
            if business_criticality is not None:
                add_heading(doc, "Análisis de Interdependencias Tecnológicas y Negocio", level=2, primary_color_rgb=p_color_rgb)
                
                # Introductory paragraph (un-italicized, justified, size 10)
                if doc_lang == "es":
                    intro_text_inter = (
                        "La infraestructura tecnológica no opera de manera aislada; un evento en un dominio específico puede "
                        "propagar riesgos y afectar la continuidad de los servicios de negocio de forma inmediata. Por ello, "
                        "esta sección conecta el diagnóstico técnico de la plataforma con su impacto estratégico real. Para lograrlo, "
                        "el motor de evaluación analiza de forma integrada tres dimensiones clave:"
                    )
                else:
                    intro_text_inter = (
                        "Technology infrastructure does not operate in isolation; an event in a specific domain can propagate "
                        "risks and immediately impact business service continuity. Therefore, this section connects the technical "
                        "diagnosis of the platform with its real strategic impact. To achieve this, the evaluation engine integrates "
                        "three key dimensions:"
                    )
                add_body_paragraph(doc, intro_text_inter, text_color_rgb=text_color_rgb)
                
                # Three clear bullet points
                if doc_lang == "es":
                    add_body_paragraph(doc, "Criticidad Operativa y Presión Regulatoria: Determina el nivel de dependencia directa de los procesos de negocio y la exigencia de conformidad legal y normativa (v.g. NIS2, DORA o ISO 27001) sobre este dominio.", style="List Bullet", text_color_rgb=text_color_rgb)
                    add_body_paragraph(doc, "Viabilidad de la Transformación: Estima la complejidad técnica y facilidad operativa para ejecutar los proyectos del plan de acción propuesto.", style="List Bullet", text_color_rgb=text_color_rgb)
                    add_body_paragraph(doc, "Propagación Topológica y SPOF: Cuantifica el riesgo de que un incidente crítico se propague en cascada a otras torres y determina si el dominio actúa como un Punto Único de Fallo.", style="List Bullet", text_color_rgb=text_color_rgb)
                else:
                    add_body_paragraph(doc, "Operational Criticality and Regulatory Pressure: Assesses the level of direct business process dependency and legal compliance requirements (e.g., NIS2, DORA, or ISO 27001) on this domain.", style="List Bullet", text_color_rgb=text_color_rgb)
                    add_body_paragraph(doc, "Transformation Feasibility: Estimates the technical complexity and operational ease of executing the projects in the proposed action plan.", style="List Bullet", text_color_rgb=text_color_rgb)
                    add_body_paragraph(doc, "Topological Propagation and SPOF: Quantifies the risk of critical incident cascade propagation to other towers and determines if the domain acts as a Single Point of Failure.", style="List Bullet", text_color_rgb=text_color_rgb)
                
                # Concluding paragraph (size 10, justified)
                if doc_lang == "es":
                    desc_rest = "Estos indicadores proporcionan un contexto de decisión cuantitativo y objetivo, permitiendo priorizar las inversiones de transformación en base a su retorno estratégico y resiliencia para la organización:"
                else:
                    desc_rest = "These indicators provide an objective, quantitative decision context, allowing strategic investments to be prioritized based on transformation viability and overall resilience:"
                add_body_paragraph(doc, desc_rest, text_color_rgb=text_color_rgb)
                
                add_spacer(doc, 5)

                spof_status = "SÍ" if (tower_id == spof_by_cascade or tower_id == spof_by_centrality) else "NO"
                spof_status_text = t("interdep_spof_yes", locale=doc_lang, default="YES") if spof_status == "SÍ" else t("interdep_spof_no", locale=doc_lang, default="NO")
                dii_val = f"{dii_03:.1f}%" if dii_03 is not None else "0,0%"
                erc_val = f"{erc:.3f}" if erc is not None else "0,000"

                inter_table = doc.add_table(rows=1, cols=3)
                inter_table.alignment = WD_TABLE_ALIGNMENT.CENTER
                inter_table.style = "Table Grid"

                headers_inter = [
                    t("interdep_header_indicator", locale=doc_lang, default="Indicador Estratégico"),
                    t("interdep_header_value", locale=doc_lang, default="Valor / Score"),
                    t("interdep_header_status", locale=doc_lang, default="Estado y Clasificación"),
                ]
                for i, h_txt in enumerate(headers_inter):
                    set_cell_text_custom(
                        inter_table.rows[0].cells[i], h_txt, bold=True, font_size=10, color_rgb=RGBColor(255, 255, 255), align=WD_ALIGN_PARAGRAPH.CENTER
                    )
                    shade_cell(inter_table.rows[0].cells[i], p_color_hex)

                crit_label = t("interdep_status_extreme", locale=doc_lang, default="Extrema (Pilar Crítico)") if business_criticality >= 80.0 else (t("interdep_status_high", locale=doc_lang, default="Alta") if business_criticality >= 50.0 else t("interdep_status_medium", locale=doc_lang, default="Media"))
                reg_label = t("interdep_status_critical", locale=doc_lang, default="Crítica (Regulación Estricta)") if regulatory_compliance >= 80.0 else (t("interdep_status_moderate", locale=doc_lang, default="Moderada") if regulatory_compliance >= 50.0 else t("interdep_status_standard", locale=doc_lang, default="Estándar"))
                viab_label = t("interdep_status_viable", locale=doc_lang, default="Viable") if implementation_feasibility >= 60.0 else t("interdep_status_complex", locale=doc_lang, default="Complejo (Requiere mitigación)")
                dii_label = t("interdep_status_stable_diag", locale=doc_lang, default="Estable (Diagnóstico Robusto)") if (dii_03 or 0) < 15.0 else (t("interdep_status_mod_diag", locale=doc_lang, default="Moderado") if (dii_03 or 0) < 30.0 else t("interdep_status_volatile_diag", locale=doc_lang, default="Sensible"))
                erc_label = t("interdep_status_high_influence", locale=doc_lang, default="Alta Influencia") if (erc or 0) >= 0.50 else (t("interdep_status_moderate", locale=doc_lang, default="Media") if (erc or 0) >= 0.20 else t("interdep_status_low_influence", locale=doc_lang, default="Baja/Aislada"))
                spof_label = t("interdep_status_bottleneck", locale=doc_lang, default="Cuello de Botella Estructural") if spof_status == "SÍ" else t("interdep_status_not_bottleneck", locale=doc_lang, default="Estable en Red Causal")

                spof_row_title = t("interdep_spof_title", locale=doc_lang, default="Punto Único de Fallo (SPOF)")

                inter_data = [
                    (t("interdep_business_criticality_title", locale=doc_lang, default="Criticidad de Negocio (MCDA)"), f"{business_criticality:.1f}%", crit_label),
                    (t("interdep_reg_pressure_title", locale=doc_lang, default="Presión Regulatoria (MCDA)"), f"{regulatory_compliance:.1f}%", reg_label),
                    (t("interdep_op_viability_title", locale=doc_lang, default="Viabilidad Operativa (MCDA)"), f"{implementation_feasibility:.1f}%", viab_label),
                    (t("interdep_dii_title", locale=doc_lang, default="Consistencia del Diagnóstico (DII)"), dii_val, dii_label),
                    (t("interdep_erc_title", locale=doc_lang, default="Propagación de Fallos en Cascada (ERC)"), erc_val, erc_label),
                    (spof_row_title, spof_status_text, spof_label)
                ]

                for r_idx, row_vals in enumerate(inter_data):
                    row = inter_table.add_row()
                    set_cell_text_custom(row.cells[0], row_vals[0], bold=True, font_size=10)
                    
                    if row_vals[0] == spof_row_title:
                        set_cell_text_custom(row.cells[1], row_vals[1], bold=True, font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
                        shade_cell(row.cells[1], "F2D9D9" if spof_status == "SÍ" else "D9F2D9")
                    else:
                        set_cell_text_custom(row.cells[1], row_vals[1], font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
                        
                    set_cell_text_custom(row.cells[2], row_vals[2], font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

                    if r_idx % 2 == 0:
                        for cell in row.cells:
                            if cell != row.cells[1] or row_vals[0] != spof_row_title:
                                shade_cell(cell, alt_row_hex)

                autofit_table_to_contents(inter_table)
                add_spacer(doc, 10)

                # Add Glossary / Legend
                p_gloss = doc.add_paragraph()
                p_gloss.paragraph_format.space_before = Pt(8)
                p_gloss.paragraph_format.space_after = Pt(2)
                run_g_title = p_gloss.add_run(t("interdep_gloss_title", locale=doc_lang, default="Análisis Ejecutivo de Indicadores de Interdependencia:"))
                run_g_title.bold = True
                run_g_title.font.name = "Arial"
                run_g_title.font.size = Pt(10)
                run_g_title.font.color.rgb = RGBColor(*text_color_rgb)

                glossary_items = []
                
                if business_criticality >= 80.0:
                    glossary_items.append(t("gloss_mcda_crit_extrema", locale=doc_lang, val=f"{business_criticality:.1f}"))
                elif business_criticality >= 50.0:
                    glossary_items.append(t("gloss_mcda_crit_alta", locale=doc_lang, val=f"{business_criticality:.1f}"))
                else:
                    glossary_items.append(t("gloss_mcda_crit_media", locale=doc_lang, val=f"{business_criticality:.1f}"))

                if regulatory_compliance >= 80.0:
                    glossary_items.append(t("gloss_mcda_reg_critica", locale=doc_lang, val=f"{regulatory_compliance:.1f}"))
                elif regulatory_compliance >= 50.0:
                    glossary_items.append(t("gloss_mcda_reg_moderada", locale=doc_lang, val=f"{regulatory_compliance:.1f}"))
                else:
                    glossary_items.append(t("gloss_mcda_reg_estandar", locale=doc_lang, val=f"{regulatory_compliance:.1f}"))

                if implementation_feasibility >= 60.0:
                    glossary_items.append(t("gloss_mcda_viab_fav", locale=doc_lang, val=f"{implementation_feasibility:.1f}"))
                else:
                    glossary_items.append(t("gloss_mcda_viab_comp", locale=doc_lang, val=f"{implementation_feasibility:.1f}"))

                dii_pct = dii_03 if dii_03 is not None else 0.0
                if dii_pct < 15.0:
                    glossary_items.append(t("gloss_dii_alta", locale=doc_lang, val=f"{dii_pct:.1f}"))
                elif dii_pct < 30.0:
                    glossary_items.append(t("gloss_dii_mod", locale=doc_lang, val=f"{dii_pct:.1f}"))
                else:
                    glossary_items.append(t("gloss_dii_vol", locale=doc_lang, val=f"{dii_pct:.1f}"))

                erc_val_num = erc if erc is not None else 0.0
                if erc_val_num >= 0.50:
                    glossary_items.append(t("gloss_erc_alta", locale=doc_lang, val=f"{erc_val_num:.3f}"))
                elif erc_val_num >= 0.20:
                    glossary_items.append(t("gloss_erc_media", locale=doc_lang, val=f"{erc_val_num:.3f}"))
                else:
                    glossary_items.append(t("gloss_erc_baja", locale=doc_lang, val=f"{erc_val_num:.3f}"))

                if spof_status == "SÍ":
                    glossary_items.append(t("gloss_spof_crit", locale=doc_lang))
                else:
                    glossary_items.append(t("gloss_spof_stable", locale=doc_lang))
                
                for item in glossary_items:
                    add_body_paragraph(doc, item, style="Bullet", text_color_rgb=text_color_rgb)
                
                add_spacer(doc, 20)
        except Exception as e:
            logger.info(f"⚠️ Error injecting systemic risk metrics: {e}")

    #


