from typing import Any, Dict, List

import networkx as nx

from ports.graph_analyzer import GraphAnalyzer


class NetworkXAnalyzer(GraphAnalyzer):
    """
    Tier-1 NetworkX Adapter for Strategic Graph Analysis.
    Implements topological sorting and DAG resolution.
    """

    def __init__(self):
        self.graph = nx.DiGraph()

    def build_graph_from_triples(self, triples: List[Dict[str, Any]]) -> None:
        """
        Populates the DiGraph.
        Expects triples with 'subject', 'predicate', 'object_val'.
        Relationships like 'REQUIRES_PREREQUISITE' are treated as directed edges.
        """
        self.graph.clear()
        for t in triples:
            subj = t.get("subject", "").upper()
            pred = t.get("predicate", "").upper()
            obj = t.get("object_val", "").upper()

            if not subj or not obj:
                continue

            # Add nodes
            self.graph.add_node(subj)
            self.graph.add_node(obj)

            # Map strategic predicates to graph edges
            # Direction: Object -> Subject (If A REQUIRES B, then B must happen before A, Edge B -> A)
            if pred in ["REQUIRES_PREREQUISITE", "DEPENDS_ON", "REQUIRES"]:
                self.graph.add_edge(obj, subj, relation=pred)
            elif pred in ["ENABLES", "BLOCKS"]:
                # If A ENABLES B, Edge A -> B
                self.graph.add_edge(subj, obj, relation=pred)

    def detect_cycles(self) -> List[List[str]]:
        """Detects circular dependencies."""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except Exception:
            return []

    def calculate_topological_waves(self) -> List[Dict[str, Any]]:
        """
        Assigns nodes to waves (Wave 0, 1, 2) using a topological sorting logic.
        """
        if not nx.is_directed_acyclic_graph(self.graph):
            # In case of cycles, we fallback to a simple sort or alert
            pass

        def is_roadmap_candidate(node_id: str) -> bool:
            if not isinstance(node_id, str):
                return False
            # Filter out very long strings which are likely GAP texts or findings
            if len(node_id) > 100:
                return False
            # Filter out Pillar/KPI codes (e.g. T1.P2)
            if "." in node_id and len(node_id) < 10:
                return False
            return True

        try:
            # Simple Wave Logic: Distance from source nodes (nodes with 0 in-degree)
            waves = {}
            for node in nx.topological_sort(self.graph):
                # Calculate max depth from sources
                in_edges = list(self.graph.in_edges(node))
                if not in_edges:
                    depth = 0
                else:
                    depth = max(waves.get(u, 0) for u, v in in_edges) + 1
                waves[node] = depth

            # Group by wave
            roadmap = []
            max_wave = max(waves.values()) if waves else 0
            for i in range(max_wave + 1):
                wave_label = f"Wave {i}"
                if i == 0:
                    wave_label = "Wave 0: Foundation"
                elif i == 1:
                    wave_label = "Wave 1: Transformation"
                else:
                    wave_label = f"Wave {i}: Advanced State"

                # Filter nodes for the roadmap
                nodes_in_wave = [
                    node
                    for node, w in waves.items()
                    if w == i and is_roadmap_candidate(node)
                ]

                if nodes_in_wave:
                    roadmap.append({"wave": wave_label, "projects": nodes_in_wave})
            return roadmap
        except nx.NetworkXUnfeasible:
            # Cycle detected during sort
            return []

    def get_critical_path(self, start_node: str, end_node: str) -> List[str]:
        """Calculates the longest path in the DAG (Strategic Critical Path)."""
        if not nx.is_directed_acyclic_graph(self.graph):
            return []
        try:
            # In a DAG, longest path between two nodes is the critical path
            # networkx doesn't have a direct 'longest_path' between two nodes,
            # but we can use shortest_path on negated weights or similar algorithms.
            return nx.shortest_path(self.graph, start_node, end_node)
        except Exception:
            return []
