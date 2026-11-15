#!/usr/bin/env python3
"""
Invoke gemini-4-argon to architect the Phase 9: Iteration 6 Universal Factual Grounding Master Plan.

Adheres strictly to the user's operational standards:
1. 100% Technical English prompt and generated documentation.
2. Multi-phase implementation plan with strict Quality Gates.
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

def generate_iteration6_master_plan() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: ITERATION 6 FACTUAL GROUNDING MASTER PLAN")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are Gemini-4-Argon, Chief Systems Architect, Actuarial Fellow, and Global Managing Partner for Enterprise Due Diligence.

MANDATE & CONTEXT:
The latest forensic audit (`Revision_Profunda_Torre_2_Iteracion_6.txt`) rated our current deliverable at 8.0/10. It formally validated our mathematical engine (weights summing to 100%, 1.85 score alignment, FAIR chain integration, 13.75k - 27k EUR risk sum, and clean 15-page layout).
To reach a certified 9.5+/10 Tier-1 World Class level for any enterprise globally, we must solve 5 specific factual, epistemic, and qualitative alignment challenges before touching the codebase:

1. UNIVERSAL MULTI-CLOUD FOOTPRINT DISENTANGLEMENT:
   - Current Flaw: The qualitative narrative inadvertently conflated cloud ERP (SAP S/4HANA on Google Cloud) with on-premises VMs running on local hyperconverged clusters (SimpliVity/VMware).
   - Goal: Implement an algorithmic multi-cloud topology partitioner in the prompt and synthesis schemas that strictly segregates: (a) Local On-Premises Hyperconvergence, (b) Cloud Hyperscaler PaaS/IaaS workloads (e.g. SAP on GCP, Analytics on Azure), and (c) Edge/Specialized platforms (e.g. OCI databases or plant systems), prohibiting cross-location conflation.

2. STRICT METRIC GROUNDING ENGINE (ZERO FABRICATED METRICS):
   - Current Flaw: When interview transcripts state that capacity metrics are unmeasured (e.g. the customer stated "I cannot tell you the exact vCPU overcommit ratio"), the LLM fabricated "85% RAM saturation" and "high vCPU oversubscription".
   - Goal: Enforce a strict Evidence-Grounding Parser. If an infrastructure capacity metric is unmeasured, the engine MUST explicitly state that the metric is unquantified and pending formal telemetry confirmation (e.g. via vCenter or cloud monitoring), describing operational tension without fabricating quantitative percentages.

3. FAIR OPERATIONAL POSTURE RECOGNITION (OBSERVABILITY & TOOLING REALITY):
   - Current Flaw: The diagnostic narrative claimed "exclusively static alerts" and "severe ticketing delays", directly contradicting recorded evidence demonstrating that the client uses Zabbix with synthetic URL probes, auto-remediation scripts, and maintains timely ticket resolution.
   - Goal: Implement a Balanced Diagnostic Tone directive. The engine must actively recognize existing operational tooling and successes, framing the actual strategic gap as the lack of unified enterprise observability (SLO/SLI budgeting, full-stack tracing) and manual scaling constraints.

4. CALIBRATED ACTUARIAL ASSUMPTION FRAMING:
   - Current Flaw: Stating that 80%-95% vulnerability is "objectively derived" from CMMI maturity creates epistemic friction with quantitative risk auditors.
   - Goal: Formulate the vulnerability ratio in Section 4.2 as a "calibrated actuarial model assumption conditioned on CMMI Level 1 operational posture (absence of automated preventative safeguards)", aligning with Open FAIR™ and NIST SP 800-30 doctrine.

5. EMPIRICAL ADOPTION TRAJECTORY FOR INCIPIENT CAPABILITIES:
   - Current Flaw: When calibrating a capability from a high self-assessed score (e.g. 4.25) to Level 1 (Initial), phrasing it as a blunt absence ("no container platform exists") clashes with the client having hired dedicated talent and running pilot projects.
   - Goal: Frame calibration gap narratives as an "incipient adoption trajectory" (exploratory lab phase without enterprise production governance), honoring the client's strategic intent while defending the Level 1 operational reality.

CORE INVARIANTS:
- 100% Technical English in code, variables, classes, docstrings, comments, logs, and prompt files.
- Zero Hardcoding: Algorithms and prompt directives must be universal, scaling from a $50M mid-market firm to a $100B global conglomerate.
- Zero Regressions: Must pass all 47 existing architecture and actuarial tests.

YOUR DELIVERABLE:
Write a comprehensive, exhaustive, publication-grade MASTER ARCHITECTURAL BLUEPRINT in Markdown format to be saved at `docs/architecture/ARGON_PHASE9_ITERATION6_MASTER_PLAN.md`.

Structure the plan into:
1. EXECUTIVE SUMMARY & CONSULTING MANIFESTO: Addressing the 5 challenges.
2. DETAILED PHASED IMPLEMENTATION STRATEGY:
   - Phase 1: Algorithmic Multi-Cloud Topology Partitioning (Schema & Prompts).
   - Phase 2: Strict Metric Grounding & Telemetry Disclaimer Guardrails.
   - Phase 3: Balanced Operational Posture & Tooling Recognition Directive.
   - Phase 4: Calibrated Open FAIR™ Vulnerability Assumption Framing.
   - Phase 5: Incipient Adoption Trajectory Calibration Framing.
3. QUALITY GATES & VERIFICATION ORACLES: Deterministic pytest validation suites.
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

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_PHASE9_ITERATION6_MASTER_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Master Plan successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    generate_iteration6_master_plan()
