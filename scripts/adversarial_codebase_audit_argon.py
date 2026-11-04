#!/usr/bin/env python3
"""Execute full adversarial audit with gemini-4-argon on recent code changes.

Audits:
- src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py
- src/assessment_engine/application/generate_global_radar_chart.py
- engine_config/locales.json (recent keys)

Enforces:
1. Multi-Tenant Scalability: Must serve any enterprise worldwide (mid-market to Top Tier-1, any vertical, any currency).
2. Zero Hardcoding: No hardcoded client names (Molins, Secil), monetary values, or tenant assumptions.
3. 100% Technical English Codebase: Zero Spanish in Python code, comments, docstrings, or symbols.
4. Clean Architecture & Anti-Pattern Detection.
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


def read_file_safe(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return f"[File {path.name} not found]"


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    compiler_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py"
    )
    radar_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/application/generate_global_radar_chart.py"
    )

    prompt = f"""
Role: Principal Enterprise Systems Architect, Lead Code Auditor for Global Multi-Tenant Platforms, and Hardcore Quality Gatekeeper.

MISSION:
Execute an uncompromising, adversarial forensic code review of recent changes in the Assessment Engine repository. The user has specifically requested an exhaustive audit to catch ANY bug, anti-pattern, hardcoding, or language leakage.

MANDATORY LAWS & VERIFICATION CRITERIA:
1. Zero Hardcoding & Universal Multi-Tenancy:
   - The platform MUST serve ANY enterprise in the world, from mid-market ($50M) to Top Tier-1 global conglomerates ($50B+), across ANY vertical (heavy manufacturing, banking, healthcare, retail, public sector), in ANY currency (USD, EUR, JPY, GBP), and in ANY language (es, en, pt, fr, de, ja).
   - Zero hardcoded client names (e.g., "Molins", "Secil", "Cempro", "Sant Vicenç").
   - Zero hardcoded monetary values, downtime rates, or fixed incident dollar amounts in Python logic.
   - All financial parameters must be dynamically derived from tenant payloads (`financial_telemetry`, `global_payload`, `tower_payloads`) or closed-form parametric formulas based on revenue.
2. 100% Technical English Codebase:
   - Zero Spanish words in Python code (no Spanish variable names, function names, docstrings, comments, log messages, or exception strings).
   - Spanish (and pt, fr, de, ja) is strictly data localized within `engine_config/locales.json`.
3. Architectural Cleanliness & Anti-Pattern Detection:
   - Audit for any script proliferation, file collision risks, zip-slip vulnerabilities, or brittle regex matching.
   - Audit Table 2 and Chapter 2 maturity model to ensure no legacy fake benchmarks or broken references remain.
   - Audit Table 4 and Chapter 3 actuarial calculations to guarantee closed-form conservation without integer rounding errors.

SOURCE CODE UNDER AUDIT:

--- FILE 1: `src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py` ---
{compiler_code}

--- FILE 2: `src/assessment_engine/application/generate_global_radar_chart.py` ---
{radar_code}

YOUR ADVERSARIAL REPORT MUST DELIVER:
1. Executive Verdict & Overall Code Quality Score (0 to 10).
2. Forensic Finding Log (categorized by Critical, High, Medium, Low):
   - Pinpoint line numbers, file paths, and exact problematic expressions.
   - Detail any tenant leakage, hardcoding, or non-English impurities found.
3. Specific Code Remediation Instructions:
   - Provide exact before-and-after replacements for any defect found.
"""

    print(f"Requesting full adversarial code audit from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/ARGON_FULL_ADVERSARIAL_AUDIT_REPORT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Successfully generated adversarial audit report: {out_file}")


if __name__ == "__main__":
    main()
