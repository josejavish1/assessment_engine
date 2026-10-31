"""Deterministic Verification Oracle for CEGAR Synthesis (RFC-009).

Sub-millisecond pure-code invariant evaluator enforcing mathematical, financial,
epistemic, and structural guarantees with zero LLM invocations.
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
import re
from typing import Any
import zlib
from pydantic import BaseModel, ConfigDict, Field

from assessment_engine.domain.synthesis.schemas import (
    CandidateEnterpriseDeliverable,
    CounterexampleVector,
    CounterexampleViolation,
    OptimizationAxis,
    SeverityLevel,
)


class SynthesisContext(BaseModel):
    """Immutable runtime execution context injected into the Deterministic Oracle."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    valid_evidence_ids: frozenset[str] = Field(default_factory=frozenset)
    target_currency: str = Field(default="EUR", min_length=3, max_length=3)
    target_locale: str = Field(default="en")
    target_isic_code: str = Field(default="6201")
    min_compression_ratio: float = Field(default=0.38, gt=0.0, lt=1.0)
    min_ttr_ratio: float = Field(default=0.55, gt=0.0, lt=1.0)
    max_single_source_citation_ratio: float = Field(default=0.60, gt=0.0, lt=1.0)
    min_distinct_evidence_threshold: int = Field(default=5, ge=1)


class DeterministicVerificationOracle:
    """Zero-LLM, sub-millisecond invariant auditor for candidate deliverables."""

    @classmethod
    def verify(
        cls,
        candidate: CandidateEnterpriseDeliverable,
        context: SynthesisContext,
        attempt: int = 1,
    ) -> CounterexampleVector:
        """Run all formal mathematical, epistemic, and structural verification rules.

        Returns an empty CounterexampleVector if all invariants pass; otherwise,
        returns an isolated list of CounterexampleViolations with RFC 6901 JSON pointers.
        """
        violations: list[CounterexampleViolation] = []

        # 1. Financial Invariants (Accounting Identity & FAIR Monotonicity)
        for idx, option in enumerate(candidate.pareto_frontier):
            f = option.financials
            exp_path = f"/pareto_frontier/{idx}/financials"

            expected_tco = f.capex_allocation + f.opex_allocation
            if f.total_cost_of_ownership != expected_tco:
                violations.append(
                    CounterexampleViolation(
                        rule_id="FIN_IDENTITY_ERR",
                        json_path=f"{exp_path}/total_cost_of_ownership",
                        severity=SeverityLevel.CRITICAL,
                        expected_invariant=f"total_cost_of_ownership must equal capex ({f.capex_allocation}) + opex ({f.opex_allocation}) = {expected_tco}",
                        actual_value=str(f.total_cost_of_ownership),
                        remediation_directive=f"Reconcile financials so that total_cost_of_ownership == {expected_tco} exactly.",
                    )
                )

            if not (f.risk_exposure_p10 <= f.risk_exposure_p50 <= f.risk_exposure_p90):
                violations.append(
                    CounterexampleViolation(
                        rule_id="FAIR_MONOTONICITY_ERR",
                        json_path=f"{exp_path}/risk_exposure_p50",
                        severity=SeverityLevel.CRITICAL,
                        expected_invariant=f"P10 ({f.risk_exposure_p10}) <= P50 ({f.risk_exposure_p50}) <= P90 ({f.risk_exposure_p90})",
                        actual_value=f"P10={f.risk_exposure_p10}, P50={f.risk_exposure_p50}, P90={f.risk_exposure_p90}",
                        remediation_directive="Ensure FAIR percentile ordering monotonically satisfies risk_exposure_p10 <= p50 <= p90.",
                    )
                )

        # 2. Pareto Orthogonality (3 distinct strategic vectors)
        axes = [opt.primary_axis for opt in candidate.pareto_frontier]
        unique_axes = set(axes)
        if len(unique_axes) != 3 or unique_axes != set(OptimizationAxis):
            violations.append(
                CounterexampleViolation(
                    rule_id="PARETO_ORTHOGONALITY_ERR",
                    json_path="/pareto_frontier",
                    severity=SeverityLevel.CRITICAL,
                    expected_invariant="Pareto frontier must contain exactly 3 orthogonal options mapping to CAPITAL_EFFICIENCY, OPERATIONAL_RESILIENCE, and EXECUTION_VELOCITY",
                    actual_value=f"{[a.value for a in axes]}",
                    remediation_directive="Restructure pareto_frontier so every option champions a unique OptimizationAxis.",
                )
            )

        # 3. Referential Integrity (Selected Option in Frontier)
        option_map = {opt.option_id: opt for opt in candidate.pareto_frontier}
        if candidate.selected_equilibrium_option_id not in option_map:
            violations.append(
                CounterexampleViolation(
                    rule_id="REF_INTEGRITY_ERR",
                    json_path="/selected_equilibrium_option_id",
                    severity=SeverityLevel.CRITICAL,
                    expected_invariant=f"Selected option must exist in pareto_frontier IDs: {list(option_map.keys())}",
                    actual_value=candidate.selected_equilibrium_option_id,
                    remediation_directive=f"Set selected_equilibrium_option_id to one of {list(option_map.keys())}.",
                )
            )
        else:
            # 4. Roadmap Financial Reconciliation against Selected Option TCO
            selected_opt = option_map[candidate.selected_equilibrium_option_id]
            roadmap_total = sum(
                (phase.allocated_budget for phase in candidate.execution_roadmap),
                Decimal("0.00"),
            )
            if roadmap_total != selected_opt.financials.total_cost_of_ownership:
                violations.append(
                    CounterexampleViolation(
                        rule_id="ROADMAP_BUDGET_MISMATCH",
                        json_path="/execution_roadmap",
                        severity=SeverityLevel.CRITICAL,
                        expected_invariant=f"Sum of roadmap phase budgets ({roadmap_total}) must equal selected option TCO ({selected_opt.financials.total_cost_of_ownership})",
                        actual_value=str(roadmap_total),
                        remediation_directive=f"Adjust allocated_budget across phases so their sum equals {selected_opt.financials.total_cost_of_ownership}.",
                    )
                )

            # 5. Degenerate Budget Allocation Check (if len > 1, no single phase consumes 0% or 100%)
            if len(candidate.execution_roadmap) > 1:
                tco = selected_opt.financials.total_cost_of_ownership
                for p_idx, phase in enumerate(candidate.execution_roadmap):
                    if phase.allocated_budget == Decimal("0.00") or (tco > 0 and phase.allocated_budget == tco):
                        violations.append(
                            CounterexampleViolation(
                                rule_id="DEGENERATE_BUDGET_ALLOCATION_ERR",
                                json_path=f"/execution_roadmap/{p_idx}/allocated_budget",
                                severity=SeverityLevel.HIGH,
                                expected_invariant=f"No phase in multi-phase roadmap may consume 0.00 or 100% of TCO ({tco})",
                                actual_value=str(phase.allocated_budget),
                                remediation_directive="Distribute financial allocation realistically across roadmap phases.",
                            )
                        )

        # 6. Sequential Phase Ordering (contiguous 1..N)
        expected_indices = list(range(1, len(candidate.execution_roadmap) + 1))
        actual_indices = [p.phase_index for p in candidate.execution_roadmap]
        if actual_indices != expected_indices:
            violations.append(
                CounterexampleViolation(
                    rule_id="ROADMAP_SEQUENCE_ERR",
                    json_path="/execution_roadmap",
                    severity=SeverityLevel.HIGH,
                    expected_invariant=f"Phase indices must be contiguous sequential numbers {expected_indices}",
                    actual_value=f"{actual_indices}",
                    remediation_directive=f"Renumber roadmap phase indices contiguously from 1 to {len(candidate.execution_roadmap)}.",
                )
            )

        # 7. Epistemic Citation Graph Resolution against Evidence Registry
        if context.valid_evidence_ids:
            all_citations: list[str] = []
            for o_idx, opt in enumerate(candidate.pareto_frontier):
                for c_idx, cite in enumerate(opt.supporting_evidence_ids):
                    all_citations.append(cite)
                    if cite not in context.valid_evidence_ids:
                        violations.append(
                            CounterexampleViolation(
                                rule_id="EPISTEMIC_UNGROUNDED_ERR",
                                json_path=f"/pareto_frontier/{o_idx}/supporting_evidence_ids/{c_idx}",
                                severity=SeverityLevel.CRITICAL,
                                expected_invariant=f"Citation '{cite}' must exist in input Evidence Registry",
                                actual_value=cite,
                                remediation_directive=f"Replace '{cite}' with a valid ID from the evidence registry.",
                            )
                        )

            for p_idx, phase in enumerate(candidate.execution_roadmap):
                for c_idx, cite in enumerate(phase.evidence_citations):
                    all_citations.append(cite)
                    if cite not in context.valid_evidence_ids:
                        violations.append(
                            CounterexampleViolation(
                                rule_id="EPISTEMIC_UNGROUNDED_ERR",
                                json_path=f"/execution_roadmap/{p_idx}/evidence_citations/{c_idx}",
                                severity=SeverityLevel.CRITICAL,
                                expected_invariant=f"Citation '{cite}' must exist in input Evidence Registry",
                                actual_value=cite,
                                remediation_directive=f"Replace '{cite}' with a valid ID from the evidence registry.",
                            )
                        )

            # 8. Citation Diversity & Monoculture Guard
            if (
                len(context.valid_evidence_ids) >= context.min_distinct_evidence_threshold
                and all_citations
            ):
                counts = Counter(all_citations)
                max_source, max_count = counts.most_common(1)[0]
                ratio = max_count / len(all_citations)
                if ratio > context.max_single_source_citation_ratio:
                    violations.append(
                        CounterexampleViolation(
                            rule_id="EPISTEMIC_MONOCULTURE_ERR",
                            json_path="/supporting_evidence_ids",
                            severity=SeverityLevel.HIGH,
                            expected_invariant=f"Single source citation ratio ({ratio:.2f}) must not exceed {context.max_single_source_citation_ratio:.2f}",
                            actual_value=f"Source '{max_source}' accounts for {ratio * 100:.1f}% of all citations",
                            remediation_directive="Diversify evidentiary citations across multiple distinct evidence IDs.",
                        )
                    )

        # 9. Lexical Entropy & Compression Ratio (Anti-Gaming / Goodhart's Law)
        text_nodes = [
            ("/executive_thesis", candidate.executive_thesis),
            ("/equilibrium_justification", candidate.equilibrium_justification),
        ]
        for o_idx, opt in enumerate(candidate.pareto_frontier):
            text_nodes.append((f"/pareto_frontier/{o_idx}/architectural_rationale", opt.architectural_rationale))
            text_nodes.append((f"/pareto_frontier/{o_idx}/sacrificed_dimension_analysis", opt.sacrificed_dimension_analysis))

        for json_path, text in text_nodes:
            cls._check_information_density(json_path, text, context, violations)

        return CounterexampleVector(synthesis_attempt=attempt, violations=violations)

    @classmethod
    def _check_information_density(
        cls,
        json_path: str,
        text: str,
        context: SynthesisContext,
        violations: list[CounterexampleViolation],
    ) -> None:
        """Evaluate information density via zlib compression ratio or Type-Token Ratio."""
        raw_bytes = text.strip().encode("utf-8")
        if len(raw_bytes) > 500:
            compressed = zlib.compress(raw_bytes, level=9)
            ratio = len(compressed) / len(raw_bytes)
            if ratio < context.min_compression_ratio:
                violations.append(
                    CounterexampleViolation(
                        rule_id="LOW_INFORMATION_DENSITY_ERR",
                        json_path=json_path,
                        severity=SeverityLevel.HIGH,
                        expected_invariant=f"Compression ratio ({ratio:.3f}) must meet or exceed {context.min_compression_ratio:.3f}",
                        actual_value=f"{ratio:.3f}",
                        remediation_directive="Eliminate repetitive syntactical filler and provide substantive executive insights.",
                    )
                )
        else:
            # Short-block Type-Token Ratio (TTR)
            words = [w.lower() for w in re.findall(r"\b\w+\b", text)]
            if len(words) >= 10:
                ttr = len(set(words)) / len(words)
                if ttr < context.min_ttr_ratio:
                    violations.append(
                        CounterexampleViolation(
                            rule_id="LOW_INFORMATION_DENSITY_ERR",
                            json_path=json_path,
                            severity=SeverityLevel.HIGH,
                            expected_invariant=f"Type-Token Ratio ({ttr:.3f}) must meet or exceed {context.min_ttr_ratio:.3f}",
                            actual_value=f"{ttr:.3f}",
                            remediation_directive="Avoid repetitive vocabulary in short-form analyses.",
                        )
                    )
