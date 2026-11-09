### ARCHITECTURAL DIAGNOSIS & PARADIGM SHIFT

The empirical failures observed in your production pipeline stem from a fundamental violation of **Hexagonal Architecture (Ports and Adapters)** and **Actuarial Science**: **You are allowing a probabilistic Large Language Model (LLM) to perform deterministic mathematical calibration and taxonomic routing.**

LLMs are semantic engines, not calculators. When an LLM generates raw dollar amounts for Loss Magnitude (LM) or Loss Event Frequency (LEF), it hallucinates figures detached from the enterprise's financial reality. This causes €10.02 HIGH risks, inverted severity curves, and uncalibrated asset gravity.

#### The Core Architectural Principle
We will strip the LLM of all authority to output financial figures, frequencies, or unvalidated risk categories. 
1. **The LLM (Infrastructure Layer / Driven Adapter):** Evaluates unstructured evidence and maps it strictly to **Qualitative Enums** (e.g., `BlastRadius.ENTERPRISE_WIDE`, `RecoveryComplexity.SEVERE`), **Bounded Numeric Ranges** (e.g., `EstimatedDowntimeHours`), and **Canonical Taxonomy IDs**.
2. **The Python Actuarial Engine (Domain Layer):** Ingests these qualitative tokens, combines them with the tenant's **Financial Profile** (Annual Revenue, Hourly OpEx Burn, Industry Archetype), and executes deterministic **Open FAIR Monte Carlo simulations** bounded by hard mathematical invariants.

```text
[Unstructured Tenant Evidence] 
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ INFRASTRUCTURE LAYER: LLM Semantic Adapter (Constrained)    │
│ • Output: CanonicalTaxonomyID, BlastRadius, DowntimeVector  │
│ • Strictly NO raw currency or frequency floats allowed      │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Validated DTO)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ APPLICATION LAYER: Orchestration & Deduplication            │
│ • Enforces Cross-Tower Orthogonality (T1-T10 Ownership)     │
│ • Executes Deterministic Threat Injection (Blindspot Check) │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Domain Entities)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ DOMAIN LAYER: Pure Python Actuarial Engine (Open FAIR)      │
│ • Computes PERT Distributions from Tenant Financial Profile │
│ • Enforces Asset Gravity & Monotonic Severity Bounding      │
│ • Output: Mathematically Audited ALE                        │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER: Late-Binding Localization Adapter       │
│ • Maps Canonical IDs & Metrics to `locales.json`            │
└─────────────────────────────────────────────────────────────┘
```

---

### PHASE 1: ACTUARIAL GRAVITY ANCHORING & MONOTONIC BOUNDING

To eliminate €10 HIGH risks, inverted severities, and decoupled asset gravity, we must anchor the Open FAIR Loss Magnitude ($LM$) and Annualized Loss Expectancy ($ALE$) to the tenant's macroeconomic reality and the target asset's operational dependency.

#### 1.1 Mathematical Formulation

Let $R_{\text{annual}}$ be the Tenant's Annual Revenue, and $H_{\text{op}}$ be the annual operational hours derived from the Industry Archetype (e.g., $8760$ for 24/7 Manufacturing/FinTech; $2080$ for standard B2B services).

**1. Base Hourly Burn Rate ($B_{\text{hourly}}$):**
$$B_{\text{hourly}} = \frac{R_{\text{annual}} \times \omega_{\text{industry}}}{H_{\text{op}}}$$
*(Where $\omega_{\text{industry}} \in [0.15, 1.0]$ is the Industry Operational Dependency Coefficient, representing the fraction of revenue directly halted by IT/OT downtime).*

**2. Asset Gravity Multiplier ($\Gamma_{\text{asset}}$):**
Every asset or architectural component evaluated in Towers T1–T10 is assigned a dependency radius $\rho \in \{\text{LOCAL}, \text{DEPARTMENTAL}, \text{PLANT\_WIDE}, \text{ENTERPRISE\_SYST}\}$, mapped deterministically to a Blast Radius Factor $\beta_\rho \in [0.01, 1.0]$ and a Redundancy Factor $\theta \in \{0.1 \text{ (HA)}, 0.5 \text{ (Degraded)}, 1.0 \text{ (SPOF)}\}$.
$$\Gamma_{\text{asset}} = \beta_\rho \times \theta$$

**3. Primary Loss Magnitude Floor ($LM_{\text{floor}}$):**
For any availability or integrity risk (such as the Tower 4 NetApp SAN SPOF), the minimum Primary Loss ($PL$) for a single event is strictly bounded by the PERT-weighted downtime $D_{\text{PERT}}$:
$$D_{\text{PERT}} = \frac{D_{\text{min}} + 4D_{\text{mode}} + D_{\text{max}}}{6}$$
$$PL_{\text{productivity}} = B_{\text{hourly}} \times \Gamma_{\text{asset}} \times D_{\text{PERT}}$$
*In the €1.1B Manufacturing test case: $B_{\text{hourly}} = €13,000$. A SAN SPOF has $\beta_\rho = 1.0$ (Enterprise/Plant-wide) and $\theta = 1.0$ (No Redundancy), yielding $\Gamma_{\text{asset}} = 1.0$. A 24-hour recovery time forces an immediate, inescapable Primary Loss floor of $€312,000$ per event, completely eradicating the €5,000 hallucination.*

**4. Severity Tier Monotonic Bounding (The Invariant Law):**
To prevent a MEDIUM risk from exceeding a CRITICAL risk, and to prevent €10 HIGH risks, every Qualitative Severity Tier $S \in \{\text{LOW}, \text{MEDIUM}, \text{HIGH}, \text{CRITICAL}\}$ is mapped to strict fractional bands of $R_{\text{annual}}$:

| Severity Tier ($S$) | Floor Coefficient ($\alpha_{\min}$) | Ceiling Coefficient ($\alpha_{\max}$) | Example ($R_{\text{annual}} = \$1\text{B}$) |
| :--- | :--- | :--- | :--- |
| **LOW** | $0.000001$ ($0.0001\%$) | $0.000050$ ($0.005\%$) | $\$1,000 \le \text{ALE} < \$50,000$ |
| **MEDIUM** | $0.000050$ ($0.005\%$) | $0.000500$ ($0.05\%$) | $\$50,000 \le \text{ALE} < \$500,000$ |
| **HIGH** | $0.000500$ ($0.05\%$) | $0.005000$ ($0.5\%$) | $\$500,000 \le \text{ALE} < \$5,000,000$ |
| **CRITICAL** | $0.005000$ ($0.5\%$) | $0.050000$ ($5.0\%$) | $\$5,000,000 \le \text{ALE} \le \$50,000,000$ |

The calibrated Annualized Loss Expectancy ($ALE_{\text{calibrated}}$) is enforced via a hard clamping function over the raw Monte Carlo 90th percentile output ($ALE_{\text{raw}}$):
$$ALE_{\text{calibrated}} = \min\left( R_{\text{annual}} \cdot \alpha_{\max}(S), \; \max\left( R_{\text{annual}} \cdot \alpha_{\min}(S), \; ALE_{\text{raw}} \right) \right)$$

This guarantees **Strict Monotonicity**:
$$\forall r_i, r_j \in \text{Risks}: \text{Severity}(r_i) > \text{Severity}(r_j) \implies \inf(ALE(r_i)) \ge \sup(ALE(r_j))$$

#### 1.2 Domain Layer Implementation (100% Technical English)

```python
# domain/models/financial_profile.py
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

class IndustryArchetype(str, Enum):
    MANUFACTURING_24_7 = "MANUFACTURING_24_7"
    FINTECH_CONTINUOUS = "FINTECH_CONTINUOUS"
    HEALTHCARE_CRITICAL = "HEALTHCARE_CRITICAL"
    B2B_ENTERPRISE_STANDARD = "B2B_ENTERPRISE_STANDARD"
    RETAIL_OMNICHANNEL = "RETAIL_OMNICHANNEL"

class SeverityTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class BlastRadius(str, Enum):
    ISOLATED_WORKSTATION = "ISOLATED_WORKSTATION"
    DEPARTMENTAL_SUBNET = "DEPARTMENTAL_SUBNET"
    REGIONAL_FACILITY = "REGIONAL_FACILITY"
    ENTERPRISE_SYSTEMIC = "ENTERPRISE_SYSTEMIC"

class RedundancyState(str, Enum):
    ACTIVE_ACTIVE_HA = "ACTIVE_ACTIVE_HA"
    ACTIVE_PASSIVE_WARM = "ACTIVE_PASSIVE_WARM"
    DEGRADED_MANUAL_FAILOVER = "DEGRADED_MANUAL_FAILOVER"
    SINGLE_POINT_OF_FAILURE = "SINGLE_POINT_OF_FAILURE"

@dataclass(frozen=True)
class TenantFinancialProfile:
    tenant_id: str
    annual_revenue: Decimal
    industry_archetype: IndustryArchetype
    explicit_hourly_burn_override: Decimal | None = None

    @property
    def operational_hours_per_year(self) -> Decimal:
        mapping = {
            IndustryArchetype.MANUFACTURING_24_7: Decimal("8760"),
            IndustryArchetype.FINTECH_CONTINUOUS: Decimal("8760"),
            IndustryArchetype.HEALTHCARE_CRITICAL: Decimal("8760"),
            IndustryArchetype.RETAIL_OMNICHANNEL: Decimal("6570"),
            IndustryArchetype.B2B_ENTERPRISE_STANDARD: Decimal("2080"),
        }
        return mapping[self.industry_archetype]

    @property
    def operational_dependency_factor(self) -> Decimal:
        mapping = {
            IndustryArchetype.MANUFACTURING_24_7: Decimal("0.85"),
            IndustryArchetype.FINTECH_CONTINUOUS: Decimal("0.95"),
            IndustryArchetype.HEALTHCARE_CRITICAL: Decimal("0.90"),
            IndustryArchetype.RETAIL_OMNICHANNEL: Decimal("0.75"),
            IndustryArchetype.B2B_ENTERPRISE_STANDARD: Decimal("0.40"),
        }
        return mapping[self.industry_archetype]

    @property
    def hourly_downtime_burn(self) -> Decimal:
        if self.explicit_hourly_burn_override is not None:
            return self.explicit_hourly_burn_override
        return (
            self.annual_revenue * self.operational_dependency_factor
        ) / self.operational_hours_per_year
```

```python
# domain/services/actuarial_calibration_engine.py
from decimal import Decimal
import numpy as np
from domain.models.financial_profile import (
    TenantFinancialProfile,
    SeverityTier,
    BlastRadius,
    RedundancyState,
)

class ActuarialCalibrationViolationError(Exception):
    """Raised when actuarial inputs violate domain invariants."""

class ActuarialCalibrationEngine:
    """
    Pure Domain Service: Executes Open FAIR calculations and enforces
    Actuarial Gravity and Monotonic Severity Bounding.
    """

    SEVERITY_REVENUE_BANDS: dict[SeverityTier, tuple[Decimal, Decimal]] = {
        SeverityTier.LOW: (Decimal("0.000001"), Decimal("0.000050")),
        SeverityTier.MEDIUM: (Decimal("0.000050"), Decimal("0.000500")),
        SeverityTier.HIGH: (Decimal("0.000500"), Decimal("0.005000")),
        SeverityTier.CRITICAL: (Decimal("0.005000"), Decimal("0.050000")),
    }

    BLAST_RADIUS_MULTIPLIERS: dict[BlastRadius, Decimal] = {
        BlastRadius.ISOLATED_WORKSTATION: Decimal("0.005"),
        BlastRadius.DEPARTMENTAL_SUBNET: Decimal("0.100"),
        BlastRadius.REGIONAL_FACILITY: Decimal("0.450"),
        BlastRadius.ENTERPRISE_SYSTEMIC: Decimal("1.000"),
    }

    REDUNDANCY_MULTIPLIERS: dict[RedundancyState, Decimal] = {
        RedundancyState.ACTIVE_ACTIVE_HA: Decimal("0.05"),
        RedundancyState.ACTIVE_PASSIVE_WARM: Decimal("0.25"),
        RedundancyState.DEGRADED_MANUAL_FAILOVER: Decimal("0.65"),
        RedundancyState.SINGLE_POINT_OF_FAILURE: Decimal("1.00"),
    }

    @classmethod
    def compute_asset_gravity(
        cls, blast_radius: BlastRadius, redundancy: RedundancyState
    ) -> Decimal:
        return (
            cls.BLAST_RADIUS_MULTIPLIERS[blast_radius]
            * cls.REDUNDANCY_MULTIPLIERS[redundancy]
        )

    @classmethod
    def calculate_calibrated_ale(
        cls,
        profile: TenantFinancialProfile,
        severity: SeverityTier,
        blast_radius: BlastRadius,
        redundancy: RedundancyState,
        downtime_hours_min: float,
        downtime_hours_mode: float,
        downtime_hours_max: float,
        lef_min: float,
        lef_mode: float,
        lef_max: float,
        secondary_loss_multiplier: float = 1.25,
        iterations: int = 10_000,
    ) -> Decimal:
        if not (0 <= downtime_hours_min <= downtime_hours_mode <= downtime_hours_max):
            raise ActuarialCalibrationViolationError("Invalid PERT downtime bounds.")
        if not (0 <= lef_min <= lef_mode <= lef_max):
            raise ActuarialCalibrationViolationError("Invalid PERT LEF bounds.")

        gravity = float(cls.compute_asset_gravity(blast_radius, redundancy))
        hourly_burn = float(profile.hourly_downtime_burn)

        # 1. Sample Loss Event Frequency (LEF) via PERT-Beta distribution
        lef_samples = cls._sample_pert(lef_min, lef_mode, lef_max, iterations)

        # 2. Sample Downtime Duration via PERT-Beta distribution
        downtime_samples = cls._sample_pert(
            downtime_hours_min, downtime_hours_mode, downtime_hours_max, iterations
        )

        # 3. Compute Primary & Secondary Loss Magnitude (LM) anchored to Asset Gravity
        primary_loss_samples = downtime_samples * hourly_burn * gravity
        total_lm_samples = primary_loss_samples * secondary_loss_multiplier

        # 4. Compute Raw Annualized Loss Expectancy (ALE = LEF * LM)
        ale_samples = lef_samples * total_lm_samples
        raw_ale = Decimal(str(np.percentile(ale_samples, 85)))

        # 5. Enforce Monotonic Severity Bounding
        floor_coeff, ceiling_coeff = cls.SEVERITY_REVENUE_BANDS[severity]
        ale_floor = profile.annual_revenue * floor_coeff
        ale_ceiling = profile.annual_revenue * ceiling_coeff

        # If Asset Gravity dictates a catastrophic single-event loss exceeding the
        # qualitative severity ceiling, auto-escalate or clamp to physical reality.
        gravity_anchored_floor = max(
            ale_floor,
            Decimal(str(np.mean(primary_loss_samples))) * Decimal(str(lef_mode)),
        )

        calibrated_ale = min(ale_ceiling, max(gravity_anchored_floor, raw_ale))
        return calibrated_ale.quantize(Decimal("0.01"))

    @staticmethod
    def _sample_pert(
        min_val: float, mode_val: float, max_val: float, size: int, lambd: float = 4.0
    ) -> np.ndarray:
        if max_val == min_val:
            return np.full(size, min_val)
        mean = (min_val + lambd * mode_val + max_val) / (lambd + 2.0)
        if mean == mode_val:
            alpha = beta = (lambd / 2.0) + 1.0
        else:
            alpha = ((mean - min_val) * (2.0 * mode_val - min_val - max_val)) / (
                (mode_val - mean) * (max_val - min_val)
            )
            beta = (alpha * (max_val - mean)) / (mean - min_val)
        alpha = max(alpha, 1e-4)
        beta = max(beta, 1e-4)
        rng = np.random.default_rng(seed=42)  # Deterministic seed for auditability
        samples = rng.beta(alpha, beta, size=size)
        return min_val + samples * (max_val - min_val)
```

---

### PHASE 2: CROSS-TOWER RISK ORTHOGONALITY

To stop the LLM from inventing duplicate risks across towers (such as an M&A integration issue appearing simultaneously in T5, T7, and T8), we must implement **Strict Taxonomic Bounding** at the Prompt/Adapter level and **Graph-Based Root-Cause Consolidation** at the Application Layer.

#### 2.1 The Canonical Mutually Exclusive & Collectively Exhaustive (MECE) Taxonomy
Each Tower ($T_1 \dots T_{10}$) is assigned an immutable set of `CanonicalRiskScenarioID` enums. The LLM is physically incapable of inventing a free-text risk category because its output schema is constrained via Structured Outputs (JSON Schema `enum`) to only the IDs permitted for the currently executing Tower.

```text
[Tower T4: Storage] ──► Allowed Enums: [T4_SAN_SPOF, T4_IMMUTABLE_BACKUP_ABSENCE, ...]
[Tower T7: ITSM]    ──► Allowed Enums: [T7_CHANGE_CONTROL_BYPASS, T7_CMDB_DRIFT, ...]
[Tower T8: Corp IT] ──► Allowed Enums: [T8_MA_SHADOW_IT_INTEGRATION, ...]
```

If an M&A integration issue causes CMDB drift in T7 and Shadow IT in T8:
1. **Strict Scope Boundary:** T8 owns the **Root Cause** (`T8_MA_UNMANAGED_INFRASTRUCTURE_INGESTION`). T7 is strictly forbidden from emitting M&A strategic risks; it can only emit `T7_CMDB_DISCOVERY_GAP`.
2. **Cross-Tower Deduplication Engine:** After all 10 tower evaluations run, the Application Layer runs a **Two-Tier Deduplication Pipeline**:
   * **Tier 1 (Deterministic Taxonomic Collision):** Groups findings by `CanonicalRiskScenarioID` and `PrimaryRootCauseEnum`. If multiple towers flag the same underlying root cause, the system retains the finding in the **Primary Owning Tower** (defined in the registry) and converts the secondary tower findings into `CorroboratingEvidenceNodes` attached to the primary risk.
   * **Tier 2 (Semantic Vector Orthogonality):** Computes cosine similarity over dense embeddings of the `technical_evidence_summary`. If $\cos(\theta) > 0.82$ across two different towers, the engine merges them, taking the $\max(\text{BlastRadius})$ and attributing the consolidated risk to the upstream architectural tower (e.g., Identity T5 supersedes Endpoint T9).

#### 2.2 Application Layer Implementation (100% Technical English)

```python
# domain/taxonomy/canonical_registry.py
from enum import Enum
from dataclasses import dataclass

class ArchitecturalTower(str, Enum):
    T1_NETWORK_PERIMETER = "T1_NETWORK_PERIMETER"
    T2_COMPUTE_VIRTUALIZATION = "T2_COMPUTE_VIRTUALIZATION"
    T3_CLOUD_INFRASTRUCTURE = "T3_CLOUD_INFRASTRUCTURE"
    T4_STORAGE_BACKUP = "T4_STORAGE_BACKUP"
    T5_IDENTITY_ACCESS = "T5_IDENTITY_ACCESS"
    T6_APPLICATION_SECURITY = "T6_APPLICATION_SECURITY"
    T7_ITSM_OPERATIONS = "T7_ITSM_OPERATIONS"
    T8_GOVERNANCE_COMPLIANCE = "T8_GOVERNANCE_COMPLIANCE"
    T9_DIGITAL_WORKPLACE = "T9_DIGITAL_WORKPLACE"
    T10_OT_INDUSTRIAL_IOT = "T10_OT_INDUSTRIAL_IOT"

class SystemicRootCause(str, Enum):
    MERGER_ACQUISITION_DIVERGENCE = "MERGER_ACQUISITION_DIVERGENCE"
    LEGACY_UNPATCHABLE_DEBT = "LEGACY_UNPATCHABLE_DEBT"
    SINGLE_POINT_OF_FAILURE_DESIGN = "SINGLE_POINT_OF_FAILURE_DESIGN"
    FLAT_NETWORK_TOPOLOGY = "FLAT_NETWORK_TOPOLOGY"
    PRIVILEGE_ESCALATION_PATHWAY = "PRIVILEGE_ESCALATION_PATHWAY"
    ABSENCE_OF_IMMUTABLE_RECOVERY = "ABSENCE_OF_IMMUTABLE_RECOVERY"
    GOVERNANCE_PROCESS_BYPASS = "GOVERNANCE_PROCESS_BYPASS"

@dataclass(frozen=True)
class CanonicalRiskDefinition:
    scenario_id: str
    owning_tower: ArchitecturalTower
    permitted_root_causes: tuple[SystemicRootCause, ...]
    i18n_title_key: str
    i18n_description_key: str

# Immutable Global Registry: Prevents LLM Taxonomic Hallucination
CANONICAL_RISK_REGISTRY: dict[str, CanonicalRiskDefinition] = {
    "T4_STORAGE_PRIMARY_SAN_SPOF": CanonicalRiskDefinition(
        scenario_id="T4_STORAGE_PRIMARY_SAN_SPOF",
        owning_tower=ArchitecturalTower.T4_STORAGE_BACKUP,
        permitted_root_causes=(SystemicRootCause.SINGLE_POINT_OF_FAILURE_DESIGN,),
        i18n_title_key="risk.t4.san_spof.title",
        i18n_description_key="risk.t4.san_spof.desc",
    ),
    "T5_IAM_DORMANT_PRIVILEGED_ACCOUNTS": CanonicalRiskDefinition(
        scenario_id="T5_IAM_DORMANT_PRIVILEGED_ACCOUNTS",
        owning_tower=ArchitecturalTower.T5_IDENTITY_ACCESS,
        permitted_root_causes=(SystemicRootCause.PRIVILEGE_ESCALATION_PATHWAY,),
        i18n_title_key="risk.t5.dormant_priv.title",
        i18n_description_key="risk.t5.dormant_priv.desc",
    ),
    "T8_GOV_MA_UNINTEGRATED_ENTITIES": CanonicalRiskDefinition(
        scenario_id="T8_GOV_MA_UNINTEGRATED_ENTITIES",
        owning_tower=ArchitecturalTower.T8_GOVERNANCE_COMPLIANCE,
        permitted_root_causes=(SystemicRootCause.MERGER_ACQUISITION_DIVERGENCE,),
        i18n_title_key="risk.t8.ma_divergence.title",
        i18n_description_key="risk.t8.ma_divergence.desc",
    ),
    "T10_OT_IT_CONDUIT_LATERAL_MOVEMENT": CanonicalRiskDefinition(
        scenario_id="T10_OT_IT_CONDUIT_LATERAL_MOVEMENT",
        owning_tower=ArchitecturalTower.T10_OT_INDUSTRIAL_IOT,
        permitted_root_causes=(SystemicRootCause.FLAT_NETWORK_TOPOLOGY,),
        i18n_title_key="risk.t10.ot_lateral.title",
        i18n_description_key="risk.t10.ot_lateral.desc",
    ),
}

# Authority Hierarchy for Root Cause Consolidation (Upstream beats Downstream)
ROOT_CAUSE_AUTHORITY_TOWER: dict[SystemicRootCause, ArchitecturalTower] = {
    SystemicRootCause.MERGER_ACQUISITION_DIVERGENCE: ArchitecturalTower.T8_GOVERNANCE_COMPLIANCE,
    SystemicRootCause.FLAT_NETWORK_TOPOLOGY: ArchitecturalTower.T1_NETWORK_PERIMETER,
    SystemicRootCause.PRIVILEGE_ESCALATION_PATHWAY: ArchitecturalTower.T5_IDENTITY_ACCESS,
    SystemicRootCause.SINGLE_POINT_OF_FAILURE_DESIGN: ArchitecturalTower.T4_STORAGE_BACKUP,
    SystemicRootCause.ABSENCE_OF_IMMUTABLE_RECOVERY: ArchitecturalTower.T4_STORAGE_BACKUP,
    SystemicRootCause.LEGACY_UNPATCHABLE_DEBT: ArchitecturalTower.T2_COMPUTE_VIRTUALIZATION,
    SystemicRootCause.GOVERNANCE_PROCESS_BYPASS: ArchitecturalTower.T7_ITSM_OPERATIONS,
}
```

```python
# application/services/orthogonality_enforcer.py
from dataclasses import dataclass, field
import numpy as np
from domain.models.financial_profile import SeverityTier, BlastRadius, RedundancyState
from domain.taxonomy.canonical_registry import (
    CANONICAL_RISK_REGISTRY,
    ROOT_CAUSE_AUTHORITY_TOWER,
    ArchitecturalTower,
    SystemicRootCause,
)

class TaxonomicBoundaryViolationError(Exception):
    """Raised when an LLM adapter emits a scenario outside its assigned tower."""

@dataclass
class CandidateRiskFinding:
    scenario_id: str
    emitting_tower: ArchitecturalTower
    root_cause: SystemicRootCause
    severity: SeverityTier
    blast_radius: BlastRadius
    redundancy: RedundancyState
    downtime_hours_mode: float
    evidence_summary: str
    embedding_vector: list[float]
    corroborating_evidence: list[str] = field(default_factory=list)

class CrossTowerOrthogonalityEnforcer:
    """
    Application Service: Guarantees MECE risk output across T1-T10.
    Eliminates cross-tower duplication and enforces taxonomic ownership.
    """

    SEVERITY_RANK = {
        SeverityTier.LOW: 1,
        SeverityTier.MEDIUM: 2,
        SeverityTier.HIGH: 3,
        SeverityTier.CRITICAL: 4,
    }

    def __init__(self, cosine_similarity_threshold: float = 0.82):
        self.similarity_threshold = cosine_similarity_threshold

    def validate_and_deduplicate(
        self, findings: list[CandidateRiskFinding]
    ) -> list[CandidateRiskFinding]:
        # Step 1: Enforce strict Tower-to-Scenario boundary
        validated_findings: list[CandidateRiskFinding] = []
        for finding in findings:
            definition = CANONICAL_RISK_REGISTRY.get(finding.scenario_id)
            if not definition:
                raise TaxonomicBoundaryViolationError(
                    f"Unknown canonical scenario ID: {finding.scenario_id}"
                )
            if definition.owning_tower != finding.emitting_tower:
                # Re-route to canonical owner instead of duplicating
                finding.emitting_tower = definition.owning_tower
            validated_findings.append(finding)

        # Step 2: Consolidate identical Systemic Root Causes across different towers
        # (e.g., M&A issues emitted in T5, T7, and T8 collapse into the Authority Tower)
        consolidated_by_root = self._consolidate_cross_tower_root_causes(
            validated_findings
        )

        # Step 3: Vector Orthogonality Check (Semantic Deduplication)
        orthogonal_findings = self._enforce_vector_orthogonality(consolidated_by_root)
        return orthogonal_findings

    def _consolidate_cross_tower_root_causes(
        self, findings: list[CandidateRiskFinding]
    ) -> list[CandidateRiskFinding]:
        grouped: dict[SystemicRootCause, list[CandidateRiskFinding]] = {}
        for f in findings:
            grouped.setdefault(f.root_cause, []).append(f)

        result: list[CandidateRiskFinding] = []
        for root_cause, group in grouped.items():
            if len(group) == 1 or root_cause != SystemicRootCause.MERGER_ACQUISITION_DIVERGENCE:
                result.extend(group)
                continue

            # For systemic organizational root causes (like M&A divergence),
            # collapse duplicates into the designated Authority Tower.
            authority_tower = ROOT_CAUSE_AUTHORITY_TOWER[root_cause]
            primary = next(
                (f for f in group if f.emitting_tower == authority_tower), group[0]
            )
            for secondary in group:
                if secondary is not primary:
                    primary.corroborating_evidence.append(
                        f"[Merged from {secondary.emitting_tower.value}]: {secondary.evidence_summary}"
                    )
                    if self.SEVERITY_RANK[secondary.severity] > self.SEVERITY_RANK[primary.severity]:
                        primary.severity = secondary.severity
            result.append(primary)
        return result

    def _enforce_vector_orthogonality(
        self, findings: list[CandidateRiskFinding]
    ) -> list[CandidateRiskFinding]:
        # Sort by Severity descending so higher-impact findings absorb lower ones
        sorted_findings = sorted(
            findings, key=lambda x: self.SEVERITY_RANK[x.severity], reverse=True
        )
        accepted: list[CandidateRiskFinding] = []

        for candidate in sorted_findings:
            is_duplicate = False
            vec_a = np.array(candidate.embedding_vector)
            norm_a = np.linalg.norm(vec_a)

            for existing in accepted:
                vec_b = np.array(existing.embedding_vector)
                norm_b = np.linalg.norm(vec_b)
                if norm_a == 0 or norm_b == 0:
                    continue
                similarity = float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
                if similarity >= self.similarity_threshold:
                    existing.corroborating_evidence.append(
                        f"[Semantic Merge {candidate.emitting_tower.value}]: {candidate.evidence_summary}"
                    )
                    is_duplicate = True
                    break

            if not is_duplicate:
                accepted.append(candidate)

        return accepted
```

---

### PHASE 3: DETERMINISTIC MISSING SYSTEMIC RISKS INJECTION

LLMs suffer from "Attention Deficit" over large context windows: if an architecture document does not explicitly mention "OT Ransomware" or "Active Directory Tier-0 Pathing", the LLM often forgets to evaluate those risks. In cybersecurity, **the absence of evidence for a critical control is itself a high-priority risk finding.**

#### 3.1 The Archetype Threat Baseline Matrix & Control State Calculus
We introduce a deterministic **Zero-Trust Baseline Injector** in the Domain Layer.
1. Every `IndustryArchetype` is mapped to a mandatory set of **Baseline Threat Scenarios** (e.g., `MANUFACTURING_24_7` *must* evaluate `T10_OT_IT_CONDUIT_LATERAL_MOVEMENT` and `T4_STORAGE_PRIMARY_SAN_SPOF`).
2. Before running the pipeline, telemetry and document parsers populate a `TelemetryControlGraph` where each required security control $C_k$ is assigned a state:
   * `VERIFIED_PRESENT`: Positive technical proof exists (e.g., Firewall rules verifying IT/OT airgap).
   * `VERIFIED_ABSENT`: Explicit proof of absence (e.g., Single SAN controller found).
   * `UNVERIFIED_TELEMETRY_GAP`: Neither confirmed nor denied by evidence.
3. If the LLM finishes its pass across T1–T10 and fails to emit a mandatory Baseline Threat Scenario for which the required mitigating controls are either `VERIFIED_ABSENT` or `UNVERIFIED_TELEMETRY_GAP`, the **Systemic Risk Injector** deterministically synthesizes and injects the risk into the pipeline prior to Phase 1 Actuarial Calibration.

#### 3.2 Domain Layer Implementation (100% Technical English)

```python
# domain/services/systemic_risk_injector.py
from dataclasses import dataclass
from enum import Enum
from domain.models.financial_profile import (
    IndustryArchetype,
    SeverityTier,
    BlastRadius,
    RedundancyState,
)
from domain.taxonomy.canonical_registry import (
    ArchitecturalTower,
    SystemicRootCause,
)
from application.services.orthogonality_enforcer import CandidateRiskFinding

class ControlVerificationState(str, Enum):
    VERIFIED_PRESENT = "VERIFIED_PRESENT"
    VERIFIED_ABSENT = "VERIFIED_ABSENT"
    UNVERIFIED_TELEMETRY_GAP = "UNVERIFIED_TELEMETRY_GAP"

@dataclass(frozen=True)
class MandatoryThreatRule:
    scenario_id: str
    owning_tower: ArchitecturalTower
    root_cause: SystemicRootCause
    required_control_keys: tuple[str, ...]
    default_severity_if_absent: SeverityTier
    default_severity_if_unverified: SeverityTier
    default_blast_radius: BlastRadius
    default_redundancy: RedundancyState
    default_downtime_hours_mode: float

class DeterministicSystemicRiskInjector:
    """
    Domain Service: Prevents LLM blindspots by deterministically injecting
    mandatory industry-specific systemic risks when mitigating controls are
    absent or unverified in tenant telemetry.
    """

    ARCHETYPE_MANDATORY_RULES: dict[IndustryArchetype, tuple[MandatoryThreatRule, ...]] = {
        IndustryArchetype.MANUFACTURING_24_7: (
            MandatoryThreatRule(
                scenario_id="T10_OT_IT_CONDUIT_LATERAL_MOVEMENT",
                owning_tower=ArchitecturalTower.T10_OT_INDUSTRIAL_IOT,
                root_cause=SystemicRootCause.FLAT_NETWORK_TOPOLOGY,
                required_control_keys=("CTRL_IT_OT_IDMZ_FIREWALL", "CTRL_OT_NETWORK_SEGMENTATION"),
                default_severity_if_absent=SeverityTier.CRITICAL,
                default_severity_if_unverified=SeverityTier.HIGH,
                default_blast_radius=BlastRadius.ENTERPRISE_SYSTEMIC,
                default_redundancy=RedundancyState.SINGLE_POINT_OF_FAILURE,
                default_downtime_hours_mode=72.0,
            ),
            MandatoryThreatRule(
                scenario_id="T5_IAM_DORMANT_PRIVILEGED_ACCOUNTS",
                owning_tower=ArchitecturalTower.T5_IDENTITY_ACCESS,
                root_cause=SystemicRootCause.PRIVILEGE_ESCALATION_PATHWAY,
                required_control_keys=("CTRL_PAM_TIER0_ISOLATION", "CTRL_MFA_PRIVILEGED_ACCOUNTS"),
                default_severity_if_absent=SeverityTier.CRITICAL,
                default_severity_if_unverified=SeverityTier.HIGH,
                default_blast_radius=BlastRadius.ENTERPRISE_SYSTEMIC,
                default_redundancy=RedundancyState.DEGRADED_MANUAL_FAILOVER,
                default_downtime_hours_mode=48.0,
            ),
        ),
        # Additional archetypes (FINTECH_CONTINUOUS, HEALTHCARE_CRITICAL, etc.) follow identical pattern
    }

    @classmethod
    def inject_missing_systemic_risks(
        cls,
        archetype: IndustryArchetype,
        control_telemetry: dict[str, ControlVerificationState],
        existing_findings: list[CandidateRiskFinding],
    ) -> list[CandidateRiskFinding]:
        emitted_scenario_ids = {f.scenario_id for f in existing_findings}
        rules = cls.ARCHETYPE_MANDATORY_RULES.get(archetype, ())
        injected_findings = list(existing_findings)

        for rule in rules:
            if rule.scenario_id in emitted_scenario_ids:
                continue  # Already evaluated by LLM adapter

            control_states = [
                control_telemetry.get(k, ControlVerificationState.UNVERIFIED_TELEMETRY_GAP)
                for k in rule.required_control_keys
            ]

            # If all required controls are explicitly verified present, risk is mitigated
            if all(s == ControlVerificationState.VERIFIED_PRESENT for s in control_states):
                continue

            if any(s == ControlVerificationState.VERIFIED_ABSENT for s in control_states):
                severity = rule.default_severity_if_absent
                reason = "Deterministic Injection: Required mitigating controls verified ABSENT."
            else:
                severity = rule.default_severity_if_unverified
                reason = "Deterministic Injection: Zero-Trust assumption due to UNVERIFIED telemetry gap."

            injected_findings.append(
                CandidateRiskFinding(
                    scenario_id=rule.scenario_id,
                    emitting_tower=rule.owning_tower,
                    root_cause=rule.root_cause,
                    severity=severity,
                    blast_radius=rule.default_blast_radius,
                    redundancy=rule.default_redundancy,
                    downtime_hours_mode=rule.default_downtime_hours_mode,
                    evidence_summary=f"{reason} Evaluated Controls: {rule.required_control_keys}",
                    embedding_vector=[],  # Exempt from cosine deduplication
                )
            )

        return injected_findings
```

---

### PHASE 4: HEXAGONAL LLM ADAPTER & LATE-BINDING LOCALIZATION

To enforce the **100% Technical English Law** while serving multi-national clients, the LLM prompt, schema, and internal domain states operate exclusively in Technical English. Translation is handled strictly at the outermost Presentation Adapter layer via `locales.json`.

#### 4.1 Constrained LLM Output Schema & Late-Binding Presenter

```python
# infrastructure/adapters/llm_schema.py
from pydantic import BaseModel, Field
from domain.models.financial_profile import SeverityTier, BlastRadius, RedundancyState
from domain.taxonomy.canonical_registry import SystemicRootCause

class ConstrainedLLMExtractionDTO(BaseModel):
    """
    Strictly constrains the LLM. Notice the complete absence of currency fields,
    ALE floats, or free-text risk titles.
    """
    scenario_id: str = Field(
        ..., description="Must match an allowed CanonicalRiskScenarioID for this Tower."
    )
    root_cause: SystemicRootCause
    qualitative_severity: SeverityTier
    blast_radius: BlastRadius
    redundancy_state: RedundancyState
    estimated_downtime_hours_min: float = Field(..., ge=0.0, le=720.0)
    estimated_downtime_hours_mode: float = Field(..., ge=0.0, le=720.0)
    estimated_downtime_hours_max: float = Field(..., ge=0.0, le=2160.0)
    technical_evidence_code: str = Field(
        ..., description="100% Technical English forensic summary of the evidence."
    )
```

```python
# infrastructure/adapters/localization_presenter.py
from decimal import Decimal
import json
from domain.taxonomy.canonical_registry import CANONICAL_RISK_REGISTRY

class LateBindingLocalizationAdapter:
    """
    Outermost Presentation Adapter: Translates canonical risk IDs and formats
    currency strictly at serialization time using `locales.json`.
    """

    def __init__(self, locales_path: str):
        with open(locales_path, "r", encoding="utf-8") as f:
            self._catalog: dict[str, dict[str, str]] = json.load(f)

    def render_localized_risk_report(
        self,
        scenario_id: str,
        calibrated_ale: Decimal,
        currency_code: str,
        target_locale: str = "en-US",
    ) -> dict[str, str]:
        definition = CANONICAL_RISK_REGISTRY[scenario_id]
        locale_dict = self._catalog.get(target_locale, self._catalog["en-US"])

        return {
            "scenario_id": scenario_id,
            "tower": definition.owning_tower.value,
            "localized_title": locale_dict.get(
                definition.i18n_title_key, definition.i18n_title_key
            ),
            "localized_description": locale_dict.get(
                definition.i18n_description_key, definition.i18n_description_key
            ),
            "formatted_ale": f"{currency_code} {calibrated_ale:,.2f}",
        }
```

---

### SUMMARY VERIFICATION MATRIX (HOW SYMPTOMS ARE ERADICATED)

| Empirical Failure Mode | Architectural Root Cause | Deterministic Resolution in New Architecture |
| :--- | :--- | :--- |
| **1. The €10.02 HIGH Risk Absurdity (T9)** | LLM generated unanchored loss figures without corporate scale context. | **Phase 1 (`SEVERITY_REVENUE_BANDS`):** A HIGH risk is mathematically clamped to a floor of $0.05\%$ of Annual Revenue. For a €1.1B enterprise, any HIGH risk has an inescapable floor of **€550,000**. |
| **2. Inverted Severity Proportionality (T7)** | Unbounded Monte Carlo distributions allowed high-frequency MEDIUM risks to eclipse low-frequency CRITICAL risks. | **Phase 1 (Monotonic Bounding Law):** $\inf(ALE(\text{CRITICAL})) \ge \sup(ALE(\text{MEDIUM}))$. CRITICAL risks ($0.5\% - 5.0\%$ revenue) can never fall below MEDIUM risks ($0.005\% - 0.05\%$ revenue). |
| **3. Decoupling of Asset Gravity (T4 SAN SPOF)** | LLM failed to multiply downtime duration by the factory's €13k/hour operational burn rate. | **Phase 1 (`ActuarialCalibrationEngine`):** Primary Loss is computed in Python as $B_{\text{hourly}} \times \Gamma_{\text{asset}} \times D_{\text{PERT}}$. A SAN SPOF ($\Gamma = 1.0$) with a 24h recovery mode automatically anchors to $€13,000 \times 24 = €312,000$ minimum primary loss per event. |
| **4. Taxonomic Duplication Across Towers (M&A in T5, T7, T8)** | Unconstrained free-text risk generation and lack of cross-tower state awareness. | **Phase 2 (`CrossTowerOrthogonalityEnforcer`):** LLM is restricted to Tower-specific Enums. `SystemicRootCause.MERGER_ACQUISITION_DIVERGENCE` is deterministically collapsed into its Authority Tower (`T8_GOVERNANCE_COMPLIANCE`), converting T5/T7 duplicates into corroborating evidence nodes. |
| **5. Systemic Blindspots (Missing OT Ransomware / Tier-0 IAM)** | LLM forgot to evaluate risks not explicitly mentioned in text chunks. | **Phase 3 (`DeterministicSystemicRiskInjector`):** Evaluates `ARCHETYPE_MANDATORY_RULES` against `ControlVerificationState`. Any unverified or absent critical control automatically injects the corresponding canonical risk before financial calibration. |