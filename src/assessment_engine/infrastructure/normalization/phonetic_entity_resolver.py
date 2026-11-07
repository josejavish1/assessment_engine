"""Phonetic Entity Resolver Infrastructure Adapter (RFC 082).

Normalizes Speech-to-Text phonetic corruptions into canonical enterprise architecture
entities dynamically via externalized ontology configuration with O(N) single-pass matching.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Tuple

import yaml

from assessment_engine.domain.contracts.ingestion_ports import IPhoneticResolverPort
from assessment_engine.domain.schemas.epistemic_ledger import (
    NormalizedUtterance,
    RawUtterance,
    ResolvedEntity,
)
from assessment_engine.infrastructure.runtime_paths import ROOT

logger = logging.getLogger(__name__)


def _normalize_key(text: str) -> str:
    """Normalizes Unicode strings via NFKC casefolding without destroying non-Latin scripts."""
    return unicodedata.normalize("NFKC", text).casefold().strip()


def _strip_diacritics(text: str) -> str:
    """Strips combining diacritical marks while preserving base Unicode characters."""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFKC", stripped).casefold().strip()


class PhoneticEntityResolver(IPhoneticResolverPort):
    """Acoustic-semantic resolver normalizing STT artifacts using dynamic ontologies."""

    def __init__(self, ontology_path: Optional[Path] = None) -> None:
        self.ontology_path = ontology_path or (
            ROOT / "engine_config" / "ontologies" / "global_tech_ontology.yaml"
        )
        self._canonical_entities: List[Dict[str, Any]] = []
        self._alias_map: Dict[str, Tuple[str, str]] = {}
        self._compiled_pattern: Optional[Pattern[str]] = None
        self._load_ontology()

    def _register_alias(
        self, alias: str, canonical_name: str, category: str
    ) -> None:
        cleaned = alias.strip()
        if not cleaned:
            return
        self._alias_map[_normalize_key(cleaned)] = (canonical_name, category)
        stripped = _strip_diacritics(cleaned)
        if stripped:
            self._alias_map.setdefault(stripped, (canonical_name, category))

    def _load_ontology(self) -> None:
        if not self.ontology_path.exists():
            logger.warning("Ontology file not found at %s", self.ontology_path)
            return

        with open(self.ontology_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        self._canonical_entities = data.get("canonical_entities", [])
        for item in self._canonical_entities:
            c_name = item.get("canonical_name", "").strip()
            cat = item.get("category", "")
            if not c_name:
                continue

            self._register_alias(c_name, c_name, cat)
            for acr in item.get("acronyms", []):
                self._register_alias(acr, c_name, cat)
            for alias in item.get("phonetic_aliases", []):
                self._register_alias(alias, c_name, cat)

        self._compiled_pattern = self._build_alternation_regex(self._alias_map)

    @staticmethod
    def _build_alternation_regex(
        alias_map: Dict[str, Tuple[str, str]]
    ) -> Optional[Pattern[str]]:
        if not alias_map:
            return None
        sorted_aliases = sorted(alias_map.keys(), key=len, reverse=True)
        escaped = [re.escape(a) for a in sorted_aliases if a]
        if not escaped:
            return None
        # Unicode-safe token boundary lookarounds
        pattern_str = rf"(?<!\w)(?:{'|'.join(escaped)})(?!\w)"
        return re.compile(pattern_str, re.IGNORECASE | re.UNICODE)

    def _prepare_matcher(
        self, runtime_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Tuple[str, str]], Optional[Pattern[str]]]:
        if not runtime_context or "known_systems" not in runtime_context:
            return self._alias_map, self._compiled_pattern

        effective_map = dict(self._alias_map)
        for sys_name in runtime_context["known_systems"]:
            cleaned = str(sys_name).strip()
            if cleaned:
                effective_map[_normalize_key(cleaned)] = (cleaned, "tenant_custom")
                stripped = _strip_diacritics(cleaned)
                if stripped:
                    effective_map.setdefault(stripped, (cleaned, "tenant_custom"))

        return effective_map, self._build_alternation_regex(effective_map)

    def _normalize_single_with_compiled(
        self,
        utterance: RawUtterance,
        effective_map: Dict[str, Tuple[str, str]],
        pattern: Optional[Pattern[str]],
    ) -> NormalizedUtterance:
        original_text = utterance.raw_text
        if pattern is None:
            return NormalizedUtterance(
                utterance_id=utterance.utterance_id,
                sequence_index=utterance.sequence_index,
                source_file=utterance.source_file,
                timestamp_start=utterance.timestamp_start,
                timestamp_end=utterance.timestamp_end,
                speaker_identifier=utterance.speaker_identifier,
                speaker_role=utterance.speaker_role,
                raw_text=original_text,
                normalized_text=original_text,
                resolved_entities=[],
                normalization_confidence=1.0,
            )

        reconstructed_parts: List[str] = []
        resolved: List[ResolvedEntity] = []
        last_idx = 0

        for match in pattern.finditer(original_text):
            start, end = match.span()
            matched_text = match.group(0)
            lookup_key = _normalize_key(matched_text)
            if lookup_key not in effective_map:
                lookup_key = _strip_diacritics(matched_text)

            target_entry = effective_map.get(lookup_key)
            if not target_entry:
                continue

            canonical_name, _ = target_entry
            if matched_text.strip() != canonical_name.strip():
                reconstructed_parts.append(original_text[last_idx:start])
                reconstructed_parts.append(canonical_name)
                last_idx = end
                resolved.append(
                    ResolvedEntity(
                        original_token=matched_text,
                        canonical_entity=canonical_name,
                        resolution_method="EXACT_ONTOLOGY_MATCH",
                        phonetic_distance=0.0,
                        confidence=1.0,
                    )
                )

        reconstructed_parts.append(original_text[last_idx:])
        normalized_text = "".join(reconstructed_parts)
        conf = 1.0 if not resolved else min(r.confidence for r in resolved)

        return NormalizedUtterance(
            utterance_id=utterance.utterance_id,
            sequence_index=utterance.sequence_index,
            source_file=utterance.source_file,
            timestamp_start=utterance.timestamp_start,
            timestamp_end=utterance.timestamp_end,
            speaker_identifier=utterance.speaker_identifier,
            speaker_role=utterance.speaker_role,
            raw_text=original_text,
            normalized_text=normalized_text,
            resolved_entities=resolved,
            normalization_confidence=conf,
        )

    def normalize_utterance(
        self,
        utterance: RawUtterance,
        runtime_context: Optional[Dict[str, Any]] = None,
    ) -> NormalizedUtterance:
        """Normalizes STT errors in a single raw utterance."""
        effective_map, pattern = self._prepare_matcher(runtime_context)
        return self._normalize_single_with_compiled(utterance, effective_map, pattern)

    def normalize_batch(
        self,
        utterances: List[RawUtterance],
        runtime_context: Optional[Dict[str, Any]] = None,
    ) -> List[NormalizedUtterance]:
        """Normalizes a stream of utterances compiling the matcher once per batch."""
        effective_map, pattern = self._prepare_matcher(runtime_context)
        return [
            self._normalize_single_with_compiled(u, effective_map, pattern)
            for u in utterances
        ]
