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
    get_localized_list,
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
    global_band = ctx.get("global_band", t("band_defined", locale=doc_lang))
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
    chapter_3_title = t("chapter_3_title", locale=doc_lang)
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
        t("maturity_ref_framework_title", locale=doc_lang),
        level=3,
        primary_color_rgb=p_color_rgb,
    )

    p_ref_intro = add_body_paragraph(
        doc,
        t("cmmi_table_intro", locale=doc_lang),
        text_color_rgb=text_color_rgb
    )
    add_spacer(doc, 5)

    ref_table = doc.add_table(rows=1, cols=3)
    ref_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    ref_table.style = "Table Grid"
    
    headers_ref = [
        t("cmmi_table_header_level", locale=doc_lang),
        t("cmmi_table_header_range", locale=doc_lang),
        t("cmmi_table_header_desc", locale=doc_lang),
    ]
    for i, h_txt in enumerate(headers_ref):
        set_cell_text_custom(ref_table.rows[0].cells[i], h_txt, bold=True, font_size=8.5, color_rgb=RGBColor(255, 255, 255), align=WD_ALIGN_PARAGRAPH.CENTER)
        shade_cell(ref_table.rows[0].cells[i], p_color_hex)
        
    levels_data = [
        (t("cmmi_level_1_title", locale=doc_lang), t("cmmi_level_1_range", locale=doc_lang), t("cmmi_level_1_desc", locale=doc_lang)),
        (t("cmmi_level_2_title", locale=doc_lang), t("cmmi_level_2_range", locale=doc_lang), t("cmmi_level_2_desc", locale=doc_lang)),
        (t("cmmi_level_3_title", locale=doc_lang), t("cmmi_level_3_range", locale=doc_lang), t("cmmi_level_3_desc", locale=doc_lang)),
        (t("cmmi_level_4_title", locale=doc_lang), t("cmmi_level_4_range", locale=doc_lang), t("cmmi_level_4_desc", locale=doc_lang)),
        (t("cmmi_level_5_title", locale=doc_lang), t("cmmi_level_5_range", locale=doc_lang), t("cmmi_level_5_desc", locale=doc_lang)),
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
            actual_badge = t("current_state_badge", locale=doc_lang)
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
    score_formatted = format_number(gs_val, locale=doc_lang, decimals=2)
    explanation_str = t(
        "maturity_narrative_explanation",
        locale=doc_lang,
        score_formatted=score_formatted,
        global_band=global_band,
        global_reading=global_reading.strip() + " ",
    )
    add_body_paragraph(doc, explanation_str, text_color_rgb=text_color_rgb)
    add_spacer(doc, 15)

    # Standard Diagnostic and Performance Matrix by Technical Domain
    health_title = t("diagnosis_performance_matrix_title", locale=doc_lang)
    add_heading(doc, health_title, level=2, primary_color_rgb=p_color_rgb)
    add_body_paragraph(
        doc,
        t("diagnosis_performance_matrix_intro", locale=doc_lang),
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
            ),
            t("table_header_score_asis", locale=doc_lang),
            t(
                "table_header_maturity_level",
                locale=doc_lang,
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
                logger.info(f"✅ Radar chart auto-generated successfully at: {radar_path}")
        except Exception as ex:
            logger.info(f"⚠️ Failed to auto-generate radar chart: {ex}")

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
                    add_heading(doc, t("rage_traceability_heading", locale=doc_lang), level=2, primary_color_rgb=p_color_rgb)
                    intro_text = t("rage_traceability_intro", locale=doc_lang)
                    add_body_paragraph(doc, intro_text, text_color_rgb=text_color_rgb)
                    add_spacer(doc, 10)

                    for t_id, t_snap in valid_snapshots:
                        framework_name = t_snap.get("framework_name", t("rage_framework_fallback", locale=doc_lang))
                        score = t_snap.get("dynamic_score", 4.0)
                        quote = t_snap.get("evidence_quote", "")
                        url = t_snap.get("evidence_source_url", "")
                        local_path = t_snap.get("local_snapshot_path", "")

                        header_p = t("rage_tower_header", locale=doc_lang, tower_id=t_id, framework_name=framework_name, score=f"{score:,.1f}")
                        add_body_paragraph(doc, header_p, text_color_rgb=text_color_rgb)

                        quote_p = t("rage_evidence_extracted", locale=doc_lang, quote=quote)
                        add_body_paragraph(doc, quote_p, italic=True, text_color_rgb=text_color_rgb)

                        source_p = t("rage_reference_source", locale=doc_lang, url=url)
                        if local_path:
                            source_p += t("rage_local_vault", locale=doc_lang, local_path=local_path)
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
                just_hdr = t("asis_header_score_justification", locale=doc_lang)
                justification_cell_text = re.sub(
                    r"\*\*.*?(?:Nota|Score|Evaluation)\s*\(\d+[,.]\d+\):\*\*",
                    f"**{just_hdr}**",
                    justification_cell_text,
                )
                justification_cell_text = re.sub(
                    r".*?(?:Nota|Score|Evaluation)\s*\(\d+[,.]\d+\):",
                    just_hdr,
                    justification_cell_text,
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

    transversal_title = t("transversal_analysis_title", locale=doc_lang)
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
                add_heading(doc, t("section_interdependence_analysis", locale=doc_lang), level=2, primary_color_rgb=p_color_rgb)

                intro_text_inter = t("interdep_intro_text", locale=doc_lang)
                add_body_paragraph(doc, intro_text_inter, text_color_rgb=text_color_rgb)

                for b_text in get_localized_list("interdep_key_bullets", locale=doc_lang):
                    add_body_paragraph(doc, b_text, style="List Bullet", text_color_rgb=text_color_rgb)

                desc_rest = t("interdep_concl_text", locale=doc_lang)
                add_body_paragraph(doc, desc_rest, text_color_rgb=text_color_rgb)

                add_spacer(doc, 5)

                is_spof = (tower_id == spof_by_cascade or tower_id == spof_by_centrality)
                spof_status = "YES" if is_spof else "NO"
                spof_status_text = t("interdep_spof_yes", locale=doc_lang) if is_spof else t("interdep_spof_no", locale=doc_lang)
                dii_val = f"{dii_03:.1f}%" if dii_03 is not None else "0,0%"
                erc_val = f"{erc:.3f}" if erc is not None else "0,000"

                inter_table = doc.add_table(rows=1, cols=3)
                inter_table.alignment = WD_TABLE_ALIGNMENT.CENTER
                inter_table.style = "Table Grid"

                headers_inter = [
                    t("interdep_header_indicator", locale=doc_lang),
                    t("interdep_header_value", locale=doc_lang),
                    t("interdep_header_status", locale=doc_lang),
                ]
                for i, h_txt in enumerate(headers_inter):
                    set_cell_text_custom(
                        inter_table.rows[0].cells[i], h_txt, bold=True, font_size=10, color_rgb=RGBColor(255, 255, 255), align=WD_ALIGN_PARAGRAPH.CENTER
                    )
                    shade_cell(inter_table.rows[0].cells[i], p_color_hex)

                if business_criticality >= 80.0:
                    crit_label = t("interdep_status_extreme", locale=doc_lang)
                elif business_criticality >= 50.0:
                    crit_label = t("interdep_status_high", locale=doc_lang)
                else:
                    crit_label = t("interdep_status_medium", locale=doc_lang)

                if regulatory_compliance >= 80.0:
                    reg_label = t("interdep_status_critical", locale=doc_lang)
                elif regulatory_compliance >= 50.0:
                    reg_label = t("interdep_status_moderate", locale=doc_lang)
                else:
                    reg_label = t("interdep_status_standard", locale=doc_lang)

                if implementation_feasibility >= 60.0:
                    viab_label = t("interdep_status_viable", locale=doc_lang)
                else:
                    viab_label = t("interdep_status_complex", locale=doc_lang)

                if (dii_03 or 0) < 15.0:
                    dii_label = t("interdep_status_stable_diag", locale=doc_lang)
                elif (dii_03 or 0) < 30.0:
                    dii_label = t("interdep_status_mod_diag", locale=doc_lang)
                else:
                    dii_label = t("interdep_status_volatile_diag", locale=doc_lang)

                if (erc or 0) >= 0.50:
                    erc_label = t("interdep_status_high_influence", locale=doc_lang)
                elif (erc or 0) >= 0.20:
                    erc_label = t("interdep_status_moderate", locale=doc_lang)
                else:
                    erc_label = t("interdep_status_low_influence", locale=doc_lang)

                spof_label = t("interdep_status_bottleneck", locale=doc_lang) if is_spof else t("interdep_status_not_bottleneck", locale=doc_lang)

                spof_row_title = t("interdep_spof_title", locale=doc_lang)

                inter_data = [
                    (t("interdep_business_criticality_title", locale=doc_lang), f"{business_criticality:.1f}%", crit_label),
                    (t("interdep_reg_pressure_title", locale=doc_lang), f"{regulatory_compliance:.1f}%", reg_label),
                    (t("interdep_op_viability_title", locale=doc_lang), f"{implementation_feasibility:.1f}%", viab_label),
                    (t("interdep_dii_title", locale=doc_lang), dii_val, dii_label),
                    (t("interdep_erc_title", locale=doc_lang), erc_val, erc_label),
                    (spof_row_title, spof_status_text, spof_label)
                ]

                for r_idx, row_vals in enumerate(inter_data):
                    row = inter_table.add_row()
                    set_cell_text_custom(row.cells[0], row_vals[0], bold=True, font_size=10)
                    
                    if row_vals[0] == spof_row_title:
                        set_cell_text_custom(row.cells[1], row_vals[1], bold=True, font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
                        shade_cell(row.cells[1], "F2D9D9" if is_spof else "D9F2D9")
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
                run_g_title = p_gloss.add_run(t("interdep_gloss_title", locale=doc_lang))
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

                if is_spof:
                    glossary_items.append(t("gloss_spof_crit", locale=doc_lang))
                else:
                    glossary_items.append(t("gloss_spof_stable", locale=doc_lang))
                
                for item in glossary_items:
                    add_body_paragraph(doc, item, style="Bullet", text_color_rgb=text_color_rgb)
                
                add_spacer(doc, 20)
        except Exception as e:
            logger.info(f"⚠️ Error injecting systemic risk metrics: {e}")

    #


