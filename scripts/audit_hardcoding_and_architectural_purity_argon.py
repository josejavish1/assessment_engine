#!/usr/bin/env python3
"""Zero-Mercy Adversarial Audit on Hardcoding and Architectural Purity via gemini-4-argon."""

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

    prompt = """
Role: Principal Enterprise Systems Architect, Zero-Trust Code Auditor, and Staff Infrastructure Engineer for Global Multi-Tenant Platforms.

MISSION:
Execute an uncompromising, adversarial forensic audit of recent code in `tomo_asis_ast_compiler.py` and localization catalogs to hunt down and eradicate ALL hardcoded constants, numerical literals, tenant assumptions, and language couplings.

THE CRITICAL PROBLEM IDENTIFIED:
Recent changes introduced severe hardcoded numbers, constants, and client assumptions directly inside compiler code:
1. Hardcoded Corporate Values:
   - Line 333: `916416.0` hardcoded as corporate ALE fallback.
   - Line 334: `2291040.0` hardcoded as P90 tail risk fallback.
2. Hardcoded Downtime Hourly Rates:
   - Line 445: `5000.0` hardcoded as local plant downtime rate.
   - Line 446: `13061.29` hardcoded as consolidated group downtime rate.
3. Hardcoded Domain Allocation Map:
   - Lines 730-740 & Lines 1105-1115: `[("T1", ..., 141132.0), ("T2", ..., 100806.0), ("T3", ..., 82477.0), ("T4", ..., 30242.0), ("T5", ..., 206194.0), ("T6", ..., 64149.0), ("T7", ..., 43988.0), ("T8", ..., 132880.0), ("T9", ..., 27493.0), ("T10", ..., 87055.0)]` hardcoding domain ALEs.
4. Hardcoded Major Incident Outage Figures:
   - Lines 837-843: `450000.0` total outage loss, `225548.0` direct stoppage, `224452.0` emergency recovery, and bucket breakdown `94270.0`, `74069.0`, `56113.0`.
   - Line 836: `"17,3 h" if doc_lang in ("es", "pt", "fr", "de") else "17.3 hrs"` (inline language ternary and hardcoded duration).
5. Operational Inefficiency:
   - Rebuilding the whole 50-file client suite (`build_full_client_delivery_suite.py`) every time Tomo 1 is touched wastes excessive time and compute.

INVARIANTS TO ENFORCE:
- Multi-Tenant Scale: Must scale for a 50M$ mid-market retailer in USD, a 50B¥ electronics maker in JPY, or a 5B£ utility in GBP.
- 100% Technical English Codebase: Zero Spanish in Python code (no Spanish variable names, comments, docstrings, or strings).
- Zero Hardcoded Numbers: All financials, rates, durations, and allocations MUST be derived dynamically from `financial_telemetry`, `global_payload`, and `tower_payloads` or mathematically parameterized.

YOUR ADVERSARIAL AUDIT MUST DELIVER:
1. Complete list of all hardcoded literals and anti-patterns found in the compiler.
2. The exact mathematical and data-binding blueprint to dynamically resolve:
   - Corporate ALE & P90 tail risk.
   - Local facility rate vs consolidated corporate hourly rate.
   - Single facility major incident loss, recovery duration, and emergency expense buckets.
   - Dynamic domain allocation across N domains using `ActuarialReconciler`.
3. Standalone compilation architecture for Tomo 1 only (`scripts/compile_tomo1_asis_only.py`) that compiles only Tomo 1 in <5 seconds.
4. Exact code changes required in `tomo_asis_ast_compiler.py`.
"""

    print(f"Requesting zero-mercy hardcoding audit from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/ARGON_DEEP_AUDIT_HARDCODING_AND_LANGUAGE_PURITY.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Successfully generated audit report: {out_file}")


if __name__ == "__main__":
    main()
