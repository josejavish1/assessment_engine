"""Constructs the global report payload, encapsulating the primary business logic for the Assessment Engine's reporting pipeline."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import tempfile
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from assessment_engine.domain.actuarial_scale_calibrator import (
    resolve_iso_currency_code,
    safe_float,
)

CURRENCY_SYMBOLS: Final[Mapping[str, str]] = MappingProxyType({
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "BRL": "R$",
    "MXN": "$",
    "CHF": "CHF",
    "CAD": "CA$",
    "AUD": "A$",
    "SEK": "kr",
    "NOK": "kr",
    "DKK": "kr.",
    "INR": "₹",
    "KRW": "₩",
    "CNY": "¥",
    "SGD": "S$",
    "HKD": "HK$",
    "PLN": "zł",
    "ZAR": "R",
    "AED": "AED",
    "SAR": "SAR",
})


def _discover_custom_risk_profiles(client_dir: Path) -> list[Path]:
    """Discovers tenant-level and domain-level custom_risk_profile.json files across any topology."""
    candidates: list[Path] = []
    root_profile = client_dir / "custom_risk_profile.json"
    if root_profile.exists():
        candidates.append(root_profile)
    candidates.extend(sorted(client_dir.glob("*/custom_risk_profile.json"), key=_natural_tower_sort_key))
    return candidates


DEFAULT_YEAR1_OPEX_RATIO: Final[float] = 0.40
DEFAULT_YEAR1_OPEX_FALLBACK: Final[float] = 250_000.0
MIN_EXECUTIVE_ALE_REVENUE_RATIO: Final[float] = 0.015
STRATEGIC_CYCLE_YEARS: Final[float] = 3.0
MONTHS_PER_YEAR: Final[float] = 12.0
DEFAULT_PAYBACK_MONTHS: Final[float] = 6.0
DEFAULT_ROI_RATIO: Final[float] = 1.0
MIN_SIGNIFICANT_CAPEX_THRESHOLD: Final[float] = 1_000.0

BILLION_THRESHOLD: Final[float] = 1_000_000_000.0
MILLION_THRESHOLD: Final[float] = 1_000_000.0
THOUSAND_THRESHOLD: Final[float] = 1_000.0

WAVE_0_MAX_INDEX: Final[int] = 12
WAVE_1_MAX_INDEX: Final[int] = 28
WAVE_2_MAX_INDEX: Final[int] = 44
WAVE_0_START_MONTH: Final[int] = 0
WAVE_0_DURATION_MONTHS: Final[int] = 3
WAVE_1_START_MONTH: Final[int] = 3
WAVE_1_DURATION_MONTHS: Final[int] = 9
WAVE_2_START_MONTH: Final[int] = 12
WAVE_2_DURATION_MONTHS: Final[int] = 12
WAVE_3_START_MONTH: Final[int] = 24
WAVE_3_DURATION_MONTHS: Final[int] = 12

TOP_CORPORATE_RISKS_LIMIT: Final[int] = 5

DEFAULT_ANNUAL_REVENUE_FALLBACK: Final[float] = 100_000_000.0
DEFAULT_HOURLY_DOWNTIME_COST_FALLBACK: Final[float] = 5_000.0
DEFAULT_REG_MAX_FINE_FALLBACK: Final[float] = 2_000_000.0
DEFAULT_FINOPS_WASTE_RATIO: Final[float] = 0.00135
DEFAULT_BASELINE_DOWNTIME_HOURS: Final[float] = 27.0
DEFAULT_TAIL_RISK_MIN_RATIO: Final[float] = 0.45
DEFAULT_TAIL_RISK_MAX_RATIO: Final[float] = 0.65

DEFAULT_TARGET_MATURITY_SCORE: Final[float] = 4.0
DEFAULT_AUDIT_MATURITY_FALLBACK: Final[float] = 3.0
DEFAULT_VULNERABILITY_LEVEL: Final[int] = 3
CRITICAL_VULNERABILITY_THRESHOLD: Final[int] = 5
HIGH_VULNERABILITY_THRESHOLD: Final[int] = 4
MIN_CENTRALITY_RISK_FLOOR: Final[float] = 0.01
CENTRALITY_PIVOT_SCORE: Final[float] = 3.0
CENTRALITY_SCALE_DIVISOR: Final[float] = 2.0


def _round_half_up(val: float, decimals: int = 0) -> float:
    """Deterministic half-up rounding avoiding IEEE-754 banker's rounding bias."""
    clean = safe_float(val, allow_zero=True) or 0.0
    quant_str = "1" if decimals <= 0 else f"0.{'0' * decimals}"
    try:
        res = Decimal(str(clean)).quantize(Decimal(quant_str), rounding=ROUND_HALF_UP)
        return float(res)
    except (InvalidOperation, ValueError, OverflowError):
        return 0.0

from assessment_engine.infrastructure.client_intelligence import (
    build_client_context_packet,
    load_client_intelligence,
)
from assessment_engine.infrastructure.global_maturity_policy import (
    average_pillar_score,
    average_pillar_target,
    band_for_score,
    status_color_for_score,
)
from assessment_engine.infrastructure.localization import (
    format_currency,
    format_date_localized,
    resolve_base_locale,
    t,
)
from assessment_engine.infrastructure.text_utils import clean_text_for_word

logger = logging.getLogger(__name__)

def get_tower_name(tid: str, doc_lang: str) -> str:
    """Resolve canonical tower name dynamically through localization."""
    return t(
        f"tower_{tid.lower()}_name",
        locale=doc_lang,
    )


def load_json(path: Path) -> dict[str, Any] | None:
    """Safely loads and parses a JSON file from a specified path with explicit logging on failure."""
    if not path.exists():
        logger.debug("JSON file does not exist at path: %s", path)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        logger.error("Failed to parse JSON file at %s: %s", path, exc)
        return None


def _natural_tower_sort_key(blueprint_path: Path) -> tuple[int, int | str, str]:
    """Deterministic natural sort key supporting both canonical (T1..TN) and custom (SEC-01) tower IDs."""
    folder_name = blueprint_path.parent.name.strip().upper()
    canonical_match = re.match(r"^T(\d+)$", folder_name)
    if canonical_match:
        return (0, int(canonical_match.group(1)), folder_name)

    num_match = re.search(r"(\d+)", folder_name)
    if num_match:
        prefix = folder_name[: num_match.start()]
        return (1, int(num_match.group(1)), prefix)
    return (2, 0, folder_name)


def _build_source_version(blueprint_towers: list[str]) -> str:
    blueprint_part = ",".join(blueprint_towers) or "none"
    return f"blueprint-only;blueprints={blueprint_part}"


def _aggregate_tower_blueprints(
    blueprint_files: list[Path],
    doc_lang: str,
) -> tuple[list[dict], list[dict], list[dict], list[str], list[str], list[str]]:
    """Parse and aggregate tower blueprint files into consolidated metrics and initiative lists."""
    towers_data: list[dict] = []
    strategic_risks: list[dict] = []
    all_initiatives: list[dict] = []
    all_principles: list[str] = []
    all_implications: list[str] = []
    blueprint_towers: list[str] = []

    for bp in sorted(blueprint_files, key=_natural_tower_sort_key):
        data = load_json(bp)
        if not data:
            continue

        tid = data.get("document_meta", {}).get("tower_code", bp.parent.name).upper()
        blueprint_towers.append(tid)
        doc_tname = data.get("document_meta", {}).get("tower_name")
        tname = doc_tname if doc_tname else get_tower_name(tid, doc_lang=doc_lang)

        pillars_analysis = data.get("pillars_analysis", [])
        avg_score = _round_half_up(average_pillar_score(pillars_analysis, default=0.0), 2)
        target_score = _round_half_up(
            average_pillar_target(pillars_analysis, default=DEFAULT_TARGET_MATURITY_SCORE), 2
        )

        towers_data.append(
            {
                "id": tid,
                "name": tname,
                "score": f"{avg_score:.1f}",
                "score_num": avg_score,
                "band": band_for_score(avg_score, doc_lang=doc_lang),
                "status_color": status_color_for_score(avg_score),
                "executive_message": data.get("executive_snapshot", {}).get(
                    "bottom_line", ""
                ),
                "target_maturity": f"{target_score:.1f}",
            }
        )

        r_idx = 1
        p_idx = 1
        for pillar in data.get("pillars_analysis", []):
            for hc in pillar.get("health_check_asis", []):
                vuln = hc.get("vulnerability_level", DEFAULT_VULNERABILITY_LEVEL)
                impact_label = (
                    t("critical_severity_lbl", locale=doc_lang)
                    if vuln >= CRITICAL_VULNERABILITY_THRESHOLD
                    else (
                        t("high_severity_lbl", locale=doc_lang)
                        if vuln >= HIGH_VULNERABILITY_THRESHOLD
                        else t("medium_severity_lbl", locale=doc_lang)
                    )
                )
                strategic_risks.append(
                    {
                        "id": f"R-{tid}-{r_idx:02d}",
                        "title": hc.get("capability")
                        or hc.get("target_state", t("capability_default_lbl", locale=doc_lang)),
                        "tower": tname,
                        "impact_level": impact_label,
                        "description": hc.get("finding"),
                        "business_impact": hc.get("business_risk") or hc.get("impact"),
                    }
                )
                r_idx += 1
            for proj in pillar.get("projects_todo", []):
                all_initiatives.append(
                    {
                        "id": f"INIT-{tid}-{p_idx:02d}",
                        "tower": tname,
                        "title": proj.get("name")
                        or proj.get("initiative", t("initiative_default_lbl", locale=doc_lang)),
                        "objective": proj.get("tech_objective")
                        or proj.get("objective", ""),
                        "priority": proj.get("priority", t("high_severity_lbl", locale=doc_lang)),
                        "expected_outcome": proj.get("business_case")
                        or proj.get("expected_outcome", ""),
                        "capex_estimate": str(
                            proj.get("capex_estimate")
                            or proj.get("capex")
                            or proj.get("budget")
                            or proj.get("opex_estimate")
                            or "0"
                        ),
                    }
                )
                p_idx += 1

        if data.get("architecture_principles"):
            all_principles.extend(data.get("architecture_principles", []))
        if data.get("operating_model_implications"):
            all_implications.extend(data.get("operating_model_implications", []))

    return (
        towers_data,
        strategic_risks,
        all_initiatives,
        all_principles,
        all_implications,
        blueprint_towers,
    )


def _get_cross_tower_nexus_rules(doc_lang: str) -> list[dict[str, str]]:
    """Declarative cross-tower nexus dependency rules resolved dynamically through i18n."""
    t1_name = f"T1: {get_tower_name('T1', doc_lang=doc_lang)}"
    t2_name = f"T2: {get_tower_name('T2', doc_lang=doc_lang)}"
    t3_name = f"T3: {get_tower_name('T3', doc_lang=doc_lang)}"
    t4_name = f"T4: {get_tower_name('T4', doc_lang=doc_lang)}"
    t5_name = f"T5: {get_tower_name('T5', doc_lang=doc_lang)}"
    t6_name = f"T6: {get_tower_name('T6', doc_lang=doc_lang)}"
    t7_name = f"T7: {get_tower_name('T7', doc_lang=doc_lang)}"
    t8_name = f"T8: {get_tower_name('T8', doc_lang=doc_lang)}"

    return [
        {
            "source_tower": t6_name,
            "target_tower": t2_name,
            "dependency_type": t("nexus_dep_type_critical", locale=doc_lang),
            "architectural_rationale": t("nexus_rule_1_rationale", locale=doc_lang),
            "delay_impact": t("nexus_rule_1_delay", locale=doc_lang),
        },
        {
            "source_tower": t5_name,
            "target_tower": t4_name,
            "dependency_type": t("nexus_dep_type_tech", locale=doc_lang),
            "architectural_rationale": t("nexus_rule_2_rationale", locale=doc_lang),
            "delay_impact": t("nexus_rule_2_delay", locale=doc_lang),
        },
        {
            "source_tower": t3_name,
            "target_tower": t1_name,
            "dependency_type": t("nexus_dep_type_resilience", locale=doc_lang),
            "architectural_rationale": t("nexus_rule_3_rationale", locale=doc_lang),
            "delay_impact": t("nexus_rule_3_delay", locale=doc_lang),
        },
        {
            "source_tower": t6_name,
            "target_tower": t7_name,
            "dependency_type": t("nexus_dep_type_ops", locale=doc_lang),
            "architectural_rationale": t("nexus_rule_4_rationale", locale=doc_lang),
            "delay_impact": t("nexus_rule_4_delay", locale=doc_lang),
        },
        {
            "source_tower": t8_name,
            "target_tower": t2_name,
            "dependency_type": t("nexus_dep_type_finops", locale=doc_lang),
            "architectural_rationale": t("nexus_rule_5_rationale", locale=doc_lang),
            "delay_impact": t("nexus_rule_5_delay", locale=doc_lang),
        },
    ]


def _parse_currency_amount_to_float(val_str: Any, locale: str | None = None) -> float:
    """Robustly parses localized currency strings into finite non-negative floats."""
    return safe_float(val_str, locale=locale, allow_zero=True) or 0.0


_PREFIX_CURRENCY_SYMBOLS: Final[frozenset[str]] = frozenset({
    "$", "£", "¥", "R$", "CA$", "A$", "S$", "HK$", "₹", "₩", "R",
})
_COMMA_DECIMAL_BASE_LANGS: Final[frozenset[str]] = frozenset({
    "es", "de", "fr", "it", "pt", "nl", "da", "pl", "tr", "id", "vi",
})


_GENERIC_INDUSTRY_PLACEHOLDERS: Final[frozenset[str]] = frozenset({
    "default",
    "enterprise",
    "general enterprise",
    "industry baseline",
    "unknown",
    "n/a",
})


def _format_executive_currency(
    val: float, currency_symbol: str = "€", doc_lang: str = "en"
) -> str:
    """Formats numeric amounts for C-Level executives respecting international locale and scale conventions."""
    clean_val = safe_float(val, allow_zero=True) or 0.0
    norm_loc = str(doc_lang or "en").strip().replace("_", "-").lower()
    parts = [p for p in norm_loc.split("-") if p]
    base_lang = parts[0] if parts else "en"
    region = parts[1] if len(parts) > 1 and len(parts[1]) == 2 else ""

    is_comma_decimal = (
        base_lang in _COMMA_DECIMAL_BASE_LANGS
        and not (base_lang == "es" and region in ("mx", "us", "pr"))
        and region != "ch"
    )
    is_prefix_symbol = (
        currency_symbol in _PREFIX_CURRENCY_SYMBOLS
        and (
            base_lang in ("en", "ja", "zh", "ko", "pt", "hi")
            or (base_lang == "es" and region in ("mx", "ar", "cl", "co", "pe", "uy", "us", "pr"))
        )
    )

    if clean_val >= BILLION_THRESHOLD:
        scaled = _round_half_up(clean_val / BILLION_THRESHOLD, 1)
        num_str = f"{scaled:.1f}"
        if is_comma_decimal:
            num_str = num_str.replace(".", ",")
        return f"{currency_symbol}{num_str}B" if is_prefix_symbol else f"{num_str}B {currency_symbol}"
    if clean_val >= MILLION_THRESHOLD or _round_half_up(clean_val / THOUSAND_THRESHOLD, 0) >= 1000.0:
        scaled = _round_half_up(clean_val / MILLION_THRESHOLD, 1)
        num_str = f"{scaled:.1f}"
        if is_comma_decimal:
            num_str = num_str.replace(".", ",")
        return f"{currency_symbol}{num_str}M" if is_prefix_symbol else f"{num_str}M {currency_symbol}"
    if clean_val >= THOUSAND_THRESHOLD:
        scaled = _round_half_up(clean_val / THOUSAND_THRESHOLD, 0)
        num_str = f"{scaled:.0f}"
        return f"{currency_symbol}{num_str}K" if is_prefix_symbol else f"{num_str}K {currency_symbol}"
    scaled = _round_half_up(clean_val, 0)
    num_str = f"{scaled:.0f}"
    return f"{currency_symbol}{num_str}" if is_prefix_symbol else f"{num_str} {currency_symbol}"


def _build_stratified_financial_case(
    client_name: str,
    client_dir: Path | None,
    towers_data: list[dict],
    blueprint_files: list[Path],
    doc_lang: str,
) -> dict[str, Any]:
    """Constructs a Tier-1 3-Layer Financial Risk & ROI Stratification model.

    100% dynamic, mathematical, and agnostic across any client, size, country, currency, and language.
    """
    fallbacks_path = (
        Path(__file__).resolve().parents[3]
        / "engine_config"
        / "policies"
        / "financial_fallbacks.json"
    )
    strat_metrics = {}
    if fallbacks_path.exists():
        try:
            fb_data = json.loads(fallbacks_path.read_text(encoding="utf-8"))
            strat_metrics = fb_data.get("financial_fallbacks", {}).get("stratification_metrics", {})
        except (OSError, ValueError, KeyError) as ex:
            logger.debug("[GlobalPayload] Fallbacks metrics loading fallback: %s", ex)

    finops_waste_ratio = safe_float(strat_metrics.get("finops_cash_waste_ratio")) or DEFAULT_FINOPS_WASTE_RATIO
    baseline_downtime_hours = safe_float(strat_metrics.get("baseline_annual_downtime_hours")) or DEFAULT_BASELINE_DOWNTIME_HOURS
    tail_risk_min_ratio = safe_float(strat_metrics.get("tail_risk_p90_ratio_min")) or DEFAULT_TAIL_RISK_MIN_RATIO
    tail_risk_max_ratio = safe_float(strat_metrics.get("tail_risk_p90_ratio_max")) or DEFAULT_TAIL_RISK_MAX_RATIO

    currency_code = "EUR"
    currency_symbol = "€"
    annual_revenue = safe_float(strat_metrics.get("default_annual_revenue")) or DEFAULT_ANNUAL_REVENUE_FALLBACK
    hourly_downtime_cost = safe_float(strat_metrics.get("default_hourly_downtime_cost")) or DEFAULT_HOURLY_DOWNTIME_COST_FALLBACK
    reg_max_fine = safe_float(strat_metrics.get("default_reg_max_fine")) or DEFAULT_REG_MAX_FINE_FALLBACK
    compliance_framework = t("default_compliance_framework", locale=doc_lang)

    if client_dir:
        intel_path = client_dir / "client_intelligence.json"
        if intel_path.exists():
            try:
                intel_data = json.loads(intel_path.read_text(encoding="utf-8-sig"))
                c_code = (
                    intel_data.get("currency")
                    or intel_data.get("currency_code")
                    or intel_data.get("profile", {}).get("currency")
                )
                if c_code:
                    currency_code = resolve_iso_currency_code(str(c_code), locale=doc_lang)
                    currency_symbol = CURRENCY_SYMBOLS.get(currency_code, currency_code)
                c_sym = intel_data.get("currency_symbol")
                if c_sym:
                    currency_symbol = str(c_sym).strip()
                    if not c_code:
                        currency_code = resolve_iso_currency_code(currency_symbol, locale=doc_lang)
                framework = (
                    intel_data.get("compliance", {}).get("primary_framework")
                    or intel_data.get("primary_framework")
                )
                if framework:
                    compliance_framework = framework
            except (OSError, ValueError, KeyError) as ex:
                logger.debug("[GlobalPayload] Intelligence currency/framework loading fallback: %s", ex)

        for prof_path in _discover_custom_risk_profiles(client_dir):
            try:
                prof_data = json.loads(prof_path.read_text(encoding="utf-8-sig"))
                raw_prof_code = prof_data.get("currency_code") or prof_data.get("currency")
                raw_prof_sym = prof_data.get("currency_symbol")
                if raw_prof_code:
                    currency_code = resolve_iso_currency_code(str(raw_prof_code), locale=doc_lang)
                elif raw_prof_sym:
                    currency_code = resolve_iso_currency_code(str(raw_prof_sym), locale=doc_lang)
                currency_symbol = str(
                    raw_prof_sym or CURRENCY_SYMBOLS.get(currency_code, currency_symbol)
                ).strip()
                annual_revenue = (
                    safe_float(prof_data.get("annual_revenue"), locale=doc_lang)
                    or safe_float(prof_data.get("annual_revenue_eur"), locale=doc_lang)
                    or annual_revenue
                )
                hourly_downtime_cost = (
                    safe_float(prof_data.get("hourly_downtime_cost"), locale=doc_lang)
                    or safe_float(prof_data.get("hourly_burn_rate"), locale=doc_lang)
                    or safe_float(prof_data.get("hourly_downtime_cost_eur"), locale=doc_lang)
                    or hourly_downtime_cost
                )
                reg_max_fine = (
                    safe_float(prof_data.get("reg_max_fine"), locale=doc_lang)
                    or safe_float(prof_data.get("reg_max_fine_eur"), locale=doc_lang)
                    or reg_max_fine
                )
                compliance_framework = prof_data.get("compliance_framework", compliance_framework)
                break
            except (OSError, ValueError, KeyError) as ex:
                logger.debug("[GlobalPayload] Risk profile loading fallback: %s", ex)

    total_opex_inv = 0.0
    total_capex_inv = 0.0
    year_1_opex = 0.0
    total_fair_ale = 0.0

    for bp in blueprint_files:
        try:
            bp_data = json.loads(bp.read_text(encoding="utf-8-sig"))
            t_ale_cands = [
                safe_float(bp_data.get("total_fair_ale"), locale=doc_lang, allow_zero=True),
                safe_float(bp_data.get("annualized_loss_expectancy"), locale=doc_lang, allow_zero=True),
                safe_float(bp_data.get("executive_summary", {}).get("total_fair_ale"), locale=doc_lang, allow_zero=True),
            ]
            t_ale = next((c for c in t_ale_cands if c is not None), 0.0)
            total_fair_ale += t_ale
            for pil in bp_data.get("pillars_analysis", []):
                for pr in pil.get("projects_todo", []):
                    op_val = _parse_currency_amount_to_float(pr.get("opex_estimate"), locale=doc_lang)
                    total_opex_inv += op_val
                    if any(h in str(pr.get("duration", "")) for h in ("H1", "H2", "1", "2")):
                        year_1_opex += op_val
                    cap_val = _parse_currency_amount_to_float(pr.get("capex_estimate"), locale=doc_lang)
                    total_capex_inv += cap_val
        except Exception as ex:
            logger.debug("[Financial Stratification] Error parsing blueprint: %s", ex)

    if year_1_opex <= 0.0:
        year_1_opex = (
            total_opex_inv * DEFAULT_YEAR1_OPEX_RATIO
            if total_opex_inv > 0.0
            else DEFAULT_YEAR1_OPEX_FALLBACK
        )

    # Layer 1: Cash Inefficiency modeling
    layer_1_amount = _round_half_up(annual_revenue * finops_waste_ratio, 0)
    layer_1_display = format_currency(layer_1_amount, currency_code=currency_code, locale=doc_lang, decimals=0)

    # Operational downtime friction component
    layer_2_amount = _round_half_up(hourly_downtime_cost * baseline_downtime_hours, 0)
    layer_2_display = format_currency(layer_2_amount, currency_code=currency_code, locale=doc_lang, decimals=0)

    # Layer 3: Dynamic Actuarial Tail Risk (P90 FAIR value: calibrated ratio of total FAIR exposure)
    if total_fair_ale <= 0.0:
        total_fair_ale = annual_revenue * MIN_EXECUTIVE_ALE_REVENUE_RATIO
        
    layer_3_min = _round_half_up(total_fair_ale * tail_risk_min_ratio, 0)
    layer_3_max = _round_half_up(total_fair_ale * tail_risk_max_ratio, 0)
    l3_min_fmt = format_currency(layer_3_min, currency_code=currency_code, locale=doc_lang, decimals=0)
    l3_max_fmt = format_currency(layer_3_max, currency_code=currency_code, locale=doc_lang, decimals=0)
    layer_3_display = f"{l3_min_fmt} - {l3_max_fmt}"

    # Payback & ROI (TCO = OpEx + CapEx vs Total Financial Exposure Mitigated over 3 years)
    total_inv = year_1_opex + total_capex_inv
    # The true 'savings' is the cash inefficiency + downtime friction + expected actuarial loss avoided, projected over a 3-year strategic cycle
    annual_value_protected = layer_1_amount + layer_2_amount + layer_3_max
    total_value_protected = annual_value_protected * STRATEGIC_CYCLE_YEARS
    
    payback_months = (
        _round_half_up((total_inv / annual_value_protected) * MONTHS_PER_YEAR, 1)
        if annual_value_protected > 0
        else DEFAULT_PAYBACK_MONTHS
    )
    roi_ratio = (
        _round_half_up(total_value_protected / total_inv, 1)
        if total_inv > 0
        else DEFAULT_ROI_RATIO
    )

    hourly_cost_fmt = format_currency(hourly_downtime_cost, currency_code=currency_code, locale=doc_lang, decimals=0)
    reg_fine_fmt = format_currency(reg_max_fine, currency_code=currency_code, locale=doc_lang, decimals=0)
    total_opex_fmt = _format_executive_currency(year_1_opex, currency_symbol=currency_symbol, doc_lang=doc_lang)
    total_capex_fmt = _format_executive_currency(total_capex_inv, currency_symbol=currency_symbol, doc_lang=doc_lang)
    total_value_fmt = _format_executive_currency(total_value_protected, currency_symbol=currency_symbol, doc_lang=doc_lang)

    placeholders = {
        "currency": currency_symbol,
        "hourly_cost": hourly_cost_fmt,
        "compliance_framework": compliance_framework,
        "reg_max_fine": reg_fine_fmt,
        "total_opex": total_opex_fmt,
        "total_capex": total_capex_fmt,
        "year_1_savings": total_value_fmt,
        "payback_months": f"{payback_months:.0f}",
        "roi_ratio": f"{roi_ratio}",
    }

    return {
        "title": t("financial_stratification_title", locale=doc_lang),
        "layer_1_cash_inefficiency": {
            "title": t("layer_1_title", locale=doc_lang),
            "amount_display": f"~{layer_1_display}",
            "bullets": [
                t("layer_1_bullet_1", locale=doc_lang, **placeholders),
                t("layer_1_bullet_2", locale=doc_lang, **placeholders),
                t("layer_1_bullet_3", locale=doc_lang, **placeholders),
            ],
        },
        "layer_2_operational_friction": {
            "title": t("layer_2_title", locale=doc_lang),
            "amount_display": f"~{layer_2_display}",
            "bullets": [
                t("layer_2_bullet_1", locale=doc_lang, **placeholders),
                t("layer_2_bullet_2", locale=doc_lang, **placeholders),
            ],
        },
        "layer_3_actuarial_tail_risk": {
            "title": t("layer_3_title", locale=doc_lang),
            "amount_display": f"~{layer_3_display} ({t('actuarial_p90_label', locale=doc_lang)})",
            "bullets": [
                t("layer_3_bullet_1", locale=doc_lang, **placeholders),
                t("layer_3_bullet_2", locale=doc_lang, **placeholders),
                t("layer_3_bullet_3", locale=doc_lang, **placeholders),
            ],
        },
        "return_on_investment": {
            "title": t("roi_statement_label", locale=doc_lang),
            "body": t("roi_statement_body", locale=doc_lang, **placeholders),
            "total_opex_investment": total_opex_fmt,
            "capex_required": total_capex_fmt,
            "year_1_cash_savings": layer_1_display,
            "payback_period": f"~{payback_months:.0f} {t('months_unit_lbl', locale=doc_lang)}",
            "roi_ratio": f"{roi_ratio}x",
        },
    }


def _build_board_memo(
    towers_data: list[dict],
    blueprint_files: list[Path],
    client_name: str,
    doc_lang: str,
    client_dir: Path | None = None,
) -> dict[str, Any]:
    currency_code = "EUR"
    currency_symbol = "€"
    if client_dir:
        intel_path = client_dir / "client_intelligence.json"
        if intel_path.exists():
            try:
                intel_data = json.loads(intel_path.read_text(encoding="utf-8-sig"))
                c_code = (
                    intel_data.get("currency")
                    or intel_data.get("currency_code")
                    or intel_data.get("profile", {}).get("currency")
                )
                if c_code:
                    currency_code = resolve_iso_currency_code(str(c_code), locale=doc_lang)
                    currency_symbol = CURRENCY_SYMBOLS.get(currency_code, currency_code)
                c_sym = intel_data.get("currency_symbol")
                if c_sym:
                    currency_symbol = str(c_sym).strip()
                    if not c_code:
                        currency_code = resolve_iso_currency_code(currency_symbol, locale=doc_lang)
            except (OSError, ValueError, KeyError, TypeError) as ex:
                logger.debug("Error reading client_intelligence currency: %s", ex)

        for prof_path in _discover_custom_risk_profiles(client_dir):
            try:
                prof_data = json.loads(prof_path.read_text(encoding="utf-8-sig"))
                raw_prof_code = prof_data.get("currency_code") or prof_data.get("currency")
                raw_prof_sym = prof_data.get("currency_symbol")
                if raw_prof_code:
                    currency_code = resolve_iso_currency_code(str(raw_prof_code), locale=doc_lang)
                elif raw_prof_sym:
                    currency_code = resolve_iso_currency_code(str(raw_prof_sym), locale=doc_lang)
                currency_symbol = str(
                    raw_prof_sym or CURRENCY_SYMBOLS.get(currency_code, currency_symbol)
                ).strip()
                break
            except (OSError, ValueError, KeyError) as ex:
                logger.debug("[GlobalPayload] Currency loading fallback: %s", ex)

    items = []
    total_holding_opex = 0.0
    total_holding_capex = 0.0

    for t_item in towers_data:
        tid = t_item.get("id", "")
        tname = t_item.get("name", "")
        if not tname:
            tower_loc = t(f"tower_{tid.lower()}_name", locale=doc_lang)
            if tower_loc and tower_loc != f"tower_{tid.lower()}_name":
                tname = tower_loc
        score = t_item.get("score", "0.0")
        band = t_item.get("band", "")
        status_color = t_item.get("status_color", "E06666")

        coi_text = t("parametric_evaluation_lbl", locale=doc_lang)
        opex_tower = 0.0
        capex_tower = 0.0
        top_project_name = None

        for bp in blueprint_files:
            if bp.parent.name.upper() == tid.upper():
                cand = bp.parent / f"approved_annex_{tid.lower()}.template_payload.json"
                if cand.exists():
                    try:
                        ax_data = json.loads(cand.read_text(encoding="utf-8-sig"))
                        fin_coi = ax_data.get("executive_summary", {}).get("financial_coi", {})
                        raw_ext = fin_coi.get("coi_3y_extreme") or fin_coi.get("coi_3y_ordinary")
                        ext_num = _parse_currency_amount_to_float(raw_ext, locale=doc_lang)
                        if ext_num > 0.0:
                            ext_fmt = _format_executive_currency(ext_num, currency_symbol, doc_lang)
                            coi_text = t("coi_3y_ext", locale=doc_lang, amount=ext_fmt)
                    except Exception as err:
                        logger.debug("Error reading annex for coi_text: %s", err)
                try:
                    bp_data = json.loads(bp.read_text(encoding="utf-8-sig"))
                    for pil in bp_data.get("pillars_analysis", []):
                        for pr in pil.get("projects_todo", []):
                            if not top_project_name and pr.get("name"):
                                top_project_name = pr.get("name")
                            opex_tower += _parse_currency_amount_to_float(pr.get("opex_estimate"), locale=doc_lang)
                            capex_tower += _parse_currency_amount_to_float(pr.get("capex_estimate"), locale=doc_lang)
                except Exception as err:
                    logger.debug("Error reading blueprint for budget: %s", err)

        total_holding_opex += opex_tower
        total_holding_capex += capex_tower
        total_inv_tower = opex_tower + capex_tower

        fallback_budget_lbl = t("budget_subscription_fallback", locale=doc_lang)
        if total_inv_tower > 0:
            if capex_tower >= MIN_SIGNIFICANT_CAPEX_THRESHOLD:
                tot_fmt = _format_executive_currency(total_inv_tower, currency_symbol, doc_lang)
                cap_fmt = _format_executive_currency(capex_tower, currency_symbol, doc_lang)
                op_fmt = _format_executive_currency(opex_tower, currency_symbol, doc_lang)
                budget_display = t(
                    "budget_capex_opex_format",
                    locale=doc_lang,
                    total_inv=tot_fmt,
                    capex=cap_fmt,
                    opex=op_fmt,
                )
            else:
                op_fmt = _format_executive_currency(total_inv_tower, currency_symbol, doc_lang)
                budget_display = t(
                    "budget_pure_opex_format",
                    locale=doc_lang,
                    opex=op_fmt,
                )
        else:
            budget_display = fallback_budget_lbl

        # Board Decisions must remain strictly at the executive program level (C-Suite altitude)
        strat_dec = t(f"decision_{tid}", locale=doc_lang)
        if strat_dec and strat_dec != f"decision_{tid}":
            crit_dec = strat_dec
        elif top_project_name:
            crit_dec = t(
                "decision_priority_project_template",
                locale=doc_lang,
                project_name=top_project_name,
                tower_name=tname,
            )
        else:
            crit_dec = t("decision_default_template", locale=doc_lang, tower_name=tname)

        items.append({
            "domain": f"{tid}: {tname}",
            "score": score,
            "band": band,
            "status_color": status_color,
            "fair_exposure_3y": coi_text,
            "critical_decision": crit_dec,
            "budget_estimate": budget_display,
        })

    stratified_case = _build_stratified_financial_case(client_name, client_dir, towers_data, blueprint_files, doc_lang=doc_lang)

    memo_headline = t(
        "board_memo_headline",
        locale=doc_lang,
        client_name=client_name,
    )
    memo_summary = t(
        "board_memo_summary",
        locale=doc_lang,
    )
    memo_consolidated_exposure = t(
        "board_memo_consolidated_exposure",
        locale=doc_lang,
    )

    tot_holding_all = total_holding_opex + total_holding_capex
    tot_all_fmt = format_currency(tot_holding_all, currency_code=currency_code, locale=doc_lang, decimals=0)
    tot_cap_fmt = format_currency(total_holding_capex, currency_code=currency_code, locale=doc_lang, decimals=0)
    tot_op_fmt = format_currency(total_holding_opex, currency_code=currency_code, locale=doc_lang, decimals=0)

    memo_budget_estimate_txt = t(
        "total_holding_budget_summary",
        locale=doc_lang,
        total_inv=tot_all_fmt,
        total_capex=tot_cap_fmt,
        total_opex=tot_op_fmt,
    )

    return {
        "headline": memo_headline,
        "summary": memo_summary,
        "items": items,
        "consolidated_exposure_3y": memo_consolidated_exposure,
        "total_budget_estimate": memo_budget_estimate_txt,
        "financial_stratification": stratified_case,
    }


def _build_cross_tower_nexus(
    towers_data: list[dict],
    _blueprint_files: list[Path] | None = None,
    doc_lang: str = "en",
) -> dict[str, Any]:
    gen_tids = {t["id"].upper() for t in towers_data}
    all_rules = _get_cross_tower_nexus_rules(doc_lang=doc_lang)
    active_rules = [
        r
        for r in all_rules
        if r["source_tower"].split(":")[0].strip().upper() in gen_tids
        and r["target_tower"].split(":")[0].strip().upper() in gen_tids
    ]
    if not active_rules:
        active_rules = [
            r
            for r in all_rules
            if r["source_tower"].split(":")[0].strip().upper() in gen_tids
            or r["target_tower"].split(":")[0].strip().upper() in gen_tids
        ]

    return {
        "title": t(
            "nexus_matrix_title",
            locale=doc_lang,
        ),
        "description": t(
            "nexus_matrix_description",
            locale=doc_lang,
        ),
        "dependencies": active_rules if active_rules else all_rules,
    }


def _build_executive_callouts(
    client_name: str,
    towers_data: list[dict],
    doc_lang: str,
    client_dir: Path | None = None,
) -> list[dict[str, str]]:
    fallbacks_path = (
        Path(__file__).resolve().parents[3]
        / "engine_config"
        / "policies"
        / "financial_fallbacks.json"
    )
    strat_metrics = {}
    if fallbacks_path.exists():
        try:
            fb_data = json.loads(fallbacks_path.read_text(encoding="utf-8"))
            strat_metrics = fb_data.get("financial_fallbacks", {}).get("stratification_metrics", {})
        except (OSError, ValueError, KeyError) as ex:
            logger.debug("[GlobalPayload] Fallbacks metrics loading fallback: %s", ex)

    currency_code = "EUR"
    currency_symbol = "€"
    hourly_downtime_cost = (
        safe_float(strat_metrics.get("default_hourly_downtime_cost"))
        or DEFAULT_HOURLY_DOWNTIME_COST_FALLBACK
    )
    reg_max_fine = (
        safe_float(strat_metrics.get("default_reg_max_fine"))
        or DEFAULT_REG_MAX_FINE_FALLBACK
    )
    industry_name = t("default_industry_name", locale=doc_lang)

    if client_dir:
        for prof_path in _discover_custom_risk_profiles(client_dir):
            try:
                prof_data = json.loads(prof_path.read_text(encoding="utf-8-sig"))
                raw_prof_code = prof_data.get("currency_code") or prof_data.get("currency")
                raw_prof_sym = prof_data.get("currency_symbol")
                if raw_prof_code:
                    currency_code = resolve_iso_currency_code(str(raw_prof_code), locale=doc_lang)
                elif raw_prof_sym:
                    currency_code = resolve_iso_currency_code(str(raw_prof_sym), locale=doc_lang)
                currency_symbol = str(
                    raw_prof_sym or CURRENCY_SYMBOLS.get(currency_code, currency_symbol)
                ).strip()
                hourly_downtime_cost = (
                    safe_float(prof_data.get("hourly_downtime_cost"), locale=doc_lang)
                    or safe_float(prof_data.get("hourly_burn_rate"), locale=doc_lang)
                    or safe_float(prof_data.get("hourly_downtime_cost_eur"), locale=doc_lang)
                    or hourly_downtime_cost
                )
                reg_max_fine = (
                    safe_float(prof_data.get("reg_max_fine"), locale=doc_lang)
                    or safe_float(prof_data.get("reg_max_fine_eur"), locale=doc_lang)
                    or reg_max_fine
                )
                break
            except (OSError, ValueError, KeyError, TypeError) as ex:
                logger.debug("Error reading custom_risk_profile: %s", ex)

        intel_path = client_dir / "client_intelligence.json"
        if intel_path.exists():
            try:
                intel_data = json.loads(intel_path.read_text(encoding="utf-8-sig"))
                ind = intel_data.get("profile", {}).get("industry") or intel_data.get("industry")
                if ind:
                    ind_clean = str(ind).lower().strip()
                    if ind_clean in _GENERIC_INDUSTRY_PLACEHOLDERS:
                        industry_name = t("default_industry_name", locale=doc_lang)
                    else:
                        industry_name = str(ind).strip()
            except (OSError, ValueError, KeyError, TypeError) as ex:
                logger.debug("Error reading client_intelligence industry: %s", ex)

    reg_fine_fmt = format_currency(reg_max_fine, currency_code=currency_code, locale=doc_lang, decimals=0)
    hourly_cost_fmt = format_currency(hourly_downtime_cost, currency_code=currency_code, locale=doc_lang, decimals=0)

    placeholders = {
        "client_name": client_name,
        "industry_name": industry_name,
        "reg_max_fine": reg_fine_fmt,
        "hourly_downtime_cost": hourly_cost_fmt,
        "currency": currency_symbol,
    }

    return [
        {
            "callout_type": "legal",
            "title": t("callout_regulatory_title", locale=doc_lang),
            "message": t("callout_regulatory_message", locale=doc_lang, **placeholders),
            "key_metric": t("callout_regulatory_metric", locale=doc_lang, **placeholders),
        },
        {
            "callout_type": "factory",
            "title": t("callout_continuity_title", locale=doc_lang),
            "message": t("callout_continuity_message", locale=doc_lang, **placeholders),
            "key_metric": t("callout_continuity_metric", locale=doc_lang, **placeholders),
        },
        {
            "callout_type": "decision",
            "title": t("callout_wave0_title", locale=doc_lang),
            "message": t("callout_wave0_message", locale=doc_lang, **placeholders),
            "key_metric": t("callout_wave0_metric", locale=doc_lang, **placeholders),
        },
    ]


def build_global_payload(
    client_dir: Path, client_name: str, doc_lang: str | None = None
) -> dict[str, Any] | None:
    """Aggregates client data into a consolidated global report payload across all evaluated domains."""
    blueprint_files = sorted(
        client_dir.glob("*/blueprint_*_payload.json"),
        key=_natural_tower_sort_key,
    )

    if not blueprint_files:
        logger.warning("No tower payload files found in %s", client_dir)
        return None

    intelligence_dossier = {}
    resolved_lang = doc_lang
    intelligence_path = Path(client_dir) / "client_intelligence.json"
    if intelligence_path.exists():
        try:
            raw_int = json.loads(intelligence_path.read_text(encoding="utf-8-sig"))
            intelligence_dossier = build_client_context_packet(raw_int)
            if not resolved_lang:
                resolved_lang = (
                    raw_int.get("language")
                    or raw_int.get("locale")
                    or raw_int.get("doc_lang")
                )
        except Exception as ex:
            logger.debug("Failed to load client_intelligence.json at %s: %s", intelligence_path, ex)
            intelligence_dossier = {}

    if not resolved_lang:
        resolved_lang = os.environ.get("ASSESSMENT_DOC_LANG") or os.environ.get("ASSESSMENT_LANGUAGE")

    doc_lang = resolve_base_locale(resolved_lang or "en")

    (
        towers_data,
        strategic_risks,
        all_initiatives,
        all_principles,
        all_implications,
        blueprint_towers,
    ) = _aggregate_tower_blueprints(blueprint_files, doc_lang=doc_lang)

    if not towers_data:
        return None

    # Pass 2 (A Posteriori): Propagate actual audited scores through the Epistemic Graph BBN
    try:
        from assessment_engine.infrastructure.epistemic_graph_service import (
            EpistemicGraphService,
        )

        ind_profile = intelligence_dossier.get("profile", {}).get("industry", "default")
        graph_service = EpistemicGraphService(industry_profile=ind_profile)

        intrinsic_audited = {
            item["id"]: (
                safe_float(
                    item.get("score_num") if item.get("score_num") is not None else item.get("score"),
                    locale=doc_lang,
                    allow_zero=True,
                )
                or 0.0
            )
            for item in towers_data
        }
        # Actuarial model: Impute empirical mean of audited towers to prevent Bayesian dilution bias
        avg_audited_score = (
            sum(intrinsic_audited.values()) / len(intrinsic_audited)
            if intrinsic_audited
            else DEFAULT_AUDIT_MATURITY_FALLBACK
        )
        for t_id in graph_service.towers:
            if t_id not in intrinsic_audited:
                intrinsic_audited[t_id] = avg_audited_score

        propagated_audited = graph_service.propagate_risk(intrinsic_audited)

        # Calculate actual audited risk volatilities for PageRank Centrality
        audited_risks = {
            t_id: max(
                MIN_CENTRALITY_RISK_FLOOR,
                1.0 - (propagated_audited.get(t_id, DEFAULT_TARGET_MATURITY_SCORE) - CENTRALITY_PIVOT_SCORE) / CENTRALITY_SCALE_DIVISOR,
            )
            for t_id in graph_service.towers
        }
        audited_centrality = graph_service.calculate_risk_centrality(audited_risks)
        empirical_spof = (
            max(audited_centrality.items(), key=lambda kv: (kv[1], kv[0]))[0]
            if audited_centrality
            else (towers_data[0]["id"] if towers_data else "T1")
        )

        # Update towers_data with propagated (effective) maturity scores
        for item in towers_data:
            tid = item["id"].upper()
            score_cand = item.get("score_num") if item.get("score_num") is not None else item.get("score")
            fallback_score = safe_float(score_cand, locale=doc_lang, allow_zero=True) or 0.0
            eff_score = _round_half_up(propagated_audited.get(tid, fallback_score), 2)
            item["effective_score"] = f"{eff_score:.1f}"
            item["effective_score_num"] = eff_score
            item["effective_band"] = band_for_score(eff_score, doc_lang=doc_lang)
            item["effective_status_color"] = status_color_for_score(eff_score)

        avg_effective_score = _round_half_up(
            sum(
                safe_float(
                    t.get("effective_score_num") if t.get("effective_score_num") is not None else t.get("effective_score"),
                    locale=doc_lang,
                    allow_zero=True,
                ) or 0.0
                for t in towers_data
            )
            / max(1, len(towers_data)),
            2,
        )

        epistemic_analysis = {
            "empirical_single_point_of_failure": empirical_spof,
            "empirical_risk_centrality": audited_centrality,
            "average_effective_score": avg_effective_score,
            "propagated_effective_scores": {
                k: f"{v:.1f}" for k, v in propagated_audited.items()
            },
        }
    except Exception as e:
        logger.warning(
            f"Error calculating A Posteriori epistemic risk propagation: {e}"
        )
        avg_effective_score = 0.0
        epistemic_analysis = {}

    blueprint_towers = sorted(dict.fromkeys(blueprint_towers))

    # Executes the graph-based resolution algorithm to determine strategic alignments and dependencies, a core component of Phase 2 Tier 1 logic.
    try:
        from assessment_engine.application.run_strategic_orchestrator import (
            run_strategic_orchestration,
        )

        run_strategic_orchestration(client_name)
    except Exception as ex:
        logger.debug("[GlobalPayload] Strategic orchestration deferred: %s", ex)

    # Collect approved priority initiatives across towers for clean executive horizons
    approved_initiatives = []
    if client_dir:
        for bp in blueprint_files:
            cand = bp.parent / f"approved_annex_{bp.parent.name.lower()}.template_payload.json"
            if cand.exists():
                try:
                    ax = json.loads(cand.read_text(encoding="utf-8-sig"))
                    inits = ax.get("sections", {}).get("todo", {}).get("priority_initiatives", [])
                    for it in inits:
                        approved_initiatives.append({
                            "tower": bp.parent.name,
                            "initiative": it.get("initiative", ""),
                            "objective": it.get("objective", ""),
                            "priority": it.get("priority", "Medium"),
                        })
                except Exception as ex:
                    logger.debug("Error reading approved_annex: %s", ex)

    final_horizons = {
        "quick_wins_0_3_months": [],
        "year_1_3_12_months": [],
        "year_2_12_24_months": [],
        "year_3_24_36_months": [],
    }

    wave_0_lbl = t("wave_0_title", locale=doc_lang)
    wave_1_lbl = t("wave_1_title", locale=doc_lang)
    wave_2_lbl = t("wave_2_title", locale=doc_lang)
    wave_3_lbl = t("wave_3_title", locale=doc_lang)

    default_init_prefix = t("initiative_default_lbl", locale=doc_lang)
    high_priority_tokens = {
        str(tok).strip().lower()
        for tok in ("high", "critical", t("high_severity_lbl", locale=doc_lang))
        if str(tok).strip()
    }

    for idx, item in enumerate(approved_initiatives):
        proj_name = clean_text_for_word(item.get("initiative") or f"{default_init_prefix} {idx + 1}")
        obj_text = clean_text_for_word(item.get("objective", "")) or t("quick_win_objective_default", locale=doc_lang)
        prio = str(item.get("priority", "")).lower()

        if any(tok in prio for tok in high_priority_tokens) or idx < WAVE_0_MAX_INDEX:
            h_key = "quick_wins_0_3_months"
            w_lbl = wave_0_lbl
            s_m = WAVE_0_START_MONTH
            d_m = WAVE_0_DURATION_MONTHS
        elif idx < WAVE_1_MAX_INDEX:
            h_key = "year_1_3_12_months"
            w_lbl = wave_1_lbl
            s_m = WAVE_1_START_MONTH
            d_m = WAVE_1_DURATION_MONTHS
        elif idx < WAVE_2_MAX_INDEX:
            h_key = "year_2_12_24_months"
            w_lbl = wave_2_lbl
            s_m = WAVE_2_START_MONTH
            d_m = WAVE_2_DURATION_MONTHS
        else:
            h_key = "year_3_24_36_months"
            w_lbl = wave_3_lbl
            s_m = WAVE_3_START_MONTH
            d_m = WAVE_3_DURATION_MONTHS

        init_def = {
            "program": w_lbl,
            "title": proj_name,
            "business_case": obj_text,
            "start_month": s_m,
            "duration_months": d_m,
        }
        final_horizons[h_key].append(init_def)

    avg_score = _round_half_up(
        sum(
            safe_float(
                t.get("score_num") if t.get("score_num") is not None else t.get("score"),
                locale=doc_lang,
                allow_zero=True,
            ) or 0.0
            for t in towers_data
        )
        / max(1, len(towers_data)),
        2,
    )

    # Performs deduplication on the aggregated list and truncates it to a predefined maximum length, ensuring the final result set is both unique and concise.
    unique_principles = list(dict.fromkeys(all_principles))
    unique_implications = list(dict.fromkeys(all_implications))

    dynamic_date_str = format_date_localized(locale=doc_lang)
    version_str = t("report_version_dto", locale=doc_lang)

    # Serializes the resolved data into the final `GlobalReportPayload` Pydantic schema for validation and downstream consumption.
    payload = {
        "_generation_metadata": {
            "artifact_type": "global_report_payload",
            "artifact_version": "1.0.0",
            "source_version": _build_source_version(blueprint_towers),
        },
        "meta": {
            "client": client_name,
            "date": dynamic_date_str,
            "version": version_str,
            "language": doc_lang,
        },
        "executive_summary": {
            "headline": t(
                "maturity_pulse_headline_template",
                locale=doc_lang,
                avg_score=f"{avg_score:.1f}",
            ),
            "narrative": t("executive_summary_narrative_default", locale=doc_lang),
            "key_business_impacts": [
                t("impact_time_to_market", locale=doc_lang),
                t("impact_operational_risk", locale=doc_lang),
                t("impact_cost_optimization", locale=doc_lang),
            ],
            "top_strategic_risks": strategic_risks[:TOP_CORPORATE_RISKS_LIMIT],
            "maturity_pulse": {
                "score": avg_score,
                "band": band_for_score(avg_score, doc_lang=doc_lang),
                "trend": "Stable",
            },
        },
        "strategic_overview": {
            "asis_summary": t(
                "strategic_overview_asis_default",
                locale=doc_lang,
            ),
            "tobe_vision": t(
                "strategic_overview_tobe_default",
                locale=doc_lang,
            ),
            "value_targets": unique_implications[:TOP_CORPORATE_RISKS_LIMIT],
        },
        "burning_platform": [
            {
                "theme": risk.get("title", t("risk_theme_default", locale=doc_lang)),
                "business_risk": risk.get("business_impact", t("risk_business_impact_default", locale=doc_lang)),
                "root_causes": [
                    risk.get("description", t("risk_root_cause_default", locale=doc_lang))
                ],
            }
            for risk in strategic_risks[:TOP_CORPORATE_RISKS_LIMIT]
        ],
        "intelligence_dossier": intelligence_dossier,
        "epistemic_analysis": epistemic_analysis,
        "heatmap": towers_data,
        "tower_bottom_lines": [
            {
                "id": t_item["id"],
                "name": t_item["name"],
                "score": t_item["score"],
                "band": t_item["band"],
                "status_color": t_item["status_color"],
                "bottom_line": t_item["executive_message"],
            }
            for t_item in towers_data
        ],
        "target_vision": {
            "value_proposition": t(
                "target_vision_value_prop_default",
                locale=doc_lang,
            ),
            "evolution_principles": [
                {
                    "principle": p,
                    "description": t("evolution_principle_desc_default", locale=doc_lang),
                }
                for p in unique_principles[:TOP_CORPORATE_RISKS_LIMIT]
            ],
            "strategic_pillars": [
                {
                    "pillar": p,
                    "description": t("strategic_pillar_desc_default", locale=doc_lang),
                }
                for p in unique_implications[:TOP_CORPORATE_RISKS_LIMIT]
            ],
        },
        "execution_roadmap": {
            "programs": [],
            "horizons": final_horizons,
        },
        "executive_decisions": {
            "immediate_decisions": [
                {
                    "decision_type": t("decision_type_investment", locale=doc_lang),
                    "action_required": t("immediate_decision_wave0_action", locale=doc_lang),
                    "impact_if_delayed": t("immediate_decision_wave0_delay", locale=doc_lang),
                }
            ]
        },
        "visuals": {
            "radar_chart": "global_radar_chart.png",
            "roadmap_timeline": "global_roadmap_timeline.png",
        },
    }

    # Populates the Programs-by-Tower data structure, a prerequisite for enabling the 'To-Do' deep dive analysis feature in the final report.
    for t_item in towers_data:
        tid = t_item.get("id", "")
        actual_tname = t_item.get("name", "")
        if not actual_tname:
            loc_tname = t(f"tower_{tid.lower()}_name", locale=doc_lang)
            if loc_tname and loc_tname != f"tower_{tid.lower()}_name":
                actual_tname = loc_tname
        prog_name = t(
            "program_modernization_template",
            locale=doc_lang,
            tower_name=actual_tname,
        )
        
        exec_msg = t_item.get("executive_message", "")
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z\u00C0-\u017F])", exec_msg.strip())
        prog_desc = sentences[0] if sentences else exec_msg
        
        payload["execution_roadmap"]["programs"].append(
            {
                "id": t_item["id"],
                "name": prog_name,
                "description": prog_desc,
                "projects": [i for i in all_initiatives if i["tower"] == t_item["name"]],
            }
        )

    from assessment_engine.application.tools.corporate_project_aggregator import (
        aggregate_corporate_projects,
    )

    corp_result = aggregate_corporate_projects(all_initiatives)
    payload["execution_roadmap"]["corporate_programs"] = [
        {
            "program_id": cp.program_id,
            "participating_towers": cp.participating_towers,
            "linear_capex": cp.linear_capex_numeric,
            "consolidated_capex": cp.consolidated_capex_numeric,
            "synergy_savings": cp.synergy_savings_numeric,
            "work_packages_count": len(cp.work_packages),
            "work_packages": [
                {
                    "id": wp.id,
                    "tower": wp.tower,
                    "title": wp.title,
                    "objective": wp.objective,
                    "priority": wp.priority,
                    "capex_numeric": wp.capex_numeric,
                }
                for wp in cp.work_packages
            ],
        }
        for cp in corp_result.get("programs", [])
    ]
    payload["execution_roadmap"]["standalone_initiatives"] = corp_result.get(
        "standalone_initiatives", []
    )

    # Applies an executive-level refinement layer, allowing for the direct override of certain report elements as specified by Tier 1 configurations.
    # Dynamically extracts the headline and C-level narrative from client-specific configuration extensions, if such extensions are provided.
    intel_headline = None
    intel_narrative = None

    if intelligence_path.exists():
        try:
            raw_intel = load_client_intelligence(intelligence_path)
            extensions = (
                raw_intel.get("extensions", {}) if isinstance(raw_intel, dict) else {}
            )
            exec_sum = (
                extensions.get("executive_summary", {})
                if isinstance(extensions, dict)
                else {}
            )
            if isinstance(exec_sum, dict):
                intel_headline = exec_sum.get("headline")
                intel_narrative = exec_sum.get("narrative")
        except (OSError, ValueError, KeyError, AttributeError) as ex:
            logger.debug(f"[Fallback] Handled exception: {ex}")

    if intel_headline:
        payload["executive_summary"]["headline"] = intel_headline
    else:
        payload["executive_summary"]["headline"] = t(
            "global_report_headline_template",
            locale=doc_lang,
            client_name=client_name,
        )

    if intel_narrative:
        payload["executive_summary"]["narrative"] = intel_narrative

    payload["board_memo"] = _build_board_memo(
        towers_data, blueprint_files, client_name, client_dir=client_dir, doc_lang=doc_lang
    )
    payload["cross_tower_nexus"] = _build_cross_tower_nexus(
        towers_data, doc_lang=doc_lang
    )
    payload["executive_callouts"] = _build_executive_callouts(
        client_name, towers_data, client_dir=client_dir, doc_lang=doc_lang
    )

    return payload


def main(argv: list[str] | None = None) -> None:
    """Parses command-line arguments to build and save a global report payload.

    This function serves as the main entry point for the script. It orchestrates
    the process by parsing command-line arguments for a client directory, client
    name, and an output file path. It then invokes `build_global_payload` to
    construct the report data and serializes the resulting payload to a
    JSON file at the specified output path.

    Args:
        argv: An optional list of string arguments, defaulting to `sys.argv`.
            The list is expected to contain the script name followed by the
            client directory path, client name, and the output file path.

    Raises:
        SystemExit: If fewer than four command-line arguments are provided.
        IOError: If an error occurs while writing the payload to the output file
            (e.g., permission denied, non-existent parent directory).
        TypeError: If the payload returned by `build_global_payload` contains
            objects that cannot be serialized to JSON.
    """
    raw_args = list(argv if argv is not None else sys.argv)
    if len(raw_args) < 4:
        sys.exit(1)
    client_dir = Path(raw_args[1])
    client_name = raw_args[2]
    doc_lang = raw_args[4].lower() if len(raw_args) > 4 else None
    payload = build_global_payload(client_dir, client_name, doc_lang=doc_lang)
    if payload:
        out_file = Path(raw_args[3])
        out_file.parent.mkdir(parents=True, exist_ok=True)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=str(out_file.parent), prefix="tmp_global_payload_", suffix=".json"
        )
        fd_closed = False
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                fd_closed = True
                json.dump(payload, f, ensure_ascii=False, indent=2)
                f.write("\n")
            os.replace(temp_path, str(out_file))
        except Exception:
            if not fd_closed:
                try:
                    os.close(temp_fd)
                except OSError:
                    pass
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except OSError:
                pass
            raise
        logger.info("Dynamic payload generated successfully.")


if __name__ == "__main__":
    main()
