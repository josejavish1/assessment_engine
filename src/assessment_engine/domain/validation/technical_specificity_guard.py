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
    r"\bVESDA\b": "aspirating smoke detection systems",
    r"\bCRAC\b": "precision cooling units for technical rooms",
    r"\bATS\b": "automatic transfer switches",
    r"\blectores biom\u00e9tricos\b": "reinforced physical access controls",
    r"\bNVR\b": "physical security video surveillance systems",
    r"\bDCIM\b": "data center infrastructure management tools",

    # T3 Network
    r"\bBFD\b": "sub-second link fault detection mechanisms",
    r"\bSNMPv3\b": "secure network monitoring protocols",
    r"\btelemetr\u00eda de buffers\b": "advanced switching performance telemetry",
    r"\bVRF\b": "virtual routing table segmentation",

    # T9 Workplace
    r"\bZero-Touch Provisioning\b": "unattended workplace deployment",
    r"\bBitLocker\b": "local endpoint storage encryption",
    r"\bEntra ID\b": "enterprise identity and directory services",
    r"\bSAML 2\.0\b": "federated single sign-on protocols",
    r"\bOpenID Connect\b": "modern identity federation standards",
    r"\bSSPR\b": "self-service password reset",
    r"\bDLP\b": "endpoint data loss prevention policies",

    # Universal Governance / Invariant Guardrails
    r"\bRTO contractual\b": "operational recovery estimate",
    r"\bRTO Contractual\b": "operational recovery estimate",
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
