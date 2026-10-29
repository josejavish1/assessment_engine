"""Technical appendices and regulatory disclaimers builder for Word DOCX."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
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
    add_appendix_heading,
    add_appendix_subheading,
    add_body_paragraph,
    add_spacer,
    format_currency_custom,
    set_cell_border_white,
    set_cell_text_custom,
)

logger = logging.getLogger(__name__)

def _compile_appendices(doc: Any, ctx: DocumentCompilationContext) -> None:
    """Assemble and render Appendices A, B, C, and D."""
    p_color_rgb = ctx["p_color_rgb"]
    text_color_rgb = ctx["text_color_rgb"]
    p_color_hex = ctx["p_color_hex"]
    alt_row_hex = ctx["alt_row_hex"]
    currency = ctx["currency"]
    is_critical = ctx["is_critical"]
    industry = ctx["industry"]
    doc_lang = ctx["doc_lang"]
    company_name = ctx["company_name"]
    client_name = ctx["client_name"]
    tower_name = ctx["tower_name"]
    tower_dir_obj = ctx["tower_dir_obj"]
    modules_dir = ctx["modules_dir"]
    vocab = ctx["vocab"]
    payload_path = ctx["payload_path"]
    b_data = ctx.get("b_data", {})

    def add_markdown_bullet_local(text: str, space_after: int = 4) -> Any:
        return _add_markdown_bullet(doc, text, text_color_rgb, space_after)

    # Assemble and render Appendix A: Quantitative Risk Methodology
    appendix_a_title = t("appendix_fair_title", locale=doc_lang)
    add_appendix_heading(doc, appendix_a_title, primary_color_rgb=p_color_rgb)
    appendix_a_intro = t("appendix_fair_intro", locale=doc_lang)
    add_body_paragraph(doc, appendix_a_intro, text_color_rgb=text_color_rgb)

    # Detect if the organization operates in a regulated critical sector to apply custom parameters
    is_critical_client = is_critical if is_critical is not None else True

    # standard Actuarial Practice: Dynamic Regulatory Mapping (Industry Routing)
    if "Financial" in industry or "Banking" in industry:
        reg_name = t("reg_financial_banking", locale=doc_lang)
        reg_fine_limit = format_currency(15000000.0, currency_symbol=currency, locale=doc_lang, decimals=0)
    elif "Energy" in industry or "Critical Infrastructure" in industry:
        reg_name = t("reg_energy_infra", locale=doc_lang)
        reg_fine_limit = format_currency(10000000.0, currency_symbol=currency, locale=doc_lang, decimals=0)
    elif "Telecommunications" in industry or "Media" in industry:
        reg_name = t("reg_telecom_media", locale=doc_lang)
        reg_fine_limit = format_currency(5000000.0, currency_symbol=currency, locale=doc_lang, decimals=0)
    elif "Healthcare" in industry:
        reg_name = t("reg_healthcare", locale=doc_lang)
        reg_fine_limit = format_currency(5000000.0, currency_symbol=currency, locale=doc_lang, decimals=0)
    else:
        reg_name = t("reg_general_privacy", locale=doc_lang)
        reg_fine_limit = format_currency(2000000.0, currency_symbol=currency, locale=doc_lang, decimals=0)

    # Section 1: Quantitative Rationale
    sub_1_title = t("appendix_fair_qualitative_limitations_title", locale=doc_lang)
    add_appendix_subheading(doc, sub_1_title, primary_color_rgb=p_color_rgb)
    p_why = t("appendix_fair_rationale_p", locale=doc_lang)
    add_body_paragraph(doc, p_why, text_color_rgb=text_color_rgb)

    # Section 2: Dual-Layer Calibration Model
    sub_2_title = t("appendix_fair_dual_layer_title", locale=doc_lang)
    add_appendix_subheading(doc, sub_2_title, primary_color_rgb=p_color_rgb)
    p_layer_intro = t("appendix_fair_dual_layer_p", locale=doc_lang)
    add_body_paragraph(doc, p_layer_intro, text_color_rgb=text_color_rgb)

    add_markdown_bullet_local(
        t("appendix_fair_dual_layer_b1", locale=doc_lang),
        space_after=4
    )

    add_markdown_bullet_local(
        t("appendix_fair_dual_layer_b2", locale=doc_lang, reg_name=reg_name, reg_fine_limit=reg_fine_limit),
        space_after=12
    )

    # Section 3: Actuarial Simulation Core
    sub_3_title = t("appendix_fair_sim_kernel_title", locale=doc_lang)
    add_appendix_subheading(doc, sub_3_title, primary_color_rgb=p_color_rgb)
    p_mc_intro = t("appendix_fair_sim_kernel_p", locale=doc_lang)
    add_body_paragraph(doc, p_mc_intro, text_color_rgb=text_color_rgb)

    bullets_sim = get_localized_list("appendix_fair_sim_bullets", locale=doc_lang)
    for b_idx, b_txt in enumerate(bullets_sim):
        add_markdown_bullet_local(b_txt, space_after=12 if b_idx == len(bullets_sim) - 1 else 4)

    # Section 4: Decision Metrics
    sub_4_title = t("appendix_fair_decision_metrics_title", locale=doc_lang)
    add_appendix_subheading(doc, sub_4_title, primary_color_rgb=p_color_rgb)
    p_metrics_intro = t("appendix_fair_metrics_intro", locale=doc_lang)
    add_body_paragraph(doc, p_metrics_intro, text_color_rgb=text_color_rgb)

    bullets_met = get_localized_list("appendix_fair_metrics_bullets", locale=doc_lang)
    for b_idx, b_txt in enumerate(bullets_met):
        add_markdown_bullet_local(b_txt, space_after=12 if b_idx == len(bullets_met) - 1 else 4)

    p_convergence = t("appendix_fair_convergence_note", locale=doc_lang)
    add_body_paragraph(doc, p_convergence, text_color_rgb=text_color_rgb)
    
        # Disable the `autofit` property to enforce a fixed table width of 6.5 inches.

    #
    # Assemble and render Appendix B: Information Sources Custody Ledger
    #
    add_appendix_heading(doc, vocab["appendix_c_title"], primary_color_rgb=p_color_rgb)
    add_body_paragraph(doc, vocab["appendix_c_intro"], text_color_rgb=text_color_rgb)

    source_table = doc.add_table(rows=1, cols=3)
    source_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    finalize_table(source_table)

    for i, h_txt in enumerate(vocab["appendix_c_headers"]):
        set_cell_text_custom(
            source_table.rows[0].cells[i],
            h_txt,
            bold=True,
            font_size=10,
            color_rgb=RGBColor(255, 255, 255),
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(source_table.rows[0].cells[i], p_color_hex)

    # Set initial column widths for header cells in centimeters
    source_table.rows[0].cells[0].width = Cm(1.5)
    source_table.rows[0].cells[1].width = Cm(4.5)
    source_table.rows[0].cells[2].width = Cm(10.5)

    # Data Sanitization: Prevent generation of invalid source file paths in the bibliography, per requirement 4.
    src_data = []
    b_data = ctx.get("b_data") or {}
    if not b_data and payload_path and payload_path.exists():
        try:
            with open(payload_path, "r", encoding="utf-8-sig") as f:
                b_data = json.load(f)
        except Exception:
            b_data = {}

    source_docs = b_data.get("source_documents") if payload_path and payload_path.exists() else None

    if source_docs:
        # If source file paths are provided in the payload, use them directly, overriding any dynamic generation logic.
        for doc_item in source_docs:
            src_data.append(
                (
                    doc_item.get("code", "[Doc]"),
                    doc_item.get("name", "Documento"),
                    doc_item.get("desc", t("appendix_c_default_custody_desc", locale=doc_lang)),
                )
            )
    else:
        # Dynamically generate a context-aware bibliography based on the specified technology stack to avoid invalid source file references.
        client_name_slug = client_name.lower().replace(" ", "_")
        raw_bib_entries = get_localized_list("appendix_c_bib_entries", locale=doc_lang)
        src_data = []
        for entry in raw_bib_entries:
            tag, name_tpl, desc_tpl = entry[0], entry[1], entry[2]
            name = name_tpl.format(client_name_slug=client_name_slug, tower_name=tower_name, client_name=client_name)
            desc = desc_tpl.format(client_name_slug=client_name_slug, tower_name=tower_name, client_name=client_name)
            src_data.append((tag, name, desc))

    for s_idx, row_vals in enumerate(src_data):
        row = source_table.add_row()
        set_cell_text_custom(
            row.cells[0],
            row_vals[0],
            bold=True,
            font_size=10,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        set_cell_text_custom(
            row.cells[1], row_vals[1], font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER
        )
        set_cell_text_custom(row.cells[2], row_vals[2], font_size=10)

        row.cells[0].width = Cm(1.5)
        row.cells[1].width = Cm(4.5)
        row.cells[2].width = Cm(10.5)

        if s_idx % 2 == 1:
            shade_cell(row.cells[0], alt_row_hex)
            shade_cell(row.cells[1], alt_row_hex)
            shade_cell(row.cells[2], alt_row_hex)

    add_spacer(doc, 12)

    #
    # Assemble and render Appendix C: Terms and Abbreviations Glossary
    #
    add_appendix_heading(doc, vocab["appendix_a_title"], primary_color_rgb=p_color_rgb)
    add_body_paragraph(doc, vocab["appendix_a_intro"], text_color_rgb=text_color_rgb)

    import re

    from assessment_engine.infrastructure.config_loader import (
        load_abbreviations_glossary,
    )

    try:
        full_glossary = load_abbreviations_glossary()

        # Merge case-specific client abbreviations if they exist in the case directory
        client_glossary_path = tower_dir_obj / "client_abbreviations_glossary.json"
        if client_glossary_path.exists():
            try:
                with open(client_glossary_path, "r", encoding="utf-8-sig") as cgf:
                    client_glossary = json.load(cgf)
                    for lang, terms in client_glossary.items():
                        if lang in full_glossary:
                            full_glossary[lang].update(terms)
                        else:
                            full_glossary[lang] = terms
            except json.JSONDecodeError as ex:
                logger.info(
                    f"⚠️  [Glosario] Error de sintaxis JSON en {client_glossary_path}: {ex}"
                )
            except Exception as ex:
                logger.info(f"⚠️  [Glosario] No se pudo leer {client_glossary_path}: {ex}")

        glossary = full_glossary.get(doc_lang, full_glossary.get("en", {}))

        # Gather all text accumulated in paragraphs and tables so far (now fully includes Appendix A and B!)
        all_text_elements = []
        for p in doc.paragraphs:
            if p.text:
                all_text_elements.append(p.text)
        for tbl in doc.tables:
            for row in tbl.rows:
                for cell in row.cells:
                    if cell.text:
                        all_text_elements.append(cell.text)
        text_corpus = " ".join(all_text_elements)

        # Filter glossary keys that are actually present in the text corpus
        used_glossary = {}
        for term, desc in glossary.items():
            escaped_term = re.escape(term)
            pattern = rf"(?<![a-zA-Z0-9]){escaped_term}(?![a-zA-Z0-9])"
            if re.search(pattern, text_corpus):
                used_glossary[term] = desc

        # Quality Gate: First-Use Rule Verification
        for term, desc in used_glossary.items():
            # standard Bilingual Check: Extract both English form (before parenthesis) and Spanish translation (inside parenthesis)
            # to prevent false positive warnings when compiling documents in different languages
            parts = []
            if "(" in desc:
                main_part = desc.split("(")[0].strip()
                parts.append(main_part)
                sub_part = desc.split("(")[1].split(")")[0].strip()
                parts.append(sub_part)
            else:
                parts.append(desc)

            # Verification passes if either the English or the Spanish full form is located in the text
            if not any(p.lower() in text_corpus.lower() for p in parts if len(p) > 2):
                logger.info(
                    f"⚠️  [Glossary] Quality: Acronym '{term}' is used but its definition ('{parts[0]}') does not appear in document corpus. Recommended to expand upon first use."
                )

        if used_glossary:
            gloss_table = doc.add_table(rows=1, cols=2)
            gloss_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            finalize_table(gloss_table)

            for i, h_txt in enumerate(vocab["appendix_a_headers"]):
                set_cell_text_custom(
                    gloss_table.rows[0].cells[i],
                    h_txt,
                    bold=True,
                    font_size=10,
                    color_rgb=RGBColor(255, 255, 255),
                    align=WD_ALIGN_PARAGRAPH.CENTER,
                )
                shade_cell(gloss_table.rows[0].cells[i], p_color_hex)

            #
            gloss_table.rows[0].cells[0].width = Inches(1.5)
            gloss_table.rows[0].cells[1].width = Inches(5.0)  #

            for g_idx, (term, desc) in enumerate(sorted(used_glossary.items())):
                row = gloss_table.add_row()
                set_cell_text_custom(row.cells[0], term, bold=True, font_size=10)
                set_cell_text_custom(row.cells[1], desc, font_size=10)

                #
                row.cells[0].width = Inches(1.5)
                row.cells[1].width = Inches(5.0)

                if g_idx % 2 == 1:
                    shade_cell(row.cells[0], alt_row_hex)
                    shade_cell(row.cells[1], alt_row_hex)
    except Exception as ex:
        logger.info(f"⚠️  [Glossary] Unexpected error in abbreviations appendix: {ex}")

    add_spacer(doc, 12)

    #
    # Assemble and render Appendix D: Liability Limitation Clause
    # Always prioritize the central declarative brand disclaimer.
    #
    add_appendix_heading(doc, vocab["appendix_b_title"], primary_color_rgb=p_color_rgb)
    from assessment_engine.infrastructure.config_loader import get_localized_disclaimer
    disclaimer_raw = get_localized_disclaimer(doc_lang)
    if disclaimer_raw:
        for p_text in disclaimer_raw.split("\n\n"):
            if p_text.strip():
                formatted_p = (
                    p_text.strip().format(company_name=company_name)
                    if "{company_name}" in p_text
                    else p_text.strip()
                )
                add_body_paragraph(
                    doc,
                    formatted_p,
                    text_color_rgb=text_color_rgb,
                )
    else:
        for k in ["disclaimer_text_1", "disclaimer_text_2", "disclaimer_text_3", "disclaimer_text_4", "disclaimer_text_5"]:
            if vocab.get(k):
                add_body_paragraph(
                    doc, vocab.get(k, ""), text_color_rgb=text_color_rgb
                )

    add_spacer(doc, 20)


