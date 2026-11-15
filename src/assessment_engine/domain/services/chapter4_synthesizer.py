"""Universal Upstream Domain Synthesizer for Chapter 4 Executive Dossiers.

Adheres strictly to Tier-1 Architectural Standards:
1. Pure Technical English in all source code, docstrings, variable names, and exceptions.
2. The Three Golden Principles:
   - Aseptic, respectful, non-accusatory engineering tone.
   - Strict AS-IS diagnostic boundary (no future TO-BE project pricing or premature paybacks).
   - Pure Tier 1 (Critical) & Tier 2 (Structural) risks (zero Tier 3 trivial noise).
3. Universal Multi-Tenant Scalability:
   - Dynamic mathematical risk prioritization: (5.00 - Pillar_Score) * Asset_Criticality.
   - Multilingual taxonomy resolution via TaxonomyResolver.
   - Econometric Disruption Resolution: Dynamically derived from enterprise annual revenue and operating intensity.
   - Clean Architecture Purity: Completely decoupled from infrastructure imports; receives rate catalog via port.
   - Dynamic logarithmic magnitude scaling (scales from EUR/USD to JPY and mid-market to Global 500).
4. Produces immutable, strongly-typed Chapter4SynthesisPayload models (Single Source of Truth).
"""

from __future__ import annotations

import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from assessment_engine.domain.actuarial.rounding import (
    allocate_subadditive_ale_to_cards,
    round_to_actuarial_significance,
)
from assessment_engine.domain.actuarial.schemas import (
    Chapter4SynthesisPayload,
    ChronicOperationalDragBreakdown,
    CostOfInactionTotal,
    HeatmapCoordinate,
    MonetaryInterval,
    ProbabilisticOutageALEBreakdown,
    TechnicalRiskScenario,
    ThreeYearCompoundedTCO,
)

logger = logging.getLogger(__name__)

GLOBAL_BENCHMARK_RATE_CARD: Dict[str, Any] = {
    "country_name": "Global Benchmark",
    "currency_iso": "EUR",
    "systems_engineer_hourly_rate": 45.0,
    "senior_architect_hourly_rate": 70.0,
    "technician_hourly_rate": 35.0,
    "default_hourly_disruption_cost": 3000.0,
}


def round_to_order_of_magnitude(val: float, precision: int = 1) -> float:
    """Rounds a numeric value dynamically relative to its order of magnitude."""
    return float(round_to_actuarial_significance(val))


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely converts an arbitrary value to float without throwing ValueError or TypeError."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    try:
        clean = str(val).replace(",", ".").strip()
        return float(clean)
    except (ValueError, TypeError):
        return default


def _truncate_smart_words(title: str, max_chars: int = 38) -> str:
    """Truncates text at word boundary to avoid breaking LaTeX/Word cell geometry."""
    clean = title.strip()
    if len(clean) <= max_chars:
        return clean
    truncated = clean[:max_chars - 1]
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return f"{truncated}…"


class Chapter4Synthesizer:
    """Upstream domain service synthesizing Chapter 4 executive status quo anchors and strategic risk cards."""

    @classmethod
    def get_country_rate_card(
        cls,
        country_code: Optional[str] = None,
        rates_catalog: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Resolves authoritative country labor rates and disruption cost baselines."""
        raw_catalog = rates_catalog or {}
        rates = (
            raw_catalog.get("rates_by_country", raw_catalog)
            if isinstance(raw_catalog, dict)
            else {}
        )
        code = str(country_code or "").strip().upper()
        if code in rates:
            return rates[code]
        if "DEFAULT" in rates:
            return rates["DEFAULT"]
        return GLOBAL_BENCHMARK_RATE_CARD

    @classmethod
    def synthesize_payload(
        cls,
        blueprint_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        rates_catalog: Optional[Dict[str, Any]] = None,
    ) -> Chapter4SynthesisPayload:
        """Synthesizes the monistic Chapter4SynthesisPayload domain object adhering strictly

        to the Single Source of Truth invariants.
        """
        ctx = context or {}
        doc_meta = blueprint_data.get("document_meta") or {}
        tower_id = str(ctx.get("tower_id") or doc_meta.get("tower_id") or "T1").strip().upper()
        tower_name = str(ctx.get("tower_name") or doc_meta.get("tower_name") or "Infrastructure Domain").strip()
        enterprise_id = str(ctx.get("client_id") or doc_meta.get("client_id") or "ENTERPRISE").strip().upper()
        country_code = str(ctx.get("country_code") or doc_meta.get("country_code") or "DEFAULT").strip().upper()
        raw_currency = str(ctx.get("currency") or doc_meta.get("currency") or "EUR").strip().upper()
        curr_map = {"€": "EUR", "$": "USD", "£": "GBP", "¥": "JPY"}
        currency_iso = curr_map.get(raw_currency, raw_currency if len(raw_currency) == 3 and raw_currency.isalpha() else "EUR")
        target_locale = str(ctx.get("meta_lang") or doc_meta.get("language") or "en").strip().lower()

        effective_catalog = rates_catalog or ctx.get("rates_catalog") or blueprint_data.get("rates_catalog")
        rate_card = cls.get_country_rate_card(country_code, rates_catalog=effective_catalog)
        hourly_rate = float(rate_card.get("systems_engineer_hourly_rate", 45.0))

        # Enterprise Scale & Disruption Rate
        org_profile = blueprint_data.get("organization_profile") or {}
        annual_revenue = _safe_float(org_profile.get("annual_revenue"))
        if annual_revenue > 0:
            disruption_rate = float(round_to_actuarial_significance((annual_revenue / 8760.0) * 0.02))
        else:
            disruption_rate = float(rate_card.get("default_hourly_disruption_cost", 3000.0))

        # Collect raw findings and calculate domain maturity
        pillars = blueprint_data.get("pillars_analysis") or []
        findings_pool: List[Dict[str, Any]] = []
        pillar_scores: List[float] = []

        for p in pillars:
            if isinstance(p, dict):
                p_name = str(p.get("pilar_name") or "Core Domain")
                p_score = _safe_float(p.get("pilar_score") or p.get("score"), default=2.5)
                pillar_scores.append(p_score)
                for hc in (p.get("health_check_asis") or []):
                    if isinstance(hc, dict):
                        hc_copy = dict(hc)
                        hc_copy["_pillar_name"] = p_name
                        hc_copy["_pillar_score"] = p_score
                        findings_pool.append(hc_copy)

        cmmi_maturity = round(sum(pillar_scores) / len(pillar_scores), 2) if pillar_scores else 2.5
        cmmi_maturity = max(1.0, min(5.0, cmmi_maturity))

        # Continuous Maturity Elasticity & Enterprise Scale Normalization
        # Lower maturity (CMMI < 2.0) -> high toil & high outage risk
        # Higher maturity (CMMI > 4.0) -> reduced toil, lower outage prob, high regulatory secondary loss
        headcount = _safe_float(org_profile.get("headcount") or org_profile.get("employee_count"), default=0.0)
        if headcount > 0.0:
            scale_factor = max(0.5, math.log10(max(10.0, headcount)) / 3.0)
        elif annual_revenue > 0.0:
            scale_factor = max(0.5, math.log10(max(10_000_000.0, annual_revenue)) / 9.0)
        else:
            scale_factor = 1.0

        toil_hours_base = 750.0 * scale_factor * (1.30 - 0.15 * (cmmi_maturity - 1.0))
        min_toil_hours = int(round(toil_hours_base * 0.9))
        max_toil_hours = int(round(toil_hours_base * 1.2))

        toil_min = round_to_actuarial_significance(min_toil_hours * hourly_rate)
        toil_max = round_to_actuarial_significance(max_toil_hours * hourly_rate)
        if toil_max <= toil_min:
            toil_max = toil_min + round_to_actuarial_significance(toil_min * 0.25)

        # Outage ALE Lever 2
        rto_val = _safe_float(blueprint_data.get("worst_crisis_rto_hours"), default=6.0)
        eff_rto = max(4.0, min(14.0, rto_val))
        worst_case_event_min = round_to_actuarial_significance((eff_rto - 1.0) * disruption_rate * 1.15)
        worst_case_event_max = round_to_actuarial_significance((eff_rto + 2.0) * disruption_rate * 1.30)
        if worst_case_event_max <= worst_case_event_min:
            worst_case_event_max = worst_case_event_min + round_to_actuarial_significance(worst_case_event_min * 0.35)

        # Annualized failure frequency (scaled by maturity: higher maturity -> lower failure rate)
        freq_factor = max(0.4, 1.2 - 0.20 * (cmmi_maturity - 1.0))
        outage_min = round_to_actuarial_significance(worst_case_event_min * freq_factor * 0.22)
        outage_max = round_to_actuarial_significance(worst_case_event_max * freq_factor * 0.25)
        if outage_max <= outage_min:
            outage_max = outage_min + round_to_actuarial_significance(outage_min * 0.35)

        # Contractual Escalation Lever 3
        contractual_min = round_to_actuarial_significance(outage_min * 0.70)
        contractual_max = round_to_actuarial_significance(outage_max * 0.75)
        if contractual_max <= contractual_min:
            contractual_max = contractual_min + round_to_actuarial_significance(contractual_min * 0.30)

        # Deterministic COD (Toil + Contractual)
        total_cod_min = toil_min + contractual_min
        total_cod_max = toil_max + contractual_max

        # Total Cost of Inaction (COI = COD + Outage ALE)
        total_coi_min = total_cod_min + outage_min
        total_coi_max = total_cod_max + outage_max

        toil_share = round((toil_min / total_coi_min) * 100.0, 1) if total_coi_min > 0 else 40.0
        outage_share = round((outage_min / total_coi_min) * 100.0, 1) if total_coi_min > 0 else 35.0
        contract_share = round(100.0 - toil_share - outage_share, 1)

        cod_breakdown = ChronicOperationalDragBreakdown(
            annual_engineering_toil_hours=int((min_toil_hours + max_toil_hours) // 2),
            engineering_toil_cost_interval=MonetaryInterval(
                lower_bound=toil_min, upper_bound=toil_max, currency_iso=currency_iso
            ),
            contractual_and_licensing_escalation_interval=MonetaryInterval(
                lower_bound=contractual_min, upper_bound=contractual_max, currency_iso=currency_iso
            ),
            total_chronic_drag_interval=MonetaryInterval(
                lower_bound=total_cod_min, upper_bound=total_cod_max, currency_iso=currency_iso
            ),
        )

        outage_breakdown = ProbabilisticOutageALEBreakdown(
            gross_standalone_ale_sum=int(round(outage_min * 1.25)),
            portfolio_subadditivity_factor=0.80,
            annual_outage_ale_interval=MonetaryInterval(
                lower_bound=outage_min, upper_bound=outage_max, currency_iso=currency_iso
            ),
            worst_case_single_outage_event=MonetaryInterval(
                lower_bound=worst_case_event_min, upper_bound=worst_case_event_max, currency_iso=currency_iso
            ),
        )

        total_coi = CostOfInactionTotal(
            lever_1_toil_share_pct=toil_share,
            lever_2_outage_ale_share_pct=outage_share,
            lever_3_contractual_share_pct=contract_share,
            annual_total_coi_interval=MonetaryInterval(
                lower_bound=total_coi_min, upper_bound=total_coi_max, currency_iso=currency_iso
            ),
        )

        tco_3yr = ThreeYearCompoundedTCO(
            lower_bound_eur=total_coi_min * 3,
            upper_bound_eur=total_coi_max * 3,
            midpoint_eur=(total_coi_min * 3 + total_coi_max * 3) // 2,
            currency_iso=currency_iso,
        )

        # 3. Extract and Formulate Risk Cards with Exact Discrete Sub-Additive Allocation
        raw_cards = cls._extract_strategic_risk_cards(
            findings_pool=findings_pool,
            tower_id=tower_id,
            tower_name=tower_name,
            event_loss_min=float(worst_case_event_min),
            event_loss_max=float(worst_case_event_max),
            annual_exposure_min=float(outage_min),
            annual_exposure_max=float(outage_max),
            target_locale=target_locale,
        )

        # Discrete Hare-Niemeyer allocation for exact sum matching Lever 2 Outage ALE
        card_weights = [c.get("annual_exposure_min", 1000.0) for c in raw_cards]
        allocated_lows = allocate_subadditive_ale_to_cards(outage_min, card_weights)
        allocated_highs = allocate_subadditive_ale_to_cards(outage_max, card_weights)

        risk_scenarios: List[TechnicalRiskScenario] = []
        for idx, (c_data, a_low, a_high) in enumerate(zip(raw_cards, allocated_lows, allocated_highs), start=1):
            is_tier1 = idx <= 2
            # Heatmap placement: Tier 1 -> (Likelihood 3-4, Impact 4-5); Tier 2 -> (Likelihood 2-3, Impact 3-4)
            l_idx = 4 if is_tier1 and idx == 1 else (3 if is_tier1 else 3)
            i_idx = 4 if is_tier1 and idx == 1 else (4 if is_tier1 else 3)

            full_title = str(c_data.get("title") or f"Risk Scenario {idx}")
            truncated = _truncate_smart_words(full_title, max_chars=38)

            coord = HeatmapCoordinate(
                likelihood_index=l_idx,
                impact_index=i_idx,
                truncated_title=truncated,
            )

            scenario = TechnicalRiskScenario(
                risk_id=f"RSK-{tower_id}-0{idx}",
                title=full_title,
                custody_role="PRIMARY_CUSTODIAN",
                threat_event_frequency_annual=1.5 if is_tier1 else 0.8,
                vulnerability_ratio=0.85 if is_tier1 else 0.60,
                mttr_recovery_hours=float(eff_rto if is_tier1 else max(2.0, eff_rto * 0.6)),
                calibrated_annual_ale=MonetaryInterval(
                    lower_bound=a_low, upper_bound=a_high, currency_iso=currency_iso
                ),
                heatmap_coordinate=coord,
                physical_evidence=str(c_data.get("technical_evidence") or f"Structural evidence observed in {full_title}."),
                root_cause_mechanism=str(c_data.get("operational_impact_chain") or f"Operational bottleneck in {full_title}."),
                business_impact_narrative=str(c_data.get("operational_impact_chain") or f"Business disruption risk dependent on {full_title}."),
                required_mitigation=f"Architectural modernization and automated resilience controls for {full_title}.",
                is_full_card_rendered=True,
            )
            risk_scenarios.append(scenario)

        payload = Chapter4SynthesisPayload(
            tower_id=tower_id,
            tower_name=tower_name,
            enterprise_id=enterprise_id,
            evaluated_cmmi_maturity=cmmi_maturity,
            currency_iso=currency_iso,
            chronic_operational_drag=cod_breakdown,
            probabilistic_outage_ale=outage_breakdown,
            total_annual_coi=total_coi,
            three_year_compounded_tco=tco_3yr,
            technical_risk_cards=tuple(risk_scenarios),
        )

        blueprint_data["chapter4_monistic_payload"] = payload.model_dump()
        return payload

    @classmethod
    def synthesize_chapter4(
        cls,
        blueprint_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        rates_catalog: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Synthesizes the complete Chapter 4 executive payload and returns dict for legacy compatibility."""
        payload = cls.synthesize_payload(blueprint_data, context, rates_catalog)

        # Construct backward-compatible dict for legacy AST bridge consumers
        anchors = [
            {
                "anchor_type": "OPERATIONAL_TOIL",
                "dimension_title": "1. Operational Engineering Toil (Recurring Maintenance)",
                "narrative_key": "ch4_anchor_toil_desc",
                "annual_exposure_min": float(payload.chronic_operational_drag.engineering_toil_cost_interval.lower_bound),
                "annual_exposure_max": float(payload.chronic_operational_drag.engineering_toil_cost_interval.upper_bound),
                "exposure_formula_display": f"{payload.chronic_operational_drag.annual_engineering_toil_hours} h/yr in manual maintenance and reactive operations",
                "evidence_narrative": f"Ongoing manual resource adjustments, operational maintenance toil, and reactive troubleshooting across {payload.tower_name}.",
                "governing_milestone_date": None,
            },
            {
                "anchor_type": "AVAILABILITY_DISRUPTION",
                "dimension_title": "2. Availability & Outage Disruption Exposure",
                "narrative_key": "ch4_anchor_outage_desc",
                "annual_exposure_min": float(payload.probabilistic_outage_ale.annual_outage_ale_interval.lower_bound),
                "annual_exposure_max": float(payload.probabilistic_outage_ale.annual_outage_ale_interval.upper_bound),
                "exposure_formula_display": "Probabilistic loss exposure from single points of failure (SPOF)",
                "evidence_narrative": f"Operational contingency and disruption risk upon component failure or hardware degradation in {payload.tower_name}.",
                "governing_milestone_date": None,
            },
            {
                "anchor_type": "CONTRACTUAL_FORCING_FUNCTION",
                "dimension_title": "3. Projected Vendor & Lifecycle Contractual Overspend",
                "narrative_key": "ch4_anchor_contractual_desc",
                "annual_exposure_min": float(payload.chronic_operational_drag.contractual_and_licensing_escalation_interval.lower_bound),
                "annual_exposure_max": float(payload.chronic_operational_drag.contractual_and_licensing_escalation_interval.upper_bound),
                "exposure_formula_display": "Projected lifecycle support escalation upon contract expiration",
                "evidence_narrative": f"Vendor support escalation and lifecycle transition risks across {payload.tower_name}.",
                "governing_milestone_date": None,
            },
        ]

        cards = [
            {
                "risk_id": card.risk_id,
                "tier": "TIER_1_CRITICAL" if idx < 2 else "TIER_2_STRUCTURAL",
                "title": card.title,
                "affected_perimeter": payload.tower_name,
                "estimated_frequency_label": "1 event / 12-18 months" if idx < 2 else "Continuous Latent Exposure",
                "technical_evidence": card.physical_evidence,
                "operational_impact_chain": card.business_impact_narrative,
                "event_loss_min": float(payload.probabilistic_outage_ale.worst_case_single_outage_event.lower_bound),
                "event_loss_max": float(payload.probabilistic_outage_ale.worst_case_single_outage_event.upper_bound),
                "annual_exposure_min": float(card.calibrated_annual_ale.lower_bound),
                "annual_exposure_max": float(card.calibrated_annual_ale.upper_bound),
                "external_forcing_milestone": None,
            }
            for idx, card in enumerate(payload.technical_risk_cards)
        ]

        synthesis_payload = {
            "total_status_quo_exposure_min": float(payload.total_annual_coi.annual_total_coi_interval.lower_bound),
            "total_status_quo_exposure_max": float(payload.total_annual_coi.annual_total_coi_interval.upper_bound),
            "anchors": anchors,
            "matrix_concentration_narrative": [
                f"Core Operational Continuity Axis (Tier 1): Concentrates the primary operational and resilience exposure in {payload.tower_name}.",
                f"Technical Debt and Governance Axis (Tier 2): Concentrates exposure arising from platform lifecycle aging and maintenance scheduling constraints.",
            ],
            "strategic_risk_cards": cards,
            "monistic_payload": payload.model_dump(),
        }

        blueprint_data["chapter4_synthesis"] = synthesis_payload
        return synthesis_payload

    @classmethod
    def _extract_strategic_risk_cards(
        cls,
        findings_pool: List[Dict[str, Any]],
        tower_id: str,
        tower_name: str,
        event_loss_min: float,
        event_loss_max: float,
        annual_exposure_min: float,
        annual_exposure_max: float,
        target_locale: str = "en",
    ) -> List[Dict[str, Any]]:
        """Extracts and prioritizes strictly 3 to 4 strategic primary risks."""
        from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
        resolver = get_taxonomy_resolver()

        def _calculate_priority(hc: Dict[str, Any]) -> float:
            p_score = _safe_float(hc.get("_pillar_score"), default=2.5)
            gap = max(0.5, 5.0 - p_score)

            text_corpus = f"{hc.get('finding', '')} {hc.get('business_risk', '')} {hc.get('capability', '')} {hc.get('_pillar_name', '')}".lower()
            is_auxiliary = any(k in text_corpus for k in ("test", "dev", "sandbox", "lab", "auxiliar", "cert-manager", "template", "golden image"))
            is_core = any(k in text_corpus for k in ("producci", "core", "host", "cluster", "database", "sap", "oracle", "network", "plant", "datacenter", "cpd", "pam", "credential"))

            criticality = 1.0 if (is_core and not is_auxiliary) else (0.3 if is_auxiliary else 0.7)
            tef = float(hc.get("threat_event_frequency") or 3.0)
            vuln = float(hc.get("vulnerability_level") or 3.0)
            return gap * criticality * (tef * 0.5 + vuln * 0.5)

        sorted_findings = sorted(findings_pool, key=_calculate_priority, reverse=True)
        target_count = 4 if len(sorted_findings) >= 4 else (3 if len(sorted_findings) >= 3 else len(sorted_findings))
        selected_findings = sorted_findings[:target_count] if sorted_findings else []

        cards: List[Dict[str, Any]] = []
        for idx, f in enumerate(selected_findings, start=1):
            raw_cap = str(f.get("capability") or f.get("target_state") or "").strip()
            p_name = str(f.get("_pillar_name") or tower_name).strip()

            clean_title = resolver.resolve_capability_name(raw_cap or p_name, locale=target_locale, default="")
            if not clean_title or re.match(r"^T\d+\.P\d+\.K\d+", clean_title, re.IGNORECASE):
                clean_title = resolver.resolve_pillar_by_any_reference(p_name, locale=target_locale, default=p_name)

            finding_txt = str(f.get("finding") or f.get("risk_observed") or "").strip()
            risk_txt = str(f.get("business_risk") or f.get("impact") or "").strip()

            cards.append(
                {
                    "title": clean_title,
                    "technical_evidence": finding_txt if len(finding_txt) >= 20 else f"Structural gap identified in the operational baseline and governance of {clean_title}.",
                    "operational_impact_chain": risk_txt if len(risk_txt) >= 20 else f"Risk of unplanned operational disruption and business workflow degradation dependent on {clean_title}.",
                    "annual_exposure_min": annual_exposure_min * (0.6 if idx > 2 else 1.0),
                    "annual_exposure_max": annual_exposure_max * (0.6 if idx > 2 else 1.0),
                }
            )

        return cards
