"""Unit tests for DeclarativeI18nResolver (RFC-026 PR-1)."""

from __future__ import annotations

import pytest

from assessment_engine.i18n.resolver import (
    DeclarativeI18nResolver,
    MissingLocalizationKeyError,
)


def test_declarative_resolver_resolves_canonical_chapters() -> None:
    resolver = DeclarativeI18nResolver()

    # English canonical keys
    en_ch1 = resolver.resolve("chapter_1_executive_summary", "en")
    assert "Executive Summary" in en_ch1
    en_ch3 = resolver.resolve("chapter_3_diagnosis_cross_cutting", "en")
    assert "Technical Diagnosis" in en_ch3 or "Maturity Dashboard" in en_ch3

    # Multi-lingual dynamic verification (non-empty string resolved)
    es_ch1 = resolver.resolve("chapter_1_executive_summary", "es")
    assert len(es_ch1.strip()) > 10
    es_ch3 = resolver.resolve("chapter_3_diagnosis_cross_cutting", "es")
    assert len(es_ch3.strip()) > 10


def test_declarative_resolver_raises_on_missing_key() -> None:
    resolver = DeclarativeI18nResolver()
    with pytest.raises(MissingLocalizationKeyError):
        resolver.resolve("unregistered_arbitrary_key_99999", "en")


def test_declarative_currency_formatting() -> None:
    # Continental format with EUR
    eur_formatted = DeclarativeI18nResolver.format_currency(1234567.89, currency_code="EUR", locale="es")
    assert "1.234.567,89 €" == eur_formatted

    # Anglo-Saxon format with USD
    usd_formatted = DeclarativeI18nResolver.format_currency(1234567.89, currency_code="USD", locale="en")
    assert "$1,234,567.89" == usd_formatted

    # Zero-decimal currency format with JPY
    jpy_formatted = DeclarativeI18nResolver.format_currency(1250000.0, currency_code="JPY", locale="en")
    assert "¥1,250,000" == jpy_formatted
