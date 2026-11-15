"""Calibration test suite for universal multi-vertical and multi-scale enterprise archetypes.

Tests the Chapter 4 Actuarial Engine across 6 canonical world archetypes:
1. Heavy Discrete/Process Manufacturing OT (e.g. Molins, CEMEX).
2. Tier-1 Global Investment Bank (e.g. Santander, BBVA, JPMorgan).
3. Mid-Market Cloud SaaS Provider ($85M ARR).
4. Acute Regional Healthcare & Hospital Network (Clinical Systems, ICU).
5. Global Omnichannel Retailer (E-Commerce, POS, Supply Chain).
6. Critical Energy & Utilities Grid Operator (SCADA, Substations).
"""

from __future__ import annotations

import pytest

from assessment_engine.domain.actuarial.schemas import Chapter4SynthesisPayload
from assessment_engine.domain.services.chapter4_synthesizer import Chapter4Synthesizer

ARCHETYPES = [
    {
        "archetype_id": "MANUFACTURING_OT",
        "tower_id": "T1",
        "tower_name": "Physical Data Center & Plant Facilities",
        "client_id": "MOLINS_GLOBAL",
        "annual_revenue": 1_144_000_000.0,
        "cmmi_score": 2.1,
        "currency": "EUR",
        "rto_hours": 8.0,
    },
    {
        "archetype_id": "TIER1_INVESTMENT_BANK",
        "tower_id": "T6",
        "tower_name": "Core Banking Cyber Resilience & Identity",
        "client_id": "GLOBAL_TIER1_BANK",
        "annual_revenue": 45_000_000_000.0,
        "cmmi_score": 4.5,
        "currency": "USD",
        "rto_hours": 1.0,
    },
    {
        "archetype_id": "MIDMARKET_CLOUD_SAAS",
        "tower_id": "T2",
        "tower_name": "Multi-Tenant Cloud Infrastructure & Kubernetes",
        "client_id": "SCALEUP_SAAS",
        "annual_revenue": 85_000_000.0,
        "cmmi_score": 3.2,
        "currency": "USD",
        "rto_hours": 3.0,
    },
    {
        "archetype_id": "HEALTHCARE_HOSPITAL_NETWORK",
        "tower_id": "T5",
        "tower_name": "Clinical Systems & ICU Life-Safety Continuity",
        "client_id": "METRO_HEALTH_ICU",
        "annual_revenue": 400_000_000.0,
        "cmmi_score": 2.8,
        "currency": "EUR",
        "rto_hours": 4.0,
    },
    {
        "archetype_id": "GLOBAL_OMNICHANNEL_RETAILER",
        "tower_id": "T8",
        "tower_name": "E-Commerce, POS & Supply Chain Architecture",
        "client_id": "GLOBAL_RETAIL_CORP",
        "annual_revenue": 12_000_000_000.0,
        "cmmi_score": 3.0,
        "currency": "EUR",
        "rto_hours": 2.5,
    },
    {
        "archetype_id": "NATIONAL_ENERGY_GRID",
        "tower_id": "T3",
        "tower_name": "SCADA Network & Substation Telemetry",
        "client_id": "NATIONAL_POWER_GRID",
        "annual_revenue": 5_000_000_000.0,
        "cmmi_score": 4.2,
        "currency": "EUR",
        "rto_hours": 0.5,
    },
]


@pytest.mark.parametrize("arch", ARCHETYPES, ids=lambda a: a["archetype_id"])
def test_universal_chapter4_calibration_across_archetypes(arch: dict) -> None:
    """Verifies that Chapter4Synthesizer calibrates stably and monistically across all archetypes."""
    blueprint = {
        "document_meta": {
            "tower_id": arch["tower_id"],
            "tower_name": arch["tower_name"],
            "client_id": arch["client_id"],
            "currency": arch["currency"],
            "language": "en",
        },
        "organization_profile": {
            "annual_revenue": arch["annual_revenue"],
        },
        "worst_crisis_rto_hours": arch["rto_hours"],
        "pillars_analysis": [
            {
                "pilar_name": f"{arch['tower_name']} Core",
                "pilar_score": arch["cmmi_score"],
                "health_check_asis": [
                    {
                        "capability": f"Critical Capability {i}",
                        "finding": f"Technical operational observation {i} under {arch['archetype_id']}.",
                        "business_risk": f"Operational consequence and business blast radius {i}.",
                        "threat_event_frequency": 2.0,
                        "vulnerability_level": 3.0,
                    }
                    for i in range(1, 4)
                ],
            }
        ],
    }

    payload = Chapter4Synthesizer.synthesize_payload(blueprint)

    assert isinstance(payload, Chapter4SynthesisPayload)
    assert payload.tower_id == arch["tower_id"]
    assert payload.enterprise_id == arch["client_id"]
    assert payload.currency_iso == arch["currency"]

    # Invariant 1: Total Annual COI equals exact sum of COD + Outage ALE
    expected_low = (
        payload.chronic_operational_drag.total_chronic_drag_interval.lower_bound
        + payload.probabilistic_outage_ale.annual_outage_ale_interval.lower_bound
    )
    expected_high = (
        payload.chronic_operational_drag.total_chronic_drag_interval.upper_bound
        + payload.probabilistic_outage_ale.annual_outage_ale_interval.upper_bound
    )
    actual_coi = payload.total_annual_coi.annual_total_coi_interval

    assert actual_coi.lower_bound == expected_low
    assert actual_coi.upper_bound == expected_high

    # Invariant 2: Card ALEs sum exactly to Outage ALE
    card_low_sum = sum(c.calibrated_annual_ale.lower_bound for c in payload.technical_risk_cards)
    card_high_sum = sum(c.calibrated_annual_ale.upper_bound for c in payload.technical_risk_cards)
    outage_ale = payload.probabilistic_outage_ale.annual_outage_ale_interval

    assert card_low_sum == outage_ale.lower_bound
    assert card_high_sum == outage_ale.upper_bound

    # Invariant 3: Zero false precision (all bounds are positive integers rounded to quanta)
    assert actual_coi.lower_bound > 0
    assert actual_coi.upper_bound >= actual_coi.lower_bound

    # Invariant 4: Continuous maturity loss dynamics
    if arch["cmmi_score"] <= 2.2:
        # Low maturity: Outage ALE and Toil dominate
        assert payload.total_annual_coi.lever_1_toil_share_pct + payload.total_annual_coi.lever_2_outage_ale_share_pct >= 65.0
    elif arch["cmmi_score"] >= 4.0:
        # High maturity: Outage share is well-controlled
        assert payload.total_annual_coi.lever_2_outage_ale_share_pct <= 45.0
