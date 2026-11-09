#!/usr/bin/env python3
"""Forensic Audit of Risk Dossiers vs. Raw Interview Transcripts by gemini-4-argon."""

import json
import sys
from pathlib import Path
import docx

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.adapters.compilers.in_memory_asis_compiler import derive_in_memory_fair_risks
from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

# 1. Read Raw Source Transcripts
doc1 = docx.Document(REPO_ROOT / "source_docs/molins/260721 Transcripción sesion de contexto de molins (Fairfly) 1.docx")
transcript_text = "\n".join([p.text for p in doc1.paragraphs if p.text.strip()])

doc2 = docx.Document(REPO_ROOT / "source_docs/molins/Assessment_Contexto_Molins.docx")
context_doc_text = "\n".join([p.text for p in doc2.paragraphs if p.text.strip()])

# 2. Extract Current Risk Registers across all 10 towers
towers_risk_data = {}
for t in ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"]:
    p = REPO_ROOT / f"working/molins/{t}/blueprint_{t.lower()}_payload.json"
    if not p.exists():
        continue
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)

    risks, _ = derive_in_memory_fair_risks(d, doc_lang="es", currency="€")
    towers_risk_data[t] = {
        "tower_code": t,
        "tower_name": d.get("tower_name") or d.get("document_meta", {}).get("tower_name"),
        "risks": [
            {
                "id": r.get("id"),
                "pillar": r.get("pillar"),
                "capability": r.get("capability"),
                "finding": r.get("finding"),
                "business_risk": r.get("business_risk"),
                "ownership_type": r.get("ownership_type"),
                "ale": r.get("ale"),
                "tef": r.get("tef"),
                "lm": r.get("lm")
            }
            for r in risks
        ]
    }

prompt_risks_json = json.dumps(towers_risk_data, indent=2, ensure_ascii=False)

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

AUDIT_PROMPT = f"""You are 'gemini-4-argon', the Chief Technology & Risk Auditor.

THE USER HAS REQUESTED A QUALITATIVE & FORENSIC DIAGNOSTIC CHECK OF THE RISK REGISTERS AGAINST THE RAW SOURCE INTERVIEWS:
"Beyond the financial numbers, what I really want is for gemini-4-argon to tell us:
1. Whether the risks are properly diagnosed.
2. What risks are MISSING that the client mentioned in the interviews/questionnaires and the AI/process failed to capture.
3. What risks are REDUNDANT / LEFTOVER (hallucinations, generic filler, or boilerplate that Molins never said and that doesn't apply to them).
4. An empirical explanation of why certain risks showed `ALE = 0.0` (is it cross-tower deduplication where another tower holds the cost, or uncalibrated questionnaire placeholders?)."

HERE IS THE COMPLETE RAW EVIDENCE BASE:

--- RAW TRANSCRIPT OF MOLINS CONTEXT SESSION (64,000 characters) ---
{transcript_text}

--- MOLINS CONTEXT & DISCOVERY SYNTHESIS DOCUMENT (16,000 characters) ---
{context_doc_text}

--- CURRENT EXTRACTED RISK REGISTERS ACROSS ALL 10 TOWERS ---
{prompt_risks_json}

DELIVER A THOROUGH, DETAILED, AND FORENSIC REPORT (IN SPANISH) STRUCTURING YOUR FINDINGS AS FOLLOWS:

### 1. EXPLICACIÓN TÉCNICA DEL `ALE = 0.0` (Despejando la duda del usuario)
- Explain exactly why 9 risks in the register show `ALE = 0.0`.
- Detail whether it is due to `TANGENTIAL_CONTRIBUTOR` (anti-double-counting logic) or uncalibrated questionnaire checklist items (`health_check_asis` without loss formulas).

### 2. RIESGOS BIEN DIAGNOSTICADOS (Aciertos Factuales de la IA)
- For each tower, list the risks in the register that accurately and faithfully capture what the Molins team explained (e.g., 613 days ESXi uptime without patching, SimpliVity OT cluster RAM exhaustion, 500m CPD proximity, weighbridge/truck logistics, single Croatian DBA, 1GB disk margin for SQL logs, M&A legacy ERP graveyard).

### 3. RIESGOS QUE FALTAN (Puntos Ciegos: Lo que Molins dijo y la IA se dejó fuera)
- Identify the real operational risks, architectural headaches, vendor dependencies, and organizational friction that the Molins team EXPLICITLY narrated in the transcripts, but which were OMITTED or DILUTED in the current risk register.
- Be concrete: cite specific systems, locations, people, processes, or quotes from the transcripts.

### 4. RIESGOS QUE SOBRAN (Ruido, Relleno de Catálogo y Alucinaciones)
- Identify which risks in the current register are generic textbook filler, questionnaire placeholders, or abstract concepts that Molins never talked about and that do not apply to their reality.

### 5. CONCLUSIÓN Y PLAN DE ACCIÓN RECOMENDADO
- Concrete, actionable steps to make the risk registers 100% faithful to Molins's reality before presenting to leadership.
"""


def main() -> None:
    print("Initiating forensic audit of risks vs. raw transcripts with gemini-4-argon...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )

    out_file = REPO_ROOT / "docs/audits/ARGON_FORENSIC_RISK_TRANSCRIPT_AUDIT.md"
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
- risks
doc_type: operational
diataxis: reference
verification_mode: editorial
---

"""
    out_file.write_text(front_matter + response.text, encoding="utf-8")

    print("=" * 80)
    print("ARGON FORENSIC RISK VS. TRANSCRIPT AUDIT REPORT:")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"Full audit report written to {out_file}")


if __name__ == "__main__":
    main()
