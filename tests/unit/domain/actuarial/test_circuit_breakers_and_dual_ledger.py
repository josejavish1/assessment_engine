"""Unit test suite for Actuarial Pre-Flight Circuit Breakers and Dual-Ledger Architecture (SR 11-7)."""

from __future__ import annotations

from decimal import Decimal
import pytest

from assessment_engine.domain.actuarial.finding_archetype_resolver import (
    AdditiveLossDecomposition,
    FindingLossPhysics,
    PolymorphicFindingClassifier,
)
from assessment_engine.domain.actuarial.input_resolver import ActuarialInputResolver
from assessment_engine.domain.actuarial.euler_allocator import EulerPortfolioAllocator
from assessment_engine.domain.bayesian_fair_copula_engine import OperationalZone
from assessment_engine.domain.taxonomy.archetype_registry import LossArchetypeType


@pytest.fixture
def standard_operational_zone() -> OperationalZone:
    return OperationalZone(
        zone_id="ZONE_TEST",
        hourly_burn_rate=13061.29,
        max_annual_outage_hours=72.0,
    )


def test_non_prod_zero_outage_circuit_breaker(standard_operational_zone: OperationalZone) -> None:
    """Verifies that non-production/lab environments mandate 0.0h downtime and 0.0 blast radius."""
    hc = {
        "id": "HC-DEV-01",
        "title": "Kubernetes Experimental Lab Container Ingress",
        "finding": "Adopcion incipiente de contenedores en entorno de laboratorio y pruebas sin ingress formal.",
        "environment": "LAB",
        "recovery_time_hours": 14.0,  # Erroneous macro default in payload
    }
    inputs, telemetry, _ = ActuarialInputResolver.resolve_finding_inputs(
        hc=hc,
        tower_id="T2",
        pillar_cmmi=2.0,
        zone=standard_operational_zone,
        archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
        currency_code="EUR",
        annual_revenue=1144000000.0,
        annual_it_opex=18000000.0,
        hourly_wage=55.0,
    )
    # Circuit breaker must force RTO to 0.0 and blast radius to 0.0
    assert float(inputs.rto_hours_mode.effective_value) == 0.0
    assert float(inputs.blast_radius_alpha.effective_value) == 0.0


def test_internal_task_cap_circuit_breaker(standard_operational_zone: OperationalZone) -> None:
    """Verifies that internal sysadmin tasks (like deleting orphaned VMs) cannot claim consulting fees."""
    hc = {
        "id": "HC-VM-01",
        "title": "Orphaned VM Decommissioning",
        "finding": "Ausencia de desmantelamiento de maquinas virtuales inactivas en cluster local.",
        "remediation_type": "INTERNAL_SYSADMIN_CLEANUP",
        "direct_replacement_cost": 30000.0,  # Unacceptable Big-4 fee in payload
    }
    inputs, telemetry, _ = ActuarialInputResolver.resolve_finding_inputs(
        hc=hc,
        tower_id="T2",
        pillar_cmmi=2.0,
        zone=standard_operational_zone,
        archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
        currency_code="EUR",
        annual_revenue=1144000000.0,
        annual_it_opex=18000000.0,
        hourly_wage=55.0,
    )
    # Circuit breaker must cap direct replacement to internal labor (e.g. <= 40h * wage)
    assert float(inputs.direct_replacement_cost.effective_value) <= (40.0 * 55.0)


def test_tier_a_operational_friction_circuit_breaker(standard_operational_zone: OperationalZone) -> None:
    """Verifies that local maintenance (like unrotated log files filling disk) is capped at 0.5h."""
    hc = {
        "id": "HC-LOG-01",
        "title": "Linux Root Partition Log Saturation",
        "finding": "Saturacion de espacio en disco por ficheros de log sin rotar alertando a 1GB.",
        "recovery_time_hours": 8.0,  # Erroneous 8-hour factory outage
    }
    inputs, telemetry, _ = ActuarialInputResolver.resolve_finding_inputs(
        hc=hc,
        tower_id="T4",
        pillar_cmmi=2.0,
        zone=standard_operational_zone,
        archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
        currency_code="EUR",
        annual_revenue=1144000000.0,
        annual_it_opex=18000000.0,
        hourly_wage=55.0,
    )
    # Tier A friction: RTO capped at 0.5h (30 min max)
    assert float(inputs.rto_hours_mode.effective_value) <= 0.5
    assert float(inputs.blast_radius_alpha.effective_value) <= 0.05


def test_vulnerability_control_gap_circuit_breaker(standard_operational_zone: OperationalZone) -> None:
    """Verifies that security control gaps (NAC, PAM, DRP docs) have 0.0h primary downtime."""
    for finding_title in [
        "Network Access Control (NAC) 802.1X Deployment",
        "Privileged Access Management (PAM) Shared Root Credentials",
        "Disaster Recovery (DRP) Documentation and Runbook Governance",
    ]:
        hc = {
            "id": "HC-CTRL-01",
            "title": finding_title,
            "finding": f"Carencia de controles formales de {finding_title}.",
            "recovery_time_hours": 8.0,  # Erroneous primary downtime in payload
        }
        inputs, telemetry, _ = ActuarialInputResolver.resolve_finding_inputs(
            hc=hc,
            tower_id="T6",
            pillar_cmmi=2.0,
            zone=standard_operational_zone,
            archetype=LossArchetypeType.REGULATORY_AND_BREACH,
            currency_code="EUR",
            annual_revenue=1144000000.0,
            annual_it_opex=18000000.0,
            hourly_wage=55.0,
        )
        assert float(inputs.rto_hours_mode.effective_value) == 0.0


def test_fleet_volume_multiplier_toil_calculation() -> None:
    """Verifies that fleet toil scales by volume (N_fleet * hours * wage) in Ledger B with 0% Euler discount."""
    findings = [
        {
            "id": "RVS-TOIL-01",
            "loss_physics": "ENGINEERING_VELOCITY_FRICTION",
            "is_deterministic": True,
            "ledger_type": "LEDGER_B_DETERMINISTIC_OPEX",
            "fleet_volume": 350,  # 350 laptops
            "unit_toil_hours": 3.5,  # 3.5 hours per laptop
            "hourly_wage": 45.0,
            "gross_mean_sle": 158,  # 3.5h * 45 €/h
            "mean_lef": 350.0,
            "gross_standalone_ale": 55125,  # 350 * 3.5 * 45 = 55,125 €
        }
    ]
    decomps = EulerPortfolioAllocator.allocate_findings_within_domain(
        findings_raw=findings,
        currency_iso="EUR",
    )
    decomp = decomps["RVS-TOIL-01"]
    assert decomp.gross_standalone_ale == 55125
    assert decomp.net_allocated_ale == 55125  # Zero Euler diversification discount
    assert decomp.euler_overlap_adjustment_ale == 0
    assert float(decomp.euler_discount_pct) == 0.0


def test_dual_ledger_segregation_contract() -> None:
    """Verifies that AdditiveLossDecomposition supports Ledger A and Ledger B differentiation."""
    stochastic_decomp = AdditiveLossDecomposition(
        currency_iso="EUR",
        mean_lef=0.5,
        expected_downtime_loss=40000,
        expected_replacement_cost=10000,
        expected_secondary_loss=0,
        gross_mean_sle=50000,
        gross_standalone_ale=25000,
        euler_overlap_adjustment_ale=-5000,
        net_allocated_ale=20000,
        euler_discount_pct=Decimal("20.0"),
        gross_standalone_p90=60000,
        net_allocated_p90=50000,
        loss_physics="AVAILABILITY_OUTAGE",
        epistemic_state="VERIFIED_EMPIRICAL",
        ledger_type="LEDGER_A_STOCHASTIC",
        is_deterministic=False,
    )
    stochastic_decomp.validate_conservation()
    assert stochastic_decomp.ledger_type == "LEDGER_A_STOCHASTIC"
    assert stochastic_decomp.is_deterministic is False

    deterministic_decomp = AdditiveLossDecomposition(
        currency_iso="EUR",
        mean_lef=1.0,
        expected_downtime_loss=0,
        expected_replacement_cost=450000,
        expected_secondary_loss=0,
        gross_mean_sle=450000,
        gross_standalone_ale=450000,
        euler_overlap_adjustment_ale=0,  # Must be 0 for deterministic OpEx
        net_allocated_ale=450000,
        euler_discount_pct=Decimal("0.0"),
        gross_standalone_p90=450000,
        net_allocated_p90=450000,
        loss_physics="FINOPS_RESOURCE_WASTE",
        epistemic_state="VERIFIED_EMPIRICAL",
        ledger_type="LEDGER_B_DETERMINISTIC_OPEX",
        is_deterministic=True,
    )
    deterministic_decomp.validate_conservation()
    assert deterministic_decomp.ledger_type == "LEDGER_B_DETERMINISTIC_OPEX"
    assert deterministic_decomp.is_deterministic is True
    assert deterministic_decomp.euler_overlap_adjustment_ale == 0
