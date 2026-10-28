from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph


class BaseSovereignPolicy(ABC):
    """Abstract base class for sovereign data policies.

    Defines the contract for policies that evaluate an EpistemicGraph and patch
    a payload dictionary accordingly.
    """

    @abstractmethod
    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a knowledge graph against a policy and patch a data payload."""
        pass
