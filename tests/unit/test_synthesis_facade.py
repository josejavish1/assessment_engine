"""Unit tests for the Polymorphic Synthesis Facade and Anti-Corruption Layer (RFC-009 / PR-3)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
import pytest

from assessment_engine.application.services.cegar_synthesis_engine import (
    CegarSynthesisEngine,
)
from assessment_engine.application.services.synthesis_facade import (
    PolymorphicSynthesisFacade,
    SynthesisAntiCorruptionLayer,
    SynthesisMode,
)
from assessment_engine.domain.synthesis.oracle import SynthesisContext
from assessment_engine.domain.synthesis.schemas import (
    CandidateEnterpriseDeliverable,
    ExecutiveRoadmapPhase,
    FinancialProjection,
    OptimizationAxis,
    StrategicOption,
    VerifiedEnterpriseDeliverable,
)
from assessment_engine.infrastructure.llm.cegar_adapter import CegarLLMAdapter


def _build_valid_verified_deliverable() -> VerifiedEnterpriseDeliverable:
    """Helper building a verified enterprise deliverable for facade testing."""
    fin = FinancialProjection(
        currency_iso_4217="EUR",
        capex_allocation=Decimal("60000.00"),
        opex_allocation=Decimal("90000.00"),
        total_cost_of_ownership=Decimal("150000.00"),
        risk_exposure_p10=Decimal("15000.00"),
        risk_exposure_p50=Decimal("45000.00"),
        risk_exposure_p90=Decimal("120000.00"),
    )
    opts = [
        StrategicOption(
            option_id="OPT-CAP1",
            primary_axis=OptimizationAxis.CAPITAL_EFFICIENCY,
            strategy_designation="Capital Efficiency Strategy",
            architectural_rationale=(
                "Modernization combining hybrid edge resilience with sovereign cloud decoupling. "
                "Provides substantial operational leverage while shielding core enterprise boundaries."
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
            strategy_designation="Operational Resilience Strategy",
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
            strategy_designation="Execution Velocity Strategy",
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

    return VerifiedEnterpriseDeliverable(
        bcp47_locale="en-US",
        industry_isic_code="6201",
        executive_thesis=(
            "The enterprise stands at a pivotal technological inflection point where technical entropy directly "
            "constrains commercial agility. Through disciplined capital allocation and automated governance, "
            "leadership can secure sovereign operational autonomy while reducing baseline expenditure."
        ),
        pareto_frontier=opts,
        selected_equilibrium_option_id="OPT-CAP1",
        equilibrium_justification=(
            "Selecting Option OPT-CAP1 establishes the optimal strategic equilibrium between risk exposure mitigation "
            "and capital efficiency across the multi-horizon transformation lifecycle. This posture satisfies strict "
            "corporate governance requirements while systematically remediating vulnerability vectors."
        ),
        execution_roadmap=[
            ExecutiveRoadmapPhase(
                phase_index=1,
                phase_title="Phase 1: Foundation",
                duration_weeks=12,
                deliverable_artifacts=["Telemetry Gateway"],
                allocated_budget=Decimal("60000.00"),
                evidence_citations=["EV-001", "EV-002"],
            ),
            ExecutiveRoadmapPhase(
                phase_index=2,
                phase_title="Phase 2: Modernization",
                duration_weeks=16,
                deliverable_artifacts=["Service Mesh"],
                allocated_budget=Decimal("90000.00"),
                evidence_citations=["EV-002", "EV-003"],
            ),
        ],
    )


def _build_context() -> SynthesisContext:
    return SynthesisContext(
        valid_evidence_ids=frozenset(["EV-001", "EV-002", "EV-003", "EV-004", "EV-005"]),
        target_currency="EUR",
        target_locale="en-US",
        target_isic_code="6201",
    )


@pytest.mark.asyncio
async def test_facade_mode_legacy() -> None:
    """Verify that mode LEGACY routes strictly to legacy synthesizer callable."""
    legacy_called = False

    async def mock_legacy(**kwargs: Any) -> dict[str, Any]:
        nonlocal legacy_called
        legacy_called = True
        return {"legacy_key": "legacy_val", "status": "LEGACY_EXECUTED"}

    candidate_valid = _build_valid_verified_deliverable()
    adapter = CegarLLMAdapter(custom_caller=lambda **kwargs: candidate_valid)
    engine = CegarSynthesisEngine(generator=adapter)

    facade = PolymorphicSynthesisFacade(
        cegar_engine=engine,
        legacy_synthesizer=mock_legacy,
        default_mode=SynthesisMode.LEGACY,
    )

    result = await facade.synthesize(_build_context(), {"evidence": []})
    assert legacy_called is True
    assert result["legacy_key"] == "legacy_val"


@pytest.mark.asyncio
async def test_facade_mode_cegar(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that mode CEGAR executes CEGAR engine and returns ACL mapped dictionary."""
    monkeypatch.setenv("SYNTHESIS_ENGINE_MODE", "CEGAR")

    candidate_valid = _build_valid_verified_deliverable()
    adapter = CegarLLMAdapter(custom_caller=lambda **kwargs: candidate_valid)
    engine = CegarSynthesisEngine(generator=adapter)

    facade = PolymorphicSynthesisFacade(
        cegar_engine=engine,
        legacy_synthesizer=None,
        default_mode=SynthesisMode.LEGACY,
    )

    result = await facade.synthesize(_build_context(), {"evidence": []})

    assert result["provenance"]["engine"] == "CEGAR_VERIFIED_V1"
    assert result["provenance"]["verified"] is True
    assert result["selected_option_id"] == "OPT-CAP1"
    assert result["financials"]["tco"] == "150000.00"
    assert len(result["pareto_frontier"]) == 3
    assert len(result["execution_roadmap"]) == 2


@pytest.mark.asyncio
async def test_facade_mode_shadow(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that mode SHADOW executes legacy and runs CEGAR in shadow mode."""
    monkeypatch.setenv("SYNTHESIS_ENGINE_MODE", "SHADOW")
    legacy_called = False
    cegar_called = False

    async def mock_legacy(**kwargs: Any) -> dict[str, Any]:
        nonlocal legacy_called
        legacy_called = True
        return {"result": "legacy_production"}

    candidate_valid = _build_valid_verified_deliverable()

    async def mock_cegar(**kwargs: Any) -> CandidateEnterpriseDeliverable:
        nonlocal cegar_called
        cegar_called = True
        return candidate_valid

    adapter = CegarLLMAdapter(custom_caller=mock_cegar)
    engine = CegarSynthesisEngine(generator=adapter)

    facade = PolymorphicSynthesisFacade(
        cegar_engine=engine,
        legacy_synthesizer=mock_legacy,
        default_mode=SynthesisMode.LEGACY,
    )

    result = await facade.synthesize(_build_context(), {"evidence": []})
    if facade._background_tasks:
        import asyncio
        await asyncio.gather(*facade._background_tasks, return_exceptions=True)

    assert legacy_called is True
    assert cegar_called is True
    assert result["result"] == "legacy_production"


@pytest.mark.asyncio
async def test_facade_shadow_error_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that errors during shadow CEGAR pass do not crash legacy production execution."""
    monkeypatch.setenv("SYNTHESIS_ENGINE_MODE", "SHADOW")

    async def mock_legacy(**kwargs: Any) -> dict[str, Any]:
        return {"result": "legacy_success"}

    async def failing_cegar(**kwargs: Any) -> CandidateEnterpriseDeliverable:
        raise RuntimeError("Simulated shadow synthesis failure")

    adapter = CegarLLMAdapter(custom_caller=failing_cegar)
    engine = CegarSynthesisEngine(generator=adapter)

    facade = PolymorphicSynthesisFacade(
        cegar_engine=engine,
        legacy_synthesizer=mock_legacy,
        default_mode=SynthesisMode.LEGACY,
    )

    # Must complete safely without raising
    result = await facade.synthesize(_build_context(), {"evidence": []})
    if facade._background_tasks:
        import asyncio
        await asyncio.gather(*facade._background_tasks, return_exceptions=True)
    assert result["result"] == "legacy_success"


def test_anti_corruption_layer_mapping_fidelity() -> None:
    """Verify that ACL faithfully transforms VerifiedEnterpriseDeliverable into legacy dictionary format."""
    deliverable = _build_valid_verified_deliverable()
    mapped = SynthesisAntiCorruptionLayer.map_verified_to_legacy_dict(deliverable)

    assert mapped["locale"] == "en-US"
    assert mapped["industry_isic"] == "6201"
    assert mapped["executive_summary"] == deliverable.executive_thesis
    assert mapped["selected_option_id"] == "OPT-CAP1"
    assert mapped["selected_strategy"] == "Capital Efficiency Strategy"
    assert mapped["financials"]["currency"] == "EUR"
    assert mapped["financials"]["tco"] == "150000.00"
    assert mapped["financials"]["capex"] == "60000.00"
    assert mapped["financials"]["opex"] == "90000.00"
    assert len(mapped["execution_roadmap"]) == 2
    assert mapped["execution_roadmap"][0]["allocated_budget"] == "60000.00"
    assert mapped["provenance"]["engine"] == "CEGAR_VERIFIED_V1"
