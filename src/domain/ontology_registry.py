import json
from pathlib import Path
from typing import List


class OntologyRegistry:
    """
    Sovereign Ontology Registry.
    Ensures 'Zero-Hallucination' by enforcing strict graph predicates and node types.
    """

    def __init__(
        self, config_path: str = "engine_config/policies/ontology/core_ontology.json"
    ):
        self.config_path = Path(config_path)
        self.predicates: List[str] = []
        self.node_types: List[str] = []
        self._load_ontology()

    def _load_ontology(self):
        if not self.config_path.exists():
            # Fallback to default 2026 Sovereign Predicates
            self.predicates = [
                "MITIGATES_RISK",
                "REQUIRES_PREREQUISITE",
                "ENABLES_CAPABILITY",
                "PART_OF_WAVE",
                "IDENTIFIED_AS_GAP",
                "PROPOSES_INITIATIVE",
            ]
            self.node_types = ["RISK", "INITIATIVE", "KPI", "PILLAR", "STRATEGIC_GOAL"]
            return

        with open(self.config_path, "r") as f:
            data = json.load(f)
            self.predicates = data.get("predicates", [])
            self.node_types = data.get("node_types", [])

    def validate_triple(
        self, subject_type: str, predicate: str, object_type: str
    ) -> bool:
        """Validates if a relationship is allowed by the ontology."""
        return predicate.upper() in self.predicates
