from decimal import Decimal
from typing import Any, Dict, List

import networkx as nx

from assessment_engine.ports.graph_analyzer import GraphAnalyzer

_INVERTED_PREDICATES = {"REQUIRES_PREREQUISITE", "DEPENDS_ON", "REQUIRES"}
_DIRECT_PREDICATES = {"ENABLES", "BLOCKS"}
_WAVE_LABELS = {0: "Wave 0: Foundation", 1: "Wave 1: Transformation"}


def _is_roadmap_candidate(node_id: Any) -> bool:
    """Determine if a graph node identifier qualifies as a roadmap item candidate."""
    if not isinstance(node_id, str) or len(node_id) > 100:
        return False
    return not ("." in node_id and len(node_id) < 10)


def _get_wave_label(wave_index: int) -> str:
    """Return the descriptive label for a given execution wave index."""
    return _WAVE_LABELS.get(wave_index, f"Wave {wave_index}: Advanced State")


def _compute_node_depth(
    graph: nx.DiGraph, node: str, waves: Dict[str, int]
) -> int:
    """Calculate the topological wave depth of a single node."""
    in_edges = list(graph.in_edges(node))
    if not in_edges:
        return 0
    return max(waves.get(u, 0) for u, _ in in_edges) + 1


def _compute_all_node_waves(graph: nx.DiGraph) -> Dict[str, int]:
    """Compute wave depth mapping for all nodes in a DAG."""
    waves: Dict[str, int] = {}
    for node in nx.topological_sort(graph):
        waves[node] = _compute_node_depth(graph, node, waves)
    return waves


def _get_candidate_nodes_for_wave(
    waves: Dict[str, int], target_wave: int
) -> List[str]:
    """Filter roadmap candidate nodes belonging to a specific wave."""
    return [
        node
        for node, w in waves.items()
        if w == target_wave and _is_roadmap_candidate(node)
    ]


def _format_waves_roadmap(waves: Dict[str, int]) -> List[Dict[str, Any]]:
    """Group nodes by wave depth and format as roadmap entries."""
    if not waves:
        return []
    roadmap = []
    for i in range(max(waves.values()) + 1):
        nodes = _get_candidate_nodes_for_wave(waves, i)
        if nodes:
            roadmap.append({"wave": _get_wave_label(i), "projects": nodes})
    return roadmap


def _add_triple_to_graph(graph: nx.DiGraph, triple: Dict[str, Any]) -> None:
    """Normalize and insert a single semantic triple into the directed graph."""
    subj = triple.get("subject", "").upper()
    pred = triple.get("predicate", "").upper()
    obj = triple.get("object_val", "").upper()

    if not subj or not obj:
        return

    graph.add_node(subj)
    graph.add_node(obj)

    if pred in _INVERTED_PREDICATES:
        graph.add_edge(obj, subj, relation=pred)
    elif pred in _DIRECT_PREDICATES:
        graph.add_edge(subj, obj, relation=pred)


def _extract_capex_score(wp: Any) -> Decimal:
    """Extract CAPEX numeric value safely as a Decimal for deterministic comparison."""
    raw = getattr(wp, "capex_numeric", 0) or 0
    return Decimal(str(raw))


def _select_core_work_package(work_packages: List[Any]) -> Any:
    """Select the core platform work package (highest CAPEX) from a list."""
    return max(work_packages, key=_extract_capex_score)


def _can_safely_add_precedence(
    graph: nx.DiGraph, core_id: str, target_id: str
) -> bool:
    """Check if adding an edge from core_id to target_id preserves DAG property."""
    if core_id == target_id or graph.has_edge(core_id, target_id):
        return False
    if core_id not in graph or target_id not in graph:
        return True
    return not nx.has_path(graph, target_id, core_id)


def _enforce_single_program_precedence(
    graph: nx.DiGraph, program: Any
) -> None:
    """Add precedence edges from the core package to contributing packages."""
    wps = getattr(program, "work_packages", None) or []
    if len(wps) < 2:
        return
    core_id = getattr(_select_core_work_package(wps), "id", "")
    if not core_id:
        return

    for wp in wps:
        wp_id = getattr(wp, "id", "")
        if wp_id and _can_safely_add_precedence(graph, core_id, wp_id):
            graph.add_edge(core_id, wp_id, relation="PROGRAM_CORE_PRECEDENCE")


class NetworkXAnalyzer(GraphAnalyzer):
    """Provides an adapter for the NetworkX library for graph analysis."""

    def __init__(self) -> None:
        """Initialize the analyzer with an empty NetworkX DiGraph."""
        self.graph = nx.DiGraph()

    def build_graph_from_triples(self, triples: List[Dict[str, Any]]) -> None:
        """Reconstruct the internal directed graph from semantic triples."""
        self.graph.clear()
        for triple in triples:
            _add_triple_to_graph(self.graph, triple)

    def enforce_program_temporal_precedence(
        self, programs: List[Any]
    ) -> None:
        """Enforce temporal precedence of core packages within corporate programs."""
        for prog in programs:
            _enforce_single_program_precedence(self.graph, prog)

    def detect_cycles(self) -> List[List[str]]:
        """Detect all simple cycles in the directed graph."""
        try:
            return list(nx.simple_cycles(self.graph))
        except Exception:
            return []

    def calculate_topological_waves(self) -> List[Dict[str, Any]]:
        """Compute execution waves for nodes in a directed acyclic graph (DAG)."""
        try:
            waves = _compute_all_node_waves(self.graph)
            return _format_waves_roadmap(waves)
        except nx.NetworkXUnfeasible:
            return []

    def get_critical_path(self, start_node: str, end_node: str) -> List[str]:
        """Calculate the shortest path between two nodes in a DAG."""
        if not nx.is_directed_acyclic_graph(self.graph):
            return []
        try:
            return list(nx.shortest_path(self.graph, start_node, end_node))
        except Exception:
            return []