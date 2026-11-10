#!/usr/bin/env python3
"""Consult gemini-4-argon to conduct a comprehensive adversarial review of recent code changes."""

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

# Gather git diff for src/ and engine_config/
try:
    diff_proc = subprocess.run(
        ["git", "diff", "HEAD~1", "--", "src/assessment_engine/", "engine_config/"],
        capture_output=True,
        text=True,
        check=True,
    )
    git_diff = diff_proc.stdout
    if not git_diff.strip():
        # Fallback to unstaged diff
        diff_proc = subprocess.run(
            ["git", "diff", "--", "src/assessment_engine/", "engine_config/"],
            capture_output=True,
            text=True,
            check=True,
        )
        git_diff = diff_proc.stdout
except Exception as e:
    git_diff = f"Failed to gather git diff: {e}"

# Read newly added continuous_risk_allocator.py
allocator_code = (
    (REPO_ROOT / "src/assessment_engine/domain/actuarial/continuous_risk_allocator.py").read_text(
        encoding="utf-8"
    )
    if (REPO_ROOT / "src/assessment_engine/domain/actuarial/continuous_risk_allocator.py").exists()
    else ""
)

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

AUDIT_PROMPT = f"""You are 'gemini-4-argon', Principal Enterprise Architect, Supreme Code Quality Arbiter, and Chief Forensic Software Engineer for the Assessment Engine.

USER DIRECTIVE:
"haz una revisión completa de lo que acabas de programar y busca bugs, problemas o antipatrones, no quiero nada hardcodeado recuerda que el objetivo es que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial, de cualquier vertical, en cualquier idioma, y el código debe estar 100% en inglés nada de español ni una sola palabra. Y lo más importante: que el código permita escalar a las 100 empresas que tenemos a ver si vamos a tener cosas que cuando probemos con las 100 empresas que tenemos van a fallar."

CODE UNDER AUDIT:
=== NEW MODULE: continuous_risk_allocator.py ===
{allocator_code}

=== GIT DIFF (Recent modifications across src/ and engine_config/) ===
{git_diff[:25000]}

AUDIT MANDATES TO EXAMINE UNCOMPROMISINGLY:
1. ZERO HARDCODING LAW: Are there ANY hardcoded client names ('Molins', 'SECIL', etc.), vendor brands ('Broadcom', 'SimpliVity'), fixed currency symbols ('€', '$'), or company-specific turnover/burn rates in Python code?
2. LANGUAGE DECOUPLING LAW: Is the Python codebase 100% in Technical English? Are there ANY Spanish words in code, docstrings, comments, variable names, exception messages, logs, or regex literals? (Spanish is ONLY permitted as runtime data in locales.json).
3. SCALE INVARIANCE & 100-ENTERPRISE CRUCIBLE: Can this code scale seamlessly from a €5M SME to a €150B conglomerate? Will it crash on zero revenue, zero findings, single finding, 100 findings, or edge-case Likert scores?
4. MATHEMATICAL INTEGRITY & ACTUARIAL SOUNDNESS: Does ContinuousRiskAllocator guarantee exact closed-form closure (Hare-Niemeyer largest remainder)? Are there any division-by-zero risks or floating-point drift?
5. IDENTIFICATION OF HIDDEN ANTIPATTERNS OR DEFECTS: What subtle bugs, race conditions, or architectural smells still lurk in this implementation?

Deliver your complete adversarial audit report. Be ruthless, objective, and definitive. Respond in 100% Technical English.
"""

print(f"Calling cognitive arbiter ({model_name})...")
response = client.models.generate_content(
    model=model_name,
    contents=AUDIT_PROMPT,
)

report_text = response.text or ""
out_path = REPO_ROOT / "docs/audits/ARGON_ADVERSARIAL_CODE_AUDIT_REPORT.md"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(report_text, encoding="utf-8")

print(f"✓ Adversarial Audit Report written to: {out_path.resolve()}\n")
print(report_text[:2500])
