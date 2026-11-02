#!/usr/bin/env python3
"""Deep Adversarial Forensic Code Audit by gemini-4-argon of the recent AS-IS Deliverable Refinement & CFO Actuarial Gate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List

from google.genai import types
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)


class ForensicFinding(BaseModel):
    file_path: str = Field(..., description="File path where violation occurs")
    line_number: int = Field(..., description="Approximate line number")
    category: str = Field(..., description="Category: BUG, HARDCODING, NON_UNIVERSAL, or SPANISH_IN_CODE")
    severity: str = Field(..., description="CRITICAL, MAJOR, or MINOR")
    technical_critique: str = Field(..., description="Deep architectural and forensic explanation")
    mandatory_fix: str = Field(..., description="Concrete code or configuration change required")


class ComprehensiveArgonAuditVerdict(BaseModel):
    verdict: str = Field(..., description="Must be 'PASS' or 'FAIL'")
    zero_bugs_or_antipatterns: bool = Field(..., description="True if code is completely free of bugs")
    zero_hardcoding_verified: bool = Field(..., description="True if universal across all company tiers and verticals")
    universal_tier1_enterprise_ready: bool = Field(..., description="True if ready for mid-market to Fortune 10 across any vertical")
    strict_english_only_verified: bool = Field(..., description="True if Python source code contains zero Spanish words")
    findings: List[ForensicFinding] = Field(default_factory=list, description="List of findings, empty on PASS")
    forensic_executive_summary: str = Field(..., description="Unvarnished forensic assessment")


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    cfo_gate_code = (REPO_ROOT / "src/assessment_engine/domain/cfo_actuarial_gate.py").read_text(encoding="utf-8")
    payload_to_ast_code = (REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py").read_text(encoding="utf-8")
    docx_compiler_code = (REPO_ROOT / "src/assessment_engine/adapters/compilers/docx_compiler.py").read_text(encoding="utf-8")

    diff_cmd = ["git", "diff", "origin/main", "--", "src/", "engine_config/locales.json"]
    diff_text = subprocess.run(diff_cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout

    prompt = f"""
Role: Principal Systems Architect, Chief Compiler Engineer & Staff Quality Auditor (Google Tier-1 / Anthropic Core Infrastructure).

OBJECTIVE:
Perform a relentless, exhaustive, and adversarial code audit on the newly implemented changes:
1. `src/assessment_engine/domain/cfo_actuarial_gate.py` (Pre-flight Actuarial CFO Audit Gate)
2. `src/assessment_engine/adapters/compilers/payload_to_ast.py` (AS-IS Deliverable Purity, Open FAIR card re-engineering, Chapter 5 Diagnostic Synthesis Matrix, Appendix A single technical appendix)
3. `src/assessment_engine/adapters/compilers/docx_compiler.py` (Native OpenXML TOC, first-page footer metadata, and styling)
4. Recent git diff against origin/main.

USER'S ABSOLUTE AND NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ISSUES, OR ANTI-PATTERNS:
   - Check all math, typing, boundary conditions, exception handling, dictionary lookups, and edge cases.
   - Fail-fast enforcement: no silent error swallowing, no type unsafety, no indexing errors, no division by zero.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - The code MUST serve ANY company in the world: from a 50-person credit union or regional hospital to a top Global Fortune 10 bank, aerospace manufacturer, or energy conglomerate.
   - Any industry vertical.
   - Any ISO 4217 currency (USD, EUR, GBP, JPY, CHF, CAD, AUD, BRL, SGD, KRW).
   - Any human language (English, Spanish, German, Japanese, Portuguese, French).
   - Zero hardcoded client names ("Molins", "Acme"), zero fixed currencies, zero fixed monetary amounts, zero hardcoded risk IDs or percentages.
   - All tenant details, thresholds, and financial models must be dynamically derived or driven by configuration / locales.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - Zero Spanish words anywhere in Python identifiers, variable names, function names, docstrings, comments, exceptions, logs, or schemas.
   - Spanish and other human languages are ONLY permissible as localized data in `engine_config/locales.json` or dynamic translation output.
   - (Note: token match targets inside `ActuarialAuditPolicy.forbidden_certainty_tokens` designed to catch forbidden unvetted user inputs in multiple languages are acceptable).

SOURCE: cfo_actuarial_gate.py:
```python
{cfo_gate_code}
```

SOURCE: payload_to_ast.py (relevant sections):
```python
{payload_to_ast_code[1150:2050]}
```

GIT DIFF AGAINST ORIGIN/MAIN:
```diff
{diff_text}
```

Analyze with extreme forensic rigor. Return your output strictly conforming to the ComprehensiveArgonAuditVerdict schema.
If there are any flaws, set verdict='FAIL' and document each finding.
If the implementation is 100% flawless and satisfies all user mandates, set verdict='PASS' with findings=[].
"""

    print(f"Executing comprehensive forensic audit via {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=ComprehensiveArgonAuditVerdict,
        ),
    )

    verdict_data = json.loads(response.text)
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: FORENSIC AUDIT VERDICT")
    print("=" * 80)
    print(json.dumps(verdict_data, indent=2, ensure_ascii=False))
    print("=" * 80)

    if verdict_data.get("verdict") == "PASS":
        print("\n>>> AUDIT PASSED: 100% FLIE-FREE, ZERO HARDCODING, 100% TECHNICAL ENGLISH <<<")
    else:
        print(f"\n>>> AUDIT FAILED: {len(verdict_data.get('findings', []))} FINDINGS DETECTED <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()
