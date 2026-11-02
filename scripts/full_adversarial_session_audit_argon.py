#!/usr/bin/env python3
"""Full Adversarial Forensic Session Audit by gemini-4-argon across all session changes."""

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


class FullSessionAuditVerdict(BaseModel):
    verdict: str = Field(..., description="Must be 'PASS' or 'FAIL'")
    zero_bugs_or_antipatterns: bool = Field(..., description="True if code is completely free of bugs")
    zero_hardcoding_verified: bool = Field(..., description="True if universal across all company tiers and verticals")
    universal_tier1_enterprise_ready: bool = Field(..., description="True if ready for mid-market to Fortune 10 across any vertical")
    strict_english_only_verified: bool = Field(..., description="True if Python source code contains zero Spanish words")
    split_brain_eradicated: bool = Field(..., description="True if all towers T1..T10 are processed identically with 21 keys")
    openxml_editorial_excellence_verified: bool = Field(..., description="True if Word documents follow strict OpenXML standards with native TOC, active navigation pane, and zero corrupted XML")
    findings: List[ForensicFinding] = Field(default_factory=list, description="List of findings, empty on PASS")
    forensic_executive_summary: str = Field(..., description="Unvarnished forensic assessment")


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    diff_cmd = ["git", "diff", "origin/main", "--", "src/"]
    diff_text = subprocess.run(diff_cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout

    prompt = f"""
Role: Principal Systems Architect, Chief Compiler Engineer & Staff Quality Auditor (Google Tier-1 / Anthropic Core Infrastructure).

OBJECTIVE:
Perform a relentless, exhaustive, and adversarial code audit across all changes implemented in this session compared to `origin/main`.

AUDITED SOURCE FILES:
1. `src/assessment_engine/adapters/compilers/docx_compiler.py` (Cover containment, OpenXML SDT TOC widget, native Heading styles, outlineLvl, prefix stripping)
2. `src/assessment_engine/adapters/compilers/payload_to_ast.py` (Cover subtitle, Section 3.2 resilient pillar resolution, Chapter 4 risk cards, Chapter 5 AS-IS Diagnostic Synthesis Matrix)
3. `src/assessment_engine/adapters/compilers/ast_appendices_builder.py` (Resilient pillar resolution in methodology/capabilities)
4. `src/assessment_engine/application/universal_payload_enricher.py` (Universal 21-key payload enrichment, zero split-brain, locale normalization)
5. `src/assessment_engine/cli/enrich_tower_payload_cli.py` (Fail-fast enforcement)
6. `src/assessment_engine/domain/cfo_actuarial_gate.py` (Pre-flight CFO Actuarial Gate)
7. `src/assessment_engine/domain/contracts/enriched_payload_schema.py` (21-key Pydantic contract)
8. `src/assessment_engine/domain/services/localization_resolver.py` (14-locale typography & currency)
9. `src/assessment_engine/domain/taxonomy_resolver.py` (196 leaf KPI indexing across 10 towers)

USER'S ABSOLUTE AND NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ISSUES, OR ANTI-PATTERNS:
   - Check all math, typing, boundary conditions, exception handling, dictionary lookups, and edge cases.
   - Fail-fast enforcement: no silent error swallowing, no type unsafety, no indexing errors, no division by zero.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - The code MUST serve ANY company in the world: from a 50-person credit union or regional hospital to a top Global Fortune 10 bank, aerospace manufacturer, or energy conglomerate.
   - Any industry vertical.
   - Any ISO 4217 currency (USD, EUR, GBP, JPY, CHF, CAD, AUD, BRL, SGD, KRW).
   - Any human language (English, Spanish, German, Japanese, Portuguese, French, etc.).
   - Zero hardcoded client names ("Molins", "Acme"), zero fixed currencies, zero fixed monetary amounts, zero hardcoded risk IDs or percentages.
   - All tenant details, thresholds, and financial models must be dynamically derived or driven by configuration / locales.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - Zero Spanish words anywhere in Python identifiers, variable names, function names, docstrings, comments, exceptions, logs, or schemas.
   - Spanish and other human languages are ONLY permissible as localized data in `engine_config/locales.json` or dynamic translation output.
4. ERADICATION OF SPLIT-BRAIN:
   - Verify that all towers (T1 through T10) are processed symmetrically with the same 21 structural keys and forensic grounding.
5. OPENXML EDITORIAL EXCELLENCE:
   - Verify that Word documents strictly adhere to ISO/IEC 29500 OpenXML schemas.
   - Native TOC generated inside `<w:sdt>` with `<w:updateFields w:val="true"/>`.
   - Native Word outline levels (`<w:outlineLvl>`) activating the Word Navigation Pane.
   - Zero duplicate heading numbers.

COMPLETE GIT DIFF AGAINST ORIGIN/MAIN (src/):
```diff
{diff_text}
```

Analyze with extreme forensic rigor. Return your output strictly conforming to the FullSessionAuditVerdict schema.
If there are any flaws, set verdict='FAIL' and document each finding.
If the implementation is 100% flawless and satisfies all user mandates, set verdict='PASS' with findings=[].
"""

    print(f"Executing full adversarial session audit via {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=FullSessionAuditVerdict,
        ),
    )

    verdict_data = json.loads(response.text)
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: FULL SESSION AUDIT VERDICT")
    print("=" * 80)
    print(json.dumps(verdict_data, indent=2, ensure_ascii=False))
    print("=" * 80)

    if verdict_data.get("verdict") == "PASS":
        print("\n>>> AUDIT PASSED: ZERO BUGS, ZERO HARDCODING, 100% TECHNICAL ENGLISH, OPENXML PERFECTION <<<")
    else:
        print(f"\n>>> AUDIT FAILED: {len(verdict_data.get('findings', []))} FINDINGS DETECTED <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()
