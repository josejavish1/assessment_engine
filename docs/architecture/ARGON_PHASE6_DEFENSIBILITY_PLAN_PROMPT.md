# MASTER PLAN INSTRUCTION: DEFENSIBILITY & ACTUARIAL TRANSPARENCY

You are the Master Architect. We have identified four critical defensibility gaps in the current Assessment Engine pipeline (specifically highlighted in Tower 2 audit). We need a step-by-step execution plan to remediate these issues permanently. 

**STRICT DIRECTIVES:**
- **Language Decoupling Law:** The plan and all future code modifications MUST be 100% in Technical English. No Spanish in variables, logic, comments, or hardcoded strings. Spanish is only permitted in `locales.json`.
- **Zero Hardcoding:** All solutions must be multi-tenant, scale-agnostic, and purely algorithmic.
- **Fail-Fast & Validation:** Every step must include its validation strategy (tests).

**THE 4 STRATEGIC OBJECTIVES:**

1.  **Compiler Override Bug (The 13k vs 1.9k ALE Contradiction):**
    *   **Context:** `payload_to_ast.py` (around L3517) redundantly calls `synthesize_chapter4`, overwriting the real monistic risk cards (which correctly sum ~13.750€) with uncalibrated default fallback values (~1.900€).
    *   **Requirement:** Plan the surgical removal of this overwrite so the DOCX compiler strictly uses the pre-calibrated `chapter4_monistic_payload`.

2.  **Open FAIR Actuarial Transparency (The TEF/LEF Split-Brain):**
    *   **Context:** The risk cards currently show TEF (e.g., 2-10 events/yr) and SLE (8,000€), but an ALE of 600€. This looks like a math error to auditors because the conditional Vulnerability probability is hidden.
    *   **Requirement:** Plan the structural update to `ast_table_builders.py` and `payload_to_ast.py` to explicitly display the full FAIR chain: `TEF × Vulnerability = LEF -> LEF × SLE = ALE`.

3.  **Governance Scale Synchronization (CMMI vs Official Framework):**
    *   **Context:** `governance_scales.json` uses legacy CMMI bands (Initial, Managed, Defined, Quantitatively Managed, Optimized). The official project framework requires: Initial (1.00-1.79), Basic (1.80-2.59), Standardized (2.60-3.39), Optimized (3.40-4.19), Advanced (4.20-5.00).
    *   **Requirement:** Plan the update of `governance_scales.json` to these new bands and bounds, updating `locales.json` accordingly.

4.  **Perceptual Calibration Traceability (The 4.25 -> 1.00 Drop):**
    *   **Context:** The client self-assessed Kubernetes at 4.25, but the engine calibrated it to 1.00 because there is no production footprint. The DOCX shows 1.00 without tracing the override, eroding trust.
    *   **Requirement:** Plan the injection of a "Calibration Override Traceability" box in the AST compiler. If a pillar has a calibration override (perception gap), it must explicitly state: "Self-Assessed: X, Calibrated: Y. Justification: Z".

**OUTPUT:**
Generate a structured Markdown document outlining the 4 Phases of execution, specifying exactly which files will be modified, what classes/functions will change, and how we will verify the fix. Keep it purely technical, executive, and actionable.