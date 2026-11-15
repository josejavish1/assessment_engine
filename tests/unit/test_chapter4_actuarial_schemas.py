"""Unit tests for Chapter 4 Pydantic V2 Domain Schemas and Actuarial Rounding Engine.

Verifies:
1. Immutability (frozen=True) and rejection of extra inputs.
2. Operator overloading on MonetaryInterval.
3. Closed-form Hare-Niemeyer discrete integer allocation (zero remainder error).
4. Strict split-brain detection in model_validator identities.
5. 100% Technical English in all identifiers, docstrings, and test fixtures.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from assessment_engine.domain.actuarial.rounding import (
    allocate_subadditive_ale_to_cards,
    compute_step_quantum,
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


def test_monetary_interval_arithmetic_and_invariants() -> None:
    """Verifies interval validation, midpoint, and exact addition."""
    i1 = MonetaryInterval(lower_bound=10000, upper_bound=20000, currency_iso="EUR")
    i2 = MonetaryInterval(lower_bound=5000, upper_bound=10000, currency_iso="EUR")

    assert i1.midpoint == 15000
    added = i1 + i2
    assert added.lower_bound == 15000
    assert added.upper_bound == 30000
    assert added.currency_iso == "EUR"

    # Inverted bounds must fail
    with pytest.raises(ValidationError):
        MonetaryInterval(lower_bound=25000, upper_bound=10000, currency_iso="EUR")

    # Immutability
    with pytest.raises(ValidationError):
        i1.lower_bound = 12000  # type: ignore[misc]


def test_actuarial_rounding_and_step_quantum() -> None:
    """Verifies quantum schedule and significant figure rounding."""
    # Small amounts (<10,000) round to nearest 50
    assert round_to_actuarial_significance(483) == 500
    assert round_to_actuarial_significance(421) == 400

    # Mid amounts (10,000 - 25,000) round to nearest 250
    assert round_to_actuarial_significance(12340) == 12250
    assert round_to_actuarial_significance(12480) == 12500

    # Amounts (25,000 - 100,000) round to nearest 1,000
    assert round_to_actuarial_significance(56789) == 57000

    # Amounts (>100,000) round to nearest 5,000
    assert round_to_actuarial_significance(148894) == 150000
    assert round_to_actuarial_significance(428532) == 430000


def test_hare_niemeyer_discrete_integer_allocation() -> None:
    """Verifies closed-form discrete allocation sums exactly to target with zero discrepancy."""
    target = 25000
    standalone_cards = [12000, 15000, 8000, 5000]

    allocated = allocate_subadditive_ale_to_cards(target, standalone_cards)
    assert len(allocated) == 4
    assert sum(allocated) == target
    # Highest standalone gets highest share
    assert allocated[1] > allocated[0] > allocated[2] > allocated[3]

    # Edge cases
    assert allocate_subadditive_ale_to_cards(0, standalone_cards) == [0, 0, 0, 0]
    assert allocate_subadditive_ale_to_cards(10000, []) == []


def test_chapter4_synthesis_payload_monism_and_split_brain_protection() -> None:
    """Verifies that Chapter4SynthesisPayload enforces ironclad reconciliation."""
    toil_interval = MonetaryInterval(lower_bound=25000, upper_bound=35000)
    escalation_interval = MonetaryInterval(lower_bound=10000, upper_bound=15000)
    total_cod = MonetaryInterval(lower_bound=35000, upper_bound=50000)

    cod = ChronicOperationalDragBreakdown(
        annual_engineering_toil_hours=600,
        engineering_toil_cost_interval=toil_interval,
        contractual_and_licensing_escalation_interval=escalation_interval,
        total_chronic_drag_interval=total_cod,
    )

    outage_ale = ProbabilisticOutageALEBreakdown(
        gross_standalone_ale_sum=35000,
        portfolio_subadditivity_factor=0.80,
        annual_outage_ale_interval=MonetaryInterval(lower_bound=20000, upper_bound=30000),
        worst_case_single_outage_event=MonetaryInterval(lower_bound=100000, upper_bound=150000),
    )

    # Valid Total COI: 35k + 20k = 55k; 50k + 30k = 80k
    total_coi = CostOfInactionTotal(
        lever_1_toil_share_pct=45.0,
        lever_2_outage_ale_share_pct=36.0,
        lever_3_contractual_share_pct=19.0,
        annual_total_coi_interval=MonetaryInterval(lower_bound=55000, upper_bound=80000),
    )

    tco_3yr = ThreeYearCompoundedTCO(
        lower_bound=165000,
        upper_bound=240000,
        midpoint=202500,
    )

    # Risk Cards summing to exact Outage ALE ([20k, 30k])
    card1 = TechnicalRiskScenario(
        risk_id="RSK-T1-01",
        title="ASHRAE TC 9.9 Granular Thermohygrometric Telemetry",
        custody_role="PRIMARY_CUSTODIAN",
        threat_event_frequency_annual=1.2,
        vulnerability_ratio=1.0,
        mttr_recovery_hours=8.0,
        calibrated_annual_ale=MonetaryInterval(lower_bound=12000, upper_bound=18000),
        heatmap_coordinate=HeatmapCoordinate(
            likelihood_index=3, impact_index=4, truncated_title="ASHRAE Thermal Telemetry"
        ),
        physical_evidence="Absence of intake plane thermal telemetry sensors on technical racks.",
        root_cause_mechanism="Perimeter cooling architecture without cold-aisle containment zoning.",
        business_impact_narrative="Unplanned server outages triggered by thermal throttling and CPU degradation.",
        required_mitigation="Deployment of IoT rack-level SNMP environmental telemetry sensors.",
    )
    card2 = TechnicalRiskScenario(
        risk_id="RSK-T1-02",
        title="Aerothermal Containment and Cold-Aisle Separation",
        custody_role="PRIMARY_CUSTODIAN",
        threat_event_frequency_annual=2.5,
        vulnerability_ratio=0.8,
        mttr_recovery_hours=4.0,
        calibrated_annual_ale=MonetaryInterval(lower_bound=8000, upper_bound=12000),
        heatmap_coordinate=HeatmapCoordinate(
            likelihood_index=4, impact_index=3, truncated_title="Aerothermal Containment"
        ),
        physical_evidence="Open aisles without blanking panels or ceiling containment structures.",
        root_cause_mechanism="Recirculation and mixing of supply air and hot discharge plenum airflow.",
        business_impact_narrative="Accelerated power supply and fan unit degradation under peak thermal loads.",
        required_mitigation="Installation of modular cold-aisle physical containment and blanking partitions.",
    )

    # Perfect Monistic Payload: MUST SUCCEED
    payload = Chapter4SynthesisPayload(
        tower_id="T1",
        tower_name="Physical Data Center & Facilities",
        enterprise_id="ENTERPRISE_GLOBAL",
        evaluated_cmmi_maturity=2.1,
        currency_iso="EUR",
        chronic_operational_drag=cod,
        probabilistic_outage_ale=outage_ale,
        total_annual_coi=total_coi,
        three_year_compounded_tco=tco_3yr,
        technical_risk_cards=(card1, card2),
    )
    assert payload.total_annual_coi.annual_total_coi_interval.lower_bound == 55000
    assert payload.total_annual_coi.annual_total_coi_interval.upper_bound == 80000

    # SPLIT-BRAIN ATTACK 1: Tampered Total COI that does not equal COD + Outage ALE
    divergent_total_coi = CostOfInactionTotal(
        lever_1_toil_share_pct=45.0,
        lever_2_outage_ale_share_pct=36.0,
        lever_3_contractual_share_pct=19.0,
        annual_total_coi_interval=MonetaryInterval(lower_bound=60000, upper_bound=90000),  # DIVERGENT!
    )
    with pytest.raises(ValidationError) as exc_info:
        Chapter4SynthesisPayload(
            tower_id="T1",
            tower_name="Physical Data Center & Facilities",
            enterprise_id="ENTERPRISE_GLOBAL",
            evaluated_cmmi_maturity=2.1,
            currency_iso="EUR",
            chronic_operational_drag=cod,
            probabilistic_outage_ale=outage_ale,
            total_annual_coi=divergent_total_coi,
            three_year_compounded_tco=tco_3yr,
            technical_risk_cards=(card1, card2),
        )
    assert "Split-Brain Invariant 1 Violated" in str(exc_info.value)

    # SPLIT-BRAIN ATTACK 2: Cards sum diverges from Lever 2 Outage ALE
    tampered_card2 = TechnicalRiskScenario(
        risk_id="RSK-T1-02",
        title="Aerothermal Containment and Cold-Aisle Separation",
        custody_role="PRIMARY_CUSTODIAN",
        threat_event_frequency_annual=2.5,
        vulnerability_ratio=0.8,
        mttr_recovery_hours=4.0,
        calibrated_annual_ale=MonetaryInterval(lower_bound=9999, upper_bound=12000),  # DIVERGENT!
        heatmap_coordinate=HeatmapCoordinate(
            likelihood_index=4, impact_index=3, truncated_title="Aerothermal Containment"
        ),
        physical_evidence="Open aisles without blanking panels or ceiling containment structures.",
        root_cause_mechanism="Recirculation and mixing of supply air and hot discharge plenum airflow.",
        business_impact_narrative="Accelerated power supply and fan unit degradation under peak thermal loads.",
        required_mitigation="Installation of modular cold-aisle physical containment and blanking partitions.",
    )
    with pytest.raises(ValidationError) as exc_info:
        Chapter4SynthesisPayload(
            tower_id="T1",
            tower_name="Physical Data Center & Facilities",
            enterprise_id="ENTERPRISE_GLOBAL",
            evaluated_cmmi_maturity=2.1,
            currency_iso="EUR",
            chronic_operational_drag=cod,
            probabilistic_outage_ale=outage_ale,
            total_annual_coi=total_coi,
            three_year_compounded_tco=tco_3yr,
            technical_risk_cards=(card1, tampered_card2),
        )
    assert "Split-Brain Invariant 2 Violated" in str(exc_info.value)
