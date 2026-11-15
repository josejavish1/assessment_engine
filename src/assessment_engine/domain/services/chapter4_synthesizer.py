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

import hashlib
import logging
import math
import re
import numpy as np
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
from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver

logger = logging.getLogger(__name__)

GLOBAL_BENCHMARK_RATE_CARD: Dict[str, Any] = {
    "country_name": "Global Benchmark",
    "currency_iso": "EUR",
    "systems_engineer_hourly_rate": 45.0,
    "senior_architect_hourly_rate": 70.0,
    "technician_hourly_rate": 35.0,
    "default_hourly_disruption_cost": 3000.0,
    "annual_contractual_escalation_rate": 0.08,
}

# FX normalization multipliers relative to EUR/USD parity for high-denomination currencies
CURRENCY_UNIT_MULTIPLIERS: Dict[str, float] = {
    "EUR": 1.0,
    "USD": 1.0,
    "GBP": 0.85,
    "CHF": 0.95,
    "JPY": 160.0,
    "KRW": 1450.0,
    "MXN": 20.0,
    "BRL": 6.0,
}

CORE_ASSET_KEYWORDS: Tuple[str, ...] = (
    "production",
    "core",
    "host",
    "cluster",
    "database",
    "sap",
    "oracle",
    "network",
    "plant",
    "datacenter",
    "data center",
    "pam",
    "credential",
    "scada",
    "clinical",
    "icu",
    "payment",
    "mainframe",
)

AUXILIARY_ASSET_KEYWORDS: Tuple[str, ...] = (
    "test",
    "dev",
    "sandbox",
    "lab",
    "auxiliary",
    "staging",
    "cert-manager",
    "template",
    "golden image",
)

DEFAULT_TOWER_RTO_HOURS: Dict[str, float] = {
    "T1": 8.0,
    "T2": 6.0,
    "T3": 6.0,
    "T4": 6.0,
    "T5": 8.0,
    "T6": 12.0,
    "T7": 6.0,
    "T8": 8.0,
    "T9": 4.0,
    "T10": 10.0,
}


def round_to_order_of_magnitude(val: float, precision: int = 1) -> float:
    """Rounds a numeric value dynamically relative to its order of magnitude."""
    return float(round_to_actuarial_significance(val))


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely converts an arbitrary value to float without throwing ValueError or TypeError."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val) if math.isfinite(float(val)) else default
    try:
        clean = str(val).replace(",", ".").strip()
        parsed = float(clean)
        return parsed if math.isfinite(parsed) else default
    except (ValueError, TypeError):
        return default


def _truncate_smart_words(title: str, max_chars: int = 38) -> str:
    """Truncates text at word boundary to avoid breaking LaTeX/Word cell geometry."""
    clean = title.strip()
    if len(clean) <= max_chars:
        return clean
    truncated = clean[: max_chars - 1]
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
        currency_iso = curr_map.get(
            raw_currency,
            raw_currency if len(raw_currency) == 3 and raw_currency.isalpha() else "EUR",
        )
        target_locale = str(ctx.get("meta_lang") or doc_meta.get("language") or "en").strip().lower()

        effective_catalog = (
            rates_catalog or ctx.get("rates_catalog") or blueprint_data.get("rates_catalog")
        )
        rate_card = cls.get_country_rate_card(country_code, rates_catalog=effective_catalog)
        fx_mult = CURRENCY_UNIT_MULTIPLIERS.get(currency_iso, 1.0)
        hourly_rate = float(rate_card.get("systems_engineer_hourly_rate", 45.0 * fx_mult))

        # Enterprise Scale & Disruption Rate
        org_profile = (
            ctx.get("organization_profile")
            or blueprint_data.get("organization_profile")
            or ctx.get("client_intelligence", {}).get("profile")
            or {}
        )
        annual_revenue = _safe_float(
            ctx.get("annual_revenue")
            or org_profile.get("annual_revenue")
            or org_profile.get("consolidated_annual_revenue")
        )
        operating_hours = _safe_float(
            ctx.get("annual_operating_hours")
            or org_profile.get("annual_operating_hours"),
            default=8760.0,
        )
        operating_hours = max(2000.0, min(8760.0, operating_hours))

        explicit_rate = _safe_float(
            ctx.get("hourly_downtime_cost")
            or org_profile.get("hourly_downtime_cost")
            or org_profile.get("hourly_burn_rate")
        )
        if explicit_rate > 0.0:
            disruption_rate = float(round_to_actuarial_significance(explicit_rate))
        elif annual_revenue > 0.0:
            disruption_rate = float(
                round_to_actuarial_significance((annual_revenue / operating_hours) * 0.08)
            )
        else:
            disruption_rate = float(
                rate_card.get("default_hourly_disruption_cost", 3000.0 * fx_mult)
            )

        # Collect raw findings and calculate domain maturity (supporting canonical English + legacy keys)
        pillars = blueprint_data.get("pillars_analysis") or []
        findings_pool: List[Dict[str, Any]] = []
        pillar_scores: List[float] = []

        for p in pillars:
            if isinstance(p, dict):
                p_name = str(p.get("pillar_name") or p.get("pilar_name") or "Core Domain")
                p_score = _safe_float(
                    p.get("pillar_score") or p.get("pilar_score") or p.get("score"),
                    default=2.5,
                )
                pillar_scores.append(p_score)
                for hc in p.get("health_check_asis") or []:
                    if isinstance(hc, dict):
                        hc_copy = dict(hc)
                        hc_copy["_pillar_name"] = p_name
                        hc_copy["_pillar_score"] = p_score
                        findings_pool.append(hc_copy)

        cmmi_maturity = (
            round(sum(pillar_scores) / len(pillar_scores), 2) if pillar_scores else 2.5
        )
        cmmi_maturity = max(1.0, min(5.0, cmmi_maturity))

        # Continuous Maturity Elasticity & Enterprise Scale Normalization
        headcount = _safe_float(
            org_profile.get("headcount") or org_profile.get("employee_count"), default=0.0
        )
        normalized_rev_eur = annual_revenue / fx_mult if annual_revenue > 0 else 0.0
        if headcount > 0.0:
            scale_factor = max(0.5, math.log10(max(10.0, headcount)) / 3.0)
        elif normalized_rev_eur > 0.0:
            scale_factor = max(0.5, math.log10(max(10_000_000.0, normalized_rev_eur)) / 9.0)
        else:
            scale_factor = 1.0

        # Lever 1: Engineering Toil
        toil_hours_base = 750.0 * scale_factor * (1.30 - 0.15 * (cmmi_maturity - 1.0))
        min_toil_hours = max(40, int(round(toil_hours_base * 0.9)))
        max_toil_hours = max(min_toil_hours + 20, int(round(toil_hours_base * 1.2)))

        toil_min = round_to_actuarial_significance(min_toil_hours * hourly_rate)
        toil_max = round_to_actuarial_significance(max_toil_hours * hourly_rate)
        if toil_max <= toil_min:
            toil_max = toil_min + round_to_actuarial_significance(toil_min * 0.25)

        # Lever 2: Probabilistic Outage ALE (supports sub-hour high-frequency domains to multi-day industrial RTOs)
        raw_rto = _safe_float(
            ctx.get("worst_crisis_rto_hours")
            or blueprint_data.get("worst_crisis_rto_hours")
        )
        default_rto = DEFAULT_TOWER_RTO_HOURS.get(tower_id, 6.0)
        # Actuarial Invariant: Default domain RTO activates when raw RTO is missing or uncalibrated (<= 0.0),
        # while respecting explicit sub-hour high-availability architectures (e.g. 0.5h for Tier-1 Banks).
        eff_rto = max(0.5, min(72.0, raw_rto if raw_rto > 0.0 else default_rto))
        min_duration = max(0.25, eff_rto * 0.80)
        max_duration = max(min_duration + 0.5, eff_rto * 1.25)

        worst_case_event_min = round_to_actuarial_significance(
            min_duration * disruption_rate * 1.15
        )
        worst_case_event_max = round_to_actuarial_significance(
            max_duration * disruption_rate * 1.30
        )
        if worst_case_event_max <= worst_case_event_min:
            worst_case_event_max = worst_case_event_min + round_to_actuarial_significance(
                worst_case_event_min * 0.35
            )

        # Annualized failure frequency (scaled continuously by CMMI maturity)
        freq_factor = max(0.25, 1.25 - 0.22 * (cmmi_maturity - 1.0))
        outage_min = round_to_actuarial_significance(
            worst_case_event_min * freq_factor * 0.22
        )
        outage_max = round_to_actuarial_significance(
            worst_case_event_max * freq_factor * 0.25
        )
        if outage_max <= outage_min:
            outage_max = outage_min + round_to_actuarial_significance(outage_min * 0.35)

        # Lever 3: Contractual & Licensing Escalation (Anchored on IT/Infrastructure baseline + maturity)
        # High-maturity organizations have lower unplanned outages relative to structural licensing lock-in
        maturity_contract_weight = 0.40 + 0.15 * (cmmi_maturity - 1.0)
        baseline_economic_anchor = (outage_min * 0.60) + (toil_min * 0.45)
        contractual_min = round_to_actuarial_significance(
            baseline_economic_anchor * maturity_contract_weight
        )
        contractual_max = round_to_actuarial_significance(
            ((outage_max * 0.60) + (toil_max * 0.45)) * (maturity_contract_weight + 0.05)
        )
        if contractual_max <= contractual_min:
            contractual_max = contractual_min + round_to_actuarial_significance(
                contractual_min * 0.30
            )

        # Deterministic COD (Toil + Contractual)
        total_cod_min = toil_min + contractual_min
        total_cod_max = toil_max + contractual_max

        # Total Cost of Inaction (COI = COD + Outage ALE)
        total_coi_min = total_cod_min + outage_min
        total_coi_max = total_cod_max + outage_max

        toil_share = (
            round((toil_min / total_coi_min) * 100.0, 1) if total_coi_min > 0 else 40.0
        )
        outage_share = (
            round((outage_min / total_coi_min) * 100.0, 1) if total_coi_min > 0 else 35.0
        )
        contract_share = round(100.0 - toil_share - outage_share, 1)

        cod_breakdown = ChronicOperationalDragBreakdown(
            annual_engineering_toil_hours=int((min_toil_hours + max_toil_hours) // 2),
            engineering_toil_cost_interval=MonetaryInterval(
                lower_bound=toil_min, upper_bound=toil_max, currency_iso=currency_iso
            ),
            contractual_and_licensing_escalation_interval=MonetaryInterval(
                lower_bound=contractual_min,
                upper_bound=contractual_max,
                currency_iso=currency_iso,
            ),
            total_chronic_drag_interval=MonetaryInterval(
                lower_bound=total_cod_min,
                upper_bound=total_cod_max,
                currency_iso=currency_iso,
            ),
        )

        # Extract and Formulate Risk Cards with Exact Discrete Sub-Additive Allocation
        raw_cards = cls._extract_strategic_risk_cards(
            findings_pool=findings_pool,
            tower_id=tower_id,
            tower_name=tower_name,
            event_loss_min=float(worst_case_event_min),
            event_loss_max=float(worst_case_event_max),
            annual_exposure_min=float(outage_min),
            annual_exposure_max=float(outage_max),
            cmmi_maturity=cmmi_maturity,
            target_locale=target_locale,
        )

        # Dynamic sub-additivity factor based on portfolio card count (1 card = 1.0, 4 cards = 0.80)
        subadditivity_factor = round(max(0.75, 1.0 - 0.05 * max(0, len(raw_cards) - 1)), 2)
        gross_standalone_sum = int(round(outage_min / subadditivity_factor))

        outage_breakdown = ProbabilisticOutageALEBreakdown(
            gross_standalone_ale_sum=gross_standalone_sum,
            portfolio_subadditivity_factor=subadditivity_factor,
            annual_outage_ale_interval=MonetaryInterval(
                lower_bound=outage_min, upper_bound=outage_max, currency_iso=currency_iso
            ),
            worst_case_single_outage_event=MonetaryInterval(
                lower_bound=worst_case_event_min,
                upper_bound=worst_case_event_max,
                currency_iso=currency_iso,
            ),
        )

        total_coi = CostOfInactionTotal(
            lever_1_toil_share_pct=toil_share,
            lever_2_outage_ale_share_pct=outage_share,
            lever_3_contractual_share_pct=contract_share,
            annual_total_coi_interval=MonetaryInterval(
                lower_bound=total_coi_min,
                upper_bound=total_coi_max,
                currency_iso=currency_iso,
            ),
        )

        # 36-Month Compounded TCO (incorporates contractual escalation compounding rate)
        escalation_rate = float(rate_card.get("annual_contractual_escalation_rate", 0.0))
        compounding_multiplier = 1.0 + (1.0 + escalation_rate) + ((1.0 + escalation_rate) ** 2)
        tco_low = int(round(total_coi_min * compounding_multiplier)) if escalation_rate > 0 else total_coi_min * 3
        tco_high = int(round(total_coi_max * compounding_multiplier)) if escalation_rate > 0 else total_coi_max * 3

        tco_3yr = ThreeYearCompoundedTCO(
            lower_bound=tco_low,
            upper_bound=tco_high,
            midpoint=(tco_low + tco_high) // 2,
            compounding_rate_annual=escalation_rate,
            currency_iso=currency_iso,
        )

        # Quantum-preserving Hare-Niemeyer allocation for exact sum matching Lever 2 Outage ALE
        card_weights = [float(c.get("annual_exposure_min", 1000.0)) for c in raw_cards]
        card_ids = [f"RSK-{tower_id}-0{idx}" for idx in range(1, len(raw_cards) + 1)]
        allocated_lows = allocate_subadditive_ale_to_cards(outage_min, card_weights, card_ids=card_ids)
        allocated_highs = allocate_subadditive_ale_to_cards(outage_max, card_weights, card_ids=card_ids)

        risk_scenarios: List[TechnicalRiskScenario] = []
        # Canonical TEF midpoint anchor per heatmap likelihood row
        TEF_ROW_MIDPOINTS: dict[int, float] = {
            1: 0.05,
            2: 0.30,
            3: 1.25,
            4: 2.40,
            5: 12.0,
        }
        
        # Initialize Seeded PRNG for Deterministic Monte Carlo Convolution (N=50,000)
        seed_str = f"{enterprise_id}_{tower_id}_{sum(card_weights)}"
        seed_int = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(np.random.PCG64(seed_int))
        N_TRIALS = 50000

        for idx, (c_data, a_low, a_high) in enumerate(
            zip(raw_cards, allocated_lows, allocated_highs), start=1
        ):
            is_tier1 = idx <= 2
            safe_low = min(a_low, a_high)
            safe_high = max(a_low, a_high)

            # Tier 1 represents discrete major contingencies (TEF 3: 0.5 - 2.0/yr)
            # Tier 2 represents chronic operational friction (TEF 4: 2.0 - 10.0/yr)
            l_idx = 3 if is_tier1 else 4
            tef_val = TEF_ROW_MIDPOINTS.get(l_idx, 1.25 if is_tier1 else 2.40)
            
            # Deterministic Vulnerability Sigmoid Curve
            vuln_score_base = float(c_data.get("vuln_ratio", 3.0)) # Mapping score to vuln
            # Vuln(S) = 1 / (1 + exp(1.65 * (S - 3.0)))
            vuln_ratio = 1.0 / (1.0 + math.exp(1.65 * (vuln_score_base - 3.0))) if vuln_score_base > 1.0 else (0.80 if is_tier1 else 0.95)
            vuln_ratio = max(0.01, min(0.99, vuln_ratio))
            
            # Beta-PERT Monte Carlo Convolution
            tef_min, tef_max = max(0.01, tef_val * 0.5), tef_val * 1.5
            # Beta-PERT approximation: alpha = 1 + 4*((mode-min)/(max-min)), beta = 1 + 4*((max-mode)/(max-min))
            # For simplicity in Numpy, we can sample triangular and multiply by a Beta-sampled vulnerability
            tef_samples = rng.triangular(tef_min, tef_val, tef_max, size=N_TRIALS)
            vuln_samples = rng.beta(vuln_ratio * 10, (1 - vuln_ratio) * 10, size=N_TRIALS)
            lef_samples = tef_samples * vuln_samples
            lef_val = float(np.median(lef_samples))
            
            lef_val = max(0.01, lef_val)
            sle_mid = ((safe_low / lef_val) + (safe_high / lef_val)) / 2.0

            # Dynamic LM tier resolution based on Open FAIR scale brackets
            if sle_mid < 1000.0:
                calc_lm = 1
            elif sle_mid < 4000.0:
                calc_lm = 2
            elif sle_mid < 16000.0:
                calc_lm = 3
            elif sle_mid < 64000.0:
                calc_lm = 4
            else:
                calc_lm = 5

            i_idx = calc_lm

            full_title = str(c_data.get("title") or f"Strategic Risk Scenario {idx}")
            truncated = _truncate_smart_words(full_title, max_chars=38)

            coord = HeatmapCoordinate(
                likelihood_index=max(1, min(5, l_idx)),
                impact_index=max(1, min(5, i_idx)),
                truncated_title=truncated,
            )

            scenario = TechnicalRiskScenario(
                risk_id=card_ids[idx - 1],
                title=full_title,
                custody_role="PRIMARY_CUSTODIAN",
                threat_event_frequency_annual=tef_val,
                vulnerability_ratio=vuln_ratio,
                mttr_recovery_hours=float(max(0.1, eff_rto if is_tier1 else max(0.5, eff_rto * 0.6))),
                calibrated_annual_ale=MonetaryInterval(
                    lower_bound=safe_low, upper_bound=safe_high, currency_iso=currency_iso
                ),
                heatmap_coordinate=coord,
                physical_evidence=str(
                    c_data.get("technical_evidence")
                    or f"Structural evidence observed in {full_title}."
                ),
                root_cause_mechanism=str(
                    c_data.get("operational_impact_chain")
                    or f"Operational bottleneck identified in {full_title}."
                ),
                business_impact_narrative=str(
                    c_data.get("operational_impact_chain")
                    or f"Business disruption exposure dependent on {full_title}."
                ),
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

        anchors = [
            {
                "anchor_type": "OPERATIONAL_TOIL",
                "dimension_title": "1. Operational Engineering Toil (Recurring Maintenance)",
                "narrative_key": "ch4_anchor_toil_desc",
                "annual_exposure_min": float(
                    payload.chronic_operational_drag.engineering_toil_cost_interval.lower_bound
                ),
                "annual_exposure_max": float(
                    payload.chronic_operational_drag.engineering_toil_cost_interval.upper_bound
                ),
                "exposure_formula_display": f"{payload.chronic_operational_drag.annual_engineering_toil_hours} h/yr in manual maintenance and reactive operations",
                "evidence_narrative": f"Ongoing manual resource adjustments, operational maintenance toil, and reactive troubleshooting across {payload.tower_name}.",
                "governing_milestone_date": None,
            },
            {
                "anchor_type": "AVAILABILITY_DISRUPTION",
                "dimension_title": "2. Availability & Outage Disruption Exposure",
                "narrative_key": "ch4_anchor_outage_desc",
                "annual_exposure_min": float(
                    payload.probabilistic_outage_ale.annual_outage_ale_interval.lower_bound
                ),
                "annual_exposure_max": float(
                    payload.probabilistic_outage_ale.annual_outage_ale_interval.upper_bound
                ),
                "exposure_formula_display": "Probabilistic loss exposure from single points of failure (SPOF)",
                "evidence_narrative": f"Operational contingency and disruption risk upon component failure or hardware degradation in {payload.tower_name}.",
                "governing_milestone_date": None,
            },
            {
                "anchor_type": "CONTRACTUAL_FORCING_FUNCTION",
                "dimension_title": "3. Projected Vendor & Lifecycle Contractual Overspend",
                "narrative_key": "ch4_anchor_contractual_desc",
                "annual_exposure_min": float(
                    payload.chronic_operational_drag.contractual_and_licensing_escalation_interval.lower_bound
                ),
                "annual_exposure_max": float(
                    payload.chronic_operational_drag.contractual_and_licensing_escalation_interval.upper_bound
                ),
                "exposure_formula_display": "Projected lifecycle support escalation upon contract expiration",
                "evidence_narrative": f"Vendor support escalation and lifecycle transition risks across {payload.tower_name}.",
                "governing_milestone_date": None,
            },
        ]

        ctx = context or {}
        doc_meta = blueprint_data.get("document_meta") or {}
        target_locale = str(ctx.get("meta_lang") or doc_meta.get("language") or "en").strip().lower()
        is_es = target_locale.startswith("es")

        tef_labels_es = {
            1: "< 0,1 eventos/año (menos de 1 vez cada 10 años)",
            2: "0,1 - 0,5 eventos/año (1 evento cada 2 a 10 años)",
            3: "0,5 - 2,0 eventos/año (1 evento cada 12 a 24 meses)",
            4: "2,0 - 10,0 eventos/año (contingencia recurrente anual)",
            5: "> 10 eventos/año (frecuencia mensual / recurrencia continua)",
        }
        tef_labels_en = {
            1: "< 0.1 events/year (less than once every 10 years)",
            2: "0.1 - 0.5 events/year (once every 2 to 10 years)",
            3: "0.5 - 2.0 events/year (once every 12 to 24 months)",
            4: "2.0 - 10.0 events/year (annual recurring contingency)",
            5: "> 10 events/year (monthly frequency / continuous recurrence)",
        }

        cards = []
        for idx, card in enumerate(payload.technical_risk_cards):
            tef_val = float(card.threat_event_frequency_annual)
            vuln_ratio = float(card.vulnerability_ratio)
            lef_val = float(round(max(0.01, tef_val * vuln_ratio), 2))
            ale_low = float(card.calibrated_annual_ale.lower_bound)
            ale_high = float(card.calibrated_annual_ale.upper_bound)
            sle_low = float(round_to_actuarial_significance(ale_low / lef_val))
            sle_high = float(round_to_actuarial_significance(ale_high / lef_val))
            if sle_high <= sle_low:
                sle_high = sle_low + float(round_to_actuarial_significance(sle_low * 0.35))

            cards.append(
                {
                    "risk_id": card.risk_id,
                    "tier": "TIER_1_CRITICAL" if idx < 2 else "TIER_2_STRUCTURAL",
                    "title": card.title,
                    "affected_perimeter": payload.tower_name,
                    "estimated_frequency_label": (
                        tef_labels_es.get(card.heatmap_coordinate.likelihood_index, "0,5 - 2,0 eventos/año")
                        if is_es
                        else tef_labels_en.get(card.heatmap_coordinate.likelihood_index, "0.5 - 2.0 events/year")
                    ),
                    "technical_evidence": card.physical_evidence,
                    "operational_impact_chain": card.business_impact_narrative,
                    "threat_event_frequency_annual": tef_val,
                    "vulnerability_ratio": vuln_ratio,
                    "loss_event_frequency_annual": lef_val,
                    "event_loss_min": sle_low,
                    "event_loss_max": sle_high,
                    "annual_exposure_min": ale_low,
                    "annual_exposure_max": ale_high,
                    "external_forcing_milestone": None,
                }
            )

        concentration_narrative = [
            f"Eje de Continuidad Operativa Crítica (Tier 1): Concentra la principal exposición por indisponibilidad y resiliencia de la plataforma en {payload.tower_name}.",
            "Eje de Deuda Técnica y Gobernanza (Tier 2): Concentra la exposición derivada del envejecimiento del ciclo de vida de los activos y los condicionantes de mantenimiento operativo.",
        ] if is_es else [
            f"Core Operational Continuity Axis (Tier 1): Concentrates the primary operational and resilience exposure in {payload.tower_name}.",
            "Technical Debt and Governance Axis (Tier 2): Concentrates exposure arising from platform lifecycle aging and maintenance scheduling constraints.",
        ]

        synthesis_payload = {
            "total_status_quo_exposure_min": float(
                payload.total_annual_coi.annual_total_coi_interval.lower_bound
            ),
            "total_status_quo_exposure_max": float(
                payload.total_annual_coi.annual_total_coi_interval.upper_bound
            ),
            "anchors": anchors,
            "matrix_concentration_narrative": concentration_narrative,
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
        cmmi_maturity: float = 2.5,
        target_locale: str = "en",
    ) -> List[Dict[str, Any]]:
        """Extracts and prioritizes strictly 3 to 4 strategic primary risks (with resilience fallback)."""
        resolver = get_taxonomy_resolver()

        def _calculate_priority(hc: Dict[str, Any]) -> float:
            p_score = _safe_float(hc.get("_pillar_score"), default=cmmi_maturity)
            gap = max(0.5, 5.0 - p_score)

            text_corpus = (
                f"{hc.get('finding', '')} {hc.get('business_risk', '')} "
                f"{hc.get('capability', '')} {hc.get('_pillar_name', '')}"
            ).lower()
            is_auxiliary = any(k in text_corpus for k in AUXILIARY_ASSET_KEYWORDS)
            is_core = any(k in text_corpus for k in CORE_ASSET_KEYWORDS)

            criticality = 1.0 if (is_core and not is_auxiliary) else (0.3 if is_auxiliary else 0.7)
            tef = _safe_float(hc.get("threat_event_frequency"), default=3.0)
            vuln = _safe_float(hc.get("vulnerability_level"), default=3.0)
            return gap * criticality * (tef * 0.5 + vuln * 0.5)

        sorted_findings = sorted(findings_pool, key=_calculate_priority, reverse=True)
        target_count = (
            4
            if len(sorted_findings) >= 4
            else (3 if len(sorted_findings) >= 3 else len(sorted_findings))
        )
        selected_findings = sorted_findings[:target_count] if sorted_findings else []

        # Fallback if blueprint has zero findings so Chapter4SynthesisPayload never crashes
        if not selected_findings:
            selected_findings = [
                {
                    "capability": f"{tower_name} Resilience & Operational Continuity",
                    "_pillar_name": tower_name,
                    "_pillar_score": cmmi_maturity,
                    "finding": f"Structural operational baseline and single-point-of-failure exposure observed across {tower_name}.",
                    "business_risk": f"Unplanned service disruption and operational degradation impacting core workflows in {tower_name}.",
                    "threat_event_frequency": 2.0,
                    "vulnerability_level": 3.0,
                }
            ]

        cards: List[Dict[str, Any]] = []
        for idx, f in enumerate(selected_findings, start=1):
            raw_cap = str(f.get("capability") or f.get("target_state") or "").strip()
            p_name = str(f.get("_pillar_name") or tower_name).strip()

            clean_title = resolver.resolve_capability_name(
                raw_cap or p_name, locale=target_locale, default=""
            )
            if not clean_title or re.match(r"^T\d+\.P\d+\.K\d+", clean_title, re.IGNORECASE):
                clean_title = resolver.resolve_pillar_by_any_reference(
                    p_name, locale=target_locale, default=p_name
                )
            if len(clean_title) < 5:
                clean_title = f"{tower_name} Scenario {idx}"

            finding_txt = str(f.get("finding") or f.get("risk_observed") or "").strip()
            risk_txt = str(f.get("business_risk") or f.get("impact") or "").strip()

            raw_tef = _safe_float(f.get("threat_event_frequency"), default=2.5 if idx <= 2 else 1.5)
            raw_vuln = _safe_float(f.get("vulnerability_level"), default=3.5 if idx <= 2 else 2.5)

            l_idx = max(1, min(5, int(round(raw_tef))))
            i_idx = max(1, min(5, int(round(raw_vuln))))
            weight_factor = 1.0 if idx <= 2 else 0.6

            cards.append(
                {
                    "title": clean_title,
                    "technical_evidence": (
                        finding_txt
                        if len(finding_txt) >= 20
                        else f"Structural gap identified in the operational baseline and governance of {clean_title}."
                    ),
                    "operational_impact_chain": (
                        risk_txt
                        if len(risk_txt) >= 20
                        else f"Risk of unplanned operational disruption and business workflow degradation dependent on {clean_title}."
                    ),
                    "annual_exposure_min": annual_exposure_min * weight_factor,
                    "annual_exposure_max": annual_exposure_max * weight_factor,
                    "likelihood_index": l_idx,
                    "impact_index": i_idx,
                    "tef_annual": max(0.05, min(50.0, raw_tef * 0.6)),
                    "vuln_ratio": max(0.10, min(0.95, raw_vuln / 5.0)),
                }
            )

        return cards
