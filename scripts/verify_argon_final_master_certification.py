#!/usr/bin/env python3
"""Run final master verification audit with gemini-4-argon on hardened codebase."""

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

OUTPUT_FILE = REPO_ROOT / "docs/audits/ARGON_FINAL_MASTER_CERTIFICATION.md"

COPULA_ENGINE = (REPO_ROOT / "src/assessment_engine/domain/bayesian_fair_copula_engine.py").read_text(encoding="utf-8")
SCORE_RECONCILER = (REPO_ROOT / "src/assessment_engine/domain/services/score_reconciler.py").read_text(encoding="utf-8")
SYNC_SCORES = (REPO_ROOT / "src/assessment_engine/application/sync_payload_scores.py").read_text(encoding="utf-8")
RESYNTH_DOMAINS = (REPO_ROOT / "scripts/resynthesize_domains_from_raw_transcription.py").read_text(encoding="utf-8")
TEST_INVARIANTS = (REPO_ROOT / "tests/integration/test_scoring_ssot_invariants.py").read_text(encoding="utf-8")

PROMPT = f"""You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect and Chief Quality Gatekeeper.

Review the 5 specific hardenings applied to address your previous feedback:
1. Hardcoded Tenant Name Leak: Cleaned in `resynthesize_domains_from_raw_transcription.py` (replaced with generic `acme_corp`), `vertical_id` parameter wired from CLI.
2. Actuarial Constant Promotion: Promoted `spof_cmmi_penalty`, `max_dependence_loading`, `max_copula_correlation`, `rto_cmmi_degradation_slope`, and `rto_spof_multiplier` to `BayesianFairCopulaEngine.__init__` with fully typed defaults.
3. Strict Weight Sum Validation: Added explicit check in `_resolve_ssot_pillar_weights` requiring `total_raw` to sum to unity (1.0 within 0.001) or percentage (100.0 within 0.1), raising `QuantitativeSplitBrainError` immediately if malformed.
4. Clean CI Runner Guard: Protected `test_scoring_ssot_invariants.py` with empty discovery guard (`test_active_payloads_discovery_guard` and `skipif(len(ACTIVE_PAYLOADS) == 0)`).
5. Dynamic KPI Code Depth: In `sync_payload_scores.py::parse_raw_responses`, strip trailing question token via regex `re.match(r'^(PR|Q|QUESTION)\d+$', tokens[-1])` to support arbitrary deep KPI hierarchies.

FILES:

--- ARTIFACT 1: src/assessment_engine/domain/bayesian_fair_copula_engine.py ---
{COPULA_ENGINE}

--- ARTIFACT 2: src/assessment_engine/domain/services/score_reconciler.py ---
{SCORE_RECONCILER}

--- ARTIFACT 3: src/assessment_engine/application/sync_payload_scores.py ---
{SYNC_SCORES}

--- ARTIFACT 4: scripts/resynthesize_domains_from_raw_transcription.py ---
{RESYNTH_DOMAINS}

--- ARTIFACT 5: tests/integration/test_scoring_ssot_invariants.py ---
{TEST_INVARIANTS}

Provide:
1. Final Executive Verdict (PASS / FAIL) and Numerical Score (0.0 to 10.0).
2. Verification Checklist of the 5 Hardenings.
3. Final Architectural Certification.
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Executing final master verification audit via gemini-4-argon ({model})...")

    response = client.models.generate_content(
        model=model,
        contents=PROMPT,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"Certification saved at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON FINAL MASTER CERTIFICATION:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:60]:
        print(line)
    if len(lines) > 60:
        print(f"... ({len(lines) - 60} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
