"""Consult gemini-4-argon for a foolproof, safe execution plan to implement the 3-Layer Actuarial Architecture."""

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

PROMPT = """You are 'gemini-4-argon', Lead Adversarial Red Team Chief Architect (SR 11-7 / Open FAIR / Basel III / Solvency II).

We have established the 3-Layer Master Architecture in `docs/audits/RED_TEAM_UNIVERSAL_ACTUARIAL_MASTER_PLAN.md` to permanently solve the actuarial distortion in capability cards (e.g., T6-RVS02 PAM 3k EUR vs 198k EUR, T2-RVS03/04 K8s Lab 74k EUR vs 0 EUR revenue loss, T3-RVS04 backhoe fiber cut vs fake GDPR fines, T4-RVS02 / T10-RVS04 15-min disk cleanup vs 8-hr outage).

The user explicitly rejected any sloppy "defensive fallbacks" that silently revert to broken defaults when tags are missing. The implementation must follow:
- ZERO WORKAROUNDS (Fail-Closed contract).
- Ingestion must enrich or validate environment (`PROD_CRITICAL`, `PROD_SUPPORT`, `STAGING_UAT`, `LAB_DEV_TEST`) and role (`CONTROL_PLANE`, `DATA_PLANE`, etc.) deterministically with an immutable audit trail.
- ZERO blind defaults (purge `default_rto_hours=8.0` and arbitrary blast radiuses).
- Universal validity across any vertical (Hospitals, Banks, Factories, SaaS).
- 100% Technical English in `src/`.
- Zero regressions on existing test suites and contiguous Word annexes.

DELIVERABLE REQUIRED:
Produce the definitive, step-by-step FOOLPROOF EXECUTION PLAN:
1. Phase Breakdown (Phase 1 to Phase N) with exact file paths in `src/assessment_engine/` and `engine_config/`.
2. Fail-closed schema enforcement & deterministic topology enricher logic.
3. Mathematical implementation details for the continuous beta buffer attenuation and bow-tie control-plane escalation.
4. Testing & Validation Strategy (Exact Pytest oracles, property-based tests, and regression invariants).
5. Rollback & Safety Gates.

Provide the response in clean, authoritative Markdown.
"""

print(f"Submitting Execution Plan Request to {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=PROMPT,
)

out_file = REPO_ROOT / "docs" / "audits" / "FOOLPROOF_ACTUARIAL_IMPLEMENTATION_PLAN.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"Plan generated successfully: {len(response.text)} chars written to {out_file.relative_to(REPO_ROOT)}")
