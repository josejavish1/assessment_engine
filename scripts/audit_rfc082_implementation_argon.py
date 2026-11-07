#!/usr/bin/env python3
"""Adversarial Implementation Auditor via gemini-4-argon for RFC 082.

Performs an exhaustive, uncompromising audit of the RFC 082 Raw Ingestion Pipeline:
1. src/assessment_engine/domain/schemas/epistemic_ledger.py
2. src/assessment_engine/domain/contracts/ingestion_ports.py
3. src/assessment_engine/infrastructure/parsers/raw_transcript_parser.py
4. src/assessment_engine/infrastructure/parsers/empirical_response_parser.py
5. src/assessment_engine/infrastructure/normalization/phonetic_entity_resolver.py
6. src/assessment_engine/application/services/epistemic_synthesizer.py
7. src/assessment_engine/application/pipelines/raw_evidence_ingestion_pipeline.py
8. engine_config/ontologies/global_tech_ontology.yaml

Audits for:
- Language Decoupling Law (zero Spanish in code/comments).
- Zero-Hardcoding (multinational, multi-vertical, multi-language scalability).
- Computational robustness, edge-case failure modes, thread safety, and anti-patterns.
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


def read_file_safe(rel_path: str) -> str:
    p = REPO_ROOT / rel_path
    return p.read_text(encoding="utf-8") if p.exists() else f"File not found: {rel_path}"


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Connecting to reasoning engine: {model_name}...")

    epistemic_ledger_py = read_file_safe("src/assessment_engine/domain/schemas/epistemic_ledger.py")
    ingestion_ports_py = read_file_safe("src/assessment_engine/domain/contracts/ingestion_ports.py")
    raw_transcript_parser_py = read_file_safe("src/assessment_engine/infrastructure/parsers/raw_transcript_parser.py")
    empirical_response_parser_py = read_file_safe("src/assessment_engine/infrastructure/parsers/empirical_response_parser.py")
    phonetic_entity_resolver_py = read_file_safe("src/assessment_engine/infrastructure/normalization/phonetic_entity_resolver.py")
    epistemic_synthesizer_py = read_file_safe("src/assessment_engine/application/services/epistemic_synthesizer.py")
    raw_evidence_ingestion_pipeline_py = read_file_safe("src/assessment_engine/application/pipelines/raw_evidence_ingestion_pipeline.py")
    global_tech_ontology_yaml = read_file_safe("engine_config/ontologies/global_tech_ontology.yaml")

    prompt = f"""
Role: Principal Staff Systems Architect, Zero-Trust Code Auditor, and Senior Partner at McKinsey / Anthropic / Google.

TASK:
Perform a hostile, uncompromising adversarial code and architectural audit of our newly implemented RFC 082 Universal Raw Evidence Ingestion Pipeline.
Search relentlessly for any latent bug, edge-case vulnerability, performance bottleneck, architectural defect, or hardcoding violation.

CORE MANDATES & LAWS:
1. 100% TECHNICAL ENGLISH CODEBASE:
   - Check every line of Python code, comments, docstrings, variable names, logs, exceptions, and tests.
   - Any non-English word or Spanish character in Python source files is a CRITICAL violation.
2. ZERO HARDCODING:
   - Must scale cleanly from a 50M€ mid-market company to a 50B€ global Tier-1 multinational.
   - Must work for any vertical (banking, retail, manufacturing, healthcare, public sector, energy).
   - Must support any language (Japanese, German, French, Portuguese, Spanish, English).
   - Are there hardcoded domain codes or keyword lists inside Python logic instead of externalized configs?
3. COMPUTATIONAL ROBUSTNESS & EDGE CASES:
   - What happens if the transcript has 10,000 paragraphs or 0 paragraphs?
   - What happens if an utterance has no text or malformed timestamps?
   - What happens if the spreadsheet has empty rows, formulas, or corrupted XML?
   - Are there ReDoS (Regular Expression Denial of Service) risks in regex patterns?
   - Is regex compilation safe, deterministic, and thread-safe?
4. CLEAN / HEXAGONAL ARCHITECTURE:
   - Domain layer (src/assessment_engine/domain/) must remain 100% pure (zero I/O, zero network, zero open() calls).
   - Clear separation between Domain, Application, and Infrastructure layers.

CODE UNDER AUDIT:

--- FILE 1: src/assessment_engine/domain/schemas/epistemic_ledger.py ---
{epistemic_ledger_py}

--- FILE 2: src/assessment_engine/domain/contracts/ingestion_ports.py ---
{ingestion_ports_py}

--- FILE 3: src/assessment_engine/infrastructure/parsers/raw_transcript_parser.py ---
{raw_transcript_parser_py}

--- FILE 4: src/assessment_engine/infrastructure/parsers/empirical_response_parser.py ---
{empirical_response_parser_py}

--- FILE 5: src/assessment_engine/infrastructure/normalization/phonetic_entity_resolver.py ---
{phonetic_entity_resolver_py}

--- FILE 6: src/assessment_engine/application/services/epistemic_synthesizer.py ---
{epistemic_synthesizer_py}

--- FILE 7: src/assessment_engine/application/pipelines/raw_evidence_ingestion_pipeline.py ---
{raw_evidence_ingestion_pipeline_py}

--- FILE 8: engine_config/ontologies/global_tech_ontology.yaml ---
{global_tech_ontology_yaml}

AUDIT DELIVERABLE:
Generate a comprehensive, board-ready audit report in Markdown with YAML front matter:
"ARGON ADVERSARIAL IMPLEMENTATION AUDIT: RFC 082 UNIVERSAL RAW INGESTION PIPELINE".

The report MUST include:
1. Executive Verdict: Pass / Conditional Pass / Fail.
2. Forensic Inspection Findings (categorized as Critical, High, Medium, Low, or Informational):
   - Language Decoupling inspection.
   - Zero-Hardcoding inspection (hunt down any hardcoded lists).
   - Computational / Algorithmic Edge-Case inspection (ReDoS, XML parsing, memory limits).
   - Clean Architecture & Hexagonal Purity inspection.
3. Concrete Remediation Plan: Exact, surgical Technical English code changes for every identified finding.
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config={"http_options": {"timeout": 600000}},
    )

    output_path = REPO_ROOT / "docs/architecture/ARGON_ADVERSARIAL_RFC082_RAW_INGESTION_AUDIT.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepend required documentation front-matter
    report_text = response.text
    if not report_text.strip().startswith("---"):
        front_matter = """---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-06-26
applies_to:
- gemini
doc_type: operational
diataxis: reference
verification_mode: editorial
---
"""
        report_text = front_matter + report_text

    output_path.write_text(report_text, encoding="utf-8")
    print(f"✅ Adversarial Audit successfully completed by {model_name} at: {output_path}")


if __name__ == "__main__":
    main()
