#!/usr/bin/env python3
"""Argon-4 Master Consultation: RFC 062 Declarative AST Architecture for Consolidated Tomo 1 AS-IS.

Eradicates the split-brain between individual tower annexes and the transversal CTO/CIO deliverable.
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
    get_model,
)


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    prompt = """
Role: Chief Enterprise Architect & Principal OpenXML AST Compiler Engineer (Tier-1 Management Consulting / Google Core Infrastructure).

USER'S STRATEGIC MANDATE:
"ok lo importante es que no haya split brain"
The user mandates the complete eradication of split-brain between individual tower annexes (which are certified 10/10 under the declarative AST compiler) and the transversal Tomo 1 AS-IS diagnostic report (which was stuck in an obsolete 5.8/10 template compiler with missing chapters and over-compressed diagnostics).

OBJECTIVE:
Design the architectural specification for `TomoAsisASTCompiler` (RFC 062) to compile `Molins_202610_Tomo_1_Diagnostico_ASIS.docx` directly from enriched SSOT payloads (`global_report_payload.json`, `blueprint_t1_payload.json`, `blueprint_t2_payload.json`, etc.) into a cohesive, board-ready 25-30 page document.

ARCHITECTURAL SPECIFICATIONS REQUIRED:
1. Complete 5-Chapter Structure:
   - Chapter 1: Executive Summary & Transversal Strategic Thesis (KPI Cockpit, Diagnostic Triad table, Board narrative on industrial continuity, Secil integration, NIS2, and May 2027 contract milestone).
   - Chapter 2: Consolidated Capability Maturity Radiography (CMMI table across all 10 towers with strict CMMI bands [1.0-1.9 Initial, 2.0-2.9 Managed, 3.0-3.9 Defined], target scores, and visual distribution).
   - Chapter 3: Aggregated Open FAIR™ Actuarial Risk Register (10,000-run Monte Carlo methodology, 13,061.29 €/h baseline, aggregated ALE P50, P90 tail risk compound disaster breakdown, aggregated 5x5 heatmap, and Tier 1/2/3 risk concentration table).
   - Chapter 4: Forensic Domain Diagnostics & Critical Single Point of Failure (SPOF) Matrix (Deep-dive into evaluated domains—T1 Data Center, T2 Hybrid Compute—with real hardware/topology: Sant Vicenç dels Horts, SimpliVity, NetApp, VMware, 5,000 €/h plant weighbridge dependencies, complemented by transversal status of T3-T10, plus a dedicated SPOF Table).
   - Chapter 5: Cross-Tower Nexus & Critical Interdependencies (prerequisites table, architectural rationale, cost of delay/inaction).
   - Unified Appendix: Clean Abbreviations Glossary (18%/82% autofitted table) and Legal Liability Disclaimer.

2. Mathematical Synchronization (Zero Split-Brain):
   - Global maturity score = exact weighted average of tower maturity scores.
   - Global ALE P50 = sum of deduplicated primary risks via `DynamicCustodyResolver`.
   - All financial figures across Chapter 1, Chapter 2, Chapter 3, and Chapter 4 must be 100% mathematically aligned.

3. Non-Negotiable Engineering Laws:
   - Law #1: Zero bugs, zero antipatterns.
   - Law #2: Zero hardcoding (scales dynamically to any enterprise client worldwide, any vertical, any currency).
   - Law #3: 100% Technical English codebase (Python identifiers, classes, methods, docstrings, and comments in Technical English; Spanish ONLY in localized dictionaries).
   - Law #4: Strict Short-Hyphen Invariant (zero em-dashes `—` or en-dashes `–`).
   - Law #5: OpenXML Layout Determinism (Native headings, TableNode autofit, cantSplit, tblHeader, and DeterministicTocPageResolver synchronization).

YOUR TASK:
Synthesize an authoritative Architectural Blueprint (RFC 062) in Markdown:
1. Define the class hierarchy and methods for `TomoAsisASTCompiler`.
2. Specify the payload aggregation protocol and data flow.
3. Detail the OpenXML AST node construction for all 5 chapters.
4. Deliver a definitive VERDICT: PASS.
"""

    print(f"Requesting RFC 062 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_062_TOMO_1_ASIS_AST_COMPILER_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 062 ARCHITECTURAL BLUEPRINT")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nBlueprint saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
