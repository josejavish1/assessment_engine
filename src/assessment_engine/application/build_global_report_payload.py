"""Constructs the global report payload, encapsulating the primary business logic for the Assessment Engine's reporting pipeline."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.client_intelligence import (
    build_client_context_packet,
    load_client_intelligence,
)
from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.global_maturity_policy import (
    average_pillar_score,
    average_pillar_target,
    band_for_score,
    status_color_for_score,
)
from assessment_engine.infrastructure.localization import t
from assessment_engine.infrastructure.text_utils import slugify

logger = logging.getLogger(__name__)

def get_tower_name(tid: str, doc_lang: str) -> str:
    """Resolve canonical tower name dynamically through localization."""
    from assessment_engine.infrastructure.localization import t

    return t(
        f"tower_{tid.lower()}_name",
        locale=doc_lang,
    )


def load_json(path: Path) -> dict[str, Any] | None:
    """Safely loads and parses a JSON file from a specified path.

    This function is designed to be resilient to I/O or parsing errors. It returns
    `None` if the file does not exist, cannot be read, or contains malformed JSON,
    silencing all exceptions during the process. The file is read using the
    'utf-8-sig' encoding to correctly handle an optional leading byte order mark (BOM).

    Args:
        path: The `pathlib.Path` object pointing to the target JSON file.

    Returns:
        The deserialized JSON data as a `dict[str, Any]`, or `None` if an
        error occurs during file access or parsing.
    """
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _build_source_version(blueprint_towers: list[str]) -> str:
    blueprint_part = ",".join(blueprint_towers) or "none"
    return f"blueprint-only;blueprints={blueprint_part}"


def _aggregate_tower_blueprints(
    blueprint_files: list[Path],
    doc_lang: str,
) -> tuple[list[dict], list[dict], list[dict], list[str], list[str], list[str]]:
    """Parse and aggregate tower blueprint files into consolidated metrics and initiative lists."""
    from assessment_engine.infrastructure.localization import t

    towers_data: list[dict] = []
    strategic_risks: list[dict] = []
    all_initiatives: list[dict] = []
    all_principles: list[str] = []
    all_implications: list[str] = []
    blueprint_towers: list[str] = []

    for bp in sorted(
        blueprint_files,
        key=lambda x: int(x.parent.name[1:]) if x.parent.name[1:].isdigit() else 99,
    ):
        data = load_json(bp)
        if not data:
            continue

        tid = data.get("document_meta", {}).get("tower_code", bp.parent.name).upper()
        blueprint_towers.append(tid)
        doc_tname = data.get("document_meta", {}).get("tower_name")
        tname = doc_tname if doc_tname else get_tower_name(tid, doc_lang=doc_lang)

        pillars_analysis = data.get("pillars_analysis", [])
        avg_score = average_pillar_score(pillars_analysis, default=0.0)
        target_score = average_pillar_target(pillars_analysis, default=4.0)

        towers_data.append(
            {
                "id": tid,
                "name": tname,
                "score": f"{avg_score:.1f}",
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
        for pilar in data.get("pillars_analysis", []):
            for hc in pilar.get("health_check_asis", []):
                vuln = hc.get("vulnerability_level", 3)
                impact_label = (
                    t("critical_severity_lbl", locale=doc_lang)
                    if vuln >= 5
                    else (
                        t("high_severity_lbl", locale=doc_lang)
                        if vuln >= 4
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
            for proj in pilar.get("projects_todo", []):
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
    """Declarative cross-tower nexus dependency rules resolved through i18n."""
    from assessment_engine.infrastructure.localization import t

    return [
        {
            "source_tower": "T6: Security & Identity",
            "target_tower": "T2: Compute & Cloud",
            "dependency_type": t("nexus_dep_type_critical", locale=doc_lang),
            "architectural_rationale": t("nexus_rule_1_rationale", locale=doc_lang),
            "delay_impact": t("nexus_rule_1_delay", locale=doc_lang),
        },
        {
            "source_tower": "T5: Resilience & DR",
            "target_tower": "T4: Storage & Data",
            "dependency_type": t("nexus_dep_type_tech", locale=doc_lang),
            "architectural_rationale": t("nexus_rule_2_rationale", locale=doc_lang),
            "delay_impact": t("nexus_rule_2_delay", locale=doc_lang),
        },
        {
            "source_tower": "T3: Network & Connectivity",
            "target_tower": "T1: Physical Infrastructure",
            "dependency_type": t("nexus_dep_type_resilience", locale=doc_lang),
            "architectural_rationale": t("nexus_rule_3_rationale", locale=doc_lang),
            "delay_impact": t("nexus_rule_3_delay", locale=doc_lang),
        },
        {
            "source_tower": "T6: Security & Identity",
            "target_tower": "T7: Digital Operations",
            "dependency_type": t("nexus_dep_type_ops", locale=doc_lang),
            "architectural_rationale": t("nexus_rule_4_rationale", locale=doc_lang),
            "delay_impact": t("nexus_rule_4_delay", locale=doc_lang),
        },
        {
            "source_tower": "T8: Strategy & FinOps",
            "target_tower": "T2: Compute & Cloud",
            "dependency_type": t("nexus_dep_type_finops", locale=doc_lang),
            "architectural_rationale": t("nexus_rule_5_rationale", locale=doc_lang),
            "delay_impact": t("nexus_rule_5_delay", locale=doc_lang),
        },
    ]


def _parse_currency_amount_to_float(val_str: Any) -> float:
    """Robustly parses localized currency strings (e.g. '23.963,64 €', '$1,200.50') into float."""
    if not val_str:
        return 0.0
    s = (
        str(val_str)
        .replace("€", "")
        .replace("$", "")
        .replace("£", "")
        .replace("R$", "")
        .replace("CHF", "")
        .strip()
    )
    if "," in s and "." in s:
        if s.find(",") < s.rfind("."):
            # US format: 19,200.00
            s = s.replace(",", "")
        else:
            # EU format: 19.200,00
            s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." not in s:
        s = s.replace(",", ".")
    elif "." in s and "," not in s:
        # It might be 12.500 (12500) or 12.50 (12.5)
        if len(s) - s.rfind(".") == 4:
            s = s.replace(".", "")

    import re
    # We remove all periods except the last one if it's a decimal
    m = re.search(r"[-+]?\d*\.?\d+", s.replace(" ", ""))
    if m:
        try:
            return float(m.group())
        except ValueError:
            return 0.0
    return 0.0


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
    from assessment_engine.infrastructure.localization import (
        format_currency,
        t,
    )

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

    finops_waste_ratio = float(strat_metrics.get("finops_cash_waste_ratio", 0.00135))
    baseline_downtime_hours = float(strat_metrics.get("baseline_annual_downtime_hours", 27.0))
    tail_risk_min_ratio = float(strat_metrics.get("tail_risk_p90_ratio_min", 0.45))
    tail_risk_max_ratio = float(strat_metrics.get("tail_risk_p90_ratio_max", 0.65))

    currency_code = "EUR"
    currency_symbol = "€"
    annual_revenue = float(strat_metrics.get("default_annual_revenue", 100000000.0))
    hourly_downtime_cost = float(strat_metrics.get("default_hourly_downtime_cost", 5000.0))
    reg_max_fine = float(strat_metrics.get("default_reg_max_fine", 2000000.0))
    compliance_framework = "Normativa Aplicable"

    if client_dir:
        for prof_path in client_dir.glob("T*/custom_risk_profile.json"):
            try:
                prof_data = json.loads(prof_path.read_text(encoding="utf-8-sig"))
                currency_code = prof_data.get("currency_code", currency_code)
                currency_symbol = prof_data.get("currency_symbol", currency_symbol)
                annual_revenue = float(prof_data.get("annual_revenue_eur", annual_revenue))
                hourly_downtime_cost = float(prof_data.get("hourly_downtime_cost_eur", hourly_downtime_cost))
                reg_max_fine = float(prof_data.get("reg_max_fine_eur", reg_max_fine))
                compliance_framework = prof_data.get("compliance_framework", compliance_framework)
                break
            except (OSError, ValueError, KeyError) as ex:
                logger.debug("[GlobalPayload] Risk profile loading fallback: %s", ex)

        intel_path = client_dir / "client_intelligence.json"
        if intel_path.exists():
            try:
                intel_data = json.loads(intel_path.read_text(encoding="utf-8-sig"))
                framework = (
                    intel_data.get("compliance", {}).get("primary_framework")
                    or intel_data.get("primary_framework")
                )
                if framework:
                    compliance_framework = framework
            except (OSError, ValueError, KeyError) as ex:
                logger.debug("[GlobalPayload] Intelligence framework loading fallback: %s", ex)

    total_opex_inv = 0.0
    total_capex_inv = 0.0
    year_1_opex = 0.0
    total_fair_ale = 0.0

    for bp in blueprint_files:
        try:
            bp_data = json.loads(bp.read_text(encoding="utf-8-sig"))
            total_fair_ale += float(bp_data.get("total_fair_ale", 0.0))
            for pil in bp_data.get("pillars_analysis", []):
                for pr in pil.get("projects_todo", []):
                    op_val = _parse_currency_amount_to_float(pr.get("opex_estimate"))
                    total_opex_inv += op_val
                    if any(h in str(pr.get("duration", "")) for h in ["H1", "H2", "1", "2"]):
                        year_1_opex += op_val
                    cap_val = _parse_currency_amount_to_float(pr.get("capex_estimate"))
                    total_capex_inv += cap_val
        except Exception as ex:
            logger.debug(f"[Financial Stratification] Error parsing blueprint: {ex}")

    if year_1_opex <= 0.0:
        year_1_opex = total_opex_inv * 0.40 if total_opex_inv > 0 else 250000.0

    # Layer 1: Dynamic Cash Inefficiency (Scaled proportionally to revenue benchmark)
    layer_1_amount = round(annual_revenue * finops_waste_ratio, 0)
    layer_1_display = format_currency(layer_1_amount, currency_code=currency_code, locale=doc_lang, decimals=0)

    # Layer 2: Dynamic Operational Friction (Calibrated hourly downtime x baseline downtime hours)
    layer_2_amount = round(hourly_downtime_cost * baseline_downtime_hours, 0)
    layer_2_display = format_currency(layer_2_amount, currency_code=currency_code, locale=doc_lang, decimals=0)

    # Layer 3: Dynamic Actuarial Tail Risk (P90 FAIR value: calibrated ratio of total FAIR exposure)
    if total_fair_ale <= 0.0:
        total_fair_ale = annual_revenue * 0.010
    layer_3_min = round(total_fair_ale * tail_risk_min_ratio, 0)
    layer_3_max = round(total_fair_ale * tail_risk_max_ratio, 0)
    l3_min_fmt = format_currency(layer_3_min, currency_code=currency_code, locale=doc_lang, decimals=0)
    l3_max_fmt = format_currency(layer_3_max, currency_code=currency_code, locale=doc_lang, decimals=0)
    layer_3_display = f"{l3_min_fmt} - {l3_max_fmt}"

    # Payback & ROI (TCO = OpEx + CapEx)
    total_inv = year_1_opex + total_capex_inv
    payback_months = (
        round((total_inv / layer_1_amount) * 12, 1) if layer_1_amount > 0 else 6.0
    )
    roi_ratio = round(layer_1_amount / total_inv, 1) if total_inv > 0 else 1.0

    hourly_cost_fmt = format_currency(hourly_downtime_cost, currency_code=currency_code, locale=doc_lang, decimals=0)
    reg_fine_fmt = format_currency(reg_max_fine, currency_code=currency_code, locale=doc_lang, decimals=0)
    total_opex_fmt = format_currency(year_1_opex, currency_code=currency_code, locale=doc_lang, decimals=0)
    total_capex_fmt = format_currency(total_capex_inv, currency_code=currency_code, locale=doc_lang, decimals=0)

    placeholders = {
        "currency": currency_symbol,
        "hourly_cost": hourly_cost_fmt,
        "compliance_framework": compliance_framework,
        "reg_max_fine": reg_fine_fmt,
        "total_opex": total_opex_fmt,
        "total_capex": total_capex_fmt,
        "year_1_savings": layer_1_display,
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
            "payback_period": f"~{payback_months:.0f} meses",
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
    from assessment_engine.infrastructure.localization import format_currency, t

    currency_code = "EUR"
    currency_symbol = "€"
    if client_dir:
        for prof_path in client_dir.glob("T*/custom_risk_profile.json"):
            try:
                prof_data = json.loads(prof_path.read_text(encoding="utf-8-sig"))
                currency_code = prof_data.get("currency_code", currency_code)
                currency_symbol = prof_data.get("currency_symbol", currency_symbol)
                break
            except (OSError, ValueError, KeyError) as ex:
                logger.debug("[GlobalPayload] Currency loading fallback: %s", ex)

    items = []
    total_holding_opex = 0.0
    total_holding_capex = 0.0

    for t_item in towers_data:
        tid = t_item.get("id", "")
        tname = t_item.get("name", "")
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
                        coi_text = fin_coi.get("coi_3y_ordinary") or fin_coi.get("annual_loss_exposure") or coi_text
                        inits = ax_data.get("sections", {}).get("todo", {}).get("priority_initiatives", [])
                        if inits and inits[0].get("initiative"):
                            top_project_name = inits[0].get("initiative")
                    except Exception as err:
                        logger.debug("Error leyendo anexo para coi_text: %s", err)
                try:
                    bp_data = json.loads(bp.read_text(encoding="utf-8-sig"))
                    for pil in bp_data.get("pillars_analysis", []):
                        for pr in pil.get("projects_todo", []):
                            if not top_project_name and pr.get("name"):
                                top_project_name = pr.get("name")
                            opex_tower += _parse_currency_amount_to_float(pr.get("opex_estimate"))
                            capex_tower += _parse_currency_amount_to_float(pr.get("capex_estimate"))
                except Exception as err:
                    logger.debug("Error leyendo blueprint para budget: %s", err)

        total_holding_opex += opex_tower
        total_holding_capex += capex_tower
        total_inv_tower = opex_tower + capex_tower

        fallback_budget_lbl = t("budget_subscription_fallback", locale=doc_lang)
        if total_inv_tower > 0:
            if capex_tower > 0:
                tot_fmt = format_currency(total_inv_tower, currency_code=currency_code, locale=doc_lang, decimals=0)
                cap_fmt = format_currency(capex_tower, currency_code=currency_code, locale=doc_lang, decimals=0)
                op_fmt = format_currency(opex_tower, currency_code=currency_code, locale=doc_lang, decimals=0)
                budget_display = t(
                    "budget_capex_opex_format",
                    locale=doc_lang,
                    total_inv=tot_fmt,
                    capex=cap_fmt,
                    opex=op_fmt,
                )
            else:
                op_fmt = format_currency(opex_tower, currency_code=currency_code, locale=doc_lang, decimals=0)
                budget_display = t(
                    "budget_pure_opex_format",
                    locale=doc_lang,
                    opex=op_fmt,
                )
        else:
            budget_display = fallback_budget_lbl

        if top_project_name:
            crit_dec = t(
                "decision_priority_project_template",
                locale=doc_lang,
                project_name=top_project_name,
                tower_name=tname,
            )
        else:
            default_dec = t("decision_default_template", locale=doc_lang, tower_name=tname)
            crit_dec = t(f"decision_{tid}", locale=doc_lang, default=default_dec)

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
    towers_data: list[dict], blueprint_files: list[Path], doc_lang: str
) -> dict[str, Any]:
    gen_tids = {t["id"].upper() for t in towers_data}
    all_rules = _get_cross_tower_nexus_rules(doc_lang=doc_lang)
    active_rules = []
    for r in all_rules:
        src_id = r["source_tower"].split(":")[0].strip().upper()
        tgt_id = r["target_tower"].split(":")[0].strip().upper()
        if src_id in gen_tids or tgt_id in gen_tids or len(gen_tids) >= 3:
            active_rules.append(r)

    from assessment_engine.infrastructure.localization import t

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
    from assessment_engine.infrastructure.localization import format_currency, t

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
    hourly_downtime_cost = float(strat_metrics.get("default_hourly_downtime_cost", 5000.0))
    reg_max_fine = float(strat_metrics.get("default_reg_max_fine", 2000000.0))
    industry_name = t("default_industry_name", locale=doc_lang)

    if client_dir:
        for prof_path in client_dir.glob("T*/custom_risk_profile.json"):
            try:
                prof_data = json.loads(prof_path.read_text(encoding="utf-8-sig"))
                currency_code = prof_data.get("currency_code", currency_code)
                currency_symbol = prof_data.get("currency_symbol", currency_symbol)
                hourly_downtime_cost = float(prof_data.get("hourly_downtime_cost_eur", hourly_downtime_cost))
                reg_max_fine = float(prof_data.get("reg_max_fine_eur", reg_max_fine))
                break
            except Exception as ex:
                logger.debug("Error leyendo custom_risk_profile: %s", ex)

        intel_path = client_dir / "client_intelligence.json"
        if intel_path.exists():
            try:
                intel_data = json.loads(intel_path.read_text(encoding="utf-8-sig"))
                ind = intel_data.get("profile", {}).get("industry") or intel_data.get("industry")
                if ind:
                    industry_name = ind
            except Exception as ex:
                logger.debug("Error leyendo client_intelligence industry: %s", ex)

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


def build_global_payload(client_dir: Path, client_name: str) -> dict[str, Any] | None:
    r"""{'docstring': "Aggregates client data into a consolidated global report payload.\n\n    This function orchestrates the construction of a comprehensive dictionary by\n    collating data from multiple sources within a client's directory. It parses\n    and merges tower-specific blueprint files (`T*/blueprint_*_payload.json`),\n    prioritizing data from higher-numbered towers. The aggregated data is then\n    enriched with contextual information from `client_intelligence.json` and a\n    dynamically generated strategic roadmap from an orchestration process.\n\n    The process involves calculating maturity scores, extracting strategic risks,\n    compiling initiatives, and resolving identifiers against an epistemic graph\n    to produce human-readable labels. The final output is a structured payload\n    intended for generating a global client report, with provisions for executive\n    summary content to be overridden by the client intelligence file.\n\n    Args:\n        client_dir: The filesystem path to the root directory for a specific\n            client. This directory is expected to contain tower-specific\n            subdirectories (e.g., 'T1', 'T2') which hold blueprint JSON files.\n        client_name: The canonical name of the client. This identifier is used\n            for lookups within the epistemic graph and is embedded in the final\n            payload metadata.\n\n    Returns:\n        A dictionary representing the complete global report payload if successful.\n        Returns None if no blueprint files are found in the specified `client_dir`\n        or if the discovered files yield no processable data.\n\n    Raises:\n        FileNotFoundError: If the `client_dir` path does not exist.\n        json.JSONDecodeError: If a blueprint or client intelligence file contains\n            malformed JSON.\n        KeyError: If a required key is missing from the input JSON data\n            structures, particularly in sections not accessed with a `.get()`\n            fallback.\n        TypeError: If data in an input file has an unexpected type, causing a\n            failure in downstream operations such as numerical conversions."}."""
    # The loading process prioritizes canonical Blueprints (T1 to T10) to ensure exact adherence to the 10 core domains.
    blueprint_files = [
        bp
        for bp in client_dir.glob("T*/blueprint_*_payload.json")
        if re.match(r"^T(10|[1-9])$", bp.parent.name)
    ]

    if not blueprint_files:
        logger.warning(f"No tower payload files found in {client_dir}")
        return None

    intelligence_dossier = {}
    resolved_lang = os.environ.get("ASSESSMENT_DOC_LANG") or os.environ.get("ASSESSMENT_LANGUAGE")
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
        except Exception:
            intelligence_dossier = {}

    from assessment_engine.infrastructure.localization import resolve_base_locale

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

        intrinsic_audited = {item["id"]: float(item["score"]) for item in towers_data}
        # Actuarial model: Impute empirical mean of audited towers to prevent Bayesian dilution bias
        avg_audited_score = (
            sum(intrinsic_audited.values()) / len(intrinsic_audited)
            if intrinsic_audited
            else 3.0
        )
        for t_id in graph_service.towers:
            if t_id not in intrinsic_audited:
                intrinsic_audited[t_id] = avg_audited_score

        propagated_audited = graph_service.propagate_risk(intrinsic_audited)

        # Calculate actual audited risk volatilities for PageRank Centrality
        audited_risks = {
            t_id: max(0.01, 1.0 - (propagated_audited.get(t_id, 4.0) - 3.0) / 2.0)
            for t_id in graph_service.towers
        }
        audited_centrality = graph_service.calculate_risk_centrality(audited_risks)
        empirical_spof = max(audited_centrality, key=audited_centrality.get)

        # Update towers_data with propagated (effective) maturity scores
        for item in towers_data:
            tid = item["id"].upper()
            eff_score = propagated_audited.get(tid, float(item["score"]))
            item["effective_score"] = f"{eff_score:.1f}"
            item["effective_band"] = band_for_score(eff_score, doc_lang=doc_lang)
            item["effective_status_color"] = status_color_for_score(eff_score)

        avg_effective_score = round(
            sum(float(t["effective_score"]) for t in towers_data) / len(towers_data), 1
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
    from assessment_engine.application.run_strategic_orchestrator import (
        run_strategic_orchestration,
    )

    strategic_result = run_strategic_orchestration(client_name)
    strategic_roadmap = strategic_result.get("roadmap", [])

    # Resolves UUIDs against the graph's data dictionary to substitute them with human-readable labels, ensuring the final report is intelligible to end-users.
    graph = EpistemicGraph(client_id=slugify(client_name))
    truth = graph.resolve_truth()

    def get_label(node_id: str) -> str:
        """Resolve a node ID to its canonical display label.

        Searches the global `truth` data structure for a label associated with the
        provided `node_id`. The resolution logic attempts to find a label value from
        predicates in a specific order of precedence:
        1. 'PROPOSES_INITIATIVE'
        2. 'IDENTIFIED_AS_GAP'

        If no label is found under these predicates, the function returns the
        original `node_id` as a fallback identifier.

        Args:
            node_id: The unique identifier for the node to be resolved.

        Returns:
            The corresponding display label as a string, or the original `node_id`
            if a label cannot be resolved.
        """
        predicates = truth.get(node_id, {})
        return (
            predicates.get("PROPOSES_INITIATIVE", {}).get("value")
            or predicates.get("IDENTIFIED_AS_GAP", {}).get("value")
            or node_id
        )

    final_roadmap_programs = []
    final_horizons = {
        "quick_wins_0_3_months": [],
        "year_1_3_12_months": [],
        "year_2_12_24_months": [],
        "year_3_24_36_months": [],
    }

    seen_labels = set()
    for wave in strategic_roadmap:
        wave_label = wave["wave"]
        for node_id in wave["projects"]:
            human_name = get_label(node_id)

            # Executes a case-insensitive deduplication process to maintain data integrity by canonicalizing entries that differ only in character casing.
            norm_label = human_name.strip().upper()
            if norm_label in seen_labels:
                continue
            seen_labels.add(norm_label)

            # Truncates description fields that are repurposed as titles to a maximum length, preventing text overflow and maintaining visual layout consistency in the generated report.
            if len(human_name) > 120:
                human_name = human_name[:117] + "..."

            init_def = {
                "program": wave_label,
                "title": human_name,
                "business_case": t("quick_win_objective_default", locale=doc_lang),
                "start_month": 0
                if "0" in wave_label
                else 6
                if "1" in wave_label
                else 12,
                "duration_months": 6,
            }
            if "0" in wave_label:
                final_horizons["quick_wins_0_3_months"].append(init_def)
            elif "1" in wave_label:
                final_horizons["year_1_3_12_months"].append(init_def)
            else:
                final_horizons["year_2_12_24_months"].append(init_def)

    # Aggregates a distinct set of all programs to ensure data integrity and prevent redundant entries in subsequent processing stages.
    unique_waves = list(set(w["wave"] for w in strategic_roadmap))
    for uw in unique_waves:
        final_roadmap_programs.append(
            {"name": uw, "description": f"{uw} execution phase of the strategic roadmap."}
        )

    avg_score = round(sum(float(t["score"]) for t in towers_data) / len(towers_data), 1)

    # Performs deduplication on the aggregated list and truncates it to a predefined maximum length, ensuring the final result set is both unique and concise.
    unique_principles = list(dict.fromkeys(all_principles))
    unique_implications = list(dict.fromkeys(all_implications))

    now = datetime.now()
    spanish_months = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
    }
    dynamic_date_str = f"{now.day} de {spanish_months.get(now.month, 'Enero')} de {now.year}"

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
            "version": "v6.0 - Sovereign DTO",
            "language": doc_lang,
        },
        "executive_summary": {
            "headline": t(
                "maturity_pulse_headline_template",
                locale=doc_lang,
                avg_score=f"{avg_score:.1f}",
            ),
            "narrative": "PENDING STRATEGIC REFINEMENT",
            "key_business_impacts": [
                t("impact_time_to_market", locale=doc_lang),
                t("impact_operational_risk", locale=doc_lang),
                t("impact_cost_optimization", locale=doc_lang),
            ],
            "top_strategic_risks": strategic_risks[:5],
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
            "value_targets": unique_implications[:5],
        },
        "burning_platform": [
            {
                "theme": risk.get("title", t("risk_theme_default", locale=doc_lang)),
                "business_risk": risk.get("business_impact", t("risk_business_impact_default", locale=doc_lang)),
                "root_causes": [
                    risk.get("description", t("risk_root_cause_default", locale=doc_lang))
                ],
            }
            for risk in strategic_risks[:5]
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
                for p in unique_principles[:5]
            ],
            "strategic_pillars": [
                {
                    "pillar": p,
                    "description": t("strategic_pillar_desc_default", locale=doc_lang),
                }
                for p in unique_implications[:5]
            ],
        },
        "execution_roadmap": {
            "programs": [],  #
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
        prog_name = t(
            "program_modernization_template",
            locale=doc_lang,
            tower_name=t_item["name"],
        )
        payload["execution_roadmap"]["programs"].append(
            {
                "id": t_item["id"],
                "name": prog_name,
                "description": t_item["executive_message"],
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

    doc_lang: str
    if intelligence_path.exists():
        try:
            raw_int = json.loads(intelligence_path.read_text(encoding="utf-8-sig"))
            doc_lang = (
                raw_int.get("language")
                or raw_int.get("locale")
                or raw_int.get("doc_lang")
                or "en"
            ).lower()
        except (OSError, ValueError, KeyError, AttributeError) as ex:
            logger.debug("[Fallback] Handled exception: %s", ex)

    payload["board_memo"] = _build_board_memo(
        towers_data, blueprint_files, client_name, client_dir=client_dir, doc_lang=doc_lang
    )
    payload["cross_tower_nexus"] = _build_cross_tower_nexus(
        towers_data, blueprint_files, doc_lang=doc_lang
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
        Path(raw_args[3]).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        logger.info("Dynamic payload generated successfully.")


if __name__ == "__main__":
    main()
