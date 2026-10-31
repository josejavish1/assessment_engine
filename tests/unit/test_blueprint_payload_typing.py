# golden-path: ignore
"""Unit tests verifying strong typing contracts and BlueprintPayload domain validations."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from assessment_engine.application.run_tower_blueprint_engine import (
    _calculate_total_fair_ale,
    get_default_blueprint_payload,
)
from assessment_engine.domain.schemas.blueprint import (
    BlueprintDocumentMeta,
    BlueprintPayload,
    CrossCapabilitiesAnalysis,
    ExecutiveSnapshot,
    HealthCheckAsIs,
    PillarBlueprintDraft,
    TargetArchitectureToBe,
)


def test_default_blueprint_payload_structure() -> None:
    payload_dict = get_default_blueprint_payload(
        client_name="Acme Corp",
        tower_name="Cloud Security",
        tower_id="T2",
        intel_data={"financial_tier": "Tier 1", "transformation_horizon": "2026-2028"},
        doc_lang="en",
    )

    assert isinstance(payload_dict, dict)
    assert payload_dict["document_meta"]["client_name"] == "Acme Corp"
    assert payload_dict["document_meta"]["tower_code"] == "T2"
    assert len(payload_dict["design_principles"]) >= 3


def test_calculate_total_fair_ale_with_typed_blueprint_payload() -> None:
    doc_meta = BlueprintDocumentMeta(
        client_name="Global Enterprise",
        tower_name="Infrastructure",
        tower_code="T1",
        financial_tier="Tier 1",
        transformation_horizon="Strategic",
    )
    exec_snap = ExecutiveSnapshot(
        bottom_line="Target architecture achieved.",
        decisions=["Adopt Sovereign Cloud"],
        cost_of_inaction="Severe regulatory penalties",
        structural_risks=["Legacy Single Points of Failure"],
        business_impact="Critical revenue continuity",
        operational_benefits=["50% reduction in MTTR"],
        transformation_complexity="Medium",
    )
    cross_cap = CrossCapabilitiesAnalysis(
        common_deficiency_patterns=["Manual deployments"],
        transformation_paradigm="GitOps infrastructure as code",
        critical_technical_debt="Unpatched hypervisors",
    )
    finding = HealthCheckAsIs(
        capability="Network Segmentation",
        finding="Flat network without zero trust zones",
        business_risk="Lateral movement vector",
        fair_ale_score=150000.0,
        threat_event_frequency=2.0,
        vulnerability_level=3.0,
        loss_magnitude=4.0,
    )
    pillar = PillarBlueprintDraft(
        thought_process="Analysis complete",
        pillar_id="T1.P1",
        pillar_name="Network Architecture",
        score=2.0,
        target_score=4.0,
        asis_architecture_description="Flat enterprise network with legacy core switches.",
        health_check_asis=[finding],
        target_architecture_tobe=TargetArchitectureToBe(
            key_paradigm="Zero Trust Network Access",
            vision="Zero Trust Enterprise Architecture",
            architectural_state_summary="Software-defined microsegmentation deployed across all VPCs.",
        ),
        projects_todo=[],
    )

    # Invariant: Both canonical English and legacy aliases must resolve
    assert pillar.pillar_id == "T1.P1"
    assert pillar.pilar_id == "T1.P1"
    assert pillar.pillar_name == "Network Architecture"
    assert pillar.pilar_name == "Network Architecture"

    typed_payload = BlueprintPayload(
        document_meta=doc_meta,
        executive_snapshot=exec_snap,
        design_principles=[
            "Zero Trust Architecture",
            "Infrastructure as Code",
            "Automated Observability",
        ],
        cross_capabilities_analysis=cross_cap,
        roadmap=[],
        external_dependencies=[],
        pillars_analysis=[pillar],
        total_fair_ale=150000.0,
    )

    # Test calculation with typed instance
    calc_ale = _calculate_total_fair_ale(typed_payload)
    assert calc_ale == 150000.0

    # Test fallback extraction when total_fair_ale is None
    typed_payload_none_ale = typed_payload.model_copy(update={"total_fair_ale": None})
    calc_fallback = _calculate_total_fair_ale(typed_payload_none_ale)
    assert calc_fallback == 150000.0
