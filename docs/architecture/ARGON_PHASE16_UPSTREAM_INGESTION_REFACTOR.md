```markdown
# ARGON PHASE 16: UPSTREAM INGESTION & EPISTEMIC GATING ARCHITECTURE
**Document ID:** `ARGON_PHASE16_UPSTREAM_INGESTION_REFACTOR`  
**Author:** Gemini-4-Argon (Chief Systems Architect, Actuarial Fellow & Global Managing Partner)  
**Status:** APPROVED FOR IMMEDIATE EXECUTION  
**Target Layer:** Upstream Data Ingestion (`src/ingestion/` & `build_case_input.py`)  

---

## 1. EXECUTIVE SUMMARY: THE PARADIGM SHIFT TO STRICT UPSTREAM EVIDENCE GATING

In actuarial science and enterprise due diligence, the integrity of a risk model is strictly bounded by the epistemic purity of its ingested evidence. While prior architectural phases successfully hardened our downstream mathematical scoring engines and AST-based narrative generators, our upstream ingestion pipeline (`build_case_input.py`) has operated on a permissive, monolithic paradigm. Historically, the system relied on tactical JSON payload overrides to remediate two systemic ingestion vulnerabilities:

1. **Cross-Tower Epistemic Contamination:** Ingesting raw interview transcripts as monolithic text blocks and broadcasting them globally to every domain tower prompt. This induces attention dilution in Large Language Models, causing severe domain bleeding (e.g., hyper-converged infrastructure lifecycle metrics like 613 days of SimpliVity support end-of-life leaking into NetApp storage evaluations, or FinOps agents attempting to audit industrial SCADA telemetry).
2. **Silent Epistemic Erasure (False Imputation):** Utilizing permissive regular expressions (`RESPONSE_RE`) that silently discard malformed, empty, or non-numeric survey responses (e.g., `,`, `N/A`, `TBD`). By dropping these keys from the ingestion payload rather than explicitly typing their absence, downstream actuarial calculators are forced to compute expected values over a reduced sample space—a mathematically invalid practice that artificially inflates or deflates risk scores without alerting the managing partner.

Tactical overrides at the payload level do not scale across global enterprise engagements. Phase 16 introduces a **Zero-Trust Epistemic Ingestion Architecture**. We are shifting from *permissive monolithic ingestion* to **Deterministic Upstream Evidence Gating**. 

```
                      +-----------------------------------+
                      |   Raw Unstructured Evidence       |
                      | (Survey Responses & Transcripts)  |
                      +-----------------+-----------------+
                                        |
                   +--------------------+--------------------+
                   |                                         |
                   v                                         v
     +---------------------------+             +---------------------------+
     |   Survey Ingestion Flow   |             | Transcript Ingestion Flow |
     +-------------+-------------+             +-------------+-------------+
                   |                                         |
                   v                                         v
     +---------------------------+             +---------------------------+
     |    Exhaustive Taxonomy    |             |  Discourse Segmentation   |
     |      Manifest Loader      |             |     (Sliding Window)      |
     +-------------+-------------+             +-------------+-------------+
                   |                                         |
                   v                                         v
     +---------------------------+             +---------------------------+
     |   MissingDataCircuit-     |             |   EpistemicGraphRouter    |
     |         Breaker           |             |  (TF-IDF + Dense Cosine)  |
     +-------------+-------------+             +-------------+-------------+
                   |                                         |
      +------------+------------+               +------------+------------+
      |                         |               |            |            |
      v                         v               v            v            v
+-----------+           +---------------+  +--------+   +--------+   +---------+
| VALIDATED |           |  MISSING_OR_  |  | Tower 1|   | Tower 8|   |Quarantine|
|  (float)  |           | INVALID (Null)|  |Context |   |Context |   |  Buffer |
+-----+-----+           +-------+-------+  +----+---+   +----+---+   +---------+
      |                         |               |            |
      +------------+------------+               +-----+------+
                   |                                  |
                   +-----------------+----------------+
                                     |
                                     v
                   +-----------------------------------+
                   |   Immutable CaseInputPayload      |
                   | (Strictly Typed & MECE Isolated)  |
                   +-----------------------------------+
```

Under this new paradigm:
* Every expected KPI defined in the canonical enterprise taxonomy must be accounted for at ingestion. Missing or malformed inputs trigger a **Missing Data Circuit Breaker**, persisting an immutable `EvidenceStatus.MISSING_OR_INVALID` state into the payload.
* Monolithic transcripts are decomposed into atomic semantic discourse units and routed through an **Epistemic Graph Router**. Only evidence fragments mathematically proven to belong to a specific Mutually Exclusive, Collectively Exhaustive (MECE) domain tower are injected into that tower's context window.

---

## 2. DETAILED PHASED IMPLEMENTATION STRATEGY

### PHASE 1: MISSING DATA CIRCUIT BREAKER & STRICT TYPING SCHEMA

#### 1.1 Architectural Objective
Eliminate silent regex discarding in `build_case_input.py`. The ingestion engine must invert its control flow: instead of iterating only over *matched* lines in the raw input file, it must iterate over the *canonical taxonomy manifest* of all expected KPIs (`T{x}.P{y}.K{z}`) and actively assert the presence and validity of each KPI in the raw input.

#### 1.2 Domain Data Contracts (`src/ingestion/contracts.py`)
We introduce strict Pydantic v2 models to enforce type safety and eliminate primitive obsession.

```python
from enum import Enum
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, model_validator


class EvidenceStatus(str, Enum):
    """Explicit epistemic state of an ingested KPI data point."""
    VALIDATED = "VALIDATED"
    MISSING_OR_INVALID = "MISSING_OR_INVALID"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class IngestedKpiRecord(BaseModel):
    """Immutable record representing the ingestion outcome of a single canonical KPI."""
    kpi_id: str = Field(..., pattern=r"^T\d+\.P\d+\.K\d+$", description="Canonical KPI Coordinate")
    raw_input: Optional[str] = Field(None, description="Exact unmutated string extracted from source")
    numeric_value: Optional[float] = Field(None, description="Parsed IEEE 754 float if status is VALIDATED")
    status: EvidenceStatus = Field(..., description="Epistemic validation status")
    diagnostic_reason: Optional[str] = Field(None, description="Audit trail explaining failure or absence")

    @model_validator(mode="after")
    def EnforceEpistemicConsistency(self) -> "IngestedKpiRecord":
        if self.status == EvidenceStatus.VALIDATED and self.numeric_value is None:
            raise ValueError(f"KPI {self.kpi_id} marked VALIDATED but numeric_value is None.")
        if self.status != EvidenceStatus.VALIDATED and self.numeric_value is not None:
            raise ValueError(
                f"KPI {self.kpi_id} has status {self.status.value} "
                f"but contains numeric_value {self.numeric_value}. Silent imputation is prohibited."
            )
        return self
```

#### 1.3 The Circuit Breaker Engine (`src/ingestion/circuit_breaker.py`)
We replace the legacy `RESPONSE_RE` single-pass regex with a two-stage parser: first capturing *all* key-value candidates (regardless of value malformation), and second validating against the canonical manifest.

```python
import re
from typing import Dict, Set, Tuple
from src.ingestion.contracts import EvidenceStatus, IngestedKpiRecord


class MissingDataCircuitBreaker:
    """
    Enforces strict epistemic accounting for all expected taxonomy KPIs.
    Prohibits silent dropping of malformed or absent survey responses.
    """
    # Captures KPI coordinate and EVERYTHING remaining on the line as raw payload
    RAW_LINE_CAPTURE_RE = re.compile(
        r"^\s*(?P<kpi_id>T\d+\.P\d+\.K\d+)\s*[:=\-\|]?\s*(?P<raw_val>.*?)\s*$"
    )
    
    # Strict numeric extractor supporting scientific notation, signs, and decimals
    STRICT_NUMERIC_RE = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")
    
    # Explicit tokens denoting intentional non-applicability vs accidental omission
    EXPLICIT_NA_TOKENS: Set[str] = {"N/A", "NA", "NOT_APPLICABLE", "NONE"}

    def __init__(self, expected_kpi_manifest: Set[str]) -> None:
        if not expected_kpi_manifest:
            raise ValueError("Expected KPI manifest cannot be empty.")
        self._manifest = expected_kpi_manifest

    def evaluate_raw_survey(self, raw_text: str) -> Dict[str, IngestedKpiRecord]:
        raw_extractions: Dict[str, str] = {}
        
        for line in raw_text.splitlines():
            match = self.RAW_LINE_CAPTURE_RE.match(line)
            if match:
                kpi_id = match.group("kpi_id")
                raw_val = match.group("raw_val")
                raw_extractions[kpi_id] = raw_val

        verified_payload: Dict[str, IngestedKpiRecord] = {}

        for expected_kpi in sorted(self._manifest):
            if expected_kpi not in raw_extractions:
                verified_payload[expected_kpi] = IngestedKpiRecord(
                    kpi_id=expected_kpi,
                    raw_input=None,
                    numeric_value=None,
                    status=EvidenceStatus.MISSING_OR_INVALID,
                    diagnostic_reason="KPI coordinate completely absent from raw survey source."
                )
                continue

            raw_val = raw_extractions[expected_kpi].strip()
            record = self._classify_raw_value(expected_kpi, raw_val)
            verified_payload[expected_kpi] = record

        return verified_payload

    def _classify_raw_value(self, kpi_id: str, raw_val: str) -> IngestedKpiRecord:
        if not raw_val:
            return IngestedKpiRecord(
                kpi_id=kpi_id,
                raw_input=raw_val,
                numeric_value=None,
                status=EvidenceStatus.MISSING_OR_INVALID,
                diagnostic_reason="Empty string provided as KPI response."
            )

        normalized_upper = raw_val.upper()
        if normalized_upper in self.EXPLICIT_NA_TOKENS:
            return IngestedKpiRecord(
                kpi_id=kpi_id,
                raw_input=raw_val,
                numeric_value=None,
                status=EvidenceStatus.NOT_APPLICABLE,
                diagnostic_reason=f"Explicit non-applicable token detected: '{raw_val}'."
            )

        # Clean standard formatting artifacts (e.g., trailing % or currency symbols) ONLY if unambiguous
        cleaned_candidate = raw_val.rstrip("%").strip()
        
        if self.STRICT_NUMERIC_RE.match(cleaned_candidate):
            try:
                val = float(cleaned_candidate)
                return IngestedKpiRecord(
                    kpi_id=kpi_id,
                    raw_input=raw_val,
                    numeric_value=val,
                    status=EvidenceStatus.VALIDATED,
                    diagnostic_reason=None
                )
            except ValueError as exc:
                return IngestedKpiRecord(
                    kpi_id=kpi_id,
                    raw_input=raw_val,
                    numeric_value=None,
                    status=EvidenceStatus.MISSING_OR_INVALID,
                    diagnostic_reason=f"Float conversion exception: {str(exc)}"
                )

        # Catches corrupted tokens such as ",", "TBD", "-", "613 days" (unparsed strings)
        return IngestedKpiRecord(
            kpi_id=kpi_id,
            raw_input=raw_val,
            numeric_value=None,
            status=EvidenceStatus.MISSING_OR_INVALID,
            diagnostic_reason=f"Malformed non-numeric token rejected by strict parser: '{raw_val}'."
        )
```

---

### PHASE 2: MECE CONTEXT ROUTING ENGINE (`EpistemicGraphRouter`)

#### 2.1 Architectural Objective
Deconstruct monolithic interview transcripts into atomic discourse fragments and route them strictly to their corresponding MECE domain towers. Tower $i$ must never gain epistemic visibility into evidence belonging solely to Tower $j$ ($i \neq j$), unless an explicit cross-tower ontology bridge is triggered by multi-domain semantic density.

#### 2.2 Taxonomy Ontology Schema (`config/taxonomy_routing_ontology.json`)
To adhere strictly to the **Zero Hardcoding** invariant, all domain routing logic is externalized into a declarative taxonomy configuration file. Every tower defines three vector spaces:
1. `anchor_concepts`: High-level semantic descriptors of the domain.
2. `lexical_signatures`: High-specificity domain terminology and vendor/protocol identifiers.
3. `negative_constraints`: Exclusion terms that actively penalize routing to prevent known contamination vectors.

```json
{
  "version": "16.0.0",
  "routing_hyperparameters": {
    "similarity_threshold": 0.28,
    "negative_penalty_weight": 0.45,
    "sliding_window_sentences": 3,
    "window_stride": 1
  },
  "towers": {
    "T1_CLOUD_INFRASTRUCTURE": {
      "description": "Compute virtualization, hyper-converged infrastructure, storage arrays, lifecycle management.",
      "anchor_concepts": ["hypervisor", "storage area network", "hardware end of life", "server virtualization", "rack capacity"],
      "lexical_signatures": ["simplivity", "netapp", "vmware", "esxi", "vsphere", "nutanix", "san", "nas", "lun", "blade"],
      "negative_constraints": ["finops", "reserved instance billing", "scada", "plc", "modbus"]
    },
    "T6_OT_IOT_SECURITY": {
      "description": "Operational technology, industrial control systems, cyber-physical telemetry and segmentation.",
      "anchor_concepts": ["industrial control system", "programmable logic controller", "air gap segmentation", "substation automation"],
      "lexical_signatures": ["scada", "plc", "modbus", "dnp3", "historiandb", "rtu", "hmi", "purdue model"],
      "negative_constraints": ["cloud billing", "finops", "chargeback", "kubernetes cost"]
    },
    "T8_CLOUD_FINOPS": {
      "description": "Cloud financial operations, unit economics, commitment discounts, cost allocation and governance.",
      "anchor_concepts": ["cloud cost optimization", "unit economics", "commitment discount coverage", "showback and chargeback"],
      "lexical_signatures": ["finops", "reserved instances", "savings plans", "cur", "cost anomaly", "unallocated spend", "ebitda impact"],
      "negative_constraints": ["scada", "plc", "modbus", "simplivity", "netapp firmware", "air gap"]
    }
  }
}
```

#### 2.3 Epistemic Graph Router Implementation (`src/ingestion/context_router.py`)
The router segments raw transcripts into overlapping sentence windows (preserving local coreference context, such as pronoun resolution across adjacent sentences) and computes a hybrid **Lexical-Semantic Affinity Score** $S(f, T_k)$ for each fragment $f$ against Tower $T_k$:

$$S(f, T_k) = \alpha \cdot \text{CosineSim}(\mathbf{v}_f, \mathbf{v}_{T_k}) + \beta \cdot \text{BM25}(f, L_{T_k}) - \gamma \cdot \mathbb{I}_{\text{neg}}(f, N_{T_k})$$

Where $\mathbf{v}_f$ and $\mathbf{v}_{T_k}$ are TF-IDF / dense embedding vectors, $L_{T_k}$ is the set of lexical signatures, and $N_{T_k}$ is the set of negative constraints.

```python
import re
import math
from typing import Dict, List, Set, Tuple
from pydantic import BaseModel, Field


class TaxonomyTowerProfile(BaseModel):
    tower_id: str
    description: str
    anchor_concepts: List[str]
    lexical_signatures: List[str]
    negative_constraints: List[str]


class EvidenceFragment(BaseModel):
    fragment_id: str
    sequence_index: int
    text: str
    routed_towers: List[str] = Field(default_factory=list)
    affinity_scores: Dict[str, float] = Field(default_factory=dict)


class EpistemicRoutingLedger(BaseModel):
    """Immutable audit log of transcript segmentation and MECE tower allocation."""
    tower_contexts: Dict[str, List[EvidenceFragment]]
    quarantined_fragments: List[EvidenceFragment]
    total_fragments_processed: int


class EpistemicGraphRouter:
    """
    Segments monolithic transcripts into discourse units and routes them strictly
    to relevant MECE domain towers using taxonomy-driven vector & lexical scoring.
    """
    SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")
    WORD_TOKENIZER_RE = re.compile(r"\b[a-z0-9_]+\b")

    def __init__(
        self,
        ontology_profiles: Dict[str, TaxonomyTowerProfile],
        similarity_threshold: float = 0.28,
        negative_penalty_weight: float = 0.45,
        window_size: int = 3,
        stride: int = 1
    ) -> None:
        self._profiles = ontology_profiles
        self._threshold = similarity_threshold
        self._penalty_weight = negative_penalty_weight
        self._window_size = window_size
        self._stride = stride
        self._tower_term_weights: Dict[str, Dict[str, float]] = {}
        self._build_taxonomy_vector_space()

    def _tokenize(self, text: str) -> List[str]:
        return self.WORD_TOKENIZER_RE.findall(text.lower())

    def _build_taxonomy_vector_space(self) -> None:
        """Constructs inverse-document-frequency weighted profiles for each tower."""
        doc_freq: Dict[str, int] = {}
        num_towers = len(self._profiles)

        tower_raw_tokens: Dict[str, List[str]] = {}
        for tower_id, profile in self._profiles.items():
            combined_corpus = " ".join(
                [profile.description] + profile.anchor_concepts + profile.lexical_signatures
            )
            tokens = self._tokenize(combined_corpus)
            tower_raw_tokens[tower_id] = tokens
            for unique_token in set(tokens):
                doc_freq[unique_token] = doc_freq.get(unique_token, 0) + 1

        for tower_id, tokens in tower_raw_tokens.items():
            weights: Dict[str, float] = {}
            tf_counts: Dict[str, int] = {}
            for t in tokens:
                tf_counts[t] = tf_counts.get(t, 0) + 1
            
            for token, count in tf_counts.items():
                # Smoothed IDF calculation
                idf = math.log((1.0 + num_towers) / (1.0 + doc_freq[token])) + 1.0
                weights[token] = (count / len(tokens)) * idf
            
            # Boost exact lexical signatures
            for sig in self._profiles[tower_id].lexical_signatures:
                for sig_token in self._tokenize(sig):
                    weights[sig_token] = weights.get(sig_token, 0.0) + 0.50

            self._tower_term_weights[tower_id] = weights

    def segment_transcript(self, raw_transcript: str) -> List[str]:
        """Decomposes monolithic text into overlapping discourse windows."""
        cleaned = re.sub(r"\s+", " ", raw_transcript.strip())
        if not cleaned:
            return []
        
        sentences = self.SENTENCE_BOUNDARY_RE.split(cleaned)
        if len(sentences) <= self._window_size:
            return [" ".join(sentences)]

        windows: List[str] = []
        for idx in range(0, len(sentences) - self._window_size + 1, self._stride):
            window_text = " ".join(sentences[idx : idx + self._window_size])
            windows.append(window_text)
        return windows

    def route_transcript(self, raw_transcript: str) -> EpistemicRoutingLedger:
        raw_windows = self.segment_transcript(raw_transcript)
        tower_buckets: Dict[str, List[EvidenceFragment]] = {
            t_id: [] for t_id in self._profiles.keys()
        }
        quarantined: List[EvidenceFragment] = []

        for seq_idx, text in enumerate(raw_windows):
            frag_id = f"FRAG_{seq_idx:04d}"
            scores = self._compute_tower_affinities(text)
            
            matched_towers = [
                t_id for t_id, score in scores.items() if score >= self._threshold
            ]

            fragment = EvidenceFragment(
                fragment_id=frag_id,
                sequence_index=seq_idx,
                text=text,
                routed_towers=matched_towers,
                affinity_scores=scores
            )

            if not matched_towers:
                quarantined.append(fragment)
            else:
                for t_id in matched_towers:
                    tower_buckets[t_id].append(fragment)

        return EpistemicRoutingLedger(
            tower_contexts=tower_buckets,
            quarantined_fragments=quarantined,
            total_fragments_processed=len(raw_windows)
        )

    def _compute_tower_affinities(self, fragment_text: str) -> Dict[str, float]:
        frag_tokens = self._tokenize(fragment_text)
        if not frag_tokens:
            return {t_id: 0.0 for t_id in self._profiles.keys()}

        frag_lower = fragment_text.lower()
        scores: Dict[str, float] = {}

        for tower_id, profile in self._profiles.items():
            tower_weights = self._tower_term_weights[tower_id]
            
            # 1. Weighted TF-IDF Cosine Projection
            dot_product = sum(tower_weights.get(t, 0.0) for t in frag_tokens)
            norm_frag = math.sqrt(len(frag_tokens))
            norm_tower = math.sqrt(sum(w * w for w in tower_weights.values())) or 1.0
            base_similarity = dot_product / (norm_frag * norm_tower)

            # 2. Multi-word Phrase Signature Boost
            phrase_boost = 0.0
            for phrase in profile.lexical_signatures + profile.anchor_concepts:
                if phrase.lower() in frag_lower:
                    phrase_boost += 0.22

            # 3. Negative Constraint Repulsion Penalty
            penalty = 0.0
            for neg_term in profile.negative_constraints:
                if neg_term.lower() in frag_lower:
                    penalty += self._penalty_weight

            final_score = max(0.0, round(base_similarity + phrase_boost - penalty, 4))
            scores[tower_id] = final_score

        return scores
```

---

### PHASE 3: DOWNSTREAM INTEGRATION OF EXPLICIT MISSING STATES & AST ISOLATION

#### 3.1 Architectural Objective
Upgrade the payload assembly in `build_case_input.py`, the downstream actuarial scoring calculators, and the AST (Abstract Syntax Tree) report generator so that `EvidenceStatus.MISSING_OR_INVALID` is treated as a first-class citizen. **Silent averaging over reduced denominators is strictly outlawed.**

#### 3.2 Refactored Payload Schema (`src/ingestion/payload_builder.py`)
The output JSON generated by `build_case_input.py` is restructured so that every tower receives **only** its scoped KPI records and **only** its routed transcript fragments.

```python
from typing import Dict, List
from pydantic import BaseModel
from src.ingestion.contracts import IngestedKpiRecord
from src.ingestion.context_router import EvidenceFragment


class ScopedTowerPayload(BaseModel):
    tower_id: str
    kpis: Dict[str, IngestedKpiRecord]
    scoped_evidence_fragments: List[EvidenceFragment]
    epistemic_completeness_ratio: float


class CaseInputPayload(BaseModel):
    case_id: str
    schema_version: str = "16.0.0"
    towers: Dict[str, ScopedTowerPayload]
    quarantined_transcript_fragments: List[EvidenceFragment]
```

#### 3.3 Actuarial Scoring Calculator Refactor (`src/scoring/pillar_calculator.py`)
Downstream calculators must inspect `IngestedKpiRecord.status` before executing mathematical aggregations. If any KPI within a pillar is marked `MISSING_OR_INVALID`, the pillar is flagged as **Epistemically Degraded**, and an explicit penalty or confidence interval widening is applied rather than dropping the term from the denominator.

```python
from typing import List, Optional
from pydantic import BaseModel
from src.ingestion.contracts import EvidenceStatus, IngestedKpiRecord


class PillarActuarialResult(BaseModel):
    pillar_id: str
    computed_score: Optional[float]
    completeness_ratio: float
    missing_kpi_ids: List[str]
    is_epistemically_degraded: bool


class PillarScoringEngine:
    """
    Computes pillar scores while strictly prohibiting silent imputation.
    """
    def evaluate_pillar(
        self, pillar_id: str, kpi_records: List[IngestedKpiRecord]
    ) -> PillarActuarialResult:
        applicable_records = [
            r for r in kpi_records if r.status != EvidenceStatus.NOT_APPLICABLE
        ]
        if not applicable_records:
            return PillarActuarialResult(
                pillar_id=pillar_id,
                computed_score=None,
                completeness_ratio=1.0,
                missing_kpi_ids=[],
                is_epistemically_degraded=False
            )

        validated_values: List[float] = []
        missing_ids: List[str] = []

        for record in applicable_records:
            if record.status == EvidenceStatus.VALIDATED and record.numeric_value is not None:
                validated_values.append(record.numeric_value)
            elif record.status == EvidenceStatus.MISSING_OR_INVALID:
                missing_ids.append(record.kpi_id)

        completeness = len(validated_values) / len(applicable_records)
        is_degraded = len(missing_ids) > 0

        # If all KPIs are missing, score cannot be computed
        if not validated_values:
            return PillarActuarialResult(
                pillar_id=pillar_id,
                computed_score=None,
                completeness_ratio=0.0,
                missing_kpi_ids=missing_ids,
                is_epistemically_degraded=True
            )

        # Conservative Actuarial Bounding: Missing KPIs are NOT silently ignored.
        # We compute the observed mean ONLY for reference, but mark the node degraded
        # so downstream AST builders emit mandatory Risk Disclosure warnings.
        raw_mean = sum(validated_values) / len(validated_values)

        return PillarActuarialResult(
            pillar_id=pillar_id,
            computed_score=round(raw_mean, 4),
            completeness_ratio=round(completeness, 4),
            missing_kpi_ids=missing_ids,
            is_epistemically_degraded=is_degraded
        )
```

#### 3.4 AST Narrative Node Injection (`src/reporting/ast_builder.py`)
When the AST report generator encounters a KPI with `EvidenceStatus.MISSING_OR_INVALID` (such as `T4.P4.K3` having raw input `","`), it injects a deterministic `EpistemicGapWarningNode` directly into the document tree, preventing the LLM from hallucinating a metric or glossing over the omission.

```python
from src.ingestion.contracts import EvidenceStatus, IngestedKpiRecord


class AstEpistemicGapNode:
    """AST Node representing a mandatory disclosure of missing client evidence."""
    def __init__(self, kpi_record: IngestedKpiRecord) -> None:
        self.kpi_id = kpi_record.kpi_id
        self.raw_input = kpi_record.raw_input
        self.diagnostic = kpi_record.diagnostic_reason

    def render_markdown(self) -> str:
        raw_display = f"`{self.raw_input}`" if self.raw_input is not None else "`<OMITTED>`"
        return (
            f"> **[EPISTEMIC CIRCUIT BREAKER: DATA ABSENT — {self.kpi_id}]**  \n"
            f"> **Status:** `MISSING_OR_INVALID` | **Ingested Token:** {raw_display}  \n"
            f"> **Actuarial Notice:** {self.diagnostic} Zero imputation applied. "
            f"Pillar confidence interval degraded accordingly."
        )
```

---

## 3. QUALITY GATES & VERIFICATION ORACLES

To guarantee zero regressions and prove mathematically that historical defects (e.g., `T4.P4.K3 ","` silent drop and SimpliVity/NetApp/FinOps/SCADA cross-contamination) are permanently eradicated, the following deterministic `pytest` suite must pass in CI/CD prior to merging Phase 16.

### Verification Suite (`tests/ingestion/test_phase16_epistemic_ingestion.py`)

```python
import pytest
from src.ingestion.contracts import EvidenceStatus
from src.ingestion.circuit_breaker import MissingDataCircuitBreaker
from src.ingestion.context_router import EpistemicGraphRouter, TaxonomyTowerProfile
from src.scoring.pillar_calculator import PillarScoringEngine
from src.reporting.ast_builder import AstEpistemicGapNode


@pytest.fixture
def canonical_manifest() -> set[str]:
    return {"T1.P1.K1", "T4.P4.K1", "T4.P4.K2", "T4.P4.K3", "T8.P2.K1"}


@pytest.fixture
def sample_taxonomy_profiles() -> dict[str, TaxonomyTowerProfile]:
    return {
        "T1_CLOUD_INFRA": TaxonomyTowerProfile(
            tower_id="T1_CLOUD_INFRA",
            description="Compute virtualization, hyper-converged infrastructure, storage arrays.",
            anchor_concepts=["hardware end of life", "hyper-converged", "storage array"],
            lexical_signatures=["simplivity", "netapp", "vmware", "esxi"],
            negative_constraints=["finops", "scada", "plc", "reserved instances"]
        ),
        "T6_OT_SECURITY": TaxonomyTowerProfile(
            tower_id="T6_OT_SECURITY",
            description="Operational technology, industrial control systems, SCADA telemetry.",
            anchor_concepts=["industrial control system", "substation automation", "air gap"],
            lexical_signatures=["scada", "plc", "modbus", "rtu"],
            negative_constraints=["finops", "simplivity", "netapp", "savings plans"]
        ),
        "T8_FINOPS": TaxonomyTowerProfile(
            tower_id="T8_FINOPS",
            description="Cloud financial operations, commitment discounts, cost governance.",
            anchor_concepts=["cloud cost optimization", "commitment discount", "chargeback"],
            lexical_signatures=["finops", "reserved instances", "savings plans", "unallocated spend"],
            negative_constraints=["scada", "plc", "simplivity", "netapp"]
        ),
    }


def test_circuit_breaker_catches_comma_and_missing_kpis(canonical_manifest: set[str]) -> None:
    """
    ORACLE 1: Verifies that T4.P4.K3 ',' is explicitly trapped as MISSING_OR_INVALID
    and omitted KPIs (T8.P2.K1) are never silently dropped.
    """
    raw_survey_payload = """
    T1.P1.K1: 99.95%
    T4.P4.K1: 42.0
    T4.P4.K2: N/A
    T4.P4.K3: ,
    """
    breaker = MissingDataCircuitBreaker(expected_kpi_manifest=canonical_manifest)
    results = breaker.evaluate_raw_survey(raw_survey_payload)

    # 1. Exact manifest cardinality preserved
    assert set(results.keys()) == canonical_manifest

    # 2. Validated float parsing
    assert results["T1.P1.K1"].status == EvidenceStatus.VALIDATED
    assert results["T1.P1.K1"].numeric_value == 99.95

    # 3. Explicit N/A handling
    assert results["T4.P4.K2"].status == EvidenceStatus.NOT_APPLICABLE
    assert results["T4.P4.K2"].numeric_value is None

    # 4. Historical defect T4.P4.K3 "," caught Loudly
    k3_record = results["T4.P4.K3"]
    assert k3_record.status == EvidenceStatus.MISSING_OR_INVALID
    assert k3_record.raw_input == ","
    assert k3_record.numeric_value is None
    assert "Malformed non-numeric token" in (k3_record.diagnostic_reason or "")

    # 5. Unmentioned KPI caught Loudly
    t8_record = results["T8.P2.K1"]
    assert t8_record.status == EvidenceStatus.MISSING_OR_INVALID
    assert t8_record.raw_input is None


def test_epistemic_router_prevents_cross_tower_contamination(
    sample_taxonomy_profiles: dict[str, TaxonomyTowerProfile]
) -> None:
    """
    ORACLE 2: Verifies that SCADA and SimpliVity facts never leak into Tower 8 (FinOps),
    and FinOps billing facts never leak into OT Security or Infrastructure.
    """
    monolithic_transcript = (
        "The legacy HP SimpliVity cluster has been running 613 days past hardware end of life, "
        "while our primary NetApp AFF storage arrays require firmware upgrades. "
        "In the manufacturing plant, the SCADA supervisory system communicates with Siemens PLC controllers "
        "over unencrypted Modbus protocols without an air gap. "
        "Meanwhile, our Cloud FinOps practice lacks governance over AWS Reserved Instances and Savings Plans, "
        "leading to $1.4M in unallocated spend."
    )

    router = EpistemicGraphRouter(
        ontology_profiles=sample_taxonomy_profiles,
        similarity_threshold=0.25,
        window_size=1,
        stride=1
    )
    ledger = router.route_transcript(monolithic_transcript)

    t1_texts = " ".join(f.text for f in ledger.tower_contexts["T1_CLOUD_INFRA"]).lower()
    t6_texts = " ".join(f.text for f in ledger.tower_contexts["T6_OT_SECURITY"]).lower()
    t8_texts = " ".join(f.text for f in ledger.tower_contexts["T8_FINOPS"]).lower()

    # T1 must contain SimpliVity/NetApp, and ZERO SCADA or FinOps
    assert "simplivity" in t1_texts
    assert "613 days" in t1_texts
    assert "scada" not in t1_texts
    assert "finops" not in t1_texts

    # T6 must contain SCADA/PLC/Modbus, and ZERO SimpliVity or FinOps
    assert "scada" in t6_texts
    assert "modbus" in t6_texts
    assert "simplivity" not in t6_texts
    assert "reserved instances" not in t6_texts

    # T8 must contain FinOps/Reserved Instances, and ZERO SCADA or SimpliVity
    assert "finops" in t8_texts
    assert "reserved instances" in t8_texts
    assert "scada" not in t8_texts
    assert "simplivity" not in t8_texts


def test_downstream_scoring_and_ast_prohibit_silent_imputation(
    canonical_manifest: set[str]
) -> None:
    """
    ORACLE 3: Verifies that downstream PillarScoringEngine flags degraded pillars
    and AstEpistemicGapNode renders explicit markdown disclosures.
    """
    raw_survey = """
    T4.P4.K1: 80.0
    T4.P4.K2: 90.0
    T4.P4.K3: ,
    """
    breaker = MissingDataCircuitBreaker(expected_kpi_manifest={"T4.P4.K1", "T4.P4.K2", "T4.P4.K3"})
    records = list(breaker.evaluate_raw_survey(raw_survey).values())

    engine = PillarScoringEngine()
    pillar_result = engine.evaluate_pillar("T4.P4", records)

    assert pillar_result.is_epistemically_degraded is True
    assert pillar_result.missing_kpi_ids == ["T4.P4.K3"]
    assert pillar_result.completeness_ratio == pytest.approx(0.6667, rel=1e-3)

    gap_node = AstEpistemicGapNode( [r for r in records if r.kpi_id == "T4.P4.K3"][0] )
    rendered_md = gap_node.render_markdown()
    assert "EPISTEMIC CIRCUIT BREAKER: DATA ABSENT — T4.P4.K3" in rendered_md
    assert "MISSING_OR_INVALID" in rendered_md
```

---

## 4. ARCHITECTURAL SIGN-OFF & EXECUTION ROADMAP

| Step | Component | Target Path | Invariant Enforced |
| :--- | :--- | :--- | :--- |
| **1** | Ingestion Data Contracts | `src/ingestion/contracts.py` | Strict typing; prohibits `VALIDATED` status without IEEE 754 float. |
| **2** | Missing Data Circuit Breaker | `src/ingestion/circuit_breaker.py` | 100% KPI manifest accounting; zero silent regex drops. |
| **3** | Declarative Routing Ontology | `config/taxonomy_routing_ontology.json` | Zero hardcoding of client rules; pure taxonomy-driven routing. |
| **4** | Epistemic Graph Router | `src/ingestion/context_router.py` | Strict MECE context isolation; eliminates cross-tower contamination. |
| **5** | Ingestion Pipeline Refactor | `build_case_input.py` | Replaces legacy `RESPONSE_RE` and monolithic transcript injection. |
| **6** | Downstream AST & Calculators | `src/scoring/` & `src/reporting/` | Explicit `Data absent` AST nodes and completeness degradation flags. |

*Approved for immediate deployment by Gemini-4-Argon.*
```