---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/infrastructure/epistemic_graph.py
- src/assessment_engine/infrastructure/evidence_engine.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: editorial
notes: Technical specification of the data provenance ontology and evidence extraction heuristics.
---
# Data Provenance Ontology & Extraction Heuristics

Canonical specification defining the formal data provenance ontology, evidence ingestion mechanics, and epistemic uncertainty modeling across `assessment-engine`.

---

## 1. Epistemic Graph Architecture

The platform grounds all architectural assertions, technical gap diagnoses, and maturity scores in an event-sourced relational graph managed by `EpistemicGraph` (`epistemic_graph.py`) and populated by `EvidenceEngine` (`evidence_engine.py`):

```
[ Raw Document: .docx / .pdf ] 
             |
             v (EvidenceEngine.ingest_file)
    [ EvidenceFragment ]  (Content-Addressable L0 Anchor)
             |
             +----------------------------+
             |                            |
             v                            v
     [ Technical Gap ] <--(VIOLATES)--> [ Regulatory Control ]
             |                           (ENS, NIS2, DORA, ISO 27001)
             v
   [ Transformation Initiative ] <--(REQUIRES)--> [ Pre-requisite ]
```

Every claim synthesized by an LLM MUST link directly to an underlying `EvidenceFragment` to guarantee zero-hallucination auditability.

---

## 2. Ontological Node & Edge Schema

### 2.1 Core Node Classifications
| Entity Class | Defining Attributes | Epistemic Role |
|---|---|---|
| `EvidenceFragment` | `fragment_id: str`, `source_file: str`, `heading_path: List[str]`, `content_hash: str`, `text: str`, `confidence_score: float` | Verbatim text extract from customer documentation acting as immutable evidence. |
| `SystemEntity` | `entity_id: str`, `name: str`, `network_tier: str`, `technology_stack: List[str]` | Physical or logical infrastructure component audited in the engagement. |
| `TechnicalGap` | `gap_id: str`, `pillar_id: str`, `severity: str`, `risk_exposure: float` | Discovered vulnerability, operational bottleneck, or architectural flaw. |
| `RegulatoryControl`| `control_id: str`, `framework: str`, `clause: str`, `target_level: float` | Compliance requirement or industry standard rubric (e.g., CMMI, DORA). |
| `InitiativeEntity` | `initiative_id: str`, `tower: str`, `sizing: str`, `horizon: str` | Proposed remediation project allocated to a specific delivery wave ($H_1, H_2, H_3$). |

### 2.2 Relational Edge Grammar
- $\langle \text{TechnicalGap} \rangle \xrightarrow{\text{SUPPORTED\_BY}} \langle \text{EvidenceFragment} \rangle$: Anchors an identified flaw to exact textual proof.
- $\langle \text{TechnicalGap} \rangle \xrightarrow{\text{VIOLATES}} \langle \text{RegulatoryControl} \rangle$: Maps a technical deviation directly to the regulatory clause breached.
- $\langle \text{SystemEntity} \rangle \xrightarrow{\text{COVERS}} \langle \text{RegulatoryControl} \rangle$: Certifies that an operational control is actively enforced by an existing system.
- $\langle \text{InitiativeEntity} \rangle \xrightarrow{\text{REQUIRES}} \langle \text{InitiativeEntity} \rangle$: Establishes hard DAG wait-for constraints for topological execution sorting.

---

## 3. Evidence Extraction Pipeline

Raw multi-modal ingestion converts unstructured files into content-addressable fragments via deterministic heuristics:

```
[ Unstructured Input ] ──> [ Block Iterator ] ──> [ Heading Stack Tracking ] ──> [ SHA-256 Hashing ] ──> [ Vault Storage ]
```

### 3.1 Extraction Heuristics
1. **Hierarchical Context Tracking:** `_parse_docx` and `_parse_text` maintain an active heading stack ($H_1 \to H_2 \to H_3$). Every paragraph inherits its current parent heading path to preserve operational context.
2. **Content-Addressable Deduplication:** Each extracted fragment computes a deterministic SHA-256 digest over normalized text (`unicodedata.normalize("NFC", text)`). Duplicate fragments across annexes are resolved implicitly without redundant storage.
3. **Surrounding Context Anchoring:** Captures surrounding block boundaries to facilitate human forensic verification and multi-turn LLM reasoning.

---

## 4. Confidence Scoring Formulation

Evidence validity and epistemic certainty are quantified using deterministic scoring:

$$\text{Confidence Score} = w_{\text{source}} \times w_{\text{extraction}} \times \left(1.0 - \text{decay}\right)$$

| Verification Factor | Assigned Weight | Criteria |
|---|---|---|
| **$w_{\text{source}}$** | $1.0$ (Primary Source) | Official customer architectural blueprints or configuration exports. |
| | $0.8$ (Secondary Source) | Questionnaire transcripts or informal operational notes. |
| **$w_{\text{extraction}}$** | $1.0$ (Exact Match) | Direct block-level verbatim extraction with validated heading stack. |
| | $0.7$ (Inferred Extract) | LLM-synthesized claim derived from high-level RAPTOR tree clusters. |
| **Freshness Decay** | $\text{age} / \text{max\_age}$ | Linearly degrades confidence when evidence age approaches `verified_max_age_days`. |

---

## 5. Architectural Invariants for Agents

1. **Immutable Provenance:** Fragments stored in `evidence_vault.json` are append-only; retroactive text editing of stored fragments is strictly prohibited.
2. **Citations Required:** Every `Finding` in `findings.json` and `blueprint_<tower>_payload.json` must reference at least one valid `fragment_id`.
3. **Deterministic Persistence:** All graph transactions must record via `EpistemicGraph.append_event()` to maintain replayability and audit logging in SQLite.
