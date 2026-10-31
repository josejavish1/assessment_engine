"""Domain-level exception hierarchy for the Assessment Engine.

Pure Python exception classes with zero I/O and zero external dependencies.
"""
from __future__ import annotations

from typing import Any, Mapping


class AssessmentDomainError(Exception):
    """Base exception for all domain-level invariant and business rule violations."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "DOMAIN_ERROR",
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message
        self.error_code: str = error_code
        self.context: dict[str, Any] = dict(context) if context else {}

    def __str__(self) -> str:
        if not self.context:
            return f"[{self.error_code}] {self.message}"
        context_str = ", ".join(f"{k}={v!r}" for k, v in sorted(self.context.items()))
        return f"[{self.error_code}] {self.message} | Context: ({context_str})"

    def to_dict(self) -> dict[str, Any]:
        """Serializes exception metadata for structured logging and telemetry."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
        }


class DomainValidationError(AssessmentDomainError, ValueError):
    """Raised when a domain entity or value object fails invariant validation."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "DOMAIN_VALIDATION_VIOLATION",
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code, context=context)


class InvalidScoreError(DomainValidationError):
    """Raised when an assessment score falls outside the mathematically valid domain range."""

    def __init__(
        self,
        score: float,
        min_allowed: float = 0.0,
        max_allowed: float = 100.0,
    ) -> None:
        super().__init__(
            f"Score {score} is out of valid mathematical bounds [{min_allowed}, {max_allowed}].",
            error_code="INVALID_SCORE_RANGE",
            context={
                "score": score,
                "min_allowed": min_allowed,
                "max_allowed": max_allowed,
            },
        )


class MaturityBandContiguityError(DomainValidationError):
    """Raised when maturity bands contain gaps, overlaps, or fail to cover the spectrum."""

    def __init__(
        self,
        message: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            error_code="MATURITY_BAND_CONTIGUITY_ERROR",
            context=context,
        )


class UnmappedScoreError(AssessmentDomainError):
    """Raised when a valid score cannot be resolved to any configured maturity band."""

    def __init__(self, score: float) -> None:
        super().__init__(
            f"No maturity band configured to resolve score: {score}.",
            error_code="UNMAPPED_MATURITY_SCORE",
            context={"score": score},
        )
