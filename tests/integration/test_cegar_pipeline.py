"""Integration tests for the CEGAR Synthesis Pipeline (RFC-009).

Verifies the Generator-Verifier-Optimizer (GVO) state machine, 1-shot recovery,
and deterministic fail-fast circuit breaking.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
import pytest

from assessment_engine.application.services.cegar_synthesis_engine import (
    CegarSynthesisEngine,
)
from assessment_engine.domain.synthesis.exceptions import UnverifiableSynthesisError
from assessment_engine.domain.synthesis.oracle import (
    DeterministicVerificationOracle,
    SynthesisContext,
)
from assessment_engine.domain.synthesis.schemas import (
    CandidateEnterpriseDeliverable,
    ExecutiveRoadmapPhase,
    FinancialProjection,
    OptimizationAxis,
    StrategicOption,
    VerifiedEnterpriseDeliverable,
)
from assessment_engine.infrastructure.llm.cegar_adapter import CegarLLMAdapter


def _create_mock_deliverable(
    currency: str = "EUR",
    locale: str = "en-US",
    isic_code: str = "6201",
    tco: str = "150000.00",
    invalid_tco: str | None = None,
) -> CandidateEnterpriseDeliverable:
    """Helper building a candidate deliverable for pipeline testing."""
    tco_dec = Decimal(tco)
    capex = tco_dec * Decimal("0.40")
    opex = tco_dec * Decimal("0.60")
    display_tco = Decimal(invalid_tco) if invalid_tco is not None else tco_dec

    fin = FinancialProjection(
        currency_iso_4217=currency,
        capex_allocation=capex,
        opex_allocation=opex,
        total_cost_of_ownership=display_tco,
        risk_exposure_p10=Decimal("15000.00"),
        risk_exposure_p50=Decimal("45000.00"),
        risk_exposure_p90=Decimal("120000.00"),
    )

    opts = [
        StrategicOption(
            option_id="OPT-CAP1",
            primary_axis=OptimizationAxis.CAPITAL_EFFICIENCY,
            strategy_designation="Capital-Efficient Modernization",
            architectural_rationale=(
                "Modernization combining hybrid edge resilience with sovereign cloud decoupling. "
                "Provides substantial operational leverage while shielding core boundaries."
            ),
            sacrificed_dimension_analysis=(
                "Immediate short-term execution velocity is deliberately traded off in favor of comprehensive "
                "telemetry shielding and zero-trust verification baselines across distributed microservices."
            ),
            financials=fin,
            supporting_evidence_ids=["EV-001", "EV-002"],
            utility_weights={
                OptimizationAxis.CAPITAL_EFFICIENCY: 0.34,
                OptimizationAxis.OPERATIONAL_RESILIENCE: 0.33,
                OptimizationAxis.EXECUTION_VELOCITY: 0.33,
            },
        ),
        StrategicOption(
            option_id="OPT-RES2",
            primary_axis=OptimizationAxis.OPERATIONAL_RESILIENCE,
            strategy_designation="Resilience-Focused Hardening",
            architectural_rationale=(
                "Comprehensive high resilience architecture shielding mission critical enterprise systems "
                "against cascading availability failures and malicious boundary penetration attempts."
            ),
            sacrificed_dimension_analysis=(
                "Immediate cost minimization is deliberately traded off for geographic redundancy, automated "
                "failover infrastructure, and multi-region active-active database clustering."
            ),
            financials=fin,
            supporting_evidence_ids=["EV-002", "EV-003"],
            utility_weights={
                OptimizationAxis.CAPITAL_EFFICIENCY: 0.33,
                OptimizationAxis.OPERATIONAL_RESILIENCE: 0.34,
                OptimizationAxis.EXECUTION_VELOCITY: 0.33,
            },
        ),
        StrategicOption(
            option_id="OPT-VEL3",
            primary_axis=OptimizationAxis.EXECUTION_VELOCITY,
            strategy_designation="Rapid Velocity Transformation",
            architectural_rationale=(
                "Accelerated digital transformation utilizing pre-built enterprise modules, opinionated "
                "developer golden paths, and managed software-as-a-service application backbones."
            ),
            sacrificed_dimension_analysis=(
                "Bespoke architectural customization depth is traded off for speed to market, standardized "
                "deployment templates, and immediate commercial time-to-value acceleration."
            ),
            financials=fin,
            supporting_evidence_ids=["EV-004", "EV-005"],
            utility_weights={
                OptimizationAxis.CAPITAL_EFFICIENCY: 0.33,
                OptimizationAxis.OPERATIONAL_RESILIENCE: 0.33,
                OptimizationAxis.EXECUTION_VELOCITY: 0.34,
            },
        ),
    ]

    phase_budget_1 = display_tco * Decimal("0.40")
    phase_budget_2 = display_tco * Decimal("0.60")

    return CandidateEnterpriseDeliverable(
        bcp47_locale=locale,
        industry_isic_code=isic_code,
        executive_thesis=(
            "The enterprise stands at a critical technological inflection point where legacy architectural entropy "
            "directly constrains commercial agility and introduces unhedged operational risk vectors. Through "
            "disciplined capital allocation, sovereign cloud decoupling, and the implementation of automated "
            "governance gates, leadership can secure lasting operational resilience while reducing ongoing expenditure."
        ),
        pareto_frontier=opts,
        selected_equilibrium_option_id="OPT-CAP1",
        equilibrium_justification=(
            "Selecting Option OPT-CAP1 establishes the optimal strategic equilibrium between risk exposure mitigation "
            "and capital efficiency. This posture satisfies corporate governance requirements while systematically "
            "remediating the highest-severity vulnerability vectors across the infrastructure portfolio."
        ),
        execution_roadmap=[
            ExecutiveRoadmapPhase(
                phase_index=1,
                phase_title="Phase 1: Baseline Architecture",
                duration_weeks=12,
                deliverable_artifacts=["Telemetry Gateway"],
                allocated_budget=phase_budget_1,
                evidence_citations=["EV-001", "EV-002"],
            ),
            ExecutiveRoadmapPhase(
                phase_index=2,
                phase_title="Phase 2: Workload Decoupling",
                duration_weeks=16,
                deliverable_artifacts=["Service Mesh"],
                allocated_budget=phase_budget_2,
                evidence_citations=["EV-002", "EV-003"],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_cegar_pipeline_happy_path() -> None:
    """Verify that a compliant candidate deliverable completes in 1 LLM call with zero repairs."""
    call_count = 0
    candidate_valid = _create_mock_deliverable()

    async def mock_caller(**kwargs: Any) -> CandidateEnterpriseDeliverable:
        nonlocal call_count
        call_count += 1
        return candidate_valid

    adapter = CegarLLMAdapter(custom_caller=mock_caller)
    engine = CegarSynthesisEngine(generator=adapter)

    context = SynthesisContext(
        valid_evidence_ids=frozenset(["EV-001", "EV-002", "EV-003", "EV-004", "EV-005"]),
        target_currency="EUR",
        target_locale="en-US",
        target_isic_code="6201",
    )

    result = await engine.synthesize(context, {"raw_evidence": []})

    assert isinstance(result, VerifiedEnterpriseDeliverable)
    assert call_count == 1
    assert result.bcp47_locale == "en-US"
    assert result.industry_isic_code == "6201"


@pytest.mark.asyncio
async def test_cegar_pipeline_one_shot_recovery() -> None:
    """Verify that initial candidate defects are isolated by the Oracle and repaired in 1 shot (2 LLM calls)."""
    call_count = 0
    candidate_defective = _create_mock_deliverable(tco="150000.00", invalid_tco="200000.00")
    candidate_repaired = _create_mock_deliverable(tco="150000.00")

    async def mock_caller(prompt: str, **kwargs: Any) -> CandidateEnterpriseDeliverable:
        nonlocal call_count
        call_count += 1
        if prompt == "GENERATE":
            return candidate_defective
        if prompt == "REPAIR":
            # Assert counterexamples were injected
            c_vector = kwargs.get("counterexamples")
            assert c_vector is not None
            assert len(c_vector.violations) > 0
            return candidate_repaired
        raise ValueError(f"Unknown prompt type: {prompt}")

    adapter = CegarLLMAdapter(custom_caller=mock_caller)
    engine = CegarSynthesisEngine(generator=adapter)

    context = SynthesisContext(
        valid_evidence_ids=frozenset(["EV-001", "EV-002", "EV-003", "EV-004", "EV-005"]),
        target_currency="EUR",
        target_locale="en-US",
        target_isic_code="6201",
    )

    result = await engine.synthesize(context, {"raw_evidence": []})

    assert isinstance(result, VerifiedEnterpriseDeliverable)
    assert call_count == 2
    assert result.selected_equilibrium_option_id == "OPT-CAP1"


@pytest.mark.asyncio
async def test_cegar_pipeline_fail_fast_circuit_breaker() -> None:
    """Verify that persistent defects after 1-shot repair pass immediately halt with typed error."""
    call_count = 0
    candidate_defective = _create_mock_deliverable(tco="150000.00", invalid_tco="200000.00")

    async def mock_caller(prompt: str, **kwargs: Any) -> CandidateEnterpriseDeliverable:
        nonlocal call_count
        call_count += 1
        return candidate_defective  # Returns defective output on both attempts

    adapter = CegarLLMAdapter(custom_caller=mock_caller)
    engine = CegarSynthesisEngine(generator=adapter)

    context = SynthesisContext(
        valid_evidence_ids=frozenset(["EV-001", "EV-002", "EV-003", "EV-004", "EV-005"]),
        target_currency="EUR",
        target_locale="en-US",
        target_isic_code="6201",
    )

    with pytest.raises(UnverifiableSynthesisError) as exc_info:
        await engine.synthesize(context, {"raw_evidence": []})

    assert call_count == 2
    err = exc_info.value
    assert err.synthesis_attempt == 2
    assert len(err.violations) > 0
    assert any(v["rule_id"] == "FIN_IDENTITY_ERR" for v in err.violations)


@pytest.mark.asyncio
async def test_cegar_pipeline_multilingual_japanese_context() -> None:
    """Verify CEGAR pipeline handles Japanese Yen and BCP-47 locale seamlessly."""
    candidate_jpy = _create_mock_deliverable(
        currency="JPY",
        locale="ja-JP",
        isic_code="C10",
        tco="15000000.00",
    )

    async def mock_caller(**kwargs: Any) -> CandidateEnterpriseDeliverable:
        return candidate_jpy

    adapter = CegarLLMAdapter(custom_caller=mock_caller)
    engine = CegarSynthesisEngine(generator=adapter)

    context = SynthesisContext(
        valid_evidence_ids=frozenset(["EV-001", "EV-002", "EV-003", "EV-004", "EV-005"]),
        target_currency="JPY",
        target_locale="ja-JP",
        target_isic_code="C10",
    )

    result = await engine.synthesize(context, {"raw_evidence": []})
    assert isinstance(result, VerifiedEnterpriseDeliverable)
    assert result.bcp47_locale == "ja-JP"
    assert result.industry_isic_code == "C10"
    assert result.pareto_frontier[0].financials.currency_iso_4217 == "JPY"
