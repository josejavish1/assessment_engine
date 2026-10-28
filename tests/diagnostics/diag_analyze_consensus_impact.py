#!/usr/bin/env python3
import os
from pathlib import Path
import re

def main():
    root_dir = Path("working/redeia_v3")
    towers = ["T2", "T4", "T5", "T6", "T7", "T8", "T10"]
    
    print("=======================================================================")
    print(" 📊 ANÁLISIS DE REDUCCIÓN DE RIESGOS (CONSENSO ADVERSARIAL)")
    print("=======================================================================\n")
    
    global_tef_reductions = []
    global_lm_reductions = []
    global_slef_reductions = []

    for t in towers:
        log_file = root_dir / t / "adversarial_consensus_transcript.log"
        if not log_file.exists():
            continue
            
        content = log_file.read_text(encoding="utf-8")
        
        # Count total debates
        debates = content.count("DEBATE COMPLETO PARA CAPACIDAD:")
        if debates == 0:
            continue
            
        print(f"--- TORRE {t} ---")
        print(f"Riesgos debatidos (Tier 1 y 2): {debates}")
        
        # Find all TEF and LM modifications
        tef_mods = re.findall(r"- TEF Mod:\s*([0-9.]+)", content)
        lm_mods = re.findall(r"- LM Mod:\s*([0-9.]+)", content)
        fines_mods = re.findall(r"- Fines Mod:\s*([0-9.]+)", content)
        
        # Calculate average reductions
        if tef_mods:
            avg_tef = sum(float(m) for m in tef_mods) / len(tef_mods)
            global_tef_reductions.extend([float(m) for m in tef_mods])
            print(f"  * Frecuencia (TEF) reducida en un: {(1 - avg_tef) * 100:.0f}% en promedio")
            
        if lm_mods:
            avg_lm = sum(float(m) for m in lm_mods) / len(lm_mods)
            global_lm_reductions.extend([float(m) for m in lm_mods])
            print(f"  * Severidad (LM) reducida en un: {(1 - avg_lm) * 100:.0f}% en promedio")

        if fines_mods:
            avg_fines = sum(float(m) for m in fines_mods) / len(fines_mods)
            global_slef_reductions.extend([float(m) for m in fines_mods])
            print(f"  * Multas (SLEF) reducidas en un: {(1 - avg_fines) * 100:.0f}% en promedio")
            
        print("")

    print("=======================================================================")
    print(" 📈 RESUMEN GLOBAL (Impacto del CFO Escéptico)")
    print("=======================================================================")
    if global_tef_reductions:
        g_tef = sum(global_tef_reductions) / len(global_tef_reductions)
        print(f"Impacto en Frecuencia: Ataques mitigados un {(1 - g_tef) * 100:.0f}% globalmente.")
    if global_lm_reductions:
        g_lm = sum(global_lm_reductions) / len(global_lm_reductions)
        print(f"Impacto en Severidad: Daño directo rebajado un {(1 - g_lm) * 100:.0f}% globalmente.")
    if global_slef_reductions:
        g_slef = sum(global_slef_reductions) / len(global_slef_reductions)
        print(f"Impacto en Multas: Exposición regulatoria reducida un {(1 - g_slef) * 100:.0f}% globalmente.")

if __name__ == "__main__":
    main()
