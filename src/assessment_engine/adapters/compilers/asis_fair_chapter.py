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
from docx.shared import Cm, Inches

from assessment_engine.adapters.emitters.docx_style_resolver import DocxStyleResolver
from assessment_engine.domain.theme_registry import SemanticColorRole, TypographyRole
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


def _render_fair_heatmap(
    doc: Any,
    ctx: DocumentCompilationContext,
    risks_data_list: list[dict[str, Any]],
    doc_lang: str,
    client_name: str,
    currency: str,
    is_critical: bool,
    p_color_rgb: tuple[int, int, int],
    text_color_rgb: tuple[int, int, int],
    vocab: dict[str, Any],
) -> None:
    """Renders the 5x5 quantitative risk heatmap table as a visual synthesis."""
    if not risks_data_list:
        return

    industry_name = ctx.get("industry", "Enterprise & Industrial Technology")
    add_heading(
        doc, vocab["exposure_summary_title"], level=2, primary_color_rgb=p_color_rgb
    )

    sec_intro_p1 = t("fair_heatmap_sec_p1", locale=doc_lang)
    sec_intro_p2 = t(
        "fair_heatmap_sec_p2",
        locale=doc_lang,
        client_name=client_name,
        industry_name=industry_name,
    )
    sec_intro_p3 = t("fair_heatmap_sec_p3", locale=doc_lang)

    add_body_paragraph(doc, sec_intro_p1, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, sec_intro_p2, text_color_rgb=text_color_rgb)
    if sec_intro_p3:
        add_body_paragraph(doc, sec_intro_p3, text_color_rgb=text_color_rgb)
    add_spacer(doc, 15)

    matrix_cells = {r: {c: [] for c in range(1, 6)} for r in range(5, 0, -1)}
    for r in risks_data_list:
        r_tef = min(5, max(1, int(round(r["tef"]))))
        r_lm = min(5, max(1, int(round(r["lm"]))))
        matrix_cells[r_tef][r_lm].append(r["id"])

    heatmap_table = doc.add_table(rows=6, cols=6)
    heatmap_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    finalize_table(heatmap_table)

    resolver = DocxStyleResolver.get_default(language_code=doc_lang)
    cell_0_0 = heatmap_table.rows[0].cells[0]
    set_cell_text_custom(
        cell_0_0,
        "TEF \\ LM",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        typography_role=TypographyRole.TABLE_HEADER,
        color_role=SemanticColorRole.TEXT_INVERSE,
        resolver=resolver,
        no_bullets=True,
    )
    shade_cell(cell_0_0, COLOR_BLUE)
    set_cell_border_white(cell_0_0)
    cell_0_0.width = Inches(1.3)
    cell_0_0.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    rate_mult = float(ctx.get("rate_mult", 1.0))
    for col_idx in range(1, 6):
        if is_critical:
            lm_ranges = {
                1: f"< {format_number(1000.0 * rate_mult, locale=doc_lang, decimals=0)} {currency}",
                2: f"{format_number(1000.0 * rate_mult, locale=doc_lang, decimals=0)} - {format_number(10000.0 * rate_mult, locale=doc_lang, decimals=0)} {currency}",
                3: f"{format_number(10000.0 * rate_mult, locale=doc_lang, decimals=0)} - {format_number(50000.0 * rate_mult, locale=doc_lang, decimals=0)} {currency}",
                4: f"{format_number(50000.0 * rate_mult, locale=doc_lang, decimals=0)} - {format_number(250000.0 * rate_mult, locale=doc_lang, decimals=0)} {currency}",
                5: f"> {format_number(250000.0 * rate_mult, locale=doc_lang, decimals=0)} {currency}",
            }
        else:
            lm_ranges = {
                1: f"< {format_number(1000.0 * rate_mult, locale=doc_lang, decimals=0)} {currency}",
                2: f"{format_number(1000.0 * rate_mult, locale=doc_lang, decimals=0)} - {format_number(5000.0 * rate_mult, locale=doc_lang, decimals=0)} {currency}",
                3: f"{format_number(5000.0 * rate_mult, locale=doc_lang, decimals=0)} - {format_number(25000.0 * rate_mult, locale=doc_lang, decimals=0)} {currency}",
                4: f"{format_number(25000.0 * rate_mult, locale=doc_lang, decimals=0)} - {format_number(100000.0 * rate_mult, locale=doc_lang, decimals=0)} {currency}",
                5: f"> {format_number(100000.0 * rate_mult, locale=doc_lang, decimals=0)} {currency}",
            }
        lm_lbl = f"LM {col_idx}\n({lm_ranges[col_idx]})"
        cell = heatmap_table.rows[0].cells[col_idx]
        set_cell_text_custom(
            cell,
            lm_lbl,
            align=WD_ALIGN_PARAGRAPH.CENTER,
            typography_role=TypographyRole.TABLE_HEADER,
            color_role=SemanticColorRole.TEXT_INVERSE,
            resolver=resolver,
            no_bullets=True,
        )
        shade_cell(cell, COLOR_BLUE)
        set_cell_border_white(cell)
        cell.width = Inches(1.04)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

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
            align=WD_ALIGN_PARAGRAPH.CENTER,
            typography_role=TypographyRole.TABLE_HEADER,
            color_role=SemanticColorRole.TEXT_INVERSE,
            resolver=resolver,
            no_bullets=True,
        )
        shade_cell(cell_header, COLOR_BLUE)
        set_cell_border_white(cell_header)
        cell_header.width = Inches(1.3)
        cell_header.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

        for col_idx, lm_val in enumerate(range(1, 6), 1):
            cell = heatmap_table.rows[row_idx].cells[col_idx]
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
                shade_cell(cell, "FADBD8")
            elif severity >= 8:
                shade_cell(cell, "FCF3CF")
            else:
                shade_cell(cell, "D5F5E3")

    heatmap_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    add_spacer(doc, 20)


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

    # Section 4.1: Operational Risk Assessment and Resilience
    add_heading(
        doc,
        t("operational_risk_framework_title", locale=doc_lang),
        level=2,
        primary_color_rgb=p_color_rgb,
    )

    add_body_paragraph(doc, intro_prose_p1, text_color_rgb=text_color_rgb)

    p_exp_lead = doc.add_paragraph(style="Normal")
    resolver = DocxStyleResolver.get_default(language_code=doc_lang)
    resolver.apply_paragraph_typography(p_exp_lead, TypographyRole.BODY_REGULAR)
    p_exp_lead.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r_exp_lbl = p_exp_lead.add_run(t("lbl_resilience_and_economic_impact", locale=doc_lang) + " ")
    resolver.apply_run_style(
        r_exp_lbl,
        typo_role=TypographyRole.BODY_STRONG,
        color_role=SemanticColorRole.BRAND_PRIMARY,
        bold_override=True,
    )

    r_exp_body = p_exp_lead.add_run(f"{intro_prose_p2} {intro_prose_p3}")
    resolver.apply_run_style(
        r_exp_body,
        typo_role=TypographyRole.BODY_REGULAR,
        color_role=SemanticColorRole.TEXT_PRIMARY,
    )

    if intro_prose_p4:
        add_body_paragraph(doc, intro_prose_p4, text_color_rgb=text_color_rgb)
    add_spacer(doc, 8)

    lbl_metrics_intro = t("fair_guide_intro", locale=doc_lang)
    add_body_paragraph(doc, lbl_metrics_intro, text_color_rgb=text_color_rgb)
    for g_bullet in get_localized_list("fair_guide_bullets", locale=doc_lang):
        add_body_paragraph(doc, g_bullet, style="List Bullet", text_color_rgb=text_color_rgb)
    add_spacer(doc, 15)

    def add_markdown_bullet_local(text: str, space_after: int = 4) -> Any:
        return _add_markdown_bullet(doc, text, text_color_rgb, space_after)

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
    elif b_data and b_data.get("pillars_analysis"):
        from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
            derive_in_memory_fair_risks,
        )
        rate_mult = float(ctx.get("rate_mult", 1.0))
        risks_data_list, risks_by_pilar = derive_in_memory_fair_risks(
            b_data, doc_lang=doc_lang, currency=currency, rate_mult=rate_mult
        )

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

    # Section 4.2: Prioritized Risk Catalog
    add_heading(
        doc, t("detailed_risks_title", locale=doc_lang), level=2, primary_color_rgb=p_color_rgb
    )
    add_body_paragraph(
        doc,
        t("fair_catalog_intro", locale=doc_lang),
        text_color_rgb=text_color_rgb,
    )
    add_spacer(doc, 10)

    # Sort all risks strictly by ALE descending for unified global prioritization
    risks_data_list.sort(key=lambda r: r["ale"], reverse=True)
    for idx, r in enumerate(risks_data_list):
        r["id"] = f"{tower_id}-RSK-{idx + 1:02d}"
        r["rank"] = idx + 1

    total_risks_count = len(risks_data_list)
    local_mean_ale = (sum(r["ale"] for r in risks_data_list) / total_risks_count) if total_risks_count > 0 else 0.0
    tier1_threshold = local_mean_ale * 1.5
    tier2_threshold = local_mean_ale * 0.5

    # Part A: Executive Risk Summary Table (1 single consolidated table)
    table_risks = doc.add_table(rows=1, cols=6)
    table_risks.alignment = WD_TABLE_ALIGNMENT.LEFT
    finalize_table(table_risks)
    table_risks.autofit = False
    table_risks.allow_autofit = False

    tblPr = table_risks._tbl.tblPr
    if tblPr is None:
        tblPr = OxmlElement('w:tblPr')
        table_risks._tbl.insert(0, tblPr)

    tblGrid = table_risks._tbl.find(qn('w:tblGrid'))
    if tblGrid is not None:
        table_risks._tbl.remove(tblGrid)

    tblGrid = OxmlElement('w:tblGrid')
    sum_col_widths = [Cm(2.2), Cm(5.1), Cm(3.4), Cm(2.0), Cm(2.0), Cm(1.8)]
    for w in sum_col_widths:
        gridCol = OxmlElement('w:gridCol')
        gridCol.set(qn('w:w'), str(int(w.twips)))
        tblGrid.append(gridCol)

    tblPr_index = table_risks._tbl.index(tblPr)
    table_risks._tbl.insert(tblPr_index + 1, tblGrid)

    for child in list(tblPr):
        if child.tag.endswith('tblLayout') or child.tag.endswith('tblW'):
            tblPr.remove(child)

    tblLayout = OxmlElement('w:tblLayout')
    tblLayout.set(qn('w:type'), 'fixed')
    tblPr.append(tblLayout)

    tblW = OxmlElement('w:tblW')
    tblW.set(qn('w:type'), 'dxa')
    tblW.set(qn('w:w'), str(sum(int(w.twips) for w in sum_col_widths)))
    tblPr.append(tblW)

    summary_headers = get_localized_list("risk_summary_headers", locale=doc_lang)
    if not isinstance(summary_headers, list) or len(summary_headers) < 6:
        summary_headers = ["ID", "Evaluated Risk / Asset", "Pillar", "Frequency (TEF)", "Outage Cost (P90)", "Annual Loss (ALE)"]

    for i, h_txt in enumerate(summary_headers):
        cell = table_risks.rows[0].cells[i]
        set_cell_text_custom(
            cell,
            h_txt,
            align=WD_ALIGN_PARAGRAPH.CENTER,
            typography_role=TypographyRole.TABLE_HEADER,
            color_role=SemanticColorRole.TEXT_INVERSE,
            resolver=resolver,
            no_bullets=True,
        )
        tcPr = cell._tc.get_or_add_tcPr()
        tcW = tcPr.find(qn('w:tcW'))
        if tcW is not None:
            tcPr.remove(tcW)
        tcW = OxmlElement('w:tcW')
        tcW.set(qn('w:type'), 'dxa')
        tcW.set(qn('w:w'), str(int(sum_col_widths[i].twips)))
        tcPr.append(tcW)
        shade_cell(cell, p_color_hex)

    from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
    taxonomy_resolver = get_taxonomy_resolver()
    style_resolver = DocxStyleResolver.get_default(language_code=doc_lang)

    for r_idx, r in enumerate(risks_data_list):
        row = table_risks.add_row()
        raw_cap = r["capability"]
        cap_name = taxonomy_resolver.resolve_capability_name(raw_cap, default=raw_cap, locale=doc_lang)
        raw_pilar = r.get("pillar") or r.get("pilar", "Pillar")
        pilar_name = taxonomy_resolver.resolve_pillar_by_any_reference(raw_pilar, default=raw_pilar, locale=doc_lang)

        fair_metrics = fair_lookup.get(raw_cap, fair_lookup.get(cap_name, {}))
        p90_val = r.get("p90") or fair_metrics.get("p90", 0.0) or (r["ale"] * 2.5)
        formatted_ale_r = format_currency_custom(r["ale"], t_sep, d_sep).split(d_sep)[0]
        formatted_p90_r = format_currency_custom(p90_val, t_sep, d_sep).split(d_sep)[0]

        set_cell_text_custom(row.cells[0], r["id"], bold=True, font_size=8.0, align=WD_ALIGN_PARAGRAPH.CENTER, no_bullets=True)
        set_cell_text_custom(row.cells[1], cap_name, bold=True, font_size=8.0, no_bullets=True)
        set_cell_text_custom(row.cells[2], pilar_name, font_size=8.0, no_bullets=True)
        set_cell_text_custom(row.cells[3], f"{r['tef']:.1f} / 5.0", font_size=8.0, align=WD_ALIGN_PARAGRAPH.CENTER, no_bullets=True)
        set_cell_text_custom(row.cells[4], f"{formatted_p90_r} {currency}", font_size=8.0, align=WD_ALIGN_PARAGRAPH.RIGHT, no_bullets=True)
        set_cell_text_custom(row.cells[5], f"{formatted_ale_r} {currency}", bold=True, font_size=8.0, align=WD_ALIGN_PARAGRAPH.RIGHT, no_bullets=True)

        for i, w in enumerate(sum_col_widths):
            cell = row.cells[i]
            tcPr = cell._tc.get_or_add_tcPr()
            tcW = tcPr.find(qn('w:tcW'))
            if tcW is not None:
                tcPr.remove(tcW)
            tcW = OxmlElement('w:tcW')
            tcW.set(qn('w:type'), 'dxa')
            tcW.set(qn('w:w'), str(int(sum_col_widths[i].twips)))
            tcPr.append(tcW)
            if r_idx % 2 == 1:
                shade_cell(cell, alt_row_hex)

    add_spacer(doc, 15)

    # Part B: Executive 2-Line Risk Cards
    lbl_diag = t("label_operational_diagnostic", locale=doc_lang)
    lbl_econ = t("label_economic_impact", locale=doc_lang)

    import re
    from assessment_engine.infrastructure.localization import apply_vocabulary_substitutions
    raw_client_name = ctx.get("raw_client_name", client_name)

    for r in risks_data_list:
        raw_cap = r["capability"]
        cap_name = taxonomy_resolver.resolve_capability_name(raw_cap, default=raw_cap, locale=doc_lang)
        fair_metrics = fair_lookup.get(raw_cap, fair_lookup.get(cap_name, {}))
        p90_val = r.get("p90") or fair_metrics.get("p90", 0.0) or (r["ale"] * 2.5)
        formatted_ale_r = format_currency_custom(r["ale"], t_sep, d_sep).split(d_sep)[0]
        formatted_p90_r = format_currency_custom(p90_val, t_sep, d_sep).split(d_sep)[0]

        if r["ale"] >= tier1_threshold:
            tier_badge = t("tier_label_critical", locale=doc_lang)
        elif r["ale"] >= tier2_threshold:
            tier_badge = t("tier_label_medium", locale=doc_lang)
        else:
            tier_badge = t("tier_label_moderate", locale=doc_lang)

        # Risk Card Heading
        card_title = f"[{r['id']}] {cap_name} ({tier_badge})"
        add_heading(doc, card_title, level=3, primary_color_rgb=p_color_rgb)

        raw_f = re.split(r"\n\n(?:Evidencia|Evidence|Audit)", r["finding"])[0].strip()
        raw_br = r["business_risk"].strip()

        clean_f = apply_vocabulary_substitutions(clean_text_for_word(raw_f), locale=doc_lang)
        clean_f = re.sub(re.escape(raw_client_name), client_name, clean_f, flags=re.IGNORECASE).strip()
        f_parts = re.split(r"(?<!\d)\.(?!\d)\s+", clean_f)
        clean_f = f_parts[0].strip() if f_parts else clean_f

        clean_br = apply_vocabulary_substitutions(clean_text_for_word(raw_br), locale=doc_lang)
        clean_br = re.sub(re.escape(raw_client_name), client_name, clean_br, flags=re.IGNORECASE).strip()
        br_parts = re.split(r"(?<!\d)\.(?!\d)\s+", clean_br)
        clean_br = br_parts[0].strip() if br_parts else clean_br
        clean_br_low = clean_br[:1].lower() + clean_br[1:] if clean_br else ""

        tef_val = r["tef"]
        if tef_val >= 4.0:
            freq_str = t("resilience_freq_high", locale=doc_lang)
        elif tef_val >= 2.5:
            freq_str = t("resilience_freq_med", locale=doc_lang)
        else:
            freq_str = t("resilience_freq_low", locale=doc_lang)

        calc_basis = t(
            "calc_basis_note_template",
            locale=doc_lang,
            freq_str=freq_str,
            tef_score=f"{tef_val:.1f}",
        )

        # 1. Operational Diagnostic Line
        p_diag = doc.add_paragraph(style="Normal")
        style_resolver.apply_paragraph_typography(p_diag, TypographyRole.BODY_REGULAR)
        p_diag.paragraph_format.left_indent = Inches(0.12)
        p_diag.paragraph_format.first_line_indent = Inches(-0.12)
        p_diag.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        r_lbl1 = p_diag.add_run(f"• {lbl_diag}: ")
        style_resolver.apply_run_style(
            r_lbl1,
            typo_role=TypographyRole.TABLE_CELL,
            color_role=SemanticColorRole.TEXT_PRIMARY,
            bold_override=True,
        )

        diag_body = t(
            "risk_card_diagnostic_template",
            locale=doc_lang,
            finding=clean_f.rstrip("."),
            risk=clean_br_low.rstrip("."),
        )
        r_body1 = p_diag.add_run(diag_body)
        style_resolver.apply_run_style(
            r_body1,
            typo_role=TypographyRole.TABLE_CELL,
            color_role=SemanticColorRole.TEXT_PRIMARY,
        )

        # 2. Economic Impact Line
        p_econ = doc.add_paragraph(style="Normal")
        style_resolver.apply_paragraph_typography(p_econ, TypographyRole.BODY_REGULAR)
        p_econ.paragraph_format.left_indent = Inches(0.12)
        p_econ.paragraph_format.first_line_indent = Inches(-0.12)
        p_econ.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        r_lbl2 = p_econ.add_run(f"• {lbl_econ}: ")
        style_resolver.apply_run_style(
            r_lbl2,
            typo_role=TypographyRole.TABLE_CELL,
            color_role=SemanticColorRole.TEXT_PRIMARY,
            bold_override=True,
        )

        year_suffix = t("lbl_year", locale=doc_lang)
        r_body2_bold = p_econ.add_run(f"{formatted_ale_r} {currency}/{year_suffix} (ALE)")
        style_resolver.apply_run_style(
            r_body2_bold,
            typo_role=TypographyRole.TABLE_CELL,
            color_role=SemanticColorRole.STATUS_CRITICAL,
            bold_override=True,
        )

        txt_mid = t("lbl_and_up_to_crisis_cost", locale=doc_lang, formatted_p90=formatted_p90_r, currency=currency)
        r_body2_mid = p_econ.add_run(txt_mid)
        style_resolver.apply_run_style(
            r_body2_mid,
            typo_role=TypographyRole.TABLE_CELL,
            color_role=SemanticColorRole.TEXT_PRIMARY,
            bold_override=True,
        )

        r_body2_calc = p_econ.add_run(f"({calc_basis}).")
        style_resolver.apply_run_style(
            r_body2_calc,
            typo_role=TypographyRole.CAPTION,
            color_role=SemanticColorRole.TEXT_MUTED,
        )

    add_spacer(doc, 15)

    # Render Section 4.2: 5x5 Heatmap as a visual synthesis of all evaluated risks
    _render_fair_heatmap(
        doc=doc,
        ctx=ctx,
        risks_data_list=risks_data_list,
        doc_lang=doc_lang,
        client_name=client_name,
        currency=currency,
        is_critical=is_critical,
        p_color_rgb=p_color_rgb,
        text_color_rgb=text_color_rgb,
        vocab=vocab,
    )

    # Section 4.4: Mitigation Levers and Resilience Return (Hexagon of Value)
    add_heading(
        doc, t("value_hexagon_heading", locale=doc_lang), level=2, primary_color_rgb=p_color_rgb
    )
    lever_intro = t("value_hexagon_intro", locale=doc_lang)
    add_body_paragraph(doc, lever_intro, text_color_rgb=text_color_rgb)
    for l_idx, lever_text in enumerate(get_localized_list("value_hexagon_bullets", locale=doc_lang)):
        add_markdown_bullet_local(lever_text, space_after=12 if l_idx == 5 else 3)

    return {
        "total_p90": total_p90,
        "formatted_ale_item": formatted_ale_item,
        "formatted_p90": formatted_p90,
        "t_sep": t_sep,
        "d_sep": d_sep,
    }


