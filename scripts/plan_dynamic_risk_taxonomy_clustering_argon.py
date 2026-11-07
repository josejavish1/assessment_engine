#!/usr/bin/env python3
"""Section 3.2 Dynamic Risk Taxonomy Clustering Blueprint Generator via gemini-4-argon.

Consults gemini-4-argon (reasoning tier) to produce an authoritative, board-level
architectural blueprint (RFC 081) transforming Section 3.2 (Heatmap Matrix) from a 
cryptic 5x5 grid into a dynamic, Tier-1 corporate risk taxonomy presentation.
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
    print(f"Connecting to reasoning engine: {model_name}...")

    prompt = """
Role: Chief Corporate Governance Advisor, Executive Editorial Director, and Principal Actuarial Risk Architect advising Global Fortune 500 Boards, CEOs, CFOs, and CIOs.

CONTEXT & PROBLEM STATEMENT:
In the Assessment Engine's Consolidated AS-IS Diagnostic deliverable (Volume 1 / Tomo 1), Section 3.2 currently renders a classic 5x5 Open FAIR Heatmap Matrix. 
However, it suffers from severe "broad-brush" (trazo gordo) presentation flaws and is disconnected from the underlying forensic reality of the audit:

1. Cryptic and Orphaned Plot Points:
   - The matrix renders points with raw internal system codes (e.g., "T05.R01", "T02.R01") without any legend or explanation. A CEO or CFO reading this matrix does not know what these acronyms mean or what business threat they represent.

2. Numerical Contradiction & Loss of Granularity:
   - The forensic audit (detailed in the 10 specialist annexes) uncovers the full reality (e.g., 143 total granular technical findings across 10 towers: 24 Critical, 68 High, 51 Medium).
   - But Section 3.2 only plots exactly 10 abstract dots (one per tower). It fails to bridge the gap between the 143 forensic findings and the overarching systemic risk vectors.

3. The "State-of-the-Art" Requirement (Open FAIR™ / ORX / Gartner Taxonomy):
   - Tier-1 global risk practices (McKinsey, BCG, Big 4) never present a 100+ item "laundry list", nor do they force companies into a rigid, hardcoded 4-pillar risk box.
   - The state-of-the-art solution is a Dynamic Ontological Clustering Engine: 
     A canonical catalog of universal risk families (e.g., Lifecycle Obsolescence, Manual Process Frictions, Perimeter/Edge Resilience, Compliance/Identity Governance, Supply Chain/Vendor Lock-in). 
     The engine dynamically groups the client's actual empirical findings into these families. It only displays the families that have non-zero findings, ordered by aggregate financial impact (ALE).

MANDATORY LAWS & ARCHITECTURAL INVARIANTS:
1. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, comments, docstrings, variable names, logs, exceptions, and tests MUST be 100% Technical English.
   - Spanish exists strictly as data in `locales.json`.
2. ZERO HARDCODING (Dynamic N-Axis Polymorphism):
   - No hardcoded client names ("MOLINS"), domain codes ("T4", "T5"), or specific industry nouns in Python code or catalog templates.
   - The taxonomy mapping MUST NOT force exactly 4 or 5 buckets. It must dynamically resolve the N active buckets based on the payload data. If a Fintech has 0 findings in "Industrial Edge Resilience", that row MUST NOT appear.
3. 6-LOCALE MATHEMATICAL SYMMETRY:
   - Symmetrical updates in `locales.json` across `es`, `en`, `pt`, `fr`, `de`, `ja`.
   - The taxonomy category names and dynamic explanations must be flawlessly localized.
4. MAINTAIN THE FAIR MATRICES:
   - The 5x5 heatmap visual is retained (Boards expect it), but it MUST be immediately followed by a clear, high-value "Risk Taxonomy & Findings Clustering" table that translates the matrix codes into systemic business threats and aggregates the granular findings.

DELIVERABLE:
Generate an authoritative, board-ready architectural blueprint in Markdown:
"RFC 081: Section 3.2 Dynamic Risk Taxonomy Clustering & Heatmap Legend Governance".

The RFC MUST include:
1. Executive Verdict & ORX/FAIR State-of-the-Art Justification.
2. The Canonical Risk Taxonomy Catalog: Define 5-6 universal risk families (Technical English internal keys) and their dynamic mapping logic.
3. Codebase Modification Plan: 
   - Enhancements to `TowerPayloadHydrator` or `ActuarialReconciler` to aggregate the 10-tower findings (Critical, High, Medium counts) into the dynamic taxonomy clusters.
   - Updates to `tomo_asis_ast_compiler.py` (`_build_chapter_3_actuarial_risk_register`) to append the high-value "Taxonomy Clustering & Legend Table" directly beneath the 5x5 Heatmap.
   - Exact `locales.json` catalog updates for the taxonomy families across all 6 locales.
4. Automated Quality Gate Test Specification (`tests/unit/test_rfc081_dynamic_risk_taxonomy_clustering.py`).
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    output_path = REPO_ROOT / "docs/architecture/RFC_081_DYNAMIC_RISK_TAXONOMY_CLUSTERING_ARGON.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response.text, encoding="utf-8")
    print(f"✅ RFC 081 successfully generated by {model_name} at: {output_path}")


if __name__ == "__main__":
    main()
