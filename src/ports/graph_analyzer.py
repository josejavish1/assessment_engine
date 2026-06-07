from abc import ABC, abstractmethod
from typing import Any, Dict, List


class GraphAnalyzer(ABC):
    """
    Tier-1 Port for Graph Analysis.
    Decouples strategic algorithms (Topological Sort, DAG resolution) from specific implementations.
    """

    @abstractmethod
    def build_graph_from_triples(self, triples: List[Dict[str, Any]]) -> None:
        """Populates the internal graph structure from a list of epistemic triples."""
        pass

    @abstractmethod
    def detect_cycles(self) -> List[List[str]]:
        """Returns a list of detected cycles in the graph to prevent strategic circularities."""
        pass

    @abstractmethod
    def calculate_topological_waves(self) -> List[Dict[str, Any]]:
        """
        Calculates the strategic roadmap waves (Wave 0, 1, 2) based on dependencies.
        Returns a stratified list of projects.
        """
        pass

    @abstractmethod
    def get_critical_path(self, start_node: str, end_node: str) -> List[str]:
        """Calculates the critical path between two strategic milestones."""
        pass
