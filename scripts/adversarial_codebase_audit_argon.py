#!/usr/bin/env python3
"""Deep Adversarial Forensic Code Audit by gemini-4-argon (100% Technical English)."""

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

    payload_to_ast_code = (REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py").read_text(encoding="utf-8")
    ast_appendices_code = (REPO_ROOT / "src/assessment_engine/adapters/compilers/ast_appendices_builder.py").read_text(encoding="utf-8")

    diff_cmd = ["git", "show", "8ab2894", "--", "src/assessment_engine/adapters/compilers/", "engine_config/locales.json"]
    diff_text = subprocess.run(diff_cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout

    prompt = f"""
Role: Principal Systems Architect, Chief Compiler Engineer & Staff Quality Auditor (Google Tier-1 / Anthropic Core Infrastructure).

OBJECTIVE:
Perform a deep, exhaustive, adversarial code audit on the full AST compilation engine (`payload_to_ast.py` and `ast_appendices_builder.py`), plus the recent changeset in commit 8ab2894.

USER'S ABSOLUTE AND NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ISSUES, OR ANTI-PATTERNS:
   - Check all visitor handlers, node constructors, table builders, mathematical calculations, and exception handling.
   - Fail-fast enforcement: no silent error swallowing, no type unsafety, no indexing errors, no division by zero.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - The platform MUST serve ANY company in the world: from a 50-person mid-market firm to a top Global Fortune 10 bank, healthcare conglomerate, or tech giant.
   - Any industry vertical (Banking, Capital Markets, Heavy Industry, Healthcare, Aerospace, Energy, SaaS, Retail, Telecom).
   - Any ISO 4217 currency (USD, EUR, GBP, JPY, CHF, CAD, AUD, BRL, SGD, KRW).
   - Any human language (English, Spanish, German, Japanese, Portuguese, French, Arabic).
   - Zero hardcoded client names ("Molins", "Acme"), zero fixed currencies ("EUR", "$"), zero fixed monetary amounts, zero hardcoded risk IDs or percentages.
   - All tenant details, thresholds, and financial models must be dynamically derived or driven by configuration.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - Zero Spanish words anywhere in Python identifiers, variable names, function names, docstrings, comments, exceptions, logs, or schemas.
   - Spanish and other human languages are ONLY permissible as localized data in `engine_config/locales.json`.

FULL SOURCE: payload_to_ast.py ({len(payload_to_ast_code)} chars):
```python
{payload_to_ast_code}
```

FULL SOURCE: ast_appendices_builder.py ({len(ast_appendices_code)} chars):
```python
{ast_appendices_code}
```

RECENT CHANGESET (Commit 8ab2894):
```diff
{diff_text[:30000]}
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

    report = ComprehensiveArgonAuditVerdict.model_validate_json(response.text)

    print("\n" + "=" * 80)
    print("AUDITORÍA FORENSE AVANZADA: GEMINI-4-ARGON (REVISIÓN DE CÓDIGO)")
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
            print(f"[{idx}] {f.file_path}:{f.line_number} [{f.category}] (Severity: {f.severity})")
            print(f"    Critique: {f.technical_critique}")
            print(f"    Required Fix: {f.mandatory_fix}")
            print()
    else:
        print("CERTIFICACIÓN: Cero defectos encontrados. El código cumple al 100% con todos los mandatos.")

    print("=" * 80)


if __name__ == "__main__":
    main()
