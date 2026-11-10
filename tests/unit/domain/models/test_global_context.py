"""Unit tests verifying GlobalAssessmentContext and FX evidence enforcement (SR 11-7)."""

import pytest
from pydantic import ValidationError

from assessment_engine.domain.models.global_context import (
    FXRateSnapshot,
    GlobalAssessmentContext,
    JurisdictionParameterPack,
)


def _make_valid_context(**overrides) -> GlobalAssessmentContext:
    defaults = {
        "tenant_id": "TENANT_ACME",
        "business_entity_id": "ACME_HOLDINGS_LLC",
        "operating_site_id": "SITE_CHICAGO",
        "country_code": "US",
        "jurisdiction_code": "US_SEC_CYBER",
        "source_currency": "USD",
        "reporting_currency": "EUR",
        "assessment_period": "2026.Q4",
        "sector_code": "FINANCIAL_SERVICES",
        "subsector_code": "PAYMENT_PROCESSORS",
        "fx_snapshots": {
            "USD_EUR": FXRateSnapshot(
                source_currency="USD",
                reporting_currency="EUR",
                rate=0.92,
                source="ECB Reference Rates",
                snapshot_date="2026-11-01",
                provenance_reference="ECB_FX_20261101",
            )
        },
    }
    defaults.update(overrides)
    return GlobalAssessmentContext(**defaults)


def test_global_context_currency_normalization_with_fx() -> None:
    """Verifies that currency normalization succeeds when a valid FX snapshot is present."""
    ctx = _make_valid_context()
    converted = ctx.normalize_monetary_amount(10000.0, "USD")
    assert converted == 9200.0

    # Same currency does not require FX rate
    assert ctx.normalize_monetary_amount(5000.0, "EUR") == 5000.0


def test_global_context_currency_normalization_fails_without_fx() -> None:
    """Verifies that raw multi-currency consolidation without FX evidence raises ValueError."""
    ctx = _make_valid_context(fx_snapshots={})

    with pytest.raises(ValueError, match="Unsupported Context Error: No verified FX snapshot found"):
        ctx.normalize_monetary_amount(10000.0, "USD")


def test_global_context_rejects_unsupported_currency_xyz() -> None:
    """Verifies that unsupported non-ISO currencies like XYZ fail validation explicitly."""
    with pytest.raises(ValidationError, match="not supported in the active ISO 4217 catalog"):
        _make_valid_context(reporting_currency="XYZ")

    with pytest.raises(ValidationError, match="not supported in the active ISO 4217 catalog"):
        _make_valid_context(source_currency="XYZ")


def test_global_context_requires_mandatory_fields() -> None:
    """Verifies that missing context fields fail validation (no silent defaults)."""
    with pytest.raises(ValidationError):
        GlobalAssessmentContext()


def test_jurisdiction_pack_model_default_cannot_be_confirmed() -> None:
    """Invariant: MODEL_DEFAULT cannot have confidence CONFIRMED."""
    with pytest.raises(ValidationError, match="MODEL_DEFAULT cannot have confidence CONFIRMED"):
        JurisdictionParameterPack(
            jurisdiction_code="EU_GDPR",
            provenance="MODEL_DEFAULT",
            confidence="CONFIRMED",
        )
