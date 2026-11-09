# RFC 082: UNIVERSAL RAW EVIDENCE EXTRACTION AND PHONETIC RESOLUTION PIPELINE

| Metadata | Details |
| :--- | :--- |
| **Document ID** | RFC-082 |
| **Title** | Universal Raw Evidence Extraction and Phonetic Resolution Pipeline |
| **Author** | Principal Staff Systems Architect / Senior Partner (Architecture & AI) |
| **Status** | RATIFIED FOR IMMEDIATE EXECUTION |
| **Target Architecture** | Assessment Engine Core (Hexagonal / Clean Architecture) |
| **Classification** | Tier-1 Mission-Critical Infrastructure |

---

## 0. EXECUTIVE SUMMARY & PARADIGM SHIFT

Empirical audits of the Assessment Engine's output have confirmed that the ingestion of intermediate "Synthesized Context Documents" introduces unacceptable epistemic risk. Human consultants consistently inject subjective bias, prematurely extrapolate architectural conclusions, and omit granular operational telemetry. This degrades the mathematical integrity of downstream actuarial scoring.

**RFC 082 mandates the immediate deprecation of all human-synthesized intermediate documents.** The engine will transition to a **Zero-Trust Epistemic Ingestion Pipeline**. It will consume only unvarnished, primary-source data:
1. **Raw Interview Transcriptions** (`.docx`, `.vtt`, `.txt`) generated directly by Speech-to-Text (STT) engines.
2. **Empirical Assessment Responses** (`.xlsx`, `.csv`, `.json`) containing deterministic telemetry and survey responses.

To achieve this without introducing brittle, tenant-specific hardcoding into the domain logic, this blueprint establishes a dynamic, configuration-driven **Phonetic & Entity Normalization Layer** and a probabilistic **Epistemic Truth Resolution Engine** that outputs an immutable `evidence_ledger.json`.

---

## 1. ARCHITECTURAL DESIGN: HEXAGONAL RAW INGESTION PIPELINE

To preserve Domain Purity, the ingestion pipeline strictly adheres to the Ports and Adapters (Hexagonal) pattern. Raw file parsing and external LLM calls are isolated in the **Infrastructure Layer**, while epistemic decomposition, entity resolution interfaces, and ledger reconciliation reside within the **Domain and Application Layers**.

### 1.1 High-Level Data Flow

```text
[Raw DOCX/VTT] ──> [Transcript Adapter] ──> [Utterance Stream] 
                                                    │
[Engine Config] ──> [Phonetic Normalizer] <─────────┤ (LLM + Dynamic Lexicon)
                                                    ▼
[Raw XLSX/TXT]  ──> [Telemetry Adapter]  ──> [Epistemic Synthesizer] ──> [evidence_ledger.json]
```

### 1.2 Transcript Decomposition & Speaker Diarization (`raw_transcript_parser.py`)
The `RawTranscriptParser` (Infrastructure Adapter) ingests unstructured conversational streams and transforms them into deterministic `RawUtterance` data structures before passing them to the Domain Layer.

1. **Format-Agnostic Ingestion:** 
   * `.vtt` files are parsed using deterministic regex state machines capturing timecodes (`HH:MM:SS.mmm`), speaker tags, and raw text payloads.
   * `.docx` files are parsed via AST (Abstract Syntax Tree) traversal (`python-docx`), inspecting paragraph styles, bolding patterns, and line-break delimiters to identify speaker transitions and temporal markers.
2. **Speaker Diarization & Role Attribution:**
   * Speakers are extracted as raw strings (e.g., `"Speaker 1"`, `"John Doe - VP Infra"`).
   * An initialization pass maps speakers to canonical `AuthorityRoles` (`INTERVIEWER`, `SME_TECHNICAL`, `EXECUTIVE_SPONSOR`, `UNKNOWN`) using contextual heuristics, weighting the epistemic authority of their subsequent statements (e.g., an `INTERVIEWER` prompt carries zero evidentiary weight; an `SME_TECHNICAL` response carries high weight).
3. **Semantic Topic Segmentation (Sliding Window Chunking):**
   * Raw human speech is fragmented and nonlinear. The parser groups contiguous utterances into `ConversationalSegments` using a sliding window with configurable token overlap.
   * Boundary detection is executed by calculating cosine similarity drops between utterance embeddings or via a lightweight structural LLM pass that detects shifts in architectural domains (e.g., transitioning from *Network Topology* to *Disaster Recovery*).

### 1.3 Core Domain Data Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from uuid import UUID, uuid4

class RawUtterance(BaseModel):
    utterance_id: UUID = Field(default_factory=uuid4)
    sequence_index: int
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    speaker_identifier: str
    speaker_role: Literal["INTERVIEWER", "SME_TECHNICAL", "EXECUTIVE_SPONSOR", "UNKNOWN"]
    raw_text: str

class NormalizedUtterance(RawUtterance):
    normalized_text: str
    resolved_entities: List[dict] = Field(default_factory=list)
    normalization_confidence: float = Field(ge=0.0, le=1.0)
```

---

## 2. PHONETIC & ENTITY NORMALIZATION STRATEGY

Speech-to-Text (STT) engines consistently hallucinate out-of-vocabulary (OOV) technical terms, proprietary vendor names, and regional geographic identifiers based on phonetic approximations (e.g., transcribing *"HPE SimpliVity"* as *"simply"*, *"Oracle Cloud"* as *"occlout"*, or *"Sant Vicenç"* as *"samisense"*).

**Law #2 (Zero Hardcoding) strictly prohibits embedding replacement dictionaries inside Python source code.** We solve this via a two-tier **Dynamic Phonetic & Semantic Resolution Engine**.

### 2.1 Tier 1: Externalized Runtime Lexicons (`engine_config/`)
Domain-specific and tenant-specific vocabularies are externalized as YAML/JSON configuration artifacts injected at runtime via Dependency Injection.

* **Global Technical Lexicon (`engine_config/ontologies/global_tech_ontology.yaml`):** Contains canonical vendor names, protocols, and enterprise architectures (e.g., Kubernetes, SimpliVity, Nutanix, BGP, Active Directory).
* **Tenant Runtime Context (`engine_config/tenants/{tenant_id}_context.yaml`):** A lightweight, declarative configuration file provided per engagement containing known organizational metadata: geographic locations, subsidiary names, project codenames, and core tech stack pillars.

```yaml
# Example: engine_config/tenants/tenant_alpha_context.yaml
tenant_metadata:
  industry_vertical: "Manufacturing & Logistics"
  known_geographies:
    - "Sant Vicenç dels Horts"
    - "Zaragoza"
  known_systems:
    - "SAP S/4HANA"
    - "Oracle Cloud Infrastructure"
    - "HPE SimpliVity"
  custom_acronyms:
    "MES": "Manufacturing Execution System"
```

### 2.2 Tier 2: Acoustic-Semantic LLM Resolution Pipeline
Before an utterance is converted into an epistemic claim, it passes through the `PhoneticEntityResolver`. This component does not use brittle regex; it executes a constrained, deterministic LLM pass (`temperature=0.0`) combined with phonetic distance algorithms.

1. **Candidate Detection & Double Metaphone Indexing:**
   The resolver scans the `RawUtterance` for low-probability n-grams, out-of-context common nouns (e.g., the adverb *"simply"* used where a noun/system is syntactically expected), and proper nouns. It computes the **Double Metaphone** and **Soundex** phonetic hashes of these tokens and compares them against the phonetic hashes of the injected `EngineConfig` ontologies.
2. **Contextual LLM Reconstruction:**
   The utterance, along with the top-$K$ phonetically similar canonical terms from the external config, is passed to an LLM agent operating under a strict system prompt:
   * *Task:* Identify STT phonetic corruptions based on syntactic anomalies and acoustic similarity to the provided runtime ontology.
   * *Constraint:* Do not alter the speaker's intent, sentiment, or factual assertions. Only replace acoustically corrupted tokens with their canonical equivalents from the injected context, or deduce the canonical technical term from global architectural knowledge if confidence $\ge 0.85$.
3. **Audit Trail Preservation:**
   The `NormalizedUtterance` retains both `raw_text` and `normalized_text`, logging every transformation in `resolved_entities`:
   ```json
   {
     "original_token": "occlout",
     "canonical_entity": "Oracle Cloud Infrastructure",
     "resolution_method": "PHONETIC_CONTEXTUAL_LLM",
     "phonetic_distance": 0.18,
     "confidence": 0.96
   }
   ```

---

## 3. EPISTEMIC LEDGER CONSTRUCTION (`EvidenceLedger`)

Once transcripts are normalized and empirical test files (`.xlsx`/`.txt`) are parsed, the **Epistemic Synthesizer** merges these disparate streams into a unified, immutable `evidence_ledger.json`. This ledger serves as the absolute Ground Truth for all downstream scoring and reporting.

### 3.1 Epistemic Decomposition (Atomic Fact Extraction)
Conversational segments are decomposed into **Epistemic Fragments**—isolated, atomic assertions of fact stripped of conversational filler.
* *Raw Normalized Input:* *"Well, we tried to set up automated failover for the Oracle Cloud databases last year, around Q3, but the licensing costs were too high so we still do it manually via scripts."*
* *Extracted Atomic Fragments:*
  1. `System [Oracle Cloud Database] lacks automated failover.` (Polarity: Negative, State: Current)
  2. `System [Oracle Cloud Database] relies on manual scripted failover.` (Polarity: Neutral/Descriptive, State: Current)
  3. `Automated failover implementation was halted due to licensing cost constraints.` (Polarity: Contextual/Causal, State: Historical)

### 3.2 Multi-Modal Triangulation & Truth Resolution
The engine ingests two primary modalities: **Deterministic Telemetry/Surveys** (XLSX/TXT) and **Probabilistic Oral Testimony** (Transcripts). These streams frequently contradict one another (e.g., an XLSX survey claims *"RPO is < 15 minutes"*, while an engineer in the transcript states *"We run backups once a night via cron"*).

The `TruthResolutionEngine` resolves conflicts using an **Epistemic Hierarchy of Trust**:

| Source Modality | Epistemic Weight ($W_e$) | Nature of Evidence |
| :--- | :---: | :--- |
| **Empirical Telemetry** (Logs, Config Dumps in TXT/XLSX) | `1.00` | Deterministic System Truth |
| **Quantitative Test Responses** (Structured XLSX Matrix) | `0.80` | Structured Declarative Truth |
| **SME Technical Testimony** (Transcript - Engineer/Architect) | `0.75` | Operational Reality (High Context) |
| **Executive Testimony** (Transcript - Management) | `0.50` | Strategic Intent (Prone to Optimism Bias) |

#### Conflict Resolution Algorithm:
When an Epistemic Fragment from the transcript ($F_{trans}$) maps to the same architectural control domain as an Empirical Test Response ($F_{xlsx}$):
1. **Corroboration:** If $F_{trans}$ and $F_{xlsx}$ are semantically aligned, the resulting Ledger Entry's confidence score is boosted: $C_{final} = 1 - (1 - C_{trans})(1 - C_{xlsx})$.
2. **Dissonance Detection (The "Reality Gap"):** If $F_{trans}$ contradicts $F_{xlsx}$ (e.g., Survey says "Automated", SME says "Manual"), the engine **does not overwrite or average them**. Instead, it flags an `EPISTEMIC_DISSONANCE` event in the ledger.
   * If $F_{xlsx}$ is a self-reported survey answer and $F_{trans}$ is a specific technical operational description by an SME, the engine elevates the SME's testimony as the *Operational Truth* and logs the discrepancy as a **Governance/Visibility Finding** (i.e., leadership believes a control exists when operationally it does not).

### 3.3 The `evidence_ledger.json` Schema

```json
{
  "ledger_id": "uuid-v4",
  "generated_at": "2025-05-14T12:00:00Z",
  "schema_version": "2.0.0-RFC082",
  "epistemic_entries": [
    {
      "entry_id": "EVD-9081",
      "domain_taxonomy_ref": "RESILIENCE.DR.FAILOVER",
      "canonical_assertion": "Database failover in Oracle Cloud Infrastructure is executed manually via custom scripts.",
      "truth_status": "VERIFIED_DISSONANT",
      "composite_confidence": 0.91,
      "dissonance_flag": true,
      "dissonance_analysis": "Structured survey (XLSX Row 42) claims 'Fully Automated DR', directly contradicted by SME Technical testimony confirming manual script execution.",
      "supporting_fragments": [
        {
          "source_type": "RAW_TRANSCRIPT",
          "source_file": "interview_infra_lead.vtt",
          "utterance_id": "uuid-utterance-104",
          "speaker_role": "SME_TECHNICAL",
          "raw_excerpt": "we still do it manually via scripts in occlout.",
          "normalized_excerpt": "we still do it manually via scripts in Oracle Cloud Infrastructure.",
          "epistemic_weight": 0.75
        },
        {
          "source_type": "EMPIRICAL_XLSX",
          "source_file": "maturity_questionnaire.xlsx",
          "cell_reference": "Sheet1!D42",
          "raw_excerpt": "Question: DR Automation Level | Response: Tier 4 - Fully Automated",
          "epistemic_weight": 0.80
        }
      ]
    }
  ]
}
```

---

## 4. STEP-BY-STEP EXECUTION PLAN

This execution plan follows a strict dependency order to ensure zero regression and continuous testability. All legacy code referencing "Synthesized Context Documents" will be severed upon completion of Phase 4.

### Phase 1: Domain Layer & Configuration Contracts
**Step 1.1: Create `src/domain/models/epistemic_ledger.py`**
* **Action:** Define strict Pydantic v2 models for `RawUtterance`, `NormalizedUtterance`, `EpistemicFragment`, `EvidenceEntry`, and `EvidenceLedger`.
* **Mandate:** Ensure models are immutable (`frozen=True`) and contain zero infrastructure dependencies.

**Step 1.2: Create `src/domain/ports/ingestion_ports.py`**
* **Action:** Define Abstract Base Classes (Ports) for the pipeline:
  * `ITranscriptParserPort`: Interface for extracting utterances from raw media/text documents.
  * `IEmpiricalDataParserPort`: Interface for extracting structured responses from XLSX/TXT.
  * `IPhoneticResolverPort`: Interface for normalizing STT artifacts.
  * `IEpistemicSynthesizerPort`: Interface for decomposing text into atomic facts and resolving truth.

**Step 1.3: Create `engine_config/schemas/vocabulary_schema.json` & Baseline Ontologies**
* **Action:** Establish the JSON Schema validating runtime vocabulary files. Create `engine_config/ontologies/global_tech_ontology.yaml` populated with standard enterprise architecture nomenclature.

### Phase 2: Infrastructure Adapters (Raw Parsing & Phonetic Normalization)
**Step 2.1: Create `src/infrastructure/parsers/raw_transcript_parser.py`**
* **Action:** Implement `ITranscriptParserPort`. Build concrete parsers for `.vtt` (timecode/speaker regex parser) and `.docx` (paragraph/style inspection parser). Implement heuristic speaker role classification.

**Step 2.2: Create `src/infrastructure/parsers/empirical_response_parser.py`**
* **Action:** Implement `IEmpiricalDataParserPort`. Build deterministic readers using `openpyxl` (for `.xlsx`) and structured text parsers (for `.txt`/`.csv`), preserving exact cell/line provenance metadata for every extracted value.

**Step 2.3: Create `src/infrastructure/normalization/phonetic_entity_resolver.py`**
* **Action:** Implement `IPhoneticResolverPort`.
* **Logic:**
  1. Load `global_tech_ontology.yaml` and the runtime tenant YAML configuration.
  2. Pre-compute Double Metaphone phonetic keys (using the `metaphone` Python library) for all canonical entities.
  3. Implement the LLM resolution client utilizing structured outputs (JSON mode / tool calling) to correct STT corruptions in `RawUtterance` batches based on acoustic proximity and syntactic context.

### Phase 3: Application Services & Epistemic Truth Resolution
**Step 3.1: Create `src/application/services/epistemic_synthesizer.py`**
* **Action:** Implement `IEpistemicSynthesizerPort`.
* **Logic:**
  1. Segment `NormalizedUtterance` streams into topical windows.
  2. Invoke LLM decomposition to extract atomic `EpistemicFragment` objects mapped to the engine's canonical taxonomy domains.
  3. Execute semantic similarity clustering (via embeddings) to group transcript fragments with corresponding XLSX/TXT empirical responses.
  4. Run the **Truth Resolution & Dissonance Detection Algorithm** to compute composite confidence scores and generate `EvidenceEntry` objects.

**Step 3.2: Create `src/application/pipelines/raw_evidence_ingestion_pipeline.py`**
* **Action:** Create the primary Application Orchestrator that wires the Ports and Adapters together.
* **Workflow:** `Ingest Raw Files` $\rightarrow$ `Parse to Utterances/Responses` $\rightarrow$ `Execute Phonetic Normalization` $\rightarrow$ `Synthesize Epistemic Fragments` $\rightarrow$ `Resolve Truth & Flag Dissonance` $\rightarrow$ `Serialize to evidence_ledger.json`.

### Phase 4: CLI Integration, Deprecation & Verification
**Step 4.1: Modify `src/interfaces/cli/assessment_runner.py` (or primary entrypoint)**
* **Action:** Update the CLI/API ingestion arguments. Deprecate `--context-doc`. Introduce `--raw-transcripts <dir_or_files>`, `--empirical-data <dir_or_files>`, and `--tenant-config <path_to_yaml>`.
* **Action:** Wire the entrypoint to execute `RawEvidenceIngestionPipeline` and pass the resulting `evidence_ledger.json` directly into the Actuarial Scoring Engine.

**Step 4.2: Create `tests/integration/test_rfc082_raw_pipeline.py`**
* **Action:** Build an end-to-end deterministic test suite.
* **Test Fixtures:** Inject a synthetic raw transcript containing severe STT corruptions (e.g., *"occlout"*, *"simply"*, *"samisense"*) and deliberate contradictions against a mock `.xlsx` questionnaire.
* **Assertions:**
  1. Verify 100% accuracy in phonetic resolution using a mock tenant config YAML (proving zero hardcoded dependencies).
  2. Verify that the generated `evidence_ledger.json` accurately flags `EPISTEMIC_DISSONANCE` where the transcript contradicts the spreadsheet.
  3. Verify complete traceability from the final ledger entry back to the exact utterance ID and XLSX cell reference.