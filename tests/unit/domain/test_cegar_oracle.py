"""Unit and invariant verification tests for the CEGAR Deterministic Oracle (RFC-009)."""

from __future__ import annotations

from decimal import Decimal
import pytest

from assessment_engine.domain.synthesis.oracle import (
    DeterministicVerificationOracle,
    SynthesisContext,
)
from assessment_engine.domain.synthesis.schemas import (
    CandidateEnterpriseDeliverable,
    ExecutiveRoadmapPhase,
    FinancialProjection,
    OptimizationAxis,
    SeverityLevel,
    StrategicOption,
)


def _build_valid_financials(currency: str = "EUR", tco: str = "150000.00") -> FinancialProjection:
    """Helper creating a mathematically valid financial projection."""
    tco_dec = Decimal(tco)
    capex = tco_dec * Decimal("0.40")
    opex = tco_dec * Decimal("0.60")
    return FinancialProjection(
        currency_iso_4217=currency,
        capex_allocation=capex,
        opex_allocation=opex,
        total_cost_of_ownership=tco_dec,
        risk_exposure_p10=Decimal("15000.00"),
        risk_exposure_p50=Decimal("45000.00"),
        risk_exposure_p90=Decimal("120000.00"),
    )


def _build_valid_option(
    opt_id: str,
    axis: OptimizationAxis,
    tco: str = "150000.00",
    currency: str = "EUR",
    evidence_ids: list[str] | None = None,
) -> StrategicOption:
    """Helper creating a single valid Pareto frontier option."""
    return StrategicOption(
        option_id=opt_id,
        primary_axis=axis,
        strategy_designation=f"Strategic Posture for {axis.value}",
        architectural_rationale=(
            "Comprehensive enterprise modernization combining edge resilience with sovereign cloud decoupling. "
            "Our strategic analysis reveals substantial operational leverage across hybrid infrastructure tiers, "
            "enabling rapid deployment cycles without compromising strict regulatory governance boundaries."
        ),
        sacrificed_dimension_analysis=(
            "Immediate short-term execution velocity is deliberately traded off in favor of comprehensive "
            "telemetry shielding and zero-trust verification baselines across distributed microservices."
        ),
        financials=_build_valid_financials(currency=currency, tco=tco),
        supporting_evidence_ids=evidence_ids or ["EV-001", "EV-002"],
        utility_weights={
            OptimizationAxis.CAPITAL_EFFICIENCY: 0.34,
            OptimizationAxis.OPERATIONAL_RESILIENCE: 0.33,
            OptimizationAxis.EXECUTION_VELOCITY: 0.33,
        },
    )


def _build_valid_deliverable(
    locale: str = "en-US",
    isic_code: str = "6201",
    currency: str = "EUR",
    evidence_ids: list[str] | None = None,
) -> CandidateEnterpriseDeliverable:
    """Helper building a 100% valid candidate deliverable."""
    ev = evidence_ids or ["EV-001", "EV-002", "EV-003", "EV-004", "EV-005"]
    opts = [
        _build_valid_option("OPT-CAP1", OptimizationAxis.CAPITAL_EFFICIENCY, "150000.00", currency, [ev[0], ev[1]]),
        _build_valid_option("OPT-RES2", OptimizationAxis.OPERATIONAL_RESILIENCE, "180000.00", currency, [ev[1], ev[2]]),
        _build_valid_option("OPT-VEL3", OptimizationAxis.EXECUTION_VELOCITY, "160000.00", currency, [ev[3], ev[4]]),
    ]
    return CandidateEnterpriseDeliverable(
        bcp47_locale=locale,
        industry_isic_code=isic_code,
        executive_thesis=(
            "The enterprise stands at a pivotal juncture where technical entropy threatens core business agility. "
            "Through systematic modernization of the hybrid estate and proactive implementation of automated "
            "governance gates, leadership can secure sovereign operational autonomy while reducing baseline expenditure. "
            "Our quantitative modeling demonstrates compelling return on security investment across all horizons."
        ),
        pareto_frontier=opts,
        selected_equilibrium_option_id="OPT-CAP1",
        equilibrium_justification=(
            "Selecting Option OPT-CAP1 establishes the optimal equilibrium between risk exposure mitigation and "
            "disciplined capital allocation. This strategic posture protects enterprise cash flow while remediating "
            "the highest-severity vulnerability vectors identified during telemetry harvesting."
        ),
        execution_roadmap=[
            ExecutiveRoadmapPhase(
                phase_index=1,
                phase_title="Phase 1: Foundation & Baseline Modernization",
                duration_weeks=12,
                deliverable_artifacts=["Telemetry Ingress Gateway", "Core Identity Directory"],
                allocated_budget=Decimal("60000.00"),
                evidence_citations=[ev[0], ev[1]],
            ),
            ExecutiveRoadmapPhase(
                phase_index=2,
                phase_title="Phase 2: Workload Decoupling & Autonomous Ops",
                duration_weeks=16,
                deliverable_artifacts=["Sovereign Service Mesh", "Automated Policy Engine"],
                allocated_budget=Decimal("90000.00"),
                evidence_citations=[ev[1], ev[2]],
            ),
        ],
    )


def _build_context(
    currency: str = "EUR",
    locale: str = "en-US",
    isic_code: str = "6201",
    evidence_ids: list[str] | None = None,
) -> SynthesisContext:
    """Helper building a strict runtime context."""
    ev = evidence_ids or ["EV-001", "EV-002", "EV-003", "EV-004", "EV-005"]
    return SynthesisContext(
        valid_evidence_ids=frozenset(ev),
        target_currency=currency,
        target_locale=locale,
        target_isic_code=isic_code,
    )


def test_oracle_happy_path_validation() -> None:
    """Verify that a compliant candidate deliverable produces an empty counterexample vector."""
    candidate = _build_valid_deliverable()
    context = _build_context()
    result = DeterministicVerificationOracle.verify(candidate, context)
    assert result.is_valid is True
    assert len(result.violations) == 0


def test_oracle_detects_contextual_locale_mismatch() -> None:
    """Verify that candidate emitting wrong locale triggers LOCALE_MISMATCH_ERR."""
    candidate = _build_valid_deliverable(locale="es-ES")
    context = _build_context(locale="en-US")
    result = DeterministicVerificationOracle.verify(candidate, context)
    assert result.is_valid is False
    viol = next(v for v in result.violations if v.rule_id == "LOCALE_MISMATCH_ERR")
    assert viol.severity == SeverityLevel.CRITICAL
    assert viol.json_path == "/bcp47_locale"


def test_oracle_detects_contextual_isic_mismatch() -> None:
    """Verify that candidate emitting wrong industry code triggers ISIC_MISMATCH_ERR."""
    candidate = _build_valid_deliverable(isic_code="K6419")
    context = _build_context(isic_code="6201")
    result = DeterministicVerificationOracle.verify(candidate, context)
    assert result.is_valid is False
    viol = next(v for v in result.violations if v.rule_id == "ISIC_MISMATCH_ERR")
    assert viol.severity == SeverityLevel.CRITICAL
    assert viol.json_path == "/industry_isic_code"


def test_oracle_detects_currency_mismatch() -> None:
    """Verify that candidate option financial projection in wrong currency triggers CURRENCY_MISMATCH_ERR."""
    candidate = _build_valid_deliverable(currency="USD")
    context = _build_context(currency="EUR")
    result = DeterministicVerificationOracle.verify(candidate, context)
    assert result.is_valid is False
    viol = next(v for v in result.violations if v.rule_id == "CURRENCY_MISMATCH_ERR")
    assert viol.severity == SeverityLevel.CRITICAL
    assert viol.json_path == "/pareto_frontier/0/financials/currency_iso_4217"


def test_oracle_detects_duplicate_option_ids() -> None:
    """Verify that duplicate option_ids across pareto_frontier trigger DUPLICATE_OPTION_ID_ERR."""
    candidate = _build_valid_deliverable()
    mutated_opts = list(candidate.pareto_frontier)
    # Assign duplicate option_id
    mutated_opts[1] = mutated_opts[1].model_copy(update={"option_id": mutated_opts[0].option_id})
    candidate_mutated = candidate.model_copy(update={"pareto_frontier": mutated_opts})

    result = DeterministicVerificationOracle.verify(candidate_mutated, _build_context())
    assert result.is_valid is False
    assert any(v.rule_id == "DUPLICATE_OPTION_ID_ERR" for v in result.violations)


def test_oracle_detects_financial_identity_violation() -> None:
    """Verify that TCO != CAPEX + OPEX is isolated with RFC 6901 JSON pointer."""
    candidate = _build_valid_deliverable()
    bad_f = FinancialProjection(
        currency_iso_4217="EUR",
        capex_allocation=Decimal("50000.00"),
        opex_allocation=Decimal("50000.00"),
        total_cost_of_ownership=Decimal("120000.00"),  # Error: 50k + 50k != 120k
        risk_exposure_p10=Decimal("10000.00"),
        risk_exposure_p50=Decimal("20000.00"),
        risk_exposure_p90=Decimal("30000.00"),
    )
    mutated_opts = list(candidate.pareto_frontier)
    mutated_opts[0] = mutated_opts[0].model_copy(update={"financials": bad_f})
    candidate_mutated = candidate.model_copy(update={"pareto_frontier": mutated_opts})

    result = DeterministicVerificationOracle.verify(candidate_mutated, _build_context())
    assert result.is_valid is False
    viol = next(v for v in result.violations if v.rule_id == "FIN_IDENTITY_ERR")
    assert viol.severity == SeverityLevel.CRITICAL
    assert viol.json_path == "/pareto_frontier/0/financials/total_cost_of_ownership"


def test_oracle_detects_fair_monotonicity_violation() -> None:
    """Verify that inverted FAIR risk percentiles (P10 > P50) trigger formal violation."""
    candidate = _build_valid_deliverable()
    bad_f = FinancialProjection(
        currency_iso_4217="EUR",
        capex_allocation=Decimal("60000.00"),
        opex_allocation=Decimal("90000.00"),
        total_cost_of_ownership=Decimal("150000.00"),
        risk_exposure_p10=Decimal("80000.00"),  # Error: P10 > P50
        risk_exposure_p50=Decimal("40000.00"),
        risk_exposure_p90=Decimal("90000.00"),
    )
    mutated_opts = list(candidate.pareto_frontier)
    mutated_opts[0] = mutated_opts[0].model_copy(update={"financials": bad_f})
    candidate_mutated = candidate.model_copy(update={"pareto_frontier": mutated_opts})

    result = DeterministicVerificationOracle.verify(candidate_mutated, _build_context())
    assert result.is_valid is False
    viol = next(v for v in result.violations if v.rule_id == "FAIR_MONOTONICITY_ERR")
    assert viol.severity == SeverityLevel.CRITICAL
    assert viol.json_path == "/pareto_frontier/0/financials/risk_exposure_p50"


def test_oracle_detects_pareto_orthogonality_violation() -> None:
    """Verify that duplicate optimization axes trigger PARETO_ORTHOGONALITY_ERR."""
    candidate = _build_valid_deliverable()
    mutated_opts = list(candidate.pareto_frontier)
    mutated_opts[1] = mutated_opts[1].model_copy(update={"primary_axis": OptimizationAxis.CAPITAL_EFFICIENCY})
    candidate_mutated = candidate.model_copy(update={"pareto_frontier": mutated_opts})

    result = DeterministicVerificationOracle.verify(candidate_mutated, _build_context())
    assert result.is_valid is False
    viol = next(v for v in result.violations if v.rule_id == "PARETO_ORTHOGONALITY_ERR")
    assert viol.severity == SeverityLevel.CRITICAL


def test_oracle_detects_referential_integrity_violation() -> None:
    """Verify that selecting a non-existent option ID triggers REF_INTEGRITY_ERR."""
    candidate = _build_valid_deliverable()
    candidate_mutated = candidate.model_copy(update={"selected_equilibrium_option_id": "OPT-NONEXISTENT"})

    result = DeterministicVerificationOracle.verify(candidate_mutated, _build_context())
    assert result.is_valid is False
    viol = next(v for v in result.violations if v.rule_id == "REF_INTEGRITY_ERR")
    assert viol.severity == SeverityLevel.CRITICAL


def test_oracle_detects_roadmap_budget_mismatch() -> None:
    """Verify that sum(phases) != selected_option.TCO triggers ROADMAP_BUDGET_MISMATCH."""
    candidate = _build_valid_deliverable()
    bad_phases = [
        candidate.execution_roadmap[0].model_copy(update={"allocated_budget": Decimal("40000.00")}),
        candidate.execution_roadmap[1].model_copy(update={"allocated_budget": Decimal("50000.00")}),
    ]  # Sum = 90k, but selected TCO = 150k
    candidate_mutated = candidate.model_copy(update={"execution_roadmap": bad_phases})

    result = DeterministicVerificationOracle.verify(candidate_mutated, _build_context())
    assert result.is_valid is False
    viol = next(v for v in result.violations if v.rule_id == "ROADMAP_BUDGET_MISMATCH")
    assert viol.severity == SeverityLevel.CRITICAL


def test_oracle_detects_degenerate_budget_allocation() -> None:
    """Verify that dumping 100% of budget into one phase triggers DEGENERATE_BUDGET_ALLOCATION_ERR."""
    candidate = _build_valid_deliverable()
    bad_phases = [
        candidate.execution_roadmap[0].model_copy(update={"allocated_budget": Decimal("150000.00")}),
        candidate.execution_roadmap[1].model_copy(update={"allocated_budget": Decimal("0.00")}),
    ]
    candidate_mutated = candidate.model_copy(update={"execution_roadmap": bad_phases})

    result = DeterministicVerificationOracle.verify(candidate_mutated, _build_context())
    assert result.is_valid is False
    assert any(v.rule_id == "DEGENERATE_BUDGET_ALLOCATION_ERR" for v in result.violations)


def test_oracle_detects_non_contiguous_roadmap_indices() -> None:
    """Verify that non-contiguous phase indices trigger ROADMAP_SEQUENCE_ERR."""
    candidate = _build_valid_deliverable()
    bad_phases = [
        candidate.execution_roadmap[0].model_copy(update={"phase_index": 1}),
        candidate.execution_roadmap[1].model_copy(update={"phase_index": 3}),  # Gap: skipped 2
    ]
    candidate_mutated = candidate.model_copy(update={"execution_roadmap": bad_phases})

    result = DeterministicVerificationOracle.verify(candidate_mutated, _build_context())
    assert result.is_valid is False
    viol = next(v for v in result.violations if v.rule_id == "ROADMAP_SEQUENCE_ERR")
    assert viol.severity == SeverityLevel.HIGH


def test_oracle_detects_ungrounded_epistemic_citation() -> None:
    """Verify that citing non-existent evidence IDs triggers EPISTEMIC_UNGROUNDED_ERR."""
    candidate = _build_valid_deliverable(evidence_ids=["EV-001", "EV-002", "EV-003", "EV-004", "EV-HALLUCINATED"])
    context = _build_context(evidence_ids=["EV-001", "EV-002", "EV-003", "EV-004", "EV-005"])

    result = DeterministicVerificationOracle.verify(candidate, context)
    assert result.is_valid is False
    viol = next(v for v in result.violations if v.rule_id == "EPISTEMIC_UNGROUNDED_ERR")
    assert viol.severity == SeverityLevel.CRITICAL
    assert "EV-HALLUCINATED" in viol.actual_value


def test_oracle_detects_epistemic_monoculture() -> None:
    """Verify that citing single source for >60% of claims triggers EPISTEMIC_MONOCULTURE_ERR."""
    candidate = _build_valid_deliverable(evidence_ids=["EV-001", "EV-001", "EV-001", "EV-001", "EV-002"])
    context = SynthesisContext(
        valid_evidence_ids=frozenset(["EV-001", "EV-002", "EV-003", "EV-004", "EV-005"]),
        target_currency="EUR",
        target_locale="en-US",
        target_isic_code="6201",
        max_single_source_citation_ratio=0.60,
        min_distinct_evidence_threshold=5,
    )
    result = DeterministicVerificationOracle.verify(candidate, context)
    assert result.is_valid is False
    viol = next(v for v in result.violations if v.rule_id == "EPISTEMIC_MONOCULTURE_ERR")
    assert viol.json_path == "/pareto_frontier"


def test_oracle_detects_low_information_density_repetitive_text() -> None:
    """Verify that repetitive boilerplate triggers LOW_INFORMATION_DENSITY_ERR."""
    candidate = _build_valid_deliverable()
    repetitive_text = ("Enterprise digital transformation strategy requires synergy. " * 30).strip()
    candidate_mutated = candidate.model_copy(update={"executive_thesis": repetitive_text})

    result = DeterministicVerificationOracle.verify(candidate_mutated, _build_context())
    assert result.is_valid is False
    assert any(v.rule_id == "LOW_INFORMATION_DENSITY_ERR" for v in result.violations)


def test_pydantic_decimal_coercion_and_bool_rejection() -> None:
    """Verify that financial fields cleanly coerce strings/floats and reject booleans."""
    f = FinancialProjection(
        currency_iso_4217="USD",
        capex_allocation="40000.50",
        opex_allocation=60000.50,
        total_cost_of_ownership="100001.00",
        risk_exposure_p10="1000.00",
        risk_exposure_p50="5000.00",
        risk_exposure_p90="20000.00",
    )
    assert isinstance(f.capex_allocation, Decimal)
    assert f.capex_allocation == Decimal("40000.50")
    assert isinstance(f.opex_allocation, Decimal)
    assert f.opex_allocation == Decimal("60000.50")
    assert f.total_cost_of_ownership == Decimal("100001.00")

    # Boolean is rejected despite being int subclass
    with pytest.raises(ValueError, match="Cannot coerce boolean to Decimal"):
        FinancialProjection(
            currency_iso_4217="USD",
            capex_allocation=True,  # type: ignore[arg-type]
            opex_allocation=Decimal("0.00"),
            total_cost_of_ownership=Decimal("0.00"),
            risk_exposure_p10=Decimal("0.00"),
            risk_exposure_p50=Decimal("0.00"),
            risk_exposure_p90=Decimal("0.00"),
        )
