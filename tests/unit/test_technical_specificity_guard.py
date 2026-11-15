"""
Unit test suite for TechnicalSpecificityGuard.
Verifies:
1. Replacement of ungrounded technical entities with neutral capabilities.
2. Preservation of specific entities when present in the evidence corpus.
3. Case-insensitivity and regex boundary accuracy.
"""

from assessment_engine.domain.validation.technical_specificity_guard import TechnicalSpecificityGuard

def test_specificity_guard_sanitizes_unaccredited_entities():
    sample_text = (
        "La sala de servidores dispone de sistemas VESDA y equipos CRAC con control de temperatura, "
        "mientras que la red de datos emplea BFD para detección de caídas."
    )
    evidence_corpus = "La sala cuenta con climatización estándar y switches de fibra oscura."

    sanitized, replaced = TechnicalSpecificityGuard.sanitize_draft_entities(sample_text, evidence_corpus)

    assert "VESDA" not in sanitized
    assert "CRAC" not in sanitized
    assert "BFD" not in sanitized
    assert "sistemas de detección precoz por aspiración" in sanitized
    assert "unidades de climatización de precisión para salas técnicas" in sanitized
    assert "mecanismos de detección ultrarrápida de fallos de enlace" in sanitized
    assert len(replaced) == 3

def test_specificity_guard_preserves_grounded_entities():
    sample_text = (
        "Los puestos de trabajo emplean BitLocker para cifrado y Entra ID para autenticación."
    )
    evidence_corpus = "La empresa utiliza BitLocker en todos los portátiles corporativos según el inventario."

    sanitized, replaced = TechnicalSpecificityGuard.sanitize_draft_entities(sample_text, evidence_corpus)

    # BitLocker was in the evidence corpus -> MUST be preserved
    assert "BitLocker" in sanitized
    # Entra ID was NOT in the evidence corpus -> MUST be sanitized
    assert "Entra ID" not in sanitized
    assert "directorio corporativo y proveedor centralizado de identidades" in sanitized
    assert replaced == ["entra id"]
