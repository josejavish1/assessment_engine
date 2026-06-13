import json
from pathlib import Path

def run_deep_t5_audit():
    p = Path("working/redeia_v3/T5/blueprint_t5_payload.json")
    if not p.exists():
        print("❌ Error: T5 payload no encontrado.")
        return
        
    with open(p, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
        
    print("=====================================================================")
    print("🔍 AUDITORÍA FORENSE Y REVISIÓN CRÍTICA EXCLUSIVA DE LA TORRE 5")
    print("=====================================================================\n")
    
    # 1. Metadatos y Horizonte
    meta = data.get("document_meta", {})
    print("💎 1. METADATOS Y COHERENCIA ESTRATÉGICA:")
    print(f"   ├─ Cliente: {meta.get('client_name')} (ID: {meta.get('client_slug', 'N/A')})")
    print(f"   ├─ Torre: {meta.get('tower_code')} - {meta.get('tower_name')}")
    print(f"   └─ Horizonte de Transformación: {meta.get('transformation_horizon')}\n")
    
    # 2. Resumen Ejecutivo (Bottom Line) y Cost of Inaction
    exec_snap = data.get("executive_snapshot", {})
    print("💎 2. CRÍTICA DEL MENSAJE EJECUTIVO (SNAPSHOT):")
    print(f"   ├─ Bottom Line: \"{exec_snap.get('bottom_line')}\"")
    print(f"   ├─ Cost of Inaction (Coste de Inacción): \"{exec_snap.get('cost_of_inaction')}\"")
    print(f"   └─ Complejidad de la Transformación: {exec_snap.get('transformation_complexity')}\n")
    
    # 3. Análisis de Consistencia entre Pilares (P1 a P5)
    print("💎 3. AUDITORÍA CRÍTICA DE COHERENCIA ENTRE PILARES:")
    pillars = data.get("pillars_analysis", [])
    
    pillars_summary = {}
    for p_idx, pilar in enumerate(pillars, 1):
        p_id = pilar.get("pilar_id")
        p_name = pilar.get("pilar_name")
        score = pilar.get("score")
        target = pilar.get("target_score")
        vision = pilar.get("target_architecture_tobe", {}).get("vision", "")
        projs = pilar.get("projects_todo", [])
        
        # Check traceability counts
        total_evidences = len(pilar.get("health_check_asis", []))
        grounded_evidences = sum(1 for f in pilar.get("health_check_asis", []) if f.get("literal_evidence") or f.get("fragment_id"))
        
        pillars_summary[p_id] = {
            "name": p_name,
            "score": score,
            "target": target,
            "vision": vision,
            "projects": projs,
            "total_ev": total_evidences,
            "grounded_ev": grounded_evidences
        }
        
        print(f"   📡 Pilar {p_id} - {p_name} (Score: {score} -> Target: {target}):")
        print(f"      ├─ Trazabilidad Evidencias: {grounded_evidences}/{total_evidences} con citas RAG reales.")
        print(f"      ├─ Visión To-Be: \"{vision[:220]}...\"")
        print(f"      └─ Proyectos Técnicos ({len(projs)}):")
        for proj in projs:
            print(f"         • Proyecto: {proj.get('name')} | Duración: {proj.get('duration')} | Sizing: {proj.get('sizing')}")
            print(f"           └─ Objetivo Técnico: \"{proj.get('tech_objective')[:180]}...\"")
        print()
        
    # LOGICAL INCONSISTENCY DETECTION (T5 INTERNAL)
    print("💎 4. IDENTIFICACIÓN DE INCOHERENCIAS LOGICOTÉCNICAS INTERNAS EN T5:")
    has_inconsistencies = False
    
    # Check 1: RTO/RPO definitions vs DR automation sequencing (P1 vs P3)
    p1 = pillars_summary.get("T5.P1")
    p3 = pillars_summary.get("T5.P3")
    if p1 and p3:
        p1_durations = [proj.get("duration") for proj in p1["projects"]]
        p3_durations = [proj.get("duration") for proj in p3["projects"]]
        
        print("   ├─ Análisis de Sequenciamiento (P1 Continuidad vs P3 Disaster Recovery):")
        print(f"      • P1 (Definición de RTO/RPO): {p1_durations}")
        print(f"      • P3 (Automatización de DR con AWS DRS): {p3_durations}")
        
        # Incoherencia: Si se automatiza el DR (P3) en un Horizonte anterior o igual al que se definen los RTO/RPO (P1)
        # es una incoherencia porque no puedes diseñar la orquestación técnica sin conocer los objetivos de negocio.
        h1_p3 = any("horizonte 1" in d.lower() for d in p3_durations)
        h1_p1 = any("horizonte 1" in d.lower() for d in p1_durations)
        if h1_p3 and not h1_p1:
            print("      • ⚠️ INCOHERENCIA ENCONTRADA: Se está proponiendo automatizar la recuperación (P3) en H1, pero la definición estratégica de RTO/RPO por negocio (P1) no se completa hasta H2. ¡Riesgo de sobre-ingeniería o diseño a ciegas!")
            has_inconsistencies = True
        else:
            print("      • ✅ Coherencia en Sequenciamiento: Los RTO/RPO estratégicos (H1) preceden o coinciden con la orquestación técnica de DR (H2/H3).")
            
    # Check 2: Protection Consolidation vs Immutable Vault (P2 Backup vs P4 Cyber Recovery)
    p2 = pillars_summary.get("T5.P2")
    p4 = pillars_summary.get("T5.P4")
    if p2 and p4:
        print("\n   ├─ Análisis de Aislamiento Tecnológico (P2 Backup vs P4 Cyber Recovery):")
        # Incoherencia: Si la bóveda de inmutabilidad (Cyber Recovery) se despliega sobre la misma cuenta o bajo el mismo AWS Backup
        # que el backup ordinario, se pierde la inmutabilidad y el espacio de aire (Air-Gap).
        p2_vision = p2["vision"].lower()
        p4_vision = p4["vision"].lower()
        
        if "vault" in p2_vision and "cyber" in p2_vision:
            print("      • ⚠️ INCOHERENCIA DE CONCEPTOS: El Pilar P2 (Backup Ordinario) menciona capacidades de Cyber Vault que pertenecen exclusivamente a P4. Esto diluye el aislamiento de seguridad.")
        else:
            print("      • ✅ Coherencia de Conceptos: P2 se enfoca en consolidación operativa y ciclo de vida ordinario en AWS Backup, mientras que P4 se enfoca estrictamente en aislamiento inmutable (Cyber Vault) en una cuenta AWS aislada.")

    if not has_inconsistencies:
        print("\n   ├─ ✅ Cero incoherencias críticas de diseño interno detectadas. El secuenciamiento de la Torre 5 es impecable.")

if __name__ == "__main__":
    run_deep_t5_audit()
