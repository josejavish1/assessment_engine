"""
Technical Specificity Guard (Fail-Closed Entity Sanitizer & Validator).

Enforces closed-world evidence grounding by detecting unaccredited technical
products, protocols, and proprietary brand names in generated narrative drafts
that do not appear in the accredited evidence ledger for that tower.

If an unaccredited specific entity is detected, this guard deterministically
substitutes it with an authoritative, vendor-neutral consulting capability description,
preventing hallucinated technical architectures from entering the executive deliverable.
"""

from typing import Dict, List, Tuple
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
    r"\bNVR\b": "physical security video surveillance systems",
    r"\bCCTV\b": "video surveillance monitoring systems",
    r"\bDCIM\b": "data center infrastructure management tools",
    r"\bN\+1\s*(?:or|o)\s*2N\b": "modular redundancy architecture",

    # T3 Network
    r"\bBGP\b": "dynamic routing protocols",
    r"\bBFD\b": "sub-second link fault detection mechanisms",
    r"\bSNMPv3\b": "secure network monitoring protocols",
    r"\bSFP\+\b": "high-speed network interfaces",
    r"\bQSFP\+\b": "optical aggregation interfaces",
    r"\bVRF\b": "virtual routing table segmentation",

    # T4 Storage
    r"\bNetApp Volume Encryption\b": "storage encryption at rest",
    r"\bVolume Encryption\b": "storage encryption at rest",
    r"\bWORM\b": "storage immutability policies",
    r"\bVAAI\b": "storage hardware offload primitives",
    r"\bSVM\b": "storage virtual machines",

    # T6 Identity & Security / T9 Workplace
    r"\bcentralized PAM vault\b": "centralized privileged access management controls",
    r"\bsession recording\b": "session audit traceability",
    r"\bcommand logging\b": "command-level administrative monitoring",
    r"\bRODC\b": "read-only directory services",
    r"\bEDR\b": "endpoint detection and response controls",
    r"\bZero-Touch Provisioning\b": "unattended workplace deployment",
    r"\bBitLocker\b": "local endpoint storage encryption",
    r"\bEntra ID\b": "enterprise identity and directory services",
    r"\bSAML\s*(?:2(?:\.0)?)?\b": "federated single sign-on protocols",
    r"\bOpenID Connect\b": "modern identity federation standards",
    r"\bSSPR\b": "self-service password reset",
    r"\bDLP\b": "endpoint data loss prevention policies",
    r"\bWindows 10/11 Enterprise\b": "corporate endpoint operating systems",
    r"\bCSAT/NPS\b": "end-user satisfaction metrics",

    # Universal Governance / Invariant Guardrails
    r"\bRTO contractual\b": "operational recovery estimate",
    r"\bRTO Contractual\b": "operational recovery estimate",
}


def _load_localized_specificity_patterns() -> Dict[str, str]:
    """Dynamically loads localized non-English regex patterns from configuration."""
    from pathlib import Path
    import json

    cfg_path = (
        Path(__file__).resolve().parents[4]
        / "engine_config"
        / "policies"
        / "epistemic_dependencies.json"
    )
    if cfg_path.exists():
        try:
            cfg_data = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
            return cfg_data.get("technical_specificity_patterns", {})
        except Exception:
            pass
    return {}


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

        patterns_to_scan = dict(SPECIFICITY_ABSTRACTION_MAP)
        patterns_to_scan.update(_load_localized_specificity_patterns())

        for pattern, neutral_replacement in patterns_to_scan.items():
            # Check if pattern matches in text
            matches = list(re.finditer(pattern, sanitized_text, flags=re.IGNORECASE))
            if not matches:
                continue

            # Check if this specific entity exists in the evidence corpus
            raw_keyword = pattern.replace(r"\b", "").replace(r"\.", ".").replace(r"\+", "+").lower()
            if raw_keyword in evidence_lower:
                # Check for negation in evidence: e.g. "no usamos BGP"
                negation_pattern = re.compile(
                    r"\b(?:no\s+(?:tenemos|usamos|hay|disponemos|contamos\s+con)|carece\s+de)\s+[^.\n]*"
                    + re.escape(raw_keyword),
                    re.IGNORECASE,
                )
                if not negation_pattern.search(evidence_lower):
                    # Grounded in positive evidence -> permit explicit mention
                    continue

            # Unaccredited or negated specific entity detected -> sanitize to neutral capability
            sanitized_text = re.sub(pattern, neutral_replacement, sanitized_text, flags=re.IGNORECASE)
            sanitized_entities.append(raw_keyword)
            logger.info(
                "[SpecificityGuard] Replaced ungrounded entity '%s' with '%s'",
                raw_keyword,
                neutral_replacement,
            )

        return sanitized_text, sanitized_entities
