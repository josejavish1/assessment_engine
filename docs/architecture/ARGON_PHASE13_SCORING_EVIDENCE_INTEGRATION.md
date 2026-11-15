```markdown
# ARGON PHASE 13: DETERMINISTIC SCORING & EVIDENCE LEDGER INTEGRATION

**Document ID**: `ARGON-ARCH-P13-REV1`  
**Author**: Gemini-4-Argon (Chief Systems Architect, Actuarial Fellow & Global Managing Partner)  
**Target Architecture**: Universal Enterprise Due Diligence Engine  
**Status**: **APPROVED FOR EXECUTION**  
**Enforcement Level**: **STRICT / FAIL-CLOSED**  

---

## 1. EXECUTIVE SUMMARY & CONSULTING MANIFESTO

### 1.1 The Actuarial Imperative: Eradicating Stochastic Drift
In Tier-1 M&A and Enterprise Due Diligence, a valuation model or technical risk assessment is only as defensible as its underlying audit trail. Historically, Large Language Models (LLMs) have been deployed as hybrid agents—simultaneously attempting to evaluate raw evidence, compute weighted averages, apply structural penalties, and synthesize narrative prose. 

This conflation of **Actuarial Computation** and **Linguistic Rendering** is an architectural antipattern of the highest order. LLMs are probabilistic token predictors; they are fundamentally incapable of deterministic arithmetic, consistent threshold gating, or invariant application of structural caps (e.g., *Structural Cap 2.0*, *Risk Exposure Multipliers*). Allowing an LLM to calculate or interpolate a maturity score introduces stochastic drift, rendering the final deliverable legally and financially indefensible.

### 1.2 The Paradigm Shift: LLM-as-Calculator $\rightarrow$ LLM-as-Renderer
With the completion of Phase 1 (`src/assessment_engine/domain/scoring_engine.py`), we have established a 100% deterministic mathematical kernel. Phase 2 and Phase 3 execute the definitive decoupling of **Domain Math** from **Language Rendering**:

1. **Deterministic Computation (The Actuarial Kernel)**: The `ScoringEngine` ingests raw KPI evaluations, applies exact pillar weights, evaluates non-compensatory structural caps, and emits an immutable `ScoringAuditTrail`.
2. **Evidence Indexing (The Forensic Ledger)**: Raw, unredacted evidentiary artifacts (interview transcripts, system logs, architecture diagrams) are ingested, hashed, and indexed strictly along the taxonomic hierarchy: `Tower -> Pillar -> KPI`. Lossy, generalized pre-summaries are eradicated.
3. **Constrained Linguistic Synthesis (The Renderer)**: The LLM is stripped of all mathematical agency. It receives the immutable `ScoringAuditTrail` and the exact, KPI-scoped raw evidence excerpts. Its sole mandate is to explain *why* the deterministic score exists by citing the forensic ledger, operating under a **Fail-Closed for Technical Facts** protocol.

```
                     +---------------------------------------+
                     |     Raw Evidence & Matrix Inputs      |
                     +---------------------------------------+
                                   |                   |
          [Deterministic Math]     |                   |     [Forensic Indexing]
                                   v                   v
                     +-------------------+       +-------------------+
                     |   ScoringEngine   |       |  EvidenceLedger   |
                     | (Actuarial Domain)|       | (KPI-Scoped Raw)  |
                     +-------------------+       +-------------------+
                                   |                   |
                Immutable          |                   |     Exact Raw Excerpts
                ScoringAuditTrail  |                   |     & Validation States
                                   v                   v
                     +---------------------------------------+
                     |    Orchestration Injection Layer      |
                     |   (Immutable Context Construction)    |
                     +---------------------------------------+
                                         |
                                         v
                     +---------------------------------------+
                     |         LLM Rendering Engine          |
                     |  (Zero Math Agency / Fail-Closed)     |
                     +---------------------------------------+
```

### 1.3 Core Architectural Invariants
* **Invariant 1 (Linguistic Purity)**: 100% Technical English across all codebases, schemas, logs, docstrings, and system prompts.
* **Invariant 2 (Zero Hardcoding)**: No vertical-specific, company-specific, or static taxonomy assumptions in the orchestration or ledger layers. All routing is driven dynamically by canonical IDs (`tower_id`, `pillar_id`, `kpi_id`).
* **Invariant 3 (Mathematical Immutability)**: If the LLM outputs a number that deviates by even $10^{-4}$ from the `ScoringEngine` output, the pipeline halts immediately via a post-generation verification oracle.
* **Invariant 4 (Evidentiary Traceability)**: Every technical claim rendered by the LLM must map to an indexed `EvidenceItem` with an explicit `ValidationState` (`EXPLORATORY`, `CONTRASTED`, or `EVIDENCED`).

---

## 2. DETAILED IMPLEMENTATION STRATEGY

---

### 2.1 PHASE 2: SCORING ENGINE ORCHESTRATION & PROMPT SANITIZATION

#### 2.1.1 Architectural Objective
Intercept the raw assessment matrices prior to LLM invocation in both the Tower Blueprint and Executive Annex pipelines. Compute the exact mathematical state using `ScoringEngine`, serialize the resulting `ScoringAuditTrail` into a cryptographic-grade JSON block, and inject it into the LLM context as an immutable system constraint.

#### 2.1.2 Exact Modifications to `run_tower_blueprint_engine.py`
The orchestration script `src/assessment_engine/orchestration/run_tower_blueprint_engine.py` must be refactored to eliminate direct pass-through of raw, uncalculated score sheets to the prompt builder.

**Step-by-Step Refactoring Specification:**
1. **Import the Actuarial Kernel**: Import `ScoringEngine`, `TowerEvaluationInput`, and `ScoringAuditTrail` from `src.assessment_engine.domain.scoring_engine`.
2. **Pre-Computation Interception**: In the main execution loop per tower, parse the raw JSON matrix into strict Pydantic domain models (`TowerEvaluationInput`).
3. **Execute Deterministic Scoring**: Invoke `ScoringEngine.evaluate_tower(tower_input)` to produce the `TowerScoringResult` (which encapsulates the `ScoringAuditTrail`).
4. **Construct Immutable Context**: Inject the serialized `ScoringAuditTrail` into a dedicated, non-negotiable XML/JSON boundary tag `<IMMUTABLE_ACTUARIAL_AUDIT_TRAIL>` within `context_str`.
5. **Post-Generation Score Verification**: Implement a deterministic regex/AST parser on the LLM's output to verify that rendered scores match the `ScoringAuditTrail` exactly before persisting to disk.

**Production Implementation (`src/assessment_engine/orchestration/run_tower_blueprint_engine.py`):**

```python
import json
import logging
from pathlib import Path
from typing import Dict, Any

from src.assessment_engine.domain.scoring_engine import (
    ScoringEngine,
    TowerEvaluationInput,
    TowerScoringResult,
)
from src.assessment_engine.domain.evidence_ledger import EvidenceLedger
from src.assessment_engine.infrastructure.llm_client import LLMClient
from src.assessment_engine.orchestration.validators import verify_rendered_scores_match_audit_trail

logger = logging.getLogger(__name__)


class TowerBlueprintOrchestrator:
    """
    Orchestrates the generation of Tower Blueprints by binding deterministic
    actuarial scores with KPI-scoped forensic evidence prior to LLM rendering.
    """

    def __init__(
        self,
        scoring_engine: ScoringEngine,
        evidence_ledger: EvidenceLedger,
        llm_client: LLMClient,
        prompt_template_path: Path,
    ) -> None:
        self._scoring_engine = scoring_engine
        self._evidence_ledger = evidence_ledger
        self._llm_client = llm_client
        self._prompt_template = prompt_template_path.read_text(encoding="utf-8")

    def execute_tower_blueprint(
        self, raw_tower_matrix: Dict[str, Any], output_path: Path
    ) -> TowerScoringResult:
        """
        Executes the deterministic scoring and constrained narrative rendering for a single tower.
        """
        tower_id = raw_tower_matrix.get("tower_id")
        if not tower_id:
            raise ValueError("CRITICAL: Missing 'tower_id' in raw_tower_matrix.")

        logger.info("Initiating deterministic evaluation for Tower: %s", tower_id)

        # 1. Parse raw matrix into strict Actuarial Domain Input
        evaluation_input = TowerEvaluationInput.model_validate(raw_tower_matrix)

        # 2. Compute 100% deterministic scores, bands, and structural caps
        scoring_result: TowerScoringResult = self._scoring_engine.evaluate_tower(
            evaluation_input
        )

        # 3. Retrieve KPI-scoped raw forensic evidence (Phase 3 Integration)
        kpi_evidence_map = self._evidence_ledger.get_evidence_by_tower(tower_id=tower_id)

        # 4. Construct the immutable context string for the LLM Renderer
        context_str = self._build_immutable_context(
            scoring_result=scoring_result,
            kpi_evidence_map=kpi_evidence_map,
        )

        # 5. Invoke LLM strictly as a Linguistic Renderer
        logger.info("Invoking LLM Renderer for Tower: %s", tower_id)
        rendered_markdown = self._llm_client.generate(
            system_prompt=self._prompt_template,
            user_context=context_str,
            temperature=0.0,  # Enforce maximum determinism in token selection
        )

        # 6. Fail-Closed Post-Generation Verification Oracle
        verify_rendered_scores_match_audit_trail(
            rendered_text=rendered_markdown,
            scoring_result=scoring_result,
        )

        # 7. Persist verified artifact and companion actuarial audit trail
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered_markdown, encoding="utf-8")
        
        audit_trail_path = output_path.with_suffix(".audit.json")
        audit_trail_path.write_text(
            scoring_result.model_dump_json(indent=2), encoding="utf-8"
        )

        logger.info("Successfully generated and verified Tower Blueprint: %s", tower_id)
        return scoring_result

    def _build_immutable_context(
        self,
        scoring_result: TowerScoringResult,
        kpi_evidence_map: Dict[str, Any],
    ) -> str:
        """
        Serializes the deterministic audit trail and raw KPI evidence into an
        unambiguous, machine-enforced context payload.
        """
        audit_payload = scoring_result.model_dump(mode="json")
        
        context_blocks = [
            "<IMMUTABLE_ACTUARIAL_AUDIT_TRAIL>",
            json.dumps(audit_payload, indent=2, sort_keys=True),
            "</IMMUTABLE_ACTUARIAL_AUDIT_TRAIL>",
            "",
            "<FORENSIC_EVIDENCE_LEDGER_BY_KPI>",
            json.dumps(kpi_evidence_map, indent=2, sort_keys=True),
            "</FORENSIC_EVIDENCE_LEDGER_BY_KPI>",
        ]
        return "\n".join(context_blocks)
```

#### 2.1.3 Exact Modifications to `run_executive_annex_synthesizer.py`
The Executive Annex synthesizes cross-tower dynamics, enterprise-wide risk exposure, and portfolio-level maturity. Previously, it relied on the LLM to aggregate tower scores into an enterprise score. This is now strictly prohibited.

**Step-by-Step Refactoring Specification:**
1. **Ingest Verified `.audit.json` Artifacts**: `run_executive_annex_synthesizer.py` must not read markdown files to extract scores. It must ingest the `.audit.json` files emitted by `TowerBlueprintOrchestrator` or invoke `ScoringEngine.evaluate_enterprise(tower_results)`.
2. **Compute Enterprise Rollup**: Use `ScoringEngine` to compute the weighted enterprise maturity score, cross-tower systemic caps, and aggregate risk exposure.
3. **Inject Enterprise Audit Trail**: Pass the resulting `EnterpriseScoringResult` inside `<IMMUTABLE_ENTERPRISE_AUDIT_TRAIL>` to the synthesizer prompt.

**Production Implementation (`src/assessment_engine/orchestration/run_executive_annex_synthesizer.py`):**

```python
import json
import logging
from pathlib import Path
from typing import List

from src.assessment_engine.domain.scoring_engine import (
    ScoringEngine,
    TowerScoringResult,
    EnterpriseScoringResult,
)
from src.assessment_engine.domain.evidence_ledger import EvidenceLedger
from src.assessment_engine.infrastructure.llm_client import LLMClient
from src.assessment_engine.orchestration.validators import verify_enterprise_scores_match_audit_trail

logger = logging.getLogger(__name__)


class ExecutiveAnnexSynthesizer:
    """
    Synthesizes the Executive Annex using pre-computed, immutable TowerScoringResults
    and high-criticality evidentiary claims from the EvidenceLedger.
    """

    def __init__(
        self,
        scoring_engine: ScoringEngine,
        evidence_ledger: EvidenceLedger,
        llm_client: LLMClient,
        prompt_template_path: Path,
    ) -> None:
        self._scoring_engine = scoring_engine
        self._evidence_ledger = evidence_ledger
        self._llm_client = llm_client
        self._prompt_template = prompt_template_path.read_text(encoding="utf-8")

    def synthesize_executive_annex(
        self,
        tower_results: List[TowerScoringResult],
        enterprise_weights: dict[str, float],
        output_path: Path,
    ) -> EnterpriseScoringResult:
        """
        Computes deterministic enterprise-wide rollup metrics and renders the Executive Annex.
        """
        if not tower_results:
            raise ValueError("CRITICAL: Cannot synthesize Executive Annex with zero TowerScoringResults.")

        logger.info("Computing deterministic Enterprise Rollup across %d towers.", len(tower_results))

        # 1. Compute Enterprise-level deterministic rollup via ScoringEngine
        enterprise_result: EnterpriseScoringResult = self._scoring_engine.evaluate_enterprise(
            tower_results=tower_results,
            tower_weights=enterprise_weights,
        )

        # 2. Extract critical/cap-triggering KPI evidence across all towers
        critical_kpi_ids = enterprise_result.get_cap_triggering_kpi_ids()
        critical_evidence_payload = self._evidence_ledger.get_evidence_for_kpi_subset(
            kpi_ids=critical_kpi_ids
        )

        # 3. Build immutable context
        context_str = (
            "<IMMUTABLE_ENTERPRISE_AUDIT_TRAIL>\n"
            f"{enterprise_result.model_dump_json(indent=2)}\n"
            "</IMMUTABLE_ENTERPRISE_AUDIT_TRAIL>\n\n"
            "<CRITICAL_CAP_TRIGGERING_EVIDENCE>\n"
            f"{json.dumps(critical_evidence_payload, indent=2, sort_keys=True)}\n"
            "</CRITICAL_CAP_TRIGGERING_EVIDENCE>"
        )

        # 4. Invoke LLM Renderer
        rendered_annex = self._llm_client.generate(
            system_prompt=self._prompt_template,
            user_context=context_str,
            temperature=0.0,
        )

        # 5. Fail-Closed Verification
        verify_enterprise_scores_match_audit_trail(
            rendered_text=rendered_annex,
            enterprise_result=enterprise_result,
        )

        # 6. Persist artifacts
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered_annex, encoding="utf-8")
        output_path.with_suffix(".enterprise_audit.json").write_text(
            enterprise_result.model_dump_json(indent=2), encoding="utf-8"
        )

        return enterprise_result
```

#### 2.1.4 Stripping Score Calculation Logic from Prompt Files
All system prompts in `src/assessment_engine/prompts/` must undergo a surgical purge of mathematical instructions.

**Antipatterns to Purge Immediately:**
* *"Calculate the weighted average of the pillars using the following weights..."*
* *"If any critical KPI is below 2.0, cap the pillar score at 2.0..."*
* *"Determine the maturity band based on the final score (e.g., 1.0-1.9 = Initial)..."*
* *"Estimate the score if evidence is partial..."*

**Replacement System Prompt Directive (Mandatory Injection into all Blueprint/Annex Prompts):**

```markdown
### ACTUARIAL SCORE IMMUTABILITY MANDATE (FAIL-CLOSED PROTOCOL)
1. **ZERO MATHEMATICAL AGENCY**: You are strictly prohibited from calculating, rounding, interpolating, averaging, or modifying any numerical score, weight, penalty, structural cap, or maturity band.
2. **SINGLE SOURCE OF TRUTH**: All numerical values, maturity bands, cap activations, and audit equations are pre-computed by a deterministic actuarial kernel and provided to you inside the `<IMMUTABLE_ACTUARIAL_AUDIT_TRAIL>` block.
3. **EXACT TRANSCRIPTION**: Whenever you render a Tower Score, Pillar Score, KPI Score, Weight, or Maturity Band in prose or Markdown tables, you MUST transcribe the exact floating-point value (to two decimal places, e.g., `2.35`) and exact string label provided in `<IMMUTABLE_ACTUARIAL_AUDIT_TRAIL>`.
4. **EXPLANATORY MANDATE**: Your sole analytical function regarding scores is to explain *why* the deterministic engine arrived at that exact figure by referencing the `applied_caps`, `penalty_triggers`, and the corresponding raw forensic excerpts inside `<FORENSIC_EVIDENCE_LEDGER_BY_KPI>`.
5. **EVIDENTIARY FAIL-CLOSED RULE**: You must only cite facts, metrics, and architectural states explicitly present in `<FORENSIC_EVIDENCE_LEDGER_BY_KPI>`. If a KPI has `validation_state: "EXPLORATORY"` or lacks documentary verification, you must explicitly state that the finding is unverified management assertion and explain how the deterministic engine penalized or capped the score accordingly.
```

---

### 2.2 PHASE 3: RAW EVIDENCE INGESTION & THE KPI-INDEXED EVIDENCE LEDGER

#### 2.2.1 Architectural Objective
Eliminate lossy intermediate summaries. Re-architect the ingestion and ledger pipelines (`build_case_input.py` and `build_evidence_ledger.py`) so that every raw evidentiary excerpt (interview transcript verbatim quote, configuration file snippet, audit log) is cryptographically fingerprinted, assigned an actuarial `ValidationState`, and indexed strictly along the canonical coordinate system: `tower_id -> pillar_id -> kpi_id`.

#### 2.2.2 Domain Schema Definitions (`src/assessment_engine/domain/evidence_models.py`)
We define strict Pydantic v2 models enforcing immutability (`frozen=True`), cryptographic integrity (`sha256_hash`), and explicit epistemic states (`ValidationState`).

```python
import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, computed_field, model_validator


class ValidationState(str, Enum):
    """
    Epistemic status of a technical claim or evidentiary artifact.
    Ordered by increasing forensic reliability.
    """
    EXPLORATORY = "EXPLORATORY"  # Single-source verbal assertion (e.g., uncorroborated interview quote).
    CONTRASTED = "CONTRASTED"    # Cross-referenced across multiple independent interviews or secondary docs.
    EVIDENCED = "EVIDENCED"      # Hard primary production artifact (e.g., Terraform state, CI/CD log, APM export).


class SourceModality(str, Enum):
    """Classification of the raw evidentiary source."""
    INTERVIEW_TRANSCRIPT = "INTERVIEW_TRANSCRIPT"
    PRODUCTION_CONFIG = "PRODUCTION_CONFIG"
    ARCHITECTURE_DIAGRAM = "ARCHITECTURE_DIAGRAM"
    TELEMETRY_LOG = "TELEMETRY_LOG"
    POLICY_DOCUMENT = "POLICY_DOCUMENT"
    FINANCIAL_LEDGER = "FINANCIAL_LEDGER"


class EvidenceItem(BaseModel):
    """
    Represents a single, immutable, raw evidentiary excerpt tied to a specific taxonomic coordinate.
    Contains ZERO summarized or paraphrased text—only verbatim source material.
    """
    model_config = {"frozen": True, "extra": "forbid"}

    evidence_id: str = Field(..., description="Globally unique deterministic ID (e.g., EV-T01-P02-K04-001).")
    tower_id: str = Field(..., min_length=2, description="Canonical Tower Identifier (e.g., 'T01_CLOUD_INFRA').")
    pillar_id: str = Field(..., min_length=2, description="Canonical Pillar Identifier (e.g., 'P01_RESILIENCE').")
    kpi_id: str = Field(..., min_length=2, description="Canonical KPI Identifier (e.g., 'KPI_01_02_MULTI_AZ').")
    
    source_modality: SourceModality
    source_document_uri: str = Field(..., description="Relative path or URI to the raw origin file.")
    source_locator: str = Field(
        ...,
        description="Exact coordinate in source (e.g., 'lines 142-158', 'timestamp 00:14:22-00:15:05')."
    )
    speaker_or_author: Optional[str] = Field(
        default=None, description="Role or identifier of speaker/author (e.g., 'VP of Infrastructure')."
    )
    raw_verbatim_excerpt: str = Field(
        ..., min_length=10, description="Exact, unedited verbatim excerpt from the source artifact."
    )
    validation_state: ValidationState = Field(
        ..., description="Forensic validation state assigned during ingestion."
    )
    ingested_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @computed_field
    @property
    def content_sha256(self) -> str:
        """Cryptographic fingerprint of the coordinate and verbatim excerpt to guarantee non-tampering."""
        payload = f"{self.tower_id}|{self.pillar_id}|{self.kpi_id}|{self.source_document_uri}|{self.raw_verbatim_excerpt}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class Claim(BaseModel):
    """
    An analytical or technical assertion mapped to a specific KPI, backed by one or more EvidenceItems.
    """
    model_config = {"frozen": True, "extra": "forbid"}

    claim_id: str = Field(..., description="Unique Claim Identifier (e.g., CLM-KPI_01_02-01).")
    tower_id: str
    pillar_id: str
    kpi_id: str
    assertion_statement: str = Field(
        ..., description="Precise technical statement of fact subject to verification."
    )
    supporting_evidence_ids: List[str] = Field(
        ..., min_length=1, description="List of EvidenceItem IDs substantiating this claim."
    )
    contradicting_evidence_ids: List[str] = Field(
        default_factory=list, description="List of EvidenceItem IDs that refute or qualify this claim."
    )
    effective_validation_state: ValidationState = Field(
        ..., description="Derived epistemic state based on supporting and contradicting evidence."
    )

    @model_validator(mode="after")
    def validate_epistemic_consistency(self) -> "Claim":
        if not self.supporting_evidence_ids:
            raise ValueError(f"Claim {self.claim_id} must reference at least one supporting EvidenceItem.")
        return self


class KPIEvidenceBundle(BaseModel):
    """
    The complete forensic package for a single KPI, injected directly into the LLM context.
    """
    model_config = {"frozen": True, "extra": "forbid"}

    tower_id: str
    pillar_id: str
    kpi_id: str
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    claims: List[Claim] = Field(default_factory=list)
    highest_validation_state: Optional[ValidationState] = None
    has_evidentiary_contradictions: bool = False
```

#### 2.2.3 Re-Architecting `build_evidence_ledger.py`
The module `src/assessment_engine/domain/evidence_ledger.py` (invoked by `src/assessment_engine/orchestration/build_evidence_ledger.py`) is responsible for constructing the hierarchical index `tower_id -> pillar_id -> kpi_id` and resolving epistemic states deterministically.

**Key Algorithmic Mechanisms:**
1. **Hierarchical O(1) Indexing**: Maintains an internal 3-level dictionary `_index[tower_id][pillar_id][kpi_id] -> KPIEvidenceBundle` plus a flat `_kpi_lookup[kpi_id] -> KPIEvidenceBundle` for instant retrieval.
2. **Automatic Validation State Promotion/Demotion**:
   * If a KPI only possesses `INTERVIEW_TRANSCRIPT` items from a single source, its maximum state is `EXPLORATORY`.
   * If corroborated across $\ge 2$ distinct speakers/documents without contradiction, it can reach `CONTRASTED`.
   * Only when backed by `PRODUCTION_CONFIG`, `TELEMETRY_LOG`, or verified `ARCHITECTURE_DIAGRAM` does it achieve `EVIDENCED`.

**Production Implementation (`src/assessment_engine/domain/evidence_ledger.py`):**

```python
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Iterable, Any, Optional

from src.assessment_engine.domain.evidence_models import (
    EvidenceItem,
    Claim,
    KPIEvidenceBundle,
    ValidationState,
)


class EvidenceLedger:
    """
    Immutable, strictly indexed Forensic Evidence Ledger.
    Indexes raw EvidenceItems and Claims strictly by: tower_id -> pillar_id -> kpi_id.
    """

    _STATE_RANK = {
        ValidationState.EXPLORATORY: 1,
        ValidationState.CONTRASTED: 2,
        ValidationState.EVIDENCED: 3,
    }

    def __init__(
        self,
        evidence_items: Iterable[EvidenceItem],
        claims: Optional[Iterable[Claim]] = None,
    ) -> None:
        self._items_by_id: Dict[str, EvidenceItem] = {}
        self._claims_by_id: Dict[str, Claim] = {}
        
        # Hierarchical Index: tower_id -> pillar_id -> kpi_id -> KPIEvidenceBundle
        self._hierarchy: Dict[str, Dict[str, Dict[str, KPIEvidenceBundle]]] = defaultdict(
            lambda: defaultdict(dict)
        )
        # Direct KPI Lookup: kpi_id -> KPIEvidenceBundle
        self._kpi_index: Dict[str, KPIEvidenceBundle] = {}

        self._build_index(evidence_items, claims or [])

    def _build_index(
        self,
        evidence_items: Iterable[EvidenceItem],
        claims: Iterable[Claim],
    ) -> None:
        grouped_items: Dict[tuple[str, str, str], List[EvidenceItem]] = defaultdict(list)
        grouped_claims: Dict[tuple[str, str, str], List[Claim]] = defaultdict(list)

        for item in evidence_items:
            if item.evidence_id in self._items_by_id:
                raise ValueError(f"Duplicate EvidenceItem ID detected: {item.evidence_id}")
            self._items_by_id[item.evidence_id] = item
            coord = (item.tower_id, item.pillar_id, item.kpi_id)
            grouped_items[coord].append(item)

        for claim in claims:
            if claim.claim_id in self._claims_by_id:
                raise ValueError(f"Duplicate Claim ID detected: {claim.claim_id}")
            # Verify referential integrity against EvidenceItems
            for ev_id in claim.supporting_evidence_ids + claim.contradicting_evidence_ids:
                if ev_id not in self._items_by_id:
                    raise KeyError(
                        f"Claim {claim.claim_id} references non-existent EvidenceItem {ev_id}."
                    )
                ev_item = self._items_by_id[ev_id]
                if (ev_item.tower_id, ev_item.pillar_id, ev_item.kpi_id) != (
                    claim.tower_id,
                    claim.pillar_id,
                    claim.kpi_id,
                ):
                    raise ValueError(
                        f"Taxonomic coordinate mismatch between Claim {claim.claim_id} "
                        f"and EvidenceItem {ev_id}."
                    )
            self._claims_by_id[claim.claim_id] = claim
            coord = (claim.tower_id, claim.pillar_id, claim.kpi_id)
            grouped_claims[coord].append(claim)

        all_coords = set(grouped_items.keys()).union(set(grouped_claims.keys()))

        for tower_id, pillar_id, kpi_id in sorted(all_coords):
            k_items = sorted(grouped_items[(tower_id, pillar_id, kpi_id)], key=lambda x: x.evidence_id)
            k_claims = sorted(grouped_claims[(tower_id, pillar_id, kpi_id)], key=lambda x: x.claim_id)

            highest_state: Optional[ValidationState] = None
            if k_items:
                highest_state = max(k_items, key=lambda x: self._STATE_RANK[x.validation_state]).validation_state

            has_contradictions = any(len(c.contradicting_evidence_ids) > 0 for c in k_claims)

            bundle = KPIEvidenceBundle(
                tower_id=tower_id,
                pillar_id=pillar_id,
                kpi_id=kpi_id,
                evidence_items=k_items,
                claims=k_claims,
                highest_validation_state=highest_state,
                has_evidentiary_contradictions=has_contradictions,
            )

            self._hierarchy[tower_id][pillar_id][kpi_id] = bundle
            if kpi_id in self._kpi_index:
                raise ValueError(
                    f"KPI ID '{kpi_id}' is not globally unique across towers/pillars."
                )
            self._kpi_index[kpi_id] = bundle

    def get_kpi_bundle(self, tower_id: str, pillar_id: str, kpi_id: str) -> KPIEvidenceBundle:
        """
        Retrieves the exact KPIEvidenceBundle for a canonical coordinate.
        Returns an empty bundle (Fail-Closed signal) if no evidence exists for the coordinate.
        """
        bundle = self._hierarchy.get(tower_id, {}).get(pillar_id, {}).get(kpi_id)
        if bundle is None:
            return KPIEvidenceBundle(
                tower_id=tower_id,
                pillar_id=pillar_id,
                kpi_id=kpi_id,
                evidence_items=[],
                claims=[],
                highest_validation_state=None,
                has_evidentiary_contradictions=False,
            )
        return bundle

    def get_evidence_by_tower(self, tower_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Returns a deterministic dictionary structured as:
        { pillar_id: { kpi_id: KPIEvidenceBundle.model_dump() } }
        Strictly scoped to the requested tower_id.
        """
        if tower_id not in self._hierarchy:
            return {}
        
        result: Dict[str, Dict[str, Any]] = {}
        for pillar_id, kpi_map in sorted(self._hierarchy[tower_id].items()):
            result[pillar_id] = {
                kpi_id: bundle.model_dump(mode="json")
                for kpi_id, bundle in sorted(kpi_map.items())
            }
        return result

    def get_evidence_for_kpi_subset(self, kpi_ids: Iterable[str]) -> Dict[str, Any]:
        """
        Retrieves serialized KPIEvidenceBundles for a specific list of KPIs
        (e.g., cap-triggering KPIs for the Executive Annex).
        """
        return {
            kpi_id: self._kpi_index[kpi_id].model_dump(mode="json")
            for kpi_id in sorted(set(kpi_ids))
            if kpi_id in self._kpi_index
        }

    def export_ledger_json(self, output_path: Path) -> None:
        """Persists the entire indexed ledger to disk for forensic auditability."""
        full_dump = {
            tower_id: self.get_evidence_by_tower(tower_id)
            for tower_id in sorted(self._hierarchy.keys())
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(full_dump, indent=2, sort_keys=True), encoding="utf-8")
```

#### 2.2.4 Re-Architecting `build_case_input.py`
The script `src/assessment_engine/orchestration/build_case_input.py` is responsible for assembling the raw assessment inputs from the Data Room (transcripts, technical artifacts, raw KPI observation tables) into the canonical case payload consumed by `ScoringEngine` and `EvidenceLedger`.

**Key Architectural Changes:**
1. **Deprecation of Free-Text Summary Fields**: Any field named `executive_summary`, `general_notes`, or `pillar_overview` in the raw ingestion files is ignored and stripped.
2. **Deterministic Validation State Epistemic Classifier**: When ingesting raw evidence records, `build_case_input.py` validates that every KPI evaluation in the matrix links to concrete `EvidenceItem` records and computes the epistemic ceiling for the `ScoringEngine`. If a KPI claims a score $> 2.0$ (`Repeatable`) in the raw input, but the `EvidenceLedger` shows `highest_validation_state == ValidationState.EXPLORATORY` (or `None`), `build_case_input.py` flags an `unverified_assertion_flag = True` on the KPI input so `ScoringEngine` deterministically applies the **Evidentiary Penalty / Cap**.

**Production Implementation (`src/assessment_engine/orchestration/build_case_input.py`):**

```python
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from src.assessment_engine.domain.evidence_models import (
    EvidenceItem,
    Claim,
    ValidationState,
)
from src.assessment_engine.domain.evidence_ledger import EvidenceLedger

logger = logging.getLogger(__name__)


class CaseInputBuilder:
    """
    Ingests raw Data Room extractions (verbatim transcripts, artifact logs, raw KPI matrices),
    builds the KPI-indexed EvidenceLedger, and emits sanitized, deterministic Case Input payloads.
    """

    def __init__(self, raw_evidence_path: Path, raw_matrix_dir: Path) -> None:
        self._raw_evidence_path = raw_evidence_path
        self._raw_matrix_dir = raw_matrix_dir

    def build_ledger_and_case_inputs(
        self, output_case_dir: Path, ledger_output_path: Path
    ) -> EvidenceLedger:
        """
        1. Loads and validates all raw EvidenceItems and Claims.
        2. Constructs and persists the EvidenceLedger.
        3. Enriches raw tower matrices with deterministic epistemic flags from the ledger.
        """
        raw_ledger_data = json.loads(self._raw_evidence_path.read_text(encoding="utf-8"))

        evidence_items = [
            EvidenceItem.model_validate(item)
            for item in raw_ledger_data.get("evidence_items", [])
        ]
        claims = [
            Claim.model_validate(claim)
            for claim in raw_ledger_data.get("claims", [])
        ]

        ledger = EvidenceLedger(evidence_items=evidence_items, claims=claims)
        ledger.export_ledger_json(ledger_output_path)
        logger.info("Indexed %d EvidenceItems and %d Claims into EvidenceLedger.", len(evidence_items), len(claims))

        output_case_dir.mkdir(parents=True, exist_ok=True)

        for matrix_file in sorted(self._raw_matrix_dir.glob("*.json")):
            raw_matrix = json.loads(matrix_file.read_text(encoding="utf-8"))
            sanitized_matrix = self._bind_evidence_metadata_to_matrix(raw_matrix, ledger)
            
            target_path = output_case_dir / matrix_file.name
            target_path.write_text(
                json.dumps(sanitized_matrix, indent=2, sort_keys=True), encoding="utf-8"
            )

        return ledger

    def _bind_evidence_metadata_to_matrix(
        self, raw_matrix: Dict[str, Any], ledger: EvidenceLedger
    ) -> Dict[str, Any]:
        """
        Strips any legacy summary prose from the matrix and binds exact epistemic
        validation states from the EvidenceLedger to each KPI prior to ScoringEngine execution.
        """
        tower_id = raw_matrix["tower_id"]
        sanitized_pillars: List[Dict[str, Any]] = []

        for pillar in raw_matrix.get("pillars", []):
            pillar_id = pillar["pillar_id"]
            sanitized_kpis: List[Dict[str, Any]] = []

            for kpi in pillar.get("kpis", []):
                kpi_id = kpi["kpi_id"]
                bundle = ledger.get_kpi_bundle(
                    tower_id=tower_id, pillar_id=pillar_id, kpi_id=kpi_id
                )

                highest_state = (
                    bundle.highest_validation_state.value
                    if bundle.highest_validation_state
                    else "NONE"
                )

                # Construct pure actuarial KPI input (stripping any free-text notes/summaries)
                sanitized_kpi = {
                    "kpi_id": kpi_id,
                    "kpi_name": kpi["kpi_name"],
                    "raw_observed_score": float(kpi["raw_observed_score"]),
                    "weight": float(kpi["weight"]),
                    "is_critical_cap_trigger": bool(kpi.get("is_critical_cap_trigger", False)),
                    "highest_validation_state": highest_state,
                    "evidence_count": len(bundle.evidence_items),
                    "has_evidentiary_contradictions": bundle.has_evidentiary_contradictions,
                    "linked_evidence_ids": [ev.evidence_id for ev in bundle.evidence_items],
                }
                sanitized_kpis.append(sanitized_kpi)

            sanitized_pillars.append(
                {
                    "pillar_id": pillar_id,
                    "pillar_name": pillar["pillar_name"],
                    "weight": float(pillar["weight"]),
                    "kpis": sanitized_kpis,
                }
            )

        return {
            "tower_id": tower_id,
            "tower_name": raw_matrix["tower_name"],
            "pillars": sanitized_pillars,
        }
```

---

## 3. QUALITY GATES & VERIFICATION ORACLES

To guarantee zero regressions, 100% deterministic math adherence, and strict KPI-scoped evidentiary integrity, we introduce two mandatory layers of defense:
1. **Runtime Post-Generation Verification Oracles** (`src/assessment_engine/orchestration/validators.py`)
2. **Automated Pytest Verification Suites** (`tests/verification/test_phase2_phase3_integration.py`)

### 3.1 Runtime Verification Oracle (`src/assessment_engine/orchestration/validators.py`)
This module acts as a circuit breaker after the LLM returns generated Markdown. If the LLM fabricates a score, omits a mandatory KPI score, or cites an `EvidenceItem` ID that does not belong to the tower under evaluation, the pipeline raises a `DeterministicVerificationError` and halts.

```python
import re
from typing import Set
from src.assessment_engine.domain.scoring_engine import (
    TowerScoringResult,
    EnterpriseScoringResult,
)


class DeterministicVerificationError(RuntimeError):
    """Raised when LLM output violates actuarial or evidentiary immutability invariants."""


def verify_rendered_scores_match_audit_trail(
    rendered_text: str,
    scoring_result: TowerScoringResult,
     allowed_evidence_ids: Set[str] | None = None,
) -> None:
    """
    Fail-Closed Oracle: Verifies that the LLM rendered the exact Tower Score,
    Maturity Band, Pillar Scores, and KPI Scores computed by ScoringEngine.
    """
    expected_tower_score = f"{scoring_result.final_score:.2f}"
    if expected_tower_score not in rendered_text:
        raise DeterministicVerificationError(
            f"ACTUARIAL VIOLATION: Expected Tower final_score '{expected_tower_score}' "
            f"for {scoring_result.tower_id} was not found verbatim in rendered output."
        )

    if scoring_result.maturity_band not in rendered_text:
        raise DeterministicVerificationError(
            f"ACTUARIAL VIOLATION: Expected maturity_band '{scoring_result.maturity_band}' "
            f"for {scoring_result.tower_id} was not found verbatim in rendered output."
        )

    for pillar in scoring_result.pillar_results:
        expected_pillar_score = f"{pillar.final_score:.2f}"
        if pillar.pillar_id not in rendered_text or expected_pillar_score not in rendered_text:
            raise DeterministicVerificationError(
                f"ACTUARIAL VIOLATION: Pillar '{pillar.pillar_id}' or its exact score "
                f"'{expected_pillar_score}' missing/mutated in rendered output."
            )

        for kpi in pillar.kpi_results:
            expected_kpi_score = f"{kpi.final_score:.2f}"
            if kpi.kpi_id not in rendered_text or expected_kpi_score not in rendered_text:
                raise DeterministicVerificationError(
                    f"ACTUARIAL VIOLATION: KPI '{kpi.kpi_id}' or its exact score "
                    f"'{expected_kpi_score}' missing/mutated in rendered output."
                )

    # Verify zero hallucinated Evidence IDs if allowed set is provided
    if allowed_evidence_ids is not None:
        cited_ids = set(re.findall(r"\bEV-[A-Z0-9_-]+\b", rendered_text))
        unauthorized_ids = cited_ids - allowed_evidence_ids
        if unauthorized_ids:
            raise DeterministicVerificationError(
                f"FORENSIC VIOLATION: LLM cited unauthorized or hallucinated Evidence IDs: "
                f"{sorted(unauthorized_ids)}"
            )


def verify_enterprise_scores_match_audit_trail(
    rendered_text: str,
    enterprise_result: EnterpriseScoringResult,
) -> None:
    """
    Fail-Closed Oracle for Executive Annex synthesis.
    """
    expected_ent_score = f"{enterprise_result.enterprise_final_score:.2f}"
    if expected_ent_score not in rendered_text:
        raise DeterministicVerificationError(
            f"ACTUARIAL VIOLATION: Expected Enterprise Score '{expected_ent_score}' "
            f"missing from Executive Annex."
        )
```

### 3.2 Deterministic Pytest Suite (`tests/verification/test_phase2_phase3_integration.py`)
The following test suite serves as the formal gatekeeper in CI/CD. All tests must pass with 100% coverage over the new orchestration and ledger logic before Phase 2 and Phase 3 can be merged.

```python
import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from src.assessment_engine.domain.evidence_models import (
    EvidenceItem,
    Claim,
    ValidationState,
    SourceModality,
)
from src.assessment_engine.domain.evidence_ledger import EvidenceLedger
from src.assessment_engine.orchestration.validators import (
    verify_rendered_scores_match_audit_trail,
    DeterministicVerificationError,
)


@pytest.fixture
def sample_evidence_items() -> list[EvidenceItem]:
    return [
        EvidenceItem(
            evidence_id="EV-T01-P01-K01-001",
            tower_id="T01_INFRA",
            pillar_id="P01_CLOUD",
            kpi_id="KPI_MULTI_AZ",
            source_modality=SourceModality.INTERVIEW_TRANSCRIPT,
            source_document_uri="interviews/vp_infra_2025.txt",
            source_locator="lines 45-52",
            speaker_or_author="VP of Infrastructure",
            raw_verbatim_excerpt="We currently run all primary databases in a single availability zone in us-east-1a.",
            validation_state=ValidationState.EXPLORATORY,
        ),
        EvidenceItem(
            evidence_id="EV-T01-P01-K01-002",
            tower_id="T01_INFRA",
            pillar_id="P01_CLOUD",
            kpi_id="KPI_MULTI_AZ",
            source_modality=SourceModality.PRODUCTION_CONFIG,
            source_document_uri="terraform/rds_prod.tf",
            source_locator="lines 12-18",
            speaker_or_author="Terraform State Export",
            raw_verbatim_excerpt='resource "aws_db_instance" "prod" { multi_az = false, availability_zone = "us-east-1a" }',
            validation_state=ValidationState.EVIDENCED,
        ),
    ]


def test_evidence_ledger_hierarchical_kpi_indexing(sample_evidence_items: list[EvidenceItem]) -> None:
    """
    Gate 1: Verifies that EvidenceLedger indexes items strictly by tower_id -> pillar_id -> kpi_id
    and computes the highest ValidationState deterministically without lossy summarization.
    """
    claim = Claim(
        claim_id="CLM-001",
        tower_id="T01_INFRA",
        pillar_id="P01_CLOUD",
        kpi_id="KPI_MULTI_AZ",
        assertion_statement="Production RDS instances lack Multi-AZ failover configuration.",
        supporting_evidence_ids=["EV-T01-P01-K01-001", "EV-T01-P01-K01-002"],
        effective_validation_state=ValidationState.EVIDENCED,
    )

    ledger = EvidenceLedger(evidence_items=sample_evidence_items, claims=[claim])
    bundle = ledger.get_kpi_bundle("T01_INFRA", "P01_CLOUD", "KPI_MULTI_AZ")

    assert len(bundle.evidence_items) == 2
    assert bundle.highest_validation_state == ValidationState.EVIDENCED
    assert bundle.has_evidentiary_contradictions is False
    assert 'multi_az = false' in bundle.evidence_items[1].raw_verbatim_excerpt


def test_evidence_ledger_rejects_cross_coordinate_claim_contamination(
    sample_evidence_items: list[EvidenceItem],
) -> None:
    """
    Gate 2: Verifies that a Claim cannot cite an EvidenceItem belonging to a different KPI.
    """
    invalid_claim = Claim(
        claim_id="CLM-INVALID",
        tower_id="T01_INFRA",
        pillar_id="P01_CLOUD",
        kpi_id="KPI_OTHER_UNRELATED",
        assertion_statement="Mismatched KPI coordinate claim.",
        supporting_evidence_ids=["EV-T01-P01-K01-001"],
        effective_validation_state=ValidationState.EXPLORATORY,
    )

    with pytest.raises(ValueError, match="Taxonomic coordinate mismatch"):
        EvidenceLedger(evidence_items=sample_evidence_items, claims=[invalid_claim])


def test_verification_oracle_halts_on_llm_score_hallucination() -> None:
    """
    Gate 3: Verifies that if the LLM mutates or rounds a deterministic score from ScoringEngine,
    the post-generation oracle immediately halts execution with DeterministicVerificationError.
    """
    mock_kpi = MagicMock(kpi_id="KPI_MULTI_AZ", final_score=1.50)
    mock_pillar = MagicMock(pillar_id="P01_CLOUD", final_score=1.85, kpi_results=[mock_kpi])
    mock_tower_result = MagicMock(
        tower_id="T01_INFRA",
        final_score=1.85,
        maturity_band="Initial",
        pillar_results=[mock_pillar],
    )

    # LLM hallucinates 1.90 instead of the deterministic 1.85
    corrupted_llm_markdown = """
    # Tower T01_INFRA Blueprint
    **Final Score**: 1.90 (Initial)
    - Pillar P01_CLOUD: 1.90
      - KPI_MULTI_AZ: 1.50 (EV-T01-P01-K01-002)
    """

    with pytest.raises(DeterministicVerificationError, match="ACTUARIAL VIOLATION"):
        verify_rendered_scores_match_audit_trail(
            rendered_text=corrupted_llm_markdown,
            scoring_result=mock_tower_result,
            allowed_evidence_ids={"EV-T01-P01-K01-002"},
        )


def test_verification_oracle_halts_on_unauthorized_evidence_citation() -> None:
    """
    Gate 4: Verifies that if the LLM cites an Evidence ID not present in the KPI ledger,
    the oracle halts execution.
    """
    mock_kpi = MagicMock(kpi_id="KPI_MULTI_AZ", final_score=1.50)
    mock_pillar = MagicMock(pillar_id="P01_CLOUD", final_score=1.85, kpi_results=[mock_kpi])
    mock_tower_result = MagicMock(
        tower_id="T01_INFRA",
        final_score=1.85,
        maturity_band="Initial",
        pillar_results=[mock_pillar],
    )

    hallucinated_evidence_markdown = """
    # Tower T01_INFRA Blueprint
    **Final Score**: 1.85 (Initial)
    - Pillar P01_CLOUD: 1.85
      - KPI_MULTI_AZ: 1.50 (Citing fabricated evidence EV-T99-P99-K99-999)
    """

    with pytest.raises(DeterministicVerificationError, match="FORENSIC VIOLATION"):
        verify_rendered_scores_match_audit_trail(
            rendered_text=hallucinated_evidence_markdown,
            scoring_result=mock_tower_result,
            allowed_evidence_ids={"EV-T01-P01-K01-001", "EV-T01-P01-K01-002"},
        )
```

---

## 4. EXECUTION ROADMAP & SIGN-OFF CRITERIA

| Step | Component | Target File(s) | Verification Criterion |
| :--- | :--- | :--- | :--- |
| **1** | Forensic Schemas | `src/assessment_engine/domain/evidence_models.py` | 100% Pydantic v2 strict validation, SHA-256 computed fingerprinting. |
| **2** | Ledger Engine | `src/assessment_engine/domain/evidence_ledger.py` | O(1) lookup by `tower_id -> pillar_id -> kpi_id`; zero cross-KPI leakage. |
| **3** | Case Input Builder | `src/assessment_engine/orchestration/build_case_input.py` | Strips all legacy summary fields; injects ledger epistemic states into matrix. |
| **4** | Prompt Sanitization | `src/assessment_engine/prompts/*.md` | Complete removal of arithmetic rules; injection of Fail-Closed Mandate. |
| **5** | Orchestration Binding | `run_tower_blueprint_engine.py`, `run_executive_annex_synthesizer.py` | Pre-computation via `ScoringEngine`; context injection; Oracle validation. |
| **6** | CI/CD Gate | `tests/verification/test_phase2_phase3_integration.py` | `pytest` passes 100% with zero warnings or regressions. |
```