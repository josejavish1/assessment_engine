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
from docx.shared import Inches, Pt, RGBColor, Cm

from assessment_engine.infrastructure.docx_render_utils import (
    autofit_table_to_contents,
    finalize_table,
    set_cell_text,
    shade_cell,
)
from assessment_engine.infrastructure.text_utils import clean_text_for_word, format_date_spanish
from assessment_engine.infrastructure.localization import (
    format_currency,
    format_number,
    t,
)

# Re-export primitives and constants from asis_docx_primitives for 100% backward compatibility
from assessment_engine.adapters.compilers.asis_docx_primitives import (
    COLOR_BLUE,
    COLOR_HEADER_BG,
    COLOR_ROW_ALT,
    LANG_VOCAB,
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

# Import decoupled chapter compilers
from assessment_engine.adapters.compilers.asis_maturity_chapter import _compile_chapter_3_maturity_profile
from assessment_engine.adapters.compilers.asis_fair_chapter import _compile_chapter_4_fair_risk_matrix
from assessment_engine.adapters.compilers.asis_conclusions_chapter import _compile_chapter_5_conclusions
from assessment_engine.adapters.compilers.asis_appendices_chapter import _compile_appendices

def _compile_cover_and_toc(doc: Any, ctx: dict[str, Any]) -> None:
    """Render Section 0 (Corporate Cover Page) and Section 0.1 (Table of Contents)."""
    p_color_rgb = ctx["p_color_rgb"]
    text_color_rgb = ctx["text_color_rgb"]
    doc_lang = ctx.get("doc_lang", "es")

    add_spacer(doc, 200)

    p_title = doc.add_paragraph()
    run_title = p_title.add_run(t("title", locale=doc_lang))
    run_title.bold = True
    run_title.font.name = "Arial"
    run_title.font.size = Pt(36)
    run_title.font.color.rgb = RGBColor(*text_color_rgb)

    p_sub = doc.add_paragraph()
    sub_prefix = t("annex_technical_prefix", locale=doc_lang)
    run_sub = p_sub.add_run(f"{sub_prefix} {ctx['tower_name']}")
    run_sub.font.name = "Arial"
    run_sub.font.size = Pt(20)
    run_sub.font.color.rgb = RGBColor(*p_color_rgb)

    add_spacer(doc, 140)

    p_client = doc.add_paragraph()
    client_label = t("client_lbl", locale=doc_lang)
    run_cli_lbl = p_client.add_run(client_label)
    run_cli_lbl.bold = True
    run_cli_lbl.font.name = "Arial"
    run_cli_lbl.font.size = Pt(28)
    run_cli_lbl.font.color.rgb = RGBColor(*text_color_rgb)

    if ctx.get("client_group"):
        run_cli = p_client.add_run(f"{ctx['client_name'].upper()} ({ctx['client_group']})")
    else:
        run_cli = p_client.add_run(f"{ctx['client_name'].upper()}")
    run_cli.bold = True
    run_cli.font.name = "Arial"
    run_cli.font.size = Pt(28)
    run_cli.font.color.rgb = RGBColor(0, 114, 188)

    p_proj = doc.add_paragraph()
    proj_label = t("proj_lbl", locale=doc_lang)
    project_title = t("project", locale=doc_lang)
    if project_title:
        run_proj_lbl = p_proj.add_run(proj_label)
        run_proj_lbl.bold = True
        run_proj_lbl.font.name = "Arial"
        run_proj_lbl.font.size = Pt(14)
        run_proj_lbl.font.color.rgb = RGBColor(*text_color_rgb)

        run_proj = p_proj.add_run(f"{project_title}")
        run_proj.font.name = "Arial"
        run_proj.font.size = Pt(14)
        run_proj.font.color.rgb = RGBColor(*text_color_rgb)

    add_spacer(doc, 140)

    classification_clean = ctx["classification"].replace(" (Tier-1 Assessment)", "")
    version_label = t("v_lbl", locale=doc_lang)

    p_footer = doc.add_paragraph()
    company_prefix = f"{ctx['company_name'].upper()} | " if ctx.get("company_name") else ""
    run_date = p_footer.add_run(
        f"{company_prefix}{ctx['doc_date']} | {version_label}{ctx['doc_version']} | {classification_clean}"
    )
    run_date.font.name = "Arial"
    run_date.font.size = Pt(9.5)
    run_date.font.color.rgb = RGBColor(150, 150, 150)

    doc.add_page_break()

    # Section 0.1: Table of Contents (TOC).
    toc_heading = t("toc_title", locale=doc_lang)
    add_heading(doc, toc_heading, level=4, primary_color_rgb=p_color_rgb)
    add_toc(doc)


def _compile_introduction_and_scope(doc: Any, ctx: dict[str, Any]) -> None:
    """Render Chapter 1 (Executive Summary intro) and Chapter 2 (Methodology, Scope, Objectives)."""
    p_color_rgb = ctx["p_color_rgb"]
    text_color_rgb = ctx["text_color_rgb"]
    vocab = ctx["vocab"]
    modules_dir = ctx["modules_dir"]

    # Assemble and render Chapter 1: Executive Summary and Business Context.
    parse_and_append_markdown_section(
        doc, modules_dir / "02_resumen_ejecutivo.md", p_color_rgb, text_color_rgb
    )

    # Assemble and render Chapter 2: Objective, Scope, and Assessment Methodology.
    add_heading(
        doc,
        vocab.get("methodology_chapter_title", "Marco de Referencia, Objetivos y Alcance del Assessment"),
        level=1,
        primary_color_rgb=p_color_rgb,
    )
    parse_and_append_markdown_section(
        doc,
        modules_dir / "01_introduccion.md",
        p_color_rgb,
        text_color_rgb,
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

    logger.info(f"📦 Compilando Anexo Técnico AS-IS Word desde módulos en: {modules_dir}")

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
        logger.info("   ⚠️ No se encontró plantilla. Inicializando documento en blanco.")

    # Initialize the document by removing all placeholder paragraphs and tables from the template.
    for p in list(doc.paragraphs):
        p._element.getparent().remove(p._element)
    for t in list(doc.tables):
        t._element.getparent().remove(t._element)

    # The `blueprint_payload` file path is resolved dynamically to support a multi-tenant architecture.
    payload_path = next(tower_dir_obj.glob("blueprint_*_payload.json"), None)
    if not payload_path:
        payload_path = tower_dir_obj / "blueprint_t2_payload.json"  #

    scoring_path = tower_dir_obj / "scoring_output.json"

    tower_name = "Desconocida"
    client_name = "Cliente"
    global_fair_ale = 0.0
    global_score = 3.0
    global_band = "Definido"
    global_reading = "Prácticas operativas consolidadas."
    client_group = None
    custom_overview_intro = None
    b_data: dict[str, Any] = {}

    #
    doc_lang = "es"  #
    doc_date = format_date_spanish()
    doc_version = "1.0"
    currency = "€"
    is_critical = False

    # Local inline Markdown parser to cleanly render bold (**) and italics (_) inside bullet points.
    # Defined early here so it is in scope for any calls inside compile_docx.
    def add_markdown_bullet_local(text, space_after=4):
        p = doc.add_paragraph(style='Bullet')
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        # Split on the first colon to find the heading label
        if ":" in text:
            label, body = text.split(":", 1)
            run_lbl = p.add_run(label + ":")
            run_lbl.bold = True
            run_lbl.font.name = "Arial"
            run_lbl.font.size = Pt(9.5)
            run_lbl.font.color.rgb = RGBColor(*text_color_rgb)
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
                run.bold = is_bold
                run.italic = is_italic
                run.font.name = "Arial"
                run.font.size = Pt(9.5)
                run.font.color.rgb = RGBColor(*text_color_rgb)
        return p

    if payload_path.exists():
        with open(payload_path, "r", encoding="utf-8-sig") as f:
            b_data = json.load(f)
            tower_meta = b_data.get("document_meta", {})
            tower_name = tower_meta.get("tower_name", "Desconocida")
            tower_id = tower_meta.get("tower_code", tower_meta.get("tower_id", "TXX"))
            raw_client_name = tower_meta.get("client_name", "Cliente")
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
            doc_lang = tower_meta.get("language", "es").lower()

            vocab_fallback = _load_asis_vocab().get(doc_lang, _load_asis_vocab().get("es", {}))
            from assessment_engine.infrastructure.config_loader import resolve_localized_vocabulary
            vocab_loaded = resolve_localized_vocabulary(doc_lang)
            vocab = {**vocab_fallback, **vocab_loaded}

            doc_date = format_date_spanish(tower_meta.get("date"))
            doc_version = tower_meta.get("version", doc_version)
            currency = tower_meta.get("currency", currency)

            # Resolve localized brand attributes from canonical vocabulary
            canonical_brand_vocab = resolve_localized_vocabulary(doc_lang)
            classification = canonical_brand_vocab.get(
                "default_classification", classification
            )
            disclaimer_text = canonical_brand_vocab.get(
                "disclaimer_text", disclaimer_text
            )

    # Load client_intelligence.json
    intel_data = {}
    client_intel_file = tower_dir_obj.parent / "client_intelligence.json"
    if client_intel_file.exists():
        try:
            with open(client_intel_file, "r", encoding="utf-8-sig") as cif:
                intel_data = json.load(cif)
        except (OSError, ValueError, KeyError, AttributeError) as ex:

            logger.debug(f"[Fallback] Excepción controlada: {ex}")

    profile_sec = intel_data.get("profile", {}) if isinstance(intel_data, dict) else {}
    industry = profile_sec.get("industry", "Standard")
    industry_name = (
        profile_sec.get("industry_type_es", "Sector Estándar")
        if doc_lang == "es"
        else profile_sec.get("industry_type_en", "Standard Industry")
    )

    from assessment_engine.infrastructure.localization import (
        format_currency,
        t,
    )

    # standard Actuarial Practice: Dynamic Regulatory Mapping (Industry Routing)
    # The regulatory framework narrative is mapped dynamically to the client's industry sector.
    if "Financial" in industry or "Banking" in industry:
        reg_name = t(
            "reg_desc_financial",
            locale=doc_lang,
            default=(
                "las regulaciones vigentes de resiliencia operativa financiera (v.g. DORA o normativas de banca central)"
                if doc_lang == "es"
                else "financial operational resilience regulations (e.g. DORA or central bank mandates)"
            ),
        )
        reg_fine_limit = format_currency(
            15000000.0,
            currency_code="EUR",
            currency_symbol=currency,
            locale=doc_lang,
            decimals=0,
        )
    elif "Energy" in industry or "Critical Infrastructure" in industry:
        reg_name = t(
            "reg_desc_critical_infra",
            locale=doc_lang,
            default=(
                "los marcos normativos de protección de infraestructuras críticas (v.g. Directiva NIS2 o leyes de seguridad nacional)"
                if doc_lang == "es"
                else "critical infrastructure protection frameworks (e.g. NIS2 Directive or national security laws)"
            ),
        )
        reg_fine_limit = format_currency(
            10000000.0,
            currency_code="EUR",
            currency_symbol=currency,
            locale=doc_lang,
            decimals=0,
        )
    elif "Telecommunications" in industry or "Media" in industry:
        reg_name = t(
            "reg_desc_telecom",
            locale=doc_lang,
            default=(
                "los marcos regulatorios sectoriales de Telecomunicaciones, Media y soberanía de datos"
                if doc_lang == "es"
                else "sectoral regulatory frameworks for Telecommunications, Media, and data sovereignty"
            ),
        )
        reg_fine_limit = format_currency(
            5000000.0,
            currency_code="EUR",
            currency_symbol=currency,
            locale=doc_lang,
            decimals=0,
        )
    elif "Healthcare" in industry:
        reg_name = t(
            "reg_desc_healthcare",
            locale=doc_lang,
            default=(
                "las regulaciones de protección de datos de salud y privacidad (v.g. HIPAA o marcos locales equivalentes)"
                if doc_lang == "es"
                else "healthcare data protection and privacy regulations (e.g. HIPAA or equivalent local frameworks)"
            ),
        )
        reg_fine_limit = format_currency(
            5000000.0,
            currency_code="EUR",
            currency_symbol=currency,
            locale=doc_lang,
            decimals=0,
        )
    else:
        reg_name = t(
            "reg_desc_general",
            locale=doc_lang,
            default=(
                "los marcos generales de protección de datos y privacidad (v.g. RGPD o legislación sectorial estándar)"
                if doc_lang == "es"
                else "general data protection and privacy frameworks (e.g. GDPR or standard sectoral legislation)"
            ),
        )
        reg_fine_limit = format_currency(
            2000000.0,
            currency_code="EUR",
            currency_symbol=currency,
            locale=doc_lang,
            decimals=0,
        )

    if scoring_path.exists():
        with open(scoring_path, "r", encoding="utf-8-sig") as f:
            s_data = json.load(f)
            global_score = s_data.get("tower_score_exact", 3.0)
            global_band = s_data.get("maturity_band_from_exact", {}).get(
                "label", "Definido"
            )
            global_reading = s_data.get("maturity_band_from_exact", {}).get(
                "reading", "Gobernanza estándar."
            )

    org_label = (
        "holding" if client_group else ("group" if doc_lang == "en" else "organización")
    )

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
        f"🎉 ¡Anexo Técnico AS-IS COMPILADO modularmente con éxito en: {output_path}!"
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        logger.info(
            "Uso: python compile_asis_docx_from_modules.py <tower_dir> <output_doc.docx>"
        )
        sys.exit(1)
    compile_docx(sys.argv[1], sys.argv[2])
