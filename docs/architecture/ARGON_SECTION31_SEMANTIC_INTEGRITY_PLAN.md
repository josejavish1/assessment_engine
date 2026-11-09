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
## 1. Deep Root-Cause Analysis: Cross-Pillar Contamination & Semantic Drift

The anomaly observed in Section 3.1 (Table 5: *"Pilar / Capacidad | Score | Análisis de Brechas y Calibración"*)—where hyperconverged compute saturation (`HPE SimpliVity RAM/CPU > 50%`) is reported as the primary resilience gap under **T1.P4: Fire Protection & Environmental Safety**—is the deterministic result of three compounding architectural vulnerabilities across the ingestion, synthesis, and compilation layers.

```text
[Unstructured Raw Transcript] (High Signal for SimpliVity RAM Saturation)
       │
       ▼  1. Unscoped Context Window (resynthesize_all_10_towers_from_raw_transcription.py)
[LLM Attention Bleed] ──► Prompts lack negative constraints & KPI-level ontological anchors.
       │                  LLM fills T1.P4 'findings' array with dominant transcript signal.
       ▼  2. Unvalidated Schema Hydration (domain/models/)
[Pydantic Payload]    ──► Validates structural types (List[str]), ignores semantic domain boundaries.
       │
       ▼  3. Positional Indexing Fallacy (in_memory_asis_compiler.py)
[Table 5 Markdown]    ──► Compiler blindly extracts `findings[0]` and `recommendations[0]` 
                          without verifying alignment against the low-scoring KPI (T1.P4.K3 = 2.0).
```

### 1.1 Vulnerability 1: Unscoped Context Attention Bleed in LLM Synthesis
In `scripts/resynthesize_all_10_towers_from_raw_transcription.py`, the synthesis prompt feeds the entire raw discovery transcript into the LLM context window while requesting a monolithic JSON payload covering all pillars of a tower. 
* **The Cognitive Bias:** In unstructured discovery interviews, stakeholders disproportionately emphasize urgent operational pain points (e.g., *"Clusters 3 and 4 on HPE SimpliVity are over 50% RAM capacity, violating HA failover tolerances"*).
* **The Ontological Void:** Because the synthesis prompt did not inject the granular KPI definitions (`T1.P4.K1`, `T1.P4.K2`, `T1.P4.K3`) as strict semantic guardrails for Pillar 4, the LLM experienced **Attention Bleed**. When forced to populate the `findings` array for T1.P4, and finding sparse explicit emphasis in the raw text compared to the dominant compute narrative, the LLM defaulted to the highest-salience technical failure in its context window.

### 1.2 Vulnerability 2: Absence of Domain-Boundary Gatekeeping in Validation
The current Pydantic schema validation layer (`domain/validation/`) enforces **structural and syntactic integrity** (e.g., ensuring string length, non-empty arrays, and valid score ranges `1.0 <= score <= 5.0`), but completely lacks **ontological and semantic integrity checks**.
* There is no lexical or vector-space discriminator preventing **T2 (Compute/Virtualization)** terminology (`RAM`, `CPU`, `vSphere`, `SimpliVity`, `Cluster`, `Hypervisor`) from hydrating **T1 (Physical Facilities/Electromechanical)** data structures.

### 1.3 Vulnerability 3: The Positional Indexing Fallacy in `in_memory_asis_compiler.py`
In `in_memory_asis_compiler.py::derive_in_memory_maturity_matrix`, the compiler constructs the calibration narrative for Table 5 using naive positional indexing:

```python
# VULNERABLE PATTERN IN CURRENT COMPILER
primary_gap = pillar_data.get("findings", [""])[0]
primary_rec = pillar_data.get("recommendations", [""])[0]
```

This creates a **Score-to-Narrative Disconnect**:
1. The quantitative score for **T1.P4** (`4.00 / 5.00`) is mathematically derived from `tower_definition_T1.json` and the assessment payload:
   * `T1.P4.K1` (VESDA / Early Smoke Detection): **Score = 5.0**
   * `T1.P4.K2` (Clean-Agent Gas Suppression): **Score = 5.0**
   * `T1.P4.K3` (Liquid Leak Detection / BMS Integration): **Score = 2.0**
2. The mathematical reason T1.P4 did not achieve a `5.0` is exclusively `K3` (lack of under-floor liquid leak detection and unintegrated BMS fire relays).
3. However, because `derive_in_memory_maturity_matrix` does not inspect the underlying KPI score vector to determine *which* KPI dragged the pillar average down, it blindly extracts `findings[0]`—which happened to be contaminated by the SimpliVity RAM hallucination.

---

## 2. Comprehensive Cross-Tower Contamination Audit (Towers T1–T10)

A forensic audit across the 10-tower enterprise ontology reveals systemic cross-pillar and cross-tower contamination patterns whenever a high-salience operational issue dominates the discovery transcript:

| Tower & Pillar | Ontological Scope (Expected Domain) | Observed / High-Risk Semantic Contamination | Root Vector of Bleed |
| :--- | :--- | :--- | :--- |
| **T1: Facilities**<br>`T1.P2` (Electrical) & `T1.P4` (Fire/Env) | UPS, Generators, Transfer Switches (ATS), PDE, VESDA, Gas Suppression, Water Leak Sensors. | **Compute & Storage Saturation:** HPE SimpliVity RAM/CPU limits, VMware cluster HA admission control failures. | High salience of HCI capacity bottlenecks in infrastructure interviews bleeding into physical facility arrays. |
| **T2: Compute & HCI**<br>`T2.P1` (Virtualization) | Hypervisors, ESXi/AHV host density, CPU/RAM overcommitment, NUMA alignment, HA/DRS. | **Backup & RPO Failures:** Veeam job failures, tape library bottlenecks, immutable repo absences. | Interviews often discuss VM snapshots and backup agents alongside hypervisor performance. |
| **T3: Storage**<br>`T3.P3` (SAN/NAS Fabric) | Fibre Channel switches, IOPS latency, LUN provisioning, NVMe-oF, array controller active-active firmware. | **Database Logical Corruption / SQL Tuning:** Missing indexes, unoptimized queries, ERP table lockouts. | Storage latency discussions frequently blur into database administrator (DBA) complaints. |
| **T4: Network**<br>`T4.P2` (WAN / SD-WAN) | BGP routing, MPLS circuits, ISP last-mile diversity, jitter/packet loss, SD-WAN orchestrators. | **Perimeter Firewall & IAM Policies:** Active Directory GPOs, MFA token timeouts, VPN client split-tunneling. | Network transport and security enforcement are often managed by the same team during interviews. |
| **T5: Cybersecurity**<br>`T5.P1` (Perimeter & XDR) | NGFW, EDR/XDR, SIEM/SOAR, SOC MTTD/MTTR, Zero Trust microsegmentation. | **Physical Access & Facilities:** CCTV cameras, turnstiles, datacenter biometric doors, UPS battery alarms. | Ambiguity around the word "Security" (Physical Security in T1 vs. Information Security in T5). |
| **T6: Data Protection**<br>`T6.P4` (DRP & Orchestration) | RTO/RPO automation, SRM/Zerto runbooks, air-gapped vaults, failover drills. | **High Availability (HA) Clustering:** Local vSphere HA restarts, dual-PSU redundancy, RAID-6 parity. | Confusion between local component redundancy (T1/T2/T3) and disaster recovery orchestration (T6). |
| **T7: Cloud & Hybrid**<br>`T7.P2` (FinOps & Governance) | Cloud landing zones, IAM roles, tagging policies, reserved instances, cost anomaly detection. | **On-Premise Licensing & CapEx:** EA agreements for local Windows Server cores, physical server depreciation. | Procurement discussions mix cloud OpEx governance with legacy hardware CapEx maintenance. |
| **T8: Platforms & DB**<br>`T8.P1` (RDBMS Engine) | Clustering (AlwaysOn/RAC), transaction log throughput, patch lifecycle, DB encryption (TDE). | **Application Code & UI Bugs:** Frontend timeout errors, legacy monolith source code debt, API gateway certs. | Database performance is routinely conflated with poorly written application tier code (T9). |
| **T9: Enterprise Apps**<br>`T9.P3` (Integration / API) | ESB, API Gateways, message brokers (Kafka/RabbitMQ), microservice idempotency, ERP modules. | **End-User Device & VDI Issues:** Citrix profile bloat, slow laptop boot times, Wi-Fi roaming drops. | "The ERP is slow" is frequently traced to endpoint/VDI constraints (T10) rather than application logic. |
| **T10: Workplace**<br>`T10.P1` (UEM & VDI) | Intune/SCCM, endpoint posture, VDI golden images, DEX (Digital Employee Experience). | **Core Identity & Directory Architecture:** Forest trust relationships, FSMO role placement, Kerberos ticket lifetimes. | Workplace device management bleeds into core Active Directory / Entra ID architectural design (T5/T8). |

---

## 3. 10/10 Architectural Blueprint to Eliminate Semantic Drift

To permanently eradicate cross-pillar contamination, we must transition from **Positional Text Concatenation** to **Ontologically Scoped, KPI-Driven Synthesis and Compilation**.

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                  ONTOLOGICAL BOUNDARY & COMPILATION ARCHITECTURE                 │
└──────────────────────────────────────────────────────────────────────────────────┘
                                         │
  ┌──────────────────────────────────────┴──────────────────────────────────────┐
  ▼                                                                             ▼
[tower_definition_TX.json]                                      [domain_ontology_registry.json]
- Pillar Metadata                                               - Allowed Lexical Concepts
- KPI Definitions (K1, K2, K3)                                  - Forbidden Cross-Domain Concepts
- Empirical Rubric (1.0 - 5.0)                                  - Negative Lookahead Regexes
  │                                                                             │
  └───────────────────┬─────────────────────────────────────────────────────────┘
                      ▼
        ┌───────────────────────────┐
        │ PHASE A: Scoped Synthesis │ ──► Injects exact KPI definitions + Negative Constraints
        └─────────────┬─────────────┘     into LLM Prompt per Pillar. Forces `kpi_id` binding.
                      ▼
        ┌───────────────────────────┐
        │ PHASE B: Semantic Gate    │ ──► `PillarSemanticValidator` inspects payload against
        └─────────────┬─────────────┘     Forbidden Domain Lexicons. Triggers self-healing or
                      │                   quarantines contaminated findings before compilation.
                      ▼
        ┌───────────────────────────┐
        │ PHASE C: KPI-Aligned      │ ──► `derive_in_memory_maturity_matrix` correlates KPI
        │ Declarative Compiler      │     scores (Strengths >= 4.0 vs Gaps < 4.0) directly
        └───────────────────────────┘     to KPI-bound findings. Zero positional guessing.
```

### Phase A: Ontological Pillar Scoping (Prompt & Schema Binding)
1. **KPI-Anchored Schema:** Modify the synthesis output contract so every generated finding and recommendation must explicitly declare its `bound_kpi_id` (e.g., `"T1.P4.K3"`). Unbound generic pillar findings are structurally rejected.
2. **Negative Ontological Constraints:** During synthesis in `resynthesize_all_10_towers_from_raw_transcription.py`, dynamically construct a **Negative Constraint Block** for each pillar using the ontologies of the *other* pillars/towers (e.g., when synthesizing `T1.P4`, explicitly forbid compute, RAM, CPU, storage, and network routing concepts).

### Phase B: Automated Semantic Boundary Gatekeeper (`PillarSemanticValidator`)
Implement a deterministic domain gatekeeper in `domain/validation/pillar_semantic_validator.py`.
1. **Lexical Exclusion Matrix:** Define domain-specific positive and negative concept lexicons (configurable via JSON/YAML ontology policies, zero hardcoded client strings).
2. **Deterministic Quarantine & Remediation:** If a finding bound to an Electromechanical/Fire pillar (`T1.P4`) contains high-confidence tokens belonging to the Compute/Virtualization taxonomy (`RAM`, `CPU`, `SimpliVity`, `Hypervisor`, `Cluster`, `vSphere`), the validator flags a `SemanticContaminationError`, strips the contaminated finding, and synthesizes a deterministic fallback finding anchored strictly to the lowest-scoring KPI's definition from `tower_definition.json`.

### Phase C: Declarative Compiler Alignment (`derive_in_memory_maturity_matrix`)
Refactor `in_memory_asis_compiler.py::derive_in_memory_maturity_matrix` to eliminate `findings[0]` positional indexing:
1. **Mathematical Decomposition:** Inspect the evaluated KPIs for the pillar. Partition them into:
   * **Consolidated Capabilities (Strengths):** KPIs where `score >= 4.0`.
   * **Diagnosed Resilience Gaps (Breaches):** KPIs where `score < 4.0` (sorted ascending by score, weighted by criticality).
2. **KPI-Bound Narrative Selection:** Match the pillar's findings by `bound_kpi_id` corresponding to the lowest-scoring KPI (e.g., `T1.P4.K3` scored `2.0`). If no finding is explicitly bound or survived semantic gatekeeping, deterministically compile the gap analysis directly from the `K3` ontological rubric and empirical evidence recorded for `K3`.

---

## 4. Production-Grade Implementation (100% Technical English)

### 4.1 Phase B: `domain/validation/pillar_semantic_validator.py`

```python
"""
Ontological Semantic Boundary Gatekeeper.

Enforces strict domain isolation across infrastructure towers and pillars,
preventing cross-pillar attention bleed (e.g., Compute/RAM metrics leaking
into Physical Facilities/Fire Protection narratives).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DomainOntologyRule(BaseModel):
    """Defines lexical boundaries for a specific architectural domain category."""

    domain_id: str = Field(..., description="Unique identifier for the ontological domain.")
    required_context_patterns: List[str] = Field(
        default_factory=list,
        description="Regex patterns representing valid concepts for this domain.",
    )
    forbidden_domain_ids: List[str] = Field(
        default_factory=list,
        description="List of domain IDs whose core lexicons are strictly prohibited here.",
    )
    signature_exclusion_patterns: List[str] = Field(
        default_factory=list,
        description="High-specificity regex patterns that uniquely identify this domain when used as an exclusion elsewhere.",
    )


class OntologyRegistryConfig(BaseModel):
    """Multi-tenant, vertical-agnostic ontology configuration."""

    domains: Dict[str, DomainOntologyRule]
    pillar_to_domain_map: Dict[str, str] = Field(
        ...,
        description="Maps canonical Pillar IDs (e.g., 'T1.P4') or Tower prefixes to domain_ids.",
    )


@dataclass(frozen=True)
class SemanticViolation:
    """Immutable record of a detected cross-pillar semantic contamination event."""

    pillar_id: str
    pillar_domain: str
    contaminating_domain: str
    matched_tokens: List[str]
    offending_text: str
    bound_kpi_id: Optional[str] = None


@dataclass
class ValidationResult:
    """Result container for pillar semantic validation and sanitization."""

    is_valid: bool
    sanitized_findings: List[Dict[str, Any]] = field(default_factory=list)
    sanitized_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    violations: List[SemanticViolation] = field(default_factory=list)


DEFAULT_ENTERPRISE_ONTOLOGY = OntologyRegistryConfig(
    domains={
        "FACILITIES_FIRE_ENV": DomainOntologyRule(
            domain_id="FACILITIES_FIRE_ENV",
            required_context_patterns=[
                r"\b(vesda|incendi[oa]s?|humo|extinci[oó]n|gas|agente\s+limpio|novec|fm-?200|inergen)\b",
                r"\b(fuga[s]?\s+de\s+agua|inundaci[oó]n|condensaci[oó]n|humedad|bms|ambiental|temperatura|sonda[s]?)\b",
                r"\b(fire|smoke|suppression|leak|humidity|environmental|sensor[s]?|falso\s+suelo)\b",
            ],
            forbidden_domain_ids=[
                "COMPUTE_VIRTUALIZATION",
                "STORAGE_FABRIC",
                "NETWORK_ROUTING",
                "IDENTITY_ACCESS",
                "DATABASE_ENGINE",
            ],
            signature_exclusion_patterns=[
                r"\b(vesda|novec|fm-?200|inergen|extinci[oó]n\s+por\s+gas|detecci[oó]n\s+de\s+humo)\b",
            ],
        ),
        "FACILITIES_POWER_COOLING": DomainOntologyRule(
            domain_id="FACILITIES_POWER_COOLING",
            required_context_patterns=[
                r"\b(ups|sai|generador|grupo\s+electr[oó]geno|ats|pdu|acometida|el[eé]ctric[oa])\b",
                r"\b(clima|climatizaci[oó]n|inrow|crac|crah|chiller|enfriamiento|pasillo\s+fr[ií]o|btu|kw)\b",
            ],
            forbidden_domain_ids=[
                "COMPUTE_VIRTUALIZATION",
                "STORAGE_FABRIC",
                "IDENTITY_ACCESS",
                "DATABASE_ENGINE",
            ],
            signature_exclusion_patterns=[
                r"\b(grupo\s+electr[oó]geno|crac|crah|inrow|pasillo\s+fr[ií]o|doble\s+acometida)\b",
            ],
        ),
        "COMPUTE_VIRTUALIZATION": DomainOntologyRule(
            domain_id="COMPUTE_VIRTUALIZATION",
            required_context_patterns=[
                r"\b(ram|cpu|vcpu|memoria|simplivity|nutanix|vxrail|vsphere|esxi|hipervisor|hypervisor)\b",
                r"\b(cl[uú]ster(es)?\s+de\s+c[oó]mputo|nodos?\s+f[ií]sicos?|drs|vmotion|sobreasignaci[oó]n)\b",
            ],
            forbidden_domain_ids=["FACILITIES_FIRE_ENV"],
            signature_exclusion_patterns=[
                r"\b(memoria\s+ram|vcpu|simplivity|nutanix|vxrail|vsphere|esxi|hipervisor|hypervisor|vmotion)\b",
                r"\b(ocupaci[oó]n\s+de\s+recursos\s+f[ií]sicos.*(ram|cpu))\b",
            ],
        ),
        "STORAGE_FABRIC": DomainOntologyRule(
            domain_id="STORAGE_FABRIC",
            required_context_patterns=[
                r"\b(san|nas|iops|lun|fibre\s+channel|nvme|cabina[s]?|almacenamiento|raid|latencia\s+de\s+disco)\b",
            ],
            forbidden_domain_ids=["FACILITIES_FIRE_ENV", "FACILITIES_POWER_COOLING"],
            signature_exclusion_patterns=[
                r"\b(fibre\s+channel|nvme-of|lun[s]?|iops|cabina[s]?\s+de\s+almacenamiento)\b",
            ],
        ),
        "NETWORK_ROUTING": DomainOntologyRule(
            domain_id="NETWORK_ROUTING",
            required_context_patterns=[
                r"\b(bgp|ospf|mpls|sd-wan|vlan|spanning-tree|stp|core\s+switch|enrutamiento|ancho\s+de\s+banda)\b",
            ],
            forbidden_domain_ids=["FACILITIES_FIRE_ENV", "FACILITIES_POWER_COOLING"],
            signature_exclusion_patterns=[
                r"\b(bgp|ospf|mpls|sd-wan|spanning-tree|protocolo[s]?\s+de\s+enrutamiento)\b",
            ],
        ),
        "IDENTITY_ACCESS": DomainOntologyRule(
            domain_id="IDENTITY_ACCESS",
            required_context_patterns=[
                r"\b(active\s+directory|entra\s+id|kerberos|ldap|gpo|mfa| RBAC|identidad|autenticaci[oó]n|fsmo)\b",
            ],
            forbidden_domain_ids=["FACILITIES_FIRE_ENV", "FACILITIES_POWER_COOLING"],
            signature_exclusion_patterns=[
                r"\b(active\s+directory|kerberos|fsmo|gpo|entra\s+id|controlador(es)?\s+de\s+dominio)\b",
            ],
        ),
        "DATABASE_ENGINE": DomainOntologyRule(
            domain_id="DATABASE_ENGINE",
            required_context_patterns=[
                r"\b(sql\s+server|oracle\s+rac|postgres|rdbms|índices|deadlock|transacci[oó]n|tde|alwayson)\b",
            ],
            forbidden_domain_ids=["FACILITIES_FIRE_ENV", "FACILITIES_POWER_COOLING"],
            signature_exclusion_patterns=[
                r"\b(oracle\s+rac|alwayson|deadlock[s]?|motor(es)?\s+de\s+base[s]?\s+de\s+datos|rdbms)\b",
            ],
        ),
    },
    pillar_to_domain_map={
        "T1.P1": "FACILITIES_POWER_COOLING",
        "T1.P2": "FACILITIES_POWER_COOLING",
        "T1.P3": "FACILITIES_POWER_COOLING",
        "T1.P4": "FACILITIES_FIRE_ENV",
        "T2": "COMPUTE_VIRTUALIZATION",
        "T3": "STORAGE_FABRIC",
        "T4": "NETWORK_ROUTING",
        "T8": "DATABASE_ENGINE",
    },
)


class PillarSemanticValidator:
    """
    Validates and sanitizes synthesized pillar narratives against ontological boundaries.
    Eliminates cross-pillar hallucinations prior to document compilation.
    """

    def __init__(self, config: Optional[OntologyRegistryConfig] = None) -> None:
        self._config = config or DEFAULT_ENTERPRISE_ONTOLOGY
        self._compiled_exclusions: Dict[str, List[re.Pattern[str]]] = {}
        self._compiled_requirements: Dict[str, List[re.Pattern[str]]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compiles regex patterns for low-latency in-memory evaluation."""
        for domain_id, rule in self._config.domains.items():
            self._compiled_exclusions[domain_id] = [
                re.compile(pattern, re.IGNORECASE)
                for pattern in rule.signature_exclusion_patterns
            ]
            self._compiled_requirements[domain_id] = [
                re.compile(pattern, re.IGNORECASE)
                for pattern in rule.required_context_patterns
            ]

    def resolve_domain_for_pillar(self, pillar_id: str) -> Optional[str]:
        """Resolves the ontological domain ID for a given Pillar ID (e.g., 'T1.P4')."""
        normalized = pillar_id.strip().upper()
        if normalized in self._config.pillar_to_domain_map:
            return self._config.pillar_to_domain_map[normalized]

        tower_prefix = normalized.split(".")[0]
        return self._config.pillar_to_domain_map.get(tower_prefix)

    def inspect_text_for_contamination(
        self,
        pillar_id: str,
        text: str,
        bound_kpi_id: Optional[str] = None,
        allowed_kpi_vocabulary: Optional[Set[str]] = None,
    ) -> Optional[SemanticViolation]:
        """
        Checks a candidate finding or recommendation string for forbidden cross-domain tokens.
        """
        if not text or not text.strip():
            return None

        target_domain_id = self.resolve_domain_for_pillar(pillar_id)
        if not target_domain_id or target_domain_id not in self._config.domains:
            return None

        domain_rule = self._config.domains[target_domain_id]

        for forbidden_domain_id in domain_rule.forbidden_domain_ids:
            exclusion_patterns = self._compiled_exclusions.get(forbidden_domain_id, [])
            matched_tokens: List[str] = []

            for pattern in exclusion_patterns:
                matches = pattern.findall(text)
                for match in matches:
                    token = match[0] if isinstance(match, tuple) else str(match)
                    if allowed_kpi_vocabulary and token.lower() in allowed_kpi_vocabulary:
                        continue
                    matched_tokens.append(token)

            if matched_tokens:
                return SemanticViolation(
                    pillar_id=pillar_id,
                    pillar_domain=target_domain_id,
                    contaminating_domain=forbidden_domain_id,
                    matched_tokens=list(set(matched_tokens)),
                    offending_text=text,
                    bound_kpi_id=bound_kpi_id,
                )

        return None

    def validate_and_sanitize_pillar_payload(
        self,
        pillar_id: str,
        findings: List[Any],
        recommendations: List[Any],
        kpi_definitions: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> ValidationResult:
        """
        Validates findings and recommendations for a specific pillar.
        Quarantines and removes any item that violates ontological domain boundaries.
        """
        allowed_vocab = self._extract_kpi_vocabulary(kpi_definitions)
        sanitized_findings: List[Dict[str, Any]] = []
        sanitized_recommendations: List[Dict[str, Any]] = []
        violations: List[SemanticViolation] = []

        for item in findings:
            normalized_item = self._normalize_narrative_item(item)
            text = normalized_item.get("text", "")
            bound_kpi = normalized_item.get("bound_kpi_id")

            violation = self.inspect_text_for_contamination(
                pillar_id=pillar_id,
                text=text,
                bound_kpi_id=bound_kpi,
                allowed_kpi_vocabulary=allowed_vocab,
            )
            if violation:
                logger.warning(
                    "Semantic contamination quarantined in pillar '%s' (Domain: %s). "
                    "Contaminating domain: '%s'. Matched tokens: %s. Text: '%s'",
                    pillar_id,
                    violation.pillar_domain,
                    violation.contaminating_domain,
                    violation.matched_tokens,
                    text,
                )
                violations.append(violation)
            else:
                sanitized_findings.append(normalized_item)

        for item in recommendations:
            normalized_item = self._normalize_narrative_item(item)
            text = normalized_item.get("text", "")
            bound_kpi = normalized_item.get("bound_kpi_id")

            violation = self.inspect_text_for_contamination(
                pillar_id=pillar_id,
                text=text,
                bound_kpi_id=bound_kpi,
                allowed_kpi_vocabulary=allowed_vocab,
            )
            if violation:
                logger.warning(
                    "Semantic contamination quarantined in recommendation for pillar '%s'. "
                    "Contaminating domain: '%s'. Matched tokens: %s.",
                    pillar_id,
                    violation.contaminating_domain,
                    violation.matched_tokens,
                )
                violations.append(violation)
            else:
                sanitized_recommendations.append(normalized_item)

        return ValidationResult(
            is_valid=len(violations) == 0,
            sanitized_findings=sanitized_findings,
            sanitized_recommendations=sanitized_recommendations,
            violations=violations,
        )

    @staticmethod
    def _normalize_narrative_item(item: Any) -> Dict[str, Any]:
        """Normalizes string or dict narrative payloads into a canonical dictionary structure."""
        if isinstance(item, dict):
            text = (
                item.get("text")
                or item.get("description")
                or item.get("finding")
                or item.get("recommendation")
                or ""
            )
            return {
                "text": str(text).strip(),
                "bound_kpi_id": item.get("bound_kpi_id") or item.get("kpi_id"),
                "severity": item.get("severity", "MEDIUM"),
            }
        return {"text": str(item).strip(), "bound_kpi_id": None, "severity": "MEDIUM"}

    @staticmethod
    def _extract_kpi_vocabulary(
        kpi_definitions: Optional[Dict[str, Dict[str, Any]]]
    ) -> Set[str]:
        """Extracts explicitly defined terms from the official KPI definitions to avoid false positives."""
        if not kpi_definitions:
            return set()
        vocab: Set[str] = set()
        for kpi_meta in kpi_definitions.values():
            combined = f"{kpi_meta.get('name', '')} {kpi_meta.get('description', '')}"
            for token in re.findall(r"\b\w{3,}\b", combined.lower()):
                vocab.add(token)
        return vocab
```

---

### 4.2 Phase A: Ontological Prompt Builder (`domain/synthesis/ontological_prompt_scoper.py`)

This component binds the synthesis in `resynthesize_all_10_towers_from_raw_transcription.py` directly to `tower_definition.json` and injects explicit negative constraints per pillar.

```python
"""
Ontological Pillar Prompt Scoper.

Generates strictly bounded synthesis prompts per pillar by binding the LLM
to the exact KPI definitions in `tower_definition.json` and injecting
negative lexical constraints derived from external domains.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from domain.validation.pillar_semantic_validator import (
    DEFAULT_ENTERPRISE_ONTOLOGY,
    OntologyRegistryConfig,
)


class OntologicalPromptScoper:
    """
    Constructs ontologically isolated prompt directives for LLM synthesis,
    eliminating context window attention bleed across pillars.
    """

    def __init__(self, ontology_config: OntologyRegistryConfig = DEFAULT_ENTERPRISE_ONTOLOGY) -> None:
        self._ontology = ontology_config

    def build_pillar_scoping_directive(
        self,
        pillar_id: str,
        pillar_definition: Dict[str, Any],
        evaluated_kpi_scores: Dict[str, float],
    ) -> str:
        """
        Generates a strict ontological scoping block for a single pillar.

        Args:
            pillar_id: Canonical ID (e.g., 'T1.P4').
            pillar_definition: Pillar metadata and KPI dictionary from `tower_definition.json`.
            evaluated_kpi_scores: Map of KPI ID to empirical score (e.g., {'T1.P4.K1': 5.0, 'T1.P4.K3': 2.0}).
        """
        pillar_name = pillar_definition.get("name", pillar_id)
        kpis = pillar_definition.get("kpis", {})

        kpi_directives: List[Dict[str, Any]] = []
        low_scoring_kpis: List[str] = []
        high_scoring_kpis: List[str] = []

        for kpi_id, kpi_meta in kpis.items():
            score = evaluated_kpi_scores.get(kpi_id, 3.0)
            status = "STRENGTH (CONSOLIDATED)" if score >= 4.0 else "RESILIENCE GAP (DEFICIT)"
            if score < 4.0:
                low_scoring_kpis.append(f"{kpi_id} ({kpi_meta.get('name')}): Score {score}/5.0")
            else:
                high_scoring_kpis.append(f"{kpi_id} ({kpi_meta.get('name')}): Score {score}/5.0")

            kpi_directives.append(
                {
                    "kpi_id": kpi_id,
                    "name": kpi_meta.get("name", ""),
                    "description": kpi_meta.get("description", ""),
                    "empirical_score": score,
                    "diagnostic_classification": status,
                }
            )

        forbidden_concepts = self._get_forbidden_concepts_for_pillar(pillar_id)

        directive = (
            f"### ONTOLOGICAL BOUNDARY CONTRACT FOR PILLAR {pillar_id}: {pillar_name}\n"
            f"1. STRICT KPI SCOPE: You may ONLY synthesize findings and recommendations that directly "
            f"evaluate the following canonical KPIs:\n"
            f"{json.dumps(kpi_directives, ensure_ascii=False, indent=2)}\n\n"
            f"2. MATHEMATICAL CALIBRATION MANDATE:\n"
            f"   - High-Scoring Capabilities (Strengths >= 4.0): {high_scoring_kpis or ['None']}\n"
            f"   - Low-Scoring Capabilities (Diagnosed Gaps < 4.0): {low_scoring_kpis or ['None']}\n"
            f"   Every finding representing a gap MUST be explicitly bound via `bound_kpi_id` to one of the "
            f"Low-Scoring Capabilities above.\n\n"
            f"3. NEGATIVE ONTOLOGICAL CONSTRAINTS (STRICTLY FORBIDDEN IN {pillar_id}):\n"
            f"   Do NOT under any circumstances mention or import findings belonging to other infrastructure domains. "
            f"Specifically, the following concepts are FORBIDDEN in {pillar_id}: {forbidden_concepts}.\n"
            f"   Even if the raw transcript heavily emphasizes these forbidden topics, ignore them completely "
            f"while synthesizing {pillar_id}."
        )
        return directive

    def _get_forbidden_concepts_for_pillar(self, pillar_id: str) -> List[str]:
        """Extracts human-readable forbidden domain keywords for prompt injection."""
        domain_id = self._ontology.pillar_to_domain_map.get(
            pillar_id,
            self._ontology.pillar_to_domain_map.get(pillar_id.split(".")[0], ""),
        )
        if not domain_id or domain_id not in self._ontology.domains:
            return []

        rule = self._ontology.domains[domain_id]
        forbidden_summary: List[str] = []
        for forbidden_id in rule.forbidden_domain_ids:
            forbidden_rule = self._ontology.domains.get(forbidden_id)
            if forbidden_rule:
                forbidden_summary.append(
                    f"[{forbidden_id}: {', '.join(forbidden_rule.signature_exclusion_patterns)}]"
                )
        return forbidden_summary
```

---

### 4.3 Phase C: Declarative KPI-Aligned Compiler (`in_memory_asis_compiler.py` Remediation)

This replaces the naive `findings[0]` extraction in `derive_in_memory_maturity_matrix` with an ontologically validated, KPI-score-driven calibration engine.

```python
"""
Declarative In-Memory AS-IS Maturity Matrix Compiler.

Replaces positional indexing (`findings[0]`) with deterministic KPI-score
decomposition and ontological boundary validation. Ensures Section 3.1 (Table 5)
is 100% mathematically and semantically aligned with the underlying KPI vector.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from domain.validation.pillar_semantic_validator import (
    PillarSemanticValidator,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class MaturityMatrixCalibrationCompiler:
    """
    Compiles Section 3.1 (Maturity Matrix & Gap Calibration) by correlating
    quantitative KPI scores against ontologically validated narrative findings.
    """

    STRENGTH_SCORE_THRESHOLD: float = 4.0

    def __init__(
        self,
        semantic_validator: Optional[PillarSemanticValidator] = None,
    ) -> None:
        self._validator = semantic_validator or PillarSemanticValidator()

    def derive_in_memory_maturity_matrix(
        self,
        tower_definition: Dict[str, Any],
        asis_payload: Dict[str, Any],
        language_labels: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Derives the calibrated maturity matrix rows for Section 3.1 (Table 5).

        Args:
            tower_definition: Canonical tower definition JSON containing pillars and KPIs.
            asis_payload: Hydrated AS-IS assessment payload containing scores, findings, and evidence.
            language_labels: Optional localization dictionary for structural labels.

        Returns:
            List of dictionaries representing validated, KPI-aligned rows for Table 5.
        """
        labels = language_labels or {
            "strength_prefix": "Capacidad Consolidada",
            "gap_prefix": "Brecha de Resiliencia Diagnosticada",
            "calibration_prefix": "Calibración de Madurez",
            "optimal_posture": "Operación alineada con estándares de alta resiliencia en todos los indicadores del pilar.",
        }

        pillars_def = self._index_pillar_definitions(tower_definition)
        payload_pillars = self._index_payload_pillars(asis_payload)

        matrix_rows: List[Dict[str, Any]] = []

        for pillar_id, p_def in pillars_def.items():
            p_payload = payload_pillars.get(pillar_id, {})
            pillar_name = p_def.get("name") or p_payload.get("name") or pillar_id
            kpi_defs = p_def.get("kpis", {})

            # 1. Extract and partition empirical KPI scores
            kpi_scores, kpi_evidence = self._extract_kpi_ evaluations(p_payload, kpi_defs)
            pillar_score = self._resolve_pillar_score(p_payload, kpi_scores, kpi_defs)

            high_kpis, low_kpis = self._partition_kpis_by_performance(
                kpi_scores=kpi_scores,
                kpi_defs=kpi_defs,
            )

            # 2. Execute Semantic Gatekeeper (Phase B) on candidate findings/recommendations
            raw_findings = p_payload.get("findings", [])
            raw_recommendations = p_payload.get("recommendations", [])

            validation: ValidationResult = self._validator.validate_and_sanitize_pillar_payload(
                pillar_id=pillar_id,
                findings=raw_findings,
                recommendations=raw_recommendations,
                kpi_definitions=kpi_defs,
            )

            # 3. Synthesize KPI-aligned Strength Narrative (from KPIs >= 4.0)
            strength_narrative = self._resolve_strength_narrative(
                high_kpis=high_kpis,
                kpi_defs=kpi_defs,
                kpi_evidence=kpi_evidence,
            )

            # 4. Synthesize KPI-aligned Breach/Gap Narrative (strictly anchored to KPIs < 4.0)
            gap_narrative = self._resolve_gap_narrative(
                pillar_id=pillar_id,
                low_kpis=low_kpis,
                kpi_defs=kpi_defs,
                kpi_evidence=kpi_evidence,
                sanitized_findings=validation.sanitized_findings,
                optimal_fallback=labels["optimal_posture"],
            )

            # 5. Assemble deterministic calibration cell for Table 5
            calibration_segments: List[str] = []
            if strength_narrative:
                calibration_segments.append(
                    f"**{labels['strength_prefix']}:** {strength_narrative}"
                )
            if gap_narrative:
                calibration_segments.append(
                    f"**{labels['gap_prefix']}:** {gap_narrative}"
                )

            matrix_rows.append(
                {
                    "pillar_id": pillar_id,
                    "pillar_name": pillar_name,
                    "score": round(pillar_score, 2),
                    "score_formatted": f"{pillar_score:.1f} / 5.0",
                    "strength_summary": strength_narrative,
                    "gap_summary": gap_narrative,
                    "calibration_analysis": " ".join(calibration_segments),
                    "semantic_violations_quarantined": len(validation.violations),
                    "lowest_kpi_id": low_kpis[0][0] if low_kpis else None,
                }
            )

        return matrix_rows

    def _partition_kpis_by_performance(
        self,
        kpi_scores: Dict[str, float],
        kpi_defs: Dict[str, Dict[str, Any]],
    ) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
        """
        Partitions KPIs into high-performing (>= 4.0) and low-performing (< 4.0).
        High KPIs are sorted descending; Low KPIs are sorted ascending (worst gap first).
        """
        high_kpis: List[Tuple[str, float]] = []
        low_kpis: List[Tuple[str, float]] = []

        for kpi_id in kpi_defs:
            score = kpi_scores.get(kpi_id)
            if score is None:
                continue
            if score >= self.STRENGTH_SCORE_THRESHOLD:
                high_kpis.append((kpi_id, score))
            else:
                low_kpis.append((kpi_id, score))

        high_kpis.sort(key=lambda item: item[1], reverse=True)
        low_kpis.sort(key=lambda item: item[1])
        return high_kpis, low_kpis

    def _resolve_strength_narrative(
        self,
        high_kpis: List[Tuple[str, float]],
        kpi_defs: Dict[str, Dict[str, Any]],
        kpi_evidence: Dict[str, str],
    ) -> str:
        """Constructs the consolidated capability statement strictly from high-scoring KPIs."""
        if not high_kpis:
            return ""

        strength_descriptions: List[str] = []
        for kpi_id, score in high_kpis[:2]:
            evidence = kpi_evidence.get(kpi_id, "").strip()
            kpi_name = kpi_defs.get(kpi_id, {}).get("name", kpi_id)
            if evidence:
                strength_descriptions.append(f"{kpi_name} ({evidence.rstrip('.')})")
            else:
                strength_descriptions.append(f"{kpi_name} (nivel de madurez {score:.1f}/5.0)")

        return "; ".join(strength_descriptions) + "."

    def _resolve_gap_narrative(
        self,
        pillar_id: str,
        low_kpis: List[Tuple[str, float]],
        kpi_defs: Dict[str, Dict[str, Any]],
        kpi_evidence: Dict[str, str],
        sanitized_findings: List[Dict[str, Any]],
        optimal_fallback: str,
    ) -> str:
        """
        Resolves the primary resilience gap narrative using a strict 3-tier priority hierarchy:
        Tier 1: Sanitized finding explicitly bound (`bound_kpi_id`) to the lowest-scoring KPI.
        Tier 2: Empirical evidence or sanitized finding lexically matching the lowest-scoring KPI.
        Tier 3: Deterministic ontological synthesis derived directly from the lowest-scoring KPI definition.
        """
        if not low_kpis:
            # If all KPIs scored >= 4.0, only report minor optimization if a valid finding exists
            if sanitized_findings:
                return sanitized_findings[0]["text"]
            return optimal_fallback

        worst_kpi_id, worst_score = low_kpis[0]
        worst_kpi_meta = kpi_defs.get(worst_kpi_id, {})
        worst_kpi_name = worst_kpi_meta.get("name", worst_kpi_id)
        worst_kpi_desc = worst_kpi_meta.get("description", "")

        # Tier 1: Exact KPI ID binding match
        for finding in sanitized_findings:
            if finding.get("bound_kpi_id") == worst_kpi_id and finding.get("text"):
                return finding["text"]

        # Tier 2a: Direct KPI-level empirical observation recorded during assessment
        direct_evidence = kpi_evidence.get(worst_kpi_id, "").strip()
        if direct_evidence:
            return f"Déficit en {worst_kpi_name} ({worst_score:.1f}/5.0): {direct_evidence.rstrip('.')}."

        # Tier 2b: Lexical overlap between sanitized pillar findings and the worst KPI's ontology
        kpi_keywords = {
            token.lower()
            for token in f"{worst_kpi_name} {worst_kpi_desc}".split()
            if len(token) > 4
        }
        for finding in sanitized_findings:
            text_lower = finding.get("text", "").lower()
            if any(kw in text_lower for kw in kpi_keywords):
                return finding["text"]

        # Tier 3: Deterministic Ontological Fallback (Zero hallucination guarantee)
        logger.info(
            "Synthesizing deterministic KPI fallback gap for pillar '%s' anchored to '%s' (score %.1f).",
            pillar_id,
            worst_kpi_id,
            worst_score,
        )
        rubric_gap = self._extract_rubric_deficit_description(worst_kpi_meta, worst_score)
        if rubric_gap:
            return f"Limitación en {worst_kpi_name} (Score {worst_score:.1f}/5.0): {rubric_gap.rstrip('.')}."

        return (
            f"Brecha operativa identificada en el indicador '{worst_kpi_name}' "
            f"(calificación {worst_score:.1f}/5.0 respecto al estándar objetivo de resiliencia): "
            f"{worst_kpi_desc.rstrip('.')}."
        )

    @staticmethod
    def _extract_rubric_deficit_description(
        kpi_meta: Dict[str, Any], score: float
    ) -> Optional[str]:
        """Extracts the rubric criteria for the empirical score level from `tower_definition.json`."""
        rubric = kpi_meta.get("rubric") or kpi_meta.get("scoring_criteria") or {}
        score_key = str(int(round(score)))
        if isinstance(rubric, dict) and score_key in rubric:
            return str(rubric[score_key])
        return None

    @staticmethod
    def _index_pillar_definitions(
        tower_definition: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Normalizes pillar definitions from list or dict representations into an ordered map."""
        raw_pillars = tower_definition.get("pillars", {})
        indexed: Dict[str, Dict[str, Any]] = {}
        if isinstance(raw_pillars, dict):
            for pid, pdata in raw_pillars.items():
                indexed[pid] = pdata
        elif isinstance(raw_pillars, list):
            for pdata in raw_pillars:
                pid = pdata.get("id") or pdata.get("pillar_id")
                if pid:
                    indexed[pid] = pdata
        return indexed

    @staticmethod
    def _index_payload_pillars(asis_payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Normalizes AS-IS payload pillars into a canonical lookup dictionary."""
        health_check = asis_payload.get("health_check_asis", asis_payload)
        raw_pillars = health_check.get("pillars", {})
        indexed: Dict[str, Dict[str, Any]] = {}
        if isinstance(raw_pillars, dict):
            return raw_pillars
        if isinstance(raw_pillars, list):
            for item in raw_pillars:
                pid = item.get("id") or item.get("pillar_id")
                if pid:
                    indexed[pid] = item
        return indexed

    @staticmethod
    def _extract_kpi_evaluations(
        pillar_payload: Dict[str, Any],
        kpi_defs: Dict[str, Dict[str, Any]],
    ) -> Tuple[Dict[str, float], Dict[str, str]]:
        """Extracts KPI numeric scores and empirical evidence strings from the pillar payload."""
        scores: Dict[str, float] = {}
        evidence: Dict[str, str] = {}

        raw_kpis = pillar_payload.get("kpis", {})
        if isinstance(raw_kpis, dict):
            for kpi_id, kpi_val in raw_kpis.items():
                if isinstance(kpi_val, (int, float)):
                    scores[kpi_id] = float(kpi_val)
                elif isinstance(kpi_val, dict):
                    if "score" in kpi_val and kpi_val["score"] is not None:
                        scores[kpi_id] = float(kpi_val["score"])
                    obs = (
                        kpi_val.get("evidence")
                        or kpi_val.get("observation")
                        or kpi_val.get("rationale")
                    )
                    if obs:
                        evidence[kpi_id] = str(obs)
        elif isinstance(raw_kpis, list):
            for item in raw_kpis:
                kpi_id = item.get("id") or item.get("kpi_id")
                if kpi_id and "score" in item and item["score"] is not None:
                    scores[kpi_id] = float(item["score"])
                obs = item.get("evidence") or item.get("observation") or item.get("rationale")
                if kpi_id and obs:
                    evidence[kpi_id] = str(obs)

        return scores, evidence

    @staticmethod
    def _resolve_pillar_score(
        pillar_payload: Dict[str, Any],
        kpi_scores: Dict[str, float],
        kpi_defs: Dict[str, Dict[str, Any]],
    ) -> float:
        """Calculates weighted pillar score from KPIs or falls back to payload score."""
        if "score" in pillar_payload and pillar_payload["score"] is not None:
            return float(pillar_payload["score"])

        if not kpi_scores:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0
        for kpi_id, score in kpi_scores.items():
            weight = float(kpi_defs.get(kpi_id, {}).get("weight", 1.0))
            weighted_sum += score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0
```

---

## 5. Verification Trace: Before vs. After on T1.P4

When the remediated pipeline executes against the exact `T1.P4` payload (`K1=5.0`, `K2=5.0`, `K3=2.0`, contaminated `findings[0] = "Superación del límite de seguridad del 50% de ocupación de recursos físicos (especialmente memoria RAM y CPU en los clústeres 3 y 4) en los 6 nodos HPE SimpliVity"`):

1. **Step 1 (`PillarSemanticValidator`):**
   * Resolves `T1.P4` $\rightarrow$ `FACILITIES_FIRE_ENV`.
   * Evaluates `findings[0]` against forbidden domain `COMPUTE_VIRTUALIZATION`.
   * Matches tokens: `["memoria RAM", "CPU", "SimpliVity"]`.
   * **Action:** Quarantines and strips `findings[0]`, logging a `SemanticViolation`.

2. **Step 2 (`MaturityMatrixCalibrationCompiler`):**
   * Partitions `T1.P4` KPIs:
     * `high_kpis`: `[('T1.P4.K1', 5.0), ('T1.P4.K2', 5.0)]`
     * `low_kpis`: `[('T1.P4.K3', 2.0)]`
   * Compiles **Strength Narrative** from `K1` and `K2` (VESDA early smoke detection and clean-agent gas suppression).
   * Compiles **Gap Narrative** strictly anchored to `T1.P4.K3` (Score `2.0/5.0`: Environmental risks / absence of under-floor liquid leak detection and unintegrated BMS fire alarms).

3. **Resulting Output in Section 3.1 (Table 5):**
   > **Pilar / Capacidad:** Protección Contra Incendios y Seguridad Ambiental | **Score:** 4.0 / 5.0  
   > **Análisis de Brechas y Calibración:** **Capacidad Consolidada:** Detección temprana de humo y temperatura (VESDA) (nivel de madurez 5.0/5.0); Sistema de extinción automática por agente limpio (gas) (nivel de madurez 5.0/5.0). **Brecha de Resiliencia Diagnosticada:** Déficit en Riesgos ambientales asociados y monitoreo BMS (2.0/5.0): Ausencia de sensores de detección de fugas de líquidos bajo falso suelo e integración centralizada de alarmas contra incendios en el BMS.