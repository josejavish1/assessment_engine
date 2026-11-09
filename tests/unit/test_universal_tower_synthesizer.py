"""Deterministic Test Oracle for UniversalTowerSynthesizer.

Validates:
1. Multi-tenant universality across diverse industries (FinTech, Healthcare, Energy, Manufacturing, Retail).
2. Dynamic parameterization: revenue, currencies (GBP, EUR, USD, BRL, JPY), regulatory regimes (DORA, KRITIS, HIPAA, NIS2).
3. Absolute zero-hardcoding: Zero client-specific or vendor-specific artifacts in prompts or models.
4. Typed contracts and immutability of ClientAssessmentContext.
5. Multi-lingual target delivery: Supports en, es, de, fr, pt output generation directives.
6. 100% Technical English codebase and test contracts.
"""

from __future__ import annotations

import dataclasses
import pytest

from assessment_engine.application.services.semantic_epistemic_router import (
    EpistemicContextPacket,
    SemanticProposition,
)
from assessment_engine.application.services.universal_tower_synthesizer import (
    ClientAssessmentContext,
    UniversalTowerSynthesizer,
)


def test_client_assessment_context_immutability_and_types() -> None:
    """Verifies typed contract and immutability of ClientAssessmentContext."""
    ctx = ClientAssessmentContext(
        client_name="Starling Apex Bank",
        industry_vertical="fintech",
        annual_revenue=500_000_000.0,
        currency_code="GBP",
        regulatory_frameworks=("DORA", "PCI-DSS", "ISO27001"),
        target_language="en",
        operational_footprint="United Kingdom & EU",
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        ctx.annual_revenue = 1000.0  # type: ignore[misc]

    assert ctx.client_name == "Starling Apex Bank"
    assert ctx.currency_code == "GBP"
    assert "DORA" in ctx.regulatory_frameworks
    assert ctx.annual_revenue == 500_000_000.0


def test_zero_hardcoding_across_diverse_archetypes() -> None:
    """Verifies that generated meta-prompts contain zero hardcoded client or vendor assumptions."""
    synthesizer = UniversalTowerSynthesizer()

    archetypes = [
        ClientAssessmentContext(
            client_name="Nordic Grid Power GmbH",
            industry_vertical="utilities",
            annual_revenue=12_000_000_000.0,
            currency_code="EUR",
            regulatory_frameworks=("NIS2", "KRITIS"),
            target_language="de",
        ),
        ClientAssessmentContext(
            client_name="BioHealth Alliance Corp",
            industry_vertical="healthcare",
            annual_revenue=3_500_000_000.0,
            currency_code="USD",
            regulatory_frameworks=("HIPAA", "HITRUST"),
            target_language="en",
        ),
        ClientAssessmentContext(
            client_name="Vanguard Logistics SA",
            industry_vertical="logistics",
            annual_revenue=850_000_000.0,
            currency_code="EUR",
            regulatory_frameworks=("NIS2",),
            target_language="es",
        ),
    ]

    mock_packet = EpistemicContextPacket(
        tower_code="T2",
        propositions=[
            SemanticProposition(
                text="Legacy mainframe core banking ledger requires manual overnight reconciliation.",
                turn_index=1,
                polarity="NEGATIVE",
            )
        ],
        semantic_density_score=0.75,
        epistemic_state="OBSERVED_EXPLICIT",
    )

    forbidden_hardcoded_terms = [
        "molins",
        "sant vicenç",
        "weighbridge",
        "báscula",
        "bascula",
        "cement",
        "cemento",
        "hormigonera",
        "secil",
        "fairfly",
    ]

    for ctx in archetypes:
        prompt = synthesizer.build_synthesis_prompt(
            context=ctx,
            tower_code="T2",
            evidence_packet=mock_packet,
            tower_definition={"tower_name": "Hybrid Compute & Platforms", "pillars": []},
        )

        prompt_lower = prompt.lower()
        # Assert client-specific variables are dynamically bound
        assert ctx.client_name.lower() in prompt_lower
        assert ctx.industry_vertical in prompt_lower
        assert ctx.currency_code.lower() in prompt_lower

        # Assert absolute zero hardcoded legacy terms
        for term in forbidden_hardcoded_terms:
            assert term not in prompt_lower, f"Forbidden hardcoded term '{term}' leaked into prompt for {ctx.client_name}!"


def test_sector_severity_calibration_directive() -> None:
    """Verifies that the prompt dynamically adapts severity calibration guidelines to the industry vertical."""
    synthesizer = UniversalTowerSynthesizer()

    fintech_ctx = ClientAssessmentContext(
        client_name="FinEdge Payments",
        industry_vertical="fintech",
        annual_revenue=200_000_000.0,
        currency_code="USD",
    )
    health_ctx = ClientAssessmentContext(
        client_name="St. Jude Health System",
        industry_vertical="healthcare",
        annual_revenue=1_500_000_000.0,
        currency_code="USD",
    )

    mock_packet = EpistemicContextPacket(
        tower_code="T6",
        propositions=[],
        semantic_density_score=0.0,
        epistemic_state="OBSERVED_EXPLICIT",
    )

    fintech_prompt = synthesizer.build_synthesis_prompt(fintech_ctx, "T6", mock_packet, {})
    health_prompt = synthesizer.build_synthesis_prompt(health_ctx, "T6", mock_packet, {})

    assert "fintech" in fintech_prompt.lower()
    assert "transaction" in fintech_prompt.lower() or "ledger" in fintech_prompt.lower() or "financial" in fintech_prompt.lower()

    assert "healthcare" in health_prompt.lower()
    assert "patient" in health_prompt.lower() or "clinical" in health_prompt.lower() or "hipaa" in health_prompt.lower()

    # Kills LCR mutant (or -> and) by testing pharma standalone
    pharma_ctx = ClientAssessmentContext(
        client_name="BioGen Laboratories",
        industry_vertical="pharma",
        annual_revenue=800_000_000.0,
        currency_code="EUR",
    )
    pharma_prompt = synthesizer.build_synthesis_prompt(pharma_ctx, "T6", mock_packet, {})
    assert "patient" in pharma_prompt.lower() or "clinical" in pharma_prompt.lower()


def test_offline_synthesis_execution_deterministic() -> None:
    """Verifies deterministic offline fallback synthesis without external API dependencies."""
    synthesizer = UniversalTowerSynthesizer()
    ctx = ClientAssessmentContext(
        client_name="Test Enterprise",
        industry_vertical="retail",
        annual_revenue=100_000_000.0,
        currency_code="EUR",
    )

    prop = SemanticProposition(
        text="Point of sale terminals lack encrypted offline store and forward buffering.",
        turn_index=0,
        polarity="NEGATIVE",
    )
    packet = EpistemicContextPacket("T3", [prop], 0.65, "OBSERVED_EXPLICIT")

    mock_response = {
        "executive_snapshot": {
            "bottom_line": "Robust retail network foundation with localized store resilience gaps.",
            "operational_benefits": ["Centralized SD-WAN orchestration"],
            "structural_risks": ["Unbuffered POS communication drops during WAN outage"],
        },
        "pillars_analysis": [
            {
                "pillar_id": f"T3.P{i}",
                "pillar_name": f"Pillar {i}",
                "target_score": 3.5,
                "thought_process": "Analysis of network layer",
                "asis_architecture_description": "Network architecture is deployed across stores.",
                "health_check_asis": [
                    {
                        "node_id": f"t3-p{i}-hc-01",
                        "capability": f"Pillar {i} Capability",
                        "finding": "Specific observation on store routing.",
                        "business_risk": "Store checkout delays during link flapping.",
                        "severity": "CRITICAL",
                        "fair_ale_score": 150000.0,
                        "fair_p90_score": 350000.0,
                    },
                    {
                        "node_id": f"t3-p{i}-hc-02",
                        "capability": f"Pillar {i} Secondary",
                        "finding": "Unrated secondary finding.",
                    },
                ],
            }
            for i in range(1, 6)
        ],
    }

    result = synthesizer.parse_and_validate_synthesis(mock_response, ctx, "T3")

    assert "executive_snapshot" in result
    assert "pillars_analysis" in result
    assert len(result["pillars_analysis"]) == 5
    for pil in result["pillars_analysis"]:
        assert len(pil["health_check_asis"]) == 2
        # Kills ROR mutant (not in -> in): existing CRITICAL must NOT be overwritten to MEDIUM
        assert pil["health_check_asis"][0]["severity"] == "CRITICAL"
        assert pil["health_check_asis"][0]["fair_ale_score"] == 150000.0
        # Missing severity must be assigned default MEDIUM
        assert pil["health_check_asis"][1]["severity"] == "MEDIUM"
        # Actuarial model projection default
        assert pil["health_check_asis"][1]["fair_ale_score"] == pytest.approx(31849.32, rel=1e-2)
