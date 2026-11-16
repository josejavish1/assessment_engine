#!/usr/bin/env python3
"""
Invoke gemini-4-argon to architect the Phase 27 Master Implementation Blueprint for Epistemic Evidence Gating.

Addresses the remaining generative defects from Delivery 17:
1. KPI-to-Claim Alignment Error: Hallucinating specific technical failings (e.g., CCTV) from unrelated KPIs (e.g., third-party management).
2. Technical Specificity Hallucination: Inventing specific protocols/features (BGP, WORM, WAAP) without transcript evidence.
3. Capability vs Implementation Conflation: Converting high maturity scores directly into specific commercial implementations (e.g., PAM vaults, session recording) instead of operational capabilities.
4. Tower Context Contamination: Tower 8 (Governance) inheriting unrelated hardware specifics from other towers.
5. FAIR Provenance: Requiring explicit tracking of the sources for TEF, Vulnerability, and SLE.

100% Technical English in prompt and generated blueprint.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def request_argon_phase27_master_plan() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: PHASE 27 EPISTEMIC EVIDENCE GATING BLUEPRINT")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are Gemini-4-Argon, Global Chief Systems Architect, Principal Compiler Engineer, and Fellow of the Society of Actuaries.

MANDATE & OBJECTIVE:
We have successfully stabilized the actuarial mathematics (Scoring Engine, FAIR TEF classification, pure SLE/ALE derivations). However, our Tier-1 auditor's review of Delivery 17 exposed severe remaining defects in the Epistemic Control Plane. The LLM's generative freedom is still substituting verified reality with plausible hallucinations.

We need a Master Implementation Blueprint to permanently eradicate these five failure modes:

1. KPI-TO-CLAIM ALIGNMENT ERROR: The generator infers concrete physical implementations from unrelated survey scores. Example: A low score (1.0) on "Third-Party Vendor Management" was used by the LLM to hallucinate "CCTV with blind spots and NVRs with <30 days retention."
2. TECHNICAL SPECIFICITY HALLUCINATION: The LLM continues to inject unverified protocols, hardware mechanisms, and features (e.g., BFD, BGP routing, NetApp CSI, WORM, deduplication, SFP+) that do NOT exist in the audio transcripts.
3. CAPABILITY VS IMPLEMENTATION CONFLATION: High survey scores (e.g., PAM = 4.50) are being translated into unverified commercial implementations (e.g., "centralized CyberArk vault, automatic password rotation, keystroke logging") instead of mature capability governance.
4. TOWER CONTEXT CONTAMINATION: Governance and FinOps (Tower 8) is re-interpreting hardware nodes (SimpliVity, ESXi, NetApp) from other towers instead of receiving strictly filtered decision-oriented facts (portfolio decisions, licensing renewals).
5. FAIR PROVENANCE OBFUSCATION: The strategic risk cards lack explicit, traceable provenance fields identifying exactly where the TEF, Vulnerability, and SLE parameters originated.

THE REQUIRED ARCHITECTURAL SHIFT:
You must design a purely deterministic, 100% code-driven architecture (Zero-Prompt-Reliance). 
- Do not rely on telling the LLM "do not hallucinate" or "be careful".
- We need structural pre-generation filtering, strict payload reduction (TowerContextBuilder semantic filtering), and strict post-generation AST enforcement.
- Everything must be universally scalable across any enterprise vertical globally.
- ZERO hardcoding. ZERO Spanish logic. 100% Technical English.

YOUR DELIVERABLE:
Write an exhaustive, high-signal, publication-grade MASTER IMPLEMENTATION BLUEPRINT in Markdown format to be saved at `docs/architecture/ARGON_PHASE27_EVIDENCE_GATING_BLUEPRINT.md`.

Structure your blueprint into:
1. EXECUTIVE SUMMARY & EPISTEMIC PARADIGM SHIFT.
2. DETAILED PHASED IMPLEMENTATION STRATEGY:
   - Phase 27.1: KPI Semantic Bounding (Restricting claim scope strictly to the KPI definition).
   - Phase 27.2: Transcript Evidence Hard-Lock (Forbidding specific protocols/features without explicit regex/semantic hits in transcript).
   - Phase 27.3: Tower Context Filtration (Strict payload isolation for T8/Governance).
   - Phase 27.4: FAIR Provenance Schema (Enforcing `tef_source`, `vuln_source`, `sle_source` in technical risk cards).
3. ARCHITECTURAL CONTRACTS (Updated Python schemas, AST changes).
4. VERIFICATION ORACLES (Deterministic invariant testing criteria).

CORE INVARIANTS:
- 100% Technical English. Zero sycophancy. Zero conversational filler.
"""

    print("Sending prompt to Gemini-4-Argon for Phase 27 Master Blueprint...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=16000,
        ),
    )

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_PHASE27_EVIDENCE_GATING_BLUEPRINT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Master Blueprint successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    request_argon_phase27_master_plan()
