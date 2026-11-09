#!/usr/bin/env python3
"""Execute an exhaustive, comprehensive adversarial audit with gemini-4-argon across the entire newly programmed subsystem."""

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

OUTPUT_FILE = REPO_ROOT / "docs/audits/ARGON_COMPREHENSIVE_SESSION_AUDIT.md"

COPULA_ENGINE = (REPO_ROOT / "src/assessment_engine/domain/bayesian_fair_copula_engine.py").read_text(encoding="utf-8")
SCORE_RECONCILER = (REPO_ROOT / "src/assessment_engine/domain/services/score_reconciler.py").read_text(encoding="utf-8")
MATH_INTEGRITY = (REPO_ROOT / "src/assessment_engine/domain/validation/mathematical_integrity.py").read_text(encoding="utf-8")
SYNC_SCORES = (REPO_ROOT / "src/assessment_engine/application/sync_payload_scores.py").read_text(encoding="utf-8")
HYDRATOR_ACTUARIAL = (REPO_ROOT / "src/assessment_engine/application/services/tower_payload_hydrator.py").read_text(encoding="utf-8")[130:2600]
BLUEPRINT_PHASE81 = (REPO_ROOT / "src/assessment_engine/application/run_tower_blueprint_engine.py").read_text(encoding="utf-8")[1250:1330]
RESYNTH_DOMAINS = (REPO_ROOT / "scripts/resynthesize_domains_from_raw_transcription.py").read_text(encoding="utf-8")
TEST_COPULA = (REPO_ROOT / "tests/unit/test_bayesian_fair_copula_engine.py").read_text(encoding="utf-8")
TEST_RECONCILER = (REPO_ROOT / "tests/unit/test_score_reconciler.py").read_text(encoding="utf-8")
TEST_INVARIANTS = (REPO_ROOT / "tests/integration/test_scoring_ssot_invariants.py").read_text(encoding="utf-8")

PROMPT = f"""You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect, Lead Actuarial Auditor, and Chief Quality Gatekeeper.

Perform an UNCOMPROMISING, BRUTALLY ADVERSARIAL MASTER AUDIT of the entire subsystem engineered during this session:
- Open FAIR™ Bayesian Copula Risk Engine
- Deterministic Quantitative State Reconciler & Invariant Gatekeeper
- Dynamic Topology Synchronizer & Resynthesis Orchestrator
- Phase 8.1 Pipeline Gatekeeping
- Automated Test Suites (Unit + Integration)

THE USER'S MANDATES FOR THIS AUDIT:
1. LANGUAGE DECOUPLING LAW:
   - All code, variable names, function signatures, docstrings, comments, exceptions, logs, and tests MUST be 100% Technical English.
   - ZERO SPANISH WORDS in the code! Spanish is strictly reserved for the human user conversation in chat and client delivery templates (via locales.json). Check every identifier, comment, and log string.
2. ZERO HARDCODED NUMBERS & VERTICAL/TENANT AGNOSTICISM:
   - The engine must work seamlessly for ANY company in the world (from a $20M mid-market firm to a $500B Fortune 10 global conglomerate).
   - The engine must work for ANY vertical (Banking, Healthcare, Retail, Technology, Heavy Manufacturing, Public Sector).
   - The topology must support any number of domains/towers (not hardcoded to T1..T10; support D1..D8, custom domain slugs, etc.) and any N-pillar topology with arbitrary valid weights.
   - Multi-currency support across any global ISO currency code (USD, EUR, GBP, JPY, CHF, CAD, etc.).
3. MATHEMATICAL & ALGORITHMIC RIGOR:
   - Identify bugs, edge cases (empty lists, division by zero, non-finite numbers, floating point drift, unhandled exceptions, race conditions, atomic persistence), performance traps, or anti-patterns.

CODE ARTIFACTS UNDER AUDIT:

--- ARTIFACT 1: src/assessment_engine/domain/bayesian_fair_copula_engine.py ---
{COPULA_ENGINE}

--- ARTIFACT 2: src/assessment_engine/domain/services/score_reconciler.py ---
{SCORE_RECONCILER}

--- ARTIFACT 3: src/assessment_engine/domain/validation/mathematical_integrity.py ---
{MATH_INTEGRITY}

--- ARTIFACT 4: src/assessment_engine/application/sync_payload_scores.py ---
{SYNC_SCORES}

--- ARTIFACT 5: Excerpt of compute_canonical_score & Copula in tower_payload_hydrator.py ---
{HYDRATOR_ACTUARIAL}

--- ARTIFACT 6: Phase 8.1 Gatekeeper in run_tower_blueprint_engine.py ---
{BLUEPRINT_PHASE81}

--- ARTIFACT 7: scripts/resynthesize_domains_from_raw_transcription.py ---
{RESYNTH_DOMAINS}

--- ARTIFACT 8: tests/unit/test_bayesian_fair_copula_engine.py ---
{TEST_COPULA}

--- ARTIFACT 9: tests/unit/test_score_reconciler.py ---
{TEST_RECONCILER}

--- ARTIFACT 10: tests/integration/test_scoring_ssot_invariants.py ---
{TEST_INVARIANTS}

YOUR TASK:
Provide an exhaustive, brutally honest master audit report:
1. Executive Verdict (PASS / REVISE / FAIL) with numerical score (0.0 to 10.0).
2. Forensic Inventory of Defects:
   - Language Purity violations (List exact line numbers and Spanish words if any).
   - Hardcoding & Tenant/Topology Bias (List any residual hardcoded assumptions).
   - Mathematical & Algorithmic edge cases or bugs.
3. Verification of Universal Multi-Tenant Enterprise Readiness.
4. Architectural Certification for Production Deployment.
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Executing Master Adversarial Audit via gemini-4-argon ({model})...")

    response = client.models.generate_content(
        model=model,
        contents=PROMPT,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"Master audit report saved at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON MASTER AUDIT SUMMARY:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
