"""Domain layer for Counterexample-Guided Abstraction Refinement (CEGAR) synthesis."""

from __future__ import annotations

from assessment_engine.domain.synthesis.exceptions import (
    CounterexampleError,
    SynthesisDomainError,
    UnverifiableSynthesisError,
)
from assessment_engine.domain.synthesis.oracle import (
    DeterministicVerificationOracle,
    SynthesisContext,
)
from assessment_engine.domain.synthesis.schemas import (
    CandidateEnterpriseDeliverable,
    CounterexampleVector,
    CounterexampleViolation,
    ExecutiveRoadmapPhase,
    FinancialProjection,
    OptimizationAxis,
    SeverityLevel,
    StrategicOption,
    VerifiedEnterpriseDeliverable,
)

__all__ = [
    "CandidateEnterpriseDeliverable",
    "CounterexampleError",
    "CounterexampleVector",
    "CounterexampleViolation",
    "DeterministicVerificationOracle",
    "ExecutiveRoadmapPhase",
    "FinancialProjection",
    "OptimizationAxis",
    "SeverityLevel",
    "StrategicOption",
    "SynthesisContext",
    "SynthesisDomainError",
    "UnverifiableSynthesisError",
    "VerifiedEnterpriseDeliverable",
]
