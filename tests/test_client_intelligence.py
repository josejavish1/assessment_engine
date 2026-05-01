from __future__ import annotations

from assessment_engine.schemas.intelligence import ConfidenceAssessment
from assessment_engine.scripts.lib.client_intelligence import (
    build_client_context_packet,
    client_intelligence_to_legacy,
    client_intelligence_to_v2,
    coerce_client_dossier_v2,
    coerce_client_dossier_v3,
    get_target_maturity,
    infer_related_towers,
)


def test_client_intelligence_helpers_support_v2_shape() -> None:
    dossier = {
        "version": "2.0",
        "client_name": "vodafone_demo",
        "profile": {
            "industry": "Telecomunicaciones",
            "financial_tier": "Tier 1",
            "operating_model": "Multipaís",
            "regions": ["EU"],
        },
        "regulatory_frameworks": [
            {"name": "NIS2", "applicability": "high", "sources": [{"source": "src-1"}]}
        ],
        "business_context": {
            "ceo_agenda": {
                "summary": "Simplificar operaciones.",
                "confidence": "high",
                "sources": [{"source": "src-2"}],
            },
            "technological_drivers": [
                {"name": "Observabilidad", "confidence": "high", "sources": []}
            ],
            "osint_footprint": {
                "summary": "Plataformas comunes con heterogeneidad local.",
                "confidence": "medium",
                "sources": [],
            },
            "transformation_horizon": {
                "stage": "H1",
                "label": "Brilliant Basics",
                "rationale": "Hay heterogeneidad operativa.",
                "confidence": "high",
                "sources": [],
            },
            "constraints": [],
        },
        "tower_overrides": {
            "T5": {
                "target_maturity": 3.7,
                "business_criticality": "high",
                "regulatory_pressure": "high",
                "change_urgency": "high",
                "constraints": [],
            }
        },
        "evidence_register": [
            {
                "claim_id": "claim_1",
                "claim": "NIS2 aplica por criticidad.",
                "claim_type": "inference",
                "confidence": "medium",
                "sources": [{"source": "src-3"}],
            }
        ],
    }

    legacy = client_intelligence_to_legacy(dossier)

    assert legacy["industry"] == "Telecomunicaciones"
    assert legacy["financial_tier"] == "Tier 1"
    assert legacy["ceo_agenda"] == "Simplificar operaciones."
    assert legacy["regulatory_frameworks"] == ["NIS2"]
    assert legacy["target_maturity_matrix"]["T5"] == 3.7
    assert get_target_maturity(dossier, "T5") == 3.7


def test_coerce_client_dossier_v2_converts_legacy_shape() -> None:
    legacy = {
        "industry": "Telecomunicaciones",
        "financial_tier": "Tier 1",
        "regulatory_frameworks": ["NIS2"],
        "ceo_agenda": "Simplificar operaciones.",
        "technological_drivers": ["Observabilidad"],
        "osint_footprint": "Plataformas comunes.",
        "transformation_horizon": "Horizonte 1: Brilliant Basics.",
        "target_maturity_matrix": {"T2": 3.9},
        "evidences": ["Fuente pública sobre resiliencia y continuidad DR."],
    }

    dossier = coerce_client_dossier_v2("vodafone_demo", legacy)

    assert dossier["version"] == "2.0"
    assert dossier["profile"]["industry"] == "Telecomunicaciones"
    assert dossier["tower_overrides"]["T2"]["target_maturity"] == 3.9
    assert (
        dossier["business_context"]["ceo_agenda"]["summary"]
        == "Simplificar operaciones."
    )


def test_coerce_client_dossier_v3_builds_richer_context_packet() -> None:
    legacy = {
        "industry": "Telecomunicaciones",
        "financial_tier": "Tier 1",
        "regulatory_frameworks": ["NIS2"],
        "ceo_agenda": "Simplificar operaciones.",
        "technological_drivers": ["Observabilidad end-to-end"],
        "osint_footprint": "Plataformas comunes con heterogeneidad local.",
        "transformation_horizon": "Horizonte 1: Brilliant Basics.",
        "target_maturity_matrix": {"T5": 3.7},
        "evidences": ["Fuente pública"],
        "priority_markets": ["España", "Alemania"],
        "business_lines": ["B2B", "IoT"],
        "active_transformations": ["Consolidación de plataformas"],
        "vendor_dependencies": ["Azure", "Cisco"],
        "recent_incident_signals": ["Interrupciones de servicio de alto impacto"],
    }

    dossier = coerce_client_dossier_v3("vodafone_demo", legacy)
    packet = build_client_context_packet(dossier, tower_id="T5")

    assert dossier["version"] == "3.0"
    assert dossier["metadata"]["schema_version"] == "3.0"
    assert dossier["technology_context"]["vendor_dependencies"] == ["Azure", "Cisco"]
    assert dossier["tower_overrides"]["T5"]["target_maturity"] == 3.7
    assert dossier["tower_overrides"]["T5"]["related_claim_ids"]
    assert len(dossier["claims"]) >= 5
    assert any(
        claim["claim_id"].startswith("vendor_dependency_")
        for claim in dossier["claims"]
    )
    assert any(
        source["source_type"] == "public"
        for claim in dossier["claims"]
        for source in claim["sources"]
    )
    assert packet["profile"]["priority_markets"] == ["España", "Alemania"]
    assert packet["technology_context"]["recent_incident_signals"] == [
        "Interrupciones de servicio de alto impacto"
    ]


def test_infer_related_towers_requires_word_boundaries_for_short_keywords() -> None:
    assert infer_related_towers("Driver modernization for android endpoints") == []
    assert infer_related_towers("Plan de continuidad con DR verificado") == ["T5"]


def test_client_intelligence_to_v2_accepts_v3_confidence_blocks() -> None:
    legacy = {
        "industry": "Telecomunicaciones",
        "financial_tier": "Tier 1",
        "regulatory_frameworks": ["NIS2"],
        "ceo_agenda": "Simplificar operaciones.",
        "technological_drivers": ["Observabilidad end-to-end"],
        "osint_footprint": "Plataformas comunes con heterogeneidad local.",
        "transformation_horizon": "Horizonte 1: Brilliant Basics.",
        "target_maturity_matrix": {"T5": 3.7},
        "evidences": ["Fuente pública"],
    }

    dossier_v3 = coerce_client_dossier_v3("vodafone_demo", legacy)
    dossier_v2 = client_intelligence_to_v2(dossier_v3)

    assert dossier_v2["version"] == "2.0"
    assert dossier_v2["business_context"]["ceo_agenda"]["confidence"] == "medium"
    assert dossier_v2["business_context"]["osint_footprint"]["confidence"] == "medium"
    assert (
        dossier_v2["business_context"]["transformation_horizon"]["confidence"]
        == "medium"
    )
    assert dossier_v2["tower_overrides"]["T5"]["business_criticality"] == "medium"


def test_client_intelligence_to_v2_downgrades_extended_claim_types() -> None:
    dossier_v3 = {
        "version": "3.0",
        "client_name": "vodafone_demo",
        "metadata": {
            "dossier_id": "vodafone-demo-1",
            "schema_version": "3.0",
            "created_at": "2026-05-01T00:00:00+00:00",
            "modified_at": "2026-05-01T00:00:00+00:00",
            "lang": "es",
            "generated_by": "assessment_engine",
        },
        "profile": {"industry": "Telecom", "financial_tier": "Tier 1"},
        "regulatory_context": [],
        "business_context": {
            "ceo_agenda": {
                "summary": "Agenda",
                "confidence": {"score": 80, "label": "high", "method": "custom"},
                "sources": [],
            },
            "strategic_priorities": [],
            "business_model_signals": [],
            "active_transformations": [],
            "transformation_horizon": {
                "stage": "H1",
                "label": "Basics",
                "rationale": "Rationale",
                "confidence": {"score": 50, "label": "medium", "method": "custom"},
                "sources": [],
            },
            "constraints": [],
        },
        "technology_context": {
            "footprint_summary": {
                "summary": "Footprint",
                "confidence": {"score": 50, "label": "medium", "method": "custom"},
                "sources": [],
            },
            "technology_drivers": [],
            "vendor_dependencies": [],
            "operating_constraints": [],
            "recent_incident_signals": [],
        },
        "tower_overrides": {},
        "claims": [
            {
                "claim_id": "claim_1",
                "claim": "Escenario de outage relevante.",
                "claim_type": "scenario",
                "confidence": {"score": 70, "label": "high", "method": "custom"},
                "sources": [],
                "valid_for_domains": ["tower"],
                "related_towers": ["T5"],
            }
        ],
        "review": {"human_review_status": "pending"},
        "extensions": {},
    }

    dossier_v2 = client_intelligence_to_v2(dossier_v3)

    assert dossier_v2["evidence_register"][0]["claim_type"] == "assumption"


def test_confidence_assessment_normalizes_very_high_label() -> None:
    confidence = ConfidenceAssessment.model_validate(
        {"score": 95, "label": "very high", "method": "custom"}
    )

    assert confidence.label == "high"
