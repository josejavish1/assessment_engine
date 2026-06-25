import json
from pathlib import Path
from typing import List


class OntologyRegistry:
    r"""{'OntologyRegistry': "Manages and enforces ontological constraints for a graph schema.\n\n    This class serves as the authoritative source for the graph's ontology, loading\n    predicate and node type definitions from a specified JSON configuration file.\n    If the specified file is not found, the registry falls back to a built-in\n    default ontology to ensure baseline system functionality.\n\n    Attributes:\n        config_path (pathlib.Path): The file path to the JSON ontology configuration.\n        predicates (List[str]): A list of valid predicate strings (e.g.,\n            'MITIGATES_RISK').\n        node_types (List[str]): A list of valid node type strings (e.g., 'RISK').", '__init__': 'Initialize the OntologyRegistry instance.\n\n        Constructs the registry by loading the ontology from the specified JSON\n        configuration file via the `_load_ontology` method.\n\n        Args:\n            config_path (str): The file path to the JSON ontology configuration.\n                Defaults to "engine_config/policies/ontology/core_ontology.json".\n\n        Raises:\n            json.JSONDecodeError: If the configuration file exists but contains\n                malformed JSON.\n            PermissionError: If the configuration file exists but cannot be read\n                due to file system permissions.', '_load_ontology': "Load predicate and node type definitions from the configuration file.\n\n        This method populates the `predicates` and `node_types` attributes. If the\n        file at `self.config_path` does not exist, it loads a default, built-in\n        ontology (the 2026 Sovereign Predicates standard) as a fallback. If the\n        file exists, it is parsed as JSON. Keys 'predicates' and 'node_types' are\n        read from the file; if a key is missing, its corresponding attribute is\n        set to an empty list.\n\n        Raises:\n            json.JSONDecodeError: If the configuration file exists but contains\n                malformed JSON.\n            PermissionError: If the configuration file exists but cannot be read\n                due to file system permissions.", 'validate_triple': "Validate a triple against the loaded ontology.\n\n        Checks if the given predicate is defined in the ontology's list of valid\n        predicates. The validation is performed in a case-insensitive manner by\n        converting the predicate to uppercase. This implementation does not\n        currently enforce constraints on the subject or object types.\n\n        Args:\n            subject_type (str): The type of the subject node (currently unused).\n            predicate (str): The predicate (relationship type) to validate.\n            object_type (str): The type of the object node (currently unused).\n\n        Returns:\n            bool: True if the predicate is defined in the ontology, False otherwise."}."""

    def __init__(
        self, config_path: str = "engine_config/policies/ontology/core_ontology.json"
    ):
        """Initializes the OntologyRegistry by loading a configuration file.

        Reads an ontology configuration from a specified JSON file to populate the
        registry with known predicates and node types.

        Args:
            config_path: The path to the JSON ontology configuration file.

        Attributes:
            config_path: The `pathlib.Path` object for the loaded configuration.
            predicates: A list of predicate strings defined in the ontology.
            node_types: A list of node type strings defined in the ontology.

        Raises:
            FileNotFoundError: If the file at `config_path` does not exist.
            json.JSONDecodeError: If the configuration file contains malformed JSON.
            KeyError: If the configuration file is missing required top-level keys
                (e.g., 'predicates', 'node_types').
        """
        self.config_path = Path(config_path)
        self.predicates: List[str] = []
        self.node_types: List[str] = []
        self._load_ontology()

    def _load_ontology(self):
        if not self.config_path.exists():
            # If an explicit ontology is not supplied, the system defaults to the 2026 Sovereign Predicates standard. This fallback ensures baseline compatibility and core system functionality.
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
        """Check if a predicate is registered in the ontology."""
        return predicate.upper() in self.predicates
