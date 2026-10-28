#!/usr/bin/env python3
import json
from pathlib import Path

def main():
    root_dir = Path("working/redeia_v3")
    towers = ["T2", "T4", "T5", "T6", "T7", "T8", "T10"]
    
    print("=======================================================================")
    print(" 📊 VERIFICACIÓN DE RANKING DE RIESGOS POST-CONSENSO")
    print("=======================================================================\n")
    
    for t in towers:
        blueprint_file = root_dir / t / f"blueprint_{t.lower()}_payload.json"
        if not blueprint_file.exists():
            continue
            
        with open(blueprint_file, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            
        all_risks = []
        for pillar in data.get("pillars_analysis", []):
            for hc in pillar.get("health_check_asis", []):
                tef = hc.get("threat_event_frequency", 0)
                lm = hc.get("loss_magnitude", 0)
                ale = hc.get("fair_ale_score", 0.0)
                
                # Check if it was debated
                debated = "_consensus_tef_mod" in hc
                
                all_risks.append({
                    "id": hc.get("node_id", "UNK"),
                    "capability": hc.get("capability", "UNK"),
                    "tef": tef,
                    "lm": lm,
                    "ale": ale,
                    "debated": debated
                })
                
        # Sort by ALE descending
        all_risks.sort(key=lambda x: x["ale"], reverse=True)
        
        print(f"--- TORRE {t} ---")
        for i, r in enumerate(all_risks[:5], 1):
            status = "🤖 DEBATIDO" if r["debated"] else "⚪ OMITIDO (Tier 3)"
            print(f"  {i}. [{status}] {r['capability'][:50]}... | ALE: {r['ale']:,.2f} € | TEF:{r['tef']} LM:{r['lm']}")
            
        # Find the highest non-debated risk
        highest_omitted = next((r for r in all_risks if not r["debated"]), None)
        if highest_omitted:
            print(f"  -> Mayor riesgo omitido: {highest_omitted['capability'][:40]}... | ALE: {highest_omitted['ale']:,.2f} €")
        else:
            print("  -> Todos los riesgos fueron debatidos.")
        print("")

if __name__ == "__main__":
    main()
