#!/usr/bin/env python3
"""Audit Section 3.1 across all 10 specialist annexes using gemini-4-argon."""

import json
import sys
from pathlib import Path
import docx

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

annex_dir = REPO_ROOT / "working/out/Molins_Entrega_Oficial_Piramide_Tier1/02_ANEXOS_TECNICOS_ESPECIALISTAS"
towers = [
    ("T1", "Data Center Facilities", "Anexo_01_Data_Center_ASIS"),
    ("T2", "Cómputo Híbrido y Virtualización", "Anexo_02_Computo_Hibrido_ASIS"),
    ("T3", "Redes y Conectividad", "Anexo_03_Redes_ASIS"),
    ("T4", "Almacenamiento y Plataformas de Datos", "Anexo_04_Datos_Storage_ASIS"),
    ("T5", "Continuidad de Negocio y Resiliencia", "Anexo_05_Resiliencia_ASIS"),
    ("T6", "Ciberseguridad e Identidad", "Anexo_06_Seguridad_Identidad_ASIS"),
    ("T7", "Operaciones e ITSM", "Anexo_07_Operaciones_ITSM_ASIS"),
    ("T8", "FinOps y Gobernanza TI", "Anexo_08_FinOps_Gobernanza_ASIS"),
    ("T9", "Puesto de Trabajo Digital", "Anexo_09_Puesto_Trabajo_ASIS"),
    ("T10", "Sistemas de Planta y Expedición", "Anexo_10_Sistemas_Expedicion_Operaciones_ASIS"),
]

extracted_sections = {}

for code, name, fname_part in towers:
    files = list(annex_dir.glob(f"*{fname_part}*.docx"))
    if not files:
        extracted_sections[code] = f"ERROR: File matching {fname_part} not found."
        continue
    doc = docx.Document(files[0])
    
    start_idx = None
    end_idx = None
    for idx, p in enumerate(doc.paragraphs):
        if p.style.name == "Heading 1" and "Diagnóstico Técnico y Cuadro de Mando de Madurez" in p.text:
            start_idx = idx
        elif start_idx is not None and ("3.2." in p.text or "Diagnóstico Técnico Detallado por Capacidad" in p.text):
            end_idx = idx
            break
            
    if start_idx is not None:
        if end_idx is None: end_idx = len(doc.paragraphs)
        paras = [p.text.strip() for p in doc.paragraphs[start_idx:end_idx] if p.text.strip()]
        extracted_sections[code] = "\n\n".join(paras)
    else:
        extracted_sections[code] = "ERROR: Heading 1 not found."

prompt_content = f"""You are 'gemini-4-argon', Chief Technology Auditor & Supreme Evaluator of Tier-1 Executive Deliverables.

We are auditing SECTION 3.1 ("Diagnóstico Técnico y Cuadro de Mando de Madurez" before Section 3.2) across ALL 10 SPECIALIST ANNEXES of the Molins IT Assessment deliverable.

THE 4-DIMENSIONAL AUDIT RUBRIC (0.0 to 10.0 scale, Weighted Average):
- D1: Macroscopic Domain Synthesis (25%): Does it provide a bespoke, high-level operational overview of this specific technology domain in Molins (factories, logistics, offices), or is it generic?
- D2: Factual Truth & Zero Template (25%): Are the introductory paragraphs and transversal patterns grounded 100% in Molins's real evidence, or are they copy-paste templates? (Look out for copy-paste domain bugs, like Storage or FinOps describing Compute/Virtualization!).
- D3: Strategic Value for the Board (25%): Does it translate technical debt into business consequences (CapEx, downtime risk, truck weighbridge queues, licensing)?
- D4: Scope Separation & Non-Cannibalization (25%): Does it give executive telescope vision without preemptively cannibalizing Section 3.2 capability details or Volume 2 solutions?

HERE IS THE EXTRACTED SECTION 3.1 CONTENT FOR ALL 10 TOWERS:

"""

for code, name, fname_part in towers:
    prompt_content += f"\n{'='*70}\nTOWER {code}: {name}\n{'='*70}\n{extracted_sections.get(code, '')}\n"

prompt_content += """
YOUR AUDIT INSTRUCTIONS:
1. Grade EACH tower from 0.0 to 10.0 across D1, D2, D3, D4 and compute the Weighted Overall Score.
2. Provide a blunt, unflinching evaluation of each tower:
   - Identify critical defects (especially copy-paste contamination, generic boilerplate, or lack of factual teeth).
   - Point out what works well.
3. Compute the Global Section 3.1 Average Score across all 10 towers.
4. Provide the exact architectural prescription to elevate Section 3.1 across all 10 towers to a certified 10.0/10.0.

Format your response in professional Markdown with an executive summary table at the top.
"""

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

def main() -> None:
    print("Initiating Section 3.1 comprehensive audit across all 10 towers with gemini-4-argon...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt_content,
    )

    out_file = REPO_ROOT / "docs/audits/ARGON_AUDIT_SECTION_3_1_ALL_TOWERS.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    front_matter = """---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-08
applies_to:
- gemini
- audits
doc_type: operational
diataxis: reference
verification_mode: editorial
---

"""
    out_file.write_text(front_matter + response.text, encoding="utf-8")

    print("=" * 80)
    print("ARGON SECTION 3.1 AUDIT REPORT:")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"Full report written to {out_file}")

if __name__ == "__main__":
    main()
