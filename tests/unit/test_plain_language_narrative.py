"""Unit test suite for PlainLanguageRiskNarrative across multiple enterprise verticals."""

from __future__ import annotations

import pytest

from assessment_engine.domain.actuarial.plain_language_narrative import (
    PlainLanguageRiskNarrative,
)


def test_manufacturing_narrative_references_plant_and_dispatch() -> None:
    """Verifies that heavy manufacturing narrative focuses on plant stoppage, weighbridges, and dispatch."""
    narrative = PlainLanguageRiskNarrative.format_plain_narrative(
        tower_code="T1",
        kpi_name="Autonomía eléctrica",
        failure_desc="La autonomía de baterías es desconocida o inferior a 10 min",
        industry="heavy_manufacturing",
        sle=38530.0,
        ale=34615.0,
        rto_hours=6.0,
        hourly_rate=13061.0,
    )

    assert "• Impacto en la Operación:" in narrative
    assert "• Justificación del Coste Económico:" in narrative

    # Operational plant tokens
    assert "pesaje" in narrative.lower() or "camiones" in narrative.lower() or "albaranes" in narrative.lower()
    # Financial grounding
    assert "38,530" in narrative
    assert "34,615" in narrative


def test_healthcare_narrative_references_clinical_systems_and_patients() -> None:
    """Verifies that hospital narrative focuses on HIS/PACS, emergency flow, and patient care."""
    narrative = PlainLanguageRiskNarrative.format_plain_narrative(
        tower_code="T1",
        kpi_name="Climatización y Energía",
        failure_desc="Sin redundancia de climatización en CPD hospitalario",
        industry="healthcare",
        sle=45000.0,
        ale=12000.0,
        rto_hours=4.0,
        hourly_rate=15000.0,
    )

    assert "historia clínica" in narrative.lower() or "pacientes" in narrative.lower() or "médico" in narrative.lower()
    assert "45,000" in narrative
    assert "12,000" in narrative


def test_banking_narrative_references_transactions_and_clearing() -> None:
    """Verifies that banking narrative focuses on payment clearing, online banking, and ATMs."""
    narrative = PlainLanguageRiskNarrative.format_plain_narrative(
        tower_code="T2",
        kpi_name="Clústeres de Cómputo",
        failure_desc="Contención crítica en clústeres transaccionales",
        industry="banking",
        sle=120000.0,
        ale=60000.0,
        rto_hours=2.0,
        hourly_rate=50000.0,
    )

    assert "pagos" in narrative.lower() or "transaccional" in narrative.lower() or "banca" in narrative.lower()
    assert "120,000" in narrative
    assert "60,000" in narrative
