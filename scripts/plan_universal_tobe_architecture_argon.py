#!/usr/bin/env python3
"""Argon-4 Master Architectural Consultation: RFC 072 Universal TO-BE Architecture & Pipeline.

Formulates a zero-hardcoding, bug-free architectural blueprint for the TO-BE deliverables:
1. Eradicates the 10-tower fragmented TO-BE annex antipattern.
2. Establishes the authoritative 2-Volume Target Suite:
   - Tomo 2: Transversal Target Architecture & Enterprise Platform Blueprint.
   - Tomo 3: Strategic Transformation Roadmap, Business Case & NTT DATA Delivery Pipeline.
3. Maximizes commercial pipeline generation for NTT DATA (H1/H2/H3 waves, WBS, sizing, TCO/ROI).
4. Guarantees universal multi-tenant scalability across ANY enterprise (mid-market to Top Tier-1),
   ANY vertical (Banking, Health, Retail, Manufacturing, Gov), ANY currency, and ANY language.
5. 100% Technical English codebase, schemas, and compiler architecture.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_fallback_model,
    get_model,
)


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    prompt = """
Role: Global Managing Director of Enterprise Architecture & Strategic Advisory (Google Cloud / NTT DATA Fellow / McKinsey Senior Partner / Gartner Distinguished Analyst).

MISSION OBJECTIVE:
Formulate the definitive, production-grade architectural specification (RFC 072: Universal TO-BE Architecture & Commercial Pipeline Blueprint) to govern the target-state deliverables of the assessment engine:
- Volume 2 (Tomo 2): Transversal Target Architecture & Enterprise Platform Blueprint.
- Volume 3 (Tomo 3): Strategic Transformation Roadmap, Business Case & NTT DATA Delivery Pipeline.

CORE STRATEGIC CONTEXT & COMMERCIAL MANDATE:
1. Elimination of the 10-Tower Fragmented TO-BE Antipattern:
   - Fragmenting the future state into 10 separate tower annexes creates severe cognitive overload (Cognitive Load Theory) for the C-suite (CIO, CTO, CFO).
   - Crucially, presenting 10 separate documents encourages clients to split the procurement into 10 small, commoditized RFPs where NTT DATA competes on hourly rates against niche vendors.
   - Conversely, a consolidated, programmatic target architecture (Tomo 2) coupled with a multi-year transformation roadmap (Tomo 3) positions NTT DATA as the Prime Contractor & Strategic Partner for a multi-million-euro end-to-end modernization program (professional services + managed services recurring revenue).

2. Universal Multi-Tenant Scalability (Mid-Market to Top Global Tier-1):
   - The engine must seamlessly support ANY enterprise in the world:
     * Revenue scale: $10M mid-market to $100B Global Fortune 500.
     * Industry vertical: Banking/Insurance (DORA, Basel III), Healthcare (HIPAA, HITRUST), Retail/eCommerce (PCI-DSS), Critical Infrastructure/Manufacturing (NIS2, IEC 62443), Public Sector.
     * Geography & Currency: EUR, USD, JPY, GBP, CHF.
     * Delivery Languages: English, Spanish, Portuguese, French, German, Japanese.
   - Zero hardcoding: No client names, vendor lock-in assumptions (e.g. VMware, SimpliVity), local facilities, or cement/manufacturing biases.

3. Complete Architectural Purity:
   - 100% Technical English codebase: All data models, compilers, AST structures, methods, docstrings, and tests must be in English.
   - Declarative OpenXML AST Compilation: Eradicate template-replacement split-brains. Tomo 2 and Tomo 3 must be compiled via a deterministic, high-fidelity AST compiler (similar to TomoAsisASTCompiler), enforcing the Strict Short-Hyphen Invariant (zero em-dashes U+2014 or en-dashes U+2013) and strict vertical layout containment.

REQUIRED DELIVERABLE STRUCTURE (RFC 072):
Please formulate a comprehensive, rigorous architectural blueprint covering:

1. Executive Delivery Architecture & Value Proposition:
   - The C-Suite Cognitive Model: Information architecture of Tomo 2 and Tomo 3 designed to guide the CIO, CTO, and CFO from technical vision to approved commercial budget.
   - The NTT DATA Commercial Pipeline Engine: How the platform dynamically translates diagnostic findings and capability maturity deficits into structured, billable project initiatives across 3 execution horizons (H1: Immediate Stabilization, H2: Core Modernization & Cloud Convergence, H3: Platform Innovation & Autonomous Operations).

2. Data Contract & Domain Schemas (TargetStatePayload & TransformationPipelinePayload):
   - Formal Pydantic schemas in 100% Technical English defining the SSOT inputs for Tomo 2 and Tomo 3.
   - Platform architecture model: Transitioning from siloed towers to transversal technology platforms:
     * Platform 1: Sovereign Hybrid Cloud & Modern Compute (Landing Zones, Kubernetes, Virtualization Migration).
     * Platform 2: Zero Trust Network Fabric & Distributed Connectivity (SD-WAN, SASE, Microsegmentation).
     * Platform 3: Data Fabric, Enterprise Storage & Resilience (Immutable Backups, Object Storage, Disaster Recovery).
     * Platform 4: Identity Governance, Modern Workplace & Cyber Defense (Tier-0 PAM, EDR, Unified Identity).
     * Platform 5: Autonomous Operations, Observability & FinOps (OpenTelemetry, AIOps, Cost Governance).
   - Project initiative schema: WBS breakdown, sizing (S/M/L/XL), profile allocations (Lead Architect, Senior Engineer, PM), Capex/Opex estimates, ROI justification, and risk mitigation links.

3. Compiler Architecture Blueprint (Tomo2TargetArchitectureCompiler & Tomo3TransformationRoadmapCompiler):
   - Detailed chapter structure and layout specifications for both volumes:
     * Tomo 2 Chapters: (1) Executive Architecture Synthesis & North Star Vision; (2) Transversal Enterprise Platforms; (3) Multi-Cloud & Hybrid Infrastructure Topology; (4) Resilient Data & Application Modernization; (5) Enterprise Security Architecture & Compliance Matrix.
     * Tomo 3 Chapters: (1) Executive Roadmap Memo & Investment Horizon; (2) Master Transformation Roadmap (Gantt & Dependency Graph); (3) Project Portfolio & Work Breakdown Structure (WBS); (4) Comprehensive Business Case, TCO & Actuarial ROI; (5) Governance, Sizing & Delivery Operating Model (NTT DATA Partnership).
   - Layout & OpenXML typography standards: Table autofit, accent borders, page budgeting, visual diagram anchors.

4. Dynamic Sector & Localization Adaptation:
   - Dynamic parameterization of regulatory frameworks, platform initiatives, and financial rate cards based on `case_input.json`, `industry_profiles/`, and `engine_config/rate_card.json`.
   - Internationalization architecture: Separation of linguistic framing (`locales.json`) from dynamic project metadata.

5. Implementation Roadmap & Multi-Phase Execution Plan:
   - Phase-by-phase execution sequence to implement the compilers, schemas, and delivery suite orchestrator with deterministic quality gates.
"""

    print(f"Submitting RFC 072 prompt to {model_name}...")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
    except Exception as e:
        print(f"Error querying primary model {model_name}: {e}")
        fallback = get_fallback_model(model_name)
        if fallback:
            print(f"Falling back to {fallback}...")
            response = client.models.generate_content(
                model=fallback,
                contents=prompt,
            )
        else:
            raise

    out_file = REPO_ROOT / "docs/architecture/RFC_072_UNIVERSAL_TOBE_ARCHITECTURE_AND_PIPELINE_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("RFC 072 TO-BE ARCHITECTURAL PLAN GENERATED SUCCESSFULLY")
    print("=" * 80)
    print(f"Output saved to: {out_file.relative_to(REPO_ROOT)} ({len(response.text):,} characters)")


if __name__ == "__main__":
    main()
