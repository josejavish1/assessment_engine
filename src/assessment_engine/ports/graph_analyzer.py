from abc import ABC, abstractmethod
from typing import Any, Dict, List


class GraphAnalyzer(ABC):
    r"""[{'name': 'GraphAnalyzer', 'docstring': 'Defines the abstract interface for graph-based strategic analysis.\n\n    This class acts as a port in a hexagonal architecture, decoupling the core\n    domain logic (e.g., topological sorting, cycle detection) from concrete\n    graph library implementations (e.g., NetworkX, graph-tool). This enables\n    interoperability and enhances testability by allowing mock implementations.'}, {'name': 'build_graph_from_triples', 'docstring': "Constructs the internal graph representation from dependency triples.\n\n        This abstract method defines the interface for populating the graph by\n        creating nodes and directed edges that model the dependency relationships\n        defined in the input. Implementations of this method should be idempotent;\n        multiple calls with the same input must result in the same graph state.\n\n        Args:\n            triples: A list of dictionaries, where each dictionary represents a\n                directed edge. Each dictionary must contain 'source' and 'target'\n                keys specifying the nodes. Additional keys may be used to store\n                edge attributes.\n\n        Returns:\n            None.\n\n        Raises:\n            ValueError: If any dictionary in the `triples` list is malformed (e.g.,\n                missing 'source' or 'target' keys).\n            TypeError: If `triples` is not a list of dictionaries."}, {'name': 'detect_cycles', 'docstring': 'Detects all cyclical dependencies within the graph.\n\n        A dependency graph must be a Directed Acyclic Graph (DAG) for its\n        relationships to be logically coherent and to permit a valid topological\n        sort. The presence of cycles indicates a logical contradiction in the\n        dependency model (e.g., A depends on B, and B depends on A).\n\n        Returns:\n            A list of cycles found in the graph. Each cycle is represented as a\n            list of node identifiers that form the loop. Returns an empty list if\n            the graph is acyclic.\n\n        Raises:\n            RuntimeError: If the graph has not been built prior to this call.'}, {'name': 'calculate_topological_waves', 'docstring': 'Partitions the graph into sequential execution waves using topological sorting.\n\n        Each wave contains a set of nodes (e.g., tasks) that can be executed\n        concurrently because their prerequisite dependencies have been met by the\n        completion of prior waves. This method is only defined for a Directed\n        Acyclic Graph (DAG).\n\n        Returns:\n            A list of dictionaries, where each dictionary represents a single\n            execution wave. The order of the list implies the sequence of\n            execution. The structure of the dictionary is implementation-specific\n            but contains the constituent nodes of the wave.\n\n        Raises:\n            ValueError: If the graph contains cycles, as a topological sort is\n                undefined for non-DAGs.\n            RuntimeError: If the graph has not been built prior to this call.'}, {'name': 'get_critical_path', 'docstring': 'Calculates the critical path between two specified nodes.\n\n        In a weighted Directed Acyclic Graph (DAG) used for project scheduling,\n        the critical path is the longest path from a start node to an end node.\n        The length of this path determines the minimum time required to complete\n        all tasks between these two points.\n\n        Args:\n            start_node: The identifier of the node where the path begins.\n            end_node: The identifier of the node where the path ends.\n\n        Returns:\n            An ordered list of node identifiers representing the critical path,\n            inclusive of the start and end nodes.\n\n        Raises:\n            ValueError: If `start_node` or `end_node` do not exist in the graph,\n                or if the graph contains cycles, which makes the longest path\n                ill-defined.\n            LookupError: If no path exists between the `start_node` and `end_node`.\n            RuntimeError: If the graph has not been built prior to this call.'}]."""

    @abstractmethod
    def build_graph_from_triples(self, triples: List[Dict[str, Any]]) -> None:
        r"""{'docstring': "Constructs the internal graph from a list of dependency triples.\n\nThis abstract method defines the contract for populating the graph.\nImplementations must parse a list of dependency triples, adding a directed\nedge from a 'source' node to a 'target' node for each triple. Nodes are\ncreated if they do not already exist. This operation must be idempotent;\nsubsequent calls with identical triples must not alter the graph's state.\n\nArgs:\n    triples: A list of dictionaries, where each dictionary represents a\n        single directed dependency. Each dictionary must contain 'source' and\n        'target' keys, whose values identify the origin and destination\n        nodes.\n\nRaises:\n    ValueError: If a dictionary within `triples` is malformed (e.g., is\n        missing a 'source' or 'target' key).\n    TypeError: If `triples` is not a list or if any of its elements are\n        not dictionaries."}."""
        pass

    @abstractmethod
    def detect_cycles(self) -> List[List[str]]:
        r"""{'docstring': 'Detects all cyclical dependencies within the graph.\n\nA dependency model must be a Directed Acyclic Graph (DAG) to allow for\ntopological sorting. The presence of cycles indicates a logical\ninconsistency in the dependency structure, which prevents the determination of\na valid sequential execution order. This method implements an algorithm to\nfind all such cyclical paths.\n\nReturns:\n    List[List[str]]: A list of all detected cycles. Each inner list\n        represents a single cycle and contains the string identifiers of the\n        nodes in the order they appear. Returns an empty list if the graph\n        is acyclic.'}."""
        pass

    @abstractmethod
    def calculate_topological_waves(self) -> List[Dict[str, Any]]:
        r"""{'docstring': 'Partitions the project dependency graph into sequential execution waves.\n\nPerforms a topological sort on the dependency graph to group projects into\nwaves. All projects within a single wave have no interdependencies and can\nbe executed in parallel. Subsequent waves contain projects that depend on the\ncompletion of projects in prior waves.\n\nReturns:\n    List[List[Dict[str, Any]]]: A list of waves, where each wave is a list\n        of project dictionaries that can be executed in parallel.\n\nRaises:\n    ValueError: If a circular dependency is detected in the project graph,\n        which makes a topological sort impossible.'}."""
        pass

    @abstractmethod
    def get_critical_path(self, start_node: str, end_node: str) -> List[str]:
        """Computes the critical path between two nodes in a directed acyclic graph (DAG).

        The critical path is defined as the longest path from a start node to an
        end node. The concept is only well-defined for DAGs, as the longest path
        is indeterminate in graphs that contain positive-weight cycles.

        This is an abstract method; concrete subclasses must provide the
        implementation for the pathfinding logic.

        Args:
            start_node (str): The identifier for the starting node of the path.
            end_node (str): The identifier for the ending node of the path.

        Returns:
            List[str]: An ordered list of node identifiers representing the
                critical path, inclusive of the start and end nodes.

        Raises:
            ValueError: If `start_node` or `end_node` do not exist in the graph,
                or if the graph contains a cycle.
            LookupError: If no path exists between the specified start and end
                nodes.
        """
        pass
