#!/usr/bin/env python3
"""Argon-4 Master Architectural Consultation: RFC 071 Universal Multi-Tenant Decoupling.

Formulates a zero-hardcoding, bug-free architectural blueprint before modifying any code:
1. Eradicates all tenant telemetry and Molins hardcoding from engine_config/locales.json.
2. Eliminates split-brain in TomoAsisASTCompiler (Chapter 4 must dynamically read tower_payloads).
3. Decouples physical infrastructure archetypes in payload_to_ast.py from cement manufacturing.
4. Transitions domain topology from a rigid 10-tower assumption to dynamic N-domain polymorphism.
5. Establishes a rigorous multi-tenant data binding contract across all capability towers.
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
Role: Chief Distributed Systems Architect & Lead Actuary (Tier-1 Advisory: Google Core Infrastructure Fellow, Gartner Distinguished VP Analyst, McKinsey Senior Partner).

MISSION OBJECTIVE:
Design the definitive architectural plan (RFC 071: Universal Multi-Tenant Decoupling & Dynamic SSOT Binding) to purge all single-tenant bias, split-brain antipatterns, and hardcoded literals from the assessment engine. The platform must scale seamlessly to ANY enterprise in the world (from $10M mid-market to $100B Global Fortune 500), across ANY industry vertical (Banking, Healthcare, Retail, Heavy Manufacturing, Utilities, Public Sector), under ANY currency (USD, EUR, JPY, GBP), and in ANY language (EN, ES, PT, FR, DE, JA).

CRITICAL AUDIT FINDINGS (THE 4 CONTAMINATION VECTORS):
1. Catalog Pollution in `engine_config/locales.json`:
   - Specific geographical sites hardcoded: "Sant Vicenç dels Horts", "18 countries".
   - Specific corporate entities/acquisitions: "Secil".
   - Specific vendor platforms & contract dates: "6 HPE SimpliVity nodes", "VMware renewal May 2027", "NetApp", "Huawei/Cisco".
   - Specific manufacturing processes & hourly rates: "weighbridges (básculas de pesaje)", "cement bagging lines (líneas de ensacado)", "5,000 EUR/h outage rate".
   - Impact: If a commercial bank or regional hospital is assessed, the engine falsely reports cement plant downtime and Catalonia data centers.

2. Split-Brain in Consolidated AS-IS AST Compiler (`tomo_asis_ast_compiler.py`):
   - In Chapter 4 (Forensic Domain Diagnostics), the compiler receives `tower_payloads` but ignores them.
   - It reads inventories, strengths, findings, and subpillars directly from static catalog entries (`tomo_tower_forensic_catalog` in `locales.json`).
   - Impact: Real findings calculated for any other client never reach the consolidated report.

3. Static Topology Assumption (Rigid 10 Towers):
   - `_resolve_domain_topology` enforces a loop over fixed canonical codes (`T1` through `T10`) with predetermined titles.
   - If a client contracts only 3 towers (e.g. Cloud, Cyber, Data) or uses a non-standard taxonomy, the compiler injects placeholder data and Molins defaults for the remaining 7 towers.

4. Hardcoded Physical Archetypes in Per-Tower Compiler (`payload_to_ast.py`):
   - In `ExecutiveNarrativeSynthesizer.synthesize_chapter_one_paragraphs`, archetype `INFRASTRUCTURE_PHYSICAL` pulls from templates with hardcoded weighbridge and cement dispatch outage narratives for T1, T4, and T5.

NON-NEGOTIABLE ENGINEERING CONSTRAINTS:
1. Zero Hardcoding: No client names, locations, vendor platforms, contract cliffs, or specific equipment in catalogs or compilers.
2. 100% Technical English Codebase: Zero Spanish in Python identifiers, schemas, comments, docstrings, or test files. Spanish is strictly an external delivery translation target in `locales.json`.
3. Dynamic SSOT Data Binding: `TomoAsisASTCompiler` must iterate exclusively over active domains present in `tower_payloads` / `global_payload.heatmap`, binding:
   - Dynamic inventory: extracted from `payload.inventory` / `case_input.json`.
   - Dynamic findings & strengths: extracted from `payload.findings`, `payload.strengths`, or `payload.pillars_analysis`.
   - Dynamic subpillars: extracted from `payload.pillars_analysis` (name, score, findings).
   - Dynamic executive narratives: synthesized parametrically using generic, sector-aware schema tokens (`{facility_summary}`, `{core_workloads}`, `{annualized_impact}`).
4. Backward Compatibility & Graceful Degradation: If an optional telemetry key is absent, compute deterministic actuarial fallbacks without failing or inventing fake assets.
5. Closed-Form Actuarial Integrity: Multi-domain allocations and tail risks must reconcile penny-exact via `ActuarialReconciler` using the Largest Remainder Method across N domains.
6. OpenXML Layout Preservation: Guarantee strict vertical budget containment (e.g. Page 3 single-page executive cockpit, clean table flow).

REQUIRED DELIVERABLE STRUCTURE (RFC 071):
Please deliver a comprehensive, production-grade architectural specification covering:
1. Core Architectural Principles & Tenant Boundary Model: Formal separation between Data SSOT (`tower_payloads`), Linguistic Framing (`locales.json`), and Domain Topology (`case_input.json` / `global_payload`).
2. Catalog Decoupling Specification:
   - Concrete before/after comparison of purged keys in `engine_config/locales.json`.
   - Parameterized placeholder schema for neutral, universally applicable templates across all archetypes (`INFRASTRUCTURE_PHYSICAL`, `COMPUTE_PLATFORMS`, `SECURITY_GOVERNANCE`).
3. Compiler Refactoring Blueprint (`tomo_asis_ast_compiler.py`):
   - Complete architectural redesign of `_resolve_domain_topology` to support N domains (1 to N) dynamically.
   - Refactored `_build_chapter_4_forensic_domains` that binds 100% to live `tower_payloads` without touching static catalogs.
   - Dynamic extraction helpers for inventories, strengths, findings, and subpillar scores.
4. Per-Tower Narrative Synthesizer Remediation (`payload_to_ast.py`):
   - Removal of hardcoded manufacturing phrases from archetypes.
   - Dynamic injection of sector context from `industry_profiles` or `case_input`.
5. Multi-Tenant Verification & Quality Gate:
   - Step-by-step test strategy demonstrating that running an arbitrary enterprise (e.g., "Nordic Health Group", "Tokyo FinTech Bank", or "Acme Retail") produces 100% accurate, zero-leak deliverables.
"""

    print(f"Submitting RFC 071 prompt to {model_name}...")
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

    out_file = REPO_ROOT / "docs/architecture/RFC_071_UNIVERSAL_MULTI_TENANT_DECOUPLING_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("RFC 071 ARCHITECTURAL PLAN GENERATED SUCCESSFULLY")
    print("=" * 80)
    print(f"Output saved to: {out_file.relative_to(REPO_ROOT)} ({len(response.text):,} characters)")


if __name__ == "__main__":
    main()
