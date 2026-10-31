"""Maturity profile, platform description, and systemic risk chapter builder for Word DOCX."""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
import re
from typing import Any

from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches

from assessment_engine.adapters.emitters.docx_style_resolver import DocxStyleResolver
from assessment_engine.domain.theme_registry import SemanticColorRole, TypographyRole
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
    from assessment_engine.domain.maturity_band import (
        ANNEX_MATURITY_BANDS,
        resolve_maturity_band,
    )

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
    style_resolver = DocxStyleResolver.get_default(language_code=doc_lang)
    for i, h_txt in enumerate([vocab["score_lbl"], vocab["maturity_lbl"]]):
        set_cell_text_custom(
            dash_table.rows[0].cells[i],
            h_txt,
            align=WD_ALIGN_PARAGRAPH.CENTER,
            typography_role=TypographyRole.TABLE_HEADER,
            color_role=SemanticColorRole.TEXT_INVERSE,
            resolver=style_resolver,
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

    # Dynamic Operational Interpretation of Maturity Score (replaces static textbook CMMI table)
    add_spacer(doc, 8)
    add_heading(
        doc,
        t("maturity_diagnostic_synthesis_title", locale=doc_lang),
        level=3,
        primary_color_rgb=p_color_rgb,
    )

    try:
        gs_val = float(global_score)
    except Exception:
        gs_val = 3.0

    target_benchmark = 3.0
    gap_score = f"{abs(gs_val - target_benchmark):.2f}"
    formatted_gs = format_number(gs_val, locale=doc_lang, decimals=2)
    band_label = resolve_maturity_band(gs_val, ANNEX_MATURITY_BANDS, locale=doc_lang)["label"]

    formatted_benchmark = format_number(3.0, locale=doc_lang, decimals=2)
    p_interp_text = t(
        "asis_band_explanation_narrative",
        locale=doc_lang,
        formatted_score=formatted_gs,
        band_label=band_label,
        gap_score=gap_score,
        benchmark_score=formatted_benchmark,
    )
    add_body_paragraph(doc, p_interp_text, text_color_rgb=text_color_rgb)
    add_spacer(doc, 12)

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
            align=WD_ALIGN_PARAGRAPH.CENTER,
            typography_role=TypographyRole.TABLE_HEADER,
            color_role=SemanticColorRole.TEXT_INVERSE,
            resolver=style_resolver,
        )
        shade_cell(health_table.rows[0].cells[i], p_color_hex)

    if b_data and "pillars_analysis" in b_data:
        from assessment_engine.domain.maturity_band import (
            ANNEX_MATURITY_BANDS,
            resolve_maturity_band,
        )

        from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
        resolver = get_taxonomy_resolver()

        for s_idx, p in enumerate(
            sorted(
                b_data.get("pillars_analysis", []),
                key=lambda item: item.get("score", 0.0),
            )
        ):
            bg = alt_row_hex if s_idx % 2 == 1 else "FFFFFF"
            raw_pname = p.get("pillar_name") or p.get("pilar_name", "Pillar")
            p_id = p.get("pillar_id") or p.get("pilar_id") or raw_pname
            p_name = resolver.resolve_pillar_by_any_reference(
                p_id, default=raw_pname, locale=doc_lang
            )
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
                raw_pname = p.get("pillar_name") or p.get("pilar_name", "Pillar")
                p_id = p.get("pillar_id") or p.get("pilar_id") or raw_pname
                p_label = resolver.resolve_pillar_by_any_reference(
                    p_id, default=raw_pname, locale=doc_lang
                )
                chart_pillars.append({
                    "pillar_label": p_label,
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
                    add_heading(
                        doc,
                        t("rage_traceability_heading", locale=doc_lang),
                        level=3,
                        primary_color_rgb=p_color_rgb,
                    )
                    intro_text = t("rage_traceability_intro", locale=doc_lang)
                    add_body_paragraph(doc, intro_text, text_color_rgb=text_color_rgb)
                    add_spacer(doc, 8)

                    bench_table = doc.add_table(rows=1, cols=3)
                    bench_table.alignment = WD_TABLE_ALIGNMENT.LEFT
                    bench_table.style = "Table Grid"

                    b_headers = [
                        t("header_framework_reference", locale=doc_lang),
                        t("header_industry_standard_score", locale=doc_lang),
                        t("header_benchmark_calibration_rationale", locale=doc_lang),
                    ]
                    for i, h_txt in enumerate(b_headers):
                        set_cell_text_custom(
                            bench_table.rows[0].cells[i],
                            h_txt,
                            align=WD_ALIGN_PARAGRAPH.CENTER,
                            typography_role=TypographyRole.TABLE_HEADER,
                            color_role=SemanticColorRole.TEXT_INVERSE,
                            resolver=style_resolver,
                        )
                        shade_cell(bench_table.rows[0].cells[i], p_color_hex)

                    for r_idx, (t_id, t_snap) in enumerate(valid_snapshots):
                        framework_name = t_snap.get(
                            "framework_name",
                            t("rage_framework_fallback", locale=doc_lang),
                        )
                        score = t_snap.get("dynamic_score", 3.0)
                        justification = t_snap.get(
                            "justification_text",
                            t_snap.get("evidence_quote", ""),
                        )
                        if "Runtime sectorial compliance research substantiates that:" in justification:
                            justification = re.sub(
                                r'Runtime sectorial compliance research substantiates that:\s*"([^"]+)"',
                                r"\1",
                                justification,
                            )
                            justification = re.sub(r"Cita Oficial Online:.*", "", justification).strip()

                        row = bench_table.add_row()
                        set_cell_text_custom(
                            row.cells[0],
                            framework_name,
                            bold=True,
                            font_size=8.5,
                        )
                        score_label = f"{score:,.1f} / 5.0"
                        set_cell_text_custom(
                            row.cells[1],
                            score_label,
                            font_size=8.5,
                            align=WD_ALIGN_PARAGRAPH.CENTER,
                        )
                        set_cell_text_custom(
                            row.cells[2],
                            justification,
                            font_size=8.5,
                            align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                        )
                        if r_idx % 2 == 1:
                            for cell in row.cells:
                                shade_cell(cell, alt_row_hex)

                    autofit_table_to_contents(bench_table)
                    add_spacer(doc, 15)

                    # Render Regulatory Compliance & Operational Resilience Scorecard
                    from assessment_engine.adapters.generate_asis_markdown_modules import _ASIS_ANNEX_DATA
                    reg_scorecards = _ASIS_ANNEX_DATA.get("tower_regulatory_scorecards", {})
                    tower_card_dict = reg_scorecards.get(tower_id, reg_scorecards.get("default", {}))
                    card_rows = tower_card_dict.get(doc_lang, tower_card_dict.get("en", []))

                    if card_rows:
                        add_heading(
                            doc,
                            t("regulatory_scorecard_title", locale=doc_lang),
                            level=3,
                            primary_color_rgb=p_color_rgb,
                        )
                        add_spacer(doc, 6)

                        reg_table = doc.add_table(rows=1, cols=4)
                        reg_table.alignment = WD_TABLE_ALIGNMENT.LEFT
                        reg_table.style = "Table Grid"

                        reg_headers = [
                            t("header_regulatory_framework", locale=doc_lang),
                            t("header_framework_core_requirement", locale=doc_lang),
                            t("header_diagnosed_operational_posture", locale=doc_lang),
                            t("header_compliance_risk_level", locale=doc_lang),
                        ]
                        for i, h_txt in enumerate(reg_headers):
                            set_cell_text_custom(
                                reg_table.rows[0].cells[i],
                                h_txt,
                                align=WD_ALIGN_PARAGRAPH.CENTER,
                                typography_role=TypographyRole.TABLE_HEADER,
                                color_role=SemanticColorRole.TEXT_INVERSE,
                                resolver=style_resolver,
                            )
                            shade_cell(reg_table.rows[0].cells[i], p_color_hex)

                        reg_col_widths = [Cm(3.8), Cm(4.2), Cm(6.0), Cm(2.4)]
                        for i in range(4):
                            reg_table.rows[0].cells[i].width = reg_col_widths[i]

                        for r_idx, r_data in enumerate(card_rows):
                            row = reg_table.add_row()
                            fw_name, req_txt, diag_txt, status_lbl, badge_bg = r_data[0], r_data[1], r_data[2], r_data[3], r_data[4]

                            set_cell_text_custom(row.cells[0], fw_name, bold=True, font_size=8, color_role=SemanticColorRole.TEXT_PRIMARY, resolver=style_resolver)
                            set_cell_text_custom(row.cells[1], req_txt, font_size=8, color_role=SemanticColorRole.TEXT_PRIMARY, resolver=style_resolver, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
                            set_cell_text_custom(row.cells[2], diag_txt, font_size=8, color_role=SemanticColorRole.TEXT_PRIMARY, resolver=style_resolver, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
                            set_cell_text_custom(row.cells[3], status_lbl, bold=True, font_size=8, color_role=SemanticColorRole.BRAND_PRIMARY, resolver=style_resolver, align=WD_ALIGN_PARAGRAPH.CENTER)

                            for i in range(4):
                                row.cells[i].width = reg_col_widths[i]
                                if r_idx % 2 == 1:
                                    shade_cell(row.cells[i], alt_row_hex)
                            shade_cell(row.cells[3], badge_bg)

                        autofit_table_to_contents(reg_table)
                        add_spacer(doc, 15)
        except Exception as ex:
            logger.info(f"⚠️  [RAGE] Failed to inject RAGE report into main document: {ex}")

    # Assemble and render Section 3.3: Score Justification Matrix; left-aligned, omits 'TO-BE Target' column.
    csv_mat_path = modules_dir / "04_matriz_madurez.csv"
    if csv_mat_path.exists():
        score_just_title = t("score_justification_section_title", locale=doc_lang)
        add_heading(doc, score_just_title, level=3, primary_color_rgb=p_color_rgb)

        mat_table = doc.add_table(rows=1, cols=3)
        mat_table.alignment = WD_TABLE_ALIGNMENT.LEFT
        mat_table.style = "Table Grid"

        headers_mat = vocab["justification_table_headers"]
        mat_col_widths = [Cm(4.0), Cm(2.5), Cm(10.0)]
        for i, h_txt in enumerate(headers_mat):
            cell = mat_table.rows[0].cells[i]
            set_cell_text_custom(
                cell,
                h_txt,
                align=WD_ALIGN_PARAGRAPH.CENTER,
                typography_role=TypographyRole.TABLE_HEADER,
                color_role=SemanticColorRole.TEXT_INVERSE,
                resolver=style_resolver,
            )
            shade_cell(cell, p_color_hex)
            cell.width = mat_col_widths[i]

        with open(csv_mat_path, "r", encoding="utf-8") as cf:
            reader = csv.reader(cf, delimiter=";")
            next(reader)  #

            for r_idx, row_data in enumerate(reader):
                row = mat_table.add_row()
                # Col 0: Pillar name
                set_cell_text_custom(
                    row.cells[0], row_data[0], bold=True, font_size=8.5, color_role=SemanticColorRole.TEXT_PRIMARY, resolver=style_resolver
                )
                
                # Col 1: Score & Qualitative Band
                sc_str = row_data[1].strip()
                try:
                    sc_val = float(sc_str.split()[0].replace(",", "."))
                    band_lbl = resolve_maturity_band(sc_val, ANNEX_MATURITY_BANDS, locale=doc_lang)["label"]
                    display_sc = f"{sc_val:.2f} / 5.00\n({band_lbl})"
                except Exception:
                    display_sc = sc_str

                set_cell_text_custom(
                    row.cells[1],
                    display_sc,
                    bold=True,
                    font_size=8.5,
                    align=WD_ALIGN_PARAGRAPH.CENTER,
                    color_role=SemanticColorRole.TEXT_PRIMARY,
                    resolver=style_resolver,
                    no_bullets=True,
                )
                
                # Col 2: Executive Justification Blocks (Bottleneck + Unlocking Lever)
                cell_just = row.cells[2]
                cell_just.text = ""
                blocks = [b.strip() for b in row_data[2].split("\n\n") if b.strip()]
                for b_idx, block in enumerate(blocks):
                    clean_block = block.replace("• ", "").strip()
                    p = cell_just.paragraphs[0] if b_idx == 0 else cell_just.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    style_resolver.apply_paragraph_typography(p, TypographyRole.BODY_REGULAR)
                    p.paragraph_format.left_indent = Inches(0.12)
                    p.paragraph_format.first_line_indent = Inches(-0.12)

                    # Extract bold label between **...**
                    if "**" in clean_block:
                        match = re.match(r"\*\*(.*?)\*\*:?\s*(.*)", clean_block, re.DOTALL)
                        if match:
                            lbl_txt = match.group(1).rstrip(":").replace("**", "").replace("*", "").strip()
                            body_txt = match.group(2).replace("**", "").replace("*", "").strip()
                        else:
                            lbl_txt = ""
                            body_txt = clean_block.replace("**", "").replace("*", "").strip()
                    elif ":" in clean_block:
                        parts = clean_block.split(":", 1)
                        lbl_txt = parts[0].replace("**", "").replace("*", "").strip()
                        body_txt = parts[1].replace("**", "").replace("*", "").strip()
                    else:
                        lbl_txt = ""
                        body_txt = clean_block.replace("**", "").replace("*", "").strip()

                    if lbl_txt:
                        r_lbl = p.add_run(f"• {lbl_txt}: ")
                        style_resolver.apply_run_style(
                            r_lbl,
                            typo_role=TypographyRole.TABLE_CELL,
                            color_role=SemanticColorRole.TEXT_PRIMARY,
                            bold_override=True,
                        )
                    else:
                        r_bullet = p.add_run("• ")
                        style_resolver.apply_run_style(
                            r_bullet,
                            typo_role=TypographyRole.TABLE_CELL,
                            color_role=SemanticColorRole.TEXT_PRIMARY,
                            bold_override=True,
                        )

                    r_body = p.add_run(body_txt)
                    style_resolver.apply_run_style(
                        r_body,
                        typo_role=TypographyRole.TABLE_CELL,
                        color_role=SemanticColorRole.TEXT_PRIMARY,
                    )

                for c_idx, w in enumerate(mat_col_widths):
                    row.cells[c_idx].width = w

                if r_idx % 2 == 1:
                    for cell in row.cells:
                        shade_cell(cell, alt_row_hex)

        autofit_table_to_contents(mat_table)
        add_spacer(doc, 20)
    elif b_data and b_data.get("pillars_analysis"):
        from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
            derive_in_memory_maturity_matrix,
        )
        score_just_title = t("score_justification_section_title", locale=doc_lang)
        add_heading(doc, score_just_title, level=3, primary_color_rgb=p_color_rgb)

        mat_table = doc.add_table(rows=1, cols=3)
        mat_table.alignment = WD_TABLE_ALIGNMENT.LEFT
        mat_table.style = "Table Grid"

        headers_mat = vocab["justification_table_headers"]
        mat_col_widths = [Cm(4.0), Cm(2.5), Cm(10.0)]
        for i, h_txt in enumerate(headers_mat):
            cell = mat_table.rows[0].cells[i]
            set_cell_text_custom(
                cell,
                h_txt,
                align=WD_ALIGN_PARAGRAPH.CENTER,
                typography_role=TypographyRole.TABLE_HEADER,
                color_role=SemanticColorRole.TEXT_INVERSE,
                resolver=style_resolver,
            )
            shade_cell(cell, p_color_hex)
            cell.width = mat_col_widths[i]

        in_mem_rows = derive_in_memory_maturity_matrix(b_data, doc_lang=doc_lang)
        for r_idx, r_data in enumerate(in_mem_rows):
            row = mat_table.add_row()
            set_cell_text_custom(
                row.cells[0], r_data["pillar_name"], bold=True, font_size=8.5, color_role=SemanticColorRole.TEXT_PRIMARY, resolver=style_resolver
            )
            display_sc = f"{r_data['score_formatted']} / 5.00\n({r_data['band_label']})"
            set_cell_text_custom(
                row.cells[1],
                display_sc,
                bold=True,
                font_size=8.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
                color_role=SemanticColorRole.TEXT_PRIMARY,
                resolver=style_resolver,
                no_bullets=True,
            )
            set_cell_text_custom(
                row.cells[2],
                r_data["justification"],
                font_size=8.5,
                color_role=SemanticColorRole.TEXT_PRIMARY,
                resolver=style_resolver,
                no_bullets=True,
            )
            for c_idx, w in enumerate(mat_col_widths):
                row.cells[c_idx].width = w
            if r_idx % 2 == 1:
                for cell in row.cells:
                    shade_cell(cell, alt_row_hex)

        autofit_table_to_contents(mat_table)
        add_spacer(doc, 20)

    # 3.4 Structural Technical Debt and Platform Bottlenecks
    debt_section_title = t("structural_debt_section_title", locale=doc_lang)
    add_heading(doc, debt_section_title, level=2, primary_color_rgb=p_color_rgb)

    cca = b_data.get("cross_capabilities_analysis", {}) if b_data else {}
    critical_debt = cca.get("critical_technical_debt", "")
    patterns = cca.get("common_deficiency_patterns", [])

    if critical_debt:
        add_callout_box(
            doc,
            critical_debt,
            bg_color_hex="F4F8FA",
            border_color_hex="0072BC",
            bold=False,
        )
        add_spacer(doc, 10)

    if patterns:
        vectors_title = t("structural_friction_vectors_title", locale=doc_lang)
        add_heading(doc, vectors_title, level=3, primary_color_rgb=p_color_rgb)

        vec_table = doc.add_table(rows=1, cols=2)
        vec_table.alignment = WD_TABLE_ALIGNMENT.LEFT
        vec_table.style = "Table Grid"

        vec_headers = [
            t("header_inefficiency_vector", locale=doc_lang),
            t("header_business_operational_impact", locale=doc_lang),
        ]
        for i, h_txt in enumerate(vec_headers):
            set_cell_text_custom(
                vec_table.rows[0].cells[i],
                h_txt,
                align=WD_ALIGN_PARAGRAPH.CENTER,
                typography_role=TypographyRole.TABLE_HEADER,
                color_role=SemanticColorRole.TEXT_INVERSE,
                resolver=style_resolver,
            )
            shade_cell(vec_table.rows[0].cells[i], p_color_hex)

        vec_table.rows[0].cells[0].width = Cm(5.0)
        vec_table.rows[0].cells[1].width = Cm(11.4)

        if isinstance(patterns, str):
            patterns = [patterns]

        for p_idx, pat in enumerate(patterns):
            pat_str = str(pat).strip()
            if ":" in pat_str:
                parts = pat_str.split(":", 1)
                v_name = parts[0].replace("**", "").replace("*", "").strip()
                v_desc = parts[1].strip()
            else:
                words = pat_str.split()
                v_name = " ".join(words[:4]).rstrip(".,;:")
                v_desc = pat_str

            row = vec_table.add_row()
            set_cell_text_custom(row.cells[0], v_name, bold=True, font_size=8.5)
            set_cell_text_custom(row.cells[1], v_desc, font_size=8.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

            row.cells[0].width = Cm(5.0)
            row.cells[1].width = Cm(11.4)

            if p_idx % 2 == 1:
                shade_cell(row.cells[0], alt_row_hex)
                shade_cell(row.cells[1], alt_row_hex)

        autofit_table_to_contents(vec_table)
        add_spacer(doc, 20)
    else:
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
                        inter_table.rows[0].cells[i],
                        h_txt,
                        align=WD_ALIGN_PARAGRAPH.CENTER,
                        typography_role=TypographyRole.TABLE_HEADER,
                        color_role=SemanticColorRole.TEXT_INVERSE,
                        resolver=style_resolver,
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
                style_resolver.apply_paragraph_typography(p_gloss, TypographyRole.BODY_REGULAR)
                run_g_title = p_gloss.add_run(t("interdep_gloss_title", locale=doc_lang))
                style_resolver.apply_run_style(
                    run_g_title,
                    typo_role=TypographyRole.BODY_STRONG,
                    color_role=SemanticColorRole.TEXT_PRIMARY,
                    bold_override=True,
                )

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


