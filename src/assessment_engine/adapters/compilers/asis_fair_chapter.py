"""Actuarial Open FAIR quantitative risk matrix chapter builder for Word DOCX."""
from __future__ import annotations

import csv
import json
import logging
import os
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
    set_cell_text,
    shade_cell,
)
from assessment_engine.infrastructure.localization import (
    get_localized_list,
    format_currency,
    format_number,
    t,
)
from assessment_engine.infrastructure.text_utils import clean_text_for_word
from assessment_engine.adapters.compilers.asis_docx_primitives import (
    COLOR_BLUE,
    Chapter4Result,
    DocumentCompilationContext,
    _add_markdown_bullet,
    add_appendix_subheading,
    add_body_paragraph,
    add_callout_box,
    add_heading,
    add_spacer,
    format_currency_custom,
    parse_and_append_markdown_section,
    set_cell_border_white,
    set_cell_text_custom,
)

logger = logging.getLogger(__name__)

def _compile_chapter_4_fair_risk_matrix(doc: Any, ctx: DocumentCompilationContext) -> Chapter4Result:
    """Assemble and render Chapter 4: Quantitative Risk Matrix."""
    p_color_rgb = ctx["p_color_rgb"]
    text_color_rgb = ctx["text_color_rgb"]
    p_color_hex = ctx["p_color_hex"]
    alt_row_hex = ctx["alt_row_hex"]
    vocab = ctx["vocab"]
    modules_dir = ctx["modules_dir"]
    doc_lang = ctx["doc_lang"]
    currency = ctx.get("currency", "€")
    is_critical = ctx.get("is_critical", False)
    global_fair_ale = ctx["global_fair_ale"]
    b_data = ctx.get("b_data", {})
    payload_path = ctx.get("payload_path", Path("."))
    tower_dir_obj = ctx["tower_dir_obj"]
    payload_path = ctx["payload_path"]
    client_name = ctx["client_name"]
    reg_name = ctx.get("reg_name", t("applicable_regulations_default", locale=doc_lang))
    industry_name = ctx.get(
        "industry_name",
        t("standard_sector_label", locale=doc_lang),
    )

    total_p90 = 0.0
    formatted_ale_item = "0"
    formatted_p90 = "0"
    t_sep = vocab.get("thousands_sep", ".")
    d_sep = vocab.get("decimal_sep", ",")

    def add_markdown_bullet_local(text: str, space_after: int = 4) -> Any:
        return _add_markdown_bullet(doc, text, text_color_rgb, space_after)

    # Assemble and render Chapter 4: Quantitative Risk Matrix.
    #
    add_heading(doc, vocab["risk_matrix_title"], level=1, primary_color_rgb=p_color_rgb)

    # Format the Annualized Loss Expectancy (ALE) value. Localization logic is isolated in a separate function, per requirement 2.
    t_sep = vocab.get("thousands_sep", ".")
    d_sep = vocab.get("decimal_sep", ",")
    formatted_ale = format_currency_custom(global_fair_ale, t_sep, d_sep)

    # Load dynamic SRE hourly rate and currency symbol from custom calibration if available (FAIR-MAM)
    import os
    client_id = os.environ.get("ASSESSMENT_CLIENT_ID", "generic_client")
    tower_id = b_data.get("document_meta", {}).get("tower_code", "T2")
    custom_profile_path = Path(f"working/{client_id}/{tower_id}/custom_risk_profile.json")
    if not custom_profile_path.exists():
        for t_code in ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"]:
            temp_path = Path(f"working/{client_id}/{t_code}/custom_risk_profile.json")
            if temp_path.exists():
                custom_profile_path = temp_path
                break

    custom_calibration = {}
    if custom_profile_path.exists():
        try:
            with open(custom_profile_path, "r", encoding="utf-8-sig") as cf:
                custom_calibration = json.load(cf)
        except (OSError, ValueError, KeyError, AttributeError) as ex:

            logger.debug(f"[Fallback] Handled exception: {ex}")

    from assessment_engine.infrastructure.config_loader import load_rate_card
    base_sre_rate = float(load_rate_card().get("tarifas_hora", {}).get("tecnico_medio", 36.0))
    sre_rate = round(float(custom_calibration.get("hourly_rate_sre_eur", base_sre_rate)))
    currency = (
        ctx.get("currency")
        or custom_calibration.get("currency_symbol")
    )
    if not currency:
        from assessment_engine.adapters.generate_asis_markdown_modules import resolve_client_currency_context
        currency, _ = resolve_client_currency_context(client_id)

    # Calculate aggregate Tail Risk (P90 and Max Probable Loss)
    total_p90 = 0.0
    total_max = 0.0
    try:
        for pillar in b_data.get("pillars_analysis", []):
            for hc in pillar.get("health_check_asis", []):
                total_p90 += hc.get("fair_p90_score", 0.0) or 0.0
                total_max += hc.get("fair_max_score", 0.0) or 0.0
    except (OSError, ValueError, KeyError, AttributeError) as ex:

        logger.debug(f"[Fallback] Handled exception: {ex}")
    
    formatted_p90 = format_currency_custom(total_p90, t_sep, d_sep).split(d_sep)[0]
    formatted_max = format_currency_custom(total_max, t_sep, d_sep).split(d_sep)[0]

    intro_prose_p1 = t("fair_intro_prose_p1", locale=doc_lang)
    intro_prose_p2 = t("fair_intro_prose_p2", locale=doc_lang, client_name=client_name, formatted_ale=formatted_ale, currency=currency)
    intro_prose_p3 = t("fair_intro_prose_p3", locale=doc_lang, reg_name=reg_name, formatted_p90=formatted_p90, formatted_max=formatted_max, currency=currency)
    intro_prose_p4 = t("fair_intro_prose_p4", locale=doc_lang, reg_name=reg_name)
    intro_prose_p5 = t("fair_intro_prose_p5", locale=doc_lang, client_name=client_name, sre_rate=sre_rate, currency=currency)

    add_body_paragraph(doc, intro_prose_p1, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, intro_prose_p2, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, intro_prose_p3, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, intro_prose_p4, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, intro_prose_p5, text_color_rgb=text_color_rgb, italic=True)

    def add_markdown_bullet_local(text: str, space_after: int = 4) -> Any:
        return _add_markdown_bullet(doc, text, text_color_rgb, space_after)

    add_appendix_subheading(doc, t("value_hexagon_heading", locale=doc_lang), primary_color_rgb=p_color_rgb)
    lever_intro = t("value_hexagon_intro", locale=doc_lang)
    add_body_paragraph(doc, lever_intro, text_color_rgb=text_color_rgb)
    for l_idx, lever_text in enumerate(get_localized_list("value_hexagon_bullets", locale=doc_lang)):
        add_markdown_bullet_local(lever_text, space_after=12 if l_idx == 5 else 3)

    #
    csv_risks_path = modules_dir / "06_matriz_riesgos_fair.csv"
    risks_data_list = []
    risks_by_pilar = {}

    if csv_risks_path.exists():
        with open(csv_risks_path, "r", encoding="utf-8") as cf:
            reader = csv.reader(cf, delimiter=";")
            next(reader)
            for r_idx, row_data in enumerate(reader):
                pilar_full_name = row_data[0].split(" - ")[0]
                r_item = {
                    "id": f"RVS{r_idx + 1:02d}",
                    "pilar": pilar_full_name,
                    "capability": row_data[0].split(" - ")[1]
                    if " - " in row_data[0]
                    else row_data[0],
                    "finding": row_data[1],
                    "business_risk": row_data[2],
                    "tef": float(row_data[3]),
                    "lm": float(row_data[4]),
                    "ale": float(row_data[5]),
                    "prioritization_rationale": row_data[6]
                    if len(row_data) > 6
                    else None,  #
                }
                risks_data_list.append(r_item)

                if pilar_full_name not in risks_by_pilar:
                    risks_by_pilar[pilar_full_name] = []
                risks_by_pilar[pilar_full_name].append(r_item)

    # Assemble and render Section 5.1: 5x5 Heatmap as a centered, native table mosaic.
    industry_name = ctx.get("industry", "Infraestructura y Operaciones")
    if risks_data_list:
        add_heading(
            doc, vocab["exposure_summary_title"], level=2, primary_color_rgb=p_color_rgb
        )

        sec_intro_p1 = t("fair_heatmap_sec_p1", locale=doc_lang)
        sec_intro_p2 = t("fair_heatmap_sec_p2", locale=doc_lang, client_name=client_name, industry_name=industry_name)
        sec_intro_p3 = t("fair_heatmap_sec_p3", locale=doc_lang)
            
        add_body_paragraph(doc, sec_intro_p1, text_color_rgb=text_color_rgb)
        add_body_paragraph(doc, sec_intro_p2, text_color_rgb=text_color_rgb)
        add_body_paragraph(doc, sec_intro_p3, text_color_rgb=text_color_rgb)
        add_spacer(doc, 15)

        matrix_cells = {r: {c: [] for c in range(1, 6)} for r in range(5, 0, -1)}
        for r in risks_data_list:
            r_tef = min(5, max(1, int(round(r["tef"]))))
            r_lm = min(5, max(1, int(round(r["lm"]))))
            matrix_cells[r_tef][r_lm].append(r["id"])

        # Initialize a 6x6 table (5x5 data grid plus headers). The table is centered and set to full page width.
        heatmap_table = doc.add_table(rows=6, cols=6)
        heatmap_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        finalize_table(heatmap_table)

        #
        cell_0_0 = heatmap_table.rows[0].cells[0]
        set_cell_text_custom(
            cell_0_0,
            "TEF \\ LM",
            bold=True,
            font_size=9,
            align=WD_ALIGN_PARAGRAPH.CENTER,
            color_rgb=RGBColor(255, 255, 255),
            no_bullets=True,
        )
        shade_cell(cell_0_0, COLOR_BLUE)
        set_cell_border_white(cell_0_0)
        cell_0_0.width = Inches(1.3)  # Slightly wider for inline ranges
        cell_0_0.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        
        for col_idx in range(1, 6):
            if is_critical:
                lm_ranges = {
                    1: f"< 1k {currency}",
                    2: f"1k - 10k {currency}",
                    3: f"10k - 50k {currency}",
                    4: f"50k - 300k {currency}",
                    5: f"250k - 1.5M {currency}",
                }
            else:
                lm_ranges = {
                    1: f"< 1k {currency}",
                    2: f"1k - 5k {currency}",
                    3: f"5k - 25k {currency}",
                    4: f"25k - 100k {currency}",
                    5: f"100k - 500k {currency}",
                }
            lm_lbl = f"LM {col_idx}\n({lm_ranges[col_idx]})"
            cell = heatmap_table.rows[0].cells[col_idx]
            set_cell_text_custom(
                cell,
                lm_lbl,
                bold=True,
                font_size=9,
                align=WD_ALIGN_PARAGRAPH.CENTER,
                color_rgb=RGBColor(255, 255, 255),
                no_bullets=True,
            )
            shade_cell(cell, COLOR_BLUE)
            set_cell_border_white(cell)
            cell.width = Inches(1.04)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

        # Populate the 5x5 data matrix with content, ensuring it fills the full width of the table.
        for row_idx, tef_val in enumerate(range(5, 0, -1), 1):
            tef_ranges = {
                5: t("tef_annual_freq_5", locale=doc_lang),
                4: t("tef_annual_freq_4", locale=doc_lang),
                3: t("tef_annual_freq_3", locale=doc_lang),
                2: t("tef_annual_freq_2", locale=doc_lang),
                1: t("tef_annual_freq_1", locale=doc_lang),
            }
            tef_lbl = f"TEF {tef_val}\n({tef_ranges[tef_val]})"
            cell_header = heatmap_table.rows[row_idx].cells[0]
            set_cell_text_custom(
                cell_header,
                tef_lbl,
                bold=True,
                font_size=9,
                align=WD_ALIGN_PARAGRAPH.CENTER,
                color_rgb=RGBColor(255, 255, 255),
                no_bullets=True,
            )
            shade_cell(cell_header, COLOR_BLUE)
            set_cell_border_white(cell_header)
            cell_header.width = Inches(1.3)
            cell_header.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            for col_idx, lm_val in enumerate(range(1, 6), 1):
                cell = heatmap_table.rows[row_idx].cells[col_idx]

                # Configure table dimensions to create a fixed, full-width mosaic layout.
                cell.width = Inches(1.04)
                heatmap_table.rows[row_idx].height = Cm(0.4)

                cell_risks = matrix_cells[tef_val][lm_val]
                cell_text = ", ".join(cell_risks) if cell_risks else "-"

                set_cell_text_custom(
                    cell,
                    cell_text,
                    bold=True,
                    font_size=8,
                    align=WD_ALIGN_PARAGRAPH.CENTER,
                )
                set_cell_border_white(cell)
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

                severity = tef_val * lm_val
                if severity >= 15:
                    shade_cell(cell, "FADBD8")  #
                elif severity >= 8:
                    shade_cell(cell, "FCF3CF")  #
                else:
                    shade_cell(cell, "D5F5E3")  #

        heatmap_table.alignment = WD_TABLE_ALIGNMENT.CENTER  # Recalculate cell content alignment. This is required because the initial auto-fit operation may not apply alignment correctly.
        add_spacer(doc, 20)

    # Build a lookup map from blueprint payload findings for detailed FAIR metrics
    fair_lookup = {}
    if payload_path.exists():
        try:
            for pillar in b_data.get("pillars_analysis", []):
                for hc in pillar.get("health_check_asis", []):
                    cap_name = hc.get("capability")
                    if cap_name:
                        fair_lookup[cap_name] = {
                            "p90": hc.get("fair_p90_score", 0.0),
                            "min": hc.get("fair_min_score", 0.0),
                            "max": hc.get("fair_max_score", 0.0),
                        }
        except (OSError, ValueError, KeyError, AttributeError) as ex:

            logger.debug(f"[Fallback] Handled exception: {ex}")

    # Assemble and render Section 5.3: Detailed Risk Register; left-aligned content per requirement 4.2.
    add_heading(
        doc, vocab["detailed_risks_title"], level=2, primary_color_rgb=p_color_rgb
    )

    detailed_risks_intro = t("fair_detailed_risks_intro", locale=doc_lang)
    guide_intro = t("fair_guide_intro", locale=doc_lang)
    add_body_paragraph(doc, detailed_risks_intro, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, guide_intro, text_color_rgb=text_color_rgb)

    for g_bullet in get_localized_list("fair_guide_bullets", locale=doc_lang):
        add_body_paragraph(doc, g_bullet, style="List Bullet", text_color_rgb=text_color_rgb)

    add_spacer(doc, 15)

    # Dynamic Relative Materiality Threshold Calculation (Statistical Mean ALE)
    total_risks_count = len(risks_data_list)
    local_mean_ale = (sum(r["ale"] for r in risks_data_list) / total_risks_count) if total_risks_count > 0 else 0.0
    
    tier1_threshold = local_mean_ale * 1.5
    tier2_threshold = local_mean_ale * 0.5

    tier1_risks = [r for r in risks_data_list if r["ale"] >= tier1_threshold]
    tier2_risks = [r for r in risks_data_list if tier2_threshold <= r["ale"] < tier1_threshold]
    tier3_risks = [r for r in risks_data_list if r["ale"] < tier2_threshold]

    # Sort each tier by ALE descending to guarantee standard prioritization
    tier1_risks.sort(key=lambda x: x["ale"], reverse=True)
    tier2_risks.sort(key=lambda x: x["ale"], reverse=True)
    tier3_risks.sort(key=lambda x: x["ale"], reverse=True)

    t_sep1 = format_currency_custom(tier1_threshold, t_sep, d_sep).split(d_sep)[0]
    t_sep2 = format_currency_custom(tier2_threshold, t_sep, d_sep).split(d_sep)[0]
    
    tiers_config = [
        (
            t("tier1_portfolio_title", locale=doc_lang),
            tier1_risks,
            t("tier1_portfolio_desc", locale=doc_lang, t_sep1=t_sep1, currency=currency),
        ),
        (
            t("tier2_portfolio_title", locale=doc_lang),
            tier2_risks,
            t("tier2_portfolio_desc", locale=doc_lang, t_sep2=t_sep2, t_sep1=t_sep1, currency=currency),
        ),
        (
            t("tier3_portfolio_title", locale=doc_lang),
            tier3_risks,
            t("tier3_portfolio_desc", locale=doc_lang, t_sep2=t_sep2, currency=currency),
        ),
    ]

    for title, p_risks, p_desc in tiers_config:
        add_heading(
            doc,
            title,
            level=3,
            primary_color_rgb=p_color_rgb,
        )
        add_body_paragraph(doc, p_desc, text_color_rgb=text_color_rgb)
        add_spacer(doc, 10)

        if not p_risks:
            empty_msg = t("msg_no_tier_vulnerabilities", locale=doc_lang)
            add_body_paragraph(doc, empty_msg, text_color_rgb=text_color_rgb)
            add_spacer(doc, 15)
            continue

        table_risks = doc.add_table(rows=1, cols=3)
        table_risks.alignment = WD_TABLE_ALIGNMENT.LEFT
        finalize_table(table_risks)
        table_risks.autofit = False
        table_risks.allow_autofit = False

        tblPr = table_risks._tbl.tblPr
        if tblPr is None:
            tblPr = OxmlElement('w:tblPr')
            table_risks._tbl.insert(0, tblPr)

        # Apply robust OXML column widths to guarantee Word doesn't shrink the third column
        tblGrid = table_risks._tbl.find(qn('w:tblGrid'))
        if tblGrid is not None:
            table_risks._tbl.remove(tblGrid)
            
        tblGrid = OxmlElement('w:tblGrid')
        col_widths = [Cm(1.2), Cm(10.45), Cm(5.77)]
        for w in col_widths:
            gridCol = OxmlElement('w:gridCol')
            gridCol.set(qn('w:w'), str(int(w.twips)))
            tblGrid.append(gridCol)
            
        # Insert tblGrid immediately after tblPr to conform to OOXML schema
        tblPr_index = table_risks._tbl.index(tblPr)
        table_risks._tbl.insert(tblPr_index + 1, tblGrid)
        
        # Remove any existing autofit tags and set rigid total width
        for child in list(tblPr):
            if child.tag.endswith('tblLayout') or child.tag.endswith('tblW'):
                tblPr.remove(child)
                
        tblLayout = OxmlElement('w:tblLayout')
        tblLayout.set(qn('w:type'), 'fixed')
        tblPr.append(tblLayout)
        
        tblW = OxmlElement('w:tblW')
        tblW.set(qn('w:type'), 'dxa')
        tblW.set(qn('w:w'), str(sum(int(w.twips) for w in col_widths)))
        tblPr.append(tblW)

        headers_table = vocab["detailed_risks_headers"]
        for i, h_txt in enumerate(headers_table):
            cell = table_risks.rows[0].cells[i]
            set_cell_text_custom(
                cell,
                h_txt,
                bold=True,
                font_size=8.5,
                color_rgb=RGBColor(255, 255, 255),
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            # Force exact width on the cell level in OXML
            tcPr = cell._tc.get_or_add_tcPr()
            tcW = tcPr.find(qn('w:tcW'))
            if tcW is not None:
                tcPr.remove(tcW)
            tcW = OxmlElement('w:tcW')
            tcW.set(qn('w:type'), 'dxa')
            tcW.set(qn('w:w'), str(int(col_widths[i].twips)))
            tcPr.append(tcW)
            shade_cell(cell, p_color_hex)

        for r_idx, r in enumerate(p_risks):
            row = table_risks.add_row()

            #
            set_cell_text_custom(
                row.cells[0],
                r["id"],
                bold=True,
                font_size=8.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            shade_cell(row.cells[0], alt_row_hex)

            # Assemble and render Section 2: Description and Evidence, justified per user request.
            # Clear default paragraph and build explicitly to prevent Shift+Enter stretching bugs
            cell_desc = row.cells[1]
            cell_desc.text = ""
            p_desc_lbl = cell_desc.paragraphs[0]
            p_desc_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_desc_lbl.paragraph_format.space_after = Pt(2)

            finding = r["finding"]
            biz_risk = r["business_risk"]
            cap_name = r["capability"]

            parts_f = finding.split("\n\nEvidencia Forense Literal (Audit RAG):\n")

            import re
            from assessment_engine.infrastructure.localization import (
                apply_vocabulary_substitutions,
            )
            raw_client_name = ctx.get("raw_client_name", client_name)

            clean_finding_text = apply_vocabulary_substitutions(
                clean_text_for_word(parts_f[0]), locale=doc_lang
            )
            clean_finding_text = re.sub(
                re.escape(raw_client_name),
                client_name,
                clean_finding_text,
                flags=re.IGNORECASE,
            ).strip()

            clean_biz_text = apply_vocabulary_substitutions(
                clean_text_for_word(biz_risk), locale=doc_lang
            )
            clean_biz_text = re.sub(
                re.escape(raw_client_name),
                client_name,
                clean_biz_text,
                flags=re.IGNORECASE,
            ).strip()

            run_obs = p_desc_lbl.add_run(t("vulnerability_identified_label", locale=doc_lang))
            run_obs.bold = True
            run_obs.font.name = "Arial"
            run_obs.font.size = Pt(8.5)

            p_desc_txt = cell_desc.add_paragraph(clean_finding_text)
            p_desc_txt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_desc_txt.paragraph_format.space_after = Pt(8)
            for run in p_desc_txt.runs:
                run.font.name = "Arial"
                run.font.size = Pt(8.5)

            p_biz_lbl = cell_desc.add_paragraph()
            p_biz_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_biz_lbl.paragraph_format.space_after = Pt(2)
            run_biz = p_biz_lbl.add_run(t("it_operational_impact_label", locale=doc_lang))
            run_biz.bold = True
            run_biz.font.name = "Arial"
            run_biz.font.size = Pt(8.5)

            p_biz_txt = cell_desc.add_paragraph(clean_biz_text)
            p_biz_txt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_biz_txt.paragraph_format.space_after = Pt(0)
            for run in p_biz_txt.runs:
                run.font.name = "Arial"
                run.font.size = Pt(8.5)

            # Assemble and render Section 3: Business Risk and FAIR Impact, left-aligned per user request.
            # Use native paragraphs to avoid Shift+Enter stretching bugs and carriage return issues
            cell_risk = row.cells[2]
            cell_risk.text = ""
            p_fair_lbl = cell_risk.paragraphs[0]
            p_fair_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_fair_lbl.paragraph_format.space_after = Pt(2)
            
            fair_lbl_txt = t("lbl_quantitative_fair_exposure", locale=doc_lang)
            run_fair_lbl = p_fair_lbl.add_run(fair_lbl_txt)
            run_fair_lbl.bold = True

            tef = r["tef"]
            lm = r["lm"]
            ale = r["ale"]

            # Fetch detailed FAIR metrics from lookup map
            fair_metrics = fair_lookup.get(cap_name, {})
            p90_val = fair_metrics.get("p90", 0.0) or 0.0
            min_val = fair_metrics.get("min", 0.0) or 0.0
            max_val = fair_metrics.get("max", 0.0) or 0.0

            p_fair_val = cell_risk.add_paragraph()
            p_fair_val.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_fair_val.paragraph_format.space_after = Pt(6)
            from assessment_engine.infrastructure.localization import format_number
            max_val_str = format_number(5.0, locale=doc_lang, decimals=1)
            p_fair_val.add_run(
                t(
                    "fair_freq_mag_template",
                    locale=doc_lang,
                    tef=format_number(tef, locale=doc_lang, decimals=1),
                    max_tef=max_val_str,
                    lm=format_number(lm, locale=doc_lang, decimals=1),
                    max_lm=max_val_str,
                )
            )

            p_exp_lbl = cell_risk.add_paragraph()
            p_exp_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_exp_lbl.paragraph_format.space_after = Pt(2)
            exp_lbl_txt = t("lbl_projected_financial_exposure", locale=doc_lang)
            run_exp_lbl = p_exp_lbl.add_run(exp_lbl_txt)
            run_exp_lbl.bold = True

            p_exp_val = cell_risk.add_paragraph()
            p_exp_val.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_exp_val.paragraph_format.space_after = Pt(0)

            formatted_p90 = format_currency_custom(p90_val, t_sep, d_sep).split(d_sep)[0]
            formatted_min = format_currency_custom(min_val, t_sep, d_sep).split(d_sep)[0]
            formatted_max = format_currency_custom(max_val, t_sep, d_sep).split(d_sep)[0]
            formatted_ale_item = format_currency_custom(ale, t_sep, d_sep).split(d_sep)[0]

            ale_lbl_txt = t("lbl_ale_bullet", locale=doc_lang)
            p_exp_val.add_run(ale_lbl_txt)
            run_ale_val = p_exp_val.add_run(f"{formatted_ale_item} {currency}\n")
            run_ale_val.bold = True
            run_ale_val.font.color.rgb = RGBColor(180, 0, 0)
            
            p_exp_val.add_run(t("lbl_cvar_bullet", locale=doc_lang, p90=formatted_p90, currency=currency))
            p_exp_val.add_run(t("lbl_probabilistic_range_bullet", locale=doc_lang, min_val=formatted_min, max_val=formatted_max, currency=currency))

            # Apply fonts to all runs in the third cell
            for p_item in cell_risk.paragraphs:
                for r_item in p_item.runs:
                    r_item.font.name = "Arial"
                    r_item.font.size = Pt(8.5)

            # Apply uniform alternating row backgrounds to maintain pure aesthetic logic
            row_bg = alt_row_hex if r_idx % 2 == 1 else "FFFFFF"
            for i in range(3):
                shade_cell(row.cells[i], row_bg)

            # Apply vertical centering to all cells in the row
            row.cells[0].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            row.cells[1].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            row.cells[2].vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            # Enforce exact centimeter-based column widths on every cell of every row at the VERY END, 
            # so that previous text injections and shade_cell don't overwrite the tcPr OXML.
            for i in range(3):
                cell = row.cells[i]
                tcPr = cell._tc.get_or_add_tcPr()
                tcW = tcPr.find(qn('w:tcW'))
                if tcW is not None:
                    tcPr.remove(tcW)
                tcW = OxmlElement('w:tcW')
                tcW.set(qn('w:type'), 'dxa')
                tcW.set(qn('w:w'), str(int(col_widths[i].twips)))
                tcPr.append(tcW)

        add_spacer(doc, 15)

    #

    return {
        "total_p90": total_p90,
        "formatted_ale_item": formatted_ale_item,
        "formatted_p90": formatted_p90,
        "t_sep": t_sep,
        "d_sep": d_sep,
    }


