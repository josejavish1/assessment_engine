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
    add_heading(doc, "Marco de Referencia de Niveles de Madurez", level=3, primary_color_rgb=p_color_rgb)

    p_ref_intro = add_body_paragraph(
        doc,
        "La evaluación del nivel de madurez de las capacidades técnicas se fundamenta en un marco de cinco niveles "
        "escalonados (escala de 1,00 a 5,00), alineados con las mejores prácticas de la industria y la ingeniería de software. "
        "La siguiente tabla describe los criterios de valoración y resalta el estado operativo actual de la organización:",
        text_color_rgb=text_color_rgb
    )
    add_spacer(doc, 5)

    ref_table = doc.add_table(rows=1, cols=3)
    ref_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    ref_table.style = "Table Grid"
    
    headers_ref = ["Nivel de Madurez", "Rango", "Descripción de Estado de Prácticas"]
    for i, h_txt in enumerate(headers_ref):
        set_cell_text_custom(ref_table.rows[0].cells[i], h_txt, bold=True, font_size=8.5, color_rgb=RGBColor(255, 255, 255), align=WD_ALIGN_PARAGRAPH.CENTER)
        shade_cell(ref_table.rows[0].cells[i], p_color_hex)
        
    levels_data = [
        ("Nivel 1 - Inicial", "1,00 a 1,79", "Procesos ad-hoc, manuales e individualizados. No existe consistencia en la ejecución ni documentación de soporte."),
        ("Nivel 2 - Repetible", "1,80 a 2,59", "Las tareas básicas se repiten pero dependen del conocimiento de personas clave. Bajo nivel de estandarización."),
        ("Nivel 3 - Definido", "2,60 a 3,39", "Procesos formalizados, documentados e implantados de manera coherente en toda la organización."),
        ("Nivel 4 - Gestionado", "3,40 a 4,19", "Existencia de monitorización continua, telemetrías y KPIs cuantitativos de rendimiento y calidad para controlar el servicio."),
        ("Nivel 5 - Optimizado", "4,20 a 5,00", "Mejora continua automatizada, autorremediación de desviaciones y optimización proactiva de la infraestructura.")
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
            set_cell_text_custom(row.cells[0], f"{lvl_name} (ACTUAL)", bold=True, font_size=8, color_rgb=RGBColor(*p_color_rgb), align=WD_ALIGN_PARAGRAPH.LEFT)
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
                dii_val = f"{dii_03:.1f}%" if dii_03 is not None else "0,0%"
                erc_val = f"{erc:.3f}" if erc is not None else "0,000"

                inter_table = doc.add_table(rows=1, cols=3)
                inter_table.alignment = WD_TABLE_ALIGNMENT.CENTER
                inter_table.style = "Table Grid"

                headers_inter = ["Indicador Estratégico", "Valor / Score", "Estado y Clasificación"]
                for i, h_txt in enumerate(headers_inter):
                    set_cell_text_custom(
                        inter_table.rows[0].cells[i], h_txt, bold=True, font_size=10, color_rgb=RGBColor(255, 255, 255), align=WD_ALIGN_PARAGRAPH.CENTER
                    )
                    shade_cell(inter_table.rows[0].cells[i], p_color_hex)

                inter_data = [
                    ("Criticidad de Negocio (MCDA)", f"{business_criticality:.1f}%", "Extrema (Pilar Crítico)" if business_criticality >= 80.0 else "Alta" if business_criticality >= 50.0 else "Media"),
                    ("Presión Regulatoria (MCDA)", f"{regulatory_compliance:.1f}%", "Crítica (Regulación Estricta)" if regulatory_compliance >= 80.0 else "Alta" if regulatory_compliance >= 50.0 else "Estándar"),
                    ("Viabilidad Operativa (MCDA)", f"{implementation_feasibility:.1f}%", "Viable" if implementation_feasibility >= 60.0 else "Complejo (Requiere mitigación)"),
                    ("Consistencia del Diagnóstico (DII)", dii_val, "Estable (Diagnóstico Robusto)" if (dii_03 or 0) < 15.0 else "Moderado" if (dii_03 or 0) < 30.0 else "Sensible"),
                    ("Propagación de Fallos en Cascada (ERC)", erc_val, "Alta Influencia" if (erc or 0) >= 0.50 else "Media" if (erc or 0) >= 0.20 else "Baja/Aislada"),
                    ("Punto Único de Fallo (SPOF)", spof_status, "Cuello de Botella Estructural" if spof_status == "SÍ" else "Estable en Red Causal")
                ]

                for r_idx, row_vals in enumerate(inter_data):
                    row = inter_table.add_row()
                    set_cell_text_custom(row.cells[0], row_vals[0], bold=True, font_size=10)
                    
                    if row_vals[0] == "Punto Único de Fallo (SPOF)":
                        set_cell_text_custom(row.cells[1], row_vals[1], bold=True, font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
                        shade_cell(row.cells[1], "F2D9D9" if spof_status == "SÍ" else "D9F2D9")
                    else:
                        set_cell_text_custom(row.cells[1], row_vals[1], font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
                        
                    set_cell_text_custom(row.cells[2], row_vals[2], font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

                    if r_idx % 2 == 0:
                        for cell in row.cells:
                            if cell != row.cells[1] or row_vals[0] != "Punto Único de Fallo (SPOF)":
                                shade_cell(cell, alt_row_hex)

                autofit_table_to_contents(inter_table)
                add_spacer(doc, 10)

                # Add Glossary / Legend
                p_gloss = doc.add_paragraph()
                p_gloss.paragraph_format.space_before = Pt(8)
                p_gloss.paragraph_format.space_after = Pt(2)
                run_g_title = p_gloss.add_run("Análisis Ejecutivo de Indicadores de Interdependencia:")
                run_g_title.bold = True
                run_g_title.font.name = "Arial"
                run_g_title.font.size = Pt(10)
                run_g_title.font.color.rgb = RGBColor(*text_color_rgb)

                glossary_items = []
                
                if business_criticality >= 80.0:
                    glossary_items.append(
                        f"**Criticidad de Negocio (MCDA) [{business_criticality:.1f}% - Extrema]:** Evalúa el nivel de dependencia directa que tienen los procesos operativos clave de la organización sobre esta torre, determinando el impacto de negocio en caso de indisponibilidad del servicio. En este caso, este valor extremo confirma que los procesos operativos core de la organización dependen críticamente de esta plataforma, y su indisponibilidad causaría una interrupción inmediata de servicios esenciales."
                    )
                elif business_criticality >= 50.0:
                    glossary_items.append(
                        f"**Criticidad de Negocio (MCDA) [{business_criticality:.1f}% - Alta]:** Evalúa el nivel de dependencia directa que tienen los procesos operativos clave de la organización sobre esta torre, determinando el impacto de negocio en caso de indisponibilidad del servicio. El score alto refleja una fuerte dependencia operativa, si bien existe un margen de tolerancia temporal antes de que impacte directamente en la continuidad del negocio."
                    )
                else:
                    glossary_items.append(
                        f"**Criticidad de Negocio (MCDA) [{business_criticality:.1f}% - Media]:** Evalúa el nivel de dependencia directa que tienen los procesos operativos clave de la organización sobre esta torre, determinando el impacto de negocio en caso de indisponibilidad del servicio. El impacto medio sugiere que la torre provee servicios de soporte o back-office cuya indisponibilidad temporal es asumible mediante planes de contingencia estándar."
                    )

                if regulatory_compliance >= 80.0:
                    glossary_items.append(
                        f"**Presión Regulatoria (MCDA) [{regulatory_compliance:.1f}% - Crítica]:** Mide la exigencia de conformidad legal y normativa obligatoria (bajo marcos normativos o directivas aplicables como NIS2, DORA o ISO 27001) que aplica sobre el perímetro de esta plataforma. Este score revela una exposición regulatoria crítica, donde las brechas de seguridad se traducen directamente en riesgo de sanciones económicas elevadas y responsabilidad legal corporativa."
                    )
                elif regulatory_compliance >= 50.0:
                    glossary_items.append(
                        f"**Presión Regulatoria (MCDA) [{regulatory_compliance:.1f}% - Moderada]:** Mide la exigencia de conformidad legal y normativa obligatoria (bajo marcos normativos o directivas aplicables como NIS2, DORA o ISO 27001) que aplica sobre el perímetro de esta plataforma. Existen requerimientos de cumplimiento y políticas de seguridad corporativas estrictas, requiriendo auditorías periódicas de los controles de TI."
                    )
                else:
                    glossary_items.append(
                        f"**Presión Regulatoria (MCDA) [{regulatory_compliance:.1f}% - Estándar]:** Mide la exigencia de conformidad legal y normativa obligatoria (bajo marcos normativos o directivas aplicables como NIS2, DORA o ISO 27001) que aplica sobre el perímetro de esta plataforma. Exposición regulatoria estándar basada en el cumplimiento de buenas prácticas de ingeniería sin un escrutinio normativo crítico directo."
                    )

                if implementation_feasibility >= 60.0:
                    glossary_items.append(
                        f"**Viabilidad Operativa (MCDA) [{implementation_feasibility:.1f}% - Favorable]:** Estima el nivel de complejidad operativa y facilidad técnica para ejecutar los proyectos del plan de acción propuesto, considerando recursos, ventanas de mantenimiento y dependencias previas. La viabilidad de transformación es favorable. Los proyectos de modernización se pueden abordar con tecnologías maduras y recursos disponibles en el mercado sin generar disrupciones críticas."
                    )
                else:
                    glossary_items.append(
                        f"**Viabilidad Operativa (MCDA) [{implementation_feasibility:.1f}% - Compleja]:** Estima el nivel de complejidad operativa y facilidad técnica para ejecutar los proyectos del plan de acción propuesto, considerando recursos, ventanas de mantenimiento y dependencias previas. La baja calificación actual refleja que existe una alta complejidad para la transformación debido a la presencia de deudas estructurales profundas, cuellos de botella en el mantenimiento o falta de talento especializado."
                    )

                dii_pct = dii_03 if dii_03 is not None else 0.0
                if dii_pct < 15.0:
                    glossary_items.append(
                        f"**Consistencia del Diagnóstico (Índice DII) [{dii_pct:.1f}% - Alta Estabilidad]:** Este indicador (Decision Instability Index) mide la robustez matemática del diagnóstico frente a cambios en la información de partida. Evalúa cuál es la probabilidad de que una variación menor en las evidencias documentales o en las respuestas de las entrevistas provoque una alteración o inestabilidad en la calificación final de madurez de la torre (valores bajos garantizan un diagnóstico altamente consistente y fiable). En este caso, el índice extremadamente bajo garantiza de forma objetiva que el diagnóstico es altamente robusto y representativo de la realidad de la plataforma, impidiendo que fluctuaciones puntuales alteren las conclusiones estratégicas."
                    )
                elif dii_pct < 30.0:
                    glossary_items.append(
                        f"**Consistencia del Diagnóstico (Índice DII) [{dii_pct:.1f}% - Estabilidad Moderada]:** Este indicador (Decision Instability Index) mide la robustez matemática del diagnóstico frente a cambios en la información de partida. Evalúa cuál es la probabilidad de que una variación menor en las evidencias documentales o en las respuestas de las entrevistas provoque una alteración o inestabilidad en la calificación final de madurez de la torre (valores bajos garantizan un diagnóstico altamente consistente y fiable). El índice registrado indica una sensibilidad moderada; el diagnóstico es sustancialmente estable, si bien ciertas puntuaciones dependen en parte de interpretaciones técnicas que requieren consolidación técnica futura."
                    )
                else:
                    glossary_items.append(
                        f"**Consistencia del Diagnóstico (Índice DII) [{dii_pct:.1f}% - Sensibilidad Alta (Volátil)]:** Este indicador (Decision Instability Index) mide la robustez matemática del diagnóstico frente a cambios en la información de partida. Evalúa cuál es la probabilidad de que una variación menor en las evidencias documentales o en las respuestas de las entrevistas provoque una alteración o inestabilidad en la calificación final de madurez de la torre (valores bajos garantizan un diagnóstico altamente consistente y fiable). El valor registrado muestra una sensibilidad alta, sugiriendo que la escasez de evidencias o variaciones de criterio podrían alterar la nota asignada, por lo que se recomienda un análisis de contraste de evidencias confirmatorio."
                    )

                erc_val_num = erc if erc is not None else 0.0
                if erc_val_num >= 0.50:
                    glossary_items.append(
                        f"**Propagación de Fallos (ERC) [{erc_val_num:.3f} - Alta]:** Cuantifica el grado de influencia de esta torre sobre el resto de dominios tecnológicos. Un valor elevado indica que un incidente crítico en este perímetro se propagaría con gran facilidad hacia otras áreas conectadas. El índice confirma una influencia estructural alta, donde una degradación de servicio desestabilizaría de manera en cadena gran parte de la plataforma corporativa."
                    )
                elif erc_val_num >= 0.20:
                    glossary_items.append(
                        f"**Propagación de Fallos (ERC) [{erc_val_num:.3f} - Media]:** Cuantifica el grado de influencia de esta torre sobre el resto de dominios tecnológicos. Un valor elevado indica que un incidente crítico en este perímetro se propagaría con gran facilidad hacia otras áreas conectadas. La influencia estructural registrada es media; un incidente tendría un efecto moderado o contenido, afectando solo a sistemas inmediatamente adyacentes."
                    )
                else:
                    glossary_items.append(
                        f"**Propagación de Fallos (ERC) [{erc_val_num:.3f} - Baja/Aislada]:** Cuantifica el grado de influencia de esta torre sobre el resto de dominios tecnológicos. Un valor de propagación bajo indica una influencia estructural baja; un fallo técnico se contendría dentro de su propio perímetro sin arrastrar a otras torres tecnológicas clave."
                    )

                if spof_status == "SÍ":
                    glossary_items.append(
                        "**Punto Único de Fallo (SPOF) [SÍ - Crítico]:** Identifica si el dominio tecnológico actúa como un cuello de botella o eslabón débil de la infraestructura que, en caso de caída o compromiso técnico, detendría inmediatamente los flujos de servicio esenciales de la organización. La evaluación alerta de manera inequívoca que esta plataforma representa un cuello de botella o eslabón débil crítico sin redundancia suficiente, requiriendo acción de mitigación inmediata."
                    )
                else:
                    glossary_items.append(
                        "**Punto Único de Fallo (SPOF) [NO - Estable]:** Identifica si el dominio tecnológico actúa como un cuello de botella o eslabón débil de la infraestructura que, en caso de caída o compromiso técnico, detendría inmediatamente los flujos de servicio esenciales de la organización. La evaluación confirma que esta torre no actúa como un cuello de botella o eslabón débil único en la topología de la red operativa general."
                    )
                
                for item in glossary_items:
                    add_body_paragraph(doc, item, style="Bullet", text_color_rgb=text_color_rgb)
                
                add_spacer(doc, 20)
        except Exception as e:
            logger.info(f"⚠️ Error injecting systemic risk metrics: {e}")

    #


