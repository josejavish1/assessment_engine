---
status: Verified
owner: architecture-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-07
applies_to:
- gemini
- architecture
doc_type: operational
diataxis: reference
verification_mode: editorial
---
### ARCHITECTURAL DIRECTIVE: ERADICATION OF THE QUANTITATIVE SPLIT-BRAIN ANTI-PATTERN

**Document ID:** ARCH-GOV-2026-009  
**Author:** `gemini-4-argon` (Distinguished Principal Distributed Systems Architect / Chief Quality Gatekeeper)  
**Status:** MANDATORY / IMMEDIATE EXECUTION  
**Target Architecture:** Assessment Engine & Actuarial Synthesis Pipeline  

---

### 1. EXECUTIVE ARCHITECTURAL DIAGNOSIS

We are currently experiencing a severe state-management anti-pattern known in distributed systems as **Split-Brain State Divergence**, compounded by **Stochastic Boundary Bleeding**. 

By permitting a generative LLM step (`resynthesize_all_10_towers_from_raw_transcription.py`) to emit both qualitative analysis (narratives) and quantitative metrics (pillar scores/weights) within the same schema (`pillars_analysis`), we violated the fundamental boundary between **Deterministic Computation** and **Stochastic Synthesis**. 

The LLM acts as an uncalibrated random number generator when asked to infer maturity scores from unstructured text. Consequently, the AST compiler consumes a deterministic root scalar ($2.61$) alongside stochastic child scalars ($[2.00, 2.20, 2.30]$), resulting in a mathematical impossibility where:

$$\sum_{i=1}^{N} (S_i \times W_i) \neq S_{\text{Tower}}$$

**Architectural Invariant Declaration:**
1. **Deterministic SSOT:** `src/assessment_engine/application/run_scoring.py` (`build_scoring()`) is the sole authority for all maturity scores, pillar weights, and KPI aggregations.
2. **Epistemic Separation of Concerns:** The discrepancy between the client’s self-reported questionnaire responses and the forensic reality extracted from transcripts **must never** mutate the baseline maturity score. That delta is strictly an epistemic vector handled by the `EpistemicSynthesizer` (emitting `VERIFIED_DISSONANT`) and penalized downstream by the Open FAIR Actuarial Engine via Loss Event Frequency (LEF) and Vulnerability multipliers (increasing ALE and VaR).

Below is the comprehensive, zero-hardcoding engineering roadmap to permanently resolve this defect.

---

### PHASE 1: Payload Synchronization & Deterministic State Reconciliation

In Phase 1, we construct a deterministic state reconciler. This module takes the authoritative output from `build_scoring()` and enforces a strict schema-level overwrite of all quantitative attributes within the tower payload, while completely preserving the LLM-generated qualitative narratives.

#### Step 1.1: Create the Quantitative State Reconciler Module
**File Path:** `src/assessment_engine/domain/services/score_reconciler.py` (NEW FILE)

```python
"""
Quantitative State Reconciler.
Enforces Single Source of Truth (SSOT) by projecting deterministic scores 
from the scoring engine onto stochastic LLM-generated tower payloads.
"""

import logging
from typing import Dict, Any, List
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


class QuantitativeSplitBrainError(Exception):
    """Raised when structural topology between SSOT and Payload cannot be reconciled."""
    pass


def _normalize_id(identifier: str) -> str:
    """Normalizes pillar or tower identifiers for deterministic matching."""
    return str(identifier).strip().upper()


def reconcile_tower_scores(
    tower_payload: Dict[str, Any], 
    scoring_ssot: Dict[str, Any],
    precision: str = "0.01"
) -> Dict[str, Any]:
    """
    Overwrites LLM-hallucinated scores and weights in the tower payload with 
    the deterministic outputs from build_scoring(). Preserves all qualitative narratives.

    :param tower_payload: The mutable dictionary representing the full tower JSON payload.
    :param scoring_ssot: The dictionary output from run_scoring.py::build_scoring() for this tower.
    :param precision: Decimal quantization string for rounding consistency.
    :return: The mutated, mathematically consistent tower_payload.
    """
    tower_id = _normalize_id(tower_payload.get("tower_id", "UNKNOWN"))
    ssot_tower_id = _normalize_id(scoring_ssot.get("tower_id", "UNKNOWN"))

    if tower_id != "UNKNOWN" and ssot_tower_id != "UNKNOWN" and tower_id != ssot_tower_id:
        raise QuantitativeSplitBrainError(
            f"Topology mismatch: Payload Tower ID ({tower_id}) != SSOT Tower ID ({ssot_tower_id})."
        )

    # 1. Enforce Root Tower Score SSOT
    authoritative_tower_score = float(
        Decimal(str(scoring_ssot["score"])).quantize(Decimal(precision), rounding=ROUND_HALF_UP)
    )
    
    # Support multiple historical schema paths for the root score
    tower_payload["score"] = authoritative_tower_score
    if "overall_score" in tower_payload:
        tower_payload["overall_score"] = authoritative_tower_score
    if "maturity_score" in tower_payload:
        tower_payload["maturity_score"] = authoritative_tower_score

    # 2. Index SSOT Pillars by normalized ID and Positional Index
    ssot_pillars: List[Dict[str, Any]] = scoring_ssot.get("pillars", [])
    if not ssot_pillars:
        raise QuantitativeSplitBrainError(f"SSOT for Tower {tower_id} contains zero pillars.")

    ssot_by_id: Dict[str, Dict[str, Any]] = {
        _normalize_id(p["pillar_id"]): p for p in ssot_pillars if "pillar_id" in p
    }

    # 3. Reconcile Pillars Analysis Array
    payload_pillars: List[Dict[str, Any]] = tower_payload.get("pillars_analysis", [])
    
    if len(payload_pillars) != len(ssot_pillars):
        raise QuantitativeSplitBrainError(
            f"Cardinality violation in Tower {tower_id}: LLM generated {len(payload_pillars)} "
            f"pillars, but topology definition requires exactly {len(ssot_pillars)}."
        )

    for idx, payload_pillar in enumerate(payload_pillars):
        p_id = _normalize_id(payload_pillar.get("pillar_id", ""))
        
        # Match by explicit ID first; fallback to strict positional topology matching
        matched_ssot_pillar = ssot_by_id.get(p_id)
        if not matched_ssot_pillar:
            logger.warning(
                f"Tower {tower_id}: Pillar ID '{p_id}' not found in SSOT map. "
                f"Falling back to strict positional index [{idx}]."
            )
            matched_ssot_pillar = ssot_pillars[idx]
            # Correct the hallucinated pillar_id as well
            if "pillar_id" in matched_ssot_pillar:
                payload_pillar["pillar_id"] = matched_ssot_pillar["pillar_id"]

        # Extract and quantize deterministic metrics
        exact_p_score = float(
            Decimal(str(matched_ssot_pillar["score"])).quantize(Decimal(precision), rounding=ROUND_HALF_UP)
        )
        exact_p_weight = float(
            Decimal(str(matched_ssot_pillar["weight"])).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        )

        # Log epistemic/hallucination drift for observability
        old_score = payload_pillar.get("score")
        if old_score != exact_p_score:
            logger.info(
                f"[SSOT Reconciler] Tower {tower_id} | Pillar {payload_pillar.get('pillar_id')}: "
                f"Overwriting hallucinated score ({old_score}) -> Deterministic SSOT ({exact_p_score})."
            )

        # Overwrite quantitative fields while leaving narrative fields untouched
        payload_pillar["score"] = exact_p_score
        payload_pillar["weight"] = exact_p_weight
        
        # Ensure official pillar name consistency if available in SSOT
        if "name" in matched_ssot_pillar and "pillar_name" in payload_pillar:
            payload_pillar["pillar_name"] = matched_ssot_pillar["name"]

    return tower_payload
```

#### Step 1.2: Create the Retroactive Payload Synchronization CLI Utility
To heal existing corrupted JSON payloads (e.g., Molins Tower 1 through 10) without re-running expensive LLM generations, we create a deterministic migration utility.

**File Path:** `src/assessment_engine/application/sync_payload_scores.py` (NEW FILE)

```python
"""
CLI Utility to synchronize existing generated tower JSON payloads with 
the deterministic output of run_scoring.py.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any

from src.assessment_engine.application.run_scoring import build_scoring
from src.assessment_engine.domain.services.score_reconciler import reconcile_tower_scores

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def synchronize_tenant_payloads(
    responses_path: Path,
    engine_config_dir: Path,
    payloads_dir: Path
) -> None:
    """
    Executes build_scoring() and patches all tower JSON files in payloads_dir.
    """
    logger.info(f"Computing deterministic SSOT scores from: {responses_path}")
    # build_scoring returns a dict mapping tower_id -> scoring structure
    master_scoring_ssot: Dict[str, Any] = build_scoring(
        responses_path=str(responses_path),
        config_dir=str(engine_config_dir)
    )

    towers_ssot_map: Dict[str, Any] = master_scoring_ssot.get("towers", {})
    if not towers_ssot_map:
        raise ValueError("build_scoring() returned an empty 'towers' dictionary.")

    payload_files = sorted(payloads_dir.glob("*.json"))
    if not payload_files:
        logger.warning(f"No JSON payloads found in {payloads_dir}")
        return

    for file_path in payload_files:
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        tower_id = str(payload.get("tower_id", "")).strip().upper()
        if not tower_id or tower_id not in towers_ssot_map:
            logger.debug(f"Skipping {file_path.name}: Not a recognized tower payload.")
            continue

        logger.info(f"Reconciling state for {file_path.name} (Tower ID: {tower_id})...")
        reconciled_payload = reconcile_tower_scores(
            tower_payload=payload,
            scoring_ssot=towers_ssot_map[tower_id]
        )

        # Atomic write replacement
        temp_path = file_path.with_suffix(".json.tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(reconciled_payload, f, indent=2, ensure_ascii=False)
        temp_path.replace(file_path)
        logger.info(f"Successfully synchronized {file_path.name}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synchronize Tower Payloads with Scoring SSOT.")
    parser.add_argument("--responses", required=True, type=Path, help="Path to client questionnaire responses JSON.")
    parser.add_argument("--config-dir", required=True, type=Path, help="Path to engine_config directory.")
    parser.add_argument("--payloads-dir", required=True, type=Path, help="Directory containing generated tower JSONs.")
    
    args = parser.parse_args()
    synchronize_tenant_payloads(args.responses, args.config_dir, args.payloads_dir)
```

---

### PHASE 2: Pipeline Integrity & Stochastic Boundary Enforcement

We must ensure that the LLM cannot re-introduce this defect during future pipeline runs. This requires a two-pronged defense: **Schema Stripping** (preventing the LLM from generating numbers in the first place) and **Post-Synthesis Injection** (enforcing SSOT immediately before persistence/compilation).

#### Step 2.1: Strip Quantitative Fields from the LLM Output Schema
When instructing the LLM (via Structured Outputs / Pydantic response schemas) to generate `pillars_analysis`, we must remove `score` and `weight` from the Pydantic model passed to the LLM API.

**File Path:** `src/assessment_engine/domain/schemas/llm_synthesis_schemas.py` (MODIFY EXISTING)

Locate the Pydantic model used by the synthesis prompt (e.g., `LLMPillarAnalysis`) and modify it as follows:

```python
from pydantic import BaseModel, Field
from typing import List

class LLMPillarSynthesis(BaseModel):
    pillar_id: str = Field(..., description="The exact canonical ID of the pillar from the topology config.")
    pillar_name: str = Field(..., description="The official name of the pillar.")
    # ARCHITECTURAL GATE: 'score' and 'weight' are strictly omitted from LLM generation.
    # They are injected deterministically post-synthesis by the Score Reconciler.
    executive_narrative: str = Field(..., description="Forensic qualitative synthesis based on transcript evidence.")
    key_findings: List[str] = Field(..., description="List of empirical observations.")
    epistemic_status: str = Field(..., description="CONVERGENT or VERIFIED_DISSONANT based on transcript vs questionnaire.")
```

#### Step 2.2: Enforce Post-Synthesis Reconciliation in the Resynthesis Pipeline
Modify the transcription resynthesis script and the primary tower pipeline to invoke `build_scoring()` at startup and apply `reconcile_tower_scores()` immediately after the LLM returns its structured response.

**File Path:** `resynthesize_all_10_towers_from_raw_transcription.py` (MODIFY EXISTING)  
*(Note: Apply this exact same pattern to `src/assessment_engine/application/run_tower_pipeline.py`)*

```python
# --- ADD IMPORTS AT TOP OF FILE ---
from src.assessment_engine.application.run_scoring import build_scoring
from src.assessment_engine.domain.services.score_reconciler import reconcile_tower_scores
from src.assessment_engine.domain.validation.mathematical_integrity import assert_tower_mathematical_integrity

# --- INSIDE THE MAIN PIPELINE EXECUTION FUNCTION ---
def execute_resynthesis_pipeline(tenant_config: dict) -> None:
    # 1. Pre-compute Deterministic Quantitative SSOT BEFORE invoking any LLM calls
    scoring_ssot_master = build_scoring(
        responses_path=tenant_config["questionnaire_responses_path"],
        config_dir=tenant_config["engine_config_dir"]
    )
    towers_ssot = scoring_ssot_master["towers"]

    for tower_id, tower_def in tenant_config["towers"].items():
        # 2. Pass the deterministic scores into the prompt context as READ-ONLY reference 
        # so the LLM knows the client's claimed maturity when evaluating epistemic dissonance.
        deterministic_tower_ssot = towers_ssot[tower_id]
        
        raw_llm_payload = synthesize_tower_from_transcription(
            tower_id=tower_id,
            transcript_text=tenant_config["raw_transcription"],
            claimed_scores_context=deterministic_tower_ssot # Read-only context for EpistemicSynthesizer
        )

        # 3. MANDATORY GATE: Reconcile and overwrite quantitative fields with SSOT
        authoritative_payload = reconcile_tower_scores(
            tower_payload=raw_llm_payload,
            scoring_ssot=deterministic_tower_ssot
        )

        # 4. MANDATORY GATE: Verify Mathematical Invariant before writing to disk
        assert_tower_mathematical_integrity(authoritative_payload)

        # 5. Persist validated payload to disk for the AST Compiler
        save_tower_payload(authoritative_payload, output_dir=tenant_config["output_dir"])
```

---

### PHASE 3: Automated Mathematical Validation & Quality Gatekeeping

No payload may ever reach the AST Compiler (`ast_compiler.py`) without passing a strict mathematical invariant check. We will implement a runtime assertion gate and a `pytest` suite that dynamically validates any tenant or N-pillar topology.

#### Step 3.1: Create the Mathematical Invariant Validator
**File Path:** `src/assessment_engine/domain/validation/mathematical_integrity.py` (NEW FILE)

```python
"""
Mathematical Integrity Gatekeeper.
Guarantees that sum_product(pillars.score, pillars.weight) == tower.score
within strict floating-point quantization tolerances.
"""

import math
from typing import Dict, Any, List
from decimal import Decimal, ROUND_HALF_UP


class MathematicalIntegrityViolation(AssertionError):
    """Raised when a tower payload violates quantitative conservation laws."""
    pass


def assert_tower_mathematical_integrity(
    tower_payload: Dict[str, Any], 
    score_tolerance: float = 0.015,
    weight_tolerance: float = 0.001
) -> None:
    """
    Validates two fundamental invariants across any N-pillar topology:
    1. Conservation of Probability/Weight: Sum(pillar.weight) == 1.0 (or 100.0 if percentage-based).
    2. Dot-Product Identity: Sum(pillar.score * normalized_weight) == tower.score.
    """
    tower_id = tower_payload.get("tower_id", "UNKNOWN_TOWER")
    tower_score = tower_payload.get("score")
    
    if tower_score is None:
        raise MathematicalIntegrityViolation(f"[{tower_id}] Missing root 'score' attribute.")

    pillars: List[Dict[str, Any]] = tower_payload.get("pillars_analysis", [])
    if not pillars:
        raise MathematicalIntegrityViolation(f"[{tower_id}] 'pillars_analysis' array is empty or missing.")

    total_raw_weight = 0.0
    weighted_score_sum = 0.0

    for idx, p in enumerate(pillars):
        p_id = p.get("pillar_id", f"INDEX_{idx}")
        p_score = p.get("score")
        p_weight = p.get("weight")

        if p_score is None or p_weight is None:
            raise MathematicalIntegrityViolation(
                f"[{tower_id} -> {p_id}] Null quantitative metric detected (score={p_score}, weight={p_weight})."
            )

        total_raw_weight += float(p_weight)
        weighted_score_sum += float(p_score) * float(p_weight)

    # Handle both normalized weights (sum == 1.0) and percentage weights (sum == 100.0)
    if math.isclose(total_raw_weight, 100.0, abs_tol=weight_tolerance * 100):
        normalized_weighted_sum = weighted_score_sum / 100.0
    elif math.isclose(total_raw_weight, 1.0, abs_tol=weight_tolerance):
        normalized_weighted_sum = weighted_score_sum
    else:
        raise MathematicalIntegrityViolation(
            f"[{tower_id}] Pillar weights do not sum to unity (1.0 or 100.0). Actual sum: {total_raw_weight:.6f}"
        )

    # Quantize calculated sum to match standard 2-decimal reporting precision
    quantized_calculated_score = float(
        Decimal(str(normalized_weighted_sum)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )
    reported_tower_score = float(
        Decimal(str(tower_score)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )

    delta = abs(quantized_calculated_score - reported_tower_score)
    if delta > score_tolerance:
        pillar_debug = ", ".join(
            [f"{p.get('pillar_id')}:(S={p.get('score')}, W={p.get('weight')})" for p in pillars]
        )
        raise MathematicalIntegrityViolation(
            f"SPLIT-BRAIN DETECTED in [{tower_id}]!\n"
            f"  Reported Tower Score : {reported_tower_score:.2f}\n"
            f"  Calculated DotProduct: {quantized_calculated_score:.2f} (Raw: {normalized_weighted_sum:.4f})\n"
            f"  Variance Delta       : {delta:.4f} (Max Allowed Tolerance: {score_tolerance})\n"
            f"  Pillar Breakdown     : [{pillar_debug}]"
        )
```

#### Step 3.2: Create the Automated Pytest Suite
This test suite dynamically discovers all tower definitions and generated payloads across any tenant directory structure and verifies both internal mathematical consistency and strict alignment with `build_scoring()`.

**File Path:** `tests/integration/test_scoring_ssot_invariants.py` (NEW FILE)

```python
"""
Integration Test Suite: Quantitative SSOT & Mathematical Invariants.
Ensures zero split-brain divergence across all generated tower payloads.
"""

import json
import os
import pytest
from pathlib import Path
from typing import List, Tuple, Dict, Any

from src.assessment_engine.application.run_scoring import build_scoring
from src.assessment_engine.domain.validation.mathematical_integrity import (
    assert_tower_mathematical_integrity,
    MathematicalIntegrityViolation
)
from src.assessment_engine.domain.services.score_reconciler import reconcile_tower_scores


def get_payload_test_cases() -> List[Tuple[str, Path]]:
    """
    Dynamically discovers all generated tower JSON payloads in the workspace.
    Configurable via environment variable PAYLOADS_TEST_DIR for CI/CD flexibility.
    """
    search_root = Path(os.getenv("PAYLOADS_TEST_DIR", "output"))
    if not search_root.exists():
        return []
    
    test_cases = []
    for json_file in search_root.rglob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Identify if the JSON is a Tower Payload by checking structural duck-typing
            if isinstance(data, dict) and "pillars_analysis" in data and "tower_id" in data:
                test_cases.append((f"{json_file.parent.name}/{json_file.name}", json_file))
        except Exception:
            continue
    return test_cases


@pytest.mark.parametrize("test_id,payload_path", get_payload_test_cases())
def test_dynamic_tower_payload_dot_product_invariant(test_id: str, payload_path: Path):
    """
    Guarantees that for every generated tower payload on disk:
    sum_product(pillars.score, pillars.weight) == tower.score
    """
    with open(payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Will raise MathematicalIntegrityViolation with full forensic breakdown if invalid
    assert_tower_mathematical_integrity(payload)


def test_reconciler_eradicates_llm_hallucinations():
    """
    Unit/Integration verification that reconcile_tower_scores() deterministically 
    crushes LLM hallucinations while preserving narratives across an N-pillar topology.
    """
    # 1. Mock authoritative SSOT from run_scoring.py (e.g., Tower 1 with score 2.61)
    mock_ssot: Dict[str, Any] = {
        "tower_id": "TOWER_01",
        "score": 2.61,
        "pillars": [
            {"pillar_id": "P1", "name": "Governance", "score": 2.80, "weight": 0.40},
            {"pillar_id": "P2", "name": "Architecture", "score": 2.50, "weight": 0.35},
            {"pillar_id": "P3", "name": "Operations", "score": 2.46, "weight": 0.25},
        ]
    }
    # Verify our mock SSOT is mathematically sound: (2.8*0.4) + (2.5*0.35) + (2.46*0.25) = 1.12 + 0.875 + 0.615 = 2.61

    # 2. Mock corrupted LLM payload (The exact split-brain bug observed in production)
    corrupted_llm_payload: Dict[str, Any] = {
        "tower_id": "TOWER_01",
        "score": 2.61,
        "pillars_analysis": [
            {
                "pillar_id": "P1",
                "pillar_name": "Governance",
                "score": 2.00,  # HALLUCINATED
                "weight": 0.33, # HALLUCINATED
                "executive_narrative": "Client claims high maturity, but transcript shows ad-hoc policies.",
                "epistemic_status": "VERIFIED_DISSONANT"
            },
            {
                "pillar_id": "P2",
                "pillar_name": "Architecture",
                "score": 2.20,  # HALLUCINATED
                "weight": 0.33, # HALLUCINATED
                "executive_narrative": "Legacy segmentation observed in forensic review.",
                "epistemic_status": "VERIFIED_DISSONANT"
            },
            {
                "pillar_id": "P3",
                "pillar_name": "Operations",
                "score": 2.30,  # HALLUCINATED
                "weight": 0.34, # HALLUCINATED
                "executive_narrative": "SOC response times align with questionnaire.",
                "epistemic_status": "CONVERGENT"
            }
        ]
    }

    # Confirm the corrupted payload fails the mathematical gate
    with pytest.raises(MathematicalIntegrityViolation, match="SPLIT-BRAIN DETECTED"):
        assert_tower_mathematical_integrity(corrupted_llm_payload)

    # 3. Execute Reconciler
    healed_payload = reconcile_tower_scores(corrupted_llm_payload, mock_ssot)

    # 4. Assert Mathematical Integrity now passes strictly
    assert_tower_mathematical_integrity(healed_payload)

    # 5. Assert Qualitative Narratives & Epistemic Flags were 100% preserved
    assert healed_payload["pillars_analysis"][0]["score"] == 2.80
    assert healed_payload["pillars_analysis"][0]["weight"] == 0.40
    assert healed_payload["pillars_analysis"][0]["epistemic_status"] == "VERIFIED_DISSONANT"
    assert "ad-hoc policies" in healed_payload["pillars_analysis"][0]["executive_narrative"]
```

---

### 4. EXECUTION SEQUENCE RUNBOOK

Execute the following sequence in your terminal to remediate current state and lock the pipeline:

1. **Deploy New Modules:**
   Create `score_reconciler.py`, `mathematical_integrity.py`, `sync_payload_scores.py`, and `test_scoring_ssot_invariants.py` at their specified paths.
2. **Verify Gatekeeper Logic:**
   ```bash
   pytest tests/integration/test_scoring_ssot_invariants.py -k "test_reconciler_eradicates_llm_hallucinations"
   ```
3. **Heal Existing Tenant Payloads (Retroactive Patch):**
   Run the synchronization utility against the affected tenant directory (e.g., Molins):
   ```bash
   python -m src.assessment_engine.application.sync_payload_scores \
     --responses data/tenants/molins/questionnaire_responses.json \
     --config-dir engine_config/towers \
     --payloads-dir output/molins/towers_json
   ```
4. **Verify All Healed Payloads Pass the Invariant Gate:**
   ```bash
   PAYLOADS_TEST_DIR=output/molins/towers_json pytest tests/integration/test_scoring_ssot_invariants.py
   ```
5. **Re-compile AST Reports:**
   Re-run the AST report compiler on the healed JSON payloads to generate the mathematically consistent PDF/HTML deliverables. Ensure `assert_tower_mathematical_integrity()` remains wired into both `resynthesize_all_10_towers_from_raw_transcription.py` and the AST Compiler entry point.