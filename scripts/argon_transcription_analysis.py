#!/usr/bin/env python3
"""Argon Transcription vs Context Analysis

Uses gemini-4-argon to compare the raw transcription of the context session 
with the synthesized context document to find biases, inventions, or incoherencies.
"""

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

def extract_text(docx_path: str) -> str:
    doc = docx.Document(docx_path)
    return "\n".join([p.text.strip() for p in doc.paragraphs if p.text.strip()])

def main():
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    
    transcription_text = extract_text(str(REPO_ROOT / "source_docs/molins/260721 Transcripción sesion de contexto de molins (Fairfly) 1.docx"))
    context_text = extract_text(str(REPO_ROOT / "source_docs/molins/Assessment_Contexto_Molins.docx"))
    
    prompt = f"""
Role: Senior Forensic IT Auditor and Principal Architect.

Task:
We have two documents from an IT Infrastructure Assessment for a client named Molins:
1. RAW TRANSCRIPTION: The exact word-for-word transcript of the initial context interview with the client's IT lead.
2. SYNTHESIZED CONTEXT DOC: A document ("Assessment_Contexto_Molins") that was generated as a summary of the context session.

The synthesized context doc has been used as the foundational truth for generating 143 technical findings across 10 domains.
However, we suspect the synthesized context document contains severe biases, inventions, or hallucinations—claims that do NOT exist in the raw transcription, or things that contradict the raw transcription.

Analyze both texts carefully. Provide a highly structured forensic report detailing EXACTLY what incoherencies, inventions, or biases exist in the SYNTHESIZED CONTEXT DOC when compared to the RAW TRANSCRIPTION.

Specifically, look for:
- Technologies, vendors, or tools mentioned in the synthesized doc that the client never said.
- Criticality, severity, or problems exaggerated in the synthesized doc that the client downplayed or said were solved.
- Scope of integration (e.g., about Secil, their recently acquired company in Portugal) where the synthesized doc assumes things the client didn't confirm.
- Any architectural assumptions (Mainframes, specific networks) invented by the synthesizer.

Provide the report in Spanish (since the interview is in Spanish and this is for the audit team to review internally).

RAW TRANSCRIPTION:
{transcription_text}

========================================================================

SYNTHESIZED CONTEXT DOC:
{context_text}
"""

    print(f"Connecting to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )
    
    output_path = REPO_ROOT / "docs/audits/transcription_vs_context_audit_argon.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response.text, encoding="utf-8")
    print(f"✅ Audit report saved to {output_path}")

if __name__ == "__main__":
    main()
