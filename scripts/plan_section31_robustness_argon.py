#!/usr/bin/env python3
"""Consult gemini-4-argon on deep root-cause analysis and robust 10/10 architecture for Section 3.1."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

OUTPUT_FILE = REPO_ROOT / "docs/architecture/ARGON_SECTION31_SEMANTIC_INTEGRITY_PLAN.md"

COMPILER_EXCERPT = (
    REPO_ROOT / "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py"
).read_text(encoding="utf-8")[155:230]

T1_P4_PAYLOAD = """
Pillar: T1.P4 Protección Contra Incendios y Seguridad Ambiental (Score: 4.0 / 5.0)
Actual Tower Definition KPIs for T1.P4:
  - T1.P4.K1: Detección temprana y cobertura (humo/temperatura) por zonas críticas (Client score: 5/5)
  - T1.P4.K2: Sistema de supresión/extinción adecuado y mantenido (gas limpio) (Client score: 5/5)
  - T1.P4.K3: Gestión de riesgos ambientales asociados (fugas de agua, alarmas) (Client score: 2/5)

What the LLM generated in T1.P4 health_check_asis[0]:
  Capability: Capacidad de Absorción ante Siniestro Físico de una Sala (Regla del 50%)
  Finding: Superación del límite de seguridad del 50% de ocupación de recursos físicos (especialmente memoria RAM y CPU en los clústeres 3 y 4) en los 6 nodos HPE SimpliVity repartidos entre el CPD A y el CPD B.

What Section 3.1 (Table 5) rendered in the Word deliverable:
  Pilar: Protección Contra Incendios y Seguridad Ambiental | Score: 4,00 (Gestionado)
  Justificación:
    • Fortaleza Operativa Identificada: La mitigación de riesgos catastróficos descansa en la segregación física en dos edificaciones a 500m...
    • Brecha de Resiliencia Diagnosticada: Superación del límite de seguridad del 50% de ocupación de recursos físicos (especialmente memoria RAM y CPU en los clústeres 3 y 4) en los 6 nodos HPE SimpliVity.
"""

PROMPT = f"""You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect, Enterprise Ontologist, and Chief Quality Gatekeeper.

USER PROBLEM STATEMENT:
In Section 3.1 of the generated tower deliverables (Table 5 in Technical Annexes: "Pilar / Capacidad | Score | Análisis de Brechas y Calibración"), the user noticed an absurd semantic dissonance:
Under "Protección Contra Incendios y Seguridad Ambiental" (Fire Protection & Environmental Safety, scored at 4.0/5.0), the table states:
"Brecha de Resiliencia Diagnosticada: Superación del límite de seguridad del 50% de ocupación de recursos físicos (especialmente memoria RAM y CPU en los clústeres 3 y 4) en los 6 nodos HPE SimpliVity."

The user rightly objected: "What on earth does RAM/CPU resource saturation in SimpliVity have to do with Fire Protection and Environmental Safety?!"

FORENSIC CODE CONTEXT:
1. In `engine_config/towers/T1/tower_definition_T1.json`, T1.P4 is strictly defined by three electromechanical/safety KPIs:
   - K1: Smoke/temperature early detection (VESDA)
   - K2: Clean-agent gas fire suppression system
   - K3: Associated environmental risks (water leaks, condensation, BMS alarms)
   The client scored 5, 5, 2 (weighted mean = 4.00). The gap in K3 is lack of water leak sensors under the raised floor and isolated fire alarms!
2. In `scripts/resynthesize_all_10_towers_from_raw_transcription.py`, the LLM was asked to generate `health_check_asis` from an unstructured interview transcript where the client talked extensively about SimpliVity RAM issues. With no semantic boundary enforcement per pillar, the LLM dumped SimpliVity RAM into Pillar 4!
3. In `in_memory_asis_compiler.py::derive_in_memory_maturity_matrix`:
```python
{COMPILER_EXCERPT}
```
The compiler naively grabbed `findings[0]` from the payload and concatenated it as the pillar's diagnosed breach!

YOUR TASK:
Provide an in-depth, authoritative, 10/10 architectural blueprint:
1. Deep Root-Cause Analysis of Cross-Pillar Contamination & Semantic Drift in Section 3.1.
2. Comprehensive Audit of all other 10 towers: Where else is this contamination happening (e.g. backup findings in networking, identity findings in workplace)?
3. Robust 10/10 Architectural Plan to eliminate semantic drift permanently:
   - Phase A: Ontological Pillar Scoping (How to strictly bind finding synthesis to the exact KPI definitions in `tower_definition.json`).
   - Phase B: Automated Semantic Boundary Gatekeeper (`PillarSemanticValidator` in `domain/validation/`) that inspects generated findings against pillar domain ontologies and rejects out-of-domain keywords (e.g. RAM/CPU keywords rejected under fire/cooling/electrical pillars).
   - Phase C: Declarative Compiler Alignment (`derive_in_memory_maturity_matrix` remediation to align strengths and gaps with the specific KPIs that caused high vs low scores).
4. Provide complete, production-grade Python code for the proposed components (100% Technical English, zero hardcoding, multi-tenant & vertical-agnostic).
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Executing Section 3.1 deep semantic audit with gemini-4-argon ({model})...")

    response = client.models.generate_content(
        model=model,
        contents=PROMPT,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"Audit report saved at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON SECTION 3.1 AUDIT & REMEDIATION PLAN SUMMARY:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
