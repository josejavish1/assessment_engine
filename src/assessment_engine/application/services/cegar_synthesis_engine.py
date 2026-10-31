"""CEGAR (Counterexample-Guided Abstraction Refinement) Synthesis Application Engine (RFC-009).

Orchestrates the Generator-Verifier-Optimizer (GVO) state machine over a strictly
bounded Directed Acyclic Graph (DAG) with N_max = 1 repair attempt.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

from assessment_engine.domain.synthesis.exceptions import UnverifiableSynthesisError
from assessment_engine.domain.synthesis.oracle import (
    DeterministicVerificationOracle,
    SynthesisContext,
)
from assessment_engine.domain.synthesis.schemas import (
    CandidateEnterpriseDeliverable,
    CounterexampleVector,
    VerifiedEnterpriseDeliverable,
)

logger = logging.getLogger(__name__)


@runtime_checkable
class SynthesisGeneratorPort(Protocol):
    """Abstract port for generative synthesis and targeted delta repair."""

    async def generate_candidate(
        self, context: SynthesisContext, evidence_payload: dict[str, Any]
    ) -> CandidateEnterpriseDeliverable:
        """Generate initial unverified candidate deliverable (Attempt 1)."""
        ...

    async def optimize_repair(
        self,
        candidate: CandidateEnterpriseDeliverable,
        counterexamples: CounterexampleVector,
        context: SynthesisContext,
    ) -> CandidateEnterpriseDeliverable:
        """Perform targeted 1-shot AST/JSON mutation addressing formal counterexamples (Attempt 2)."""
        ...


class CegarSynthesisEngine:
    """Orchestrates finite GVO state machine with deterministic verification and fail-fast circuit breaking."""

    def __init__(
        self,
        generator: SynthesisGeneratorPort,
        oracle: type[DeterministicVerificationOracle] = DeterministicVerificationOracle,
    ) -> None:
        """Initialize the CEGAR engine with a generator port adapter and verification oracle."""
        self._generator = generator
        self._oracle = oracle

    async def synthesize(
        self,
        context: SynthesisContext,
        evidence_payload: dict[str, Any],
    ) -> VerifiedEnterpriseDeliverable:
        """Execute the bounded CEGAR synthesis pipeline.

        Topology:
            Generator (Attempt 1) -> Candidate A_0
            Oracle.verify(A_0)    -> CounterexampleVector C_0
            If C_0 is valid       -> Certified Deliverable (1 LLM call)
            Optimizer (Attempt 2) -> Candidate A_1
            Oracle.verify(A_1)    -> CounterexampleVector C_1
            If C_1 is valid       -> Certified Deliverable (2 LLM calls)
            Else                  -> Raise typed UnverifiableSynthesisError (Fail-Fast Circuit Breaker)
        """
        logger.info(
            "Initiating CEGAR synthesis pass 1 (locale=%s, currency=%s, isic=%s)",
            context.target_locale,
            context.target_currency,
            context.target_isic_code,
        )

        # 1. Primary Generative Pass (Attempt 1)
        candidate_0 = await self._generator.generate_candidate(context, evidence_payload)
        c_0 = self._oracle.verify(candidate_0, context, attempt=1)

        if c_0.is_valid:
            logger.info("CEGAR synthesis passed formal verification on attempt 1 with zero violations.")
            return VerifiedEnterpriseDeliverable.model_validate(candidate_0.model_dump())

        logger.warning(
            "CEGAR attempt 1 failed verification with %d violations: %s. Initiating 1-shot repair optimizer.",
            len(c_0.violations),
            [v.rule_id for v in c_0.violations],
        )

        # 2. Targeted 1-Shot Repair Pass (Attempt 2)
        candidate_1 = await self._generator.optimize_repair(candidate_0, c_0, context)
        c_1 = self._oracle.verify(candidate_1, context, attempt=2)

        if c_1.is_valid:
            logger.info("CEGAR synthesis successfully repaired all violations on attempt 2.")
            return VerifiedEnterpriseDeliverable.model_validate(candidate_1.model_dump())

        # 3. Fail-Fast Circuit Breaker (Halt on persistent unverified defect)
        logger.error(
            "CEGAR synthesis halted: attempt 2 failed re-verification with %d violations: %s",
            len(c_1.violations),
            [v.rule_id for v in c_1.violations],
        )
        raise UnverifiableSynthesisError(
            message=(
                f"Candidate enterprise deliverable failed deterministic verification after 1-shot repair pass "
                f"({len(c_1.violations)} persistent formal violations)."
            ),
            violations=[v.model_dump() for v in c_1.violations],
            synthesis_attempt=2,
            context={
                "attempt_1_violations": [v.rule_id for v in c_0.violations],
                "attempt_2_violations": [v.rule_id for v in c_1.violations],
            },
        )
