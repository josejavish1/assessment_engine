import logging
logger = logging.getLogger(__name__)
import csv
import html
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document
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
from assessment_engine.infrastructure.text_utils import clean_text_for_word, format_date_spanish
from assessment_engine.infrastructure.localization import (
    format_currency,
    format_date_localized,
    format_number,
    t,
)

# Re-export primitives and constants from asis_docx_primitives for 100% backward compatibility
from assessment_engine.adapters.compilers.asis_docx_primitives import (
    COLOR_BLUE,
    COLOR_HEADER_BG,
    COLOR_ROW_ALT,
    LANG_VOCAB,
    Chapter4Result,
    DocumentCompilationContext,
    _add_markdown_bullet,
    _load_asis_vocab,
    add_appendix_heading,
    add_appendix_subheading,
    add_body_paragraph,
    add_callout_box,
    add_heading,
    add_spacer,
    add_toc,
    clean_client_name,
    extract_key_bullets_from_md,
    format_currency_custom,
    parse_and_append_markdown_section,
    set_cell_border_white,
    set_cell_text_custom,
    set_update_fields,
)

from assessment_engine.adapters.compilers.asis_maturity_chapter import _compile_chapter_3_maturity_profile
from assessment_engine.adapters.compilers.asis_fair_chapter import _compile_chapter_4_fair_risk_matrix
from assessment_engine.adapters.compilers.asis_conclusions_chapter import _compile_chapter_5_conclusions
from assessment_engine.adapters.compilers.asis_appendices_chapter import _compile_appendices

def _compile_cover_and_toc(doc: Any, ctx: DocumentCompilationContext) -> None:
    """Render Section 0 (Corporate Cover Page) and Section 0.1 (Table of Contents)."""
    p_color_rgb = ctx["p_color_rgb"]
    text_color_rgb = ctx["text_color_rgb"]
    doc_lang = ctx.get("doc_lang", "en")

    style_resolver = DocxStyleResolver.get_default(language_code=doc_lang)

    add_spacer(doc, 200)

    p_title = doc.add_paragraph()
    run_title = p_title.add_run(t("title", locale=doc_lang))
    style_resolver.apply_run_style(
        run_title,
        typo_role=TypographyRole.DISPLAY,
        color_role=SemanticColorRole.TEXT_PRIMARY,
        bold_override=True,
    )

    p_sub = doc.add_paragraph()
    sub_prefix = t("annex_technical_prefix", locale=doc_lang)
    run_sub = p_sub.add_run(f"{sub_prefix} {ctx['tower_name']}")
    style_resolver.apply_run_style(
        run_sub,
        typo_role=TypographyRole.HEADING_1,
        color_role=SemanticColorRole.BRAND_PRIMARY,
    )

    add_spacer(doc, 140)

    p_client = doc.add_paragraph()
    client_label = t("client_lbl", locale=doc_lang)
    run_cli_lbl = p_client.add_run(client_label)
    style_resolver.apply_run_style(
        run_cli_lbl,
        typo_role=TypographyRole.DISPLAY,
        color_role=SemanticColorRole.TEXT_PRIMARY,
        bold_override=True,
    )

    if ctx.get("client_group"):
        run_cli = p_client.add_run(f"{ctx['client_name'].upper()} ({ctx['client_group']})")
    else:
        run_cli = p_client.add_run(f"{ctx['client_name'].upper()}")
    style_resolver.apply_run_style(
        run_cli,
        typo_role=TypographyRole.DISPLAY,
        color_role=SemanticColorRole.BRAND_PRIMARY,
        bold_override=True,
    )

    p_proj = doc.add_paragraph()
    proj_label = t("proj_lbl", locale=doc_lang)
    project_title = t("project", locale=doc_lang)
    if project_title:
        run_proj_lbl = p_proj.add_run(proj_label)
        style_resolver.apply_run_style(
            run_proj_lbl,
            typo_role=TypographyRole.HEADING_2,
            color_role=SemanticColorRole.TEXT_PRIMARY,
            bold_override=True,
        )

        run_proj = p_proj.add_run(f"{project_title}")
        style_resolver.apply_run_style(
            run_proj,
            typo_role=TypographyRole.HEADING_2,
            color_role=SemanticColorRole.TEXT_PRIMARY,
        )

    add_spacer(doc, 140)

    classification_clean = ctx["classification"].replace(" (Tier-1 Assessment)", "")
    version_label = t("v_lbl", locale=doc_lang)

    p_footer = doc.add_paragraph()
    company_prefix = f"{ctx['company_name'].upper()} | " if ctx.get("company_name") else ""
    run_date = p_footer.add_run(
        f"{company_prefix}{ctx['doc_date']} | {version_label}{ctx['doc_version']} | {classification_clean}"
    )
    style_resolver.apply_run_style(
        run_date,
        typo_role=TypographyRole.CAPTION,
        color_role=SemanticColorRole.TEXT_MUTED,
    )

    doc.add_page_break()

    # Section 0.1: Table of Contents (TOC).
    # Render unnumbered title so Word does not treat the Table of Contents as Chapter 1 in the multi-level list template.
    toc_heading = t("toc_title", locale=doc_lang)
    p_toc_title = doc.add_paragraph()
    style_resolver.apply_paragraph_typography(p_toc_title, TypographyRole.HEADING_2)
    p_toc_title.paragraph_format.keep_with_next = True
    r_toc_title = p_toc_title.add_run(toc_heading)
    style_resolver.apply_run_style(
        r_toc_title,
        typo_role=TypographyRole.HEADING_2,
        color_role=SemanticColorRole.BRAND_PRIMARY,
        bold_override=True,
    )

    # Word native dynamic Table of Contents field code (TOC \o "1-2")
    add_toc(doc)

    # Preliminary Confidentiality and Liability Disclaimer
    add_spacer(doc, 30)
    p_disc = doc.add_paragraph()
    style_resolver.apply_paragraph_typography(p_disc, TypographyRole.CAPTION)
    p_disc.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    r_conf = p_disc.add_run(t("confidentiality_label", locale=doc_lang))
    style_resolver.apply_run_style(
        r_conf,
        typo_role=TypographyRole.CAPTION,
        color_role=SemanticColorRole.TEXT_MUTED,
        bold_override=True,
    )

    disc_text = t("disclaimer_statement", locale=doc_lang)
    r_body = p_disc.add_run(disc_text)
    style_resolver.apply_run_style(
        r_body,
        typo_role=TypographyRole.CAPTION,
        color_role=SemanticColorRole.TEXT_MUTED,
    )
    r_body.font.italic = True


def _compile_introduction_and_scope(doc: Any, ctx: DocumentCompilationContext) -> None:
    """Render Chapter 1 (Executive Summary intro) and Chapter 2 (Methodology, Scope, Objectives, Asset Footprint)."""
    p_color_rgb = ctx["p_color_rgb"]
    text_color_rgb = ctx["text_color_rgb"]
    p_color_hex = ctx["p_color_hex"]
    alt_row_hex = ctx["alt_row_hex"]
    doc_lang = ctx.get("doc_lang", "en")
    modules_dir = ctx["modules_dir"]
    b_data = ctx.get("b_data", {})
    style_resolver = DocxStyleResolver.get_default(language_code=doc_lang)

    # Assemble and render Chapter 1: Executive Summary and Business Context.
    parse_and_append_markdown_section(
        doc, modules_dir / "02_resumen_ejecutivo.md", p_color_rgb, text_color_rgb
    )

    # Assemble and render Chapter 2: Objective, Scope, and Assessment Methodology.
    add_heading(
        doc,
        t("methodology_chapter_title", locale=doc_lang),
        level=1,
        primary_color_rgb=p_color_rgb,
    )

    # 2.1 Objectives and Scope
    intro_file = (modules_dir / "01_introduction.md") if (modules_dir / "01_introduction.md").exists() else (modules_dir / "01_introduccion.md")
    methodology_hdr = t("methodology_section_header", locale=doc_lang)
    parse_and_append_markdown_section(
        doc,
        intro_file,
        p_color_rgb,
        text_color_rgb,
        end_header=methodology_hdr,
        skip_level_1=True,
    )

    # 2.2 Evaluated Infrastructure and Platform Perimeter (Asset Footprint)
    add_heading(
        doc,
        t("section_asset_perimeter_title", locale=doc_lang),
        level=2,
        primary_color_rgb=p_color_rgb,
    )
    add_body_paragraph(
        doc,
        t("asset_perimeter_intro", locale=doc_lang),
        text_color_rgb=text_color_rgb,
    )
    add_spacer(doc, 6)

    pillars = b_data.get("pillars_analysis", [])
    if pillars:
        fp_table = doc.add_table(rows=1, cols=2)
        fp_table.alignment = WD_TABLE_ALIGNMENT.LEFT
        fp_table.style = "Table Grid"

        fp_headers = [
            t("header_infrastructure_domain", locale=doc_lang),
            t("header_evaluated_perimeter_assets", locale=doc_lang),
        ]
        for i, h_txt in enumerate(fp_headers):
            set_cell_text_custom(
                fp_table.rows[0].cells[i],
                h_txt,
                align=WD_ALIGN_PARAGRAPH.CENTER,
                typography_role=TypographyRole.TABLE_HEADER,
                color_role=SemanticColorRole.TEXT_INVERSE,
                resolver=style_resolver,
            )
            shade_cell(fp_table.rows[0].cells[i], p_color_hex)

        fp_table.rows[0].cells[0].width = Cm(5.0)
        fp_table.rows[0].cells[1].width = Cm(11.4)

        from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
        resolver = get_taxonomy_resolver()

        for p_idx, p in enumerate(pillars):
            raw_pname = p.get("pillar_name", "Pillar")
            p_id = p.get("pillar_id")
            p_name = resolver.resolve_pillar_by_any_reference(
                p_id or raw_pname, default=raw_pname, locale=doc_lang
            )
            findings = p.get("health_check_asis", [])
            caps = []
            for f in findings:
                c = f.get("target_state") or f.get("capability")
                if c:
                    c_clean = c.split("(")[0].strip()
                    c_loc = resolver.resolve_capability_name(c_clean, default=c_clean, locale=doc_lang)
                    if c_loc and c_loc not in caps:
                        caps.append(c_loc)
            scope_desc = "; ".join(caps) if caps else t("default_evaluated_assets", locale=doc_lang)

            row = fp_table.add_row()
            set_cell_text_custom(row.cells[0], p_name, bold=True, font_size=8.5, color_role=SemanticColorRole.TEXT_PRIMARY, resolver=style_resolver)
            set_cell_text_custom(row.cells[1], scope_desc, font_size=8.5, color_role=SemanticColorRole.TEXT_PRIMARY, resolver=style_resolver, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

            row.cells[0].width = Cm(5.0)
            row.cells[1].width = Cm(11.4)

            if p_idx % 2 == 1:
                shade_cell(row.cells[0], alt_row_hex)
                shade_cell(row.cells[1], alt_row_hex)

        # Append dependent business operations row
        h_biz = t("header_dependent_business_workloads", locale=doc_lang)
        desc_biz = t("dependent_business_workloads_desc", locale=doc_lang)
        row_biz = fp_table.add_row()
        set_cell_text_custom(row_biz.cells[0], h_biz, bold=True, font_size=8.5, color_role=SemanticColorRole.TEXT_PRIMARY, resolver=style_resolver)
        set_cell_text_custom(row_biz.cells[1], desc_biz, font_size=8.5, color_role=SemanticColorRole.TEXT_PRIMARY, resolver=style_resolver, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

        row_biz.cells[0].width = Cm(5.0)
        row_biz.cells[1].width = Cm(11.4)
        if len(pillars) % 2 == 1:
            shade_cell(row_biz.cells[0], alt_row_hex)
            shade_cell(row_biz.cells[1], alt_row_hex)

        autofit_table_to_contents(fp_table)
        add_spacer(doc, 10)

    # Concluding benchmarking note for evaluated capability perimeter
    client_name = ctx.get("client_name", "Client")
    industry_name = ctx.get("industry") or t("default_industry_vertical", locale=doc_lang)
    bench_note = t(
        "asset_perimeter_benchmarking_note",
        locale=doc_lang,
        client_name=client_name,
        industry_name=industry_name,
    )
    add_body_paragraph(
        doc,
        bench_note,
        text_color_rgb=text_color_rgb,
    )
    add_spacer(doc, 15)

    # 2.3 Diagnostic Methodological Framework
    parse_and_append_markdown_section(
        doc,
        intro_file,
        p_color_rgb,
        text_color_rgb,
        start_header=methodology_hdr,
        skip_level_1=True,
    )


def compile_docx(tower_dir: str, output_path: str):
    """Assembles a DOCX report from modular source files and assessment data.

    Generates a styled DOCX report by orchestrating content from a structured
    directory of source files. The function integrates corporate branding profiles,
    internationalization (i18n) locales, assessment data (JSON, CSV), and
    narrative sections (Markdown) into a Word template. The final document
    includes a cover page, table of contents, executive summary, maturity
    analysis, quantitative risk matrix, and appendices.

    Args:
        tower_dir: The root directory path for a specific assessment. This
            directory must contain an `asis_modules` subdirectory with Markdown
            and CSV content, along with root-level JSON files for the assessment
            payload (e.g., `blueprint_*.json`) and scoring results
            (`scoring_output.json`).
        output_path: The full destination file path for the compiled DOCX document.
            The parent directory will be created if it does not exist.

    Returns:
        None. The document is generated and saved to the specified `output_path`.

    Raises:
        FileNotFoundError: If required input files or directories are not found.
        json.JSONDecodeError: If a JSON configuration or data file is malformed.
        ValueError: If data within a source file cannot be parsed into the
            expected numeric type.
    """
    tower_dir_obj = Path(tower_dir)
    modules_dir = tower_dir_obj / "asis_modules"

    logger.info(f"📦 Compiling AS-IS Technical Annex Word document from modules in: {modules_dir}")

    # Dynamically load corporate brand profiles based on the operational context.
    from assessment_engine.infrastructure.config_loader import load_brand_profile

    brand = load_brand_profile()

    company_name = brand.get("company_name", "Consultora")
    classification = brand.get("default_classification", "Confidencial")
    disclaimer_text = brand.get("disclaimer_text", "")

    styling = brand.get("styling", {})
    p_color_hex = styling.get("primary_color_hex", "0072BC")
    alt_row_hex = styling.get("alternate_row_color_hex", "F2F2F2")
    text_color_rgb = styling.get("text_dark_color_rgb", [46, 64, 77])

    #
    r_color = int(p_color_hex[0:2], 16)
    g_color = int(p_color_hex[2:4], 16)
    b_color = int(p_color_hex[4:6], 16)
    p_color_rgb = (r_color, g_color, b_color)

    #
    from assessment_engine.infrastructure.runtime_paths import (
        resolve_tower_annex_template_path,
    )

    template_path = resolve_tower_annex_template_path()
    try:
        doc = Document(str(template_path))
        logger.info("   ├─ Plantilla Word pre-estilizada cargada correctamente.")
    except Exception:
        doc = Document()
        logger.info("   ⚠️ Template not found. Initializing blank document.")

    # Initialize the document by removing all placeholder paragraphs and tables from the template.
    for p in list(doc.paragraphs):
        p._element.getparent().remove(p._element)
    for tbl in list(doc.tables):
        tbl._element.getparent().remove(tbl._element)

    # The `blueprint_payload` file path is resolved dynamically to support a multi-tenant architecture.
    payload_path = next(tower_dir_obj.glob("blueprint_*_payload.json"), None)
    if not payload_path:
        payload_path = tower_dir_obj / "blueprint_t2_payload.json"  #

    scoring_path = tower_dir_obj / "scoring_output.json"

    tower_name = "Unknown"
    client_name = "Client"
    global_fair_ale = 0.0
    global_score = 3.0
    global_band = "Defined"
    global_reading = ""
    client_group = None
    custom_overview_intro = None
    b_data: dict[str, Any] = {}

    #
    doc_lang = "en"
    from assessment_engine.infrastructure.localization import format_date_localized
    doc_date = format_date_localized(locale="en")
    doc_version = "1.0"
    currency = "€"
    is_critical = False

    # Local inline Markdown parser to cleanly render bold (**) and italics (_) inside bullet points.
    # Defined early here so it is in scope for any calls inside compile_docx.
    def add_markdown_bullet_local(text, space_after=4):
        p = doc.add_paragraph(style='Bullet')
        resolver_local = DocxStyleResolver.get_default(language_code=doc_lang)
        p.paragraph_format.space_after = resolver_local.resolve_pt(TypographyRole.TABLE_CELL)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        # Split on the first colon to find the heading label
        if ":" in text:
            label, body = text.split(":", 1)
            run_lbl = p.add_run(label + ":")
            resolver_local.apply_run_style(
                run_lbl,
                typo_role=TypographyRole.BODY_STRONG,
                color_role=SemanticColorRole.TEXT_PRIMARY,
                bold_override=True,
            )
        else:
            body = text

        # Parse bold parts (**) and italic parts (_)
        bold_parts = body.split("**")
        for b_idx, b_part in enumerate(bold_parts):
            is_bold = b_idx % 2 == 1

            italic_parts = b_part.split("_")
            for i_idx, i_part in enumerate(italic_parts):
                is_italic = i_idx % 2 == 1

                run = p.add_run(i_part)
                resolver_local.apply_run_style(
                    run,
                    typo_role=TypographyRole.BODY_REGULAR,
                    color_role=SemanticColorRole.TEXT_PRIMARY,
                    bold_override=is_bold,
                )
                run.italic = is_italic
        return p

    if payload_path.exists():
        with open(payload_path, "r", encoding="utf-8-sig") as f:
            b_data = json.load(f)
            tower_meta = b_data.get("document_meta", {})
            tower_name = tower_meta.get("tower_name", "Unknown")
            tower_id = tower_meta.get("tower_code", tower_meta.get("tower_id", "TXX"))
            raw_client_name = tower_meta.get("client_name", "Client")
            client_name = clean_client_name(raw_client_name)
            
            # Dynamically detect organizational scale to apply customized calibration.
            is_critical = brand.get("styling", {}).get("is_critical", None)
            if is_critical is None:
                is_critical = False # default fallback

            client_group = tower_meta.get("client_parent_group")  #
            global_fair_ale = b_data.get("total_fair_ale", 0.0)
            custom_overview_intro = b_data.get("platform_overview_intro")  #
            currency = (
                tower_meta.get("currency")
                or brand.get("currency_symbol")
                or currency
            )

            # Load internationalization (i18n) parameters from the input payload. The implementation avoids using default or hardcoded locales.
            doc_lang = tower_meta.get("language", "en").lower()

            vocab_fallback = _load_asis_vocab().get(doc_lang, _load_asis_vocab().get("en", {}))
            from assessment_engine.infrastructure.config_loader import resolve_localized_vocabulary
            vocab_loaded = resolve_localized_vocabulary(doc_lang)
            vocab = {**vocab_fallback, **vocab_loaded}

            doc_date = format_date_localized(tower_meta.get("date"), locale=doc_lang)
            doc_version = tower_meta.get("version", doc_version)
            currency = tower_meta.get("currency", currency)

            canonical_brand_vocab = resolve_localized_vocabulary(doc_lang)
            classification = canonical_brand_vocab.get(
                "default_classification", classification
            )
            disclaimer_text = canonical_brand_vocab.get(
                "disclaimer_text", disclaimer_text
            )
            global_reading = t("default_global_reading", locale=doc_lang)

    # Load client_intelligence.json
    intel_data = {}
    client_intel_file = (
        tower_dir_obj / "client_intelligence.json"
        if (tower_dir_obj / "client_intelligence.json").exists()
        else tower_dir_obj.parent / "client_intelligence.json"
    )
    if client_intel_file.exists():
        try:
            with open(client_intel_file, "r", encoding="utf-8-sig") as cif:
                intel_data = json.load(cif)
        except (OSError, ValueError, KeyError, AttributeError) as ex:

            logger.debug(f"[Fallback] Handled exception: {ex}")

    profile_sec = intel_data.get("profile", {}) if isinstance(intel_data, dict) else {}
    industry = profile_sec.get("industry", "Standard")
    industry_name = profile_sec.get(f"industry_type_{doc_lang}") or profile_sec.get("industry_type_en") or t("standard_sector_label", locale=doc_lang)

    curr_code = (
        tower_meta.get("currency_code")
        or ("USD" if currency == "$" else "GBP" if currency == "£" else "JPY" if currency == "¥" else "CHF" if currency == "CHF" else "EUR")
    )

    # standard Actuarial Practice: Dynamic Regulatory Mapping (Industry Routing)
    # The regulatory framework narrative is mapped dynamically to the client's industry sector.
    if "Financial" in industry or "Banking" in industry:
        reg_name = t("reg_desc_financial", locale=doc_lang)
        reg_fine_limit = format_currency(
            15000000.0,
            currency_code=curr_code,
            currency_symbol=currency,
            locale=doc_lang,
            decimals=0,
        )
    elif "Energy" in industry or "Critical Infrastructure" in industry:
        reg_name = t("reg_desc_critical_infra", locale=doc_lang)
        reg_fine_limit = format_currency(
            10000000.0,
            currency_code=curr_code,
            currency_symbol=currency,
            locale=doc_lang,
            decimals=0,
        )
    elif "Telecommunications" in industry or "Media" in industry:
        reg_name = t("reg_desc_telecom", locale=doc_lang)
        reg_fine_limit = format_currency(
            5000000.0,
            currency_code=curr_code,
            currency_symbol=currency,
            locale=doc_lang,
            decimals=0,
        )
    elif "Healthcare" in industry:
        reg_name = t("reg_desc_healthcare", locale=doc_lang)
        reg_fine_limit = format_currency(
            5000000.0,
            currency_code=curr_code,
            currency_symbol=currency,
            locale=doc_lang,
            decimals=0,
        )
    else:
        reg_name = t("reg_desc_general", locale=doc_lang)
        reg_fine_limit = format_currency(
            2000000.0,
            currency_code=curr_code,
            currency_symbol=currency,
            locale=doc_lang,
            decimals=0,
        )

    if scoring_path.exists():
        with open(scoring_path, "r", encoding="utf-8-sig") as f:
            s_data = json.load(f)
            global_score = float(s_data.get("tower_score_exact", 3.0))
            from assessment_engine.domain.maturity_band import (
                ANNEX_MATURITY_BANDS,
                resolve_maturity_band,
            )
            band_info = resolve_maturity_band(global_score, ANNEX_MATURITY_BANDS, locale=doc_lang)
            global_band = band_info["label"]

            # Universal numeric scoring bracket mapping (zero substring dependency across languages)
            if global_score < 1.80:
                desc_key = "desc_band_initial"
            elif global_score < 2.60:
                desc_key = "desc_band_repeatable"
            elif global_score < 3.40:
                desc_key = "desc_band_defined"
            elif global_score < 4.20:
                desc_key = "desc_band_managed"
            else:
                desc_key = "desc_band_optimized"

            global_reading = t(desc_key, locale=doc_lang)

    org_label = t("lbl_holding", locale=doc_lang) if client_group else t("lbl_organization", locale=doc_lang)

    doc_ctx: dict[str, Any] = {
        "p_color_rgb": p_color_rgb,
        "text_color_rgb": text_color_rgb,
        "p_color_hex": p_color_hex,
        "alt_row_hex": alt_row_hex,
        "vocab": vocab,
        "tower_name": tower_name,
        "client_name": client_name,
        "client_group": client_group,
        "classification": classification,
        "doc_date": doc_date,
        "doc_version": doc_version,
        "modules_dir": modules_dir,
        "currency": currency,
        "is_critical": is_critical,
        "industry": industry,
        "industry_name": industry_name,
        "doc_lang": doc_lang,
        "company_name": company_name,
        "tower_dir_obj": tower_dir_obj,
        "payload_path": payload_path,
        "global_fair_ale": global_fair_ale,
        "b_data": b_data,
        "global_score": global_score,
        "global_band": global_band,
        "global_reading": global_reading,
        "custom_overview_intro": custom_overview_intro,
        "intel_data": intel_data,
        "tower_id": tower_id,
        "reg_name": reg_name,
    }

    _compile_cover_and_toc(doc, doc_ctx)
    _compile_introduction_and_scope(doc, doc_ctx)

    #
    _compile_chapter_3_maturity_profile(doc, doc_ctx)

    ch4_res = _compile_chapter_4_fair_risk_matrix(doc, doc_ctx)
    ch5_ctx = {
        **doc_ctx,
        **ch4_res,
    }
    _compile_chapter_5_conclusions(doc, ch5_ctx)
    _compile_appendices(doc, doc_ctx)

    # Insert a field code to instruct the host application to update the Table of Contents upon opening.
    set_update_fields(doc)

    #
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    logger.info(
        f"🎉 AS-IS Technical Annex Word document COMPILED successfully at: {output_path}!"
    )

    try:
        from assessment_engine.infrastructure.artifacts import (
            ArtifactContext,
            ArtifactFormat,
            DocumentType,
        )
        from assessment_engine.infrastructure.runtime_paths import (
            resolve_artifact_registry,
            resolve_assessment_id,
            resolve_assessment_period,
        )

        tenant_id = client_name or "generic_client"
        asmt_id = resolve_assessment_id(tower_meta.get("assessment_id"))
        asmt_period = resolve_assessment_period(tower_meta.get("period"))

        ctx = ArtifactContext(
            tenant_id=tenant_id,
            assessment_id=asmt_id,
            period=asmt_period,
            domain_unit_id=f"tower_{tower_id.lower()}",
            doc_type=DocumentType.TECHNICAL_ANNEX,
            locale=doc_lang,
            extension=ArtifactFormat.DOCX,
        )
        registry = resolve_artifact_registry(client_id=tenant_id, assessment_id=asmt_id)
        registry.register_artifact(
            ctx=ctx,
            source_file_path=output_path_obj,
            generator_engine="compile_asis_docx_from_modules",
            presentation_metadata={
                "tenant_display_name": client_name,
                "domain_unit_display": tower_name,
                "doc_title_localized": t("lbl_technical_annex", locale=doc_lang),
            },
        )
    except Exception as ex:
        logger.debug("ArtifactRegistry technical annex registration skipped: %s", ex)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        logger.info(
            "Uso: python compile_asis_docx_from_modules.py <tower_dir> <output_doc.docx>"
        )
        sys.exit(1)
    compile_docx(sys.argv[1], sys.argv[2])
