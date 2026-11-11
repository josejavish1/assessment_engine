"""Actuarial Open FAIR quantitative risk matrix chapter builder for Word DOCX."""
from __future__ import annotations

import csv
import json
import logging
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Final

from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches

from assessment_engine.adapters.compilers.asis_docx_primitives import (
    COLOR_BLUE,
    Chapter4Result,
    DocumentCompilationContext,
    _add_markdown_bullet,
    add_body_paragraph,
    add_heading,
    add_spacer,
    set_cell_border_white,
    set_cell_text_custom,
)
from assessment_engine.adapters.compilers.ast_table_builders import (
    HEATMAP_SEVERITY_HIGH_HEX,
    HEATMAP_SEVERITY_LOW_HEX,
    HEATMAP_SEVERITY_MED_HEX,
)
from assessment_engine.adapters.emitters.docx_style_resolver import DocxStyleResolver
from assessment_engine.domain.actuarial_scale_calibrator import (
    HEATMAP_SEVERITY_HIGH_THRESHOLD,
    HEATMAP_SEVERITY_MED_THRESHOLD,
    MAX_MONETARY_LM_CUTOFF,
    MIN_MONETARY_LM_CUTOFF,
    MONETARY_CUTOFF_SCALE_RATIO,
    TEF_RESILIENCE_HIGH_THRESHOLD,
    TEF_RESILIENCE_MED_THRESHOLD,
    clamp_scale_level,
    compute_dynamic_lm_brackets,
    compute_dynamic_lm_thresholds,
    resolve_dynamic_lm_scale_level,
    resolve_dynamic_tef_scale_level,
    resolve_risk_matrix_coordinates,
    safe_float,
)
from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
from assessment_engine.domain.theme_registry import SemanticColorRole, TypographyRole
from assessment_engine.infrastructure.docx_render_utils import (
    finalize_table,
    shade_cell,
)
from assessment_engine.infrastructure.localization import (
    apply_vocabulary_substitutions,
    get_localized_list,
    t,
)
from assessment_engine.infrastructure.text_utils import clean_text_for_word

TIER1_THRESHOLD_MULTIPLIER: Final[float] = 1.5
TIER2_THRESHOLD_MULTIPLIER: Final[float] = 0.5

HEATMAP_HEADER_COL_WIDTH_IN: Final[float] = 1.30
HEATMAP_DATA_COL_WIDTH_IN: Final[float] = 1.04
HEATMAP_ROW_HEIGHT_CM: Final[float] = 0.40
HEATMAP_CELL_FONT_SIZE_PT: Final[float] = 8.0
SUMMARY_TABLE_FONT_SIZE_PT: Final[float] = 8.0
RISK_SUMMARY_COL_WIDTHS_CM: Final[tuple[float, ...]] = (2.2, 5.1, 3.4, 2.0, 2.0, 1.8)
DEFAULT_RISK_SUMMARY_HEADERS: Final[tuple[str, ...]] = (
    "ID",
    "Evaluated Risk / Asset",
    "Pillar",
    "Frequency (TEF)",
    "Outage Cost (P90)",
    "Annual Loss (ALE)",
)
RISK_CARD_HANGING_INDENT_IN: Final[float] = 0.12
CANONICAL_LEF_HEADER_TOKENS: Final[tuple[str, ...]] = ("lef", "events", "year", "annual")
DEFAULT_CURRENCY_FALLBACK: Final[str] = "EUR"

SPACER_SMALL_PT: Final[int] = 8
SPACER_MEDIUM_PT: Final[int] = 10
SPACER_STANDARD_PT: Final[int] = 15
SPACER_LARGE_PT: Final[int] = 20
BULLET_SPACE_DEFAULT_PT: Final[int] = 4
HEXAGON_BULLET_SPACE_PT: Final[int] = 3
HEXAGON_LAST_BULLET_SPACE_PT: Final[int] = 12

logger = logging.getLogger(__name__)


def _resolve_chapter4_financial_context(
    ctx: DocumentCompilationContext,
    b_data: dict[str, Any],
    custom_calibration: dict[str, Any],
    doc_lang: str,
) -> tuple[float | None, float | None]:
    """Resolves authoritative annual_revenue and hourly_downtime_cost across all payload layers."""
    fin_tel = b_data.get("financial_telemetry") or {}
    doc_meta = b_data.get("document_meta") or {}

    annual_rev = (
        safe_float(ctx.get("annual_revenue"), locale=doc_lang)
        or safe_float(custom_calibration.get("annual_revenue"), locale=doc_lang)
        or safe_float(fin_tel.get("consolidated_annual_revenue"), locale=doc_lang)
        or safe_float(fin_tel.get("annual_revenue"), locale=doc_lang)
        or safe_float(b_data.get("annual_revenue"), locale=doc_lang)
        or safe_float(doc_meta.get("annual_revenue"), locale=doc_lang)
    )
    hourly_burn = (
        safe_float(ctx.get("hourly_downtime_cost"), locale=doc_lang)
        or safe_float(ctx.get("hourly_burn_rate"), locale=doc_lang)
        or safe_float(custom_calibration.get("hourly_downtime_cost"), locale=doc_lang)
        or safe_float(custom_calibration.get("hourly_burn_rate"), locale=doc_lang)
        or safe_float(fin_tel.get("authoritative_hourly_downtime_cost"), locale=doc_lang)
        or safe_float(b_data.get("hourly_downtime_rate"), locale=doc_lang)
        or safe_float(b_data.get("hourly_burn_rate"), locale=doc_lang)
    )
    return annual_rev, hourly_burn


def _format_integer_currency_safe(
    val: Any,
    t_sep: str = ".",
    d_sep: str = ",",
    locale: str | None = None,
) -> str:
    """Safely formats a numeric value as an integer currency string (or 2-decimal sub-unit if < 1.0)."""
    clean_val = safe_float(val, locale=locale) or 0.0
    if 0.0 < clean_val < 1.0:
        try:
            sub_unit = Decimal(str(clean_val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if sub_unit >= Decimal("1.00"):
                return "1"
            if sub_unit <= Decimal("0.00"):
                return "0"
            return f"{sub_unit:.2f}".replace(".", d_sep)
        except (InvalidOperation, ValueError, OverflowError):
            return "0"
    try:
        rounded = int(Decimal(str(clean_val)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError, OverflowError):
        rounded = 0
    if t_sep:
        return f"{rounded:,}".replace(",", t_sep)
    return str(rounded)


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
    precomputed_lm_bounds: tuple[float, float, float, float] | None = None,
) -> None:
    """Renders the 5x5 quantitative risk heatmap table as a visual synthesis."""
    if not risks_data_list:
        return

    industry_name = (
        str(ctx.get("industry") or ctx.get("industry_name") or "").strip()
        or t("default_industry_name", locale=doc_lang)
    )
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
    add_spacer(doc, SPACER_STANDARD_PT)

    annual_rev, hourly_burn = _resolve_chapter4_financial_context(
        ctx=ctx,
        b_data=ctx.get("b_data", {}),
        custom_calibration=ctx.get("custom_calibration", {}),
        doc_lang=doc_lang,
    )
    dynamic_lm_bounds = precomputed_lm_bounds or compute_dynamic_lm_thresholds(
        currency=currency,
        annual_revenue=annual_rev,
        hourly_downtime_cost=hourly_burn,
        is_critical_tier=is_critical,
        locale=doc_lang,
    )
    lm_ranges = compute_dynamic_lm_brackets(
        currency=currency,
        locale=doc_lang,
        annual_revenue=annual_rev,
        hourly_downtime_cost=hourly_burn,
        is_critical_tier=is_critical,
        precomputed_thresholds=dynamic_lm_bounds,
    )

    matrix_cells = {r: {c: [] for c in range(1, 6)} for r in range(5, 0, -1)}
    for r in risks_data_list:
        r_tef, r_lm = resolve_risk_matrix_coordinates(r, dynamic_lm_bounds, locale=doc_lang)
        risk_id = str(r.get("id") or r.get("risk_id") or "").strip()
        if risk_id:
            matrix_cells[r_tef][r_lm].append(risk_id)

    heatmap_table = doc.add_table(rows=6, cols=6)
    heatmap_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    finalize_table(heatmap_table)

    resolver = DocxStyleResolver.get_default(language_code=doc_lang)
    header_hex = str(ctx.get("p_color_hex") or COLOR_BLUE).lstrip("#")
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
    shade_cell(cell_0_0, header_hex)
    set_cell_border_white(cell_0_0)
    cell_0_0.width = Inches(HEATMAP_HEADER_COL_WIDTH_IN)
    cell_0_0.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    for col_idx in range(1, 6):
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
        shade_cell(cell, header_hex)
        set_cell_border_white(cell)
        cell.width = Inches(HEATMAP_DATA_COL_WIDTH_IN)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    tef_ranges = {
        5: t("tef_annual_freq_5", locale=doc_lang),
        4: t("tef_annual_freq_4", locale=doc_lang),
        3: t("tef_annual_freq_3", locale=doc_lang),
        2: t("tef_annual_freq_2", locale=doc_lang),
        1: t("tef_annual_freq_1", locale=doc_lang),
    }

    for row_idx, tef_val in enumerate(range(5, 0, -1), 1):
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
        shade_cell(cell_header, header_hex)
        set_cell_border_white(cell_header)
        cell_header.width = Inches(HEATMAP_HEADER_COL_WIDTH_IN)
        cell_header.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

        for col_idx, lm_val in enumerate(range(1, 6), 1):
            cell = heatmap_table.rows[row_idx].cells[col_idx]
            cell.width = Inches(HEATMAP_DATA_COL_WIDTH_IN)
            heatmap_table.rows[row_idx].height = Cm(HEATMAP_ROW_HEIGHT_CM)

            cell_risks = matrix_cells[tef_val][lm_val]
            cell_text = ", ".join(cell_risks) if cell_risks else "-"

            set_cell_text_custom(
                cell,
                cell_text,
                bold=True,
                font_size=HEATMAP_CELL_FONT_SIZE_PT,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            set_cell_border_white(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            severity = tef_val * lm_val
            if severity >= HEATMAP_SEVERITY_HIGH_THRESHOLD:
                shade_cell(cell, HEATMAP_SEVERITY_HIGH_HEX)
            elif severity >= HEATMAP_SEVERITY_MED_THRESHOLD:
                shade_cell(cell, HEATMAP_SEVERITY_MED_HEX)
            else:
                shade_cell(cell, HEATMAP_SEVERITY_LOW_HEX)

    heatmap_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    add_spacer(doc, SPACER_LARGE_PT)


def _compile_chapter_4_fair_risk_matrix(doc: Any, ctx: DocumentCompilationContext) -> Chapter4Result:
    """Assemble and render Chapter 4: Quantitative Risk Matrix."""
    p_color_rgb = ctx["p_color_rgb"]
    text_color_rgb = ctx["text_color_rgb"]
    p_color_hex = ctx["p_color_hex"]
    alt_row_hex = ctx["alt_row_hex"]
    vocab = ctx["vocab"]
    modules_dir = ctx["modules_dir"]
    doc_lang = ctx["doc_lang"]
    is_critical = ctx.get("is_critical", False)
    global_fair_ale = ctx["global_fair_ale"]
    b_data = ctx.get("b_data") or {}
    tower_dir_obj = Path(ctx.get("tower_dir_obj", Path(".")))
    client_name = ctx["client_name"]
    reg_name = ctx.get("reg_name", t("applicable_regulations_default", locale=doc_lang))

    total_p90 = 0.0
    formatted_ale_item = "0"
    formatted_p90 = "0"
    t_sep = vocab.get("thousands_sep", ".")
    d_sep = vocab.get("decimal_sep", ",")

    def add_markdown_bullet_local(text: str, space_after: int = BULLET_SPACE_DEFAULT_PT) -> Any:
        return _add_markdown_bullet(doc, text, text_color_rgb, space_after)

    add_heading(doc, vocab["risk_matrix_title"], level=1, primary_color_rgb=p_color_rgb)

    formatted_ale = _format_integer_currency_safe(global_fair_ale, t_sep, d_sep, locale=doc_lang)

    # Resolve client_id and custom calibration strictly via compilation context (100% thread-safe)
    doc_meta = b_data.get("document_meta") or {}
    client_id = str(
        ctx.get("client_id")
        or doc_meta.get("client_id")
        or client_name.lower().replace(" ", "_")
    ).strip()
    tower_id = str(doc_meta.get("tower_code") or ctx.get("tower_id") or "T1").strip()

    # Check tower-specific profile first, then tenant-level profile in parent dir (never sibling towers)
    custom_profile_path = tower_dir_obj / "custom_risk_profile.json"
    if not custom_profile_path.exists() and tower_dir_obj.parent.exists():
        tenant_level_profile = tower_dir_obj.parent / "custom_risk_profile.json"
        if tenant_level_profile.exists():
            custom_profile_path = tenant_level_profile

    custom_calibration: dict[str, Any] = {}
    if custom_profile_path.exists():
        try:
            with open(custom_profile_path, "r", encoding="utf-8-sig") as cf:
                loaded_profile = json.load(cf)
            if isinstance(loaded_profile, dict):
                custom_calibration = loaded_profile
        except (OSError, ValueError, KeyError, AttributeError) as ex:
            logger.debug("[Fallback] Handled exception reading custom risk profile: %s", ex)

    currency = (
        ctx.get("currency")
        or custom_calibration.get("currency_symbol")
        or doc_meta.get("currency")
        or (b_data.get("financial_telemetry") or {}).get("currency")
    )
    if not currency:
        from assessment_engine.adapters.generate_asis_markdown_modules import (
            resolve_client_currency_context,
        )
        resolved_curr, _ = resolve_client_currency_context(client_id)
        currency = resolved_curr or DEFAULT_CURRENCY_FALLBACK

    annual_rev, hourly_burn = _resolve_chapter4_financial_context(
        ctx=ctx,
        b_data=b_data,
        custom_calibration=custom_calibration,
        doc_lang=doc_lang,
    )
    local_ctx: DocumentCompilationContext = {
        **ctx,
        "custom_calibration": custom_calibration,
        "annual_revenue": annual_rev,
        "hourly_downtime_cost": hourly_burn,
    }
    dynamic_lm_bounds = compute_dynamic_lm_thresholds(
        currency=str(currency),
        annual_revenue=annual_rev,
        hourly_downtime_cost=hourly_burn,
        is_critical_tier=is_critical,
        locale=doc_lang,
    )

    # Calculate aggregate Tail Risk (P90 and Max Probable Loss)
    total_p90 = 0.0
    total_max = 0.0
    for pillar in b_data.get("pillars_analysis", []):
        for hc in pillar.get("health_check_asis", []):
            p90_raw = safe_float(hc.get("fair_p90_score"), locale=doc_lang)
            max_raw = safe_float(hc.get("fair_max_score"), locale=doc_lang)
            if p90_raw is not None:
                total_p90 += p90_raw
            if max_raw is not None:
                total_max += max_raw

    if total_p90 <= 0.0:
        explicit_p90 = safe_float(b_data.get("total_fair_p90"), locale=doc_lang, allow_zero=True)
        total_p90 = explicit_p90 if explicit_p90 is not None and explicit_p90 > 0.0 else 0.0
    if total_max <= 0.0:
        explicit_max = safe_float(b_data.get("total_fair_max"), locale=doc_lang, allow_zero=True)
        total_max = explicit_max if explicit_max is not None and explicit_max > 0.0 else 0.0

    formatted_p90 = _format_integer_currency_safe(total_p90, t_sep, d_sep, locale=doc_lang) if total_p90 > 0 else "UNQUANTIFIED"
    formatted_max = _format_integer_currency_safe(total_max, t_sep, d_sep, locale=doc_lang) if total_max > 0 else "UNQUANTIFIED"

    intro_prose_p1 = t("fair_intro_prose_p1", locale=doc_lang)
    intro_prose_p2 = t("fair_intro_prose_p2", locale=doc_lang, client_name=client_name, formatted_ale=formatted_ale, currency=currency)
    intro_prose_p3 = t("fair_intro_prose_p3", locale=doc_lang, reg_name=reg_name, formatted_p90=formatted_p90, formatted_max=formatted_max, currency=currency)
    intro_prose_p4 = t("fair_intro_prose_p4", locale=doc_lang, reg_name=reg_name)

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
    add_spacer(doc, SPACER_SMALL_PT)

    lbl_metrics_intro = t("fair_guide_intro", locale=doc_lang)
    add_body_paragraph(doc, lbl_metrics_intro, text_color_rgb=text_color_rgb)
    for g_bullet in get_localized_list("fair_guide_bullets", locale=doc_lang):
        add_body_paragraph(doc, g_bullet, style="List Bullet", text_color_rgb=text_color_rgb)
    add_spacer(doc, SPACER_STANDARD_PT)

    # Build a lookup map from in-memory blueprint payload findings FIRST (decoupled from disk existence)
    fair_lookup: dict[str, dict[str, Any]] = {}
    for pillar in b_data.get("pillars_analysis", []):
        for hc in pillar.get("health_check_asis", []):
            cap_name = hc.get("capability")
            if cap_name:
                f_tef = safe_float(hc.get("fair_tef_score"), locale=doc_lang, allow_zero=True)
                f_lef = safe_float(hc.get("lef"), locale=doc_lang, allow_zero=True)
                fair_lookup[cap_name] = {
                    "p90": safe_float(hc.get("fair_p90_score"), locale=doc_lang, allow_zero=True) or 0.0,
                    "min": safe_float(hc.get("fair_min_score"), locale=doc_lang, allow_zero=True) or 0.0,
                    "max": safe_float(hc.get("fair_max_score"), locale=doc_lang, allow_zero=True) or 0.0,
                    "lef": f_tef if f_tef is not None else f_lef,
                    "tef_scale_level": safe_float(hc.get("tef_scale_level"), locale=doc_lang, allow_zero=True),
                }

    # Decoupled CSV risk matrix path resolved via vocabulary config or canonical English filename
    configured_csv_name = str(vocab.get("fair_risk_matrix_csv_filename") or "").strip()
    csv_candidates = [modules_dir / "06_fair_risk_matrix.csv"]
    if configured_csv_name:
        csv_candidates.insert(0, modules_dir / configured_csv_name)
    csv_risks_path = next((p for p in csv_candidates if p.exists()), csv_candidates[0])

    risks_data_list: list[dict[str, Any]] = []
    risks_by_pillar: dict[str, list[dict[str, Any]]] = {}

    if csv_risks_path.exists():
        localized_lef_tokens = [
            str(tok).strip().lower()
            for tok in (get_localized_list("lef_header_tokens", locale=doc_lang) or [])
            if str(tok).strip()
        ]
        valid_lef_tokens = set(CANONICAL_LEF_HEADER_TOKENS) | set(localized_lef_tokens)
        with open(csv_risks_path, "r", encoding="utf-8-sig") as cf:
            reader = csv.reader(cf, delimiter=";")
            header = next(reader, None)
            if header is not None:
                tef_header_norm = header[3].strip().lower() if len(header) > 3 else ""
                is_lef_column = any(tok in tef_header_norm for tok in valid_lef_tokens)
                for r_idx, row_data in enumerate(reader):
                    if len(row_data) < 6:
                        continue
                    parts_col0 = row_data[0].split(" - ", 1)
                    pillar_full_name = parts_col0[0].strip()
                    cap_raw = parts_col0[1].strip() if len(parts_col0) > 1 else pillar_full_name
                    raw_tef_cell = row_data[3]
                    raw_lm_cell = row_data[4]
                    parsed_tef_col = safe_float(raw_tef_cell, locale=doc_lang, allow_zero=True)
                    parsed_lm_col = safe_float(raw_lm_cell, locale=doc_lang, allow_zero=True)
                    raw_ale_col = safe_float(row_data[5], locale=doc_lang, allow_zero=True) or 0.0

                    bp_metrics = fair_lookup.get(cap_raw, {})
                    bp_lef = bp_metrics.get("lef")
                    bp_tef_scale = bp_metrics.get("tef_scale_level")
                    bp_sle = safe_float(bp_metrics.get("p90"), locale=doc_lang)

                    # Determine whether column 3 represents continuous LEF or discrete 1..5 TEF
                    if bp_lef is not None:
                        lef_val: float | None = bp_lef
                        tef_scale = float(resolve_dynamic_tef_scale_level(bp_lef, locale=doc_lang))
                    elif is_lef_column or (parsed_tef_col is not None and parsed_tef_col not in (1.0, 2.0, 3.0, 4.0, 5.0)):
                        lef_val = parsed_tef_col
                        tef_scale = float(resolve_dynamic_tef_scale_level(raw_tef_cell, locale=doc_lang))
                    elif parsed_tef_col is not None:
                        lef_val = None
                        tef_scale = float(clamp_scale_level(parsed_tef_col, default=1, locale=doc_lang))
                    elif bp_tef_scale is not None:
                        lef_val = None
                        tef_scale = float(clamp_scale_level(bp_tef_scale, default=1, locale=doc_lang))
                    else:
                        lef_val = None
                        tef_scale = float(clamp_scale_level(raw_tef_cell, default=1, locale=doc_lang))

                    monetary_cutoff = max(
                        MIN_MONETARY_LM_CUTOFF,
                        min(dynamic_lm_bounds[0] * MONETARY_CUTOFF_SCALE_RATIO, MAX_MONETARY_LM_CUTOFF),
                    )
                    sle_val = (
                        parsed_lm_col
                        if (parsed_lm_col is not None and parsed_lm_col >= monetary_cutoff)
                        else bp_sle
                    )
                    lm_scale = (
                        float(resolve_dynamic_lm_scale_level(sle_val, dynamic_lm_bounds, locale=doc_lang))
                        if sle_val is not None
                        else float(clamp_scale_level(raw_lm_cell, default=1, locale=doc_lang))
                    )
                    r_item = {
                        "id": f"RVS{r_idx + 1:02d}",
                        "pillar": pillar_full_name,
                        "capability": cap_raw,
                        "finding": row_data[1],
                        "business_risk": row_data[2],
                        "tef": tef_scale,
                        "lef": lef_val,
                        "lm": lm_scale,
                        "sle": sle_val,
                        "ale": raw_ale_col,
                        "prioritization_rationale": row_data[6]
                        if len(row_data) > 6
                        else None,
                    }
                    risks_data_list.append(r_item)

                    if pillar_full_name not in risks_by_pillar:
                        risks_by_pillar[pillar_full_name] = []
                    risks_by_pillar[pillar_full_name].append(r_item)
    elif b_data and b_data.get("pillars_analysis"):
        from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
            derive_in_memory_fair_risks,
        )
        rate_mult = safe_float(ctx.get("rate_mult"), locale=doc_lang) or 1.0
        risks_data_list, risks_by_pillar = derive_in_memory_fair_risks(
            b_data, doc_lang=doc_lang, currency=currency, rate_mult=rate_mult
        )
        for r_item in risks_data_list:
            sle_val = safe_float(r_item.get("sle"), locale=doc_lang)
            if sle_val is not None:
                r_item["lm"] = float(resolve_dynamic_lm_scale_level(sle_val, dynamic_lm_bounds, locale=doc_lang))
            lef_val = safe_float(r_item.get("lef"), locale=doc_lang)
            if lef_val is not None:
                r_item["tef"] = float(resolve_dynamic_tef_scale_level(lef_val, locale=doc_lang))

    # Section 4.2: Prioritized Risk Catalog
    add_heading(
        doc, t("detailed_risks_title", locale=doc_lang), level=2, primary_color_rgb=p_color_rgb
    )
    add_body_paragraph(
        doc,
        t("fair_catalog_intro", locale=doc_lang),
        text_color_rgb=text_color_rgb,
    )
    add_spacer(doc, SPACER_MEDIUM_PT)

    # Mutate deep/shallow copy to prevent global AST state pollution (Split-Brain)
    safe_risks_data_list = [dict(r) for r in risks_data_list]
    safe_risks_data_list.sort(
        key=lambda r: safe_float(r.get("ale"), locale=doc_lang, allow_zero=True) or 0.0,
        reverse=True,
    )
    for idx, r in enumerate(safe_risks_data_list):
        r["id"] = f"{tower_id}-RSK-{idx + 1:02d}"
        r["rank"] = idx + 1

    total_risks_count = len(safe_risks_data_list)
    local_mean_ale = (
        (sum(safe_float(r.get("ale"), locale=doc_lang, allow_zero=True) or 0.0 for r in safe_risks_data_list) / total_risks_count)
        if total_risks_count > 0
        else 0.0
    )
    tier1_threshold = local_mean_ale * TIER1_THRESHOLD_MULTIPLIER
    tier2_threshold = local_mean_ale * TIER2_THRESHOLD_MULTIPLIER

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
    sum_col_widths = [Cm(w) for w in RISK_SUMMARY_COL_WIDTHS_CM]
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

    def _set_cell_width_twips(cell_node: Any, width_twips: int) -> None:
        tcPr = cell_node._tc.get_or_add_tcPr()
        tcW = tcPr.find(qn('w:tcW'))
        if tcW is not None:
            tcPr.remove(tcW)
        new_tcW = OxmlElement('w:tcW')
        new_tcW.set(qn('w:type'), 'dxa')
        new_tcW.set(qn('w:w'), str(width_twips))
        tcPr.append(new_tcW)

    summary_headers = (
        get_localized_list("risk_summary_headers", locale=doc_lang)
        or get_localized_list("risk_summary_headers", locale="en")
        or list(DEFAULT_RISK_SUMMARY_HEADERS)
    )
    if not isinstance(summary_headers, list) or len(summary_headers) < len(sum_col_widths):
        summary_headers = list(DEFAULT_RISK_SUMMARY_HEADERS)
    else:
        summary_headers = summary_headers[: len(sum_col_widths)]

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
        _set_cell_width_twips(cell, int(sum_col_widths[i].twips))
        shade_cell(cell, p_color_hex)

    taxonomy_resolver = get_taxonomy_resolver()
    style_resolver = resolver

    for r_idx, r in enumerate(safe_risks_data_list):
        row = table_risks.add_row()
        raw_cap = r["capability"]
        cap_name = taxonomy_resolver.resolve_capability_name(raw_cap, default=raw_cap, locale=doc_lang)
        raw_pillar = r.get("pillar") or t("default_pillar_label", locale=doc_lang)
        pillar_name = taxonomy_resolver.resolve_pillar_by_any_reference(raw_pillar, default=raw_pillar, locale=doc_lang)

        fair_metrics = fair_lookup.get(raw_cap, fair_lookup.get(cap_name, {}))
        raw_p90_candidate = r.get("p90") if r.get("p90") is not None else fair_metrics.get("p90")
        clean_p90_candidate = safe_float(raw_p90_candidate, locale=doc_lang, allow_zero=True)
        clean_ale_val = safe_float(r.get("ale"), locale=doc_lang, allow_zero=True) or 0.0
        p90_val = clean_p90_candidate if clean_p90_candidate is not None else 0.0
        formatted_ale_r = _format_integer_currency_safe(clean_ale_val, t_sep, d_sep, locale=doc_lang) if clean_ale_val > 0 else "UNQUANTIFIED"
        formatted_p90_r = _format_integer_currency_safe(p90_val, t_sep, d_sep, locale=doc_lang) if p90_val > 0 else "UNQUANTIFIED"
        if r_idx == 0:
            formatted_ale_item = formatted_ale_r

        set_cell_text_custom(row.cells[0], r["id"], bold=True, font_size=SUMMARY_TABLE_FONT_SIZE_PT, align=WD_ALIGN_PARAGRAPH.CENTER, no_bullets=True)
        set_cell_text_custom(row.cells[1], cap_name, bold=True, font_size=SUMMARY_TABLE_FONT_SIZE_PT, no_bullets=True)
        set_cell_text_custom(row.cells[2], pillar_name, font_size=SUMMARY_TABLE_FONT_SIZE_PT, no_bullets=True)
        set_cell_text_custom(row.cells[3], f"{r['tef']:.1f} / 5.0", font_size=SUMMARY_TABLE_FONT_SIZE_PT, align=WD_ALIGN_PARAGRAPH.CENTER, no_bullets=True)
        set_cell_text_custom(row.cells[4], f"{formatted_p90_r} {currency}", font_size=SUMMARY_TABLE_FONT_SIZE_PT, align=WD_ALIGN_PARAGRAPH.RIGHT, no_bullets=True)
        set_cell_text_custom(row.cells[5], f"{formatted_ale_r} {currency}", bold=True, font_size=SUMMARY_TABLE_FONT_SIZE_PT, align=WD_ALIGN_PARAGRAPH.RIGHT, no_bullets=True)

        for i, w in enumerate(sum_col_widths):
            cell = row.cells[i]
            _set_cell_width_twips(cell, int(w.twips))
            if r_idx % 2 == 1:
                shade_cell(cell, alt_row_hex)

    add_spacer(doc, SPACER_STANDARD_PT)

    # Part B: Executive 2-Line Risk Cards
    lbl_diag = t("label_operational_diagnostic", locale=doc_lang)
    lbl_econ = t("label_economic_impact", locale=doc_lang)
    raw_client_name = ctx.get("raw_client_name", client_name)

    for r in safe_risks_data_list:
        raw_cap = r["capability"]
        cap_name = taxonomy_resolver.resolve_capability_name(raw_cap, default=raw_cap, locale=doc_lang)
        fair_metrics = fair_lookup.get(raw_cap, fair_lookup.get(cap_name, {}))
        raw_p90_candidate = r.get("p90") if r.get("p90") is not None else fair_metrics.get("p90")
        clean_p90_candidate = safe_float(raw_p90_candidate, locale=doc_lang, allow_zero=True)
        clean_ale_val = safe_float(r.get("ale"), locale=doc_lang, allow_zero=True) or 0.0
        p90_val = clean_p90_candidate if clean_p90_candidate is not None else 0.0
        formatted_ale_r = _format_integer_currency_safe(clean_ale_val, t_sep, d_sep, locale=doc_lang) if clean_ale_val > 0 else "UNQUANTIFIED"
        formatted_p90_r = _format_integer_currency_safe(p90_val, t_sep, d_sep, locale=doc_lang) if p90_val > 0 else "UNQUANTIFIED"

        if clean_ale_val > 0.0 and clean_ale_val >= tier1_threshold:
            tier_badge = t("tier_label_critical", locale=doc_lang)
        elif clean_ale_val > 0.0 and clean_ale_val >= tier2_threshold:
            tier_badge = t("tier_label_medium", locale=doc_lang)
        else:
            tier_badge = t("tier_label_moderate", locale=doc_lang)

        # Risk Card Heading
        card_title = f"[{r['id']}] {cap_name} ({tier_badge})"
        add_heading(doc, card_title, level=3, primary_color_rgb=p_color_rgb)

        finding_split_regex = vocab.get("finding_split_regex", r"\n\n(?:Evidence|Audit)")
        raw_f = re.split(finding_split_regex, r["finding"])[0].strip()
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
        if tef_val >= TEF_RESILIENCE_HIGH_THRESHOLD:
            freq_str = t("resilience_freq_high", locale=doc_lang)
        elif tef_val >= TEF_RESILIENCE_MED_THRESHOLD:
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
        p_diag.paragraph_format.left_indent = Inches(RISK_CARD_HANGING_INDENT_IN)
        p_diag.paragraph_format.first_line_indent = Inches(-RISK_CARD_HANGING_INDENT_IN)
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
        p_econ.paragraph_format.left_indent = Inches(RISK_CARD_HANGING_INDENT_IN)
        p_econ.paragraph_format.first_line_indent = Inches(-RISK_CARD_HANGING_INDENT_IN)
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

    add_spacer(doc, SPACER_STANDARD_PT)

    # Render Section 4.3: 5x5 Heatmap as a visual synthesis of all evaluated risks
    _render_fair_heatmap(
        doc=doc,
        ctx=local_ctx,
        risks_data_list=safe_risks_data_list,
        doc_lang=doc_lang,
        client_name=client_name,
        currency=str(currency),
        is_critical=is_critical,
        p_color_rgb=p_color_rgb,
        text_color_rgb=text_color_rgb,
        vocab=vocab,
        precomputed_lm_bounds=dynamic_lm_bounds,
    )

    # Section 4.4: Mitigation Levers and Resilience Return (Hexagon of Value)
    add_heading(
        doc, t("value_hexagon_heading", locale=doc_lang), level=2, primary_color_rgb=p_color_rgb
    )
    lever_intro = t("value_hexagon_intro", locale=doc_lang)
    add_body_paragraph(doc, lever_intro, text_color_rgb=text_color_rgb)
    hexagon_bullets = get_localized_list("value_hexagon_bullets", locale=doc_lang) or []
    for l_idx, lever_text in enumerate(hexagon_bullets):
        add_markdown_bullet_local(
            lever_text,
            space_after=HEXAGON_LAST_BULLET_SPACE_PT if l_idx == len(hexagon_bullets) - 1 else HEXAGON_BULLET_SPACE_PT,
        )

    return {
        "total_p90": total_p90,
        "formatted_ale_item": formatted_ale_item,
        "formatted_p90": formatted_p90,
        "t_sep": t_sep,
        "d_sep": d_sep,
    }


