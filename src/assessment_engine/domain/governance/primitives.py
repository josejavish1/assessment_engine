"""Canonical Domain Primitives for SSOT Governance (CMMI & Open FAIR).

Defines immutable Value Objects, enums, and numerical quantization sanitizers
to eliminate Split-Brain discrepancies across compilers, calculators, and presentation layers.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation
from enum import StrEnum
from typing import Optional
from pydantic import BaseModel, Field


class MaturityBandCode(StrEnum):
    """Canonical CMMI Maturity Level Codes."""
    INITIAL = "INITIAL"
    REPEATABLE = "REPEATABLE"
    DEFINED = "DEFINED"
    MANAGED = "MANAGED"
    OPTIMIZED = "OPTIMIZED"


class FinancialSeverityCode(StrEnum):
    """Canonical Financial Severity Tiers matching Open FAIR Loss Magnitude (LM1-LM5)."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ResolvedMaturity(BaseModel):
    """Authoritative, immutable evaluation of a CMMI maturity score."""
    model_config = {"frozen": True}

    raw_score: float = Field(..., ge=0.0, le=5.0)
    normalized_score: Decimal = Field(..., ge=Decimal("0.0"), le=Decimal("5.0"))
    level: int = Field(..., ge=1, le=5)
    band_code: MaturityBandCode
    label: str
    ui_semantic_token: str

    @property
    def display_tag(self) -> str:
        """Formatted display tag: e.g. 'Nivel 2 (Gestionado)'."""
        return f"Nivel {self.level} ({self.label})"


class ResolvedFinancialRisk(BaseModel):
    """Authoritative, immutable quantitative risk classification under Open FAIR."""
    model_config = {"frozen": True}

    ale_eur: Decimal = Field(..., ge=Decimal("0.0"))
    reference_revenue_eur: Decimal = Field(..., ge=Decimal("0.0"))
    severity: FinancialSeverityCode
    open_fair_lm: str = Field(..., pattern=r"^LM[1-5]$")
    label: str
    ui_semantic_token: str
    threshold_applied_eur: Decimal
    model_provenance: str = Field(..., description="SR 11-7 model calibration signature")


QUANTIZATION_STEP = Decimal("0.0001")


def sanitize_to_decimal(raw_value: float | int | str | Decimal, precision: str = "0.0001") -> Decimal:
    """
    Sanitizes any numeric representation to an exact Decimal, eliminating IEEE 754 binary floating-point drift.
    Converts floats via str(raw_value) to avoid copying float mantissa approximations.
    """
    try:
        d_val = Decimal(str(raw_value)) if isinstance(raw_value, float) else Decimal(raw_value)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid numeric input for governance resolution: {raw_value!r}") from exc

    if not d_val.is_finite() or d_val < Decimal("0"):
        raise ValueError(f"Invariant violation: non-negative finite real required, got {d_val}")

    return d_val.quantize(Decimal(precision), rounding=ROUND_HALF_EVEN)
