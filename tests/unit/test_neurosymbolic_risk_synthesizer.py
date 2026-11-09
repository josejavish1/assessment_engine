"""Unit tests for NeurosymbolicLLMSynthesizer, Circuit Breaker, and Adaptive Complexity Ceilings."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from assessment_engine.application.services.neurosymbolic_risk_synthesizer import (
    NeurosymbolicLLMSynthesizer,
)
from assessment_engine.application.services.risk_synthesis_service import (
    DeterministicFallbackSynthesizer,
)
from assessment_engine.domain.schemas.risk_synthesis import (
    RiskSynthesisContext,
    SynthesizedRiskItem,
)


def test_circuit_breaker_degrades_gracefully_on_llm_exception() -> None:
    """Verify that any LLM API error, network drop, or timeout automatically triggers the fallback."""
    synthesizer = NeurosymbolicLLMSynthesizer()
    # Mock client to raise an exception simulating API outage / quota exhaustion
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("API Quota Exceeded (HTTP 429)")
    synthesizer._client = mock_client
    synthesizer._model_name = "gemini-3.1-pro-preview"

    ctx = RiskSynthesisContext(
        client_name="Starling Bank",
        doc_lang="en",
        currency_symbol="£",
        hourly_rate=140000.0,
        verified_tech_stack=["Amazon Aurora Global PostgreSQL"],
        tower_code="T05",
        tower_name="Resilience & Continuity",
        pillar_id="T05.P03",
        pillar_name="Disaster Recovery Architecture & Failover",
        kpi_id="T05.P03.K01",
        assessed_score=4.75,
        calibrated_ale=44000.0,
        downtime_minutes=23,
        stoppage_loss=32000.0,
        recovery_burn=18000.0,
        penalty_loss=5000.0,
        total_sle=55000.0,
    )

    # Must NOT raise RuntimeError; must trip circuit breaker and return valid fallback item
    item = synthesizer.synthesize_risk(ctx)
    assert isinstance(item, SynthesizedRiskItem)
    assert "Amazon Aurora Global PostgreSQL" in item.causal_risk_title
    assert "£44,000" in item.actuarial_justification
    assert item.context_hash == ctx.compute_context_hash()


def test_adaptive_complexity_ceiling_prompt_construction() -> None:
    """Verify that low-maturity clients have forbidden vocabulary rules injected."""
    synthesizer = NeurosymbolicLLMSynthesizer()

    # Low-maturity SME context (score = 1.80)
    low_ctx = RiskSynthesisContext(
        client_name="Local Logistics Ltd",
        sub_industry="Regional Trucking",
        maturity_tier="Level 1 - Initial",
        doc_lang="en",
        currency_symbol="£",
        hourly_rate=5000.0,
        verified_tech_stack=["Local File Server"],
        tower_code="T02",
        tower_name="Compute Platforms",
        pillar_id="T02.P01",
        pillar_name="Compute Sizing",
        kpi_id="T02.P01.K01",
        assessed_score=1.80,
        calibrated_ale=12000.0,
        downtime_minutes=120,
        stoppage_loss=8000.0,
        recovery_burn=3000.0,
        penalty_loss=1000.0,
        total_sle=12000.0,
    )
    prompt_low = synthesizer._build_adaptive_prompt(low_ctx)
    assert "Strictly FORBIDDEN vocabulary" in prompt_low
    assert "Do NOT mention Kubernetes, microservices, Zero Trust" in prompt_low

    # High-maturity cloud-native context (score = 4.80)
    high_ctx = low_ctx.model_copy(update={"assessed_score": 4.80})
    prompt_high = synthesizer._build_adaptive_prompt(high_ctx)
    assert "ADAPTIVE COMPLEXITY CEILING (HIGH MATURITY / CLOUD-NATIVE)" in prompt_high
    assert "Analyze sophisticated distributed systems failure modes" in prompt_high
