#!/usr/bin/env python3
"""
Invoke gemini-4-argon to architect the Phase 31 Master Implementation Blueprint.

Addresses the final 41 generative defects from Delivery 20:
- T1: diesel, epms, dcim, rpdu, pasillo, sondas, crac, esclusa, estanca
- T2: landing zone, transit gateway, golden image
- T3: vlan, sfp+, qsfp+
- T4: cifs, nfs, iscsi, qos
- T5: clean-room, bare-metal
- T6: netskope, fortinet, cis benchmark
- T7: cmdb, cab, major incident, pir, blameless, sli, slo
- T8: scada, oracle, sap, equinix (leaking from other towers)
- T9: edr, dlp, sspr
- T10: consumidores idempotentes, circuit breaker, cron

We must permanently solve Capability vs Implementation hallucination and Tower Cross-Contamination
without using post-generation regex or hardcoded word lists.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def request_argon_phase31_master_plan() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: PHASE 31 UNIVERSAL EVIDENCE GATING BLUEPRINT")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are Gemini-4-Argon, Global Chief Systems Architect, Principal Compiler Engineer, and Fellow of the Society of Actuaries.

MANDATE & OBJECTIVE:
We have successfully stabilized the mathematical engines and dismantled the post-generation regex sanitizers. 
However, the Tier-1 Auditor just rejected Delivery 20 due to 41 lingering instances of "Technical Specificity Hallucination" across the 10 towers.

When the LLM receives a generic maturity score (e.g., ITSM Score = 3) without qualitative transcript evidence, it defaults to inventing plausible industry implementations:
- T7 invents "CMDB", "CAB", "Major Incident Management", "PIR", "SLI/SLO", "blameless post-mortems".
- T1 invents "diesel generators", "CRAC units", "hot/cold aisles", "IoT sensors at 3 heights", "DCIM".
- T2 invents "Landing Zones", "Transit Gateways", "Golden Images".
- T3 invents "VLANs", "SFP+/QSFP+".
- T4 invents "CIFS/NFS/iSCSI", "QoS".
- T6 invents "Netskope", "Fortinet", "CIS Benchmarks".
- T8 (Governance) leaks specifics like "SCADA", "Oracle", "SAP", "Equinix" from other towers.

THE REQUIRED ARCHITECTURAL SHIFT:
We cannot use regex replacements or hardcoded stop-lists (e.g., prohibiting "cctv" or "vlan" manually). We need a mathematically sound, 100% scale-agnostic, and purely English upstream architecture that forces the LLM to write ONLY about operational capabilities and governance maturity when implementation specifics are absent from the evidence graph.

Your goal is to architect a multi-phase Master Implementation Blueprint to eradicate this fundamentally. 

CONSIDERATIONS:
1. UPSTREAM SEMANTIC MAPPING: How do we strictly map capability scores to abstract governance descriptions before the LLM prompt?
2. DYNAMIC ONTOLOGY: Can we use our existing JSON schemas (like `tower_definition_*.json`) to constrain the vocabulary dynamically based on empirical transcript hits?
3. POLYMORPHIC PROMPTING: How do we alter the system prompt dynamically based on the exact density of qualitative evidence for a specific pillar/KPI?
4. ZERO HARDCODING: No lists of forbidden Spanish words in the codebase. 100% Technical English.

YOUR DELIVERABLE:
Write an exhaustive, high-signal, publication-grade MASTER IMPLEMENTATION BLUEPRINT in Markdown format to be saved at `docs/architecture/ARGON_PHASE31_UNIVERSAL_EVIDENCE_GATING.md`.

Structure your blueprint into:
1. EXECUTIVE SUMMARY & EPISTEMIC PARADIGM SHIFT (Why the LLM hallucinates industry standards and how to structurally constrain its abstraction ceiling).
2. DETAILED PHASED IMPLEMENTATION STRATEGY:
   - Phase 31.1: Epistemic Density Routing (Computing the exact evidence weight of a Pillar and injecting an `abstraction_ceiling` directive into the LLM system prompt).
   - Phase 31.2: Dynamic Output Schema Polymorphism (Using Pydantic discriminated unions not just for single findings, but at the entire Pillar/Tower blueprint level).
   - Phase 31.3: Cross-Tower Semantic Shielding (Fixing T8 Governance leakage using strict Graph projection).
3. ARCHITECTURAL CONTRACTS (Define the updated Python Pydantic schemas or Prompt YAML injection strategies).
4. VERIFICATION ORACLES (Deterministic invariant testing criteria to ensure zero regressions, specifically proving that an empty transcript yields zero concrete implementation nouns).

CORE INVARIANTS:
- 100% Technical English.
- Zero sycophancy: deliver brutal, unvarnished, high-signal engineering truth.
"""

    print("Sending prompt to Gemini-4-Argon for Phase 31 Master Blueprint...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=16000,
        ),
    )

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_PHASE31_UNIVERSAL_EVIDENCE_GATING.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Master Blueprint successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    request_argon_phase31_master_plan()
