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
# ENGINEERING DESIGN DOCUMENT (EDD): DETERMINISTIC ONTOLOGICAL GATEKEEPING & MATURITY MATRIX COMPILER REFACTORING

**Document ID:** EDD-2026-SEC31-ONTOLOGY-GATEKEEPER  
**Author:** `gemini-4-argon` (Distinguished Principal Distributed Systems Architect & Lead Enterprise Ontologist)  
**Status:** APPROVED FOR DESIGN REVIEW  
**Target Subsystem:** `in_memory_asis_compiler.py`, `engine_config/ontologies/`, `engine_config/towers/`  
**Strict Compliance Mandates:** 100% Technical English in Codebase | Zero Hardcoding | Multi-Tenant & Vertical-Agnostic | Deterministic Execution  

---

## 1. EXECUTIVE ARCHITECTURAL SUMMARY

The current implementation of `derive_in_memory_maturity_matrix` in `in_memory_asis_compiler.py` suffers from a critical **Positional Fallacy (`findings[0]`, `findings[1]`)** and **Lack of Ontological Boundary Enforcement**. When upstream ingestion or LLM-assisted extraction misclassifies an operational finding—or when a tower's local `findings` array is populated with unverified cross-domain telemetry—the compiler blindly maps `findings[0]` as a "Strength" and `findings[1]` as a "Critical Breach". This results in severe semantic contamination (e.g., reporting HCI/SimpliVity RAM saturation under *Physical Security & Fire Protection*).

To eradicate this defect class permanently across all present and future tenants, verticals, and languages, we will re-architect the compilation pipeline around a **4-Phase Deterministic Ontological Gatekeeper Pattern**. Every Strength and Critical Breach rendered in Section 3.1 will be mathematically anchored to the pillar's verified Key Performance Indicators (KPIs) and validated against a dynamically compiled, configuration-driven Domain Ontology Graph.

---

## 2. MULTI-PHASE EXECUTION ROADMAP (EXACTLY 4 PHASES)

To guarantee zero regressions, maintain clean separation of concerns, and allow atomic verification at every step, this architectural remediation requires **exactly four (4) sequential phases**.

```text
+-----------------------------------------------------------------------------------+
| PHASE 1: Dynamic Ontological Graph Loader & Taxonomic Indexer                     |
|   Input: global_tech_ontology.yaml + tower_definition_*.json                      |
|   Output: Immutable In-Memory DomainTaxonomyGraph (Zero Hardcoding)               |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| PHASE 2: Deterministic Semantic Gatekeeper & Cross-Pillar Quarantine Engine       |
|   Input: Candidate Finding / Telemetry + Target Pillar ID + DomainTaxonomyGraph   |
|   Output: OntologicalValidationResult (VALID | QUARANTINED_FOREIGN_DOMAIN)        |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| PHASE 3: KPI-Anchored Maturity Matrix Compiler Refactoring                        |
|   Input: Pillar KPIs, Validated Findings, Localized Formulation Templates         |
|   Output: Strictly Partitioned Strengths (KPI >= 4.0) & Breaches (KPI < 4.0)      |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| PHASE 4: Mathematical & Ontological Certification Test Suite                      |
|   Input: Multi-Vertical Synthetic Payloads + Adversarial Cross-Pillar Injections  |
|   Output: 100% Pass Rate on Boundary Isolation & Zero-Contamination Invariants    |
+-----------------------------------------------------------------------------------+
```

### Phase 1: Dynamic Ontological Graph Loader & Taxonomic Indexer
* **What will be programmed:** A new core module (`src/core/ontology/taxonomy_loader.py`) containing `DomainTaxonomyRegistry` and `PillarOntologyProfile`.
* **Why:** Before we can validate whether a finding belongs to a specific pillar, the system needs a deterministic, in-memory representation of what concepts, vendor technologies, metrics, and keywords belong to which domain—and which concepts are strictly mutually exclusive. By building a dynamic indexer that reads `engine_config/ontologies/global_tech_ontology.yaml` and merges it with `engine_config/towers/*/tower_definition_*.json`, we achieve **zero hardcoding**. New towers (`T1..T10`, `D1..D8`, or custom client slugs) are automatically indexed at runtime.

### Phase 2: Deterministic Semantic Gatekeeper & Cross-Pillar Quarantine Engine
* **What will be programmed:** A new validation engine (`src/core/ontology/semantic_gatekeeper.py`) implementing `OntologicalGatekeeper.evaluate_finding_affinity(text, target_pillar_id, language_code)`.
* **Why:** Textual findings arriving from upstream collectors or hybrid extractors cannot be trusted blindly. This phase implements a deterministic scoring algorithm (using exact token/phrase trie matching, vendor/product affinity maps, and negative/exclusionary boundary sets from Phase 1). If a finding assigned to *Fire Protection* contains tokens exclusively bound to *Compute/HCI* (e.g., `SimpliVity`, `RAM`, `Hypervisor`, `vCPU`), the Gatekeeper detects a **Negative Affinity Violation**, quarantines the finding, logs an structured audit event, and blocks it from entering the presentation layer.

### Phase 3: KPI-Anchored Maturity Matrix Compiler Refactoring
* **What will be programmed:** A complete refactoring of `derive_in_memory_maturity_matrix` inside `in_memory_asis_compiler.py` and the addition of a deterministic fallback synthesizer (`KPIGroundedSynthesizer`).
* **Why:** This eliminates the `findings[0]` / `findings[1]` anti-pattern.
  1. **Strengths** are strictly derived from the pillar's evaluated KPIs where `score >= 4.0` (or configurable high-water mark threshold).
  2. **Critical Breaches / Gaps** are strictly derived from the pillar's evaluated KPIs where `score < 4.0` (prioritizing the lowest scores first).
  3. Candidate textual findings are first filtered by polarity/severity and then passed through the Phase 2 `OntologicalGatekeeper`. Only findings that (a) pass ontological validation for that exact pillar and (b) correlate with the KPI's polarity are permitted. If no valid finding exists—or if the candidate finding was quarantined—the `KPIGroundedSynthesizer` generates a deterministic, localized statement directly from the KPI's metadata (`kpi_name`, `observed_value`, `target_benchmark`, `unit`) using locale templates from configuration.

### Phase 4: Mathematical & Ontological Certification Test Suite
* **What will be programmed:** Unit and integration test suites (`tests/unit/ontology/test_semantic_gatekeeper.py` and `tests/integration/compiler/test_maturity_matrix_isolation.py`).
* **Why:** To mathematically certify that cross-pillar contamination is impossible (`P(Contamination) = 0.0`), that KPI score boundaries (`>= 4.0` vs `< 4.0`) are strictly respected under all edge cases (e.g., all KPIs high, all KPIs low, empty findings, 100% poisoned findings), and that zero Spanish or hardcoded tenant strings exist in the codebase.

---

## 3. LEVERAGING CONFIGURATION ASSETS WITH ZERO HARDCODING

To serve any enterprise globally (from a $20M regional hospital to a $500B global bank) across any topology (`T1..T10`, `D1..D8`, or bespoke domain slugs), the architecture treats `global_tech_ontology.yaml` and `tower_definition_*.json` as the **Single Source of Taxonomic Truth**.

### 3.1 Configuration Schema Unification & Runtime Indexing

At initialization, `DomainTaxonomyRegistry` performs a two-stage union without relying on any static Python dictionaries or hardcoded domain names:

1. **Stage 1: Tower Definition Ingestion (`engine_config/towers/*/tower_definition_*.json`)**
   Each tower definition JSON defines its canonical `tower_id` / `pillar_id`, `domain_slug`, localized display names, `sub_pillars`, and `kpis` (including KPI names, descriptions, and measurement units). The loader extracts all domain-specific vocabulary directly from the tower's own KPI definitions and sub-pillar metadata.
2. **Stage 2: Global Tech Ontology Binding (`engine_config/ontologies/global_tech_ontology.yaml`)**
   The global ontology YAML defines hierarchical technology categories (e.g., `compute_virtualization`, `environmental_safety`, `network_fabric`, `database_engines`, `identity_access`), associated vendor/product signatures, metric signatures, and—crucially—`domain_bindings` and `mutually_exclusive_categories`.

### 3.2 Dynamic Affinity & Exclusion Matrix Construction

For every active pillar $P_i$ in the tenant's topology, the `DomainTaxonomyRegistry` constructs a `PillarOntologyProfile`:

$$\text{Profile}(P_i) = \langle \mathcal{A}^+(P_i), \mathcal{A}^-(P_i), \mathcal{K}(P_i) \rangle$$

Where:
* $\mathcal{A}^+(P_i)$ (**Positive Affinity Lexicon**): The union of normalized terms, technology signatures, acronyms, and metric units mapped to $P_i$'s `domain_slug` in `global_tech_ontology.yaml` plus terms extracted from $P_i$'s `tower_definition_*.json`.
* $\mathcal{A}^-(P_i)$ (**Negative / Exclusionary Lexicon**): The union of all technology signatures and domain-specific terms belonging exclusively to *other* pillars $\bigcup_{j \neq i} \mathcal{A}^+_{\text{exclusive}}(P_j)$ where $P_j$'s category is disjoint from $P_i$.
* $\mathcal{K}(P_i)$ (**Canonical KPI Map**): The dictionary of KPI schemas belonging strictly to $P_i$, indexed by `kpi_id`.

### 3.3 Multi-Tenant, Vertical-Agnostic, and Multi-Lingual Guarantees

| Architectural Dimension | How Zero-Hardcoding is Enforced |
| :--- | :--- |
| **Tenant Agnosticism** | No client names, environment tags, or specific asset IDs exist in Python code. Tenant context is passed via an immutable `AssessmentContext` DTO at runtime. |
| **Vertical Agnosticism** | Whether the tenant is in Banking (PCI-DSS/Core Banking), Healthcare (HIPAA/PACS), or Heavy Manufacturing (OT/SCADA), vertical-specific KPIs and ontological terms live purely in the loaded YAML/JSON packs. |
| **Topology Agnosticism** | The compiler iterates over whatever pillar IDs exist in the loaded topology graph (`for pillar_id, pillar_data in topology.pillars.items()`). It never assumes a fixed list of towers. |
| **Language Agnosticism** | All code is 100% English. Localized fallback strings for KPI synthesis are resolved via parameterized i18n template keys stored in `engine_config/locales/{lang}/compiler_templates.yaml`. |

---

## 4. DETAILED DESIGN: REFACTORING `derive_in_memory_maturity_matrix`

### 4.1 Eradicating the `findings[0]` Positional Fallacy

#### Legacy Anti-Pattern (To Be Removed)
```python
# ANTI-PATTERN: Naive positional indexing with zero semantic or KPI validation
strength = findings[0] if len(findings) > 0 else "Cumplimiento estándar"
breach = findings[1] if len(findings) > 1 else "Brecha identificada"
```
This legacy logic caused three fatal failures:
1. If `findings[0]` was a critical outage or a cross-pillar hallucination, it was reported as a **Strength**!
2. If `findings[1]` belonged to another tower (e.g., SimpliVity RAM saturation placed inside a Fire Protection array), it was blindly rendered as the **Critical Breach** for Fire Protection.
3. Hardcoded Spanish fallbacks violated the 100% English codebase mandate.

---

### 4.2 New Deterministic Architecture for `derive_in_memory_maturity_matrix`

Below is the exact production-grade Python architecture (100% English, strictly typed, zero hardcoding) that will replace the legacy function in Phase 2 and Phase 3.

#### 4.2.1 Data Contracts & Domain Models (`src/core/ontology/models.py`)

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


class ValidationVerdict(str, Enum):
    VALID_IN_DOMAIN = "VALID_IN_DOMAIN"
    QUARANTINED_FOREIGN_DOMAIN = "QUARANTINED_FOREIGN_DOMAIN"
    QUARANTINED_POLARITY_MISMATCH = "QUARANTINED_POLARITY_MISMATCH"
    INSUFFICIENT_SIGNAL = "INSUFFICIENT_SIGNAL"


class FindingPolarity(str, Enum):
    STRENGTH = "STRENGTH"
    BREACH = "BREACH"
    NEUTRAL = "NEUTRAL"


@dataclass(frozen=True)
class EvaluatedKPI:
    kpi_id: str
    pillar_id: str
    name: str
    score: float  # Normalized 1.0 to 5.0 scale
    observed_value: Optional[str] = None
    target_benchmark: Optional[str] = None
    unit: Optional[str] = None
    sub_pillar_name: Optional[str] = None


@dataclass(frozen=True)
class OntologicalValidationResult:
    verdict: ValidationVerdict
    target_pillar_id: str
    detected_foreign_pillar_id: Optional[str]
    positive_affinity_hits: List[str] = field(default_factory=list)
    negative_exclusion_hits: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    reason: str = ""


@dataclass(frozen=True)
class MaturityMatrixRow:
    pillar_id: str
    pillar_name: str
    maturity_score: float
    maturity_level_label: str
    primary_strength: str
    critical_breach: str
    supporting_strength_kpi_ids: List[str]
    supporting_breach_kpi_ids: List[str]
    quarantined_findings_count: int = 0
```

#### 4.2.2 The Semantic Gatekeeper (`src/core/ontology/semantic_gatekeeper.py`)

```python
import re
import logging
from typing import Dict, Set, Optional
from src.core.ontology.models import (
    OntologicalValidationResult,
    ValidationVerdict,
)
from src.core.ontology.taxonomy_loader import DomainTaxonomyRegistry

logger = logging.getLogger(__name__)


class OntologicalGatekeeper:
    """
    Deterministic semantic firewall that prevents cross-pillar contamination.
    Validates candidate findings against the dynamic DomainTaxonomyRegistry.
    """

    def __init__(self, taxonomy_registry: DomainTaxonomyRegistry) -> None:
        self._registry = taxonomy_registry

    def validate_finding_for_pillar(
        self,
        finding_text: str,
        target_pillar_id: str,
    ) -> OntologicalValidationResult:
        if not finding_text or not finding_text.strip():
            return OntologicalValidationResult(
                verdict=ValidationVerdict.INSUFFICIENT_SIGNAL,
                target_pillar_id=target_pillar_id,
                detected_foreign_pillar_id=None,
                reason="Candidate finding text is empty or whitespace.",
            )

        profile = self._registry.get_profile(target_pillar_id)
        normalized_text = self._normalize_text(finding_text)

        # 1. Check for Positive Affinity Matches in Target Pillar
        positive_hits = [
            term for term in profile.positive_lexicon
            if self._contains_exact_term(normalized_text, term)
        ]

        # 2. Check for Exclusive Foreign Pillar Signatures (Cross-Pillar Contamination)
        foreign_hits_by_pillar: Dict[str, List[str]] = {}
        for foreign_pillar_id, exclusive_terms in profile.negative_exclusion_map.items():
            hits = [
                term for term in exclusive_terms
                if self._contains_exact_term(normalized_text, term)
            ]
            if hits:
                foreign_hits_by_pillar[foreign_pillar_id] = hits

        # 3. Quarantine Rule: Any exclusive foreign domain signature triggers immediate quarantine
        # unless positive target domain affinity strictly dominates without exclusive hardware/tech conflict.
        if foreign_hits_by_pillar:
            dominant_foreign_pillar = max(
                foreign_hits_by_pillar.keys(),
                key=lambda k: len(foreign_hits_by_pillar[k]),
            )
            all_negative_hits = [
                hit for hits in foreign_hits_by_pillar.values() for hit in hits
            ]
            logger.warning(
                "Ontological quarantine triggered for pillar '%s'. "
                "Detected foreign domain ('%s') signatures: %s",
                target_pillar_id,
                dominant_foreign_pillar,
                all_negative_hits,
            )
            return OntologicalValidationResult(
                verdict=ValidationVerdict.QUARANTINED_FOREIGN_DOMAIN,
                target_pillar_id=target_pillar_id,
                detected_foreign_pillar_id=dominant_foreign_pillar,
                positive_affinity_hits=positive_hits,
                negative_exclusion_hits=all_negative_hits,
                confidence_score=1.0,
                reason=(
                    f"Quarantined due to exclusive foreign domain terms "
                    f"belonging to '{dominant_foreign_pillar}': {all_negative_hits}"
                ),
            )

        # 4. Require at least one positive ontological anchor in the target pillar
        if not positive_hits:
            return OntologicalValidationResult(
                verdict=ValidationVerdict.INSUFFICIENT_SIGNAL,
                target_pillar_id=target_pillar_id,
                detected_foreign_pillar_id=None,
                reason="No verifiable domain terms matched target pillar ontology.",
            )

        return OntologicalValidationResult(
            verdict=ValidationVerdict.VALID_IN_DOMAIN,
            target_pillar_id=target_pillar_id,
            detected_foreign_pillar_id=None,
            positive_affinity_hits=positive_hits,
            negative_exclusion_hits=[],
            confidence_score=min(1.0, len(positive_hits) * 0.35),
            reason="Verified ontological alignment with target pillar.",
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower().strip())

    @staticmethod
    def _contains_exact_term(normalized_text: str, term: str) -> bool:
        pattern = rf"(?<!\w){re.escape(term.lower())}(?!\w)"
        return re.search(pattern, normalized_text) is not None
```

#### 4.2.3 Refactored `derive_in_memory_maturity_matrix` (`in_memory_asis_compiler.py`)

```python
from typing import Any, Dict, List, Tuple
from src.core.ontology.models import (
    EvaluatedKPI,
    FindingPolarity,
    MaturityMatrixRow,
    ValidationVerdict,
)
from src.core.ontology.semantic_gatekeeper import OntologicalGatekeeper
from src.core.ontology.kpi_synthesizer import KPIGroundedSynthesizer

STRENGTH_SCORE_THRESHOLD: float = 4.0


def derive_in_memory_maturity_matrix(
    pillars_payload: List[Dict[str, Any]],
    gatekeeper: OntologicalGatekeeper,
    synthesizer: KPIGroundedSynthesizer,
    locale: str = "en",
) -> List[MaturityMatrixRow]:
    """
    Derives the Section 3.1 Executive Maturity Matrix deterministically.

    Architectural Invariants:
    1. Strengths are strictly anchored to pillar KPIs with score >= 4.0.
    2. Critical Breaches are strictly anchored to pillar KPIs with score < 4.0.
    3. Candidate findings must pass OntologicalGatekeeper validation for the
       specific target pillar and match the required polarity.
    4. Quarantined or missing findings are deterministically replaced with
       KPI-anchored formulations generated by KPIGroundedSynthesizer.
    """
    matrix_rows: List[MaturityMatrixRow] = []

    for pillar in pillars_payload:
        pillar_id = str(pillar["pillar_id"])
        pillar_name = str(pillar["pillar_name"])
        maturity_score = float(pillar.get("maturity_score", 0.0))
        maturity_label = synthesizer.resolve_maturity_level_label(
            score=maturity_score, locale=locale
        )

        evaluated_kpis = _extract_and_validate_kpis(pillar, pillar_id)

        # Strict Mathematical Partitioning of KPIs
        strength_kpis = sorted(
            [kpi for kpi in evaluated_kpis if kpi.score >= STRENGTH_SCORE_THRESHOLD],
            key=lambda k: (-k.score, k.kpi_id),
        )
        breach_kpis = sorted(
            [kpi for kpi in evaluated_kpis if kpi.score < STRENGTH_SCORE_THRESHOLD],
            key=lambda k: (k.score, k.kpi_id),
        )

        # Partition and Ontologically Filter Candidate Findings
        raw_findings = pillar.get("findings", [])
        valid_strength_findings, valid_breach_findings, quarantined_count = (
            _filter_and_classify_findings(
                raw_findings=raw_findings,
                pillar_id=pillar_id,
                gatekeeper=gatekeeper,
            )
        )

        # Derive Primary Strength (Strictly Grounded in KPIs >= 4.0)
        primary_strength_text = _resolve_strength_statement(
            strength_kpis=strength_kpis,
            valid_strength_findings=valid_strength_findings,
            pillar_name=pillar_name,
            synthesizer=synthesizer,
            locale=locale,
        )

        # Derive Critical Breach (Strictly Grounded in KPIs < 4.0)
        critical_breach_text = _resolve_breach_statement(
            breach_kpis=breach_kpis,
            valid_breach_findings=valid_breach_findings,
            pillar_name=pillar_name,
            synthesizer=synthesizer,
            locale=locale,
        )

        matrix_rows.append(
            MaturityMatrixRow(
                pillar_id=pillar_id,
                pillar_name=pillar_name,
                maturity_score=round(maturity_score, 2),
                maturity_level_label=maturity_label,
                primary_strength=primary_strength_text,
                critical_breach=critical_breach_text,
                supporting_strength_kpi_ids=[k.kpi_id for k in strength_kpis[:3]],
                supporting_breach_kpi_ids=[k.kpi_id for k in breach_kpis[:3]],
                quarantined_findings_count=quarantined_count,
            )
        )

    return matrix_rows


def _filter_and_classify_findings(
    raw_findings: List[Any],
    pillar_id: str,
    gatekeeper: OntologicalGatekeeper,
) -> Tuple[List[str], List[str], int]:
    """
    Passes every candidate finding through the OntologicalGatekeeper and
    verifies explicit polarity metadata (never positional index).
    """
    valid_strengths: List[str] = []
    valid_breaches: List[str] = []
    quarantined_count: int = 0

    for item in raw_findings:
        # Support structured finding dicts; reject raw unverified positional strings
        # unless they carry explicit polarity and pass ontological gatekeeping.
        if isinstance(item, dict):
            text = str(item.get("description") or item.get("text") or "").strip()
            declared_polarity = str(item.get("polarity", "")).upper()
            kpi_score_ref = item.get("kpi_score")
        else:
            # Raw strings lack verifiable polarity metadata; still run gatekeeper
            # to count quarantines, but do not guess polarity from list position!
            text = str(item).strip()
            declared_polarity = FindingPolarity.NEUTRAL.value
            kpi_score_ref = None

        validation = gatekeeper.validate_finding_for_pillar(
            finding_text=text,
            target_pillar_id=pillar_id,
        )

        if validation.verdict != ValidationVerdict.VALID_IN_DOMAIN:
            if validation.verdict == ValidationVerdict.QUARANTINED_FOREIGN_DOMAIN:
                quarantined_count += 1
            continue

        # Enforce strict alignment between finding polarity and KPI score threshold
        if (
            declared_polarity == FindingPolarity.STRENGTH.value
            and (kpi_score_ref is None or float(kpi_score_ref) >= STRENGTH_SCORE_THRESHOLD)
        ):
            valid_strengths.append(text)
        elif (
            declared_polarity == FindingPolarity.BREACH.value
            and (kpi_score_ref is None or float(kpi_score_ref) < STRENGTH_SCORE_THRESHOLD)
        ):
            valid_breaches.append(text)

    return valid_strengths, valid_breaches, quarantined_count


def _resolve_strength_statement(
    strength_kpis: List[EvaluatedKPI],
    valid_strength_findings: List[str],
    pillar_name: str,
    synthesizer: KPIGroundedSynthesizer,
    locale: str,
) -> str:
    """
    Ensures Strengths are ONLY reported when backed by KPIs >= 4.0.
    If no KPI meets the >= 4.0 threshold, deterministically states that no
    sub-pillar achieved high-maturity thresholds, preventing false-positive praise.
    """
    if not strength_kpis:
        return synthesizer.synthesize_no_high_maturity_kpi(
            pillar_name=pillar_name,
            threshold=STRENGTH_SCORE_THRESHOLD,
            locale=locale,
        )

    if valid_strength_findings:
        return valid_strength_findings[0]

    return synthesizer.synthesize_strength_from_kpis(
        top_kpis=strength_kpis[:2],
        pillar_name=pillar_name,
        locale=locale,
    )


def _resolve_breach_statement(
    breach_kpis: List[EvaluatedKPI],
    valid_breach_findings: List[str],
    pillar_name: str,
    synthesizer: KPIGroundedSynthesizer,
    locale: str,
) -> str:
    """
    Ensures Breaches are ONLY reported from KPIs < 4.0 belonging to this pillar.
    If a candidate finding was quarantined (e.g., SimpliVity RAM in Fire Protection),
    synthesizes a deterministic breach anchored strictly to the lowest-scoring KPIs.
    """
    if not breach_kpis:
        return synthesizer.synthesize_no_critical_breach_kpi(
            pillar_name=pillar_name,
            threshold=STRENGTH_SCORE_THRESHOLD,
            locale=locale,
        )

    if valid_breach_findings:
        return valid_breach_findings[0]

    return synthesizer.synthesize_breach_from_kpis(
        lowest_kpis=breach_kpis[:2],
        pillar_name=pillar_name,
        locale=locale,
    )
```

---

## 5. AUTOMATED CERTIFICATION TEST SUITE (MATHEMATICAL & ONTOLOGICAL PROOF)

To certify **10/10 quality** and prove mathematically that cross-pillar contamination cannot occur across any deliverable, Phase 4 introduces an automated verification suite divided into **Unit Tests**, **Property-Based Ontological Invariant Tests**, and **End-to-End Multi-Vertical Integration Tests**.

### 5.1 Unit Tests (`tests/unit/ontology/test_semantic_gatekeeper.py`)

1. **`test_quarantine_hci_ram_saturation_in_environmental_safety_pillar`**
   * **Scenario:** Inject the exact historical failure case (`"Critical RAM saturation at 94% on HPE SimpliVity hyperconverged cluster nodes"`) into the *Fire Protection & Environmental Safety* pillar.
   * **Assertion:** `gatekeeper.validate_finding_for_pillar()` returns `ValidationVerdict.QUARANTINED_FOREIGN_DOMAIN`, identifies the Compute/HCI domain as `detected_foreign_pillar_id`, and records `["simplivity", "ram", "hyperconverged"]` in `negative_exclusion_hits`.
2. **`test_bidirectional_cross_pillar_permutation_matrix`**
   * **Scenario:** Dynamically load all $N$ pillars from `engine_config/towers/*/tower_definition_*.json`. For every pair of distinct pillars $(P_i, P_j)$ where $i \neq j$, generate synthetic findings containing exclusive technology signatures of $P_j$ and inject them into $P_i$.
   * **Assertion:** Across all $N \times (N - 1)$ off-diagonal permutations, 100% of injected foreign findings are quarantined (`quarantine_rate == 1.0`).
3. **`test_kpi_threshold_partition_boundary_conditions`**
   * **Scenario:** Test KPIs with exact boundary scores: `3.99`, `4.00`, `4.01`, `1.00`, `5.00`.
   * **Assertion:**
     * `score == 3.99` is strictly routed to `breach_kpis` (`< 4.0`).
     * `score == 4.00` is strictly routed to `strength_kpis` (`>= 4.0`).
     * Set intersection $\text{StrengthKPIs} \cap \text{BreachKPIs} = \emptyset$.

### 5.2 Compiler Integration Tests (`tests/integration/compiler/test_maturity_matrix_isolation.py`)

4. **`test_elimination_of_findings_positional_fallacy`**
   * **Scenario:** Provide a pillar payload where `findings` is a raw list of two strings: `findings[0]` is a breach (`"FM-200 fire suppression cylinder pressure below operational threshold"`) and `findings[1]` is a foreign hallucination (`"BGP route flapping on core WAN router"`).
   * **Assertion:**
     * `findings[0]` is **never** assigned to `primary_strength` simply because it sits at index `0`.
     * `findings[1]` is quarantined (`quarantined_findings_count == 1`).
     * Both `primary_strength` and `critical_breach` are deterministically synthesized from the pillar's verified KPIs (`>= 4.0` and `< 4.0` respectively).
5. **`test_all_low_kpis_prevents_hallucinated_strength`**
   * **Scenario:** A pillar has all KPIs scoring `< 4.0` (e.g., scores `[2.1, 1.8, 3.2]`), even though a rogue positive finding was injected into `findings`.
   * **Assertion:** `primary_strength` explicitly uses the `synthesize_no_high_maturity_kpi` template rather than fabricating a false strength.
6. **`test_all_high_kpis_prevents_hallucinated_breach`**
   * **Scenario:** A pillar has all KPIs scoring `>= 4.0` (e.g., scores `[4.2, 4.8, 4.5]`).
   * **Assertion:** `critical_breach` explicitly uses the `synthesize_no_critical_breach_kpi` template rather than fabricating a false breach.
7. **`test_multi_vertical_multi_topology_agnostic_execution`**
   * **Scenario:** Parameterize the compiler test across three distinct synthetic enterprise profiles:
     * *Profile A:* Global Retail Bank (`D1..D8` topology, `en` locale).
     * *Profile B:* Healthcare Network (`T1..T10` topology, `es` locale output via config templates).
     * *Profile C:* Heavy Manufacturing Conglomerate (Custom domain slugs `OT_SCADA`, `PLANT_SAFETY`, `CLOUD_CORE`).
   * **Assertion:** All three topologies compile with zero unhandled exceptions, zero cross-pillar contamination, and 100% KPI-grounded traceability (`supporting_strength_kpi_ids` and `supporting_breach_kpi_ids` populated).
8. **`test_static_ast_codebase_english_and_zero_hardcoding_compliance`**
   * **Scenario:** Parse the Abstract Syntax Tree (AST) of all modified and newly created Python modules (`taxonomy_loader.py`, `semantic_gatekeeper.py`, `kpi_synthesizer.py`, `in_memory_asis_compiler.py`).
   * **Assertion:**
     * Zero Spanish characters/tokens (`á, é, í, ó, ú, ñ, ¿, ¡` or Spanish keywords like `brecha`, `fortaleza`, `cumplimiento`, `incendio`) exist in Python string literals, comments, identifiers, or docstrings.
     * Zero hardcoded client names or static tower names exist in the Python logic.

---

## 6. SUMMARY OF ARCHITECTURAL GUARANTEES

| Defect / Requirement | Legacy State | Post-Remediation State (EDD-2026-SEC31) |
| :--- | :--- | :--- |
| **Positional Indexing (`findings[0]`)** | Naive `findings[0]` = Strength, `findings[1]` = Breach | **Eliminated.** Driven strictly by KPI score partitions (`>= 4.0` vs `< 4.0`) and verified polarity. |
| **Cross-Pillar Contamination** | Unfiltered (e.g., SimpliVity RAM in Fire Protection) | **Quarantined.** Blocked by `OntologicalGatekeeper` using negative exclusion sets from `global_tech_ontology.yaml`. |
| **Fallback Mechanism** | Hardcoded Spanish strings | **Deterministic KPI Synthesis.** Parameterized, locale-aware templates anchored to `kpi_name`, `observed_value`, and `target_benchmark`. |
| **Codebase Language** | Mixed English/Spanish | **100% Technical English** enforced via AST static analysis test. |
| **Multi-Tenancy & Verticals** | Brittle assumptions | **100% Configuration-Driven** across any vertical, company size, or domain topology. |

---
*Ready to proceed to **Phase 1 implementation** upon your explicit authorization.*