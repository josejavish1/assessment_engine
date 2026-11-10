# ARCHITECTURAL MASTER PLAN: POLYMORPHIC OPEN FAIR ACTUARIAL ENGINE

**Author:** `gemini-4-argon` (Principal Enterprise Architect & Chief Forensic Auditor)  
**Status:** Blueprint / Request for Comments (RFC)  
**Target:** Assessment Engine Core (`src/assessment_engine/`)  
**Doctrine:** Zero-Hardcoding, Domain-Driven Design (DDD), Algebraic Data Types (ADTs), 100% Language-Agnostic Core, Strict Type Safety.

---

## EXECUTIVE SUMMARY

To elevate the Assessment Engine to the undisputed #1 global standard, we must eradicate the current architectural anti-pattern: **Actuarial Monomorphism**. Currently, the engine assumes all technological technical debt manifests as a *Mission-Critical Availability Outage* (e.g., clearing house halts, transactional downtime). While mathematically sound for Core Infrastructure or High-Frequency Trading platforms, applying this model to FinOps, Modern Workplace, or Governance towers produces forensic hallucinations (e.g., claiming a misaligned FinOps tagging strategy causes a $500k/hour clearing outage).

We will replace this with a **Polymorphic Open FAIR (Factor Analysis of Information Risk) Actuarial Engine**. This architecture decouples *Tower Identity* from *Mathematical Loss Vectors* using a declarative Taxonomy Registry, Algebraic Data Types (Pydantic Discriminated Unions), and Strategy-Pattern Calculators. It will seamlessly scale from a 50-employee regional retail firm to a Tier-1 global financial institution across any industry vertical and output locale.

---

## PHASE 1: DECLARATIVE DOMAIN-TO-ARCHETYPE MAPPING REGISTRY

### 1.1 Architectural Objective
Eliminate all `if/else` tower-to-math routing inside the actuarial engine. The engine must not know what "FinOps" or "Compute" is; it must only know how to execute mathematical strategies defined by an injected configuration contract.

### 1.2 The Four Open FAIR Loss Archetypes
Every technological failure across the 10 Towers maps to one of four universal economic loss vectors:
1. `AVAILABILITY_OUTAGE`: Direct transactional or operational revenue halt (Core Infra, Network, Critical Apps).
2. `CAPITAL_INEFFICIENCY`: Unoptimized OPEX/CAPEX, cloud waste, orphaned resources, suboptimal licensing (FinOps, Cloud Architecture, Storage).
3. `PRODUCTIVITY_TOIL`: Human capital drag, manual runbooks, slow provisioning, ticket queue friction (Workplace, DevOps/Platform Engineering, Service Management).
4. `REGULATORY_AND_BREACH`: Compliance fines, data exfiltration, SLA penalties, audit failures (Security, Data Governance, Risk & Compliance).

### 1.3 Architectural Contract (`src/assessment_engine/domain/taxonomy/archetype_registry.py`)

```python
from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict

class LossArchetypeType(StrEnum):
    AVAILABILITY_OUTAGE = "AVAILABILITY_OUTAGE"
    CAPITAL_INEFFICIENCY = "CAPITAL_INEFFICIENCY"
    PRODUCTIVITY_TOIL = "PRODUCTIVITY_TOIL"
    REGULATORY_AND_BREACH = "REGULATORY_AND_BREACH"

class TowerActuarialMapping(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    
    tower_id: str = Field(..., pattern=r"^T\d{2}_[A-Z_]+$")
    primary_archetype: LossArchetypeType
    secondary_archetype: LossArchetypeType | None = None
    default_vulnerability_baseline: float = Field(..., ge=0.0, le=1.0)
    narrative_semantic_key: str = Field(..., description="Locale-agnostic semantic pointer for AST compilation")

class ActuarialTaxonomyRegistry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    
    version: str
    mappings: Dict[str, TowerActuarialMapping]

    def get_archetype_for_tower(self, tower_id: str) -> TowerActuarialMapping:
        if tower_id not in self.mappings:
            raise KeyError(f"Forensic Registry Error: Unmapped Tower ID '{tower_id}'.")
        return self.mappings[tower_id]
```

*Note: The actual mapping data will reside in an externalized, immutable `taxonomy_v2.yaml` file loaded via Dependency Injection at runtime. Zero domain data inside `.py` files.*

---

## PHASE 2: POLYMORPHIC TELEMETRY INGESTION

### 2.1 Architectural Objective
Expand the ingestion contract (`case_input.json` / `ClientProfile`) to capture multi-dimensional macroeconomic baselines without breaking backward compatibility or requiring clients to provide data irrelevant to their specific assessment scope.

### 2.2 Industry Vertical & Maturity Normalization
To support any company worldwide (Mid-Market to Tier-1), financial telemetry must be normalized against **Industry Verticals** (e.g., `FINANCIAL_SERVICES`, `HEALTHCARE`, `MANUFACTURING`, `RETAIL`) and **Organizational Scale**.

### 2.3 Architectural Contract (`src/assessment_engine/domain/models/telemetry.py`)

```python
from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Self

class IndustryVertical(StrEnum):
    FINANCIAL_SERVICES = "FINANCIAL_SERVICES"
    RETAIL_AND_ECOMMERCE = "RETAIL_AND_ECOMMERCE"
    MANUFACTURING_AND_LOGISTICS = "MANUFACTURING_AND_LOGISTICS"
    HEALTHCARE_AND_BIOTECH = "HEALTHCARE_AND_BIOTECH"
    TECHNOLOGY_AND_SAAS = "TECHNOLOGY_AND_SAAS"
    PUBLIC_SECTOR_AND_UTILITIES = "PUBLIC_SECTOR_AND_UTILITIES"

class AvailabilityBaseline(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    hourly_revenue_at_risk_usd: float = Field(..., gt=0.0)
    critical_service_mttr_hours: float = Field(..., gt=0.0)

class CapitalEfficiencyBaseline(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    annual_it_opex_usd: float = Field(..., gt=0.0)
    annual_cloud_ infrastructure_spend_usd: float = Field(..., ge=0.0)
    estimated_unoptimized_spend_ratio: float = Field(default=0.22, ge=0.0, le=1.0)

class ProductivityBaseline(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    total_impacted_ftes: int = Field(..., gt=0)
    fully_burdened_hourly_rate_usd: float = Field(..., gt=0.0)
    annual_working_hours_per_fte: int = Field(default=1920, gt=0)

class RegulatoryBaseline(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    annual_global_turnover_usd: float = Field(..., gt=0.0)
    compromised_record_unit_cost_usd: float = Field(default=165.0, ge=0.0)
    total_pii_records_managed: int = Field(..., ge=0)

class PolymorphicFinancialTelemetry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    
    currency_iso: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    industry_vertical: IndustryVertical
    availability: AvailabilityBaseline
    capital_efficiency: CapitalEfficiencyBaseline
    productivity: ProductivityBaseline
    regulatory: RegulatoryBaseline

    @model_validator(mode="after")
    def validate_macroeconomic_coherence(self) -> Self:
        if self.capital_efficiency.annual_cloud_infrastructure_spend_usd > self.capital_efficiency.annual_it_opex_usd:
            raise ValueError("Actuarial Incoherence: Cloud spend cannot exceed total IT OPEX.")
        return self
```

---

## PHASE 3: ACTUARIAL ENGINE REFACTORING (ADTs & STRATEGY PATTERN)

### 3.1 Architectural Objective
Refactor `src/assessment_engine/domain/actuarial/` to use **Pydantic Discriminated Unions (Algebraic Data Types)** for the output vectors and the **Strategy Pattern** for the Open FAIR calculators. Each archetype uses distinct, mathematically rigorous Open FAIR variables:

*   **Outage:** $ALE = TEF \times Vuln \times (Hourly\_Rev \times MTTR)$
*   **Capital Inefficiency:** $ALE = Annual\_Spend \times Unoptimized\_Ratio \times (1 - Maturity\_Factor)$
*   **Productivity Toil:** $ALE = FTEs \times Hourly\_Rate \times Annual\_Hours \times Toil\_Friction\_Coefficient$
*   **Regulatory Breach:** $ALE = LEF \times ((Global\_Turnover \times Regulatory\_Cap\_Ratio) + (Records \times Unit\_Cost))$

### 3.2 Architectural Contract (`src/assessment_engine/domain/actuarial/vectors.py`)

```python
from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field, ConfigDict
from abc import ABC, abstractmethod
from assessment_engine.domain.taxonomy.archetype_registry import LossArchetypeType

class BaseEconomicLossVector(BaseModel, ABC):
    model_config = ConfigDict(frozen=True, extra="forbid")
    
    annualized_loss_expectancy_usd: float = Field(..., ge=0.0)
    probable_loss_magnitude_usd: float = Field(..., ge=0.0)
    loss_event_frequency_annual: float = Field(..., ge=0.0)
    confidence_interval_95_low_usd: float = Field(..., ge=0.0)
    confidence_interval_95_high_usd: float = Field(..., ge=0.0)

class AvailabilityOutageVector(BaseEconomicLossVector):
    archetype: Literal[LossArchetypeType.AVAILABILITY_OUTAGE] = LossArchetypeType.AVAILABILITY_OUTAGE
    projected_annual_downtime_hours: float = Field(..., ge=0.0)
    revenue_burn_rate_per_hour_usd: float = Field(..., gt=0.0)

class CapitalInefficiencyVector(BaseEconomicLossVector):
    archetype: Literal[LossArchetypeType.CAPITAL_INEFFICIENCY] = LossArchetypeType.CAPITAL_INEFFICIENCY
    annual_addressable_waste_usd: float = Field(..., ge=0.0)
    inefficiency_leakage_rate_pct: float = Field(..., ge=0.0, le=100.0)

class ProductivityToilVector(BaseEconomicLossVector):
    archetype: Literal[LossArchetypeType.PRODUCTIVITY_TOIL] = LossArchetypeType.PRODUCTIVITY_TOIL
    annual_hours_lost_to_toil: float = Field(..., ge=0.0)
    equivalent_fte_capacity_burned: float = Field(..., ge=0.0)

class RegulatoryBreachVector(BaseEconomicLossVector):
    archetype: Literal[LossArchetypeType.REGULATORY_AND_BREACH] = LossArchetypeType.REGULATORY_AND_BREACH
     statutory_penalty_exposure_usd: float = Field(..., ge=0.0)
    remediation_and_forensic_cost_usd: float = Field(..., ge=0.0)

# The Algebraic Data Type (Discriminated Union)
PolymorphicLossVector = Annotated[
    Union[
        AvailabilityOutageVector,
        CapitalInefficiencyVector,
        ProductivityToilVector,
        RegulatoryBreachVector
    ],
    Field(discriminator="archetype")
]
```

### 3.3 Abstract Calculator Strategy (`src/assessment_engine/domain/actuarial/calculators.py`)

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from assessment_engine.domain.models.telemetry import PolymorphicFinancialTelemetry
from assessment_engine.domain.actuarial.vectors import BaseEconomicLossVector

TVector = TypeVar("TVector", bound=BaseEconomicLossVector)

class OpenFairActuarialStrategy(ABC, Generic[TVector]):
    @abstractmethod
    def calculate_ale(
        self,
        telemetry: PolymorphicFinancialTelemetry,
        tower_maturity_score: float, # 1.0 to 5.0
        finding_severity_weights: list[float]
    ) -> TVector:
        """Executes pure, side-effect-free actuarial math for a specific archetype."""
        pass
```

---

## PHASE 4: AST COMPILER & NARRATIVE AGNOSTICISM

### 4.1 Architectural Objective
Purge all hardcoded English/Spanish strings and outage assumptions from `payload_to_ast.py` and the LLM prompt generators. The Abstract Syntax Tree (AST) must consume the `PolymorphicLossVector` using Structural Pattern Matching (`match/case` in Python 3.11+) and emit **Locale-Agnostic Semantic Tokens**. Localization into Spanish, English, German, or Japanese happens strictly at the final presentation rendering boundary.

### 4.2 AST Semantic Node Contract (`src/assessment_engine/compiler/ast_nodes.py`)

```python
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any
from assessment_engine.domain.actuarial.vectors import PolymorphicLossVector

class ActuarialNarrativeContextNode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    
    semantic_template_id: str
    primary_metric_label_key: str
    primary_metric_value: float
    secondary_metric_label_key: str
    secondary_metric_value: float
    llm_framing_directive_key: str
    raw_vector: PolymorphicLossVector

def compile_actuarial_ast_node(vector: PolymorphicLossVector) -> ActuarialNarrativeContextNode:
    match vector:
        case AvailabilityOutageVector():
            return ActuarialNarrativeContextNode(
                semantic_template_id="TPL_ACTUARIAL_OUTAGE",
                primary_metric_label_key="I18N_METRIC_DOWNTIME_HOURS",
                primary_metric_value=vector.projected_annual_downtime_hours,
                secondary_metric_label_key="I18N_METRIC_HOURLY_BURN_USD",
                secondary_metric_value=vector.revenue_burn_rate_per_hour_usd,
                llm_framing_directive_key="DIRECTIVE_FRAME_AS_OPERATIONAL_HALT",
                raw_vector=vector
            )
        case CapitalInefficiencyVector():
            return ActuarialNarrativeContextNode(
                semantic_template_id="TPL_ACTUARIAL_CAP_INEFFICIENCY",
                primary_metric_label_key="I18N_METRIC_ADDRESSABLE_WASTE_USD",
                primary_metric_value=vector.annual_addressable_waste_usd,
                secondary_metric_label_key="I18N_METRIC_LEAKAGE_RATE_PCT",
                secondary_metric_value=vector.inefficiency_leakage_rate_pct,
                llm_framing_directive_key="DIRECTIVE_FRAME_AS_OPEX_CAPITAL_EROSION",
                raw_vector=vector
            )
        case ProductivityToilVector():
            return ActuarialNarrativeContextNode(
                semantic_template_id="TPL_ACTUARIAL_PRODUCTIVITY_TOIL",
                primary_metric_label_key="I18N_METRIC_FTE_CAPACITY_BURNED",
                primary_metric_value=vector.equivalent_fte_capacity_burned,
                secondary_metric_label_key="I18N_METRIC_ANNUAL_TOIL_HOURS",
                secondary_metric_value=vector.annual_hours_lost_to_toil,
                llm_framing_directive_key="DIRECTIVE_FRAME_AS_HUMAN_CAPITAL_DRAG",
                raw_vector=vector
            )
        case RegulatoryBreachVector():
            return ActuarialNarrativeContextNode(
                semantic_template_id="TPL_ACTUARIAL_REGULATORY_BREACH",
                primary_metric_label_key="I18N_METRIC_STATUTORY_PENALTY_USD",
                primary_metric_value=vector.statutory_penalty_exposure_usd,
                secondary_metric_label_key="I18N_METRIC_FORENSIC_REMEDIATION_USD",
                secondary_metric_value=vector.remediation_and_forensic_cost_usd,
                llm_framing_directive_key="DIRECTIVE_FRAME_AS_COMPLIANCE_LIABILITY",
                raw_vector=vector
            )
```

### 4.3 Dynamic LLM System Prompt Injection
The LLM prompt builder will receive the `llm_framing_directive_key` resolved against an externalized `directives_en.yaml` (Prompting is always executed in English for maximum LLM reasoning fidelity, with target output language specified via an isolated `output_locale: es_ES | en_US | ...` parameter).
*   **FinOps Prompt Directive:** *"FORBIDDEN: Do not mention system outages, downtime, or clearing halts. Frame all financial exposure strictly as unoptimized cloud capital leakage, zombie infrastructure spend, and EBITDA margin compression."*

---

## PHASE 5: SUPREME QUALITY GATES & FORENSIC VERIFICATION

To guarantee **0% regressions** and **100% mathematical determinism**, no code will merge without passing the following automated verification gates:

### 5.1 Static & Structural Gates
1. **`mypy --strict`:** 100% type coverage. Zero `Any` types permitted in `domain/actuarial/`. Exhaustiveness checking enforced on all `match/case` blocks over `PolymorphicLossVector`.
2. **Linguistic Sovereignty Linter:** A custom pre-commit AST/Regex scanner that fails the build if a single Spanish word or hardcoded currency symbol (`$`, `€`) is detected inside `.py` files.
3. **Pydantic Strictness:** All domain models enforce `ConfigDict(frozen=True, extra="forbid", strict=True)`. Any unmapped JSON key or implicit type coercion raises an immediate `ValidationError`.

### 5.2 Pytest Verification Suite (`tests/unit/domain/actuarial/`)

1. **`test_polymorphic_monotonicity` (Property-Based Testing via `hypothesis`):**
   *   *Invariant:* Across all 4 calculators, if `tower_maturity_score` increases (e.g., from `1.5` to `4.2`) while holding telemetry constant, `annualized_loss_expectancy_usd` **must strictly decrease**.
2. **`test_scale_invariance_matrix` (Parameterized Fixtures):**
   *   *Fixture 1 (Mid-Market Retail):* $15M turnover, 100 FTEs, $200k Cloud Spend.
   *   *Fixture 2 (Tier-1 Global Bank):* $40B turnover, 65,000 FTEs, $500M Cloud Spend.
   *   *Assertion:* Verify that the engine produces proportional, bounded ALE numbers without floating-point overflow, negative numbers, or NaN values, and that `ALE <= Total_Addressable_Baseline` (e.g., FinOps waste can never exceed 100% of total Cloud Spend).
3. **`test_ast_narrative_contamination_guard`:**
   *   *Assertion:* Compile a full AST for `T08_FINOPS` and `T09_WORKPLACE`. Assert that the resulting AST nodes and compiled prompt payloads contain **zero occurrences** of the tokens `["outage", "downtime", "mttr", "clearing", "halt"]`.
4. **`test_adt_roundtrip_serialization`:**
   *   *Assertion:* Serialize every variant of `PolymorphicLossVector` to JSON and deserialize back through the parent container model. Verify exact type reconstruction via the `archetype` discriminator.

---

## EXECUTION SEQUENCE SUMMARY

1. **Step 1 (Contracts & Taxonomy):** Implement `archetype_registry.py`, `telemetry.py`, and external `taxonomy_v2.yaml`. Run `mypy --strict`.
2. **Step 2 (Math & ADTs):** Implement `vectors.py` and the four concrete `OpenFairActuarialStrategy` subclasses. Pass `hypothesis` monotonicity tests.
3. **Step 3 (Compiler & Prompts):** Refactor `payload_to_ast.py` to use `compile_actuarial_ast_node` and update prompt templates to consume semantic directives.
4. **Step 4 (End-to-End Forensic Audit):** Run the complete pipeline against the Tier-1 Bank and Mid-Size Retail fixtures in both `en_US` and `es_ES` output locales. Verify zero narrative hallucinations.

**Awaiting your authorization to initiate Phase 1 implementation.**