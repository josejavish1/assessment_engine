#!/usr/bin/env python3
import asyncio
import json
import os
from pprint import pprint
from assessment_engine.application.tools.adversarial_consensus_engine import AdversarialConsensusEngine
from assessment_engine.infrastructure.policy_engine import SovereignPolicyEngine
from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph

async def main():
    print("=====================================================================")
    print(" 🧪 TEST END-TO-END DE CONSENSO ADVERSARIAL (UN SOLO RIESGO)")
    print("=====================================================================")
    
    # 1. Setup Mock Payload for T4 Storage Provisioning (Friction Risk)
    finding_text = (
        "El aprovisionamiento de almacenamiento es un proceso manual basado en tickets (ITSM). "
        "No existe un portal de autoservicio para los desarrolladores, lo que genera retrasos "
        "de hasta 4 días en la asignación de recursos y ralentiza el time-to-market."
    )
    
    payload = {
        "document_meta": {
            "client_name": "REDEIA",
            "tower_code": "T4",
            "tower_name": "Storage & Data Platforms"
        },
        "pillars_analysis": [
            {
                "pilar_id": "T4.P1",
                "pilar_name": "Storage Foundation",
                "score": 2.0,
                "health_check_asis": [
                    {
                        "node_id": "R-TEST-01",
                        "capability": "Aprovisionamiento y Autoservicio",
                        "finding": finding_text,
                        "impact": "Retrasos operativos y frustración del usuario.",
                        "loss_magnitude": 4,
                        "threat_event_frequency": 4
                    }
                ],
                "projects_todo": []
            }
        ]
    }
    
    # Set mock environment
    os.environ["ASSESSMENT_CLIENT_ID"] = "test_client"
    os.environ["ASSESSMENT_INDUSTRY"] = "Critical Infrastructure"
    
    # 2. Run Base Policy Engine (Without Consensus) to see initial inflated numbers
    print("\n--- 1. RESULTADOS BASE (Sin Consenso Adversarial) ---")
    graph = EpistemicGraph(client_id="test_client")
    engine_base = SovereignPolicyEngine(graph)
    
    # We must deep copy payload because policy engine modifies in-place
    import copy
    payload_base = copy.deepcopy(payload)
    result_base = engine_base.compile(payload_base)
    risk_base = result_base["pillars_analysis"][0]["health_check_asis"][0]
    
    print(f"ALE: {risk_base.get('fair_ale_score', 0):,} €")
    print(f"P90: {risk_base.get('fair_p90_score', 0):,} €")
    print(f"P99 (Max): {risk_base.get('fair_max_score', 0):,} €")
    
    
    # 3. Run Adversarial Consensus Engine
    print("\n--- 2. INICIANDO DEBATE ADVERSARIAL (5 Iteraciones) ---")
    env = {}
    consensus_engine = AdversarialConsensusEngine(env=env)
    
    payload_consensus = copy.deepcopy(payload)
    payload_consensus = await consensus_engine.process_payload("T4", payload_consensus)
    
    risk_cons = payload_consensus["pillars_analysis"][0]["health_check_asis"][0]
    print("\n--- 3. MODIFICADORES EXTRAÍDOS POR LA IA ---")
    print(f"TEF Mod: {risk_cons.get('_consensus_tef_mod')}")
    print(f"LM Mod:  {risk_cons.get('_consensus_lm_mod')}")
    print(f"Fines Mod: {risk_cons.get('_consensus_slef_mod')}")
    print(f"Justificación:\n{risk_cons.get('_consensus_justification')}")
    
    # 4. Run Policy Engine on Consensused Payload
    print("\n--- 4. RESULTADOS FINALES (Con Consenso + Políticas Actuariales) ---")
    engine_final = SovereignPolicyEngine(graph)
    result_final = engine_final.compile(payload_consensus)
    risk_final = result_final["pillars_analysis"][0]["health_check_asis"][0]
    
    print(f"ALE: {risk_final.get('fair_ale_score', 0):,} €")
    print(f"P90: {risk_final.get('fair_p90_score', 0):,} €")
    print(f"P99 (Max): {risk_final.get('fair_max_score', 0):,} €")
    print("=====================================================================")

if __name__ == "__main__":
    asyncio.run(main())