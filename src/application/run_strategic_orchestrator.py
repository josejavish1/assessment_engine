import json
import logging
import sys
from typing import Any, Dict

from infrastructure.epistemic_graph import EpistemicGraph
from infrastructure.networkx_analyzer import NetworkXAnalyzer
from infrastructure.text_utils import slugify

logger = logging.getLogger(__name__)


def run_strategic_orchestration(client_name: str) -> Dict[str, Any]:
    """
    Main entry point for Strategic Graph Orchestration.
    Resolves the Roadmap DAG from the Sovereign Epistemic Graph.
    """
    print(f"🚀 [Strategic Orchestrator] Resolviendo Grafo Global para {client_name}...")

    graph = EpistemicGraph(client_id=slugify(client_name))
    analyzer = NetworkXAnalyzer()

    # 1. Materialize State from Ledger
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

    # 2. Build DAG
    analyzer.build_graph_from_triples(triples)

    # 3. Detect Cycles
    cycles = analyzer.detect_cycles()
    if cycles:
        print(f"⚠️  [Strategic Risk] Ciclos detectados en las dependencias: {cycles}")
        # In Tier-1, we would have a mitigation strategy here.

    # 4. Calculate Waves
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
        print("Uso: python -m application.run_strategic_orchestrator <client_name>")
        sys.exit(1)

    res = run_strategic_orchestration(sys.argv[1])
    print(json.dumps(res, indent=2, ensure_ascii=False))
