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
from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
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
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """Extract and calibrate FAIR risk scenarios directly from in-memory payload.

    Returns:
        Tuple of (flat_risks_list, risks_by_pillar_dict).
    """
    resolver = get_taxonomy_resolver()
    risks_data_list: list[dict[str, Any]] = []
    risks_by_pillar: dict[str, list[dict[str, Any]]] = {}

    r_counter = 1
    for pillar in b_data.get("pillars_analysis", []):
        raw_pname = pillar.get("pillar_name") or pillar.get("pilar_name") or "Pillar"
        p_id = pillar.get("pillar_id") or pillar.get("pilar_id") or raw_pname
        pillar_name = resolver.resolve_pillar_by_any_reference(
            p_id, default=raw_pname, locale=doc_lang
        )

        for hc in pillar.get("health_check_asis", []):
            finding_text = str(hc.get("finding") or hc.get("risk_observed") or "").strip()
            business_risk = str(hc.get("business_risk") or hc.get("impact") or "").strip()
            if not finding_text and not business_risk:
                continue

            raw_cap = str(hc.get("target_state") or hc.get("capability") or "General Capability")
            capability = resolver.resolve_capability_name(raw_cap, default=raw_cap, locale=doc_lang)

            tef_val = float(hc.get("threat_event_frequency") or 3.0)
            lm_val = float(hc.get("loss_magnitude") or 3.0)
            raw_ale = float(hc.get("fair_ale_score") or (tef_val * lm_val * 1000.0))
            raw_p90 = float(hc.get("fair_p90_score") or (raw_ale * 2.5))

            calibrated_ale = raw_ale * rate_mult
            calibrated_p90 = raw_p90 * rate_mult

            risk_item: dict[str, Any] = {
                "id": f"RVS{r_counter:02d}",
                "node_id": hc.get("node_id", f"NODE-{r_counter:03d}"),
                "pillar": pillar_name,
                "pillar_id": p_id,
                "capability": capability,
                "finding": finding_text,
                "business_risk": business_risk,
                "tef": tef_val,
                "lm": lm_val,
                "ale": calibrated_ale,
                "p90": calibrated_p90,
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

    for pillar in b_data.get("pillars_analysis", []):
        raw_pname = pillar.get("pillar_name") or pillar.get("pilar_name") or "Pillar"
        p_id = pillar.get("pillar_id") or pillar.get("pilar_id") or raw_pname
        pillar_name = resolver.resolve_pillar_by_any_reference(
            p_id, default=raw_pname, locale=doc_lang
        )

        exact_score = float(pillar.get("score") or 3.0)
        band_info = resolve_maturity_band(exact_score, ANNEX_MATURITY_BANDS, locale=doc_lang)
        band_label = band_info.get("label", "Defined")

        # Extract or derive executive justification block
        findings = pillar.get("health_check_asis", [])
        if findings:
            top_f = findings[0]
            f_text = (top_f.get("finding") or top_f.get("risk_observed") or "").strip()
            r_text = (top_f.get("business_risk") or top_f.get("impact") or "").strip()
            clean_f = re.split(r"(?<!\d)[\.。\u3002](?!\d)\s*", f_text)[0].strip()
            clean_r = re.split(r"(?<!\d)[\.。\u3002](?!\d)\s*", r_text)[0].strip()
            clean_r_low = clean_r[:1].lower() + clean_r[1:] if clean_r else ""
            justification = t(
                "exec_priority_domain_synthesis",
                locale=doc_lang,
                finding=clean_f.rstrip("."),
                risk=clean_r_low.rstrip("."),
            )
        else:
            justification = pillar.get("asis_architecture_description", t("default_evaluated_assets", locale=doc_lang))

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
