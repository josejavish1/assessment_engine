"""Conclusions and Cost of Inaction chapter builder for Word DOCX."""
from __future__ import annotations

import logging
from pathlib import Path
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
from assessment_engine.adapters.compilers.asis_docx_primitives import (
    DocumentCompilationContext,
    add_body_paragraph,
    add_callout_box,
    add_heading,
    add_spacer,
    format_currency_custom,
    parse_and_append_markdown_section,
    set_cell_border_white,
    set_cell_text_custom,
)
from assessment_engine.infrastructure.localization import get_localized_list, t

logger = logging.getLogger(__name__)

def _compile_chapter_5_conclusions(doc: Any, ctx: DocumentCompilationContext) -> None:
    """Assemble and render Chapter 5: Conclusions and Cost of Inaction."""
    p_color_rgb = ctx["p_color_rgb"]
    text_color_rgb = ctx["text_color_rgb"]
    p_color_hex = ctx["p_color_hex"]
    alt_row_hex = ctx["alt_row_hex"]
    modules_dir = ctx["modules_dir"]
    currency = ctx["currency"]
    client_name = ctx.get("client_name", "Client")
    tower_name = ctx.get("tower_name", "Tower")
    doc_lang = ctx.get("doc_lang", "en")
    global_fair_ale = ctx["global_fair_ale"]
    total_p90 = ctx.get("total_p90", 0.0)
    t_sep = ctx.get("t_sep", ".")
    d_sep = ctx.get("d_sep", ",")
    formatted_ale_item = format_currency_custom(round(global_fair_ale), t_sep, d_sep)
    if d_sep and d_sep in formatted_ale_item:
        formatted_ale_item = formatted_ale_item.split(d_sep)[0]
    formatted_p90 = format_currency_custom(round(total_p90), t_sep, d_sep)
    if d_sep and d_sep in formatted_p90:
        formatted_p90 = formatted_p90.split(d_sep)[0]

    # Assemble and render Chapter 5: Conclusions and Cost of Inaction.
    add_heading(
        doc,
        t("conclusions_chapter_title", locale=doc_lang),
        level=1,
        primary_color_rgb=p_color_rgb,
    )

    # 5.1 Current Situation Diagnostic Conclusions
    parse_and_append_markdown_section(
        doc,
        modules_dir / "07_conclusiones.md",
        p_color_rgb,
        text_color_rgb,
        start_header=t("conclusions_diagnosis_title", locale=doc_lang),
        end_header=t("annex_header_cost_of_inaction", locale=doc_lang),
    )

    # 5.2 Decision Dilemma: Strategic Contrast Matrix
    matrix_title = t("decision_matrix_title", locale=doc_lang)
    add_heading(doc, matrix_title, level=2, primary_color_rgb=p_color_rgb)

    matrix_intro = t("decision_matrix_intro", locale=doc_lang)
    dec_headers = get_localized_list("decision_matrix_headers", locale=doc_lang)
    matrix_data = [
        (
            t("matrix_dim_1_title", locale=doc_lang),
            t("matrix_dim_1_path_a", locale=doc_lang, formatted_ale_item=formatted_ale_item, formatted_p90=formatted_p90, currency=currency),
            t("matrix_dim_1_path_b", locale=doc_lang),
        ),
        (
            t("matrix_dim_2_title", locale=doc_lang),
            t("matrix_dim_2_path_a", locale=doc_lang),
            t("matrix_dim_2_path_b", locale=doc_lang),
        ),
        (
            t("matrix_dim_3_title", locale=doc_lang),
            t("matrix_dim_3_path_a", locale=doc_lang),
            t("matrix_dim_3_path_b", locale=doc_lang),
        ),
        (
            t("matrix_dim_4_title", locale=doc_lang),
            t("matrix_dim_4_path_a", locale=doc_lang),
            t("matrix_dim_4_path_b", locale=doc_lang),
        ),
    ]

    add_body_paragraph(doc, matrix_intro, text_color_rgb=text_color_rgb)

    # Render decision matrix table
    dec_table = doc.add_table(rows=1, cols=3)
    dec_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    finalize_table(dec_table)
    dec_table.autofit = False
    dec_table.allow_autofit = False

    dec_col_widths = [Cm(3.0), Cm(6.71), Cm(6.71)] # Sums to 16.42 cm, standard page content area
    
    # Header cells
    resolver = DocxStyleResolver.get_default(language_code=doc_lang)
    for i, h_txt in enumerate(dec_headers):
        cell = dec_table.rows[0].cells[i]
        set_cell_text_custom(
            cell,
            h_txt,
            align=WD_ALIGN_PARAGRAPH.CENTER,
            no_bullets=True,
            typography_role=TypographyRole.TABLE_HEADER,
            color_role=SemanticColorRole.TEXT_INVERSE,
            resolver=resolver,
        )
        tcPr = cell._tc.get_or_add_tcPr()
        tcW = tcPr.find(qn('w:tcW'))
        if tcW is not None:
            tcPr.remove(tcW)
        tcW = OxmlElement('w:tcW')
        tcW.set(qn('w:type'), 'dxa')
        tcW.set(qn('w:w'), str(int(dec_col_widths[i].twips)))
        tcPr.append(tcW)
        shade_cell(cell, p_color_hex)

    for r_idx, row_data in enumerate(matrix_data):
        row = dec_table.add_row()
        row_bg = alt_row_hex if r_idx % 2 == 1 else "FFFFFF"
        for i in range(3):
            cell = row.cells[i]
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.LEFT
            
            # Format lists in matrix cells using robust inline markdown parser
            lines = row_data[i].split("\n")
            for l_idx, line in enumerate(lines):
                if l_idx > 0:
                    p = cell.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.LEFT

                # Clean bullet prefix from parsing
                line_clean = line
                if line_clean.startswith("• "):
                    line_clean = line_clean[2:]

                # Native inline parser for **bold** and *italic*
                bold_parts = line_clean.split("**")
                for b_idx, b_part in enumerate(bold_parts):
                    is_bold = b_idx % 2 == 1
                    italic_parts = b_part.split("*")
                    for i_idx, i_part in enumerate(italic_parts):
                        is_italic = i_idx % 2 == 1
                        run = p.add_run(i_part)
                        resolver.apply_run_style(
                            run,
                            typo_role=TypographyRole.TABLE_CELL,
                            bold_override=is_bold,
                        )
                        run.italic = is_italic

                p.paragraph_format.space_after = resolver.resolve_pt(TypographyRole.TABLE_CELL) if l_idx < len(lines) - 1 else resolver.resolve_pt(TypographyRole.BODY_REGULAR)
                if line.startswith("• "):
                    p.paragraph_format.left_indent = Inches(0.15)
                    # Prepend a bullet character
                    p.paragraph_format.left_indent = Inches(0.15)
            
            shade_cell(cell, row_bg)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            # Width enforcement
            tcPr = cell._tc.get_or_add_tcPr()
            tcW = tcPr.find(qn('w:tcW'))
            if tcW is not None:
                tcPr.remove(tcW)
            tcW = OxmlElement('w:tcW')
            tcW.set(qn('w:type'), 'dxa')
            tcW.set(qn('w:w'), str(int(dec_col_widths[i].twips)))
            tcPr.append(tcW)

    # 5.3 Financial Inaction Impact: Cumulative Cost of Inaction
    add_heading(doc, t("coi_section_title", locale=doc_lang), level=2, primary_color_rgb=p_color_rgb)
    
    # standard Actuarial Practice: Cumulative Adverse Multi-Year Stress Test (FRTB / Basel III)
    # Instead of multiplying the extreme worst-case annual loss by 3 or 5 (which implies experiencing 
    # 3 or 5 consecutive catastrophic years, an operational impossibility), we model exactly ONE 
    # catastrophic year (the CVaR/Expected Shortfall) plus N-1 average years (ALE) during that horizon.
    coi_adverse_3y = total_p90 + (global_fair_ale * 2)
    coi_adverse_5y = total_p90 + (global_fair_ale * 4)

    # Calculate accumulated costs
    ale_3y = format_currency_custom(global_fair_ale * 3, t_sep, d_sep).split(d_sep)[0]
    ale_5y = format_currency_custom(global_fair_ale * 5, t_sep, d_sep).split(d_sep)[0]
    p90_3y = format_currency_custom(coi_adverse_3y, t_sep, d_sep).split(d_sep)[0]
    p90_5y = format_currency_custom(coi_adverse_5y, t_sep, d_sep).split(d_sep)[0]

    coi_intro = t("coi_intro", locale=doc_lang)
    add_body_paragraph(doc, coi_intro, text_color_rgb=text_color_rgb)
    add_spacer(doc, 6)

    coi_accel = t("coi_risk_acceleration_narrative", locale=doc_lang)
    add_body_paragraph(doc, coi_accel, text_color_rgb=text_color_rgb)
    add_spacer(doc, 8)

    # 5.3 Multi-Year Executive Projection Table (1y, 3y, 5y)
    coi_table = doc.add_table(rows=1, cols=4)
    coi_table.alignment = WD_TABLE_ALIGNMENT.LEFT
    coi_table.style = "Table Grid"

    coi_headers = [
        t("coi_table_header_horizon", locale=doc_lang),
        t("coi_table_header_ale", locale=doc_lang),
        t("coi_table_header_p90", locale=doc_lang),
        t("coi_table_header_consequence", locale=doc_lang),
    ]
    for i, h_txt in enumerate(coi_headers):
        set_cell_text_custom(
            coi_table.rows[0].cells[i],
            h_txt,
            align=WD_ALIGN_PARAGRAPH.CENTER,
            typography_role=TypographyRole.TABLE_HEADER,
            color_role=SemanticColorRole.TEXT_INVERSE,
            resolver=resolver,
        )
        shade_cell(coi_table.rows[0].cells[i], p_color_hex)

    coi_col_widths = [Cm(3.5), Cm(3.0), Cm(3.0), Cm(6.9)]
    for i in range(4):
        coi_table.rows[0].cells[i].width = coi_col_widths[i]

    coi_rows_data = [
        (
            t("coi_horizon_1y", locale=doc_lang),
            f"{formatted_ale_item} {currency}",
            f"{formatted_p90} {currency}",
            t("coi_consequence_1y", locale=doc_lang),
        ),
        (
            t("coi_horizon_3y", locale=doc_lang),
            f"{ale_3y} {currency}",
            f"{p90_3y} {currency}",
            t("coi_consequence_3y", locale=doc_lang),
        ),
        (
            t("coi_horizon_5y", locale=doc_lang),
            f"{ale_5y} {currency}",
            f"{p90_5y} {currency}",
            t("coi_consequence_5y", locale=doc_lang),
        ),
    ]

    for r_idx, row_vals in enumerate(coi_rows_data):
        row = coi_table.add_row()
        set_cell_text_custom(row.cells[0], row_vals[0], bold=True, font_size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_text_custom(row.cells[1], row_vals[1], font_size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_text_custom(row.cells[2], row_vals[2], font_size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_text_custom(row.cells[3], row_vals[3], font_size=8.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

        for i in range(4):
            row.cells[i].width = coi_col_widths[i]
            if r_idx % 2 == 1:
                shade_cell(row.cells[i], alt_row_hex)

    autofit_table_to_contents(coi_table)
    add_spacer(doc, 20)

    # 5.4 Bridge and Handover to Modernization Blueprint (TO-BE)
    tobe_bridge_heading = t("tobe_bridge_title", locale=doc_lang)
    add_heading(doc, tobe_bridge_heading, level=2, primary_color_rgb=p_color_rgb)

    bridge_box_body = t("tobe_bridge_box_body", locale=doc_lang, tower_name=tower_name, client_name=client_name)
    add_callout_box(
        doc,
        bridge_box_body,
        bg_color_hex="F4F8FA",
        border_color_hex="0072BC",
        bold=False,
    )
    add_spacer(doc, 15)

    #


