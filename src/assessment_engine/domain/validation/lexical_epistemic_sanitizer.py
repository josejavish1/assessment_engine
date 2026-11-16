"""
Tier-1 Dynamic Lexical Epistemic Sanitizer & Verified Entity Registry.

Implements the formal AST and Lexical compiler pass specified by the Tier-1 Red Team:
1. Replaces static keyword blacklists with an open-world and taxonomy-backed symbol table (VerifiedEntityRegistry).
2. Deterministically extracts proper nouns, CamelCase vendors, and acronyms from evidence corpora during ingestion.
3. Automatically replaces unaccredited product hallucinations with canonical functional capability archetypes
   loaded dynamically from engine_config/taxonomy/capability_archetypes.json.
4. Preserves grammatical article agreement ('a/an') and guarantees 100% Technical English codebase decoupling.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field, ConfigDict
import logging

logger = logging.getLogger(__name__)

# Locate canonical repository root
_MODULE_PATH = Path(__file__).resolve()
_REPO_ROOT = _MODULE_PATH.parents[4]  # src/assessment_engine/domain/validation -> repo root


def load_canonical_archetypes() -> Dict[str, Dict[str, str]]:
    """Loads localized capability archetypes dynamically from the configuration tier."""
    archetypes_file = _REPO_ROOT / "engine_config" / "taxonomy" / "capability_archetypes.json"
    if archetypes_file.exists():
        try:
            with open(archetypes_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as ex:
            logger.debug("Could not load capability archetypes from %s: %s", archetypes_file, ex)
    return {"en": {}, "es": {}}


class VerifiedEntityRegistry(BaseModel):
    """Open-world and taxonomy-backed symbol table mapping verified entities to exact evidence sources."""
    model_config = ConfigDict(extra="forbid")

    entity_to_evidence_map: Dict[str, Set[str]] = Field(default_factory=dict)
    localized_archetypes: Dict[str, Dict[str, str]] = Field(default_factory=load_canonical_archetypes)

    @property
    def taxonomy_archetypes_en(self) -> Dict[str, str]:
        return self.localized_archetypes.get("en", {})

    @property
    def taxonomy_archetypes_es(self) -> Dict[str, str]:
        return self.localized_archetypes.get("es", {})

    def register_verified_mention(self, entity_token: str, evidence_id: str) -> None:
        """Registers a verified entity mention associated with a specific evidence chunk ID."""
        normalized = entity_token.strip().lower()
        if normalized not in self.entity_to_evidence_map:
            self.entity_to_evidence_map[normalized] = set()
        self.entity_to_evidence_map[normalized].add(evidence_id)

    def ingest_evidence_text(self, text: str, evidence_id: str) -> None:
        """Deterministically extracts known taxonomy entities AND open-world CamelCase/Acronym tokens.

        Scans the raw evidence text chunk to populate the registry at ingestion time.
        """
        lower_text = text.lower()
        for known_entity in self.taxonomy_archetypes_en:
            if re.search(rf"(?<!\w){re.escape(known_entity)}(?!\w)", lower_text):
                self.register_verified_mention(known_entity, evidence_id)

        # Open-world extraction for CamelCase (e.g., CyberArk, ServiceNow, FortiGate) and Acronyms (3-10 chars)
        open_world_matches = re.findall(r"\b(?:[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+|[A-Z]{3,10})\b", text)
        for match in open_world_matches:
            self.register_verified_mention(match, evidence_id)

    def is_entity_authorized(self, entity_token: str, active_evidence_ids: List[str]) -> bool:
        """Verifies whether an entity token was cited in the active scoped evidence chunks."""
        normalized = entity_token.strip().lower()
        if normalized not in self.entity_to_evidence_map:
            return False
        authorized_sources = self.entity_to_evidence_map[normalized]
        if not active_evidence_ids:
            return len(authorized_sources) > 0
        return bool(authorized_sources.intersection(set(active_evidence_ids)))


class LexicalEpistemicSanitizer:
    """Two-stage AST/Lexical compiler pass that strips unverified vendor hallucinations.

    Preserves grammatical determiner agreement ('a/an') and replaces unauthorized product
    names with canonical capability archetypes derived from the official taxonomy.
    """

    def __init__(self, registry: Optional[VerifiedEntityRegistry] = None):
        self.registry = registry or VerifiedEntityRegistry()

    @staticmethod
    def _harmonize_article(preceding_article: Optional[str], replacement: str) -> str:
        """Ensures 'a/an' grammatical agreement when substituting an English archetype."""
        if not preceding_article:
            return replacement
        clean_art = preceding_article.strip()
        if clean_art.lower() in ("a", "an"):
            starts_with_vowel = replacement.strip()[0].lower() in ("a", "e", "i", "o", "u")
            correct_art = "an" if starts_with_vowel else "a"
            if clean_art[0].isupper():
                correct_art = correct_art.capitalize()
            return f"{correct_art} {replacement}"
        return f"{clean_art} {replacement}"

    def compile_and_sanitize(
        self,
        raw_narrative: str,
        scoped_evidence_ids: Optional[List[str]] = None,
        doc_lang: str = "en",
    ) -> Tuple[str, List[str]]:
        """Compiles and sanitizes raw LLM output against the verified entity registry.

        Returns:
            Tuple of (sanitized_narrative, list_of_intercepted_hallucinations).
        """
        if not raw_narrative:
            return "", []

        active_evidence_ids = scoped_evidence_ids or []
        is_es = doc_lang.strip().lower().startswith("es")
        archetype_map = self.registry.taxonomy_archetypes_es if is_es else self.registry.taxonomy_archetypes_en

        if not archetype_map:
            archetype_map = self.registry.taxonomy_archetypes_en

        sanitized_text = raw_narrative
        intercepted_hallucinations: List[str] = []

        # Sort keys descending by length so compound names ("microsoft entra id") match before ("entra id")
        sorted_entities = sorted(archetype_map.keys(), key=len, reverse=True)

        for entity in sorted_entities:
            pattern = re.compile(
                rf"(?:\b(a|an)\s+)?(?<!\w)({re.escape(entity)})(?!\w)",
                re.IGNORECASE,
            )

            def _replacer(match: re.Match) -> str:
                article = match.group(1)
                matched_token = match.group(2)
                if self.registry.is_entity_authorized(matched_token, active_evidence_ids):
                    return match.group(0)
                if entity not in intercepted_hallucinations:
                    intercepted_hallucinations.append(entity)
                archetype = archetype_map[entity]
                if is_es:
                    return archetype
                return self._harmonize_article(article, archetype)

            sanitized_text = pattern.sub(_replacer, sanitized_text)

        return sanitized_text, intercepted_hallucinations
