#!/usr/bin/env python3
"""Consult gemini-4-argon to conduct a comprehensive adversarial audit of recent code changes."""

from __future__ import annotations

import subprocess
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

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

# Extract git diff for relevant modified files
git_diff_cmd = [
    "git", "diff", "HEAD~3", "--",
    "src/assessment_engine/application/services/neurosymbolic_risk_synthesizer.py",
    "src/assessment_engine/domain/schemas/risk_synthesis.py",
    "src/assessment_engine/application/services/risk_synthesis_service.py",
    "src/assessment_engine/adapters/compilers/payload_to_ast.py",
    "scripts/build_client_delivery_suite.py",
    "engine_config/locales.json",
    "engine_config/tower_classification_keywords.json",
    "tests/unit/test_risk_synthesis_contract.py",
    "tests/unit/test_neurosymbolic_risk_synthesizer.py",
]

diff_output = subprocess.check_output(git_diff_cmd, text=True, cwd=REPO_ROOT)
if len(diff_output) > 50000:
    diff_output = diff_output[:50000] + "\n... [Diff truncated for prompt length] ...\n"

AUDIT_PROMPT = f"""You are 'gemini-4-argon', Principal Enterprise Architect, Supreme Code Quality Arbiter, and Chief Forensic Auditor for the Assessment Engine.

CRITICAL USER MANDATE & AUDIT CRITERIA:
The user demands an uncompromising, microscopic audit of the code recently implemented:
1. Zero Hardcoding: The system must work for ANY enterprise in the world, from small-and-medium enterprises (SMEs) to global Tier-1 conglomerates, across ANY vertical (Healthcare, Banking, Retail, Manufacturing, Telecom, Logistics, Aerospace) and in ANY language.
2. 100% Technical English Codebase: Zero Spanish (or Portuguese/French/German) in variable names, function names, docstrings, comments, log messages, exception messages, or test names. The code itself must be 100% technical English. (Foreign languages exist exclusively as localized output data or locale catalog strings).
3. Search for Bugs, Problems, Edge Cases, or Antipatterns: Identify any logic flaws, unhandled exceptions, race conditions, brittle string parsing, or performance bottlenecks.
4. Linguistic Purity: Ensure that when non-English deliverables (e.g. Portuguese, Spanish) are produced, there is zero cross-contamination of English tokens in localized narrative paragraphs.
5. SOTA Alignment: Assess whether this code meets the standards of Tier-1 software engineering (Palantir, OpenAI Applied, QuantumBlack).

HERE IS THE COMPLETE GIT DIFF OF THE RECENT MODIFICATIONS:
--- BEGIN GIT DIFF ---
{diff_output}
--- END GIT DIFF ---

YOUR MISSION:
Deliver a comprehensive, brutally rigorous, section-by-section audit report examining:
1. Hardcoding Analysis: Are there any hidden hardcodings, client names, industry biases, or brittle assumptions remaining?
2. Language Decoupling Law Compliance: Is the code 100% in Technical English? Are there any Spanish comments, docstrings, or variables?
3. Bugs, Fragilities & Antipatterns: Detail any discovered flaws, edge cases (e.g. empty lists, missing keys, division by zero), or architectural anti-patterns.
4. Recommendations: What exact adjustments are required to achieve undisputed 10/10 perfection?

Deliver your verdict with absolute technical authority.
"""

def main() -> None:
    print(f"Submitting comprehensive code audit to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    audit_report = response.text
    out_file = REPO_ROOT / "docs/architecture/ARGON_RECENT_CODE_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(audit_report, encoding="utf-8")
    print(f"\nAudit Report generated successfully. Written to: {out_file}\n")
    print("=" * 80)
    print(audit_report[:3500])
    if len(audit_report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")

if __name__ == "__main__":
    main()
