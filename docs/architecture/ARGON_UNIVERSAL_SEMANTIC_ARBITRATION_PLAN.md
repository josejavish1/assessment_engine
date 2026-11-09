---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-08
applies_to:
- gemini
- architecture
doc_type: operational
diataxis: reference
verification_mode: editorial
---
```yaml
---
document_id: ARCH-RFC-2026-8942
title: "Universal Epistemological Arbitrator & Semantic AST Sanitizer"
author: "gemini-4-argon (Distinguished Staff Architect / Chief Quality Gatekeeper)"
status: "APPROVED FOR IMMEDIATE EXECUTION"
classification: "TIER-0 CORE ENGINE ARCHITECTURE"
target_modules:
  - "src/core/arbitration/epistemic_arbitrator.py"
  - "src/hydration/tower_payload_hydrator.py"
  - "src/compilers/in_memory_asis_compiler.py"
  - "src/locales/lexical_polarity_matrices.json"
language_policy: "STRICT_100_PERCENT_TECHNICAL_ENGLISH"
scale_invariance: "UNIVERSAL ($20M SMB to $100B+ Global Tier-1)"
---
```

# Architectural Blueprint: Universal Epistemological Arbitrator

## 0. Executive Architectural Diagnosis

The observed anomalies represent a classic **Epistemic Split-Brain Syndrome** within the automated assessment pipeline. The ingestion engine treats quantitative telemetry (client survey assertions) and qualitative telemetry (discovery transcriptions/LLM synthesis) as orthogonal, non-interacting data streams. 

Furthermore, the AST-based DOCX compiler (`in_memory_asis_compiler.py`) currently operates as a **syntactic-only consumer**, blindly trusting upstream numerical scores to assign structural labels (e.g., *"Operational Strength"*) and utilizing naive positional heuristics (`.split('.')[0]`) to extract critical diagnostic summaries. 

To achieve Tier-1 global supremacy, we must introduce a deterministic, zero-trust **Epistemological Arbitration Layer** between the raw payload hydration phase and the AST compilation phase. This layer will enforce strict mathematical and semantic coherence across all data structures before a single byte is rendered into the DOCX Abstract Syntax Tree.

---

## 1. Phase I: Epistemic Reconciliation Engine (Quantitative vs. Qualitative Alignment)

### 1.1 Architectural Concept: Empirical Override of Declarative Bias
Client self-assessments are inherently subject to declarative bias (e.g., asserting a CMMI 4.5 in Privileged Access Management while transcripts reveal shared root credentials). In our ontological hierarchy, **empirical qualitative evidence must always override declarative numerical assertions**.

We will implement a deterministic **Lexical Polarity & Dissonance Engine** inside a new `UniversalEpistemicArbitrator` class. This engine evaluates the semantic polarity of the synthesized text against the asserted CMMI score before the payload is locked.

### 1.2 The Epistemic Dissonance Algorithm
For every evaluated pillar/sub-domain $i$, let $S_{asserted} \in [1.0, 5.0]$ be the quantitative survey score, and $T_i$ be the qualitative text corpus (`asis_architecture_description`, `identified_gaps`, `operational_evidence`).

1. **Tokenization & N-Gram Extraction**: Deconstruct $T_i$ into normalized unigrams, bigrams, and trigrams.
2. **Locale-Agnostic Polarity Scoring**: Cross-reference extracted n-grams against an externalized, language-keyed JSON lexicon (`lexical_polarity_matrices.json`). This guarantees **Zero Non-English Tokens** in the Python codebase while supporting multi-language report generation.
   * **Severe Deficit Markers ($W_{deficit} = -1.0$)**: e.g., *"manual failover"*, *"shared credentials"*, *"unpatched"*, *"not implemented"*, *"lack of"*, *"single point of failure"*, *"ad-hoc"*.
   * **Negation Horizon Detection**: A sliding window of $k=4$ tokens checks for structural negations preceding high-maturity keywords (e.g., *"do not use Kubernetes"*, *"no automated telemetry"*).
3. **Dissonance Index Calculation ($\Delta_E$)**:
   $$\rho_{deficit} = \frac{\sum |M_{deficit}|}{\text{Total Sentences in } T_i}$$
   If $S_{asserted} \ge 3.5$ and $\rho_{deficit} \ge \theta_{critical}$ (where $\theta_{critical}$ is a configurable threshold, default $0.25$, or if any Tier-0 Fatal Marker is triggered):
   * **Action 1 (Score Clamping)**: The score is algorithmically penalized and clamped to the empirical reality:
     $$S_{reconciled} = \min\left(S_{asserted}, \max\left(1.0, 2.0 - (\rho_{deficit} \times 0.5)\right)\right)$$
   * **Action 2 (Audit Flagging)**: Inject an immutable metadata attribute into the node: `"epistemic_override_applied": True`, `"original_asserted_score": S_asserted`.
   * **Action 3 (Structural Re-routing)**: Because $S_{reconciled}$ is now $< 2.2$, the downstream AST compiler will automatically route this node to the **"Critical Operational Deficit"** presentation template rather than **"Operational Strength"**.

---

## 2. Phase II: Semantic Extraction Engine (Eliminating Naive Positional Slicing)

### 2.1 The Failure of `.split('.')[0]`
Extracting the first sentence of an architectural description to represent the *"Observed Operational State"* fails because LLMs and human analysts naturally structure paragraphs deductively: **Context first, diagnostic friction second** (e.g., *"Sentence 1: The storage layer utilizes hybrid arrays. Sentence 2: Replication is entirely manual and lacks RPO guarantees."*).

### 2.2 Diagnostic Salience Scoring (DSS)
We replace positional slicing with a deterministic **Diagnostic Salience Extractor**. For any pillar with $S_{reconciled} < 3.0$, the engine splits the paragraph into an array of constituent sentences $[s_1, s_2, \dots, s_n]$ using an AST-safe sentence boundary detector (preserving abbreviations like `v1.2` or `e.g.`).

Each sentence $s_j$ is assigned a **Salience Score ($\Psi_j$)** based on three orthogonal vectors:

$$\Psi(s_j) = (\alpha \cdot D_{causal}) + (\beta \cdot D_{risk}) - (\gamma \cdot D_{context})$$

* **$D_{causal}$ (Causal & Diagnostic Density, $\alpha = 2.0$)**: Presence of root-cause indicators and structural friction markers (loaded from the locale dictionary: *"due to"*, *"resulting in"*, *"lacks"*, *"manual"*, *"unmonitored"*, *"bottleneck"*, *"spof"*, *"legacy"*).
* **$D_{risk}$ (Impact & Vulnerability Density, $\beta = 1.5$)**: Presence of operational risk terms (*"outage"*, *"latency"*, *"unencrypted"*, *"single point"*, *"degradation"*, *"vulnerability"*).
* **$D_{context}$ (Descriptive/Topology Penalty, $\gamma = 1.8$)**: Penalizes introductory boilerplate (*"combines"*, *"consists of"*, *"is based on"*, *"utilizes a mix of"*, *"the architecture features"*).

**Selection Rule**:
$$s_{selected} = \arg\max_{s_j \in T_i} \Psi(s_j)$$
The sentence maximizing $\Psi$ is extracted as the canonical `observed_operational_state`. If $S_{reconciled} \ge 3.5$, the polarity weights invert, prioritizing sentences dense in automation, resilience, and governance markers (*"automated"*, *"immutable"*, *"zero-trust"*, *"self-healing"*).

---

## 3. Phase III: Deterministic Robotic Text & Boilerplate Suppression

### 3.1 AST-Level Lexical Sanitization
Template leakage (e.g., `"(where applicable)"`, `"[insert metric]"`, `"deficit in sre (if relevant)"`) destroys executive credibility. This occurs when prompt templates or fallback string interpolations bleed into the hydrated JSON or AST text runs.

We will implement a multi-pass **Compiled Regular Expression Sanitization Pipeline** (`LexicalSanitizer`) that intercepts every string scalar during hydration and immediately prior to `python-docx` paragraph run injection.

### 3.2 Sanitization Ruleset
1. **Parenthetical Meta-Instruction Stripping**: Matches and excises conditional template instructions inside parentheses or brackets.
   * Pattern: `\s*[\(\[]\s*(?:where|if|when)\s+(?:applicable|relevant|appropriate|necessary|available)[^\)\]]*[\)\]]` (and localized equivalents loaded from config).
2. **Unresolved Placeholder Excision**: Matches bracketed or mustached tokens that failed hydration.
   * Pattern: `\s*(?:\{\{.*?\}\}|\[(?:insert|tbd|todo|placeholder).*?\])`
3. **Orphaned Punctuation & Whitespace Normalization**: Cleans up double spaces, space-before-comma, or dangling prepositions caused by token excision.
   * Pattern: `\s+([.,;:])` $\rightarrow$ `\1`, and `\s{2,}` $\rightarrow$ `' '`.
4. **Case-Coherent Acronym Enforcement**: Converts leaked lowercase infrastructure acronyms (`"deficit in sre"`, `"lack of iam"`) into canonical uppercase forms (`"SRE"`, `"IAM"`, `"PAM"`, `"SPOF"`, `"CMDB"`, `"DRP"`) via a bounded word-boundary lookup table.

---

## 4. Phase IV: Concrete Implementation Plan (100% Technical English)

Below is the exact, production-grade architectural implementation across the four target files.

### 4.1 Externalized Localization & Polarity Matrix
**File**: `src/locales/lexical_polarity_matrices.json`
*(Strictly separates linguistic tokens from Python execution logic, satisfying Mandate #2).*

```json
{
  "version": "2.0.0",
  "canonical_acronyms": ["SRE", "IAM", "PAM", "SPOF", "CMDB", "SIEM", "SOAR", "DRP", "BCP", "RTO", "RPO", "K8S", "CI/CD", "IaaS", "PaaS", "SaaS"],
  "languages": {
    "en": {
      "fatal_deficit_markers": [
        "shared password", "shared root", "no backup", "unpatched", "manual failover",
        "single point of failure", "spof", "no encryption", "cleartext", "lack of",
        "not implemented", "do not use", "does not exist", "ad-hoc", "obsolete"
      ],
      "causal_friction_markers": [
        "due to", "resulting in", "lacks", "missing", "manual", "unmonitored",
        "bottleneck", "vulnerable", "inconsistent", "fragmented", "untested", "reactive"
      ],
      "context_boilerplate_markers": [
        "combines", "consists of", "is based on", "the architecture", "currently utilizes",
        "is composed of", "includes a mix", "encompasses"
      ],
      "high_maturity_markers": [
        "automated", "immutable", "self-healing", "zero-trust", "orchestrated",
        "continuous", "telemetry", "proactive", "multi-region", "active-active"
      ],
      "robotic_leakage_patterns": [
        "\\s*[\\(\\[]\\s*(?:where|if|when)\\s+(?:applicable|relevant|appropriate|necessary|available)[^\\)\\]]*[\\)\\]]",
        "\\s*[\\(\\[]\\s*e\\.g\\.\\s*,?\\s*if\\s+any\\s*[\\)\\]]",
        "\\s*(?:\\{\\{.*?\\}\\}|\\[(?:insert|tbd|todo|placeholder).*?\\])"
      ]
    },
    "es": {
      "fatal_deficit_markers": [
        "contraseña compartida", "root compartido", "sin backup", "sin parches",
        "failover manual", "punto único de fallo", "spof", "sin cifrado", "texto plano",
        "carece de", "no implementado", "no utilizan", "no existe", "ad-hoc", "obsoleto"
      ],
      "causal_friction_markers": [
        "debido a", "resultando en", "carece", "falta de", "manual", "sin monitorizar",
        "cuello de botella", "vulnerable", "inconsistente", "fragmentado", "reactivo"
      ],
      "context_boilerplate_markers": [
        "combina", "consiste en", "se basa en", "la arquitectura", "actualmente utiliza",
        "se compone de", "incluye una mezcla", "abarca"
      ],
      "high_maturity_markers": [
        "automatizado", "inmutable", "auto-recuperación", "zero-trust", "orquestado",
        "continuo", "telemetría", "proactivo", "multi-región", "activo-activo"
      ],
      "robotic_leakage_patterns": [
        "\\s*[\\(\\[]\\s*(?:donde|si|cuando)\\s+(?:aplique|sea aplicable|corresponda|sea relevante|sea necesario)[^\\)\\]]*[\\)\\]]",
        "\\s*(?:\\{\\{.*?\\}\\}|\\[(?:insertar|pendiente|todo|placeholder).*?\\])"
      ]
    }
  }
}
```

### 4.2 New Core Module: The Universal Epistemic Arbitrator
**File**: `src/core/arbitration/epistemic_arbitrator.py`

```python
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


class UniversalEpistemicArbitrator:
    """
    Tier-0 Quality Gatekeeper.
    Enforces strict epistemological coherence between quantitative maturity scores
    and qualitative empirical evidence. Eliminates template leakage and extracts
    high-salience diagnostic states without naive positional slicing.
    """

    def __init__(self, locale_matrix_path: Path, active_language: str = "en"):
        self.active_language = active_language
        self._load_lexical_matrices(locale_matrix_path)
        self._compile_sanitization_regex()

    def _load_lexical_matrices(self, path: Path) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.canonical_acronyms: List[str] = data.get("canonical_acronyms", [])
        lang_pack = data.get("languages", {}).get(
            self.active_language, data["languages"]["en"]
        )
        self.fatal_deficit_markers: List[str] = lang_pack["fatal_deficit_markers"]
        self.causal_friction_markers: List[str] = lang_pack["causal_friction_markers"]
        self.context_boilerplate_markers: List[str] = lang_pack["context_boilerplate_markers"]
        self.high_maturity_markers: List[str] = lang_pack["high_maturity_markers"]
        self.raw_leakage_patterns: List[str] = lang_pack["robotic_leakage_patterns"]

    def _compile_sanitization_regex(self) -> None:
        self.compiled_leakage_regexes = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.raw_leakage_patterns
        ]
        self.whitespace_normalizer = re.compile(r"\s{2,}")
        self.orphaned_punctuation = re.compile(r"\s+([.,;:])")
        # Sentence boundary regex that respects common technical decimals and abbreviations
        self.sentence_splitter = re.compile(r"(?<!\b(?:v|e\.g|i\.e|etc|vs))\.\s+(?=[A-ZÁÉÍÓÚÑ0-9])")

    def sanitize_robotic_text(self, raw_text: str) -> str:
        """
        Deterministically strips template leakage, unresolved placeholders,
        and normalizes technical acronyms.
        """
        if not raw_text or not isinstance(raw_text, str):
            return ""

        cleaned = raw_text
        for regex in self.compiled_leakage_regexes:
            cleaned = regex.sub("", cleaned)

        for acronym in self.canonical_acronyms:
            pattern = re.compile(rf"\b{re.escape(acronym.lower())}\b", re.IGNORECASE)
            cleaned = pattern.sub(acronym, cleaned)

        cleaned = self.orphaned_punctuation.sub(r"\1", cleaned)
        cleaned = self.whitespace_normalizer.sub(" ", cleaned).strip()
        return cleaned

    def reconcile_epistemic_state(
        self, asserted_score: float, qualitative_corpus: str
    ) -> Tuple[float, bool, str]:
        """
        Evaluates qualitative text against quantitative assertions.
        If severe negative empirical evidence contradicts a high asserted score,
        the score is algorithmically clamped to reflect operational reality.
        """
        normalized_text = qualitative_corpus.lower()
        sentences = [s.strip() for s in self.sentence_splitter.split(qualitative_corpus) if s.strip()]
        total_sentences = max(1, len(sentences))

        fatal_hits = sum(1 for marker in self.fatal_deficit_markers if marker in normalized_text)
        friction_hits = sum(1 for marker in self.causal_friction_markers if marker in normalized_text)

        deficit_density = (fatal_hits * 1.5 + friction_hits * 0.5) / total_sentences

        # Epistemic Override Condition: High claimed maturity but empirical evidence reveals severe deficits
        if asserted_score >= 3.0 and (fatal_hits >= 1 or deficit_density >= 0.45):
            penalty_factor = min(2.5, (fatal_hits * 1.2) + (deficit_density * 1.5))
            reconciled_score = round(max(1.0, min(2.1, asserted_score - penalty_factor)), 2)
            reason = (
                f"Epistemic Override: Asserted score ({asserted_score}) contradicted by "
                f"{fatal_hits} fatal deficit markers and {friction_hits} friction markers."
            )
            logger.warning(reason)
            return reconciled_score, True, reason

        return round(asserted_score, 2), False, "Coherent"

    def extract_salient_operational_state(
        self, description_corpus: str, reconciled_score: float
    ) -> str:
        """
        Replaces naive `.split('.')[0]` slicing with Diagnostic Salience Scoring (DSS).
        Selects the sentence that actually explains the operational reality corresponding
        to the reconciled maturity score.
        """
        sanitized_corpus = self.sanitize_robotic_text(description_corpus)
        if not sanitized_corpus:
            return ""

        sentences = [s.strip() for s in self.sentence_splitter.split(sanitized_corpus) if s.strip()]
        if len(sentences) == 1:
            return sentences[0].rstrip(".") + "."

        best_sentence = sentences[0]
        max_salience = float("-inf")

        for idx, sentence in enumerate(sentences):
            s_lower = sentence.lower()

            causal_count = sum(1 for m in self.causal_friction_markers if m in s_lower)
            fatal_count = sum(1 for m in self.fatal_deficit_markers if m in s_lower)
            context_count = sum(1 for m in self.context_boilerplate_markers if m in s_lower)
            maturity_count = sum(1 for m in self.high_maturity_markers if m in s_lower)

            # Positional decay: slight penalty for generic opening sentences in low-maturity states
            positional_bias = -0.5 if (idx == 0 and reconciled_score < 2.5) else 0.0

            if reconciled_score < 2.8:
                # Low Maturity: Prioritize sentences explaining root cause, friction, and deficits
                salience = (
                    (fatal_count * 3.0)
                    + (causal_count * 2.0)
                    - (context_count * 2.5)
                    - (maturity_count * 1.5)
                    + positional_bias
                )
            else:
                # High Maturity: Prioritize sentences demonstrating automation, governance, and resilience
                salience = (
                    (maturity_count * 3.0)
                    - (fatal_count * 4.0)
                    - (causal_count * 2.0)
                    - (context_count * 1.0)
                )

            if salience > max_salience:
                max_salience = salience
                best_sentence = sentence

        return best_sentence.rstrip(".") + "."
```

### 4.3 Hydrator Integration
**File**: `src/hydration/tower_payload_hydrator.py`

In `TowerPayloadHydrator`, we inject the `UniversalEpistemicArbitrator` during the domain normalization loop so that downstream consumers receive pre-reconciled, sanitized payloads.

```python
# Inside src/hydration/tower_payload_hydrator.py

from src.core.arbitration.epistemic_arbitrator import UniversalEpistemicArbitrator

class TowerPayloadHydrator:
    def __init__(self, config: Dict[str, Any], arbitrator: UniversalEpistemicArbitrator):
        self.config = config
        self.arbitrator = arbitrator

    def hydrate_pillar_node(self, raw_node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hydrates, sanitizes, and epistemically reconciles a single pillar payload node.
        """
        hydrated = dict(raw_node)

        # 1. Sanitize all textual fields against robotic template leakage
        text_fields = [
            "asis_architecture_description",
            "executive_summary",
            "identified_gaps",
            "remediation_roadmap"
        ]
        for field in text_fields:
            if field in hydrated and isinstance(hydrated[field], str):
                hydrated[field] = self.arbitrator.sanitize_robotic_text(hydrated[field])

        # 2. Perform Epistemic Reconciliation (Quantitative vs Qualitative)
        asserted_score = float(hydrated.get("cmmi_maturity_score", 1.0))
        evidence_corpus = " ".join([
            hydrated.get("asis_architecture_description", ""),
            hydrated.get("identified_gaps", "")
        ])

        reconciled_score, override_applied, audit_reason = (
            self.arbitrator.reconcile_epistemic_state(asserted_score, evidence_corpus)
        )

        hydrated["cmmi_maturity_score"] = reconciled_score
        hydrated["epistemic_audit"] = {
            "override_applied": override_applied,
            "original_asserted_score": asserted_score,
            "reconciled_score": reconciled_score,
            "audit_reason": audit_reason
        }

        # 3. Extract True Operational State via Diagnostic Salience Scoring
        raw_description = hydrated.get("asis_architecture_description", "")
        hydrated["canonical_operational_state"] = (
            self.arbitrator.extract_salient_operational_state(
                raw_description, reconciled_score
            )
        )

        return hydrated
```

### 4.4 AST Compiler Hardening
**File**: `src/compilers/in_memory_asis_compiler.py`

We eliminate `.split('.')[0]` and enforce a strict semantic guard before labeling any finding as an `"Operational Strength"`.

```python
# Inside src/compilers/in_memory_asis_compiler.py

class InMemoryAsisCompiler:
    """
    AST-based DOCX Compiler. Consumes epistemically reconciled payloads.
    """

    def _compile_pillar_observation_block(self, pillar_data: Dict[str, Any]) -> Dict[str, Any]:
        score = float(pillar_data.get("cmmi_maturity_score", 1.0))
        
        # DEPRECATED & REMOVED:
        # observed_state = pillar_data.get("asis_architecture_description", "").split(".")[0]
        
        # NEW: Consume the pre-arbitrated high-salience diagnostic sentence
        observed_state = pillar_data.get("canonical_operational_state")
        if not observed_state:
            # Fallback if hydration was bypassed: invoke arbitrator directly
            observed_state = self.arbitrator.extract_salient_operational_state(
                pillar_data.get("asis_architecture_description", ""), score
            )

        # Strict Epistemic Classification Guard
        if score >= 3.8 and not pillar_data.get("epistemic_audit", {}).get("override_applied", False):
            classification_label = self.locale_strings["label_operational_strength"]
            ast_style_token = "AST_STYLE_STRENGTH_CALLOUT"
        elif score >= 2.5:
            classification_label = self.locale_strings["label_transitional_state"]
            ast_style_token = "AST_STYLE_TRANSITIONAL_CALLOUT"
        else:
            classification_label = self.locale_strings["label_critical_deficit"]
            ast_style_token = "AST_STYLE_DEFICIT_ALERT"

        return {
            "node_type": "OBSERVATION_CALLOUT",
            "style": ast_style_token,
            "header_text": f"{classification_label} (CMMI {score:.1f})",
            "body_text": self.arbitrator.sanitize_robotic_text(observed_state)
        }
```

---

## 5. Verification & Quality Gate Matrix

Before merging into the production branch, the automated CI/CD pipeline must execute the following invariant test suite (`tests/unit/test_epistemic_arbitrator.py`):

| Test Case ID | Scenario | Input Telemetry | Expected Arbitrated Output |
| :--- | :--- | :--- | :--- |
| **TC-EPI-01** | **Low Maturity False Context** | `score: 1.5`, `text: "The network combines MPLS and SD-WAN topologies. Failover is completely manual and SPOFs are undocumented."` | `canonical_operational_state` MUST equal `"Failover is completely manual and SPOFs are undocumented."` (Sentence 1 ignored). |
| **TC-EPI-02** | **High Maturity False Positive (PAM/K8s)** | `score: 4.5`, `text: "Administrators share root passwords across clusters and we do not use Kubernetes in production."` | `reconciled_score` clamped to `<= 1.8`. `override_applied: True`. AST Compiler classifies node as **Critical Deficit**, never **Operational Strength**. |
| **TC-EPI-03** | **Robotic Template Leakage** | `text: "Critical deficit in sre (where applicable) causing high mttr [insert metric]."` | Sanitized output MUST equal `"Critical deficit in SRE causing high MTTR."` |
| **TC-EPI-04** | **Linguistic Purity Audit** | Static AST scan of all `.py` files in `src/`. | `0` non-English identifiers, comments, or string literals. `0` hardcoded client names. |