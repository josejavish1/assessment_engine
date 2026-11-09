#!/usr/bin/env python3
"""Deep Forensic Section-by-Section Audit of Tower 2 (Hybrid Compute & Platforms).

Simulates:
1. Tough Client CTO (battle-tested, defensive, checks operational fidelity and calls out fluff/hallucinations).
2. Tier-1 Global Virtualization Fellow (grounded in SOTA 2026 papers, hypervisor internals, and NIST/IEEE/DORA standards).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from docx import Document

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

doc_path = REPO_ROOT / "working/out/Molins_Entrega_Oficial_Piramide_Tier1/02_ANEXOS_TECNICOS_ESPECIALISTAS/Molins_202610_Anexo_02_Computo_Hibrido_ASIS.docx"
doc = Document(str(doc_path))

# Extract sections cleanly
sections = {}
current_sec = "Header"
sections[current_sec] = []

for p in doc.paragraphs:
    txt = p.text.strip()
    if not txt:
        continue
    if p.style.name.startswith("Heading 1"):
        current_sec = txt
        sections[current_sec] = []
    elif p.style.name.startswith("Heading 2"):
        sections[current_sec].append(f"### {txt}")
    elif p.style.name.startswith("Heading 3"):
        sections[current_sec].append(f"#### {txt}")
    else:
        sections[current_sec].append(txt)

for t in doc.tables:
    table_rows = []
    for row in t.rows:
        row_txt = " | ".join(cell.text.strip().replace("\n", " ") for cell in row.cells)
        table_rows.append(f"| {row_txt} |")
    if current_sec in sections:
        sections[current_sec].append("\n".join(table_rows[:8]))

# Combine sections into 4 major blocks for the deep audit
sec_text_combined = "\n\n".join(f"== SECTION: {k} ==\n" + "\n".join(v[:25]) for k, v in sections.items() if len(v) > 0)

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)
print(f"Connecting to reasoning model: {model_name}...")

prompt = f"""You are 'gemini-4-argon', the Principal Staff Systems Architect, Kernel & Hypervisor Fellow, and Master Forensic Auditor.

TASK:
Perform a relentless, section-by-section, dual-persona forensic audit of the official deliverable for Tower 2:
'Molins - Anexo 02: Cómputo Híbrido y Virtualización (AS-IS)'.

THE DELIVERABLE EXTRACTS (TOWER 2):
\"\"\"
{sec_text_combined}
\"\"\"

CONTEXT OF THE CLIENT:
Molins is an international heavy building materials and cement conglomerate ($1.144B revenue).
Spain operations are centered in Sant Vicenç dels Horts (two datacenters 500m apart on-premise, 6 HPE SimpliVity nodes from 2018 running VMware vSphere, NetApp MetroCluster, Oracle 10g/11g Forms, legacy batching plants and weighbridges).
Portugal operations (SECIL) are fully outsourced to telecom operator NOS in Lisbon.

YOUR AUDIT MUST PROVIDE A RIGOROUS SECTION-BY-SECTION ANALYSIS FROM TWO PARALLEL PERSPECTIVES:

### PERSPECTIVE 1: THE TOUGH CLIENT CTO (DEEP OPERATIONAL GROUNDING)
- He knows every rack, every cable, and every flaw in his datacenter.
- He evaluates whether the document tells the brutal truth about his reality or if it hallucinates tools they don't have.
- Does it capture the real headache of the Broadcom renewal, the SimpliVity memory exhaustion, the CentOS legacy machines, the 5-person team, and the Croatian DBA?
- Where is the consultant fluff, buzzwords, or unrealistic advice?

### PERSPECTIVE 2: THE SOTA COMPUTE & VIRTUALIZATION FELLOW (ACADEMIC & TECHNICAL PURITY)
- Evaluates against the state of the art in 2026.
- Cites specific papers, engineering internals, and industry standards:
  * VMware Admission Control & HA failure domain mathematics (e.g. Percentage-based vs Slot vs Dedicated Host policies).
  * Hyperconverged Infrastructure (HCI) failure modes: OVC (OmniStack Virtual Controller) memory ballooning, vSAN/SimpliVity metadata locks, storage controller starve-out.
  * Open FAIR (Factor Analysis of Information Risk) actuarial loss modeling (LEF, SLE, ALE, P90 VaR).
  * Linux cgroups v2, NUMA node binding, hypervisor memory overcommit hazards.
  * Modernization reality: Strangler Fig pattern vs Big Bang ERP re-writes, containerization limits for stateful legacy workloads.

STRUCTURE YOUR RESPONSE CLEARLY:
1. EXECUTIVE DIAGNOSIS (Overall Grade: A-F, Hallucination Index, Antipattern Count)
2. SECTION 1 AUDIT: RESUMEN EJECUTIVO Y ALCANCE
3. SECTION 2 AUDIT: DIAGNÓSTICO TÉCNICO Y CUADRO DE MANDO (P1-P5)
4. SECTION 3 AUDIT: ANÁLISIS DE DEUDA TÉCNICA Y PATRONES DE RIESGO
5. SECTION 4 AUDIT: EVALUACIÓN ECONÓMICA FAIR Y ESCENARIO P90
6. CONSOLIDATED ANTIPATTERN & DEFECT LEDGER (Specific flaws, missing nuances, and exact fixes)

Tone: Technical English, razor-sharp, forensic, unsparing.
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON SECTION-BY-SECTION AUDIT: TOWER 2")
print("=" * 80)
print(response.text)

out_file = REPO_ROOT / "docs/audits/ARGON_DEEP_SECTION_BY_SECTION_AUDIT_TOWER2.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\n✓ Saved report to {out_file.relative_to(REPO_ROOT)}")
