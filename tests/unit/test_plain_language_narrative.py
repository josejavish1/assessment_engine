"""Unit test suite for PlainLanguageRiskNarrative across multiple enterprise verticals."""

from __future__ import annotations

import pytest

from assessment_engine.domain.actuarial.plain_language_narrative import (
    PlainLanguageRiskNarrative,
)


def test_manufacturing_narrative_references_plant_and_dispatch_english() -> None:
    """Verifies that heavy manufacturing narrative focuses on plant stoppage, weighbridges, and dispatch in English."""
    narrative = PlainLanguageRiskNarrative.format_plain_narrative(
        tower_code="T1",
        kpi_name="Electrical Autonomy",
        failure_desc="Battery autonomy is unknown or under 10 minutes",
        industry="heavy_manufacturing",
        sle=38530.0,
        ale=34615.0,
        rto_hours=6.0,
        hourly_rate=13061.0,
        doc_lang="en",
    )

    # Operational plant tokens in English
    assert "dispatch" in narrative.lower() or "weighbridge" in narrative.lower() or "transport" in narrative.lower()
    # Financial grounding
    assert "38,530" in narrative or "38.530" in narrative
    assert "34,615" in narrative or "34.615" in narrative


def test_healthcare_narrative_references_clinical_systems_and_patients_english() -> None:
    """Verifies that hospital narrative focuses on EHR/PACS, emergency flow, and patient care in English."""
    narrative = PlainLanguageRiskNarrative.format_plain_narrative(
        tower_code="T1",
        kpi_name="Cooling & Power",
        failure_desc="No cooling redundancy in hospital datacenter",
        industry="healthcare",
        sle=45000.0,
        ale=12000.0,
        rto_hours=4.0,
        hourly_rate=15000.0,
        doc_lang="en",
    )

    assert "ehr" in narrative.lower() or "pacs" in narrative.lower() or "patient" in narrative.lower()
    assert "45,000" in narrative or "45.000" in narrative
    assert "12,000" in narrative or "12.000" in narrative


def test_banking_narrative_references_transactions_and_clearing_english() -> None:
    """Verifies that banking narrative focuses on payment clearing, online banking, and ATMs in English."""
    narrative = PlainLanguageRiskNarrative.format_plain_narrative(
        tower_code="T2",
        kpi_name="Compute Clusters",
        failure_desc="Critical resource contention on transactional clusters",
        industry="banking",
        sle=120000.0,
        ale=60000.0,
        rto_hours=2.0,
        hourly_rate=50000.0,
        doc_lang="en",
    )

    assert "banking" in narrative.lower() or "point-of-sale" in narrative.lower() or "authorization" in narrative.lower()
    assert "120,000" in narrative or "120.000" in narrative
    assert "60,000" in narrative or "60.000" in narrative


def test_localized_spanish_narrative_with_injected_translator() -> None:
    """Verifies that passing a localized translator outputs authentic localized narratives."""
    translations = {
        "narrative_header_operational_impact": "• Impacto en la Operación:",
        "narrative_header_economic_cost": "• Justificación del Coste Económico:",
        "industry_disruptions_manufacturing_T1": "Al fallar el suministro eléctrico o clima del CPD, se detiene el pesaje y expedición en fábrica durante {rto_h:.1f} horas.",
        "narrative_cost_just_outage_major": "Ante una contingencia imprevista, la recuperación requiere {rto_hours} horas con impacto de {sle_formatted}.",
    }

    def mock_translator(key: str, **kwargs: str) -> str:
        tmpl = translations.get(key, key)
        try:
            return tmpl.format(**kwargs)
        except Exception:
            return tmpl

    narrative = PlainLanguageRiskNarrative.format_plain_narrative(
        tower_code="T1",
        kpi_name="Autonomía Eléctrica",
        failure_desc="Fallo de suministro",
        industry="manufacturing",
        sle=25000.0,
        ale=10000.0,
        rto_hours=5.0,
        hourly_rate=5000.0,
        doc_lang="es",
        translator=mock_translator,
    )

    assert "• Impacto en la Operación:" in narrative
    assert "• Justificación del Coste Económico:" in narrative
    assert "pesaje y expedición en fábrica" in narrative
    assert "25.000 €" in narrative
