"""Domain exceptions for the CEGAR Synthesis Engine."""

from __future__ import annotations

from typing import Any, Mapping
from assessment_engine.domain.exceptions import AssessmentDomainError


class SynthesisDomainError(AssessmentDomainError):
    """Base domain exception for all deliverable synthesis violations."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "SYNTHESIS_DOMAIN_ERROR",
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code, context=context)


class CounterexampleError(SynthesisDomainError):
    """Raised when an unhandled defect occurs during counterexample processing."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "COUNTEREXAMPLE_ERROR",
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code, context=context)


class UnverifiableSynthesisError(SynthesisDomainError):
    """Raised when candidate deliverable fails deterministic verification after repair pass."""

    def __init__(
        self,
        message: str,
        *,
        violations: list[dict[str, Any]] | None = None,
        synthesis_attempt: int = 2,
        error_code: str = "UNVERIFIABLE_SYNTHESIS_ERROR",
        context: Mapping[str, Any] | None = None,
    ) -> None:
        merged_context = dict(context or {})
        merged_context["synthesis_attempt"] = synthesis_attempt
        merged_context["violation_count"] = len(violations or [])
        if violations:
            merged_context["violations"] = violations
        super().__init__(message, error_code=error_code, context=merged_context)
        self.violations: list[dict[str, Any]] = list(violations or [])
        self.synthesis_attempt: int = synthesis_attempt
