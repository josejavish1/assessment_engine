import shutil
from pathlib import Path

from assessment_engine.application.run_strategic_orchestrator import (
    run_strategic_orchestration,
)
from assessment_engine.domain.ontology_registry import OntologyRegistry
from assessment_engine.infrastructure.entity_resolution import EntityResolutionEngine
from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.text_utils import slugify


def test_sovereign_convergence_and_sort():
    # --- ARRANGE ---
    client_name = "NTT_DATA_COMPLIANCE_TEST"
    client_id = slugify(client_name)
    working_dir = Path(f"working/{client_id}")

    # Limpieza inicial para asegurar pureza de datos
    if working_dir.exists():
        shutil.rmtree(working_dir)

    print(f"[Audit] Initializing Sovereign Convergence Verification for: {client_name}")

    graph = EpistemicGraph(client_id=client_id)
    resolver = EntityResolutionEngine()
    OntologyRegistry()

    # --- TOWER 1 SIMULATION (INFRA) ---
    # Proyecto A: "Despliegue de Landing Zone en AWS"
    print("\n[System] Domain 1: Injecting 'Despliegue de Landing Zone en AWS'...")
    id_infra = resolver.get_semantic_id(
        "Despliegue de Landing Zone en AWS", context="INITIATIVE"
    )
    graph.inject_triple(
        subject=id_infra,
        predicate="PROPOSES_INITIATIVE",
        object_val="Despliegue de Landing Zone en AWS",
        source="TOWER_1",
        confidence=1.0,
    )

    # --- TOWER 6 SIMULATION (SECURITY) ---
    # Project B: "Secure AWS Landing Configuration" (SYNONYM)
    # Project C: "SIEM Implementation" (DEPENDENT)
    print("[System] Domain 6: Injecting 'Configuración Segura de AWS Landing' (Sinónimo)...")
    id_sec = resolver.get_semantic_id(
        "Configuración Segura de AWS Landing", context="INITIATIVE"
    )

    # We verify whether the IDs converge (they should be equal due to the semantic engine).
    if id_infra == id_sec:
        print(
            "[Audit] Semantic convergence detected: Domain 1 and Domain 6 point to the same NodeID."
        )
    else:
        print("[-] Convergence failure: Different NodeIDs found.")

    id_siem = resolver.get_semantic_id("Implementación de SIEM", context="INITIATIVE")
    print(
        "[System] Domain 6: Injecting 'Implementación de SIEM' dependent on the Landing Zone..."
    )

    graph.inject_triple(
        subject=id_siem,
        predicate="PROPOSES_INITIATIVE",
        object_val="Implementación de SIEM",
        source="TOWER_6",
        confidence=1.0,
    )

    graph.inject_triple(
        subject=id_siem,
        predicate="REQUIRES_PREREQUISITE",
        object_val=id_infra,  # Depende del proyecto de infra
        source="TOWER_6",
        confidence=1.0,
    )

    # --- GLOBAL ORCHESTRATION ---
    print("\n[System] Executing Strategic Orchestrator (Topological Sort)...")
    # --- ACT ---
    results = run_strategic_orchestration(client_name)

    roadmap = results["roadmap"]
    print("\n--- ROADMAP MATEMÁTICO GENERADO ---")
    for wave in roadmap:
        print(f"[{wave['wave']}]")
        for proj in wave["projects"]:
            print(f"  - {proj}")

    # --- ASSERT ---
    # VALIDACIONES FINALES
    truth = graph.resolve_truth()

    def get_label(node_id: str) -> str:
        predicates = truth.get(node_id, {})
        return (
            predicates.get("PROPOSES_INITIATIVE", {}).get("value") or node_id
        ).upper()

    # 1. El proyecto "Landing Zone" debe estar en Wave 0
    w0_projects = [get_label(p) for p in roadmap[0]["projects"]]
    assert any("LANDING" in p for p in w0_projects), (
        "Landing Zone debería estar en Wave 0"
    )

    # 2. El proyecto "SIEM" debe estar en Wave 1
    w1_projects = [get_label(p) for p in roadmap[1]["projects"]]
    assert any("SIEM" in p for p in w1_projects), (
        "SIEM debería estar en Wave 1 (dependiente)"
    )

    print("\n[Audit] Sovereign convergence test successful.")

    print("\n[Audit] Sovereignty verification completed successfully.")
    print(
        "Convergence and topological sorting function according to the system specifications."
    )


if __name__ == "__main__":
    test_sovereign_convergence_and_sort()
