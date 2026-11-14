"""Unit tests for the immutable ConfigurationRegistry.

Validates Step 1.2 of Phase 1 of ARGON_GLOBAL_TIER1_MASTER_PLAN.md.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from assessment_engine.infrastructure.config_registry import (
    ConfigurationRegistry,
    CountryLaborRatesCatalog,
    RegulatoryJurisdictionCatalog,
    SupportedLocale,
    get_config_registry,
)


def test_supported_locale_normalization():
    """Verify BCP-47 and ISO locale normalization to SupportedLocale enum."""
    assert SupportedLocale.from_str("en-US") == SupportedLocale.EN
    assert SupportedLocale.from_str("es_ES") == SupportedLocale.ES
    assert SupportedLocale.from_str("pt-BR") == SupportedLocale.PT
    assert SupportedLocale.from_str("de-DE") == SupportedLocale.DE
    assert SupportedLocale.from_str("fr-FR") == SupportedLocale.FR
    assert SupportedLocale.from_str("ja-JP") == SupportedLocale.JA
    # Unknown fallback to English
    assert SupportedLocale.from_str("zh-CN") == SupportedLocale.EN
    assert SupportedLocale.from_str("") == SupportedLocale.EN


def test_regulatory_jurisdiction_resolution():
    """Verify deterministic regulatory resolution across multiple countries and sectors."""
    reg = get_config_registry()
    jurisdictions = reg.get_regulatory_jurisdictions()

    # Spain Manufacturing -> NIS2
    assert "NIS2" in jurisdictions.resolve_framework("ES", "MANUFACTURING_LOGISTICS")

    # Japan Manufacturing -> METI Guidelines
    jp_std = jurisdictions.resolve_framework("JP", "MANUFACTURING_LOGISTICS")
    assert "METI" in jp_std or "FISC" in jp_std or "APPI" in jp_std or "ISO" in jp_std

    # US Financial Services -> Basel / PCI / NIST
    us_std = jurisdictions.resolve_framework("US", "FINANCIAL_SERVICES")
    assert len(us_std) > 2

    # Unmapped country fallback -> ISO/IEC 27001
    fallback_std = jurisdictions.resolve_framework("XX", "MANUFACTURING_LOGISTICS")
    assert "ISO" in fallback_std or "IEC" in fallback_std


def test_country_labor_rates_resolution():
    """Verify country labor rates resolution and defaults."""
    reg = get_config_registry()
    rates_cat = reg.get_country_labor_rates()

    # Spanish senior architect rate
    es_rate = rates_cat.get_hourly_rate("ES", "senior_architect_hourly_rate")
    assert es_rate > 30.0

    # Default fallback for unknown role
    default_rate = rates_cat.get_hourly_rate("ES", "unknown_role_xyz", default_rate=75.0)
    assert default_rate == 75.0


def test_immutable_catalog_models():
    """Verify that configuration models are strictly frozen and immutable."""
    reg = get_config_registry()
    jurisdictions = reg.get_regulatory_jurisdictions()

    with pytest.raises(ValidationError):
        # Attempting to mutate a frozen Pydantic model must raise ValidationError
        jurisdictions.catalog = {}


def test_locale_bundle_parity_for_critical_keys():
    """Verify 100% key parity for critical executive cockpit keys across all 6 locales."""
    reg = get_config_registry()
    critical_keys = {
        "chapter_1_exec_summary",
        "kpi_score_header",
        "kpi_band_header",
        "kpi_inaction_header",
        "kpi_regulatory_header",
        "heatmap_section_title",
        "exec_summary_key_findings_lead",
        "decision_horizon_lead",
        "decision_horizon_body",
        "default_operational_risk_title",
        "year_lbl",
        "band_quantitatively_managed",
        "band_optimized",
    }

    missing = reg.verify_key_parity(frozenset(critical_keys))
    assert not missing, f"Missing critical translation keys in locales: {missing}"
