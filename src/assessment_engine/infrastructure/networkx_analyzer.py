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


from decimal import Decimal, InvalidOperation


def _normalize_node_id(raw_id: Any) -> str:
    """Normalize node identifiers consistently across triples and work packages."""
    return str(raw_id or "").strip().upper()


def _extract_capex_score(wp: Any) -> Decimal:
    """Extract CAPEX numeric value safely as a Decimal for deterministic comparison."""
    raw = getattr(wp, "capex_numeric", 0) or 0
    try:
        val = Decimal(str(raw))
        return val if val.is_finite() else Decimal(0)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(0)


def _select_core_work_package(valid_wps: List[Any]) -> Any:
    """Select the core platform work package deterministically (highest CAPEX, then lexical ID)."""
    return max(
        valid_wps,
        key=lambda wp: (
            _extract_capex_score(wp),
            _normalize_node_id(getattr(wp, "id", "")),
        ),
    )


def _can_safely_add_precedence(
    graph: nx.DiGraph, core_id: str, target_id: str
) -> bool:
    """Check if adding an edge from core_id to target_id preserves DAG property."""
    c_norm = _normalize_node_id(core_id)
    t_norm = _normalize_node_id(target_id)
    if not c_norm or not t_norm or c_norm == t_norm or graph.has_edge(c_norm, t_norm):
        return False
    if c_norm not in graph or t_norm not in graph:
        return True
    return not nx.has_path(graph, t_norm, c_norm)


def _enforce_single_program_precedence(
    graph: nx.DiGraph, program: Any
) -> None:
    """Add precedence edges from the core package to contributing packages."""
    raw_wps = getattr(program, "work_packages", None) or []
    valid_wps = [
        wp for wp in raw_wps if _normalize_node_id(getattr(wp, "id", ""))
    ]
    if not valid_wps:
        return

    if len(valid_wps) == 1:
        graph.add_node(_normalize_node_id(getattr(valid_wps[0], "id", "")))
        return

    core_wp = _select_core_work_package(valid_wps)
    core_id = _normalize_node_id(getattr(core_wp, "id", ""))
    graph.add_node(core_id)

    for wp in valid_wps:
        wp_id = _normalize_node_id(getattr(wp, "id", ""))
        graph.add_node(wp_id)
        if _can_safely_add_precedence(graph, core_id, wp_id):
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