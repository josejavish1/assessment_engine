from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping, Tuple

from assessment_engine.domain.actuarial_scale_calibrator import (
    CANONICAL_LM_CRITICAL_THRESHOLDS,
    CANONICAL_LM_STANDARD_THRESHOLDS,
    CANONICAL_TEF_THRESHOLDS,
    DII_HIGH_STABILITY_THRESHOLD,
    DII_MODERATE_STABILITY_THRESHOLD,
    ERC_HIGH_THRESHOLD,
    ERC_MEDIUM_THRESHOLD,
    HEATMAP_SEVERITY_HIGH_THRESHOLD,
    HEATMAP_SEVERITY_MED_THRESHOLD,
    MCDA_EXTREME_THRESHOLD,
    MCDA_FEASIBILITY_FAVORABLE_THRESHOLD,
    MCDA_HIGH_THRESHOLD,
    compute_dynamic_lm_brackets,
    compute_dynamic_lm_thresholds,
    resolve_dynamic_lm_scale_level,
    resolve_dynamic_tef_scale_level,
    resolve_risk_matrix_coordinates,
    safe_float,
)
from assessment_engine.domain.schemas.ast import (
    CellNode,
    ParagraphNode,
    TableNode,
    TableRowNode,
)
from assessment_engine.infrastructure.localization import get_localized_list, t

DEFAULT_HEATMAP_HEADER_HEX: Final[str] = "0072BC"
DEFAULT_TABLE_BG_WHITE_HEX: Final[str] = "FFFFFF"
DEFAULT_ALT_ROW_HEX: Final[str] = "F8FAFC"
HEATMAP_SEVERITY_HIGH_HEX: Final[str] = "FADBD8"
HEATMAP_SEVERITY_MED_HEX: Final[str] = "FCF3CD"
HEATMAP_SEVERITY_LOW_HEX: Final[str] = "D5F5E3"

HEADER_TEXT_WHITE_RGB: Final[Tuple[int, int, int]] = (255, 255, 255)
SCALE_TABLE_HEADER_FONT_PT: Final[float] = 8.0
SCALE_TABLE_BODY_FONT_PT: Final[float] = 7.5


def build_criticality_bullet(
    business_criticality: float, locale: str
) -> ParagraphNode:
    """Builds the MCDA business criticality bullet node."""
    clean_val = safe_float(business_criticality, locale=locale) or 0.0
    val_str = f"{clean_val:.1f}"
    if clean_val >= MCDA_EXTREME_THRESHOLD:
        return ParagraphNode(
            text=f"* {t('gloss_mcda_crit_extreme', locale=locale, val=val_str)}"
        )
    elif clean_val >= MCDA_HIGH_THRESHOLD:
        return ParagraphNode(
            text=f"* {t('gloss_mcda_crit_high', locale=locale, val=val_str)}"
        )
    return ParagraphNode(
        text=f"* {t('gloss_mcda_crit_medium', locale=locale, val=val_str)}"
    )


def build_regulatory_bullet(
    regulatory_compliance: float, locale: str
) -> ParagraphNode:
    """Builds the MCDA regulatory pressure bullet node."""
    clean_val = safe_float(regulatory_compliance, locale=locale) or 0.0
    val_str = f"{clean_val:.1f}"
    if clean_val >= MCDA_EXTREME_THRESHOLD:
        return ParagraphNode(
            text=f"* {t('gloss_mcda_reg_critical', locale=locale, val=val_str)}"
        )
    elif clean_val >= MCDA_HIGH_THRESHOLD:
        return ParagraphNode(
            text=f"* {t('gloss_mcda_reg_moderate', locale=locale, val=val_str)}"
        )
    return ParagraphNode(
        text=f"* {t('gloss_mcda_reg_standard', locale=locale, val=val_str)}"
    )


def build_feasibility_bullet(
    implementation_feasibility: float, locale: str
) -> ParagraphNode:
    """Builds the MCDA operational feasibility bullet node."""
    clean_val = safe_float(implementation_feasibility, locale=locale) or 0.0
    val_str = f"{clean_val:.1f}"
    if clean_val >= MCDA_FEASIBILITY_FAVORABLE_THRESHOLD:
        return ParagraphNode(
            text=f"* {t('gloss_mcda_viab_favorable', locale=locale, val=val_str)}"
        )
    return ParagraphNode(
        text=f"* {t('gloss_mcda_viab_complex', locale=locale, val=val_str)}"
    )


def build_dii_bullet(
    dii_pct: float, locale: str
) -> ParagraphNode:
    """Builds the Decision Instability Index (DII) bullet node."""
    clean_val = safe_float(dii_pct, locale=locale) or 0.0
    val_str = f"{clean_val:.1f}"
    if clean_val < DII_HIGH_STABILITY_THRESHOLD:
        return ParagraphNode(
            text=f"* {t('gloss_dii_high', locale=locale, val=val_str)}"
        )
    elif clean_val < DII_MODERATE_STABILITY_THRESHOLD:
        return ParagraphNode(
            text=f"* {t('gloss_dii_moderate', locale=locale, val=val_str)}"
        )
    return ParagraphNode(
        text=f"* {t('gloss_dii_volatile', locale=locale, val=val_str)}"
    )


def build_erc_bullet(
    erc_val_num: float, locale: str
) -> ParagraphNode:
    """Builds the Error Propagation Index (ERC) bullet node."""
    clean_val = safe_float(erc_val_num, locale=locale) or 0.0
    val_str = f"{clean_val:.3f}"
    if clean_val >= ERC_HIGH_THRESHOLD:
        return ParagraphNode(text=f"* {t('gloss_erc_high', locale=locale, val=val_str)}")
    elif clean_val >= ERC_MEDIUM_THRESHOLD:
        return ParagraphNode(text=f"* {t('gloss_erc_medium', locale=locale, val=val_str)}")
    return ParagraphNode(text=f"* {t('gloss_erc_low', locale=locale, val=val_str)}")


def build_spof_bullet(
    spof_status: str, locale: str
) -> ParagraphNode:
    """Builds the Single Point of Failure (SPOF) bullet node."""
    is_spof = str(spof_status).strip().upper() in ("YES", "TRUE", "1")
    if is_spof:
        return ParagraphNode(
            text=f"* {t('gloss_spof_crit', locale=locale)}"
        )
    return ParagraphNode(
        text=f"* {t('gloss_spof_stable', locale=locale)}"
    )


DEFAULT_TEF_THRESHOLDS: Final[Tuple[float, float, float, float]] = CANONICAL_TEF_THRESHOLDS
DEFAULT_LM_STANDARD_THRESHOLDS: Final[Tuple[float, float, float, float]] = CANONICAL_LM_STANDARD_THRESHOLDS
DEFAULT_LM_CRITICAL_THRESHOLDS: Final[Tuple[float, float, float, float]] = CANONICAL_LM_CRITICAL_THRESHOLDS


def resolve_tef_scale_level(
    lef_annual: float | Any,
    thresholds: Tuple[float, float, float, float] = DEFAULT_TEF_THRESHOLDS,
    locale: str | None = None,
) -> int:
    """Map continuous Loss Event Frequency (events/year) to discrete 1..5 TEF scale level.
    Delegates strictly to domain actuarial scale calibrator.
    """
    return resolve_dynamic_tef_scale_level(lef_annual, thresholds, locale=locale)


def resolve_lm_scale_level(
    sle_amount: float | Any,
    is_critical_tier: bool = False,
    standard_thresholds: Tuple[float, float, float, float] = DEFAULT_LM_STANDARD_THRESHOLDS,
    critical_thresholds: Tuple[float, float, float, float] = DEFAULT_LM_CRITICAL_THRESHOLDS,
    dynamic_thresholds: Tuple[float, float, float, float] | None = None,
    locale: str | None = None,
) -> int:
    """Map continuous Single Loss Expectancy (currency units) to discrete 1..5 LM scale level.
    Reconciles 100% with Table 4.2.2 and dynamic actuarial scale calibrator.
    """
    bounds = dynamic_thresholds or (critical_thresholds if is_critical_tier else standard_thresholds)
    return resolve_dynamic_lm_scale_level(sle_amount, bounds, locale=locale)


def build_heatmap_mosaic(
    risks_data_list: list[dict[str, Any]],
    is_critical: bool = False,
    dynamic_lm_thresholds: tuple[float, float, float, float] | None = None,
    header_bg_color: str = DEFAULT_HEATMAP_HEADER_HEX,
    locale: str | None = None,
    currency: str | None = None,
    annual_revenue: float | None = None,
    hourly_downtime_cost: float | None = None,
) -> TableNode:
    """Builds the 5x5 FAIR Risk Heatmap mosaic TableNode reconciling coordinates with TEF/LM scale criteria."""
    matrix_cells = {r: {c: [] for c in range(1, 6)} for r in range(5, 0, -1)}
    if dynamic_lm_thresholds is not None:
        effective_bounds = dynamic_lm_thresholds
    elif currency:
        effective_bounds = compute_dynamic_lm_thresholds(
            currency=currency,
            annual_revenue=annual_revenue,
            hourly_downtime_cost=hourly_downtime_cost,
            is_critical_tier=is_critical,
            locale=locale or "en",
        )
    else:
        effective_bounds = (
            DEFAULT_LM_CRITICAL_THRESHOLDS if is_critical else DEFAULT_LM_STANDARD_THRESHOLDS
        )
    for r in risks_data_list:
        r_tef, r_lm = resolve_risk_matrix_coordinates(
            r, effective_bounds, locale=locale
        )
        r["tef_scale_level"] = r_tef
        r["lm_scale_level"] = r_lm
        risk_id = str(r.get("id") or r.get("risk_id") or "").strip()
        if risk_id and risk_id not in matrix_cells[r_tef][r_lm]:
            matrix_cells[r_tef][r_lm].append(risk_id)

    heatmap_rows = []
    if currency:
        lm_brackets = compute_dynamic_lm_brackets(
            currency=currency,
            locale=locale or "en",
            annual_revenue=annual_revenue,
            hourly_downtime_cost=hourly_downtime_cost,
            is_critical_tier=is_critical,
            precomputed_thresholds=effective_bounds,
        )
        heatmap_headers = [r"TEF \ LM"] + [
            f"LM {col_idx}\n({lm_brackets[col_idx]})" for col_idx in range(1, 6)
        ]
    else:
        heatmap_headers = [r"TEF \ LM", "LM 1", "LM 2", "LM 3", "LM 4", "LM 5"]

    heatmap_rows.append(
        TableRowNode(
            cells=[
                CellNode(
                    text=h,
                    bold=True,
                    bg_color=header_bg_color,
                    text_color_rgb=list(HEADER_TEXT_WHITE_RGB),
                    font_size=SCALE_TABLE_HEADER_FONT_PT,
                    align="CENTER",
                )
                for h in heatmap_headers
            ],
            is_header=True,
        )
    )

    for tef_val in range(5, 0, -1):
        freq_locale = locale or "en"
        tef_freq_label = t(f"tef_annual_freq_{tef_val}", locale=freq_locale)
        row_header_text = (
            f"TEF {tef_val}\n({tef_freq_label})"
            if tef_freq_label and not tef_freq_label.startswith("tef_annual_freq_")
            else f"TEF {tef_val}"
        )
        row_cells = [
            CellNode(
                text=row_header_text,
                bold=True,
                bg_color=header_bg_color,
                text_color_rgb=list(HEADER_TEXT_WHITE_RGB),
                font_size=SCALE_TABLE_HEADER_FONT_PT,
                align="CENTER",
            )
        ]
        for lm_val in range(1, 6):
            cell_risks = matrix_cells[tef_val][lm_val]
            cell_text = ", ".join(cell_risks) if cell_risks else "-"
            severity = tef_val * lm_val
            if severity >= HEATMAP_SEVERITY_HIGH_THRESHOLD:
                bg_color = HEATMAP_SEVERITY_HIGH_HEX
            elif severity >= HEATMAP_SEVERITY_MED_THRESHOLD:
                bg_color = HEATMAP_SEVERITY_MED_HEX
            else:
                bg_color = HEATMAP_SEVERITY_LOW_HEX
            row_cells.append(
                CellNode(text=cell_text, bold=True, bg_color=bg_color, align="CENTER")
            )
        heatmap_rows.append(TableRowNode(cells=row_cells))

    return TableNode(rows=heatmap_rows)


TEF_SCALE_DEFINITIONS: Final[Mapping[str, Tuple[Tuple[str, str], ...]]] = MappingProxyType({
    "en": (
        ("Very Low", "< 0.1 events/year (less than once every 10 years)"),
        ("Low", "0.1 - 0.5 events/year (once every 4 years)"),
        ("Medium", "0.5 - 2.0 events/year (once a year)"),
        ("High", "2.0 - 10 events/year (once a quarter)"),
        ("Very High", "> 10 events/year (once a month)"),
    ),
})


DEFAULT_LM_LABELS_EN: Final[Tuple[str, str, str, str, str]] = (
    "Low",
    "Moderate",
    "Significant",
    "High",
    "Catastrophic",
)


def build_tef_scale_table(
    vocab: dict[str, Any],
    meta_lang: str,
    alt_row_hex: str = DEFAULT_ALT_ROW_HEX,
    header_bg_color: str = DEFAULT_HEATMAP_HEADER_HEX,
) -> TableNode:
    """Builds the Threat Event Frequency (TEF) criteria scale TableNode."""
    tef_headers = vocab.get("tef_headers") or get_localized_list(
        "tef_headers", locale=meta_lang
    )
    if not tef_headers or len(tef_headers) < 3:
        tef_headers = ["Scale", "Frequency Tier", "Operational Criteria"]

    tef_levels = get_localized_list("tef_levels", locale=meta_lang)
    if not tef_levels or len(tef_levels) < 5:
        tef_levels = [item[0] for item in TEF_SCALE_DEFINITIONS["en"]]

    tef_descs = get_localized_list("tef_descriptions", locale=meta_lang)
    if not tef_descs or len(tef_descs) < 5:
        tef_descs = [item[1] for item in TEF_SCALE_DEFINITIONS["en"]]

    tef_data = [(f"TEF {i+1}", tef_levels[i], tef_descs[i]) for i in range(5)]
    tef_rows = [
        TableRowNode(
            cells=[
                CellNode(
                    text=h,
                    bold=True,
                    bg_color=header_bg_color,
                    text_color_rgb=list(HEADER_TEXT_WHITE_RGB),
                    font_size=SCALE_TABLE_HEADER_FONT_PT,
                    align="CENTER",
                )
                for h in tef_headers
            ],
            is_header=True,
        )
    ]
    for t_idx, r_vals in enumerate(tef_data):
        bg = alt_row_hex if t_idx % 2 == 1 else DEFAULT_TABLE_BG_WHITE_HEX
        tef_rows.append(
            TableRowNode(
                cells=[
                    CellNode(text=r_vals[0], bold=True, bg_color=alt_row_hex, font_size=SCALE_TABLE_BODY_FONT_PT, align="CENTER"),
                    CellNode(text=r_vals[1], bg_color=bg, font_size=SCALE_TABLE_BODY_FONT_PT, align="CENTER"),
                    CellNode(text=r_vals[2], bg_color=bg, font_size=SCALE_TABLE_BODY_FONT_PT),
                ]
            )
        )
    return TableNode(rows=tef_rows, autofit=True)


def build_lm_scale_table(
    vocab: dict[str, Any],
    meta_lang: str,
    currency: str,
    is_critical: bool = False,
    alt_row_hex: str = DEFAULT_ALT_ROW_HEX,
    lm_brackets: dict[int, str] | None = None,
    annual_revenue: float | None = None,
    hourly_downtime_cost: float | None = None,
    dynamic_lm_thresholds: Tuple[float, float, float, float] | None = None,
    header_bg_color: str = DEFAULT_HEATMAP_HEADER_HEX,
) -> TableNode:
    """Builds the Loss Magnitude (LM) criteria scale TableNode using dynamic actuarial brackets."""
    lm_headers = vocab.get("lm_headers") or get_localized_list(
        "lm_headers", locale=meta_lang
    )
    if not lm_headers or len(lm_headers) < 3:
        lm_headers = ["Scale", "Impact Severity", f"Financial Loss Range ({currency})"]

    labels = get_localized_list("lm_labels", locale=meta_lang)
    if not labels or len(labels) < 5:
        labels = get_localized_list("lm_labels", locale="en")
    if not labels or len(labels) < 5:
        labels = list(DEFAULT_LM_LABELS_EN)

    if lm_brackets and all(k in lm_brackets for k in range(1, 6)):
        limits = [lm_brackets[i] for i in range(1, 6)]
    else:
        resolved_brackets = compute_dynamic_lm_brackets(
            currency=currency,
            locale=meta_lang,
            annual_revenue=annual_revenue,
            hourly_downtime_cost=hourly_downtime_cost,
            is_critical_tier=is_critical,
            precomputed_thresholds=dynamic_lm_thresholds,
        )
        limits = [resolved_brackets[i] for i in range(1, 6)]

    lm_data = [(f"LM {i+1}", labels[i], limits[i]) for i in range(5)]
    lm_rows = [
        TableRowNode(
            cells=[
                CellNode(
                    text=(
                        f"{h} ({currency})"
                        if h_idx == len(lm_headers) - 1 and f"({currency})" not in h
                        else h
                    ),
                    bold=True,
                    bg_color=header_bg_color,
                    text_color_rgb=list(HEADER_TEXT_WHITE_RGB),
                    font_size=SCALE_TABLE_HEADER_FONT_PT,
                    align="CENTER",
                )
                for h_idx, h in enumerate(lm_headers)
            ],
            is_header=True,
        )
    ]
    for l_idx, r_vals in enumerate(lm_data):
        bg = alt_row_hex if l_idx % 2 == 1 else DEFAULT_TABLE_BG_WHITE_HEX
        lm_rows.append(
            TableRowNode(
                cells=[
                    CellNode(text=r_vals[0], bold=True, bg_color=alt_row_hex, font_size=SCALE_TABLE_BODY_FONT_PT, align="CENTER"),
                    CellNode(text=r_vals[1], bg_color=bg, font_size=SCALE_TABLE_BODY_FONT_PT, align="CENTER"),
                    CellNode(text=r_vals[2], bg_color=bg, font_size=SCALE_TABLE_BODY_FONT_PT, align="CENTER"),
                ]
            )
        )
    return TableNode(rows=lm_rows, autofit=True)
