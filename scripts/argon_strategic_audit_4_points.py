#!/usr/bin/env python3
"""Argon-4 Deep Forensic Review on 4 Core Strategic Points of Tomo 1 AS-IS.

Points requested by the user:
1. Tone calibration: Eliminating catastrophic/alarmist rhetoric, especially in Section 1,
   elevating to a sober, factual, constructive McKinsey/Gartner Tier-1 board tone.
2. Simplification of titles and subtitles: Clear, direct, and universally understandable.
3. Strict AS-IS boundary: Purging premature TO-BE leakage and roadmap designs that belong in Tomo 2.
4. Mathematical & actuarial reconciliation: Absolute coherence, zero split-brain, transparent arithmetic.
"""

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


def extract_full_docx_text(file_path: Path) -> str:
    doc = Document(file_path)
    lines = []
    lines.append(f"=== DOCUMENT: {file_path.name} ===")
    for p in doc.paragraphs:
        txt = p.text.strip()
        if txt:
            lines.append(f"[{p.style.name}]: {txt}")
    for idx, tbl in enumerate(doc.tables):
        lines.append(f"\n--- TABLE {idx} ({len(tbl.rows)} rows, {len(tbl.columns)} cols) ---")
        for r_idx, row in enumerate(tbl.rows):
            row_txt = " | ".join(c.text.replace("\n", " ").strip() for c in row.cells)
            lines.append(f"  R{r_idx}: {row_txt[:160]}")
    return "\n".join(lines)


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    f_docx = REPO_ROOT / "working/out/Molins_Entrega_Oficial_Piramide_Tier1/01_TRIADA_ESTRATEGICA_TRANSVERSAL_CTO/Molins_202610_Tomo_1_Diagnostico_ASIS.docx"
    doc_text = extract_full_docx_text(f_docx)

    prompt = f"""
Role: You are an elite Chief Information Officer (CIO) and Senior Partner at Gartner / McKinsey, advising the Board of Directors of a Fortune 500 industrial multinational.

THE USER IDENTIFIES 4 CRITICAL OBSERVATIONS ON THE CONSOLIDATED TOMO 1 AS-IS:
1. "primero mucho texto está escrito muy catastrofista especialmente el aparatado 1, creo que lo podemos hacer mucho mejor la verdad."
2. "segundo, los titulos y subtitulos del documento deben ser sencillos y faciles de entender."
3. "tercera -> esto es un documento de AS-IS no se si debemos tener cosas del TO-BE que veo muchas."
4. "cuarta --> me preocupa mucho que los números sean coherentes y no haya split brain esto es totalmente fundamental y crítico."

MANDATE: Perform an in-depth, clinical, adversarial review of the current deliverable across EACH of these 4 specific points. Provide concrete, surgical diagnoses and exact rewrites/remediations.

CURRENT 15-PAGE TOMO 1 AS-IS TEXT AND TABLES:
{doc_text}

STRUCTURE YOUR DIAGNOSIS INTO 4 DEEP FORENSIC SECTIONS:

### 1. AUDITORÍA DE TONO (DES-CATASTROFIZACIÓN Y ELEGANCIA EJECUTIVA)
- Specific examples of alarmist, apocalyptic, or exaggerated language currently in the document (e.g., in Section 1, risk cards, triad).
- Why this backfires before a Board of Directors / CEO (sounds like a sales pitch to induce panic rather than a sober engineering assessment).
- Exact rewriting blueprint: How to convey urgency, risk, and technical reality with cold, factual, elegant, Tier-1 consulting precision (objective facts, operational metrics, financial exposure without sensationalist adjectives).

### 2. SIMPLIFICACIÓN Y CLARIDAD DE TÍTULOS Y SUBTÍTULOS
- Critique of current titles (are they too long, baroque, or jargon-heavy?).
- Proposed definitive list of simple, direct, executive titles and subtitles for the 5 chapters, sub-chapters, and tables.

### 3. FRONTERA ESTRICTA AS-IS VS. TO-BE (PURGA DE CONTAMINACIÓN FUTURA)
- Audit of premature TO-BE leakage currently in the document (e.g., target architecture prescriptions, roadmap waves, vendor escape plans, migration steps) that belong strictly in Tomo 2.
- The rule of thumb for an AS-IS: Focus on current architecture, current operational metrics, observed technical debt, and current financial exposure, limiting forward-looking text to high-level strategic opportunities or business implications without preempting the TO-BE engineering designs.
- Specific sections to cleanse.

### 4. RECONCILIACIÓN MATEMÁTICA Y CERO SPLIT-BRAIN
- Audit of all financial figures: 916.416 € ALE P50, Tier breakdown (439k, 348k, 128k), 10 individual tower ALE allocations, hourly downtime rates (13.061 €/h corporate, 5.000 €/h weighbridges), local P90 outage (450k €), and 3-year VaR (3.7M - 6.1M €).
- Are there any remaining mathematical discrepancies, rounding issues, or cognitive ambiguities for a CFO?
- Mathematical proof of closed-form integrity.

### 5. VEREDICTO Y PLAN DE ACCIÓN INMEDIATO
- Summary assessment and the exact action plan to make Tomo 1 AS-IS an undeniable 10/10 master deliverable.
"""

    print(f"Requesting deep 4-point review from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/ARGON_4_POINTS_DEEP_REVIEW_TOMO_1_ASIS.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: DEEP 4-POINT STRATEGIC REVIEW")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nReview saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
