"""Deterministic Semantic Gatekeeper Domain Service.

Enforces strict ontological boundaries across enterprise architecture pillars,
detecting and quarantining cross-pillar attention bleed using set-theoretic
token matching, phrase boundary regexes, and signal-to-noise dominance ratios.
Strictly 100% Technical English, zero hardcoding, multi-tenant and vertical-agnostic.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from assessment_engine.domain.ontology.models import (
    GatekeeperThresholds,
    OntologicalValidationResult,
    TaxonomyRegistryPort,
    ValidationVerdict,
)

logger = logging.getLogger(__name__)

_WORD_TOKEN_PATTERN = re.compile(r"[a-z0-9_\-]+")


def normalize_text(text: str) -> str:
    """Normalizes text to lowercase NFKD ASCII-compatible representation for deterministic matching."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return stripped.lower()


def extract_word_tokens(normalized_text: str) -> Set[str]:
    """Extracts a hash set of discrete word tokens from normalized text in O(N) time."""
    if not normalized_text:
        return set()
    return set(_WORD_TOKEN_PATTERN.findall(normalized_text))


def match_lexicon_terms(
    normalized_text: str,
    text_tokens: Set[str],
    lexicon: Iterable[str],
) -> List[str]:
    """Matches single-word tokens in O(1) average time and multi-word phrases via word boundaries."""
    hits: List[str] = []
    for raw_term in lexicon:
        norm_term = normalize_text(raw_term.strip())
        if not norm_term:
            continue
        if " " not in norm_term:
            if norm_term in text_tokens:
                hits.append(raw_term)
        else:
            escaped = re.escape(norm_term)
            pattern = rf"(?:\b|_){escaped}(?:\b|_)"
            if re.search(pattern, normalized_text):
                hits.append(raw_term)
    return sorted(set(hits))


class OntologicalGatekeeper:
    """Deterministic semantic firewall that prevents cross-pillar contamination

    by validating narrative texts against the dynamic TaxonomyRegistryPort.
    """

    def __init__(
        self,
        taxonomy_registry: TaxonomyRegistryPort,
        thresholds: Optional[GatekeeperThresholds] = None,
    ) -> None:
        self._registry = taxonomy_registry
        self._thresholds = thresholds or GatekeeperThresholds()

    def validate_text_for_pillar(
        self,
        text: str,
        target_pillar_id: str,
        tower_id: Optional[str] = None,
    ) -> OntologicalValidationResult:
        """Evaluates whether candidate text belongs to target_pillar_id or constitutes foreign contamination."""
        norm_pillar = str(target_pillar_id or "").strip().upper()
        norm_tower = str(tower_id or "").strip().upper() or None

        if not text or not text.strip():
            return OntologicalValidationResult(
                verdict=ValidationVerdict.INSUFFICIENT_SIGNAL,
                target_pillar_id=norm_pillar,
                confidence_score=0.0,
                reason="Candidate narrative text is empty or whitespace.",
            )

        profile = self._registry.get_profile(norm_pillar, tower_id=norm_tower)
        if not profile:
            return OntologicalValidationResult(
                verdict=ValidationVerdict.VALID_IN_DOMAIN,
                target_pillar_id=norm_pillar,
                confidence_score=self._thresholds.fallback_neutral_confidence,
                reason="No explicit ontological profile indexed for pillar; permissive pass.",
            )

        canonical_pillar_id = profile.pillar_id
        norm_text = normalize_text(text)
        text_tokens = extract_word_tokens(norm_text)

        # 1. Detect exclusive foreign domain signatures (Cross-Pillar Contamination)
        foreign_hits_by_domain: Dict[str, List[str]] = {}
        for foreign_domain_id, exclusive_terms in profile.negative_exclusion_map.items():
            hits = match_lexicon_terms(norm_text, text_tokens, exclusive_terms)
            if hits:
                foreign_hits_by_domain[foreign_domain_id] = hits

        # 2. Detect positive affinity matches within target pillar
        positive_hits = match_lexicon_terms(norm_text, text_tokens, profile.positive_lexicon)

        # 3. Evaluate Signal-to-Noise Dominance Rule for Quarantine
        if foreign_hits_by_domain:
            dominant_foreign_domain = max(
                sorted(foreign_hits_by_domain.keys()),
                key=lambda k: len(foreign_hits_by_domain[k]),
            )
            all_negative_hits = sorted(
                {hit for hits in foreign_hits_by_domain.values() for hit in hits}
            )
            neg_count = len(all_negative_hits)
            pos_count = len(positive_hits)

            foreign_ratio = neg_count / (neg_count + pos_count + self._thresholds.smoothing_epsilon)
            should_quarantine = (
                neg_count >= self._thresholds.hard_quarantine_foreign_hit_count
                or foreign_ratio >= self._thresholds.foreign_dominance_ratio_threshold
                or pos_count == 0
            )

            if should_quarantine:
                logger.warning(
                    "[Semantic Gatekeeper] Quarantining foreign contamination in pillar '%s': "
                    "Detected foreign domain '%s' with signature tokens %s (positive_hits=%d).",
                    canonical_pillar_id,
                    dominant_foreign_domain,
                    all_negative_hits[:5],
                    pos_count,
                )
                return OntologicalValidationResult(
                    verdict=ValidationVerdict.QUARANTINED_FOREIGN_DOMAIN,
                    target_pillar_id=canonical_pillar_id,
                    detected_foreign_domain_id=dominant_foreign_domain,
                    positive_affinity_hits=positive_hits,
                    negative_exclusion_hits=all_negative_hits,
                    confidence_score=round(foreign_ratio, 4),
                    reason=(
                        f"Text contains exclusive signature terms of foreign domain '{dominant_foreign_domain}' "
                        f"({', '.join(all_negative_hits[:3])}) prohibited in pillar '{canonical_pillar_id}'."
                    ),
                )

        confidence = (
            self._thresholds.default_valid_confidence
            if positive_hits
            else self._thresholds.fallback_neutral_confidence
        )
        return OntologicalValidationResult(
            verdict=ValidationVerdict.VALID_IN_DOMAIN,
            target_pillar_id=canonical_pillar_id,
            positive_affinity_hits=positive_hits,
            negative_exclusion_hits=[],
            confidence_score=confidence,
            reason="No dominant foreign domain exclusion signatures detected.",
        )

    def sanitize_pillar_findings(
        self,
        pillar_id: str,
        findings: List[Dict[str, Any]],
        tower_id: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], List[OntologicalValidationResult]]:
        """Filters a list of candidate findings, returning only ontologically valid findings

        and a quarantine audit ledger.
        """
        sanitized: List[Dict[str, Any]] = []
        quarantined: List[OntologicalValidationResult] = []

        for finding_entry in findings:
            if not isinstance(finding_entry, dict):
                continue
            text_segments = [
                str(finding_entry.get("finding") or ""),
                str(finding_entry.get("capability") or ""),
                str(finding_entry.get("risk_observed") or ""),
                str(finding_entry.get("justification") or ""),
            ]
            text_to_check = " ".join(seg for seg in text_segments if seg).strip()

            result = self.validate_text_for_pillar(
                text=text_to_check,
                target_pillar_id=pillar_id,
                tower_id=tower_id,
            )
            if result.verdict == ValidationVerdict.VALID_IN_DOMAIN:
                sanitized.append(finding_entry)
            else:
                quarantined.append(result)

        return sanitized, quarantined
