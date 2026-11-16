"""
Epistemic Graph Router & Tower Context Builder.

Routes evidence fragments to their legitimate MECE domain tower using dynamic ontology
derivation and ArgMax Primary Custody routing, completely eliminating hardcoded keyword dictionaries.
Enforces strict fail-closed boundary isolation and word-bounded token matching.
"""

from typing import Any, Dict, List, Optional, Pattern, Set
from pathlib import Path
import json
import re
import logging

logger = logging.getLogger(__name__)

# Locate canonical repository root
_MODULE_PATH = Path(__file__).resolve()
_REPO_ROOT = _MODULE_PATH.parents[4]  # src/assessment_engine/domain/ingestion -> repo root


class EpistemicContextRouter:
    """Routes evidence fragments to their legitimate MECE domain tower via dynamic ontology derivation."""

    _STOP_WORDS: Set[str] = {
        "this", "that", "with", "from", "have", "been", "were", "what", "which",
        "will", "would", "shall", "should", "about", "above", "across", "after",
        "again", "against", "along", "also", "among", "around", "because", "before",
        "behind", "below", "beneath", "beside", "between", "beyond", "both", "cannot",
        "could", "down", "during", "each", "either", "every", "first", "into", "more",
        "most", "other", "some", "such", "than", "their", "them", "then", "there",
        "these", "they", "under", "until", "upon", "while", "without", "level", "score",
        "framework", "assessment", "para", "como", "sobre", "entre", "pero", "este",
        "esta", "cada", "todo", "toda", "todos", "todas", "donde", "cuando",
    }

    _DERIVED_PATTERNS_CACHE: Dict[str, List[Pattern[str]]] = {}

    @classmethod
    def derive_domain_tokens(cls, tower_definition: Dict[str, Any]) -> Set[str]:
        """Dynamically derives ontology matching tokens from a canonical tower definition schema.

        Extracts tokens from tower_name, pillar_name, and kpi_name attributes, eliminating
        any hardcoded keyword dictionaries from domain logic.
        """
        corpus = [str(tower_definition.get("tower_name") or "")]
        for p in tower_definition.get("pillars", []):
            corpus.append(str(p.get("pillar_name") or ""))
            for k in p.get("kpis", []):
                corpus.append(str(k.get("kpi_name") or ""))

        combined = " ".join(corpus).lower()
        words = set(re.findall(r"\b[a-z]{4,}\b", combined))
        return words - cls._STOP_WORDS

    @classmethod
    def load_canonical_tower_definitions(cls, towers_dir: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
        """Loads canonical tower definitions dynamically from engine_config."""
        resolved_dir = towers_dir or (_REPO_ROOT / "engine_config" / "towers")
        definitions: Dict[str, Dict[str, Any]] = {}
        if resolved_dir.exists():
            for t_dir in sorted(resolved_dir.glob("T*")):
                def_file = t_dir / f"tower_definition_{t_dir.name}.json"
                if def_file.exists():
                    try:
                        with open(def_file, "r", encoding="utf-8") as f:
                            definitions[t_dir.name.upper()] = json.load(f)
                    except Exception as ex:
                        logger.debug("Could not load tower definition from %s: %s", def_file, ex)
        return definitions

    @classmethod
    def _get_patterns_for_tower(
        cls,
        tower_id: str,
        tower_definition: Optional[Dict[str, Any]] = None,
        custom_keywords: Optional[Set[str]] = None,
    ) -> List[Pattern[str]]:
        """Compiles word-bounded regex patterns derived dynamically from the canonical definition."""
        t_id = tower_id.strip().upper()

        if custom_keywords is not None:
            return [re.compile(rf"(?<!\w){re.escape(kw.lower())}(?!\w)") for kw in sorted(custom_keywords)]

        if t_id not in cls._DERIVED_PATTERNS_CACHE:
            t_def = tower_definition
            if not t_def:
                defs = cls.load_canonical_tower_definitions()
                t_def = defs.get(t_id)

            if not t_def:
                logger.warning("[EpistemicContextRouter] No canonical definition found for tower '%s'", t_id)
                return []

            tokens = cls.derive_domain_tokens(t_def)
            cls._DERIVED_PATTERNS_CACHE[t_id] = [
                re.compile(rf"(?<!\w){re.escape(t)}(?!\w)") for t in sorted(tokens)
            ]

        return cls._DERIVED_PATTERNS_CACHE[t_id]

    @classmethod
    def filter_context_for_tower(
        cls,
        tower_id: str,
        raw_fragments: List[str],
        max_chars: int = 25000,
        tower_definition: Optional[Dict[str, Any]] = None,
        custom_keywords: Optional[Set[str]] = None,
    ) -> str:
        """Filters evidence fragments using ArgMax Primary Custody routing.

        Assigns each fragment to the domain with the highest affinity score derived from its
        canonical schema, preventing cross-tower context contamination.
        """
        target_id = tower_id.strip().upper()
        patterns = cls._get_patterns_for_tower(target_id, tower_definition, custom_keywords)
        if not patterns:
            logger.warning(
                "[EpistemicContextRouter] Unknown or unconfigured tower_id '%s'. Failing closed with empty context.",
                tower_id,
            )
            return ""

        # Preload all tower patterns for ArgMax custody arbitration
        all_defs = cls.load_canonical_tower_definitions()
        all_patterns = {
            tid: cls._get_patterns_for_tower(tid, t_def)
            for tid, t_def in all_defs.items()
        }
        if target_id not in all_patterns:
            all_patterns[target_id] = patterns

        relevant_frags = []

        for frag in raw_fragments:
            frag_lower = frag.lower()

            # Calculate affinity across all registered canonical domains
            scores = {}
            for tid, p_list in all_patterns.items():
                match_count = sum(1 for p in p_list if p.search(frag_lower))
                if match_count >= 1:
                    scores[tid] = match_count

            # ArgMax Primary Custody: fragment belongs to the tower with the highest affinity
            # Enforce minimum affinity threshold of 2 to reject solitary generic words
            if scores:
                primary_tower = max(scores, key=scores.get)
                if primary_tower == target_id and scores[primary_tower] >= 2:
                    relevant_frags.append(frag)

        if not relevant_frags:
            logger.info(
                "[EpistemicContextRouter] Zero domain-relevant fragments matched for %s. Failing closed.",
                tower_id,
            )
            return ""

        logger.info(
            "[EpistemicContextRouter] ArgMax routing filtered %d raw fragments down to %d primary-custody fragments for %s",
            len(raw_fragments),
            len(relevant_frags),
            tower_id,
        )
        return "\n\n".join(relevant_frags)[:max_chars]
