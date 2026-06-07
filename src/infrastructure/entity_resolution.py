import difflib
import uuid
from typing import Optional


class EntityResolutionEngine:
    """
    Tier-1 Entity Resolution Engine using Semantic Normalization & Fuzzy Matching.
    Prevents 'Semantic Drift' by merging semantically identical entities.
    """

    def __init__(self, similarity_threshold: float = 0.65):
        self.similarity_threshold = similarity_threshold
        # registry: {normalized_key: (original_name, node_id)}
        self.registry: dict[str, tuple[str, str]] = {}

    def _normalize(self, text: str) -> str:
        """Deep normalization for robust matching, removing stop words."""
        stop_words = {
            "de",
            "la",
            "el",
            "en",
            "y",
            "a",
            "los",
            "para",
            "con",
            "un",
            "una",
        }
        normalized = text.lower().strip()
        normalized = "".join(ch for ch in normalized if ch.isalnum() or ch.isspace())
        # Sort words to handle permutations and filter stop words
        words = sorted([w for w in normalized.split() if w not in stop_words])
        return " ".join(words)

    def get_semantic_id(self, text: str, context: Optional[str] = None) -> str:
        """
        Calculates a stable, semantic node_id.
        Now includes a lookup in the registry to handle fuzzy matches.
        """
        if not text:
            return str(uuid.uuid4())

        # 1. Structural Nodes (Direct ID)
        if text.startswith(("T", "P", "K")) and "." in text:
            clean_id = text.split()[0].upper()
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, clean_id))

        # 2. Semantic Normalization
        norm_key = self._normalize(text)
        if context:
            norm_key += f"|{context.upper().strip()}"

        # 3. Exact Match in Registry
        if norm_key in self.registry:
            return self.registry[norm_key][1]

        # 4. Fuzzy Match in Registry (Semantic Merging)
        if self.registry:
            # We compare against original names for better fuzzy accuracy
            # though comparing against keys is faster.
            keys = list(self.registry.keys())
            matches = difflib.get_close_matches(
                norm_key, keys, n=1, cutoff=self.similarity_threshold
            )
            if matches:
                existing_key = matches[0]
                matched_id = self.registry[existing_key][1]
                # Register the synonym to avoid future fuzzy searches for this exact string
                self.registry[norm_key] = (text, matched_id)
                return matched_id

        # 5. New Entity
        new_id = str(uuid.uuid5(uuid.NAMESPACE_OID, norm_key))
        self.registry[norm_key] = (text, new_id)
        return new_id

    def resolve_entity(self, text: str, existing_nodes: list[dict]) -> str:
        """
        Resolves a text entity against existing graph nodes.
        """
        # Placeholder for future expansion
        return self.get_semantic_id(text)
