import json
from pathlib import Path


def audit_t4():
    payload_path = Path("working/redeia_v3/T4/blueprint_t4_payload.json")
    if not payload_path.exists():
        print(f"Error: {payload_path} no existe")
        return

    with open(payload_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    print("=====================================================================")
    print("🔍 AUDITORÍA ARQUITECTÓNICA - TORRE 4 (DATA SERVICES & STORAGE)")
    print("=====================================================================\n")

    # 1. Metadatos
    meta = data.get("document_meta", {})
    print("📋 METADATOS DEL DOCUMENTO:")
    print(f"   - Cliente: {meta.get('client_name')}")
    print(f"   - Torre: {meta.get('tower_name')} ({meta.get('tower_code')})")
    print(f"   - Horizonte: {meta.get('transformation_horizon')}")
    print()

    # 2. Resumen Ejecutivo (Executive Snapshot)
    snapshot = data.get("executive_snapshot", {})
    print("📌 SNAPSHOT EJECUTIVO:")
    print(f"   - bottom_line: {snapshot.get('bottom_line')[:500]}...")
    print(f"   - cost_of_inaction: {snapshot.get('cost_of_inaction')[:300]}...")
    print(f"   - decisions: {snapshot.get('decisions')}")
    print(f"   - structural_risks: {snapshot.get('structural_risks')}")
    print()

    # 3. Análisis de Pilares (Pillars Analysis)
    print("⚡ ANÁLISIS DE PILARES Y TECNOLOGÍAS ASOCIADAS:")
    pillars = data.get("pillars_analysis", [])
    for idx, pillar in enumerate(pillars, 1):
        p_id = pillar.get("pilar_id", "N/A")
        p_name = pillar.get("pilar_name", "N/A")
        score = pillar.get("score", "N/A")
        target_score = pillar.get("target_score", "N/A")
        print(
            f"\n   Pilar {idx}: {p_name} ({p_id}) | Score: {score} -> Target: {target_score}"
        )

        # Target Architecture Vision
        vision = pillar.get("target_architecture_tobe", {}).get("vision", "N/A")
        print(f"      ├─ Visión To-Be: {vision[:400]}...")

        # Projects proposed
        projects = pillar.get("projects_todo", [])
        print(f"      └─ Proyectos To-Do ({len(projects)}):")
        for proj in projects:
            print(
                f"         • {proj.get('name')} (Sizing: {proj.get('sizing')} | Duración: {proj.get('duration')})"
            )
            print(f"           - Objetivo: {proj.get('tech_objective')[:180]}...")

    # 4. Roadmap waves consistency
    print("\n🗺️ CONSISTENCIA DEL ROADMAP DE TRANSFORMACIÓN:")
    roadmap = data.get("roadmap", [])
    for wave in roadmap:
        print(f"   ├─ Wave: {wave.get('wave')}")
        print(f"   └─ Proyectos asignados: {wave.get('projects')}")


if __name__ == "__main__":
    audit_t4()
