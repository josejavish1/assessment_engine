"""In-Memory Functional Core for AS-IS Deliverable Compilation (RFC-025 / SSOT).

Extracts and structures maturity metrics, FAIR risk scenarios, and narrative sections
directly from in-memory JSON or Pydantic payloads, eliminating intermediate disk I/O.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from assessment_engine.domain.maturity_band import (
    ANNEX_MATURITY_BANDS,
    resolve_maturity_band,
)
from assessment_engine.domain.taxonomy_resolver import (
    extract_pillar_identifiers,
    get_taxonomy_resolver,
)
from assessment_engine.domain.services.dynamic_custody_resolver import DynamicCustodyResolver
from assessment_engine.infrastructure.localization import (
    format_currency,
    format_number,
    t,
)

logger = logging.getLogger(__name__)


def derive_in_memory_fair_risks(
    b_data: dict[str, Any],
    doc_lang: str,
    currency: str,
    rate_mult: float = 1.0,
    active_towers_scope: set[str] | list[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """Extract and calibrate FAIR risk scenarios directly from in-memory payload.

    Applies DynamicCustodyResolver to prevent actuarial blind spots in partial-scope assessments.

    Returns:
        Tuple of (flat_risks_list, risks_by_pillar_dict).
    """
    resolver = get_taxonomy_resolver()
    risks_data_list: list[dict[str, Any]] = []
    risks_by_pillar: dict[str, list[dict[str, Any]]] = {}

    current_tower_id = str(b_data.get("tower_id") or b_data.get("document_meta", {}).get("tower_id") or "T1").upper()
    norm_scope = {str(t_id).strip().upper() for t_id in active_towers_scope} if active_towers_scope else None
    custody_resolver = DynamicCustodyResolver(
        active_towers_scope=norm_scope,
        localizer=lambda key, **kwargs: t(key, locale=doc_lang, **kwargs),
    )

    r_counter = 1
    for pillar in b_data.get("pillars_analysis", []):
        p_id, raw_pname = extract_pillar_identifiers(pillar)
        pillar_name = resolver.resolve_pillar_by_any_reference(
            p_id or raw_pname,
            default=(raw_pname or p_id or "Pillar"),
            locale=doc_lang,
            tower_id=current_tower_id,
        )

        for hc in pillar.get("health_check_asis", []):
            finding_text = str(hc.get("finding") or hc.get("risk_observed") or "").strip()
            business_risk = str(hc.get("business_risk") or hc.get("impact") or "").strip()
            if not finding_text and not business_risk:
                continue

            # Apply dynamic custody resolution (RFC 057)
            resolved_list = custody_resolver.resolve_portfolio([hc], current_tower_id=current_tower_id)
            eff_hc = resolved_list[0] if resolved_list else hc

            raw_cap = str(eff_hc.get("target_state") or eff_hc.get("capability") or "General Capability")
            capability = resolver.resolve_capability_name(raw_cap, default=raw_cap, locale=doc_lang)

            tef_val = float(eff_hc.get("threat_event_frequency") or eff_hc.get("tef") or 3.0)
            lm_val = float(eff_hc.get("loss_magnitude") or eff_hc.get("lm") or 3.0)
            if eff_hc.get("fair_ale_score") is not None:
                raw_ale = float(eff_hc["fair_ale_score"])
            elif eff_hc.get("ale") is not None:
                raw_ale = float(eff_hc["ale"])
            else:
                raw_ale = float(tef_val * lm_val * 1000.0)

            if eff_hc.get("fair_p90_score") is not None:
                raw_p90 = float(eff_hc["fair_p90_score"])
            else:
                raw_p90 = float(raw_ale * 2.5)

            ownership = str(eff_hc.get("ownership_type") or "PRIMARY_CUSTODIAN").strip().upper()
            is_tangential = (ownership == "TANGENTIAL_CONTRIBUTOR")

            intrinsic_ale = raw_ale * rate_mult
            intrinsic_p90 = raw_p90 * rate_mult

            # Calibrate actuarial LEF and SLE (RFC 055)
            if tef_val >= 1.0:
                calc_lef = min(0.50, max(0.08, tef_val * 0.09))
            else:
                calc_lef = max(0.05, tef_val)
            calc_sle = intrinsic_ale / calc_lef if (intrinsic_ale > 0.0 and calc_lef > 0.0) else (lm_val * 5000.0)

            # Enforce zero financial double counting in ledger totals for tangential contributors:
            calibrated_ale = 0.0 if is_tangential else intrinsic_ale
            calibrated_p90 = 0.0 if is_tangential else intrinsic_p90

            risk_item: dict[str, Any] = {
                "id": eff_hc.get("id", f"RVS{r_counter:02d}"),
                "node_id": eff_hc.get("node_id", f"NODE-{r_counter:03d}"),
                "pillar": pillar_name,
                "pillar_id": p_id,
                "capability": capability,
                "finding": finding_text,
                "business_risk": business_risk,
                "tef": tef_val,
                "lm": lm_val,
                "lef": round(calc_lef, 4),
                "sle": round(calc_sle, 2),
                "ale": calibrated_ale,
                "p90": calibrated_p90,
                "intrinsic_ale": intrinsic_ale,
                "intrinsic_p90": intrinsic_p90,
                "ownership_type": ownership,
                "primary_risk_ref": (str(eff_hc.get("primary_risk_ref") or "").strip() or None) if is_tangential else None,
                "contributing_towers": eff_hc.get("contributing_towers", []) if not is_tangential else [],
                "evidence": eff_hc.get("evidence", ""),
                "mitigation_directive": eff_hc.get("mitigation_directive", ""),
                "initiating_threat": eff_hc.get("initiating_threat", ""),
                "control_vulnerability": eff_hc.get("control_vulnerability", ""),
                "primary_impact": eff_hc.get("primary_impact", ""),
                "scope_note": eff_hc.get("scope_note", ""),
                "custody_resolution_metadata": eff_hc.get("custody_resolution_metadata", {}),
                "ale_str": format_currency(
                    calibrated_ale,
                    currency_symbol=currency,
                    locale=doc_lang,
                    decimals=0,
                ),
                "p90_str": format_currency(
                    calibrated_p90,
                    currency_symbol=currency,
                    locale=doc_lang,
                    decimals=0,
                ),
            }
            risks_data_list.append(risk_item)
            risks_by_pillar.setdefault(pillar_name, []).append(risk_item)
            r_counter += 1

    return risks_data_list, risks_by_pillar


def derive_in_memory_maturity_matrix(
    b_data: dict[str, Any],
    doc_lang: str,
) -> list[dict[str, Any]]:
    """Extract and format maturity assessment matrix rows directly from in-memory payload."""
    resolver = get_taxonomy_resolver()
    rows: list[dict[str, Any]] = []
    current_tower_id = str(b_data.get("tower_id") or b_data.get("document_meta", {}).get("tower_id") or "").upper()

    for pillar in b_data.get("pillars_analysis", []):
        p_id, raw_pname = extract_pillar_identifiers(pillar)
        pillar_name = resolver.resolve_pillar_by_any_reference(
            p_id or raw_pname,
            default=(raw_pname or p_id or "Pillar"),
            locale=doc_lang,
            tower_id=current_tower_id,
        )

        exact_score = float(pillar.get("score") or 3.0)
        band_info = resolve_maturity_band(exact_score, ANNEX_MATURITY_BANDS, locale=doc_lang)
        band_label = band_info.get("label", "Defined")

        # Extract score-conditioned justification block
        findings = pillar.get("health_check_asis", [])
        low_maturity_threshold = 2.2

        if exact_score < low_maturity_threshold:
            lbl_pos = t("calib_label_observed_state", locale=doc_lang)
            lbl_neg = t("calib_label_critical_gap", locale=doc_lang)
        else:
            lbl_pos = t("calib_label_operational_strength", locale=doc_lang)
            lbl_neg = t("calib_label_operational_gap", locale=doc_lang)

        asis_desc = (pillar.get("asis_architecture_description") or "").strip()
        if "." in asis_desc:
            clean_state = asis_desc.split(".")[0].strip() + "."
        else:
            clean_state = asis_desc

        if findings:
            top_f = findings[0]
            f_text = (top_f.get("finding") or top_f.get("risk_observed") or "").strip()
            clean_f = re.split(r"(?<!\d)[\.。\u3002](?!\d)\s*", f_text)[0].strip()
            if clean_state:
                justification = f"• **{lbl_pos}:** {clean_state}\n\n• **{lbl_neg}:** {clean_f.rstrip('.')}."
            else:
                justification = f"• **{lbl_neg}:** {clean_f.rstrip('.')}."
        else:
            justification = f"• **{lbl_pos}:** {clean_state}" if clean_state else t("default_evaluated_assets", locale=doc_lang)

        rows.append(
            {
                "pillar_id": p_id,
                "pillar_name": pillar_name,
                "score": exact_score,
                "score_formatted": format_number(exact_score, locale=doc_lang, decimals=1),
                "band_label": band_label,
                "justification": justification,
            }
        )

    return rows
