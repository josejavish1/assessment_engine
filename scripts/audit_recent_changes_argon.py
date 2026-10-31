#!/usr/bin/env python3
"""Audit of recent code changes via gemini-4-argon (100% Technical English)."""

from __future__ import annotations

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


class AuditFinding(BaseModel):
    file_path: str = Field(..., description="Path to file where violation occurs")
    line_number: int = Field(..., description="Line number of violation")
    category: str = Field(..., description="Category: BUG, HARDCODING, SPANISH_IN_CODE, or NON_UNIVERSAL")
    technical_critique: str = Field(..., description="Deep architectural and forensic critique")
    mandatory_fix: str = Field(..., description="Concrete code change required to resolve")


class ArgonAuditReport(BaseModel):
    verdict: str = Field(..., description="Must be 'PASS' or 'FAIL'")
    zero_bugs_or_antipatterns: bool = Field(..., description="True if code is completely free of bugs")
    zero_hardcoding_verified: bool = Field(..., description="True if all thresholds/paths/locales are dynamic")
    universal_tier1_enterprise_ready: bool = Field(..., description="True if scales across any company, vertical, and locale")
    strict_english_only_verified: bool = Field(..., description="True if code contains zero Spanish words")
    findings: List[AuditFinding] = Field(default_factory=list, description="List of findings, empty on PASS")
    forensic_executive_summary: str = Field(..., description="Unvarnished forensic assessment")


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    # Capture all changes: tracked modified files and untracked new files
    cmd = ["git", "diff", "HEAD", "--", "src/", "engine_config/", "tests/"]
    diff_text = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout

    # Also capture new untracked files in src/ and tests/
    untracked_files = [
        "src/assessment_engine/compiler/style_invariants.py",
        "src/assessment_engine/i18n/resolver.py",
        "tests/unit/test_declarative_i18n_resolver.py",
        "tests/unit/test_style_invariants.py",
    ]
    untracked_diffs = []
    for uf in untracked_files:
        p = REPO_ROOT / uf
        if p.exists():
            untracked_diffs.append(f"--- /dev/null\n+++ b/{uf}\n" + p.read_text(encoding="utf-8"))

    full_diff = diff_text + "\n" + "\n".join(untracked_diffs)

    prompt = f"""
Role: Principal Systems Architect, Chief Compiler Engineer & Staff Quality Auditor (Google Tier-1 / Anthropic Infrastructure).

OBJECTIVE:
Perform a comprehensive adversarial code audit on the recent code changes. Search aggressively for bugs, race conditions, anti-patterns, hardcoded assumptions, or Spanish words in code.

USER'S STRICT MANDATES:
1. ZERO BUGS, ANTI-PATTERNS, OR TYPE UNSAFETY.
2. ZERO HARDCODING:
   - Must scale seamlessly to ANY company in the world: from a mid-market industrial plant to a Global Fortune 10 financial institution.
   - Any industry vertical (Banking, Heavy Industry, Healthcare, Aerospace, Energy, SaaS).
   - Any human language (English, Spanish, German, Japanese, Portuguese, Arabic).
   - Zero hardcoded client names, zero fixed currencies, zero fixed countries.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - Zero Spanish words anywhere in code identifiers, docstrings, comments, exceptions, logs, or schemas.
   - Non-English words are ONLY permissible as dynamic localized content inside localization dictionary files (locales.json), NEVER in Python code.

CHANGESET TO AUDIT:
```diff
{full_diff}
```

Evaluate the changeset and return the output strictly conforming to the ArgonAuditReport schema.
If there are any defects, set verdict='FAIL' and detail the findings.
If the code is 100% flawless, set verdict='PASS' with findings=[].
"""

    print(f"Auditing recent changes ({len(full_diff)} chars) with {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=ArgonAuditReport,
        ),
    )

    report = ArgonAuditReport.model_validate_json(response.text)

    print("\n" + "=" * 80)
    print("AUDITORÍA FORENSE: GEMINI-4-ARGON (REVISIÓN DE CÓDIGO RECIENTE)")
    print("=" * 80)
    print(f"VEREDICTO FINAL:               {report.verdict}")
    print(f"Zero Bugs / Antipatrones:      {report.zero_bugs_or_antipatterns}")
    print(f"Zero Hardcoding Verificado:    {report.zero_hardcoding_verified}")
    print(f"Universal Tier-1 Enterprise:   {report.universal_tier1_enterprise_ready}")
    print(f"100% Strict English Codebase:  {report.strict_english_only_verified}")
    print(f"Total de Hallazgos Críticos:   {len(report.findings)}")
    print("-" * 80)
    print("RESUMEN EJECUTIVO FORENSE:")
    print(report.forensic_executive_summary)
    print("-" * 80)

    if report.findings:
        print("HALLAZGOS DETALLADOS:")
        for idx, f in enumerate(report.findings, start=1):
            print(f"[{idx}] {f.file_path}:{f.line_number} [{f.category}]")
            print(f"    Critique: {f.technical_critique}")
            print(f"    Required Fix: {f.mandatory_fix}")
            print()
    else:
        print("CERTIFICACIÓN: Cero defectos encontrados. El código cumple al 100% con los mandatos.")

    print("=" * 80)


if __name__ == "__main__":
    main()
