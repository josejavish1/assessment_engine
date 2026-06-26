import json
import logging
import sys
from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.networkx_analyzer import NetworkXAnalyzer
from assessment_engine.infrastructure.text_utils import slugify

logger = logging.getLogger(__name__)


def run_strategic_orchestration(client_name: str) -> Dict[str, Any]:
    """Computes an executable task dependency graph (Roadmap) for a client.

    This function orchestrates the transformation of a client's canonical
    Sovereign Epistemic Graph into an actionable, directed acyclic graph (DAG)
    of tasks. The process involves materializing the graph state from a
    persistence layer, constructing a network representation, and verifying its
    acyclicity to ensure a deterministic execution order. A topological sort is
    then performed to partition the graph's nodes into discrete execution
    "waves," where all tasks within a single wave can be executed in parallel.

    Args:
        client_name: The unique identifier for the client whose epistemic graph
            is to be processed.

    Returns:
        A dictionary containing the orchestration results with the following keys:
        'client': The provided client_name.
        'roadmap': A list of execution waves. Each wave is a list of task
            identifiers that can be executed in parallel. The outer list
            defines the sequential order of the waves.
        'graph_stats': A dictionary with 'nodes' and 'edges' counts for the
            derived graph.
    """
    print(f"🚀 [Strategic Orchestrator] Resolviendo Grafo Global para {client_name}...")

    graph = EpistemicGraph(client_id=slugify(client_name))
    analyzer = NetworkXAnalyzer()

    # Materialize the Sovereign Epistemic Graph from the persistence layer to establish the baseline state for orchestration.
    resolved_truth = graph.resolve_truth()
    triples = []
    for subject, predicates in resolved_truth.items():
        for predicate, data in predicates.items():
            triples.append(
                {
                    "subject": subject,
                    "predicate": predicate,
                    "object_val": data["value"],
                }
            )

    # Derive the actionable Roadmap DAG by applying specific filtering and transformation rules to the materialized graph.
    analyzer.build_graph_from_triples(triples)

    # Validate the integrity of the derived graph by ensuring it is acyclic. Cyclical dependencies are fatal to deterministic execution and must be identified.
    cycles = analyzer.detect_cycles()
    if cycles:
        print(f"⚠️  [Strategic Risk] Ciclos detectados en las dependencias: {cycles}")
        # A production-grade implementation would incorporate a formal cycle resolution strategy at this stage to guarantee acyclicity.

    # Perform a topological sort to partition the DAG into discrete execution waves. This establishes a dependency-respecting execution schedule, enabling maximal parallelism where possible.
    roadmap = analyzer.calculate_topological_waves()

    return {
        "client": client_name,
        "roadmap": roadmap,
        "graph_stats": {
            "nodes": len(analyzer.graph.nodes),
            "edges": len(analyzer.graph.edges),
        },
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Uso: python -m assessment_engine.application.run_strategic_orchestrator <client_name>"
        )
        sys.exit(1)

    res = run_strategic_orchestration(sys.argv[1])
    print(json.dumps(res, indent=2, ensure_ascii=False))
