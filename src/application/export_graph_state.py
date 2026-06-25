import json
import logging
import sys
from typing import Any, Dict, List

from application.run_strategic_orchestrator import run_strategic_orchestration
from infrastructure.epistemic_graph import EpistemicGraph
from infrastructure.networkx_analyzer import NetworkXAnalyzer
from infrastructure.runtime_paths import resolve_client_dir
from infrastructure.text_utils import slugify

logger = logging.getLogger(__name__)


class DigitalTwinExporter:
    """Orchestrates the aggregation and export of a digital twin's canonical state.

    Aggregates data from a strategic orchestrator, an epistemic knowledge graph,
    and industry benchmarks to construct a comprehensive Data Transfer Object (DTO).
    This DTO encapsulates the client's strategic topology as a directed acyclic
    graph (DAG), maturity metrics, risk analysis, and a sequenced roadmap,
    structured according to a defined data contract for downstream consumers.

    Attributes:
        client_name (str): The human-readable name of the client.
        client_id (str): A slugified, unique identifier derived from the client name.
        graph (EpistemicGraph): An instance of the knowledge graph client scoped to
            the specified `client_id`.
        analyzer (NetworkXAnalyzer): An instance of a graph analysis utility.
    """

    def __init__(self, client_name: str):
        """Initializes the graph state for a specific client.

        Args:
            client_name: The human-readable name of the client. This name is
                converted into a URL-safe identifier ('slug') for the graph.

        Attributes:
            client_name (str): The original, human-readable name of the client.
            client_id (str): A slugified identifier derived from `client_name`.
            graph (EpistemicGraph): An `EpistemicGraph` instance for the client.
            analyzer (NetworkXAnalyzer): A graph analyzer instance.
        """
        self.client_name = client_name
        self.client_id = slugify(client_name)
        self.graph = EpistemicGraph(client_id=self.client_id)
        self.analyzer = NetworkXAnalyzer()

    def _load_industry_benchmark(self) -> Dict[str, float]:
        """Retrieves industry-specific maturity benchmarks for the client's designated industrial sector."""
        # TODO(jsanchhi): #81 Implement a production-ready solution for dynamic industry profile lookups to replace the current placeholder logic.
        # A default benchmark score of 3.5 is hardcoded for the Energy sector as a temporary measure until dynamic, profile-based lookups are implemented.
        return {
            "T1": 3.2,
            "T2": 3.8,
            "T3": 3.5,
            "T4": 3.0,
            "T5": 3.4,
            "T6": 4.0,
            "T7": 3.1,
            "T8": 2.8,
            "T9": 3.6,
            "T10": 2.5,
        }

    def export_state(self) -> Dict[str, Any]:
        """Assembles a Data Transfer Object of the digital twin's canonical state.

        This method orchestrates the aggregation of data from three primary sources:
        the strategic topology from `run_strategic_orchestration`, core system metrics
        from the knowledge graph (`self.graph.resolve_truth`), and industry maturity
        benchmarks from `self._load_industry_benchmark`. The internal graph
        representation is then transformed into a JSON-serializable dictionary with a
        node-edge list structure suitable for consumption by front-end services.

        Returns:
            A dictionary containing the canonical state of the digital twin. It is
            structured with the following keys:
            - 'meta': Metadata including client info, version, and timestamp.
            - 'topology': A dictionary with 'nodes' and 'edges' lists formatted
              for front-end graph visualization.
            - 'benchmarks': Industry-standard benchmark data mapped to topology
              nodes.
            - 'roadmap': The strategic roadmap data from the orchestration service.

        Raises:
            KeyError: If data from the knowledge graph or strategic orchestration
                service is malformed. This can occur if `run_strategic_orchestration`
                output is missing the 'roadmap' key, or if a predicate dictionary
                used to form an edge lacks the 'value' key.
        """
        print(f"📦 [DTO Exporter] Compilando State Object para {self.client_name}...")

        # Resolve the directed acyclic graph (DAG) that represents the strategic topology, including wave sequencing and inter-node dependencies.
        strategic_data = run_strategic_orchestration(self.client_name)

        # Extract the canonical, resolved values for all relevant system metrics from the knowledge graph.
        truth = self.graph.resolve_truth()

        # Construct the benchmark data layer by mapping industry-standard scores to their corresponding topology nodes.
        benchmarks = self._load_industry_benchmark()

        # Assemble the final Sovereign State DTO by integrating the topology, metrics, and benchmark data layers.
        state_object = {
            "meta": {
                "client": self.client_name,
                "client_id": self.client_id,
                "version": "v1.0-DTO",
                "timestamp": int(
                    self.graph.resolve_truth().get("TIMESTAMP", {}).get("value", 0)
                )
                or 1712160000,
            },
            "topology": {"nodes": [], "edges": []},
            "benchmarks": {
                "industry_name": "Energy & Infrastructure",
                "data": benchmarks,
            },
            "roadmap": strategic_data["roadmap"],
        }

        # The internal graph representation is transformed into the specific JSON schema contractually required by the front-end for topology visualization.
        for subj, predicates in truth.items():
            #
            node_type = "UNKNOWN"
            if "ADDRESSES_PILLAR" in predicates or "PROPOSES_INITIATIVE" in predicates:
                node_type = "INITIATIVE"
            elif "IDENTIFIED_AS_GAP" in predicates or "IMPACTS_PILLAR" in predicates:
                node_type = "RISK"

            #
            node_score = None
            tower_id = "GLOBAL"

            # The primary strategy for score extraction relies on locating an explicit 'score' predicate in the node data.
            for pred, data in predicates.items():
                if isinstance(data, dict):
                    if "score" in data:
                        node_score = data["score"]
                    if "metadata" in data and "score" in data["metadata"]:
                        node_score = data["metadata"]["score"]

                # The `tower_id` is primarily sourced from the 'sources' or 'metadata' fields, which serve as the authoritative provenance for this identifier.
                if isinstance(data, dict):
                    source = str(data.get("source", ""))
                    if source.startswith("TOWER_"):
                        tower_id = source.replace("TOWER_", "")
                    if "metadata" in data and "pillar" in data["metadata"]:
                        tower_id = data["metadata"]["pillar"].split(".")[0]

            # If a direct score predicate is absent, the system attempts to infer a score from the associated ontology as a fallback mechanism.
            if node_score is None and subj.startswith("T") and "." in subj:
                # Future implementations should validate nodes against the `ontology_registry` to ensure canonical representation and data integrity.
                pass

            state_object["topology"]["nodes"].append(
                {
                    "id": subj,
                    "label": predicates.get("PROPOSES_INITIATIVE", {}).get("value")
                    or predicates.get("IDENTIFIED_AS_GAP", {}).get("value")
                    or subj,
                    "type": node_type,
                    "score": node_score,
                    "tower_id": tower_id,
                    "metadata": predicates,
                }
            )

            #
            for pred, data in predicates.items():
                if pred in [
                    "REQUIRES_PREREQUISITE",
                    "DEPENDS_ON",
                    "REQUIRES",
                    "MITIGATES_RISK",
                    "ENABLES",
                ]:
                    val = data["value"]
                    # The 'REQUIRES' predicate mandates a non-standard edge directionality in the DAG. For this relationship, the triple's subject becomes the source node and its object becomes the target node (subject -> object), contrary to conventional graph mappings.
                    # The 'REQUIRES' predicate mandates a non-standard edge directionality in the DAG. For this relationship, the triple's subject becomes the source node and its object becomes the target node (subject -> object), contrary to conventional graph mappings.
                    state_object["topology"]["edges"].append(
                        {
                            "source": subj,
                            "target": val.upper() if isinstance(val, str) else str(val),
                            "relation": pred,
                        }
                    )

        return state_object


def main(argv: List[str] | None = None):
    """Serializes the digital twin graph state of a client to a JSON file.

    This function serves as the main entry point for a command-line script.
    It parses the client name from the command-line arguments, instantiates a
    `DigitalTwinExporter` to retrieve the graph state, and writes the serialized
    state to a file named `digital_twin_state.json` in the client's resolved
    directory.

    Args:
        argv: An optional list of command-line arguments. If None, `sys.argv`
            is used. The script expects the client name as the first positional
            argument after the script name.

    Raises:
        FileNotFoundError: If the directory for the specified client cannot be
            resolved.
        IOError: If the state file cannot be written to disk.
    """
    args = argv if argv is not None else sys.argv
    if len(args) < 2:
        print("Uso: python -m application.export_graph_state <client_name>")
        return

    client_name = args[1]
    exporter = DigitalTwinExporter(client_name)
    state = exporter.export_state()

    output_path = resolve_client_dir(client_name) / "digital_twin_state.json"
    output_path.write_text(json.dumps(state, indent=2, ensure_ascii=False))
    print(f"✅ State Object DTO generado: {output_path}")


if __name__ == "__main__":
    main()
