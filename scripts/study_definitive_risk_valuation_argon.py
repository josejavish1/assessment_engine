#!/usr/bin/env python3
"""Argon-4 Deep Investigation: Comprehensive Intra-Document & Cross-Tower AS-IS Split-Brain Audit.

Addresses the user's strategic questions:
1. Are risks double-counted across towers? How does Primary Custodian vs Tangential Contributor work?
2. What happens if a client only assesses a subset of towers (e.g., T1 and T2, but not T6)? Is the risk lost?
3. Deep intra-document audit: Are there remaining split-brains between Chapter 1, Chapter 2, Chapter 3, and Chapter 4 across all 10 towers?
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
Role: Chief Systems Architect & Principal Actuary (Gartner Fellow / McKinsey Senior Partner / Google Core Infrastructure).

USER'S STRATEGIC QUESTIONS & ARCHITECTURAL INQUIRY:
The user asks:
"¿podríamos hacer una investigación en profundidad intradocumentos del AS-IS de todas las secciones y como generamos todas las torres si tenemos más split brain?
Me preocupa por ejemplo que cuantifiquemos varias veces el mismo riesgo, porque se supone que muchos riesgos que eran iguales íbamos a poner en el documento que se cuantificaba en otra torre, pero no sé si eso es cierto y está funcionando, y tampoco sé por ejemplo si un cliente no hace todas las torres entonces si que el riesgo lo cuenta?"

INVESTIGATION MANDATE:
Execute an exhaustive forensic investigation covering:

1. CROSS-TOWER RISK DEDUPLICATION AUDIT:
   - What is the current state in code?
     * `ConditionalLossEvent` supports `ownership_type: PRIMARY_CUSTODIAN | TANGENTIAL_CONTRIBUTOR` and `primary_risk_ref`.
     * `ActuarialCalculator` zeroes out `effective_sle` and `ale` for tangential risks (`is_deduplicated = True`).
     * `payload_to_ast.py` omits ALE fields and renders `*Exposición Financiera (ALE) contabilizada en el Riesgo Primario: {primary_risk_ref}*`.
   - The Current Reality in Fixtures:
     * In `working/molins/T1/` and `T2/`, all risks currently have `ownership_type: None`, which defaults to `PRIMARY_CUSTODIAN`. Cross-tower deduplication is wired in the compiler, but not yet tagged in the payloads.

2. THE "SUBSET OF TOWERS" (DYNAMIC CUSTODY PROMOTION) PROBLEM:
   - If an enterprise client only contracts for 2 towers (e.g., T1 Facilities and T2 Compute, omitting T6 Cyber and T4 Network):
   - What happens if a risk in T2 is hardcoded as `TANGENTIAL_CONTRIBUTOR` pointing to a primary risk in T6 (`primary_risk_ref: "T6.R01"`)?
   - If T6 is never evaluated, T6.R01 does not exist in the deliverable. If T2 zeroes it out, the client has a catastrophic actuarial BLIND SPOT (a real risk is quantified at 0 € in T2 and never quantified anywhere else!).
   - Formulate the architectural pattern: `DynamicCustodyResolver` (Contextual Custody Promotion).
     * If `primary_tower` is in the active assessment scope -> retain as `TANGENTIAL_CONTRIBUTOR` (deduplicated).
     * If `primary_tower` is OUTSIDE the active assessment scope -> dynamically promote to `PRIMARY_CUSTODIAN` in the evaluated tower with active ALE and SLE, so no risk is ever lost!

3. COMPREHENSIVE INTRA-DOCUMENT SPLIT-BRAIN AUDIT (CHAPTER 1 TO CHAPTER 4):
   - Inspect all cross-chapter linkages:
     a) Chapter 1 Executive Cockpit vs Chapter 4 Actuarial Register:
        * Is the hourly burn rate (13,061.29 €/h) 100% identical?
        * Is ALE P50 in Chapter 1 strictly equal to the sum of primary risks in Chapter 4?
        * Is the P90 exposure consistent?
     b) Chapter 2 Methodology vs Chapter 3 Diagnostic Matrix:
        * Do evaluated capabilities and weights match?
        * Does CMMI scale (1.00 to 5.00) match between Chapter 2 and Chapter 3?
     c) Chapter 3 Technical Diagnostic vs Chapter 4 Heatmap:
        * Are the highest/lowest scoring pillars reflected in the risk findings?
     d) Chapter 4 Heatmap vs Scale Criteria vs Risk Cards:
        * Are TEF and LM coordinates strictly mapped from the 4.2.1 and 4.2.2 criteria?
        * Does SLE arithmetic ($H \\times Rate = SLE$) hold without drift?

YOUR TASK:
Synthesize an authoritative Forensic Investigation Report & Architectural Design in Markdown:
1. Provide the definitive answers to the user's questions in crystal-clear, executive Spanish suitable for the user response.
2. Specify the Python architecture for the `DynamicCustodyResolver` in 100% Technical English.
3. Confirm whether any remaining split-brains exist across the 10 capability towers.
"""

    print(f"Requesting deep investigation from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/DEEP_INVESTIGATION_ASIS_SPLIT_BRAIN_AND_DEDUPLICATION_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: DEEP INVESTIGATION ON AS-IS SPLIT-BRAIN & DEDUPLICATION")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nReport saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
