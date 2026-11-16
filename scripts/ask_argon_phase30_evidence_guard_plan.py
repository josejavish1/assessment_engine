#!/usr/bin/env python3
"""
Invoke gemini-4-argon to architect the Phase 30 Master Implementation Blueprint for True Epistemic Evidence Gating.

Addresses the remaining generative defects from Delivery 19 and the catastrophic failure of post-generation regex sanitizers:
1. KPI-to-Claim Alignment Error (T1 CCTV, T6 PAM): Prevent specific technical failing generation from unrelated/generic KPIs.
2. Technical Specificity Hallucination (T3 Network, T4 Storage, T9 Workplace): Prevent invention of specific protocols/features without transcript evidence.
3. Grammatical Degradation: Eradicate post-generation regex text replacement (LexicalEpistemicSanitizer/TechnicalSpecificityGuard) which resulted in broken grammar and duplicated nouns (e.g., "conmutadores de núcleo equipamiento de conmutación de red").
4. Tower Context Contamination (T8): Stop hardware inventory leakage into governance towers upstream.
5. SharedFactRegistry Authority: Ensure 'UNKNOWN' facts (like vCPU oversubscription and '3 and 4' ambiguity) are canonically respected and prevent the LLM from inventing severity levels.

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

def request_argon_phase30_master_plan() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: PHASE 30 TRUE EPISTEMIC EVIDENCE GATING BLUEPRINT")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are Gemini-4-Argon, Global Chief Systems Architect, Principal Compiler Engineer, and Fellow of the Society of Actuaries.

MANDATE & OBJECTIVE:
We have successfully stabilized the actuarial mathematics (Scoring Engine, FAIR TEF classification, missing values, layout). Our Tier-1 auditor's review of Delivery 19 confirmed these components are 100% stable.

However, our previous attempts to solve Evidence Gating (Phase 27-29) were a structural failure. We attempted to use post-generation regex replacements (LexicalEpistemicSanitizer and TechnicalSpecificityGuard) to scrub hallucinated terms (e.g. replacing "SimpliVity" with "infraestructura hiperconvergente"). This caused severe grammatical degradation and noun duplication in the final Spanish DOCX (e.g. "conmutadores de núcleo equipamiento de conmutación de red"). 

The auditor has mandated that we STOP post-processing text. The guard must function BEFORE redaction: `unsupported claim -> does not enter the prompt`, NOT `invented claim -> attempt to soften words later`.

We need a Master Implementation Blueprint to permanently eradicate these remaining evidence discipline failures:

1. KPI-TO-CLAIM ALIGNMENT: A low survey score on "vendor management" generated a finding about "CCTV blind spots". This is unacceptable.
2. TECHNICAL SPECIFICITY HALLUCINATION: T4 invents NetApp CSI/WORM. T6 invents centralized PAM vaults and session recording from a generic PAM maturity score. T9 invents SAML 2.0 and RODC. T3 invents physical pathway diversity.
3. SHARED FACT AUTHORITY: When vCPU oversubscription is `UNKNOWN`, the LLM still generates "severe oversubscription" based on memory pressure.
4. TOWER CONTEXT CONTAMINATION: Tower 8 (Governance) is still receiving and regurgitating hardware inventory (SimpliVity, NetApp, SCADA).

THE REQUIRED ARCHITECTURAL SHIFT:
You must design a purely deterministic, 100% code-driven UPSTREAM architecture. 
- Eliminate all post-generation regex text replacements.
- Enforce strict Epistemic Evidence Gating BEFORE the LLM prompt is assembled.
- If a capability lacks empirical transcript citations, the system must structurally restrict the payload fed to the LLM or enforce a strict JSON Schema (Discriminated Unions) that physically prevents the LLM from outputting technical implementation fields, forcing a process-governance-only response.
- Everything must be universally scalable across any enterprise vertical globally.
- ZERO hardcoding. ZERO Spanish logic in the Python source code. 100% Technical English.

YOUR DELIVERABLE:
Write an exhaustive, high-signal, publication-grade MASTER IMPLEMENTATION BLUEPRINT in Markdown format to be saved at `docs/architecture/ARGON_PHASE30_UPSTREAM_EVIDENCE_GATING_BLUEPRINT.md`.

Structure your blueprint into:
1. EXECUTIVE SUMMARY & EPISTEMIC PARADIGM SHIFT (Why post-generation regex fails and why upstream gating is the Tier-1 standard).
2. DETAILED PHASED IMPLEMENTATION STRATEGY:
   - Phase 30.1: Dismantling the Post-Generation Sanitizers (Removing TechnicalSpecificityGuard text replacement).
   - Phase 30.2: Upstream Context Filtration & Strict Payload Isolation (Fixing T8 cross-contamination definitively).
   - Phase 30.3: The Ontology-Bound Claim Compiler (OBCC) / Polymorphic Schema Enforcement (Using Pydantic Discriminated Unions to restrict JSON fields for unaccredited KPIs, forcing 'Capability-Only Mode').
   - Phase 30.4: Shared Fact Three-Valued Logic Pre-emption (Structurally preventing UNKNOWN facts like vCPU from reaching the LLM as actionable risks).
3. ARCHITECTURAL CONTRACTS (Define the updated Pydantic models or JSON configurations, demonstrating the Discriminated Union pattern).
4. VERIFICATION ORACLES (Deterministic invariant testing criteria to ensure zero regressions).

CORE INVARIANTS:
- 100% Technical English. Zero Spanish in the architecture design.
- Zero sycophancy: deliver brutal, unvarnished, high-signal engineering truth.
"""

    print("Sending prompt to Gemini-4-Argon for Phase 30 Master Blueprint...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=16000,
        ),
    )

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_PHASE30_UPSTREAM_EVIDENCE_GATING_BLUEPRINT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Master Blueprint successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    request_argon_phase30_master_plan()
