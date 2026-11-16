"""
Unit Test Suite for GATE-31.2: Dynamic Output Schema Polymorphism.

Validates the implementation of Phase 31.2:
1. When epistemic_regime == REGIME_ZERO_EVIDENCE or SPARSE_GOVERNANCE, the Pydantic schema
   must reject technical specificity implementation details, enforcing the AbstractCapabilityAnalysis branch.
2. When epistemic_regime == REGIME_EMPIRICAL_CONCRETE, the schema permits technical specifics
   via EmpiricalTechnicalAnalysis, but requires chunk bindings.
"""

import pytest
from pydantic import ValidationError

from assessment_engine.domain.schemas.blueprint import (
    PillarBlueprintDraft,
    EpistemicContaminationError,
)


def test_gate_31_2_polymorphic_rejection_of_ungrounded_tech():
    """GATE-31.2: PillarBlueprintDraft rejects ungrounded physical protocols in ZERO_EVIDENCE regime."""
    # Attempting to sneak BGP and VLANs into a zero-evidence pillar draft
    with pytest.raises(ValidationError) as exc_info:
        PillarBlueprintDraft.model_validate({
            "thought_process": "Analyzing network.",
            "pilar_id": "T3.P1",
            "pilar_name": "Network Architecture",
            "epistemic_regime": "REGIME_ZERO_EVIDENCE",
            "asis_architecture_description": "La red está configurada con BGP y múltiples VLANs.",
            "health_check_asis": [],
            "target_architecture_tobe": {
                "vision": "SD-WAN Vision",
                "architecture_description": "Migrar a SD-WAN",
                "recommended_technologies": [],
                "target_maturity_level": 4,
                "strategic_directive": "Cloud-First",
            },
            "projects_todo": [],
        })

    assert "GATE-31.2 BREACH" in str(exc_info.value) or "GATE-30.1 BREACH" in str(exc_info.value)
    assert "bgp" in str(exc_info.value).lower() or "vlan" in str(exc_info.value).lower()


def test_gate_31_2_permits_abstract_capability_governance():
    """GATE-31.2: PillarBlueprintDraft allows pure capability governance descriptions."""
    draft = PillarBlueprintDraft.model_validate({
        "thought_process": "Analyzing network governance.",
        "pilar_id": "T3.P1",
        "pilar_name": "Network Architecture",
        "epistemic_regime": "REGIME_ZERO_EVIDENCE",
        "asis_architecture_description": "Madurez inicial en la estandarización de políticas de segmentación de red. La configuración física y los protocolos permanecen pendientes de contraste pericial.",
        "health_check_asis": [],
        "target_architecture_tobe": {
            "vision": "Estandarización Vision",
            "architecture_description": "Estandarización de políticas de red",
            "recommended_technologies": [],
            "target_maturity_level": 4,
            "strategic_directive": "Cloud-First",
        },
        "projects_todo": [],
    })
    assert draft.epistemic_regime == "REGIME_ZERO_EVIDENCE"
    assert "Madurez inicial" in draft.asis_architecture_description
