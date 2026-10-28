from __future__ import annotations

import pytest

from assessment_engine.application.run_executive_annex_synthesizer import (
    derive_pillar_executive_reading,
    infer_initiative_priority,
)
from assessment_engine.infrastructure.localization import t


def test_infer_initiative_priority_multilingual():
    """Verify that infer_initiative_priority returns localized labels across locales."""
    mock_high_proj = {"priority": "Alta", "duration": "H1 (Mes 1-3)"}
    assert infer_initiative_priority(mock_high_proj, locale="es") == "Alta"
    assert infer_initiative_priority(mock_high_proj, locale="en") == "High"
    assert infer_initiative_priority(mock_high_proj, locale="de") == "Hoch"
    assert infer_initiative_priority(mock_high_proj, locale="ja") == "高"

    mock_low_proj = {"priority": "Baja", "duration": "H3 (Mes 12-24)"}
    assert infer_initiative_priority(mock_low_proj, locale="es") == "Baja"
    assert infer_initiative_priority(mock_low_proj, locale="en") == "Low"
    assert infer_initiative_priority(mock_low_proj, locale="de") == "Niedrig"
    assert infer_initiative_priority(mock_low_proj, locale="ja") == "低"


def test_derive_pillar_executive_reading_modular_structure():
    """Verify that derive_pillar_executive_reading produces a well-structured 3-part narrative."""
    class MockFinding:
        def __init__(self, target_state, vuln, ale, desc):
            self.target_state = target_state
            self.vulnerability_level = vuln
            self.fair_ale_score = ale
            self.risk_observed = desc
            self.finding = desc
            self.impact = "Impacto operacional severo"
            self.business_risk = "Impacto operacional severo"

    class MockPillar:
        def __init__(self, name, score):
            self.pilar_name = name
            self.score = score
            self.health_check_asis = [
                MockFinding("Observabilidad Unificada", 5, 250000.0, "Ausencia de métricas centralizadas."),
                MockFinding("Gestión de Parches", 3, 50000.0, "Procesos estables de actualización."),
            ]

    pillar = MockPillar("Observabilidad", 2.1)
    reading = derive_pillar_executive_reading(pillar, idx=0, locale="es")

    assert "**Situación de Capacidades (KPIs):**" in reading
    assert "**Brechas y Consecuencias Operativas:**" in reading
    assert "**Justificación de la Nota:**" in reading
    assert "Observabilidad" in reading
    assert "2,10 / 5,00" in reading


def test_coi_multilingual_templates():
    """Verify that COI templates format correctly in multiple languages."""
    assert t("coi_3y_ord", locale="es", amount="150.000 €") == "~150.000 € en 3 años"
    assert t("coi_3y_ord", locale="en", amount="$150,000") == "~$150,000 in 3 years"
    assert t("coi_3y_ord", locale="de", amount="150.000 €") == "~150.000 € in 3 Jahren"
    assert t("coi_3y_ord", locale="ja", amount="150,000円") == "~3年間で150,000円"
