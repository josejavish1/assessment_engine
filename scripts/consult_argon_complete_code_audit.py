#!/usr/bin/env python3
"""Adversarial forensic code audit by gemini-4-argon of the newly implemented UATCE and Section 4 Decoupling."""

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

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

# Load the exact files modified/created
FILES_TO_AUDIT = [
    "src/assessment_engine/domain/actuarial/euler_allocator.py",
    "src/assessment_engine/domain/actuarial/receptor_allocator.py",
    "src/assessment_engine/domain/actuarial/calibration_engine.py",
    "src/assessment_engine/domain/taxonomy/archetype_registry.py",
    "src/assessment_engine/adapters/compilers/strategies/actuarial_receptors.py",
    "src/assessment_engine/adapters/compilers/payload_to_ast.py",
    "src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py",
]

file_dumps = []
for rel_path in FILES_TO_AUDIT:
    full_path = REPO_ROOT / rel_path
    if full_path.exists():
        content = full_path.read_text(encoding="utf-8")
        # Truncate very large files to keep prompt focused on the refactored areas
        if rel_path.endswith("payload_to_ast.py"):
            lines = content.splitlines()
            # Focus on section 4 and convert methods
            content = "\n".join(lines[2500:2780])
        elif rel_path.endswith("tomo_asis_ast_compiler.py"):
            lines = content.splitlines()
            content = "\n".join(lines[1430:1620])
        file_dumps.append(f"--- FILE: {rel_path} ---\n{content}\n")

AUDIT_PROMPT = f"""You are 'gemini-4-argon', Supreme Code Quality Arbiter, Principal Systems Auditor, and Chief Actuarial Examiner.

USER DIRECTIVE:
"Quiero que le digas a gemini-4-argon que haga una revisión completa de lo que acabas de programar y busque bugs, problemas o antipatrones, no quiero nada hardcodeado recuerda que el objetivo es que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial, de cualquier vertical, en cualquier idioma, y el código debe estar 100% en ingles nada de español ni una sola palabra."

INSPECT THE FOLLOWING CODE BASE IMPLEMENTATION:
{''.join(file_dumps)}

YOUR FORENSIC AUDIT CHECKLIST:
1. **Zero Hardcoding Violations:**
   - Scan for any client names ('molins', 'starling', 'chedraui', etc.) or industry-specific assumptions hardcoded into python logic.
   - Scan for hardcoded currency symbols ('€', '£', '$', 'R$') in python files.
2. **Language Decoupling Law:**
   - Scan all Python code, docstrings, variable names, comments, exceptions, and logs for ANY Spanish words. The code MUST be 100% Technical English.
3. **Open FAIR Actuarial Rigor & Mathematical Invariants:**
   - Verify whether `ActuarialVectorAllocator`, `EulerPortfolioAllocator`, and `UniversalActuarialCalibrationEngine` uphold strict mathematical closure.
   - Check for penny-drift bugs, division-by-zero risks, simplex violations, or boundary clipping flaws.
4. **Universal Scalability & Design Patterns:**
   - Verify that the GoF Strategy Pattern in `actuarial_receptors.py` and `payload_to_ast.py` scales gracefully for ANY company size (10M to 100B), ANY vertical, and ANY of the 6 supported languages.
   - Check if `TableNode` col_widths or header styling have any defects or fragility.
5. **Actionable Findings & Remediation:**
   - Detail every single bug, flaw, antipattern, or stylistic lapse discovered (graded as P0-Blocker, P1-Warning, or P2-Minor).
   - If clean, certify with an institutional seal of approval.

Respond in 100% Technical English with supreme forensic rigor.
"""

def main() -> None:
    print(f"Submitting full codebase implementation to {model_name} for adversarial audit...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    audit_report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_FULL_IMPLEMENTATION_CODE_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(audit_report, encoding="utf-8")

    print(f"\nAudit Report written to: {out_file}\n")
    print("=" * 80)
    print(audit_report[:3500])
    if len(audit_report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
