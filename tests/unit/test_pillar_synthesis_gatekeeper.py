"""Unit tests for SemanticGatekeeper and PillarForensicSynthesizer proportional density.

Verifies:
1. Dynamic word count thresholds (sparse <= 2 findings vs dense > 2 findings).
2. Anti-boilerplate, anti-accusatory, and anti-firmographic rules.
3. Cross-domain contamination isolation.
"""

from __future__ import annotations

import pytest

from assessment_engine.application.services.synthesis.exceptions import SemanticQualityError
from assessment_engine.application.services.synthesis.gatekeeper import SemanticGatekeeper


@pytest.fixture
def gatekeeper() -> SemanticGatekeeper:
    return SemanticGatekeeper()


def test_sparse_evidence_accepts_sober_narrative(gatekeeper: SemanticGatekeeper) -> None:
    # 185 words narrative - valid for sparse evidence (<= 2 findings)
    sober_text = (
        "La arquitectura actual de este pilar opera sobre una base tecnica funcional consolidada "
        "a lo largo del tiempo. Las instalaciones cuentan con equipamiento operativo en produccion "
        "que asegura la ejecucion ininterrumpida de las cargas de trabajo industriales principales. "
        "No obstante, el entorno presenta limitaciones derivadas de la ausencia de telemetria "
        "centralizada y de la dependencia en procedimientos locales ejecutados por el personal "
        "especializado. No consta en el expediente evidencia documental relativa a programas "
        "periodicos de mantenimiento predictivo o ensayos de sobrecarga en condiciones simuladas. "
        "Esta situacion no presupone fallas en el equipamiento fisico, sino un vacio en la "
        "supervision unificada que restringe la visibilidad global sobre el estado de los activos. "
        "En escenarios de contingencia o estres operativo severo, la falta de acreditacion documental "
        "previa condicionaria la velocidad de respuesta, incrementando los tiempos de diagnostico "
        "y obligando a resolver las incidencias mediante analisis manual directo sobre las salas. "
        "Esta exposicion operativa delimita la resiliencia del pilar y senala la necesidad de "
        "formalizar registros tecnicos estructurados para respaldar futuras fases de evolucion. "
        "La transicion gradual hacia esquemas auditados permitira consolidar los niveles de servicio."
    )
    words = len(sober_text.split())
    assert 175 <= words <= 210

    # With evidence_count <= 2, it must pass
    count = gatekeeper.validate(sober_text, tower_id="T1", allowed_evidence_text="", evidence_count=1)
    assert count >= 175


def test_dense_evidence_rejects_sub_220_words(gatekeeper: SemanticGatekeeper) -> None:
    short_text = "Palabra " * 190
    with pytest.raises(SemanticQualityError, match="Semantic Anemia detected"):
        gatekeeper.validate(short_text, tower_id="T1", allowed_evidence_text="", evidence_count=5)


def test_forbidden_accusatory_language_rejected(gatekeeper: SemanticGatekeeper) -> None:
    accusatory_text = (
        ("Palabra " * 150)
        + "La inmadurez severa y negligencia de los equipos tecnicos compromete la infraestructura. "
        + ("Palabra " * 100)
    )
    with pytest.raises(SemanticQualityError, match="punitive tone"):
        gatekeeper.validate(accusatory_text, tower_id="T1", allowed_evidence_text="", evidence_count=3)


def test_forbidden_firmographic_parrot_rejected(gatekeeper: SemanticGatekeeper) -> None:
    parrot_text = (
        ("Palabra " * 120)
        + "Para Cementos Molins, considerando su escala operativa global de 1.144 millones de euros... "
        + ("Palabra " * 120)
    )
    with pytest.raises(SemanticQualityError, match="firmographic parrot"):
        gatekeeper.validate(parrot_text, tower_id="T1", allowed_evidence_text="", evidence_count=3)


def test_cross_domain_contamination_rejected(gatekeeper: SemanticGatekeeper) -> None:
    contaminated_text = (
        ("Palabra " * 120)
        + "Se constata la necesidad de sustituir las impresoras y laptops del puesto de trabajo en la sala. "
        + ("Palabra " * 120)
    )
    with pytest.raises(SemanticQualityError, match="Cross-Domain Contamination in Tower T1"):
        gatekeeper.validate(contaminated_text, tower_id="T1", allowed_evidence_text="rack SAI generador", evidence_count=3)


def test_empty_custom_contamination_matrix_disables_contamination_check() -> None:
    """Verify that passing custom_contamination_matrix={} does not revert to defaults."""
    lenient_gatekeeper = SemanticGatekeeper(custom_contamination_matrix={})
    assert lenient_gatekeeper.contamination_matrix == {}

    text_with_out_of_domain = (
        ("Palabra " * 120)
        + "Se constata la presencia de impresoras y laptops en la sala de servidores. "
        + ("Palabra " * 120)
    )
    # Should not raise Cross-Domain Contamination error because matrix is empty
    count = lenient_gatekeeper.validate(text_with_out_of_domain, tower_id="T1", allowed_evidence_text="", evidence_count=3)
    assert count >= 220


def test_english_consulting_boilerplate_rejected(gatekeeper: SemanticGatekeeper) -> None:
    english_boilerplate_text = (
        ("Word " * 120)
        + "It is essential to implement modern best practices across all datacenter environments. "
        + ("Word " * 120)
    )
    with pytest.raises(SemanticQualityError, match="prescriptive consulting boilerplate"):
        gatekeeper.validate(english_boilerplate_text, tower_id="T1", allowed_evidence_text="", evidence_count=3)
