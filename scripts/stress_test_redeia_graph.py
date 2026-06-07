from infrastructure.entity_resolution import EntityResolutionEngine
from infrastructure.epistemic_graph import EpistemicGraph
from infrastructure.text_utils import slugify


def inject_dependency():
    client_name = "redeia"
    graph = EpistemicGraph(client_id=slugify(client_name))
    resolver = EntityResolutionEngine()

    # 1. Resolve IDs for the two projects
    proj_a_name = "Project 1: Plataforma Fundacional de AIOps sobre Azure"
    proj_b_name = "Iniciativa GÉNESIS: Fundación de Persistencia para Kubernetes"

    id_a = resolver.get_semantic_id(proj_a_name, context="INITIATIVE")
    id_b = resolver.get_semantic_id(proj_b_name, context="INITIATIVE")

    print(f"Injecting dependency: {proj_a_name} -> REQUIRES -> {proj_b_name}")
    print(f"IDs: {id_a} -> {id_b}")

    graph.inject_triple(
        subject=id_a,
        predicate="REQUIRES_PREREQUISITE",
        object_val=id_b,
        source="MANUAL_STRESS_TEST",
        confidence=1.0,
        reason="AIOps requires persistent storage foundation.",
    )

    print("✅ Dependency injected into Redeia ledger.")


if __name__ == "__main__":
    inject_dependency()
