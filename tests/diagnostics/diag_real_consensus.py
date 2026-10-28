#!/usr/bin/env python3
import asyncio
import json
import os
import copy
from pathlib import Path
from assessment_engine.application.tools.adversarial_consensus_engine import AdversarialConsensusEngine
from assessment_engine.infrastructure.policy_engine import SovereignPolicyEngine
from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph

async def main():
    print("=====================================================================")
    print(" 🧪 TEST END-TO-END DE CONSENSO ADVERSARIAL (RIESGO REAL REDEIA)")
    print("=====================================================================")
    
    # Load real T6 blueprint
    blueprint_path = Path("working/legacy/redeia_v3_backup_old/T6/blueprint_t6_payload.json")
    with open(blueprint_path, "r", encoding="utf-8-sig") as f:
        payload = json.load(f)
        
    # Find the highest ALE risk
    max_ale = -1
    target_p_idx = -1
    target_h_idx = -1
    for p_idx, pillar in enumerate(payload.get("pillars_analysis", [])):
        for h_idx, hc in enumerate(pillar.get("health_check_asis", [])):
            ale = hc.get("fair_ale_score", 0)
            if ale > max_ale:
                max_ale = ale
                target_p_idx = p_idx
                target_h_idx = h_idx
                
    risk_base = payload["pillars_analysis"][target_p_idx]["health_check_asis"][target_h_idx]
    
    print(f"Riesgo Real Seleccionado: {risk_base.get('capability')}")
    print(f"Vulnerabilidad: {risk_base.get('finding')}")
    print(f"\n--- 1. RESULTADOS BASE (Sin Consenso) ---")
    print(f"ALE: {risk_base.get('fair_ale_score', 0):,} €")
    print(f"P90: {risk_base.get('fair_p90_score', 0):,} €")
    print(f"P99 (Max): {risk_base.get('fair_max_score', 0):,} €")
    
    # Isolate payload to just this risk to speed up
    payload_isolated = copy.deepcopy(payload)
    for p_idx, pillar in enumerate(payload_isolated.get("pillars_analysis", [])):
        if p_idx == target_p_idx:
            pillar["health_check_asis"] = [pillar["health_check_asis"][target_h_idx]]
        else:
            pillar["health_check_asis"] = []
            
    os.environ["ASSESSMENT_CLIENT_ID"] = "redeia_v3"
    os.environ["ASSESSMENT_INDUSTRY"] = "Critical Infrastructure"
    
    print("\n--- 2. INICIANDO DEBATE ADVERSARIAL (5 Iteraciones) ---")
    consensus_engine = AdversarialConsensusEngine(env={})
    payload_consensus = await consensus_engine.process_payload("T6_TEST", payload_isolated)
    
    risk_cons = payload_consensus["pillars_analysis"][target_p_idx]["health_check_asis"][0]
    print("\n--- 3. MODIFICADORES EXTRAÍDOS POR LA IA ---")
    print(f"TEF Mod: {risk_cons.get('_consensus_tef_mod')}")
    print(f"LM Mod:  {risk_cons.get('_consensus_lm_mod')}")
    print(f"Fines Mod: {risk_cons.get('_consensus_slef_mod')}")
    print(f"Justificación:\n{risk_cons.get('_consensus_justification')}")
    
    print("\n--- 4. TRANSCRITO COMPLETO DEL DEBATE ---")
    transcript_file = Path("working/redeia_v3/T6_TEST/adversarial_consensus_transcript.log")
    if transcript_file.exists():
        with open(transcript_file, "r", encoding="utf-8") as f:
            print(f.read())
            
    # Calculate new risk
    graph = EpistemicGraph(client_id="redeia_v3")
    engine_final = SovereignPolicyEngine(graph)
    result_final = engine_final.compile(payload_consensus)
    risk_final = result_final["pillars_analysis"][target_p_idx]["health_check_asis"][0]
    
    print("\n--- 5. RESULTADOS FINALES (Con Consenso + Políticas Actuariales) ---")
    print(f"ALE: {risk_final.get('fair_ale_score', 0):,} €")
    print(f"P90: {risk_final.get('fair_p90_score', 0):,} €")
    print(f"P99 (Max): {risk_final.get('fair_max_score', 0):,} €")
    print("=====================================================================")

if __name__ == "__main__":
    asyncio.run(main())