#!/usr/bin/env python3
"""Argon Adversarial Code Audit: Comprehensive Review of Recent Implementation.

Audits all files created or modified in the recent session:
1. src/assessment_engine/domain/schemas/evidence_extraction.py
2. src/assessment_engine/application/services/structured_evidence_extractor.py
3. src/assessment_engine/domain/schemas/executive_summary_ast.py
4. src/assessment_engine/application/services/semantic_epistemic_router.py
5. src/assessment_engine/application/services/universal_tower_synthesizer.py
6. src/assessment_engine/adapters/compilers/payload_to_ast.py

Hunts for:
- Bugs, logic flaws, runtime exceptions, type inconsistencies
- Hardcoding, client bias, vertical bias, Anglo-Saxon/Euro-centric bias
- Anti-patterns, code smells, leaky abstractions, clean architecture violations
- Spanish words or non-English contamination in code, docstrings, or variables
- Universal scalability: mid-market to Fortune 50, any vertical, any human language
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

FILES_TO_AUDIT = [
    "src/assessment_engine/domain/schemas/evidence_extraction.py",
    "src/assessment_engine/application/services/structured_evidence_extractor.py",
    "src/assessment_engine/domain/schemas/executive_summary_ast.py",
    "src/assessment_engine/application/services/semantic_epistemic_router.py",
    "src/assessment_engine/application/services/universal_tower_synthesizer.py",
    "src/assessment_engine/adapters/compilers/payload_to_ast.py",
]

code_payload = {}
for rel_path in FILES_TO_AUDIT:
    file_path = REPO_ROOT / rel_path
    if file_path.exists():
        code_payload[rel_path] = file_path.read_text(encoding="utf-8")
    else:
        code_payload[rel_path] = f"FILE NOT FOUND: {rel_path}"

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)
print(f"Connecting to Reasoning model '{model_name}' for Ruthless Codebase Audit...")

prompt = f"""You are 'gemini-4-argon', Principal Staff Systems Architect, Lead Security & Compilers Auditor, and Fortune 500 Chief Risk Officer.

THE USER'S MANDATE:
"Before continuing, I want you to tell gemini-4-argon to do a complete review of what was just programmed and look for bugs, problems, or antipatterns. I do NOT want anything hardcoded. Remember the goal is that it serves ANY company in the world from mid-size to top tier 1 globally, of any vertical, in ANY language. And the code MUST be 100% in English, not a single Spanish word (Spanish is only for chat and deliverable output)."

CODE TO AUDIT:
{json.dumps(code_payload, indent=2)}

AUDIT CRITERIA (Be ruthless, adversarial, and uncompromising):
1. BUGS & LOGIC ERRORS: Are there runtime exceptions, type mismatches, missing imports, unhandled None values, division by zero, or edge-case crashes?
2. HARDCODING & BIAS: Are there ANY hardcoded company names, client assumptions, specific vendors (e.g. weighbridges, kilns, SimpliVity), or restricted country/language mappings?
3. LANGUAGE DECOUPLING: Is the code 100% in Technical English? Are there ANY Spanish words, Spanish regexes, Spanish docstrings, or Spanish comments in production Python code?
4. SCALE INVARIANCE & UNIVERSALITY: Does the code work equally well for:
   - A $15M regional logistics firm in Germany (`de-DE`)
   - A $50B money-center bank in Japan (`ja-JP`)
   - An integrated hospital network in Brazil (`pt-BR`)
   - A heavy manufacturing firm in Spain (`es-ES`)
   - A cloud-native SaaS in the US (`en-US`)
   - A public sector sovereign agency?
5. ANTI-PATTERNS & CLEAN ARCHITECTURE: Are there leaky abstractions, violation of hexagonal boundaries (Domain importing Infrastructure), god objects, or code smells?

OUTPUT FORMAT:
- Executive Summary & Overall Grade (0 to 10)
- Concrete Bugs & Flaws Found (File by File, Line by Line)
- Hardcoding & Bias Findings
- Actionable Surgical Fixes Required
- Final Production Readiness Verdict (PASS / CONDITIONAL / FAIL)
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

out_file = REPO_ROOT / "docs/audits/ARGON_RECENT_CODE_AUDIT.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\n✓ Saved adversarial audit report to {out_file.relative_to(REPO_ROOT)}")
print("\n" + "=" * 80)
print(response.text[:2500] + "\n... [TRUNCATED] ...")
print("=" * 80)
