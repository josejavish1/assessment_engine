#!/usr/bin/env python3
"""
Elevates Molins Technical Deliverables to Top-Tier Strategic Consulting Standards (NTT DATA Standard).

Core Mandates:
1. Executive Consulting Tone: Eradicates all accusatory, aggressive, or alarming words
   ('caos operativo', 'negligencia', 'fallo flagrante', 'robo', 'sabotaje').
2. Pure Empirical Truth (Zero Brand Hallucinations): Purges all non-verified hardware brands
   (Riello, SDMO, Stulz, FM-200, VESDA, MOXA) while preserving real factual assets
   (HPE SimpliVity 6 nodes, NetApp SnapMirror, Cohesity DataPlatform, Oracle 10g/11g,
   CentOS 6, Prenet, NOS Portugal, 500m distance).
3. SSOT Score Alignment: Preserves authoritative survey scores from 261014 Respuestas Test Molins.txt
   (T1=2.61, T2=1.89, T3=2.56, T4=3.26, T5=2.20, T6=2.82, T7=2.43, T8=2.45, T9=3.19, T10=2.40).
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

REPLACEMENTS_DICT = {
    # Accusatory / Alarming words -> Strategic Consulting phrasing
    r"\bcaos operativo\b": "dilatación en los tiempos de respuesta e inconsistencia procedimental",
    r"\bCaos operativo\b": "Dilatación en los tiempos de respuesta e inconsistencia procedimental",
    r"\bnegligencia\b": "deuda operativa pendiente de formalización",
    r"\bNegligencia\b": "Deuda operativa pendiente de formalización",
    r"\bflagrante\b": "relevante",
    r"\bFlagrante\b": "Relevante",
    r"\bsabotaje\b": "manipulación inadvertida o no autorizada",
    r"\bSabotaje\b": "Manipulación inadvertida o no autorizada",
    r"\brobo\b": "acceso físico no controlado",
    r"\bRobo\b": "Acceso físico no controlado",
    r"\bcolapso catastrófico\b": "interrupción mayor no programada",
    r"\bColapso catastrófico\b": "Interrupción mayor no programada",
    r"\bdestrucción irreversible\b": "compromiso severo de la disponibilidad",
    r"\bDestrucción irreversible\b": "Compromiso severo de la disponibilidad",
    r"\bchapuza\b": "práctica operativa no estandarizada",
    r"\babsurdo\b": "desalineado con las mejores prácticas",

    # Vendor Brand Neutralization (Zero Hallucination Invariant)
    r"Riello Multi Sentry": "SAI/UPS modular de doble conversión",
    r"Riello": "SAI/UPS",
    r"SDMO": "Grupo electrógeno de emergencia",
    r"Stulz CyberAir 3": "Climatizadora de precisión de expansión directa (DX)",
    r"Stulz": "Climatizadora de precisión",
    r"FM-200 \(HFC-227ea\)": "Agente limpio gaseoso de extinción",
    r"FM-200": "Agente limpio gaseoso",
    r"Xtralis VESDA": "Detección precoz por aspiración láser",
    r"VESDA": "Detección precoz por aspiración",
    r"MOXA NPort": "Conversores industriales serie-Ethernet",
    r"MOXA": "Conversores industriales serie",
}

def sanitize_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    for pattern, repl in REPLACEMENTS_DICT.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text

def sanitize_dict(d):
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, str):
                d[k] = sanitize_text(v)
            elif isinstance(v, (dict, list)):
                sanitize_dict(v)
    elif isinstance(d, list):
        for item in d:
            if isinstance(item, (dict, list)):
                sanitize_dict(item)

def main():
    print("=" * 80)
    print("PURGING BRAND HALLUCINATIONS AND ELEVATING CONSULTING TONE ACROSS ALL BLUEPRINTS")
    print("=" * 80)

    for code in [f"T{i}" for i in range(1, 11)]:
        p = REPO_ROOT / f"working/molins/{code}/blueprint_{code.lower()}_payload.json"
        if p.exists():
            with open(p, "r", encoding="utf-8-sig") as f:
                d = json.load(f)
            sanitize_dict(d)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2, ensure_ascii=False)
            print(f"✓ Sanitized {code} blueprint payload (Zero brand hallucinations, consulting tone).")

if __name__ == "__main__":
    main()
