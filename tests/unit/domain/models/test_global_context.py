"""Unit tests verifying GlobalAssessmentContext and FX evidence enforcement (SR 11-7)."""

import pytest
from pydantic import ValidationError

from assessment_engine.domain.models.global_context import (
    FXRateSnapshot,
    GlobalAssessmentContext,
    JurisdictionParameterPack,
)


def test_global_context_currency_normalization_with_fx() -> None:
    """Verifies that currency normalization succeeds when a valid FX snapshot is present."""
    ctx = GlobalAssessmentContext(
        reporting_currency="EUR",
        fx_snapshots={
            "USD_EUR": FXRateSnapshot(
                source_currency="USD",
                reporting_currency="EUR",
                rate=0.92,
                source="ECB Reference Rates",
                snapshot_date="2026-11-01",
                provenance_reference="ECB_FX_20261101",
            )
        },
    )

    converted = ctx.normalize_monetary_amount(10000.0, "USD")
    assert converted == 9200.0

    # Same currency does not require FX rate
    assert ctx.normalize_monetary_amount(5000.0, "EUR") == 5000.0


def test_global_context_currency_normalization_fails_without_fx() -> None:
    """Verifies that raw multi-currency consolidation without FX evidence raises ValueError."""
    ctx = GlobalAssessmentContext(reporting_currency="EUR", fx_snapshots={})

    with pytest.raises(ValueError, match="Unsupported Context Error: No verified FX snapshot found"):
        ctx.normalize_monetary_amount(10000.0, "USD")


def test_jurisdiction_pack_bounds() -> None:
    """Verifies that jurisdiction parameter packs enforce statutory percentage bounds."""
    pack = JurisdictionParameterPack(
        jurisdiction_code="EU_GDPR",
        statutory_fine_cap_percentage=0.04,
        statutory_fine_ceiling_amount=20000000.0,
        legal_framework_references=["GDPR Art. 83(5)", "NIS2 Art. 34"],
    )
    assert pack.statutory_fine_cap_percentage == 0.04

    with pytest.raises(ValidationError):
        JurisdictionParameterPack(
            jurisdiction_code="INVALID",
            statutory_fine_cap_percentage=1.50,  # Invalid: > 1.0 (100%)
        )
