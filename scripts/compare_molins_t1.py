#!/usr/bin/env python3
"""Side-by-Side Forensic Comparison and Strategic Planning via gemini-4-argon (100% Technical English)."""

from __future__ import annotations

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

base_path = REPO_ROOT / "working/out/molins_baseline_pre_argon/T1/Molins_202610_Anexo_01_Data_Center_ASIS.docx"
new_path = REPO_ROOT / "working/out/molins/T1/Molins_202610_Anexo_01_Data_Center_ASIS.docx"

doc_base = Document(str(base_path))
doc_new = Document(str(new_path))


def extract_full_text(doc: Document) -> str:
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    table_lines = []
    for t in doc.tables:
        for r in t.rows:
            row_txt = " | ".join(c.text.strip() for c in r.cells if c.text.strip())
            if row_txt:
                table_lines.append(row_txt)
    return "\n".join(paragraphs + table_lines)


base_text = extract_full_text(doc_base)
new_text = extract_full_text(doc_new)

base_words = len(base_text.split())
new_words = len(new_text.split())

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

prompt = f"""
Role: Chief Technology Officer, Principal Systems Architect & Senior Strategy Partner (McKinsey & Co. / Gartner Research).

OBJECTIVE:
Perform an exhaustive, rigorous, unvarnished comparative audit between the original Baseline Deliverable and the newly compiled Deliverable for Molins T1 (Physical Data Center & Facilities):
- Baseline Deliverable (Oct 30): {len(doc_base.paragraphs)} paragraphs, {len(doc_base.tables)} tables, {base_words} words, 23 PDF pages.
- New Master Deliverable (Current HEAD): {len(doc_new.paragraphs)} paragraphs, {len(doc_new.tables)} tables, {new_words} words, 23 PDF pages.

USER'S STRATEGIC QUESTIONS AND MANDATES:
1. Did we lose any value or consulting depth compared to the original baseline?
   - Compare Chapter 1 (Executive Summary), Chapter 2 (Methodology/Scope), Chapter 3 (Maturity Dashboard), Chapter 4 (FAIR Risks), and Chapter 5 (Conclusions/Roadmap).
   - Identify any specific insights, nuances, or technical points that were present in the baseline but got lost or diluted in the new version.
2. Identify what is clearly superior in the new version:
   - Layout, typography, financial accuracy (1.05M € vs 8.4k € ALE), WCAG contrast, table modularity, absence of raw code markers (e.g. 'chapter3title', '**' markdown leaks).
3. Strategic Engineering Plan for 100% Perfection:
   - How should we address any remaining gaps before touching code?
   - Ensure the solution is 100% UNIVERSAL across any company from mid-market to Global Fortune 10, any vertical (banking, energy, manufacturing, health, tech), any language/locale, and zero hardcoding.
   - Codebase must remain 100% in Technical English (zero Spanish in code, docstrings, or schemas; Spanish only as localized output data).

BASELINE CORPUS (23 PAGES, {base_words} WORDS):
```text
{base_text[:20000]}
```

NEW MASTER CORPUS (23 PAGES, {new_words} WORDS):
```text
{new_text[:20000]}
```

Provide your structured assessment with brutal honesty, quantitative evidence, and an actionable, flawless strategic roadmap.
"""

print(f"Executing comparative forensic audit via {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print(response.text)
