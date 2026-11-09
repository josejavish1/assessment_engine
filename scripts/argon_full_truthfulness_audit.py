#!/usr/bin/env python3
"""Execute deep section-by-section forensic truthfulness and hallucination audit via gemini-4-argon."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import docx
import openpyxl

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

OUTPUT_FILE = REPO_ROOT / "docs/audits/ARGON_FORENSIC_TRUTHFULNESS_AUDIT_T1.md"


def load_docx_content(file_path: Path) -> str:
    doc = docx.Document(str(file_path))
    content_lines = []
    for p in doc.paragraphs:
        txt = p.text.strip()
        if txt:
            if p.style.name.startswith("Heading"):
                content_lines.append(f"\n## [{p.style.name}] {txt}\n")
            else:
                content_lines.append(txt)

    for idx, table in enumerate(doc.tables, 1):
        content_lines.append(f"\n### [TABLE {idx}]")
        for row in table.rows:
            cells = [c.text.strip().replace("\n", " ") for c in row.cells]
            content_lines.append(" | ".join(cells))
    return "\n".join(content_lines)


def load_t1_excel_responses() -> str:
    excel_path = (
        REPO_ROOT
        / "source_docs/molins/Preguntas Fast Assessment Molins contestadas cliente.xlsx"
    )
    wb = openpyxl.load_workbook(str(excel_path), data_only=True)
    sheet = wb["T1- Physical Data Center"]
    lines = []
    for row in sheet.iter_rows(values_only=True):
        row_vals = [str(v).strip() for v in row if v is not None and str(v).strip()]
        if row_vals:
            lines.append(" | ".join(row_vals))
    return "\n".join(lines)


def load_context_notes() -> str:
    docx_path = REPO_ROOT / "source_docs/molins/Assessment_Contexto_Molins.docx"
    doc = docx.Document(str(docx_path))
    return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())


def load_interview_t1_excerpts() -> str:
    docx_path = (
        REPO_ROOT
        / "source_docs/molins/260721 Transcripción sesion de contexto de molins (Fairfly) 1.docx"
    )
    doc = docx.Document(str(docx_path))
    t1_keywords = [
        "cpd",
        "datacenter",
        "centro de datos",
        "sant vicenç",
        "vicen",
        "sai",
        "ups",
        "clima",
        "500",
        "edificio",
        "sala",
        "incendio",
        "generador",
        "planta",
        "fabrica",
    ]
    excerpts = []
    for p in doc.paragraphs:
        txt = p.text.strip()
        if any(kw in txt.lower() for kw in t1_keywords):
            excerpts.append(txt)
    return "\n---\n".join(excerpts)


def main() -> None:
    print("Loading Ground-Truth Source Corpus...")
    t1_excel = load_t1_excel_responses()
    context_notes = load_context_notes()
    interview_excerpts = load_interview_t1_excerpts()

    print("Loading Generated Tower 1 Deliverable...")
    deliverable_path = (
        REPO_ROOT / "working/out/molins/T1/Molins_202610_Anexo_01_Data_Center_ASIS.docx"
    )
    if not deliverable_path.exists():
        deliverable_path = (
            REPO_ROOT / "working/molins/T1/Molins_202610_Anexo_01_Data_Center_ASIS.docx"
        )
    deliverable_text = load_docx_content(deliverable_path)

    prompt = f"""You are gemini-4-argon, acting as the Distinguished Forensic Systems Auditor, Lead Enterprise Ontologist, and Chief Quality Gatekeeper.

USER FEAR & AUDIT OBJECTIVE:
The user is concerned that after previous semantic drift anomalies (like SimpliVity RAM appearing in Fire Protection), there might still be hallucinated claims, invented vendors, or ungrounded statements lurking in OTHER sections of the deliverable.
You must perform an exhaustive, SECTION-BY-SECTION forensic truthfulness audit of the generated deliverable, rigorously cross-examining every paragraph, table, metric, and risk scenario against the 3 authoritative ground-truth sources:
1. Client Questionnaire Answers (Excel): `Preguntas Fast Assessment Molins contestadas cliente.xlsx` (Sheet: T1- Physical Data Center).
2. Consultant Assessment Context Notes: `Assessment_Contexto_Molins.docx`.
3. Client Transcribed Interview Audio Excerpts: `260721 Transcripción sesion de contexto de molins (Fairfly) 1.docx`.

GROUND-TRUTH CORPUS:

--- SOURCE 1: T1 Questionnaire Answers & Scores (Excel) ---
{t1_excel}

--- SOURCE 2: Consultant Context & Operational Notes (DOCX) ---
{context_notes[:10000]}

--- SOURCE 3: Literal Interview Transcription Excerpts for T1 (DOCX) ---
{interview_excerpts[:10000]}

GENERATED DELIVERABLE UNDER FORENSIC AUDIT:
--- Molins_202610_Anexo_01_Data_Center_ASIS.docx ---
{deliverable_text}

YOUR TASK:
Provide an exhaustive, section-by-section audit report:
1. Executive Verdict on Deliverable Truthfulness (Overall Score: 0.0 to 10.0 and Hallucination Risk Index: Low / Medium / High).
2. SECTION-BY-SECTION FORENSIC DIAGNOSIS:
   - Section 1: Executive Summary (Contexto Estratégico, Bottom Line, Strengths, Risks, Global Score 2.61/5.00).
   - Section 2: Platform Architecture & Baseline Physical Facilities (Sant Vicenç twin CPDs, 500m separation, electrical chain, cooling, rack density).
   - Section 3: Maturity & Capability Assessment (Pillars P1-P5 scores, Table 5 justifications, health check findings).
   - Section 4: Quantitative Risk Analysis (Open FAIR scenarios, primary downtime losses, secondary response losses, copula correlations).
   For EACH section, provide:
   * Status: [100% GROUNDED] / [EXTRAPOLATED BUT FACTUAL] / [UNSUBSTANTIATED / DRIFT]
   * Exact Source Tracing: Cite which question (e.g. T1.P1.K1.PR1 = 2), transcript quote, or context note supports the section.
   * Hallucination Audit: Specifically identify any claim, tool name, or metric that lacks factual support in the sources.
3. Summary of Findings & Actionable Recommendations: Concrete guidance to ensure 10.0/10.0 truthfulness across the entire platform.
"""

    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Executing Deep Forensic Truthfulness Audit via gemini-4-argon ({model})...")

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("---\nstatus: Verified\nowner: docs-governance\nsource_of_truth:\n- docs/README.md\nlast_verified_against: 2026-11-07\napplies_to:\n- gemini\n- architecture\ndoc_type: operational\ndiataxis: reference\nverification_mode: editorial\n---\n")
        f.write(response.text)

    print(f"Forensic audit report saved at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON FORENSIC TRUTHFULNESS AUDIT SUMMARY:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
