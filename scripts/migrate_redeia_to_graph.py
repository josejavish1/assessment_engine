import json
from pathlib import Path

from application.run_tower_blueprint_engine import sync_findings_to_graph
from domain.ontology_registry import OntologyRegistry
from infrastructure.entity_resolution import EntityResolutionEngine
from infrastructure.epistemic_graph import EpistemicGraph
from infrastructure.text_utils import slugify


def migrate_redeia():
    client_name = "redeia"
    client_dir = Path(f"working/{client_name}")

    print("🚀 [Migrator] Migrando hallazgos de REDEIA al Epistemic Graph...")

    graph = EpistemicGraph(client_id=slugify(client_name))
    resolver = EntityResolutionEngine()
    ontology = OntologyRegistry()

    blueprint_files = list(client_dir.glob("T*/blueprint_*_payload.json"))

    for bp_path in blueprint_files:
        tower_id = bp_path.parent.name
        print(f"  -> Procesando {tower_id}...")

        with open(bp_path, "r", encoding="utf-8-sig") as f:
            payload = json.load(f)

        sync_findings_to_graph(
            graph=graph,
            entity_resolver=resolver,
            ontology=ontology,
            blueprint_payload=payload,
            tower_id=tower_id,
        )

        # Save updated payload back (with node_ids)
        with open(bp_path, "w", encoding="utf-8-sig") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Migración completada. Ledger creado en {graph.ledger_path}")
    print("Ahora puedes ejecutar el pipeline global para ver el Roadmap orquestado.")


if __name__ == "__main__":
    migrate_redeia()
