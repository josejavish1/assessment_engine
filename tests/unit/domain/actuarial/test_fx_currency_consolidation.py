"""Unit tests for FX currency consolidation and context validation (SR 11-7)."""

from __future__ import annotations

import pytest

from assessment_engine.domain.models.global_context import (
    FXRateSnapshot,
    GlobalAssessmentContext,
)


def test_mismatched_currencies_without_fx_snapshot_raises_error() -> None:
    """Verifies that differing currencies without FX snapshots raise ValueError upon normalization."""
    ctx = GlobalAssessmentContext(
        tenant_id="TENANT_1",
        business_entity_id="ENTITY_1",
        operating_site_id="SITE_1",
        country_code="US",
        jurisdiction_code="US_STATUTORY",
        source_currency="USD",
        reporting_currency="EUR",
        assessment_period="2026.Q4",
        sector_code="TECH",
        subsector_code="SAAS",
        fx_snapshots={},
    )
    with pytest.raises(
        ValueError, match="Unsupported Context Error: No verified FX snapshot found"
    ):
        ctx.normalize_monetary_amount(10000.0, "USD")


def test_mismatched_currencies_with_missing_pair_in_snapshot_raises_error() -> None:
    """Verifies that missing specific currency pair in fx_snapshots raises ValueError upon normalization."""
    snapshot = FXRateSnapshot(
        source_currency="GBP",
        reporting_currency="EUR",
        rate=1.17,
        source="ECB",
        snapshot_date="2026-10-31",
        provenance_reference="ECB_FX_GBP_EUR",
    )
    ctx = GlobalAssessmentContext(
        tenant_id="TENANT_1",
        business_entity_id="ENTITY_1",
        operating_site_id="SITE_1",
        country_code="US",
        jurisdiction_code="US_STATUTORY",
        source_currency="USD",
        reporting_currency="EUR",
        assessment_period="2026.Q4",
        sector_code="TECH",
        subsector_code="SAAS",
        fx_snapshots={"GBP_EUR": snapshot},
    )
    with pytest.raises(
        ValueError, match="Unsupported Context Error: No verified FX snapshot found"
    ):
        ctx.normalize_monetary_amount(10000.0, "USD")


def test_monetary_normalization_with_verified_snapshot() -> None:
    """Verifies that monetary amounts are properly converted returning rate and snapshot provenance."""
    snapshot = FXRateSnapshot(
        source_currency="USD",
        reporting_currency="EUR",
        rate=0.92,
        source="ECB",
        snapshot_date="2026-10-31",
        provenance_reference="ECB_FX_USD_EUR_2026Q4",
    )
    ctx = GlobalAssessmentContext(
        tenant_id="TENANT_1",
        business_entity_id="ENTITY_1",
        operating_site_id="SITE_1",
        country_code="US",
        jurisdiction_code="US_STATUTORY",
        source_currency="USD",
        reporting_currency="EUR",
        assessment_period="2026.Q4",
        sector_code="TECH",
        subsector_code="SAAS",
        fx_snapshots={"USD_EUR": snapshot},
    )

    converted, rate, prov_id = ctx.normalize_monetary_amount_with_provenance(
        100_000.0, "USD"
    )
    assert converted == 92_000.0
    assert rate == 0.92
    assert prov_id == "ECB_FX_USD_EUR_2026Q4"

    # Direct float normalization
    assert ctx.normalize_monetary_amount(100_000.0, "USD") == 92_000.0

    # Same currency returns identity without error
    ident_amt, ident_rate, ident_id = ctx.normalize_monetary_amount_with_provenance(
        50_000.0, "EUR"
    )
    assert ident_amt == 50_000.0
    assert ident_rate == 1.0
    assert ident_id == "IDENTITY_1_TO_1"


def test_negative_monetary_amount_raises_value_error() -> None:
    """Verifies that negative monetary inputs are rejected by normalize_monetary_amount."""
    ctx = GlobalAssessmentContext.create_legacy_generic_context()
    with pytest.raises(ValueError, match="Monetary amount cannot be negative"):
        ctx.normalize_monetary_amount(-500.0)


def test_compute_context_sha256() -> None:
    """Verifies that compute_context_sha256 returns a 64-character deterministic digest."""
    ctx = GlobalAssessmentContext.create_legacy_generic_context()
    ctx_hash = ctx.compute_context_sha256()
    assert isinstance(ctx_hash, str)
    assert len(ctx_hash) == 64
