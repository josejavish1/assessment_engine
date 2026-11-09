"""Unit tests for Stage 4.1: Risk Synthesis Contract & Deterministic Fallback Provider."""

from __future__ import annotations

import pytest
from assessment_engine.application.services.risk_synthesis_service import (
    DeterministicFallbackSynthesizer,
)
from assessment_engine.domain.schemas.risk_synthesis import (
    RiskSynthesisContext,
    SynthesizedRiskItem,
)
from assessment_engine.infrastructure.localization import format_currency


def test_risk_synthesis_context_hash_stability() -> None:
    ctx = RiskSynthesisContext(
        client_name="Starling Bank",
        sub_industry="FinTech Clearing Bank",
        maturity_tier="Level 5 - Optimized",
        doc_lang="en",
        currency_symbol="£",
        hourly_rate=140000.0,
        verified_tech_stack=["Amazon Aurora Global PostgreSQL", "Apache Kafka"],
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
    hash_1 = ctx.compute_context_hash()
    hash_2 = ctx.compute_context_hash()
    assert hash_1 == hash_2
    assert len(hash_1) == 64

    # Altering mathematical scalar must invalidate hash
    ctx_modified = ctx.model_copy(update={"calibrated_ale": 45000.0})
    assert ctx_modified.compute_context_hash() != hash_1


def test_deterministic_fallback_synthesizer_english() -> None:
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
    synthesizer = DeterministicFallbackSynthesizer()
    item = synthesizer.synthesize_risk(ctx)

    assert isinstance(item, SynthesizedRiskItem)
    assert item.risk_id == "RSK-T05.P03.K01"
    assert "Amazon Aurora Global PostgreSQL" in item.causal_risk_title
    assert "Disaster Recovery Architecture & Failover" in item.causal_risk_title
    assert "£44,000" in item.actuarial_justification
    assert "£55,000" in item.actuarial_justification
    assert len(item.context_hash) == 64


def test_deterministic_fallback_synthesizer_portuguese() -> None:
    ctx = RiskSynthesisContext(
        client_name="Rede D'Or",
        doc_lang="pt",
        currency_symbol="R$",
        hourly_rate=420000.0,
        verified_tech_stack=["Dell EMC PowerStore"],
        tower_code="T04",
        tower_name="Armazenamento",
        pillar_id="T04.P02",
        pillar_name="Arquitetura de Armazenamento",
        kpi_id="T04.P02.K01",
        assessed_score=4.50,
        calibrated_ale=91000.0,
        downtime_minutes=45,
        stoppage_loss=180000.0,
        recovery_burn=65000.0,
        penalty_loss=15000.0,
        total_sle=260000.0,
    )
    synthesizer = DeterministicFallbackSynthesizer()
    item = synthesizer.synthesize_risk(ctx)

    assert isinstance(item, SynthesizedRiskItem)
    assert "Dell EMC PowerStore" in item.causal_risk_title
    ale_formatted = format_currency(91000.0, currency_symbol="R$", locale="pt", decimals=0)
    sle_formatted = format_currency(260000.0, currency_symbol="R$", locale="pt", decimals=0)
    assert ale_formatted in item.actuarial_justification
    assert sle_formatted in item.actuarial_justification
