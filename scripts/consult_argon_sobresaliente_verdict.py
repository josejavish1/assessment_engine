#!/usr/bin/env python3
"""Ask gemini-4-argon whether the 4 bug fixes alone achieve an outstanding (>8.5/10) grade across all towers, or what else is missing."""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, and Master of Multi-Tenant Global Platforms.

USER QUESTION (CRITICAL ANTI-SYCOPHANCY CHECK):
"¿Con eso conseguiríamos un sobresaliente en todas las torres para todas las empresas del mundo?"
(With those 4 bug fixes, would we achieve an 'outstanding' [sobresaliente / >8.5/10] in all towers for all companies in the world?)

BE RUTHLESSLY, 100% HONEST. NO FLATTERY. NO FALSE REASSURANCE.
Answer this directly:
1. Would the 4 code bug fixes alone (import re, KeyError formatting, regex relaxation, silo restriction) elevate the Tribunal grades from 5.4/10 to a true 'Sobresaliente' (>8.5/10)?
2. If NOT, why not? What are the EXACT remaining substantive reasons why world-class auditors (like the 10 top-tier experts) would still refuse to give a 9/10 or Sobresaliente?
3. Detail the exact 3 or 4 substantive dimensions beyond code syntax that must be calibrated:
   - For example: P90 recovery time realism (e.g. 23 hours for catastrophic ransomware in T6 vs 2-3 weeks).
   - For example: Macroeconomic financial materiality (justifying the CAPEX business case for a 1.14B€ company).
   - For example: Workplace metrics tailored to factory workers vs software engineers in T9.
   - For example: CMMI score vs technical text coherence (e.g. PAM scored 4.50 while text describes shared root passwords).
4. Provide the definitive roadmap to achieve an authentic, unassailable 9.0/10 Sobresaliente across any enterprise.

Respond in 100% Technical English with supreme executive authority and unflinching truthfulness.
"""

def main() -> None:
    print(f"Submitting Sobresaliente Feasibility Inquiry to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    ruling = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_SOBRESALIENTE_FEASIBILITY_VERDICT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(ruling, encoding="utf-8")

    print(f"\nVerdict written to: {out_file}\n")
    print("=" * 80)
    print(ruling[:3500])
    if len(ruling) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
