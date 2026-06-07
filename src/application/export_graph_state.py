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
    """
    Tier-1 DTO State Exporter.
    Compiles the 'Data Cartridge' for the Sovereign Dashboard.
    """

    def __init__(self, client_name: str):
        self.client_name = client_name
        self.client_id = slugify(client_name)
        self.graph = EpistemicGraph(client_id=self.client_id)
        self.analyzer = NetworkXAnalyzer()

    def _load_industry_benchmark(self) -> Dict[str, float]:
        """Loads maturity benchmarks for the client's industry."""
        # TODO: Implement real industry profile lookup
        # Defaulting to 3.5 for Energy sector as a placeholder
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
        """
        Compiles the master Digital Twin state.
        Includes: Topology (DAG), Benchmarks, and Risk Nexus.
        """
        print(f"📦 [DTO Exporter] Compilando State Object para {self.client_name}...")

        # 1. Resolve Strategic Topology (Waves & Dependencies)
        strategic_data = run_strategic_orchestration(self.client_name)

        # 2. Extract Resolved Truth for Metrics
        truth = self.graph.resolve_truth()

        # 3. Build Benchmark Layer
        benchmarks = self._load_industry_benchmark()

        # 4. Construct the Sovereign State Object
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

        # Transform Graph to UI Topology
        for subj, predicates in truth.items():
            # Add Nodes
            node_type = "UNKNOWN"
            if "ADDRESSES_PILLAR" in predicates or "PROPOSES_INITIATIVE" in predicates:
                node_type = "INITIATIVE"
            elif "IDENTIFIED_AS_GAP" in predicates or "IMPACTS_PILLAR" in predicates:
                node_type = "RISK"

            # Extract score and tower_id
            node_score = None
            tower_id = "GLOBAL"

            # 1. Search for score in predicates
            for pred, data in predicates.items():
                if isinstance(data, dict):
                    if "score" in data:
                        node_score = data["score"]
                    if "metadata" in data and "score" in data["metadata"]:
                        node_score = data["metadata"]["score"]

                # 2. Search for tower_id in sources or metadata
                if isinstance(data, dict):
                    source = str(data.get("source", ""))
                    if source.startswith("TOWER_"):
                        tower_id = source.replace("TOWER_", "")
                    if "metadata" in data and "pillar" in data["metadata"]:
                        tower_id = data["metadata"]["pillar"].split(".")[0]

            # 3. Fallback score detection from ontology if available
            if node_score is None and subj.startswith("T") and "." in subj:
                # Could lookup in ontology_registry if we want perfection
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

            # Add Edges
            for pred, data in predicates.items():
                if pred in [
                    "REQUIRES_PREREQUISITE",
                    "DEPENDS_ON",
                    "REQUIRES",
                    "MITIGATES_RISK",
                    "ENABLES",
                ]:
                    val = data["value"]
                    # For edges, we use the value as the target and the subject as the source usually,
                    # but in our DAG, REQUIRES means subj -> val
                    state_object["topology"]["edges"].append(
                        {
                            "source": subj,
                            "target": val.upper() if isinstance(val, str) else str(val),
                            "relation": pred,
                        }
                    )

        return state_object


def main(argv: List[str] | None = None):
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
