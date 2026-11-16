"""
Unit Test Suite for GATE-30.1: Closed-World Entity Symbol Table Confinement.

Validates the Pydantic @model_validator in HealthCheckAsIs:
1. Rejects unaccredited physical protocols or proprietary vendor names smuggled into
   free-form narrative strings when operating in CAPABILITY_GOVERNANCE_ONLY mode.
2. Permits pure governance, procedural, and capability maturity assertions.
3. Permits entities when explicitly accredited via ValidationInfo context pointers.
"""

import pytest
from pydantic import ValidationError

from assessment_engine.domain.schemas.blueprint import (
    HealthCheckAsIs,
    EpistemicContaminationError,
)


def test_gate_30_1_rejects_smuggled_cctv_in_governance_mode():
    """GATE-30.1: Rejects unaccredited CCTV/NVR in governance finding."""
    with pytest.raises(ValidationError) as exc_info:
        HealthCheckAsIs(
            target_state="Third-Party Vendor Management",
            finding="El sistema de videovigilancia CCTV cuenta con ángulos muertos y NVR autónomos.",
            business_risk="Riesgo de intrusión en salas técnicas sin trazabilidad forense.",
            literal_evidence="Score 1.0 in T1.P3.K3",
            threat_event_frequency=3,
            vulnerability_level=3,
            loss_magnitude=3,
            epistemic_state="CAPABILITY_GOVERNANCE_ONLY",
        )
    assert "GATE-30.1 BREACH" in str(exc_info.value)
    assert any(t in str(exc_info.value).lower() for t in ["cctv", "nvr"])


def test_gate_30_1_rejects_smuggled_storage_features():
    """GATE-30.1: Rejects NetApp CSI / WORM smuggled into survey-only findings."""
    with pytest.raises(ValidationError) as exc_info:
        HealthCheckAsIs(
            target_state="Storage Performance & Immutability",
            finding="La infraestructura requiere configuración de CSI de NetApp y políticas WORM.",
            business_risk="Riesgo de alteración maliciosa de datos.",
            threat_event_frequency=2,
            vulnerability_level=3,
            loss_magnitude=3,
            fragment_id=None,  # No empirical fragment
            literal_evidence=None,
        )
    assert "GATE-30.1 BREACH" in str(exc_info.value)


def test_gate_30_1_permits_clean_governance_maturity_findings():
    """GATE-30.1: Permits clean, vendor-neutral process governance maturity findings."""
    finding = HealthCheckAsIs(
        target_state="Vendor Governance & Technical Room Access",
        finding="Madurez inicial en cobertura y formalización de registros de acceso y control de áreas técnicas.",
        business_risk="Riesgo de falta de supervisión y gobernanza en actividades de terceros.",
        literal_evidence="Score 1.0 in T1.P3.K3",
        threat_event_frequency=3,
        vulnerability_level=3,
        loss_magnitude=3,
        epistemic_state="CAPABILITY_GOVERNANCE_ONLY",
    )
    assert finding.target_state == "Vendor Governance & Technical Room Access"
    assert "Madurez inicial" in finding.risk_observed


def test_gate_30_1_permits_authorized_entities_via_context():
    """GATE-30.1: Permits an entity if explicitly authorized via symbol table context."""
    finding = HealthCheckAsIs.model_validate(
        {
            "target_state": "Storage Orchestration",
            "finding": "Despliegue verificado del controlador CSI de NetApp en clúster auditado.",
            "business_risk": "Riesgo residual de orquestación.",
            "threat_event_frequency": 2,
            "vulnerability_level": 2,
            "loss_magnitude": 2,
            "epistemic_state": "CAPABILITY_GOVERNANCE_ONLY",
        },
        context={"authorized_entities": ["csi de netapp"]},
    )
    assert "CSI de NetApp" in finding.risk_observed
