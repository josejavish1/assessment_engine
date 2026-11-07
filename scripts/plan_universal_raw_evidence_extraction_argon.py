#!/usr/bin/env python3
"""Argon Strategic Planner for Universal Raw Evidence Extraction Pipeline.

Invokes gemini-4-argon to design an uncompromising architectural blueprint for 
transitioning the Assessment Engine's ingestion phase from relying on biased, 
human-synthesized context documents to directly processing Raw Transcriptions 
(Audio/VTT/DOCX) and empirical test answers (XLSX/TXT).
"""

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

def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Connecting to reasoning engine: {model_name}...")

    prompt = """
Role: Principal Staff Systems Architect, Zero-Trust Evidence Extraction Expert, and Senior Partner at McKinsey / Anthropic.

STRATEGIC CONTEXT & GOAL:
The Assessment Engine currently relies on an intermediate "Synthesized Context Document" (e.g., a Word doc summarizing a client interview). We have empirically proven that this intermediate document introduces severe human consulting biases, extrapolations, and omits critical factual telemetry, severely contaminating downstream actuarial scoring and findings generation.

Our goal is to execute a structural paradigm shift: THE ENGINE MUST CONSUME THE RAW INTERVIEW TRANSCRIPTION (DOCX/VTT) AND THE EMPIRICAL TEST RESPONSES (XLSX/TXT) DIRECTLY. The intermediate synthesized document is hereby deprecated.

CORE MANDATES & LAWS:
1. 100% TECHNICAL ENGLISH: The architecture, data models, logic, and your output plan MUST be 100% in Technical English. No Spanish allowed in the technical blueprint.
2. ZERO HARDCODING (UNIVERSAL SCALABILITY): The extraction logic cannot contain any hardcoded tenant names, specific verticals, or hardcoded STT (Speech-to-Text) phonetic corrections (like "Simply" -> "SimpliVity"). Phonetic and semantic normalization must be handled dynamically via externalized dictionaries or LLM-based entity resolution calibrated at runtime.
3. DOMAIN PURITY: The ingestion pipeline must align perfectly with our Clean / Hexagonal Architecture. The parser must decompose raw transcripts into isolated epistemic fragments, resolving truth probabilistically before generating the `evidence_ledger.json`.
4. WORLD-CLASS EXCELLENCE (Tier-1 Standard): The resulting pipeline must be flawless, deterministic, and capable of ingesting ambiguous, messy human transcripts and turning them into structured, irrefutable architectural findings.

TASK:
Generate a comprehensive, board-ready Architectural Blueprint and Implementation Plan in Markdown:
"RFC 082: UNIVERSAL RAW EVIDENCE EXTRACTION AND PHONETIC RESOLUTION PIPELINE".

The plan MUST include:
1. Architectural Design: How the raw transcription parser (`raw_transcript_parser.py` or similar) will extract paragraphs, identify speakers (if available), and segment topics.
2. Phonetic & Entity Normalization Strategy: How to solve Speech-to-Text artifacts (e.g., "occlout" -> "Oracle Cloud", "samisense" -> "Sant Vicenç") dynamically without hardcoding dictionaries into the Python domain logic. (Hint: utilizing LLM entity extraction + dynamic tenant vocabulary configurations in `engine_config/`).
3. Epistemic Ledger Construction: How raw fragments and numerical test responses merge into the `EvidenceLedger` to become the absolute Ground Truth.
4. Step-by-Step Execution Plan: The exact sequence of Python files to create/modify to implement this pipeline flawlessly.

Output the entire plan in strict, professional Technical English.
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    output_path = REPO_ROOT / "docs/architecture/RFC_082_UNIVERSAL_RAW_EVIDENCE_EXTRACTION_PLAN_ARGON.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response.text, encoding="utf-8")
    print(f"✅ Strategic Plan successfully completed by {model_name} at: {output_path}")

if __name__ == "__main__":
    main()
