import json
from pathlib import Path

def run_deep_t2_audit():
    p = Path("working/redeia_v3/T2/blueprint_t2_payload.json")
    if not p.exists():
        print("❌ Error: T2 payload no encontrado.")
        return
        
    with open(p, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
        
    print("=====================================================================")
    print("🔍 AUDITORÍA FORENSE Y REVISIÓN CRÍTICA EXCLUSIVA DE LA TORRE 2")
    print("=====================================================================\n")
    
    exec_snap = data.get("executive_snapshot", {})
    print("💎 2. CRÍTICA DEL MENSAJE EJECUTIVO (SNAPSHOT):")
    print(f"   ├─ Bottom Line: \"{exec_snap.get('bottom_line')}\"")
    print(f"   ├─ Cost of Inaction (Coste de Inacción): \"{exec_snap.get('cost_of_inaction')}\"")
    print()
    
    pillars = data.get("pillars_analysis", [])
    
    pillars_summary = {}
    for p_idx, pilar in enumerate(pillars, 1):
        p_id = pilar.get("pilar_id")
        p_name = pilar.get("pilar_name")
        vision = pilar.get("target_architecture_tobe", {}).get("vision", "")
        projs = pilar.get("projects_todo", [])
        
        pillars_summary[p_id] = {
            "name": p_name,
            "vision": vision,
            "projects": projs,
        }
        
        print(f"   📡 Pilar {p_id} - {p_name}:")
        print(f"      ├─ Visión To-Be: \"{vision[:220]}...\"")
        print(f"      └─ Proyectos Técnicos ({len(projs)}):")
        for proj in projs:
            print(f"         • Proyecto: {proj.get('name')} | Duración: {proj.get('duration')} | Sizing: {proj.get('sizing')}")
            print(f"           └─ Objetivo Técnico: \"{proj.get('tech_objective')}\"")
            print(f"           └─ Deliverables: {proj.get('deliverables')}")
        print()

if __name__ == "__main__":
    run_deep_t2_audit()
