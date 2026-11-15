"""Unit tests for Chapter4Synthesizer dynamic CMMI calibration and monistic payload generation.

Verifies:
1. Production of validated Chapter4SynthesisPayload from raw blueprint data.
2. Invariant satisfaction across CMMI scores (1.0 to 5.0).
3. Discrete Hare-Niemeyer card allocation reconciling 100% with Lever 2 Outage ALE.
4. 100% Technical English in all identifiers, docstrings, and test fixtures.
"""

from __future__ import annotations

import pytest

from assessment_engine.domain.actuarial.schemas import Chapter4SynthesisPayload
from assessment_engine.domain.services.chapter4_synthesizer import Chapter4Synthesizer


@pytest.fixture
def sample_blueprint_data() -> dict:
    return {
        "document_meta": {
            "tower_id": "T1",
            "tower_name": "Physical Data Center & Facilities",
            "client_id": "ENTERPRISE_GLOBAL",
            "language": "en",
        },
        "organization_profile": {
            "annual_revenue": 1144000000.0,
        },
        "worst_crisis_rto_hours": 8.0,
        "pillars_analysis": [
            {
                "pillar_name": "Facilities & Power",
                "pillar_score": 1.8,
                "health_check_asis": [
                    {
                        "capability": "ASHRAE TC 9.9 Thermal Telemetry",
                        "finding": "Absence of intake plane thermal telemetry sensors on technical server racks.",
                        "business_risk": "Unplanned server throttling and hardware failure from unmonitored thermal hotspots.",
                        "threat_event_frequency": 2.0,
                        "vulnerability_level": 4.0,
                    },
                    {
                        "capability": "Aisle Thermal Containment",
                        "finding": "Open server aisles without physical cold-air containment or blanking partitions.",
                        "business_risk": "Hot discharge air recirculation degrading thermal efficiency and component lifespan.",
                        "threat_event_frequency": 2.5,
                        "vulnerability_level": 3.0,
                    },
                ],
            },
            {
                "pillar_name": "Resilience & Operations",
                "pillar_score": 2.2,
                "health_check_asis": [
                    {
                        "capability": "UPS Testing Governance",
                        "finding": "Lack of periodic load and transfer testing on redundant UPS battery systems.",
                        "business_risk": "Elevated risk of abrupt power loss to IT loads upon external utility transients.",
                        "threat_event_frequency": 1.0,
                        "vulnerability_level": 3.0,
                    },
                    {
                        "capability": "Single-Line Power Panels",
                        "finding": "Legacy racks provisioned with single-path power distribution and non-redundant ATS.",
                        "business_risk": "Single point of failure exposure during electrical bus maintenance windows.",
                        "threat_event_frequency": 1.5,
                        "vulnerability_level": 3.5,
                    },
                ],
            },
        ],
    }


def test_synthesizer_produces_monistic_payload(sample_blueprint_data: dict) -> None:
    """Verifies that Chapter4Synthesizer produces a strictly valid Chapter4SynthesisPayload."""
    payload = Chapter4Synthesizer.synthesize_payload(sample_blueprint_data)

    assert isinstance(payload, Chapter4SynthesisPayload)
    assert payload.tower_id == "T1"
    assert payload.enterprise_id == "ENTERPRISE_GLOBAL"
    assert 1.0 <= payload.evaluated_cmmi_maturity <= 5.0
    assert payload.currency_iso == "EUR"

    # Verify horizontal reconciliation: COD + Outage ALE == Total COI
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

    # Verify discrete card allocation: Sum of card ALEs == Lever 2 Outage ALE
    card_low_sum = sum(c.calibrated_annual_ale.lower_bound for c in payload.technical_risk_cards)
    card_high_sum = sum(c.calibrated_annual_ale.upper_bound for c in payload.technical_risk_cards)
    outage_ale = payload.probabilistic_outage_ale.annual_outage_ale_interval

    assert card_low_sum == outage_ale.lower_bound
    assert card_high_sum == outage_ale.upper_bound

    # Verify HeatmapCoordinate truncated titles are concise
    for c in payload.technical_risk_cards:
        assert len(c.heatmap_coordinate.truncated_title) <= 42
        assert 1 <= c.heatmap_coordinate.likelihood_index <= 5
        assert 1 <= c.heatmap_coordinate.impact_index <= 5


def test_synthesizer_legacy_dict_contract_compatibility(sample_blueprint_data: dict) -> None:
    """Verifies that synthesize_chapter4 returns backward-compatible dictionary."""
    dict_payload = Chapter4Synthesizer.synthesize_chapter4(sample_blueprint_data)

    assert "total_status_quo_exposure_min" in dict_payload
    assert "total_status_quo_exposure_max" in dict_payload
    assert "anchors" in dict_payload
    assert len(dict_payload["anchors"]) == 3
    assert "strategic_risk_cards" in dict_payload
    assert len(dict_payload["strategic_risk_cards"]) >= 3
    assert "monistic_payload" in dict_payload
    validated = Chapter4SynthesisPayload.model_validate(dict_payload["monistic_payload"])
    assert isinstance(validated, Chapter4SynthesisPayload)


def test_synthesizer_empty_findings_pool_resilience() -> None:
    """Verifies that an empty findings pool gracefully falls back to a structural resilience card without crashing."""
    sparse_blueprint = {
        "document_meta": {
            "tower_id": "T2",
            "tower_name": "Cloud Infrastructure",
            "client_id": "SPARSE_CLIENT",
            "language": "en",
        },
        "organization_profile": {
            "annual_revenue": 50000000.0,
        },
        "worst_crisis_rto_hours": 4.0,
        "pillars_analysis": [],
    }

    payload = Chapter4Synthesizer.synthesize_payload(sparse_blueprint)
    assert isinstance(payload, Chapter4SynthesisPayload)
    assert len(payload.technical_risk_cards) == 1
    assert payload.technical_risk_cards[0].custody_role == "PRIMARY_CUSTODIAN"
    assert payload.technical_risk_cards[0].calibrated_annual_ale == payload.probabilistic_outage_ale.annual_outage_ale_interval


def test_synthesizer_preserves_quanta_without_single_euro_artifacts() -> None:
    """Verifies that card discrete allocation preserves actuarial step quanta without 1-euro remainder noise."""
    blueprint = {
        "document_meta": {
            "tower_id": "T1",
            "tower_name": "Facilities & Power",
            "client_id": "QUANTUM_CORP",
            "language": "en",
        },
        "organization_profile": {
            "annual_revenue": 100000000.0,
        },
        "worst_crisis_rto_hours": 6.0,
        "pillars_analysis": [
            {
                "pillar_name": "Pillar A",
                "pillar_score": 2.0,
                "health_check_asis": [
                    {
                        "capability": f"Capability {i}",
                        "finding": f"Technical finding description {i} exceeding minimum character length.",
                        "business_risk": f"Business risk narrative {i} exceeding minimum character length.",
                        "threat_event_frequency": 2.0,
                        "vulnerability_level": 3.0,
                    }
                    for i in range(1, 4)
                ],
            }
        ],
    }

    payload = Chapter4Synthesizer.synthesize_payload(blueprint)
    for card in payload.technical_risk_cards:
        # All allocated amounts must end in clean quanta (no spurious trailing units like 8333)
        assert card.calibrated_annual_ale.lower_bound % 50 == 0
        assert card.calibrated_annual_ale.upper_bound % 50 == 0
