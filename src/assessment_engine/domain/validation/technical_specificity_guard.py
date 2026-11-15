"""
Technical Specificity Guard (Fail-Closed Entity Sanitizer & Validator).

Enforces closed-world evidence grounding by detecting unaccredited technical
products, protocols, and proprietary brand names in generated narrative drafts
that do not appear in the accredited evidence ledger for that tower.

If an unaccredited specific entity is detected, this guard deterministically
substitutes it with an authoritative, vendor-neutral consulting capability description,
preventing hallucinated technical architectures from entering the executive deliverable.
"""

from typing import Dict, List, Set, Tuple
import re
import logging

logger = logging.getLogger(__name__)

# Disallowed specific entities mapped to their vendor-neutral capability abstractions
# when the specific entity is NOT present in the verified evidence corpus.
SPECIFICITY_ABSTRACTION_MAP: Dict[str, str] = {
    # T1 Facilities
    r"\bVESDA\b": "sistemas de detección precoz por aspiración",
    r"\bCRAC\b": "unidades de climatización de precisión para salas técnicas",
    r"\bATS\b": "conmutadores automáticos de transferencia eléctrica",
    r"\blectores biométricos\b": "mecanismos de control de acceso físico reforzado",
    r"\bNVR\b": "sistemas de videovigilancia y grabación de seguridad física",
    r"\bDCIM\b": "herramientas de gestión integral de infraestructuras de centro de datos",

    # T3 Network
    r"\bBFD\b": "mecanismos de detección ultrarrápida de fallos de enlace",
    r"\bSNMPv3\b": "protocolos seguros de monitorización de red",
    r"\btelemetría de buffers\b": "supervisión avanzada de rendimiento de conmutación",
    r"\bVRF\b": "segmentación virtual de tablas de enrutamiento",

    # T9 Workplace
    r"\bZero-Touch Provisioning\b": "aprovisionamiento desasistido de puestos de trabajo",
    r"\bBitLocker\b": "mecanismos de cifrado de almacenamiento local en endpoints",
    r"\bEntra ID\b": "directorio corporativo y proveedor centralizado de identidades",
    r"\bSAML 2\.0\b": "protocolos federados de autenticación única",
    r"\bOpenID Connect\b": "estándares modernos de federación de identidad",
    r"\bSSPR\b": "autoservicio de restablecimiento de credenciales",
    r"\bDLP\b": "políticas de prevención de fugas de información en el endpoint",
}


class TechnicalSpecificityGuard:
    """Enforces evidence gating by abstracting ungrounded specific technical entities."""

    @classmethod
    def sanitize_draft_entities(
        cls,
        text: str,
        accredited_evidence_corpus: str,
    ) -> Tuple[str, List[str]]:
        """Scans the text for specific technical entities. If an entity is not grounded

        in the accredited evidence corpus, replaces it with its vendor-neutral abstraction.
        Returns the sanitized text and a list of sanitized entities.
        """
        if not text:
            return text, []

        sanitized_text = text
        sanitized_entities = []
        evidence_lower = accredited_evidence_corpus.lower()

        for pattern, neutral_replacement in SPECIFICITY_ABSTRACTION_MAP.items():
            # Check if pattern matches in text
            matches = list(re.finditer(pattern, sanitized_text, flags=re.IGNORECASE))
            if not matches:
                continue

            # Check if this specific entity exists in the evidence corpus
            raw_keyword = pattern.replace(r"\b", "").replace(r"\.", ".").lower()
            if raw_keyword in evidence_lower:
                # Grounded in evidence -> permit explicit mention
                continue

            # Unaccredited specific entity detected -> sanitize to neutral capability
            sanitized_text = re.sub(pattern, neutral_replacement, sanitized_text, flags=re.IGNORECASE)
            sanitized_entities.append(raw_keyword)
            logger.info(
                "[SpecificityGuard] Replaced ungrounded entity '%s' with '%s'",
                raw_keyword,
                neutral_replacement,
            )

        return sanitized_text, sanitized_entities
