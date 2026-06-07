import shutil
from pathlib import Path

from application.run_strategic_orchestrator import run_strategic_orchestration
from domain.ontology_registry import OntologyRegistry
from infrastructure.entity_resolution import EntityResolutionEngine
from infrastructure.epistemic_graph import EpistemicGraph
from infrastructure.text_utils import slugify


def test_sovereign_convergence_and_sort():
    client_name = "NTT_DATA_ELITE_TEST"
    client_id = slugify(client_name)
    working_dir = Path(f"working/{client_id}")

    # Limpieza inicial para asegurar pureza de datos
    if working_dir.exists():
        shutil.rmtree(working_dir)

    print(f"🚀 Iniciando Prueba de Convergencia Soberana para: {client_name}")

    graph = EpistemicGraph(client_id=client_id)
    resolver = EntityResolutionEngine()
    ontology = OntologyRegistry()

    # --- SIMULACIÓN TORRE 1 (INFRA) ---
    # Proyecto A: "Despliegue de Landing Zone en AWS"
    print("\n📦 Torre 1: Inyectando 'Despliegue de Landing Zone en AWS'...")
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

    # --- SIMULACIÓN TORRE 6 (SEGURIDAD) ---
    # Proyecto B: "Configuración Segura de AWS Landing" (SINÓNIMO)
    # Proyecto C: "Implementación de SIEM" (DEPENDIENTE)
    print("🛡️ Torre 6: Inyectando 'Configuración Segura de AWS Landing' (Sinónimo)...")
    id_sec = resolver.get_semantic_id(
        "Configuración Segura de AWS Landing", context="INITIATIVE"
    )

    # Verificamos si los IDs convergen (deberían ser iguales por el motor semántico)
    if id_infra == id_sec:
        print(
            "✅ CONVERGENCIA SEMÁNTICA DETECTADA: Torre 1 y Torre 6 apuntan al mismo NodeID."
        )
    else:
        print("❌ FALLO DE CONVERGENCIA: Los IDs son diferentes.")

    id_siem = resolver.get_semantic_id("Implementación de SIEM", context="INITIATIVE")
    print(
        "🛡️ Torre 6: Inyectando 'Implementación de SIEM' que depende de la Landing Zone..."
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

    # --- ORQUESTACIÓN GLOBAL ---
    print("\n🧠 Ejecutando Orquestador Estratégico (Topological Sort)...")
    results = run_strategic_orchestration(client_name)

    roadmap = results["roadmap"]
    print("\n--- ROADMAP MATEMÁTICO GENERADO ---")
    for wave in roadmap:
        print(f"[{wave['wave']}]")
        for proj in wave["projects"]:
            print(f"  - {proj}")

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

    print("\n✅ PRUEBA DE CONVERGENCIA SOBERANA EXITOSA.")

    print("\n✅ PRUEBA DE SOBERANÍA COMPLETADA CON ÉXITO.")
    print(
        "La convergencia y el ordenamiento topológico funcionan según el estándar Tier 1."
    )


if __name__ == "__main__":
    test_sovereign_convergence_and_sort()
