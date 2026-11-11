"""Unit test suite for PolymorphicFindingClassifier & AdditiveLossDecomposition (SR 11-7)."""

from __future__ import annotations

from decimal import Decimal
import pytest

from assessment_engine.domain.actuarial.finding_archetype_resolver import (
    AdditiveLossDecomposition,
    EpistemicEvidenceState,
    FindingLossPhysics,
    FindingPhysicsProfile,
    PolymorphicFindingClassifier,
)
from assessment_engine.domain.taxonomy.archetype_registry import LossArchetypeType


def test_classify_finops_idle_vm_resource_waste() -> None:
    """Verifies that idle/orphaned VMs are classified as FINOPS_RESOURCE_WASTE with 0.0h downtime."""
    hc = {
        "id": "RVS07",
        "capability": "Lifecycle & VM Decommissioning",
        "finding": "Ausencia de politicas de desmantelamiento de maquinas virtuales inactivas (zombie VMs) en cluster SimpliVity.",
        "business_risk": "Consumo improductivo de capacidad de almacenamiento y memoria RAM.",
    }
    profile = PolymorphicFindingClassifier.classify_finding(hc, tower_id="T2")

    assert isinstance(profile, FindingPhysicsProfile)
    assert profile.loss_physics == FindingLossPhysics.FINOPS_RESOURCE_WASTE
    assert profile.canonical_archetype == LossArchetypeType.CAPITAL_INEFFICIENCY
    assert profile.allows_downtime_burn is False
    assert profile.default_rto_hours == 0.0
    assert profile.max_euler_ale_discount_pct == 0.0  # Deterministic OpEx cannot be diversified


def test_classify_engineering_velocity_iac_friction() -> None:
    """Verifies that missing Terraform/IaC or manual USB toil is classified as ENGINEERING_VELOCITY_FRICTION."""
    hc = {
        "id": "RVS08",
        "capability": "Infrastructure as Code",
        "finding": "Predominio de tareas manuales de configuracion sin plantillas Terraform o Ansible.",
        "business_risk": "Lentitud operativa y deriva de configuracion en despliegues.",
    }
    profile = PolymorphicFindingClassifier.classify_finding(hc, tower_id="T2")

    assert profile.loss_physics == FindingLossPhysics.ENGINEERING_VELOCITY_FRICTION
    assert profile.canonical_archetype == LossArchetypeType.PRODUCTIVITY_TOIL
    assert profile.allows_downtime_burn is False
    assert profile.default_rto_hours == 0.0
    assert profile.max_euler_ale_discount_pct == 0.10


def test_classify_asset_obsolescence_eol() -> None:
    """Verifies that EoL operating systems (CentOS 5, Oracle 10g) are classified as ASSET_OBSOLESCENCE."""
    hc = {
        "id": "RVS04",
        "capability": "OS Lifecycle",
        "finding": "Presencia confirmada de servidores CentOS 5 y CentOS 6 obsoletos sin soporte de fabricante.",
        "business_risk": "Vulnerabilidades no parcheadas y riesgo de explotacion remota.",
    }
    profile = PolymorphicFindingClassifier.classify_finding(hc, tower_id="T6")

    assert profile.loss_physics == FindingLossPhysics.ASSET_OBSOLESCENCE_AND_INTEGRITY
    assert profile.allows_downtime_burn is True
    assert profile.default_rto_hours == 4.0  # Scoped workload recovery, not 14h full plant blackout


def test_classify_regulatory_and_breach() -> None:
    """Verifies that shared root accounts or unencrypted PII are classified as REGULATORY_AND_BREACH."""
    hc = {
        "id": "RVS02",
        "capability": "PAM & Identity",
        "finding": "Operacion mediante cuentas root compartidas y credenciales administrativas sin boveda PAM.",
        "business_risk": "Incumplimiento de NIS2 y riesgo de exfiltracion de datos.",
    }
    profile = PolymorphicFindingClassifier.classify_finding(hc, tower_id="T6")

    assert profile.loss_physics == FindingLossPhysics.REGULATORY_AND_BREACH
    assert profile.canonical_archetype == LossArchetypeType.REGULATORY_AND_BREACH
    assert profile.allows_downtime_burn is False
    assert profile.default_rto_hours == 0.0


def test_classify_true_availability_outage_spof() -> None:
    """Verifies that physical SPOFs or power outages remain classified as AVAILABILITY_OUTAGE."""
    hc = {
        "id": "RVS01",
        "capability": "Power Continuity",
        "finding": "Punto unico de fallo (SPOF) en la linea de baja tension municipal compartida entre CPDs.",
        "business_risk": "Parada de planta completa y parada de expedicion de camiones.",
    }
    profile = PolymorphicFindingClassifier.classify_finding(hc, tower_id="T1")

    assert profile.loss_physics == FindingLossPhysics.AVAILABILITY_OUTAGE
    assert profile.canonical_archetype == LossArchetypeType.AVAILABILITY_OUTAGE
    assert profile.allows_downtime_burn is True
    assert profile.default_rto_hours == 8.0


def test_quarantine_survey_inferred_boilerplate() -> None:
    """Verifies that generic questionnaire fallback text is quarantined as SURVEY_INFERRED_BOILERPLATE."""
    hc = {
        "id": "RVS02",
        "capability": "HVAC Cooling Resiliency",
        "finding": "Carencia de controles operativos formalizados y falta de supervisi\u00f3n continua en Climatizaci\u00f3n.",
        "business_risk": "Carencia de controles operativos formalizados y falta de supervisi\u00f3n continua en HVAC.",
    }
    profile = PolymorphicFindingClassifier.classify_finding(hc, tower_id="T1")

    assert profile.epistemic_state == EpistemicEvidenceState.SURVEY_INFERRED_BOILERPLATE


def test_additive_loss_decomposition_conservation_success() -> None:
    """Verifies that valid AdditiveLossDecomposition validates exact conservation."""
    decomp = AdditiveLossDecomposition(
        currency_iso="EUR",
        mean_lef=1.5,
        expected_downtime_loss=25000,
        expected_replacement_cost=10000,
        expected_secondary_loss=5000,
        gross_mean_sle=40000,  # 25k + 10k + 5k == 40k
        gross_standalone_ale=60000,
        euler_overlap_adjustment_ale=-10000,  # -10k <= 0
        net_allocated_ale=50000,  # 60k - 10k == 50k
        euler_discount_pct=Decimal("16.7"),
        gross_standalone_p90=110000,
        net_allocated_p90=95000,
        loss_physics="AVAILABILITY_OUTAGE",
        epistemic_state="VERIFIED_EMPIRICAL",
    )
    # Should not raise
    decomp.validate_conservation()
    d = decomp.to_dict()
    assert d["gross_mean_sle"] == 40000
    assert d["net_allocated_ale"] == 50000


def test_additive_loss_decomposition_conservation_failure() -> None:
    """Verifies that an inconsistent AdditiveLossDecomposition raises ValueError."""
    decomp = AdditiveLossDecomposition(
        currency_iso="EUR",
        mean_lef=1.0,
        expected_downtime_loss=20000,
        expected_replacement_cost=10000,
        expected_secondary_loss=5000,
        gross_mean_sle=50000,  # 20k + 10k + 5k = 35k != 50k (Violation!)
        gross_standalone_ale=50000,
        euler_overlap_adjustment_ale=0,
        net_allocated_ale=50000,
        euler_discount_pct=Decimal("0.0"),
        gross_standalone_p90=80000,
        net_allocated_p90=80000,
        loss_physics="AVAILABILITY_OUTAGE",
        epistemic_state="VERIFIED_EMPIRICAL",
    )
    with pytest.raises(ValueError, match="SLE Additive Conservation Violation"):
        decomp.validate_conservation()
