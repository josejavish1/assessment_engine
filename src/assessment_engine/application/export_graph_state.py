import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

from assessment_engine.application.run_strategic_orchestrator import (
    run_strategic_orchestration,
)
from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.networkx_analyzer import NetworkXAnalyzer
from assessment_engine.infrastructure.runtime_paths import (
    resolve_client_dir,
)
from assessment_engine.infrastructure.text_utils import slugify

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
            industry_name (str): The resolved industry name for the client.
        """
        self.client_name = client_name
        self.client_id = slugify(client_name)
        self.graph = EpistemicGraph(client_id=self.client_id)
        self.analyzer = NetworkXAnalyzer()
        self.industry_name = "Default / General Enterprise"

    def _load_industry_benchmark(self) -> Dict[str, float]:
        """Load and resolve industry-specific maturity benchmarks dynamically from the configuration profile.

        Extracts the client's industry sector from their client_intelligence.json or any available
        case_input.json, maps it to a canonical industry profile (e.g., critical_infrastructure, retail),
        and retrieves the configured maturity benchmark curve from the corresponding JSON configuration.

        Returns:
            A dictionary mapping tower IDs (e.g., 'T1', 'T2') to their benchmark maturity scores.
        """
        fallback_benchmarks = {
            "T1": 3.0,
            "T2": 3.0,
            "T3": 3.0,
            "T4": 3.0,
            "T5": 3.0,
            "T6": 3.0,
            "T7": 3.0,
            "T8": 3.0,
            "T9": 3.0,
            "T10": 3.0,
        }

        # Resolve paths
        client_dir = resolve_client_dir(self.client_name)
        case_input_path = client_dir / "case_input.json"

        # Dual-source resolution: first check client_intelligence.json, then fall back to case_input.json
        client_intel_path = client_dir / "client_intelligence.json"

        target_path = None
        if client_intel_path.exists():
            target_path = client_intel_path
        elif case_input_path.exists():
            target_path = case_input_path
        else:
            # Look for case_input.json in any tower subdirectories
            for p in client_dir.glob("**/case_input.json"):
                target_path = p
                break

        if not target_path or not target_path.exists():
            logger.warning(
                f"No client intelligence or case input files found for {self.client_name} at {client_dir}. Utilizing fallback benchmarks."
            )
            return fallback_benchmarks

        # Step 1: Extract the raw industry sector name from the client's data using utf-8-sig to handle BOM
        industry_name = ""
        try:
            with open(target_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)

            # Support both v2 and v3 dossier formats
            profile = data.get("profile", {})
            if isinstance(profile, dict):
                industry_name = profile.get("industry", "")
            if not industry_name:
                industry_name = data.get("industry", "")
        except Exception as e:
            logger.error(f"Failed to read or parse client data at {target_path}: {e}")
            return fallback_benchmarks

        if not industry_name:
            logger.warning(
                f"No industry sector defined in client data for {self.client_name}. Utilizing default profile."
            )
            industry_name = "default"

        self.industry_name = industry_name

        # Step 2: Map the raw industry name to its canonical profile key
        mapping = {
            "energía": "critical_infrastructure",
            "eléctrico": "critical_infrastructure",
            "infraestructura crítica": "critical_infrastructure",
            "transporte": "critical_infrastructure",
            "retail": "retail",
            "comercio": "retail",
            "banca": "banking",
            "finanzas": "banking",
            "seguros": "banking",
            "salud": "healthcare",
            "hospital": "healthcare",
        }

        industry_lower = industry_name.lower()
        profile_key = "default"
        for key, val in mapping.items():
            if key in industry_lower:
                profile_key = val
                break

        # Step 3: Load the benchmark curve from the resolved JSON profile
        config_path = Path("engine_config/industry_profiles") / f"{profile_key}.json"

        if not config_path.exists():
            logger.warning(
                f"Resolved industry profile file {config_path} does not exist. Utilizing fallback benchmarks."
            )
            return fallback_benchmarks

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)

            benchmarks = profile_data.get("benchmarks")
            if isinstance(benchmarks, dict):
                cleaned_benchmarks = {}
                for k, v in benchmarks.items():
                    cleaned_benchmarks[str(k).upper()] = float(v)
                logger.info(
                    f"✓ Dynamically loaded {len(cleaned_benchmarks)} benchmarks from '{profile_key}' profile."
                )
                return cleaned_benchmarks

            logger.warning(
                f"Profile '{profile_key}' does not contain a valid 'benchmarks' mapping. Utilizing fallback benchmarks."
            )
        except Exception as e:
            logger.error(
                f"Failed to load or parse benchmarks from industry profile {profile_key}: {e}"
            )

        return fallback_benchmarks

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
                "industry_name": self.industry_name,
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
        print(
            "Uso: python -m assessment_engine.application.export_graph_state <client_name>"
        )
        return

    client_name = args[1]
    exporter = DigitalTwinExporter(client_name)
    state = exporter.export_state()

    output_path = resolve_client_dir(client_name) / "digital_twin_state.json"
    output_path.write_text(json.dumps(state, indent=2, ensure_ascii=False))
    print(f"✅ State Object DTO generado: {output_path}")


if __name__ == "__main__":
    main()
