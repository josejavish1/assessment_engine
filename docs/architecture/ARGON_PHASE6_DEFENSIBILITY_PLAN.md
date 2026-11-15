# ARGON 4-FLAWS REMEDIATION MASTER PLAN

## Executive Summary
This document outlines the strategic remediation plan for the four critical defensibility gaps identified in the Assessment Engine pipeline (Tower 2 audit). Execution is bound by strict adherence to the Language Decoupling Law (100% Technical English), Zero Hardcoding (multi-tenant, algorithmic solutions), and empirical validation (Fail-Fast & Validation).

---

## Phase 1: Compiler Override Bug (The 13k vs 1.9k ALE Contradiction)

**Context:** Redundant calls in the presentation layer overwrite the monistic risk card values.
**Target File:** `src/assessment_engine/adapters/compilers/payload_to_ast.py`

**Execution Steps:**
1. Locate the redundant `synthesize_chapter4` invocation (around L3517).
2. Remove the overwrite logic entirely. 
3. Re-route the AST compiler to strictly consume the pre-calculated `chapter4_monistic_payload` embedded in the `blueprint_data` dictionary.
4. Ensure no default fallback overrides are triggered when a valid monistic payload exists.

**Validation Strategy:**
- **Unit Testing:** Implement a test in `tests/unit/adapters/compilers/test_payload_to_ast.py` injecting a mock `chapter4_monistic_payload` with an ALE of 13,750. Assert that the resulting AST retains the exact 13,750 value and does not revert to the uncalibrated 1,900 fallback.

---

## Phase 2: Open FAIR Actuarial Transparency (The TEF/LEF Split-Brain)

**Context:** Conditional Vulnerability probability is hidden, creating an apparent mathematical error in ALE derivation.
**Target Files:** 
- `src/assessment_engine/adapters/compilers/ast_table_builders.py`
- `src/assessment_engine/adapters/compilers/payload_to_ast.py`

**Execution Steps:**
1. Modify the risk card data structures in `ast_table_builders.py` to explicitly require `vulnerability_probability` and `lef_events_per_year` parameters.
2. Update the AST table generation logic to explicitly render the mathematical chain.
3. Inject the formula into the table output format: `TEF × Vulnerability = LEF -> LEF × SLE = ALE`.
4. Ensure `payload_to_ast.py` passes the full Open FAIR tuple from the actuarial engine to the table builder.

**Validation Strategy:**
- **Integration Testing:** Run the Open FAIR derivation chain with fixed seeds. Assert the AST payload explicitly contains the literal string chain (e.g., `10.0 × 0.15 = 1.5 -> 1.5 × 8,000 = 12,000`) and that the math perfectly resolves at every step without rounding errors.

---

## Phase 3: Governance Scale Synchronization (CMMI vs Official Framework)

**Context:** Legacy CMMI terminology is misaligned with the official project framework bands.
**Target Files:**
- `engine_config/governance_scales.json`
- `engine_config/locales.json`

**Execution Steps:**
1. Overhaul `governance_scales.json` to replace the CMMI bands with the new official classification.
2. Define the new multi-tenant bands and strict bounds:
   - `Initial`: `[1.00, 1.79]`
   - `Basic`: `[1.80, 2.59]`
   - `Standardized`: `[2.60, 3.39]`
   - `Optimized`: `[3.40, 4.19]`
   - `Advanced`: `[4.20, 5.00]`
3. Update `locales.json` (English and any other supported locales as purely decoupled data) to map the new programmatic keys to their display strings.

**Validation Strategy:**
- **Functional Testing:** Evaluate edge-case scores (e.g., 1.79, 1.80, 4.19, 4.20) through the core maturity evaluator to assert the boundary transitions map strictly to the new Official Framework bands without off-by-one errors. Ensure schema validation passes on `governance_scales.json`.

---

## Phase 4: Perceptual Calibration Traceability (The 4.25 -> 1.00 Drop)

**Context:** Engine calibration overrides lack deterministic traceability in the presentation layer, eroding client trust.
**Target File:** `src/assessment_engine/adapters/compilers/payload_to_ast.py`

**Execution Steps:**
1. Update the pillar iteration logic within the AST compiler to detect a "perception gap" (`self_assessed_score != calibrated_score`).
2. Inject a new structural block into the AST schema: `Calibration Override Traceability`.
3. When a gap is detected, automatically append a formatted disclosure box to the AST pillar element: `"Self-Assessed: {X}, Calibrated: {Y}. Justification: {Z}"` (where `Z` is the dynamic actuarial justification from the policy engine).

**Validation Strategy:**
- **Unit Testing:** Inject a synthetic fixture (`self_assessed: 4.25`, `calibrated: 1.00`, `justification: "No production footprint"`) into the compiler. Assert the AST output strictly contains the `"Calibration Override Traceability"` box and validates against the expected string layout. Validate the box is completely omitted when `self_assessed == calibrated`.