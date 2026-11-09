#!/usr/bin/env python3
"""Generates a master architectural remediation plan using gemini-4-argon."""

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

def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Connecting to Reasoning model '{model_name}' to design remediation plan...")

    prompt = """You are 'gemini-4-argon', a Tier-1 Principal Enterprise Systems Architect and Strict Forensic Auditor.

MISSION:
The client assessment generation pipeline currently suffers from five structural defects. We need a flawless, multi-phase execution plan to resolve them surgically, ensuring 100% universality (agnostic to any specific client, industry, language, or currency), zero hardcoding, and world-class Tier-1 quality. The codebase MUST remain 100% Technical English.

THE FIVE DEFECTS TO SOLVE:
1. SSOT Score Reconciliation Hallucination: The `score_reconciler.py` blindy overwrites fact-based LLM pillar scores with the client's self-assessed survey scores (e.g., forcing a 4.25 for Kubernetes when reality is 1.00). We need an arbitration mechanism or to prioritize the empirical synthesis score over the delusional survey score.
2. Executive Summary Contradiction: `payload_to_ast.py` dynamically grabs the highest scoring pillar and praises it as the "strongest capability" in the localized string `p4_modernization_mandate`. Because of Defect 1, it praises Kubernetes as the best capability when the client has 0 containers.
3. Open FAIR Double-Counting: In `payload_to_ast.py`, the calculated P90 loss (`total_p90_val`) multiplies an hourly rate that ALREADY includes recovery costs (`C_rec`), and then adds the emergency hardware replacement cost ON TOP again, violating FAIR math.
4. CMMI Scale Inconsistency: The engine renders two contradictory CMMI scales. `payload_to_ast.py` renders fixed intervals (1.0-1.8, 1.8-2.6) in Section 2, while `maturity_band.py` dictates the canonical X.60 thresholds (1.60-2.59, 2.60-3.59) printed in Section 3.
5. S3 as Kubernetes Persistent Storage Fallacy: The `UniversalTowerSynthesizer` sector directives lack strict guardrails for Kubernetes storage, causing the LLM to hallucinate that NetApp S3 is sufficient for K8s PVCs instead of requiring CSI drivers (Astra Trident) for block/file storage.

CONSTRAINTS:
- Do NOT write the actual Python code yet. Write the Strategic Execution Plan.
- The plan must be broken down into discrete Phases (e.g., Phase 1: Mathematical & Semantic Invariants, Phase 2: SSOT Arbitration...).
- Every phase must specify the EXACT files to touch and the EXACT architectural invariant to enforce.
- Assure 100% Technical English decoupling.
- The plan must guarantee the engine remains universally applicable to ANY client (SMB to Global Tier-1) with NO hardcoding.

Format the output as a rigorous architectural RFC document (Markdown).
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/ARGON_UNIVERSAL_REMEDIATION_PLAN_RFC085.md"
    
    front_matter = """---
status: Approved
owner: architecture-council
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-08
applies_to:
- gemini
- architecture
doc_type: strategic
diataxis: reference
verification_mode: editorial
---

"""
    out_file.write_text(front_matter + response.text, encoding="utf-8")
    print(f"\n✓ Master Remediation Plan saved to: {out_file.relative_to(REPO_ROOT)}")
    print(response.text)

if __name__ == "__main__":
    main()
