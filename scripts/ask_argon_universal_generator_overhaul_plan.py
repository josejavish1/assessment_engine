#!/usr/bin/env python3
"""
Invoke gemini-4-argon to architect the Definitive Universal Generator Engine Overhaul Master Plan.

Addresses the 10 structural generator defects contaminating all 10 domain towers:
1. 100% deterministic scoring from official master matrices across T1..T10.
2. Official project maturity scale alignment (1.00-1.79, 1.80-2.59, 2.60-3.39, 3.40-4.19, 4.20-5.00).
3. Raw verbatim evidence retrieval by KPI (no lossy summaries).
4. Real Evidence Ledger with explicit validation states (Exploratory / Contrasted / Evidenced).
5. Explicit contradiction preservation (flagging 'Contradictory Sources' instead of force-resolving).
6. Factual parsimony prompt engine (zero generative inflation or hallucinated enterprise tooling).
7. Strict cross-tower ownership and inventory deduplication.
8. Traceable Open FAIR with transparent parameter provenance.

Adheres strictly to the user's operational standards:
1. 100% Technical English prompt and generated documentation.
2. Multi-phase phased implementation plan with strict Quality Gates.
3. Universal scalability and zero hardcoding (multi-tenant agnostic).
4. Pure Clean Architecture.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def generate_generator_overhaul_master_plan() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: UNIVERSAL GENERATOR ENGINE OVERHAUL MASTER PLAN")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are Gemini-4-Argon, Chief Systems Architect, Actuarial Fellow, and Global Managing Partner for Enterprise Due Diligence.

MANDATE & CONTEXT:
A cross-tower forensic review evaluated our 10-tower delivery suite. The audit reached a fundamental conclusion:
"You do not have ten badly generated towers. You have a generator that is visually and narratively strong, but poisoned by several architectural defects that systematically contaminate all ten towers. Stop doing manual iterative rounds on Tower 2! Fix the generator engine structurally at the baseline: master matrix scoring -> 100% deterministic code -> raw evidence retrieval by KPI -> evidence ledger -> explicit contradiction management -> factual parsimony -> cross-tower ownership -> traceable FAIR. Then regenerate the entire 10-tower suite once cleanly."

THE 10 STRUCTURAL GENERATOR DEFECTS TO SOLVE:

1. DETERMINISTIC MASTER MATRIX SCORING (ALL 10 TOWERS):
   - Flaw: Tower definitions fell back to flat 20/20/20/20/20 weights in T4, T5, T6, T7, T8, T9, T10, ignoring official master matrices (e.g. T1: 24/20/16/22/18; T5: 18/22/22/20/18; T6: 21/24/19/23/13; T7: 20/22/24/21/13; T9: 22/23/19/21/15).
   - Architectural Fix: Synchronize all `tower_definition_T*.json` with their official master matrices. Enforce 100% deterministic dot-product scoring and dual-constraint integer weight formatting across all 10 towers.

2. OFFICIAL MATURITY SCALE ALIGNMENT:
   - Flaw: The engine uses legacy CMMI intervals (1.00-1.49, 1.50-2.49, etc.), causing misclassifications (e.g. T3 score 2.57 is Level 2 Basic in the official framework, but was published as Level 3 Defined).
   - Architectural Fix: Formally align `governance_scales.json`, `scale_engine.py`, and `locales.json` with the project's official 5-tier framework:
     - Level 1 - Initial: [1.00, 1.79]
     - Level 2 - Basic: [1.80, 2.59]
     - Level 3 - Standardized: [2.60, 3.39]
     - Level 4 - Optimized: [3.40, 4.19]
     - Level 5 - Advanced: [4.20, 5.00]

3. SIGNAL-TO-ARCHITECTURE HALLUCINATION (STOPPING GENERATIVE SPECULATION):
   - Flaw: Low maturity answers cause the LLM to invent concrete enterprise architecture elements (e.g. In T1: VESDA, CRAC, ATS, dual A/B power, BMS/DCIM; in T9: Zero-Touch, BitLocker, EDR, Entra ID, SAML/OIDC, SSPR, DLP).
   - Architectural Fix: Implement a strict Evidence-Constrained Architectural Synthesizer. The LLM must be forbidden from extrapolating hypothetical components from control gaps. If a control is absent, state the absence without inventing fictional infrastructure.

4. SEPARATION OF FACTUAL EVIDENCE VS INFERENCE:
   - Flaw: Real facts (dark fiber, Huawei, Equinix, GCP Amsterdam) are mixed seamlessly with invented inferences (specific VLAN/VRF IDs, BFD protocols, buffer telemetry, AWS), destroying credibility.
   - Architectural Fix: Epistemic separation in prompt directives: clearly distinguish between (a) declared client infrastructure, (b) consultant architectural inferences, and (c) unmeasured telemetry pending validation.

5. TRUE EVIDENCE LEDGER WITH VALIDATION STATES:
   - Flaw: Everything is presented as verified fact ("audited", "empirically observed"), contradicting the disclaimer.
   - Architectural Fix: Inject an explicit Evidence Ledger model into `case_input.json` and AST generation with 3 validation tiers:
     - Exploratory: Based on unverified self-assessment survey.
     - Contrasted: Confirmed in technical discovery interview.
     - Evidenced: Supported by hard configuration, telemetry, or architecture diagram.

6. CONTRADICTION PRESERVATION (STOPPING FORCED RESOLUTIONS):
   - Flaw: In T2 (K8s: survey 4.25 vs interview no prod) and T5 (failover: survey "never tested" vs interview "15-min failover"), the engine picked a side and forced a resolution.
   - Architectural Fix: When survey answers conflict with discovery interviews, the engine must NOT unilaterally overwrite the score or pick a side. It must record both data points and publish an explicit "Contradictory Sources / Pending Validation" callout.

7. STRICT CROSS-TOWER OWNERSHIP & INVENTORY ISOLATION:
   - Flaw: The same technical inventory (NetApp, Huawei, SimpliVity, SAP, Prenet, Zabbix, WSO2) is repeated indiscriminately across T3, T4, T5, T7, T8, T10, blurring domain ownership.
   - Architectural Fix: Enforce domain-orthogonal inventory filtering. Each tower prompt only receives and describes the inventory within its architectural custody:
     - T1: Physical DC facilities, power, cooling, physical security.
     - T2: Server hypervisors, VM density, compute capacity, containers.
     - T3: LAN/WAN, routing, firewalls, cloud connectivity.
     - T4: Storage arrays, SAN/NAS, block/object storage.
     - T5: Disaster recovery, replication, backup, business continuity.
     - T6: Identity, IAM/PAM, endpoint protection, compliance.
     - T7: ITSM, incident/change management, monitoring, SLAs.
     - T8: FinOps, cloud cost attribution, procurement.
     - T9: Digital workplace, end-user hardware, collaboration.
     - T10: Operational systems, OT/SCADA, plant dispatch.

8. TRACEABLE OPEN FAIR PARAMETER PROVENANCE:
   - Flaw: Reusing generic TEF and Vuln numbers across towers without explaining their source.
   - Architectural Fix: Provide transparent mathematical provenance for all 3 levers (Toil hours, Outage frequency, Contractual EoL) and document the conditional vulnerability ratio in Section 4.2.

9. DISTINGUISHING OPERATIONAL ESTIMATES FROM FORMAL COMMITMENTS:
   - Flaw: Informal interview remarks (e.g. Prenet ~3h recovery, ~15m SimpliVity failover) were transformed into "Contractual RTO" or "Automated RTO".
   - Architectural Fix: Strict terminology parser ensuring operational recovery estimates are labeled as "Operational Recovery Estimate", never as a SLA/RTO commitment unless formally documented.

10. FACTUAL PARSIMONY (QUALITY OVER DENSITY):
    - Flaw: The prompt rewarded text volume, leading to generative filler.
    - Architectural Fix: Enforce parsimonious depth: concise, authoritative, blameless, and 100% defendable engineering prose.

CORE INVARIANTS:
- 100% Technical English in code, variables, classes, docstrings, comments, logs, and prompt files.
- Zero Hardcoding: Completely multi-tenant and scale-agnostic ($50M to $100B+).
- Zero Regressions: Must pass all 47 existing architecture and actuarial tests.

YOUR DELIVERABLE:
Write a comprehensive, publication-grade MASTER ARCHITECTURAL BLUEPRINT in Markdown format to be saved at `docs/architecture/ARGON_UNIVERSAL_GENERATOR_OVERHAUL_MASTER_PLAN.md`.

Structure the plan into:
1. EXECUTIVE SUMMARY & CONSULTING MANIFESTO: Structural overhaul of the generator engine.
2. DETAILED PHASED IMPLEMENTATION STRATEGY:
   - Phase 1: Deterministic Master Matrix Baseline & Weight Harmonization (T1..T10).
   - Phase 2: Official 5-Tier Project Maturity Scale Integration.
   - Phase 3: Raw Evidence Retrieval & Evidence Ledger Pipeline (Validation States).
   - Phase 4: Epistemic Contradiction Engine (Preserving & Highlighting Divergences).
   - Phase 5: Domain Orthogonality & Cross-Tower Inventory Filtering (MECE).
   - Phase 6: Parsimonious Grounding Engine & Open FAIR Parameter Traceability.
3. SINGLE-RUN AUTONOMOUS REGENERATION PROTOCOL: How to regenerate all 10 towers cleanly.
4. QUALITY GATES & VERIFICATION ORACLES: Deterministic pytest validation suites.
"""

    print("Sending prompt to Gemini-4-Argon...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=16000,
        ),
    )

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_UNIVERSAL_GENERATOR_OVERHAUL_MASTER_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Master Plan successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    generate_generator_overhaul_master_plan()
