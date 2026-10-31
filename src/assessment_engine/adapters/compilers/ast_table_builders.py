from __future__ import annotations

from typing import Any

from assessment_engine.domain.schemas.ast import (
    CellNode,
    ParagraphNode,
    TableNode,
    TableRowNode,
)
from assessment_engine.infrastructure.localization import get_localized_list, t


def build_criticality_bullet(
    business_criticality: float, locale: str
) -> ParagraphNode:
    """Builds the MCDA business criticality bullet node."""
    val_str = f"{business_criticality:.1f}"
    if business_criticality >= 80.0:
        return ParagraphNode(
            text=f"* {t('gloss_mcda_crit_extrema', locale=locale, val=val_str)}"
        )
    elif business_criticality >= 50.0:
        return ParagraphNode(
            text=f"* {t('gloss_mcda_crit_alta', locale=locale, val=val_str)}"
        )
    return ParagraphNode(
        text=f"* {t('gloss_mcda_crit_media', locale=locale, val=val_str)}"
    )


def build_regulatory_bullet(
    regulatory_compliance: float, locale: str
) -> ParagraphNode:
    """Builds the MCDA regulatory pressure bullet node."""
    val_str = f"{regulatory_compliance:.1f}"
    if regulatory_compliance >= 80.0:
        return ParagraphNode(
            text=f"* {t('gloss_mcda_reg_critica', locale=locale, val=val_str)}"
        )
    elif regulatory_compliance >= 50.0:
        return ParagraphNode(
            text=f"* {t('gloss_mcda_reg_moderada', locale=locale, val=val_str)}"
        )
    return ParagraphNode(
        text=f"* {t('gloss_mcda_reg_estandar', locale=locale, val=val_str)}"
    )


def build_feasibility_bullet(
    implementation_feasibility: float, locale: str
) -> ParagraphNode:
    """Builds the MCDA operational feasibility bullet node."""
    val_str = f"{implementation_feasibility:.1f}"
    if implementation_feasibility >= 60.0:
        return ParagraphNode(
            text=f"* {t('gloss_mcda_viab_fav', locale=locale, val=val_str)}"
        )
    return ParagraphNode(
        text=f"* {t('gloss_mcda_viab_comp', locale=locale, val=val_str)}"
    )


def build_dii_bullet(
    dii_pct: float, locale: str
) -> ParagraphNode:
    """Builds the Decision Instability Index (DII) bullet node."""
    val_str = f"{dii_pct:.1f}"
    if dii_pct < 15.0:
        return ParagraphNode(
            text=f"* {t('gloss_dii_alta', locale=locale, val=val_str)}"
        )
    elif dii_pct < 30.0:
        return ParagraphNode(
            text=f"* {t('gloss_dii_mod', locale=locale, val=val_str)}"
        )
    return ParagraphNode(
        text=f"* {t('gloss_dii_vol', locale=locale, val=val_str)}"
    )


def build_erc_bullet(
    erc_val_num: float, locale: str
) -> ParagraphNode:
    """Builds the Error Propagation Index (ERC) bullet node."""
    val_str = f"{erc_val_num:.3f}"
    if erc_val_num >= 0.50:
        return ParagraphNode(
            text=f"* {t('gloss_erc_alta', locale=locale, val=val_str)}"
        )
    elif erc_val_num >= 0.20:
        return ParagraphNode(
            text=f"* {t('gloss_erc_media', locale=locale, val=val_str)}"
        )
    return ParagraphNode(
        text=f"* {t('gloss_erc_baja', locale=locale, val=val_str)}"
    )


def build_spof_bullet(
    spof_status: str, locale: str
) -> ParagraphNode:
    """Builds the Single Point of Failure (SPOF) bullet node."""
    is_spof = str(spof_status).strip().upper() in ("YES", "TRUE", "1", "SI")
    if is_spof:
        return ParagraphNode(
            text=f"* {t('gloss_spof_crit', locale=locale)}"
        )
    return ParagraphNode(
        text=f"* {t('gloss_spof_stable', locale=locale)}"
    )


def build_heatmap_mosaic(risks_data_list: list[dict[str, Any]]) -> TableNode:
    """Builds the 5x5 FAIR Risk Heatmap mosaic TableNode."""
    matrix_cells = {r: {c: [] for c in range(1, 6)} for r in range(5, 0, -1)}
    for r in risks_data_list:
        r_tef = min(5, max(1, int(round(r["tef"]))))
        r_lm = min(5, max(1, int(round(r["lm"]))))
        matrix_cells[r_tef][r_lm].append(r["id"])

    heatmap_rows = []
    heatmap_headers = [r"TEF \ LM", "LM 1", "LM 2", "LM 3", "LM 4", "LM 5"]
    heatmap_rows.append(
        TableRowNode(
            cells=[
                CellNode(
                    text=h,
                    bold=True,
                    bg_color="0072BC",
                    text_color_rgb=[255, 255, 255],
                    align="CENTER",
                )
                for h in heatmap_headers
            ],
            is_header=True,
        )
    )

    for tef_val in range(5, 0, -1):
        row_cells = [
            CellNode(
                text=f"TEF {tef_val}",
                bold=True,
                bg_color="0072BC",
                text_color_rgb=[255, 255, 255],
                align="CENTER",
            )
        ]
        for lm_val in range(1, 6):
            cell_risks = matrix_cells[tef_val][lm_val]
            cell_text = ", ".join(cell_risks) if cell_risks else "-"
            severity = tef_val * lm_val
            if severity >= 15:
                bg_color = "FADBD8"
            elif severity >= 8:
                bg_color = "FCF3CD"
            else:
                bg_color = "D5F5E3"
            row_cells.append(
                CellNode(text=cell_text, bold=True, bg_color=bg_color, align="CENTER")
            )
        heatmap_rows.append(TableRowNode(cells=row_cells))

    return TableNode(rows=heatmap_rows)


TEF_SCALE_DEFINITIONS: dict[str, list[tuple[str, str]]] = {
    "en": [
        ("Very Low", "< 0.1 events/year (less than once every 10 years)"),
        ("Low", "0.1 - 0.5 events/year (once every 4 years)"),
        ("Medium", "0.5 - 2.0 events/year (once a year)"),
        ("High", "2.0 - 10 events/year (once a quarter)"),
        ("Very High", "> 10 events/year (once a month)"),
    ],
}


def build_tef_scale_table(vocab: dict[str, Any], meta_lang: str, alt_row_hex: str) -> TableNode:
    """Builds the Threat Event Frequency (TEF) criteria scale TableNode."""
    tef_headers = vocab.get("tef_headers") or get_localized_list(
        "tef_headers", locale=meta_lang
    )
    tef_levels = get_localized_list("tef_levels", locale=meta_lang)
    if not tef_levels or len(tef_levels) < 5:
        tef_levels = ["Very Low", "Low", "Medium", "High", "Very High"]

    tef_descs = get_localized_list("tef_descriptions", locale=meta_lang)
    if not tef_descs or len(tef_descs) < 5:
        tef_descs = [
            "< 0.1 events/year (less than once every 10 years)",
            "0.1 - 0.5 events/year (once every 4 years)",
            "0.5 - 2.0 events/year (once a year)",
            "2.0 - 10 events/year (once a quarter)",
            "> 10 events/year (once a month)",
        ]

    tef_data = [(f"TEF {i+1}", tef_levels[i], tef_descs[i]) for i in range(5)]
    tef_rows = [
        TableRowNode(
            cells=[
                CellNode(text=h, bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER")
                for h in tef_headers
            ],
            is_header=True,
        )
    ]
    for t_idx, r_vals in enumerate(tef_data):
        bg = alt_row_hex if t_idx % 2 == 1 else "FFFFFF"
        tef_rows.append(
            TableRowNode(
                cells=[
                    CellNode(text=r_vals[0], bold=True, bg_color=alt_row_hex, align="CENTER"),
                    CellNode(text=r_vals[1], bg_color=bg, align="CENTER"),
                    CellNode(text=r_vals[2], bg_color=bg),
                ]
            )
        )
    return TableNode(rows=tef_rows)


def build_lm_scale_table(
    vocab: dict[str, Any], meta_lang: str, currency: str, is_critical: bool, alt_row_hex: str
) -> TableNode:
    """Builds the Loss Magnitude (LM) criteria scale TableNode."""
    lm_headers = vocab.get("lm_headers") or get_localized_list(
        "lm_headers", locale=meta_lang
    )
    labels = get_localized_list("lm_labels", locale=meta_lang)
    if not labels or len(labels) < 5:
        labels = get_localized_list("lm_labels", locale="en")

    from assessment_engine.infrastructure.localization import format_number

    if is_critical:
        stress_label = t("p90_stress_scenario_label", locale=meta_lang)
        limits = [
            f"< {format_number(25000, locale=meta_lang, decimals=0)} {currency}",
            f"{format_number(25000, locale=meta_lang, decimals=0)} {currency} - {format_number(100000, locale=meta_lang, decimals=0)} {currency}",
            f"{format_number(100000, locale=meta_lang, decimals=0)} {currency} - {format_number(500000, locale=meta_lang, decimals=0)} {currency}",
            f"{format_number(500000, locale=meta_lang, decimals=0)} {currency} - {format_number(2000000, locale=meta_lang, decimals=0)} {currency}",
            f"> {format_number(2000000, locale=meta_lang, decimals=0)} {currency} ({stress_label})",
        ]
    else:
        limits = [
            f"< {format_number(1000, locale=meta_lang, decimals=0)} {currency}",
            f"{format_number(1000, locale=meta_lang, decimals=0)} {currency} - {format_number(5000, locale=meta_lang, decimals=0)} {currency}",
            f"{format_number(5000, locale=meta_lang, decimals=0)} {currency} - {format_number(25000, locale=meta_lang, decimals=0)} {currency}",
            f"{format_number(25000, locale=meta_lang, decimals=0)} {currency} - {format_number(100000, locale=meta_lang, decimals=0)} {currency}",
            f"{format_number(100000, locale=meta_lang, decimals=0)} {currency} - {format_number(500000, locale=meta_lang, decimals=0)} {currency}",
        ]

    lm_data = [(f"LM {i+1}", labels[i], limits[i]) for i in range(5)]
    lm_rows = [
        TableRowNode(
            cells=[
                CellNode(
                    text=f"{h} ({currency})" if h_idx > 0 else h,
                    bold=True,
                    bg_color="0072BC",
                    text_color_rgb=[255, 255, 255],
                    align="CENTER",
                )
                for h_idx, h in enumerate(lm_headers)
            ],
            is_header=True,
        )
    ]
    for l_idx, r_vals in enumerate(lm_data):
        bg = alt_row_hex if l_idx % 2 == 1 else "FFFFFF"
        lm_rows.append(
            TableRowNode(
                cells=[
                    CellNode(text=r_vals[0], bold=True, bg_color=alt_row_hex, align="CENTER"),
                    CellNode(text=r_vals[1], bg_color=bg, align="CENTER"),
                    CellNode(text=r_vals[2], bg_color=bg),
                ]
            )
        )
    return TableNode(rows=lm_rows)
