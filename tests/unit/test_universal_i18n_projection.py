from __future__ import annotations

import pytest

from assessment_engine.infrastructure.localization import (
    format_currency,
    format_date_localized,
    format_number,
    resolve_target_language_name,
)


def test_universal_iso_language_resolution():
    """Verify ISO 639-1 language code resolution to standardized English names for prompt projection."""
    assert resolve_target_language_name("it") == "Italian"
    assert resolve_target_language_name("nl") == "Dutch"
    assert resolve_target_language_name("ko") == "Korean"
    assert resolve_target_language_name("de") == "German"
    assert resolve_target_language_name("ja") == "Japanese"
    assert resolve_target_language_name("es") == "Spanish"
    assert resolve_target_language_name("en") == "English"
    assert resolve_target_language_name("fr") == "French"
    assert resolve_target_language_name("pt") == "Portuguese"
    assert resolve_target_language_name("sv") == "Swedish"
    assert resolve_target_language_name("pl") == "Polish"
    assert resolve_target_language_name("en_gb") == "British English"
    assert resolve_target_language_name("en_us") == "American English"
    assert resolve_target_language_name("es_es") == "European Spanish (Spain)"
    assert resolve_target_language_name("es_mx") == "Mexican Spanish"
    assert resolve_target_language_name("pt_br") == "Brazilian Portuguese"
    assert resolve_target_language_name(None) == "Spanish"


def test_universal_date_formatting():
    """Verify localized date formatting across major language families without external dependencies."""
    iso_date = "2026-06-24"
    assert format_date_localized(iso_date, locale="es") == "Junio 2026"
    assert format_date_localized(iso_date, locale="en") == "June 2026"
    assert format_date_localized(iso_date, locale="de") == "Juni 2026"
    assert format_date_localized(iso_date, locale="fr") == "Juin 2026"
    assert format_date_localized(iso_date, locale="it") == "Giugno 2026"
    assert format_date_localized(iso_date, locale="pt") == "Junho 2026"
    assert format_date_localized(iso_date, locale="ja") == "2026年6月"


def test_universal_number_and_currency_formatting():
    """Verify ICU compliant numerical formatting including Swiss apostrophe and French spaces."""
    val = 1426.94

    # Number separations
    assert format_number(val, locale="de") == "1.426,94"
    assert format_number(val, locale="es") == "1.426,94"
    assert format_number(val, locale="en") == "1,426.94"
    assert format_number(val, locale="fr") == "1 426,94"
    assert format_number(val, locale="de_CH") == "1'426.94"

    # Currency formatting
    assert format_currency(val, currency_symbol="€", locale="es") == "1.426,94 €"
    assert format_currency(val, currency_symbol="$", locale="en") == "$1,426.94"
    assert format_currency(val, currency_code="CHF", locale="de_CH") == "CHF 1'426.94"
