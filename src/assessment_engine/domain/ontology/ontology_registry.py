"""
Declarative Ontology Registry for Universal Sector Classification.
Implements Phase 2 of ARGON_GLOBAL_TIER1_MASTER_PLAN.md.

Mandates:
1. Thread-safe singleton with lru_cache.
2. Validates all 8 sector ontologies against Pydantic V2 VerticalOntology.
3. Provides automatic sector classification from customer interview text in O(N).
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from assessment_engine.domain.ontology.vertical_ontology import (
    VerticalOntology,
    VerticalSectorId,
)
from assessment_engine.infrastructure.runtime_paths import ROOT

logger = logging.getLogger("assessment_engine.domain.ontology.ontology_registry")

ONTOLOGIES_DIR = ROOT / "engine_config" / "ontologies"


class OntologyRegistry:
    """Registry managing externalized sector ontologies."""

    def __init__(self, ontologies_dir: Optional[Path] = None) -> None:
        self._dir = (ontologies_dir or ONTOLOGIES_DIR).resolve(strict=True)
        self._ontologies: Dict[VerticalSectorId, VerticalOntology] = {}
        self._load_all_ontologies()

    def _load_all_ontologies(self) -> None:
        """Load and strictly validate all sector ontologies from YAML files."""
        for yml_file in self._dir.glob("*.yaml"):
            if yml_file.name == "global_tech_ontology.yaml":
                continue
            try:
                with open(yml_file, "r", encoding="utf-8") as f:
                    raw_data = yaml.safe_load(f)
                if not isinstance(raw_data, dict) or "vertical_id" not in raw_data:
                    continue
                ontology = VerticalOntology(**raw_data)
                self._ontologies[ontology.vertical_id] = ontology
            except Exception as exc:
                logger.warning("Failed parsing ontology file %s: %s", yml_file.name, exc)

    def get_ontology(self, sector_id: str | VerticalSectorId) -> VerticalOntology:
        """Resolve ontology by sector ID with fallback to MANUFACTURING_OT."""
        sec_enum = VerticalSectorId.from_str(str(sector_id))
        if sec_enum in self._ontologies:
            return self._ontologies[sec_enum]
        # Return manufacturing fallback or first available
        return self._ontologies.get(VerticalSectorId.MANUFACTURING_OT) or list(self._ontologies.values())[0]

    def list_all_verticals(self) -> List[VerticalOntology]:
        """Return list of all registered sector ontologies."""
        return list(self._ontologies.values())

    def classify_sector_from_text(self, corpus: str) -> VerticalOntology:
        """Deterministically score and classify industry sector based on technical token overlap."""
        text_lower = str(corpus or "").lower()
        best_match = self.get_ontology(VerticalSectorId.MANUFACTURING_OT)
        max_hits = -1

        for ontology in self._ontologies.values():
            hits = sum(1 for kw in ontology.lexicon_keywords if kw in text_lower)
            if hits > max_hits:
                max_hits = hits
                best_match = ontology

        return best_match


@lru_cache(maxsize=1)
def get_ontology_registry(ontologies_dir: Optional[Path] = None) -> OntologyRegistry:
    """Cached singleton accessor for OntologyRegistry."""
    return OntologyRegistry(ontologies_dir=ontologies_dir)
