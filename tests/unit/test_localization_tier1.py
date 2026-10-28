import pytest

from assessment_engine.infrastructure.localization import (
    format_currency,
    format_number,
    get_archimate_catalog,
    get_localized_string,
)


def test_icu_regional_number_formatting():
    """Verify that numbers format according to ICU standards across European and Anglo-American locales."""
    # Continental European (Spain, Germany) -> '.' for thousands, ',' for decimals
    assert format_number(1234567.89, locale="es") == "1.234.567,89"
    assert format_number(1234567.89, locale="de") == "1.234.567,89"

    # Anglo-American -> ',' for thousands, '.' for decimals
    assert format_number(1234567.89, locale="en") == "1,234,567.89"

    # Swiss standard -> "'" for thousands, '.' for decimals
    assert format_number(1234567.89, locale="de_ch") == "1'234'567.89"


def test_icu_regional_currency_formatting():
    """Verify that currency formats position symbols and use regional conventions accurately."""
    # Spain / EUR -> '1.426,94 €'
    assert format_currency(1426.94, currency_code="EUR", locale="es") == "1.426,94 €"

    # US / USD -> '$1,426.94'
    assert format_currency(1426.94, currency_code="USD", locale="en") == "$1,426.94"

    # UK / GBP -> '£1,426.94'
    assert format_currency(1426.94, currency_code="GBP", locale="en") == "£1,426.94"

    # Switzerland / CHF -> 'CHF 1'426.94'
    assert format_currency(1426.94, currency_code="CHF", locale="de_ch") == "CHF 1'426.94"


def test_localized_string_template_interpolation():
    """Verify that get_localized_string correctly populates parameters from locales.json."""
    # Spanish audit justification template
    es_msg = get_localized_string(
        "audit_justification_template",
        locale="es",
        downtime_hours="6.0",
        hourly_rate="1.426,94 €",
        downtime_cost="8.561,64 €",
        sre_cost="663,92 €",
        sre_recovery_hours="7.4",
        sre_hourly_rate="45,00 €",
    )
    assert "Pérdida primaria contable estimada en evento base: 6.0h de parada operativa a 1.426,94 €/h" in es_msg
    assert "8.561,64 €" in es_msg

    # English audit justification template
    en_msg = get_localized_string(
        "audit_justification_template",
        locale="en",
        downtime_hours="6.0",
        hourly_rate="$1,426.94",
        downtime_cost="$8,561.64",
        sre_cost="$663.92",
        sre_recovery_hours="7.4",
        sre_hourly_rate="$45.00",
    )
    assert "Estimated primary accounting loss in base event: 6.0h operational downtime at $1,426.94/h" in en_msg
    assert "$8,561.64" in en_msg


def test_archimate_catalog_dynamically_loaded_from_locales():
    """Verify that ArchiMate deliverables catalog is loaded dynamically from locales.json with zero code hardcoding."""
    cat_es = get_archimate_catalog(locale="es")
    assert "kubernetes" in cat_es
    assert "Módulo Terraform de Orquestación de Contenedores" in cat_es["kubernetes"]

    cat_en = get_archimate_catalog(locale="en")
    assert "kubernetes" in cat_en
    assert "Container Orchestration IaC Module" in cat_en["kubernetes"]
