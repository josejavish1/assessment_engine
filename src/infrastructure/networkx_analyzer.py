from typing import Any, Dict, List

import networkx as nx

from ports.graph_analyzer import GraphAnalyzer


class NetworkXAnalyzer(GraphAnalyzer):
    r"""[{'identifier': 'NetworkXAnalyzer', 'docstring': 'Provides an adapter for the NetworkX library for graph analysis.\n\nThis class encapsulates logic for constructing directed graphs from semantic\ntriples, detecting circular dependencies, and performing topological sorts\nto determine execution waves.\n\nAttributes:\n    graph: A `networkx.DiGraph` instance holding the graph data.'}, {'identifier': 'NetworkXAnalyzer.__init__', 'docstring': 'Initializes the NetworkXAnalyzer with an empty `networkx.DiGraph`.\n\nAttributes:\n    graph: The `networkx.DiGraph` instance used for all graph operations.'}, {'identifier': 'NetworkXAnalyzer.build_graph_from_triples', 'docstring': "Builds the internal directed graph from a list of semantic triples.\n\nThis method first clears any existing graph data. It then iterates through\nthe provided triples, adding nodes and edges. All subject, object, and\npredicate names are normalized to uppercase for case-insensitive processing.\n\nThe direction of a created edge depends on the predicate:\n- 'REQUIRES_PREREQUISITE', 'DEPENDS_ON', 'REQUIRES': An edge is created\n  from the object to the subject (object -> subject) to model that the\n  object must be completed before the subject, which is the correct\n  representation for a topological sort.\n- 'ENABLES', 'BLOCKS': An edge is created from the subject to the object\n  (subject -> object).\n\nTriples with missing or empty string values for 'subject' or 'object_val'\nare silently ignored.\n\nArgs:\n    triples: A list of dictionaries, where each dictionary represents a\n        semantic triple with 'subject', 'predicate', and 'object_val' keys.\n\nRaises:\n    AttributeError: If a dictionary in `triples` lacks required keys or if\n        a value is not a string, causing methods like `.upper()` to fail.\n    TypeError: If `triples` is not an iterable."}, {'identifier': 'NetworkXAnalyzer.detect_cycles', 'docstring': 'Detects all simple cycles in the directed graph.\n\nThis method identifies circular dependencies by delegating to the\n`networkx.simple_cycles` algorithm. Cycles indicate that the graph is not a\nDirected Acyclic Graph (DAG), which is a prerequisite for dependency\nanalyses such as topological sorting. Any `Exception` during cycle\ndetection is caught, and an empty list is returned.\n\nReturns:\n    List[List[str]]: A list of cycles. Each cycle is represented as a list\n    of node identifiers. Returns an empty list if no cycles are found or\n    if an error occurs during computation.'}, {'identifier': 'NetworkXAnalyzer.calculate_topological_waves', 'docstring': 'Calculates execution waves by topologically sorting the graph nodes.\n\nA "wave" is a set of nodes that can be processed concurrently. A node\'s wave\nnumber is defined as the length of the longest path from any source node (a\nnode with zero in-degree) to that node. This method partitions nodes into\nwaves, suitable for creating a phased execution plan.\n\nAfter wave calculation, nodes are filtered to include only "roadmap\ncandidates." This filtering is based on internal heuristics that exclude\nnodes with very long names (assumed to be descriptions) or names matching\npatterns of high-level organizational constructs (e.g., \'Pillar.1\').\n\nThe first three waves are given descriptive labels: "Wave 0: Foundation",\n"Wave 1: Transformation", and "Wave {i}: Advanced State" for subsequent waves.\n\nReturns:\n    List[Dict[str, Any]]: A list of dictionaries, one for each non-empty\n    wave. Each dictionary contains a \'wave\' key with a descriptive string\n    label and a \'projects\' key with a list of node identifiers belonging\n    to that wave. Returns an empty list if the graph contains cycles, as\n    a topological sort is not possible.'}, {'identifier': 'NetworkXAnalyzer.get_critical_path', 'docstring': 'Calculates the unweighted shortest path between two nodes.\n\nNOTE: This method computes the shortest path in terms of the number of\nedges. In project management, the "critical path" typically refers to the\n*longest* path, which represents the minimum time to complete a project.\nThis implementation does not calculate the longest path.\n\nThe graph must be a Directed Acyclic Graph (DAG).\n\nArgs:\n    start_node: The identifier of the starting node for the path.\n    end_node: The identifier of the ending node for the path.\n\nReturns:\n    List[str]: A list of node identifiers representing the shortest path\n    from `start_node` to `end_node`, inclusive. Returns an empty list if\n    the graph is not a DAG, if either `start_node` or `end_node` does not\n    exist, or if no path exists between them.'}]."""

    def __init__(self):
        """{'docstring': 'Initializes the analyzer with an empty NetworkX DiGraph.'}."""
        self.graph = nx.DiGraph()

    def build_graph_from_triples(self, triples: List[Dict[str, Any]]) -> None:
        r"""{'docstring': "Reconstructs the internal directed graph from a list of semantic triples.\n\nThis method first clears any existing graph data, then populates the graph by\niterating through the provided list of triples. Node and predicate\nidentifiers are treated case-insensitively by converting them to uppercase.\n\nThe direction of a created edge is conditional upon the predicate:\n  - `REQUIRES_PREREQUISITE`, `DEPENDS_ON`, `REQUIRES`: An edge is created\n    from the object to the subject (`object -> subject`). This models the\n    object as a prerequisite that must precede the subject, which is a\n    standard convention for dependency graphing and topological sorting.\n  - `ENABLES`, `BLOCKS`: An edge is created from the subject to the object\n    (`subject -> object`).\n\nThe edge is annotated with a `relation` attribute containing the predicate.\nTriples are silently ignored if the 'subject' or 'object_val' keys are\nmissing or their corresponding values are empty strings.\n\nArgs:\n    triples: A list of dictionaries, where each dictionary represents a\n        semantic triple. Each dictionary must contain 'subject',\n        'predicate', and 'object_val' keys with string values.\n\nRaises:\n    TypeError: If `triples` is not an iterable.\n    AttributeError: If an element within `triples` is not a dictionary, or\n        if a value for 'subject', 'predicate', or 'object_val' is not a\n        string and therefore lacks an `upper()` method."}."""
        self.graph.clear()
        for t in triples:
            subj = t.get("subject", "").upper()
            pred = t.get("predicate", "").upper()
            obj = t.get("object_val", "").upper()

            if not subj or not obj:
                continue

            #
            self.graph.add_node(subj)
            self.graph.add_node(obj)

            #
            # The edge direction is inverted from the semantic predicate. For a 'REQUIRES' relationship, the dependency is modeled as B -> A to ensure the prerequisite (B) precedes the subject (A) in a topological sort.
            if pred in ["REQUIRES_PREREQUISITE", "DEPENDS_ON", "REQUIRES"]:
                self.graph.add_edge(obj, subj, relation=pred)
            elif pred in ["ENABLES", "BLOCKS"]:
                # The 'ENABLES' predicate directly maps to a directed edge from the enabler to the enabled node (A -> B), signifying a direct prerequisite relationship.
                self.graph.add_edge(subj, obj, relation=pred)

    def detect_cycles(self) -> List[List[str]]:
        r"""{'docstring': 'Detects all simple cycles in the graph.\n\n    A cycle represents a circular dependency where a sequence of nodes leads\n    back to the starting node. This method acts as a safe wrapper around the\n    `networkx.simple_cycles` generator, suppressing any exceptions that occur\n    during the detection process.\n\n    Returns:\n        A list of cycles, where each cycle is a list of node identifiers\n        (strings). An empty list is returned if no cycles are found or if an\n        exception is encountered.'}."""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except Exception:
            return []

    def calculate_topological_waves(self) -> List[Dict[str, Any]]:
        """Computes execution waves for nodes in a directed acyclic graph (DAG).

        This method partitions graph nodes into execution 'waves'. A node's wave is
        determined by the length of the longest path from any source node (a node
        with an in-degree of zero) to that node. This layering creates a sequence of
        execution groups where all prerequisites for a given wave are satisfied by
        nodes in preceding waves.

        A heuristic filter is applied to include only nodes representing actionable
        project items, excluding nodes that appear to be high-level organizational
        constructs or descriptive text based on their identifiers.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a single
                execution wave. Each dictionary contains:
                - 'wave' (str): A descriptive label for the wave (e.g., "Wave 0:
                  Foundation").
                - 'projects' (List[str]): A list of node identifiers within that
                  wave that pass the filtering criteria.
                Returns an empty list if the graph contains a cycle, as a
                topological sort is not feasible.
        """
        if not nx.is_directed_acyclic_graph(self.graph):
            # If cycles are detected, topological sorting is infeasible. The process falls back to a non-dependency-aware sorting mechanism or raises an alert.
            pass

        def is_roadmap_candidate(node_id: str) -> bool:
            r"""{'docstring': 'Determine if a graph node identifier qualifies as a roadmap item candidate.\n\nApplies a set of heuristics to a node\'s identifier to filter out nodes\nthat are unlikely to represent discrete, executable strategic items. This\nfunction filters based on identifier length and specific structural patterns.\n\nThe function returns False for identifiers that meet any of the following\nexclusion criteria:\n  - Are not strings.\n  - Exceed 100 characters in length, which are heuristically assumed to be\n    descriptive text rather than item labels.\n  - Are fewer than 10 characters long and contain a period ("."), a pattern\n    assumed to represent high-level structural identifiers (e.g.,\n    \'Pillar.1\') rather than executable tasks.\n\nArgs:\n    node_id (str): The unique identifier of the graph node to evaluate.\n\nReturns:\n    bool: True if the node identifier meets the roadmap candidate criteria,\n        False otherwise.'}."""
            if not isinstance(node_id, str):
                return False
            # Exclude nodes with excessively long labels, which are heuristically assumed to be descriptive text (e.g., GAP analysis findings) rather than discrete strategic entities.
            if len(node_id) > 100:
                return False
            # Exclude nodes representing high-level organizational constructs (e.g., Pillars, KPIs) to focus the analysis on executable items.
            if "." in node_id and len(node_id) < 10:
                return False
            return True

        try:
            # Wave assignment is determined by calculating the longest path distance of each node from a source node (a node with an in-degree of zero).
            waves = {}
            for node in nx.topological_sort(self.graph):
                # The longest path from any source node establishes the total number of execution waves.
                in_edges = list(self.graph.in_edges(node))
                if not in_edges:
                    depth = 0
                else:
                    depth = max(waves.get(u, 0) for u, v in in_edges) + 1
                waves[node] = depth

            #
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

                #
                nodes_in_wave = [
                    node
                    for node, w in waves.items()
                    if w == i and is_roadmap_candidate(node)
                ]

                if nodes_in_wave:
                    roadmap.append({"wave": wave_label, "projects": nodes_in_wave})
            return roadmap
        except nx.NetworkXUnfeasible:
            #
            return []

    def get_critical_path(self, start_node: str, end_node: str) -> List[str]:
        """Calculates the shortest path between two nodes in a directed acyclic graph.

        Note: This method computes the *shortest* path. It is named `get_critical_path`
        for contextual domain reasons, but it does not compute the longest path, which
        is the standard definition of a critical path in project management.

        The graph is first validated to be a DAG. An empty list is returned if the
        graph is not a DAG, if the start or end nodes are not present in the graph,
        or if no path exists between them.

        Args:
            start_node: The identifier of the path's starting node.
            end_node: The identifier of the path's ending node.

        Returns:
            A list of node identifiers representing the shortest path from
            `start_node` to `end_node`. Returns an empty list if the graph is not a
            DAG, if either node is not found, or if no path exists.
        """
        if not nx.is_directed_acyclic_graph(self.graph):
            return []
        try:
            # The critical path is algorithmically defined as the longest path within a directed acyclic graph (DAG).
            # The NetworkX library does not provide a native longest_path function for weighted DAGs.
            # The canonical solution involves negating edge weights and executing a shortest_path algorithm (e.g., Bellman-Ford) to find the equivalent longest path.
            return nx.shortest_path(self.graph, start_node, end_node)
        except Exception:
            return []
