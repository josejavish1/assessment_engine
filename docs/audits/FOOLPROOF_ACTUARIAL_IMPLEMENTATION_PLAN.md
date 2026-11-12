# DEFINITIVE EXECUTION PLAN: UNIVERSAL ACTUARIAL ENGINE REMEDIATION
**Document ID:** `EXEC-PLAN-SR117-2026-V1`  
**Author:** `gemini-4-argon` (Lead Adversarial Red Team Chief Architect — SR 11-7 / Open FAIR / Basel III / Solvency II)  
**Reference Architecture:** `docs/audits/RED_TEAM_UNIVERSAL_ACTUARIAL_MASTER_PLAN.md`  
**Enforcement Posture:** **FAIL-CLOSED / ZERO WORKAROUNDS / DETERMINISTIC AUDITABILITY**

---

## 1. ARCHITECTURAL MANDATE & INVARIANTS

To achieve strict compliance with Federal Reserve SR 11-7 (Model Risk Management), Basel III AMA/SMA operational risk standards, and Open FAIR taxonomy, the engine must be purged of all uncalibrated heuristics, silent fallbacks, and hardcoded constants.

1. **Zero Silent Fallbacks:** Missing topological metadata (`environment_tier`, `architectural_role`) or unmapped threat parameters must raise a fatal `ActuarialContractViolationError` during ingestion or pre-flight validation.
2. **Purge of Blind Defaults:** All instances of `default_rto_hours = 8.0`, static blast radiuses, and unconditional regulatory fine triggers are permanently excised from `src/`.
3. **Deterministic Enrichment:** Where raw client ingestion payloads lack explicit tags, a deterministic, rule-based `TopologyEnricher` resolves the attributes prior to Pydantic model instantiation and records an immutable cryptographic provenance log (`EnrichmentAuditEntry`). If deterministic resolution fails, ingestion halts.
4. **Universal Vertical Agnosticism:** All actuarial equations operate exclusively on abstract topological and operational physics (`MTTR`, `Buffer_Capacity`, `Environment_Weight`, `Blast_Radius_Graph`), ensuring mathematical validity across Healthcare, Financial Services, Industrial Manufacturing, and SaaS.

---

## 2. PHASED EXECUTION BREAKDOWN

### PHASE 1: Fail-Closed Schema Enforcement & Deterministic Ingestion Enricher
**Objective:** Establish strict Pydantic V2 data contracts and deterministic pre-ingestion topological classification.

*   **Target Files:**
    *   `src/assessment_engine/schemas/actuarial_contracts.py` *(New)*
    *   `src/assessment_engine/ingestion/topology_enricher.py` *(New)*
    *   `src/assessment_engine/core/exceptions.py` *(Modify)*
    *   `engine_config/topology_classification_rules.yaml` *(New)*
*   **Actions:**
    1. Define strict enumerations: `EnvironmentTier` (`PROD_CRITICAL`, `PROD_SUPPORT`, `STAGING_UAT`, `LAB_DEV_TEST`) and `ArchitecturalRole` (`CONTROL_PLANE`, `DATA_PLANE`, `MANAGEMENT_PLANE`, `TELEMETRY_LOGGING`, `STANDALONE_ENDPOINT`).
    2. Define `ThreatVectorPhysics` schema requiring explicit `causal_nature` (`MALICIOUS_EXFILTRATION`, `DESTRUCTIVE_SABOTAGE`, `ACCIDENTAL_PHYSICAL_SEVERANCE`, `RESOURCE_EXHAUSTION`, `CONFIGURATION_DRIFT`) and `base_mttr_distribution` (PERT parameters: `min_hours`, `mode_hours`, `max_hours`).
    3. Implement `TopologyEnricher` to evaluate asset metadata against `engine_config/topology_classification_rules.yaml`. Every inferred tag generates a mandatory `EnrichmentAuditEntry` (`asset_id`, `inferred_field`, `assigned_value`, `rule_id`, `confidence=1.0`, `sha256_rule_hash`).
    4. Remove all default values from asset and scenario Pydantic models. Any `None` or unmapped enum value raises `ActuarialContractViolationError`.

### PHASE 2: Layer 1 — Threat-Specific MTTR & Continuous Beta Buffer Attenuation
**Objective:** Eradicate the 8.0-hour outage distortion on fast-recovery/buffered events (e.g., T4-RVS02 / T10-RVS04 15-minute disk cleanup).

*   **Target Files:**
    *   `src/assessment_engine/actuarial/temporal_physics.py` *(New)*
    *   `src/assessment_engine/actuarial/loss_calculator.py` *(Modify)*
    *   `engine_config/threat_physics_catalog.yaml` *(New)*
*   **Actions:**
    1. Delete `default_rto_hours = 8.0` and all related fallback kwargs across `src/assessment_engine/`.
    2. Populate `engine_config/threat_physics_catalog.yaml` with PERT recovery distributions and operational buffer tolerances ($\tau_{\text{buffer}}$) per threat capability card.
    3. Implement the Continuous Beta Buffer Attenuation function in `temporal_physics.py` to compute Effective Business Interruption Duration ($T_{\text{eff}}$) from raw technical restoration time ($T_{\text{tech}}$) and architectural decoupling buffer ($\tau_{\text{buffer}}$).

### PHASE 3: Layer 2 — Bow-Tie Control-Plane Escalation & Topological Blast Radius
**Objective:** Resolve the Control-Plane underestimation (T6-RVS02 PAM 3k EUR vs 198k EUR) and Lab overestimation (T2-RVS03/04 K8s Lab 74k EUR vs 0 EUR revenue loss).

*   **Target Files:**
    *   `src/assessment_engine/actuarial/bowtie_escalation.py` *(New)*
    *   `src/assessment_engine/actuarial/environment_scalars.py` *(New)*
    *   `engine_config/actuarial_scalars.yaml` *(Modify)*
*   **Actions:**
    1. Implement `EnvironmentTier` loss component multipliers in `engine_config/actuarial_scalars.yaml`. Explicitly enforce $\omega_{\text{rev}}(\text{LAB\_DEV\_TEST}) = 0.0$ and $\omega_{\text{SLA}}(\text{LAB\_DEV\_TEST}) = 0.0$, restricting Lab losses strictly to direct IT reconstitution labor ($C_{\text{reconst}}$).
    2. Implement the Bow-Tie Graph Escalation algorithm in `bowtie_escalation.py`. When an asset with `ArchitecturalRole == CONTROL_PLANE` (e.g., PAM, Active Directory, IAM Root) experiences a `MALICIOUS_EXFILTRATION` or `DESTRUCTIVE_SABOTAGE` event, its blast radius automatically traverses downstream dependent `DATA_PLANE` nodes within the same or lower security boundary.

### PHASE 4: Layer 3 — Causal Regulatory Gating (Legal & Statutory Physics)
**Objective:** Eliminate spurious regulatory fines on non-breach physical/availability events (e.g., T3-RVS04 backhoe fiber cut triggering GDPR Art. 83 fines).

*   **Target Files:**
    *   `src/assessment_engine/actuarial/regulatory_gating.py` *(New)*
    *   `src/assessment_engine/actuarial/loss_calculator.py` *(Modify)*
*   **Actions:**
    1. Implement a strict Boolean/Probabilistic Causal Gate for statutory penalties (GDPR, HIPAA, PCI-DSS, NIS2/DORA).
    2. Enforce that Data Protection Fines (e.g., GDPR Art. 83) require `causal_nature == MALICIOUS_EXFILTRATION` **AND** `data_classification in {PII, PHI, PCI, MNPI}`.
    3. Physical severance (`ACCIDENTAL_PHYSICAL_SEVERANCE`) or pure resource exhaustion (`RESOURCE_EXHAUSTION`) without confidentiality compromise yields exactly $0.00\text{ EUR}$ in data privacy fines, routing secondary losses exclusively to contractual SLA penalties if $T_{\text{eff}} > \text{SLA}_{\text{threshold}}$.

### PHASE 5: Pipeline Integration & Word Annex Contiguity Verification
**Objective:** Wire the 3-Layer engine into the reporting pipeline and verify zero structural or formatting regressions in generated Word annexes.

*   **Target Files:**
    *   `src/assessment_engine/pipeline/orchestrator.py` *(Modify)*
    *   `src/assessment_engine/reporting/word_annex_generator.py` *(Modify)*
*   **Actions:**
    1. Inject `TopologyEnricher` at Stage 0 of `orchestrator.py`. Persist the `EnrichmentAuditLog` into the assessment output bundle.
    2. Update capability card rendering in `word_annex_generator.py` to display decomposed loss drivers (`Direct Reconstitution`, `Buffered Business Interruption`, `Bow-Tie Cascaded Impact`, `Statutory/Regulatory Penalties`) while preserving exact table indices, styles, and contiguous bookmark structures.

---

## 3. FAIL-CLOSED SCHEMA & ENRICHER IMPLEMENTATION SPECIFICATIONS

### 3.1 Strict Data Contracts (`src/assessment_engine/schemas/actuarial_contracts.py`)

```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from src.assessment_engine.core.exceptions import ActuarialContractViolationError

class EnvironmentTier(str, Enum):
    PROD_CRITICAL = "PROD_CRITICAL"
    PROD_SUPPORT = "PROD_SUPPORT"
    STAGING_UAT = "STAGING_UAT"
    LAB_DEV_TEST = "LAB_DEV_TEST"

class ArchitecturalRole(str, Enum):
    CONTROL_PLANE = "CONTROL_PLANE"
    DATA_PLANE = "DATA_PLANE"
    MANAGEMENT_PLANE = "MANAGEMENT_PLANE"
    TELEMETRY_LOGGING = "TELEMETRY_LOGGING"
    STANDALONE_ENDPOINT = "STANDALONE_ENDPOINT"

class CausalNature(str, Enum):
    MALICIOUS_EXFILTRATION = "MALICIOUS_EXFILTRATION"
    DESTRUCTIVE_SABOTAGE = "DESTRUCTIVE_SABOTAGE"
    ACCIDENTAL_PHYSICAL_SEVERANCE = "ACCIDENTAL_PHYSICAL_SEVERANCE"
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
    CONFIGURATION_DRIFT = "CONFIGURATION_DRIFT"

class PERTDistributionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    min_hours: float = Field(..., gt=0.0)
    mode_hours: float = Field(..., gt=0.0)
    max_hours: float = Field(..., gt=0.0)
    gamma: float = Field(default=4.0, ge=1.0, le=10.0)

    @model_validator(mode="after")
    def validate_pert_ordering(self) -> "PERTDistributionSpec":
        if not (self.min_hours <= self.mode_hours <= self.max_hours):
            raise ActuarialContractViolationError(
                f"Invalid PERT ordering: min ({self.min_hours}) <= mode ({self.mode_hours}) <= max ({self.max_hours}) violated."
            )
        return self

class AssetActuarialProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    asset_id: str = Field(..., min_length=1)
    environment_tier: EnvironmentTier
    architectural_role: ArchitecturalRole
    hourly_revenue_at_risk_eur: float = Field(..., ge=0.0)
    buffer_capacity_hours: float = Field(..., ge=0.0)
    dependent_asset_ids: List[str] = Field(default_factory=list)
    holds_regulated_data: bool
    reconstitution_hourly_rate_eur: float = Field(..., gt=0.0)
```

### 3.2 Deterministic Enricher (`src/assessment_engine/ingestion/topology_enricher.py`)

```python
import hashlib
import json
from dataclasses import dataclass
from typing import Dict, Any, Tuple, List
from src.assessment_engine.core.exceptions import ActuarialContractViolationError

@dataclass(frozen=True)
class EnrichmentAuditEntry:
    asset_id: str
    field_name: str
    resolved_value: str
    matched_rule_id: str
    rule_definition_sha256: str

class TopologyEnricher:
    """
    Deterministic, fail-closed pre-ingestion enricher.
    Zero probabilistic guessing. Zero silent default fallbacks.
    """
    def __init__(self, rules_config: Dict[str, Any]) -> None:
        if not rules_config or "rules" not in rules_config:
            raise ActuarialContractViolationError("TopologyEnricher initialized with empty or invalid ruleset.")
        self._rules = rules_config["rules"]

    def enrich_and_validate(self, raw_asset: Dict[str, Any]) -> Tuple[Dict[str, Any], List[EnrichmentAuditEntry]]:
        asset_id = raw_asset.get("asset_id")
        if not asset_id:
            raise ActuarialContractViolationError("Ingestion halted: Asset payload missing mandatory 'asset_id'.")

        enriched = dict(raw_asset)
        audit_trail: List[EnrichmentAuditEntry] = []

        for required_field in ("environment_tier", "architectural_role"):
            if enriched.get(required_field) is None:
                resolved_val, rule_id, rule_hash = self._resolve_field_deterministically(enriched, required_field)
                enriched[required_field] = resolved_val
                audit_trail.append(
                    EnrichmentAuditEntry(
                        asset_id=asset_id,
                        field_name=required_field,
                        resolved_value=resolved_val,
                        matched_rule_id=rule_id,
                        rule_definition_sha256=rule_hash,
                    )
                )

        return enriched, audit_trail

    def _resolve_field_deterministically(self, asset: Dict[str, Any], target_field: str) -> Tuple[str, str, str]:
        field_rules = self._rules.get(target_field, [])
        matches = []

        for rule in field_rules:
            if self._matches_criteria(asset, rule["criteria"]):
                rule_hash = hashlib.sha256(json.dumps(rule, sort_keys=True).encode("utf-8")).hexdigest()
                matches.append((rule["assign_value"], rule["rule_id"], rule_hash))

        if len(matches) == 0:
            raise ActuarialContractViolationError(
                f"FAIL-CLOSED: Cannot deterministically resolve '{target_field}' for asset '{asset.get('asset_id')}'. "
                f"No classification rules matched. Explicit tagging required."
            )
        if len(matches) > 1:
            matched_ids = [m[1] for m in matches]
            raise ActuarialContractViolationError(
                f"FAIL-CLOSED: Ambiguous topology resolution for '{target_field}' on asset '{asset.get('asset_id')}'. "
                f"Conflicting rules matched: {matched_ids}."
            )

        return matches[0]

    @staticmethod
    def _matches_criteria(asset: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        for key, expected_patterns in criteria.items():
            actual_val = str(asset.get(key, "")).upper()
            if not any(pattern.upper() in actual_val for pattern in expected_patterns):
                return False
        return True
```

---

## 4. MATHEMATICAL SPECIFICATION OF THE 3-LAYER ENGINE

### 4.1 Continuous Beta Buffer Attenuation (`temporal_physics.py`)

To prevent short maintenance or disk-cleanup events ($T_{\text{tech}} = 0.25\text{ hours}$) from triggering catastrophic business interruption losses while avoiding discontinuous step-function cliffs at $T_{\text{tech}} = \tau_{\text{buffer}}$, the engine implements a smooth second-order attenuation curve:

Let $T_{\text{tech}} \sim \text{PERT}(t_{\min}, t_{\text{mode}}, t_{\max}, \gamma)$ be the simulated technical restoration duration for trial $k$, and let $\tau_{\text{buffer}} \ge 0$ be the asset's operational decoupling buffer (e.g., local queue depth, active-passive failover window, or disk quota grace period).

The **Effective Business Interruption Duration** $T_{\text{eff}}$ is defined continuously as:

$$T_{\text{eff}}(T_{\text{tech}}, \tau_{\text{buffer}}) = \begin{cases} T_{\text{tech}} & \text{if } \tau_{\text{buffer}} = 0 \\[8pt] 0 & \text{if } T_{\text{tech}} \le \tau_{\text{buffer}} \cdot (1 - \delta) \\[8pt] \left( T_{\text{tech}} - \tau_{\text{buffer}} \right) \cdot \left( \frac{T_{\text{tech}}}{T_{\text{tech}} + \tau_{\text{buffer}}} \right)^{\beta} & \text{if } T_{\text{tech}} > \tau_{\text{buffer}} \end{cases}$$

Where $\beta \ge 1.0$ is the buffer elasticity shape parameter (configured in `engine_config/actuarial_scalars.yaml`, calibrated at $\beta = 2.0$ for graceful degradation architectures). For strict hard buffers ($\delta = 0$), any restoration completed within $\tau_{\text{buffer}}$ yields $T_{\text{eff}} = 0.0\text{ hours}$ of revenue loss, while still accruing direct IT engineering labor:

$$C_{\text{reconst}} = T_{\text{tech}} \cdot R_{\text{eng}} \cdot N_{\text{FTE}}$$

**Verification on T4-RVS02 / T10-RVS04 (Disk Cleanup):**
*   $T_{\text{tech}} \in [0.15, 0.25, 0.50]\text{ hours}$ (15-minute mode).
*   $\tau_{\text{buffer}} = 1.0\text{ hour}$ (monitoring alert threshold before partition lock).
*   Since $\max(T_{\text{tech}}) = 0.50 \le \tau_{\text{buffer}}$, $T_{\text{eff}} = 0.0\text{ hours}$.
*   Business interruption loss = $0.00\text{ EUR}$. Direct labor = $0.25\text{ hr} \times R_{\text{eng}} \approx 25\text{--}50\text{ EUR}$.

### 4.2 Environment Scalar Matrix & Bow-Tie Control-Plane Escalation (`bowtie_escalation.py`)

For any asset $i$, let its environment tier be $E_i \in \text{EnvironmentTier}$. The environment revenue attenuation scalar $\omega_{\text{rev}}(E_i)$ is strictly defined as:

$$\omega_{\text{rev}}(E_i) = \begin{cases} 1.00 & \text{if } E_i = \text{PROD\_CRITICAL} \\ 0.35 & \text{if } E_i = \text{PROD\_SUPPORT} \\ 0.00 & \text{if } E_i = \text{STAGING\_UAT} \\ 0.00 & \text{if } E_i = \text{LAB\_DEV\_TEST} \end{cases}$$

**Verification on T2-RVS03/04 (K8s Lab):**
*   $E_i = \text{LAB\_DEV\_TEST} \implies \omega_{\text{rev}}(E_i) = 0.00$.
*   Revenue loss = $0.00\text{ EUR}$ across all Monte Carlo percentiles. Total loss equals pure cluster rebuild labor ($C_{\text{reconst}}$).

**Bow-Tie Control-Plane Cascading Formula:**
When a threat event with causal nature $C \in \{\text{MALICIOUS\_EXFILTRATION}, \text{DESTRUCTIVE\_SABOTAGE}\}$ impacts a node $u$ where $\text{Role}(u) = \text{CONTROL\_PLANE}$, the Effective Blast Set $\mathcal{B}(u)$ expands across the directed dependency graph $G = (V, E_{\text{dep}})$:

$$\mathcal{B}(u) = \{u\} \cup \{ v \in V \mid (u \xrightarrow{*} v) \in E_{\text{dep}} \} $$

The total hourly business interruption exposure $V_{\text{cascade}}(u)$ is the Contagion-Weighted Sum over the blast set:

$$V_{\text{cascade}}(u) = V_{\text{rev}}(u)\cdot\omega_{\text{rev}}(E_u) + \sum_{v \in \mathcal{B}(u) \setminus \{u\}} \alpha(u, v) \cdot V_{\text{rev}}(v) \cdot \omega_{\text{rev}}(E_v)$$

Where $\alpha(u, v) \in (0, 1]$ is the coupling contagion coefficient (for Tier-0 PAM / Identity Control Planes, $\alpha = 1.0$ for destructive/ransomware pivot scenarios and $\alpha = 0.65$ for credential harvesting privilege escalation).

**Verification on T6-RVS02 (PAM Compromise):**
*   Direct PAM appliance revenue $V_{\text{rev}}(u) = 0\text{ EUR}$ (infrastructure node).
*   Because $\text{Role}(u) = \text{CONTROL\_PLANE}$, $\mathcal{B}(u)$ traverses all governed `PROD_CRITICAL` `DATA_PLANE` nodes, elevating the mean actuarial exposure from $3\text{k EUR}$ (local appliance rebuild) to $\approx 198\text{k EUR}$ (enterprise-wide privileged contagion).

### 4.3 Causal Regulatory Gating (`regulatory_gating.py`)

Statutory data protection fines $L_{\text{reg\_privacy}}$ are governed by an explicit indicator function $\mathbb{I}_{\text{breach}}$:

$$\mathbb{I}_{\text{breach}}(u, \text{Threat}) = \begin{cases} 1 & \text{if } \text{Threat.causal\_nature} = \text{MALICIOUS\_EXFILTRATION} \land \exists v \in \mathcal{B}(u) : \text{holds\_regulated\_data}(v) = \text{True} \\ 0 & \text{otherwise} \end{cases}$$

$$L_{\text{reg\_privacy}} = \mathbb{I}_{\text{breach}}(u, \text{Threat}) \cdot \text{PERT}(\text{Fine}_{\min}, \text{Fine}_{\text{mode}}, \text{Fine}_{\max})$$

**Verification on T3-RVS04 (Backhoe Fiber Cut):**
*   $\text{Threat.causal\_nature} = \text{ACCIDENTAL\_PHYSICAL\_SEVERANCE}$.
*   $\mathbb{I}_{\text{breach}} = 0 \implies L_{\text{reg\_privacy}} = 0.00\text{ EUR}$.

---

## 5. TESTING & VALIDATION STRATEGY (PYTEST ORACLES)

All tests must be written in 100% Technical English and executed via `pytest -v --tb=short`.

### 5.1 New Test Suite Files
*   `tests/unit/test_fail_closed_contracts.py`
*   `tests/unit/test_topology_enricher.py`
*   `tests/unit/test_actuarial_three_layer_physics.py`
*   `tests/integration/test_red_team_canary_scenarios.py`

### 5.2 Exact Pytest Oracles & Invariants

| Oracle ID | Target Scenario / Component | Input Condition | Mandatory Assertion (Oracle) |
| :--- | :--- | :--- | :--- |
| **ORC-01** | Fail-Closed Contract (`actuarial_contracts.py`) | Asset JSON missing `environment_tier` bypassing enricher | Raises `ActuarialContractViolationError`. Zero fallback to `PROD_CRITICAL` or `8.0` hours. |
| **ORC-02** | Ambiguous Enrichment (`topology_enricher.py`) | Hostname `prd-lab-k8s-01` matching both PROD and LAB rules | Raises `ActuarialContractViolationError` citing conflicting rule IDs. |
| **ORC-03** | Enrichment Provenance (`topology_enricher.py`) | Valid untagged K8s lab node `dev-k8s-worker-04` | Resolves `LAB_DEV_TEST`, emits `EnrichmentAuditEntry` with valid 64-char hex SHA-256 hash. |
| **ORC-04** | **Canary 1:** T6-RVS02 (PAM Control Plane) | `CONTROL_PLANE` PAM node ($V_{\text{rev}}=0$) governing 12 `PROD_CRITICAL` nodes | Mean ALE $\in [185,000\text{ EUR}, 215,000\text{ EUR}]$. Assert `cascaded_loss_eur > 50 * direct_reconstitution_eur`. |
| **ORC-05** | **Canary 2:** T2-RVS03/04 (K8s Lab) | `LAB_DEV_TEST` K8s cluster with nominal org revenue $50\text{k EUR/hr}$ | `business_interruption_eur == 0.0` across all 10,000 Monte Carlo trials. Total ALE $\le 5,000\text{ EUR}$ (pure IT labor). |
| **ORC-06** | **Canary 3:** T3-RVS04 (Backhoe Fiber Cut) | `ACCIDENTAL_PHYSICAL_SEVERANCE` on `PROD_CRITICAL` link carrying PII | `regulatory_privacy_fine_eur == 0.0` across all 10,000 trials. |
| **ORC-07** | **Canary 4:** T4-RVS02 / T10-RVS04 (Disk Cleanup) | `RESOURCE_EXHAUSTION`, $T_{\text{tech}} \sim \text{PERT}(0.1, 0.25, 0.5)$, $\tau_{\text{buffer}} = 1.0\text{ hr}$ | `effective_outage_hours == 0.0`, `business_interruption_eur == 0.0`, `total_loss_eur < 250.0` EUR. |
| **ORC-08** | Property-Based Monotonicity (`hypothesis`) | Any valid `AssetActuarialProfile` and `PERTDistributionSpec` | Increasing $\tau_{\text{buffer}}$ monotonically decreases or keeps constant $T_{\text{eff}}$. Never produces negative losses (`loss >= 0.0`). |
| **ORC-09** | Word Annex Contiguity (`test_word_annex.py`) | Full assessment pipeline run | Document generates with 0 broken bookmarks, identical table count, and all capability cards populated in English/target locale without `NaN` or `None`. |

### 5.3 Codebase Hygiene Gate (Static Analysis)
Execute an automated AST/grep gate in CI to ensure zero regressions:
```bash
# Must return 0 matches across src/
rg "default_rto_hours" src/
rg "8\.0" src/assessment_engine/actuarial/
```

---

## 6. ROLLBACK & SAFETY GATES

To guarantee zero operational disruption during deployment, execution is governed by three strict safety gates:

### Gate 1: Pre-Computation Dry-Run Validation (`--validate-topology-only`)
Before executing the Monte Carlo simulation or generating Word annexes, the CLI/Orchestrator runs `TopologyEnricher` across the entire asset inventory. If any asset fails deterministic resolution, the engine outputs a structured JSON diagnostic report listing all offending `asset_id` records and halts with exit code `2` before mutating any state or output files.

### Gate 2: Deterministic Seed & Golden Master Diffing
All Monte Carlo simulations enforce an explicit cryptographic PRNG seed (`numpy.random.Generator(numpy.random.PCG64(seed=42))`). Prior to merging Phase 5:
1. Run the Golden Master suite against existing assessments.
2. Verify that non-distorted scenarios remain within $\pm 0.01\%$ numerical tolerance where physics definitions did not change, while the four Red Team Canary classes shift deterministically to their mathematically sound targets.

### Gate 3: Atomic Git Tagging & Configuration Versioning
1. Tag the repository state prior to Phase 1 execution: `git tag -a pre-sr117-actuarial-remediation -m "Baseline prior to 3-Layer Actuarial Remediation"`.
2. Embed a mandatory `schema_version: "2.0.0-SR117"` header inside `engine_config/actuarial_scalars.yaml` and `engine_config/threat_physics_catalog.yaml`.
3. If the orchestrator detects a version mismatch between the Python codebase and the YAML configuration files, it immediately aborts execution (`ConfigurationVersionMismatchError`).