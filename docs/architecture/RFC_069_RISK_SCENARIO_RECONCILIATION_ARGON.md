# RFC 069: Actuarial Reconciliation and Ontological Disambiguation of Risk Scenarios vs. Diagnostic Dimensions

**Status:** Draft / Architectural Standard  
**Component:** `tomo_asis_ast_compiler.py` (Chapter 3 Actuarial Engine)  
**Author:** Principal Enterprise Systems Architect & Lead Actuary for Technology Risk  
**Compliance Mandate:** Zero-Trust Telemetry Verification, Multi-Tenant Agnosticism, 100% Technical English Codebase  

---

## 1. Executive Summary & Root Cause Audit

An audit of Chapter 3 (Section 3.1, Table 4: *Annualized Financial Exposure by Domain*) revealed an arithmetic split-brain violation. 

### 1.1 The Ontological Conflation
The AST compiler previously conflated two distinct architectural entities within the risk metamodel:
1. **Diagnostic Dimensions (`subpillars`):** Structural assessment vectors within the capability maturity framework. Every technological domain (Tower $T_i$) contains exactly $D_i = 4$ diagnostic subpillars, yielding a constant structural cardinality of $\sum_{i=1}^{10} D_i = 40$.
2. **Actuarial Risk Scenarios (`evaluated_scenarios`):** Discrete, stochastic loss events modeled via Monte Carlo simulation (FAIR taxonomy). In the reference telemetry payload, the global portfolio comprises $S_{\text{portfolio}} = 29$ active loss scenarios partitioned across three materiality tiers (Tier 1: $7$, Tier 2: $12$, Tier 3: $10$).

Because the compiler bound the Table 4 column *"Escenarios Evaluados"* to `len(tower.subpillars)` ($4 \times 10 = 40$) while hardcoding the portfolio footer to `"29"`, the generated document exhibited a fatal $40 \neq 29$ reconciliation failure.

---

## 2. Mathematical Specification & Domain Distribution

### 2.1 Formal Conservation Law
Let $\mathcal{T} = \{T_1, T_2, \dots, T_K\}$ represent the set of $K$ technological domains ($K=10$ in standard topology). Let $S_i \in \mathbb{N}^+$ denote the count of discrete actuarial risk scenarios evaluated within domain $T_i$, and let $M_m \in \mathbb{N}^0$ denote the scenario count in Materiality Tier $m \in \{1, 2, 3\}$.

The compiler must enforce the **Bi-Directional Portfolio Conservation Identity** at runtime:

$$\sum_{i=1}^{K} S_i = \sum_{m=1}^{3} M_m = S_{\text{portfolio}}$$

### 2.2 Canonical Domain Allocation Vector ($\mathbf{S}$)
For the reference 29-scenario enterprise baseline, the actuarial scenario density per domain $S_i$ is governed by the operational surface area and threat exposure of each tower, decoupling it from the 4-subpillar diagnostic structure:

| Domain ID | Technological Domain (Canonical English Taxonomy) | Diagnostic Subpillars ($D_i$) | Actuarial Risk Scenarios ($S_i$) | Primary Risk Concentration |
| :--- | :--- | :---: | :---: | :--- |
| **T1** | Enterprise Architecture & Governance | 4 | **3** | Strategic misalignment, legacy debt, governance drift |
| **T2** | Cloud Infrastructure & Hybrid Core | 4 | **4** | Multi-zone outage, hypervisor failure, IaaS misconfiguration |
| **T3** | Data Engineering, Analytics & AI | 4 | **3** | Data corruption, pipeline poisoning, regulatory PII breach |
| **T4** | Enterprise Applications & ERP Core | 4 | **2** | ERP transactional halt, monolithic core customization lock |
| **T5** | Cybersecurity & Zero-Trust Operations | 4 | **4** | Ransomware extortion, IAM compromise, lateral movement |
| **T6** | IT Service Management & SRE Operations | 4 | **3** | Incident cascade, observability blindspots, change failure |
| **T7** | Software Engineering & DevSecOps | 4 | **2** | CI/CD supply chain injection, unpatched production defects |
| **T8** | Network Topology & Edge Connectivity | 4 | **3** | SD-WAN partition, BGP/DNS hijacking, OT/IT bridge failure |
| **T9** | Digital Workplace & Endpoint Fleet | 4 | **2** | Mass endpoint bricking, identity phishing, VDI outage |
| **T10** | Third-Party Ecosystem & Vendor Risk | 4 | **3** | Critical SaaS insolvency, fourth-party concentration failure |
| **TOTAL** | **Consolidated Portfolio ($\sum$)** | **40** | **29** | $\sum_{i=1}^{10} S_i = 29 \equiv \sum_{m=1}^{3} M_m = 7 + 12 + 10 = 29$ |

### 2.3 Multi-Tenant Proportional Allocation Algorithm (Hamilton/Largest Remainder Method)
When a tenant payload provides a global scenario target $S_{\text{target}} \neq 29$ (or derives it from $\sum M_m$) without explicitly declaring per-domain counts $S_i$, the compiler dynamically computes $S_i$ using the Largest Remainder Method (Hamilton apportionment) weighted by each domain's Expected Annual Loss ($\text{ALE}_i$) or baseline catalog weights $w_i$:

1. **Weight Normalization:**
   $$w_i = \frac{\text{ALE}_i}{\sum_{j=1}^{K} \text{ALE}_j} \quad \text{(or fallback catalog prior } \frac{S_{i,\text{canonical}}}{29}\text{)}$$
2. **Exact Quota Computation (with minimum floor $S_i \ge 1$ when $S_{\text{target}} \ge K$):**
   $$q_i = 1 + w_i \cdot (S_{\text{target}} - K)$$
3. **Integer Allocation & Remainder Extraction:**
   $$S_i^{\text{floor}} = \lfloor q_i \rfloor, \quad r_i = q_i - S_i^{\text{floor}}$$
4. **Residual Distribution:**
   Let $R = S_{\text{target}} - \sum_{i=1}^{K} S_i^{\text{floor}}$. Allocate $+1$ to the $R$ domains possessing the highest fractional remainders $r_i$.

This guarantees $\sum_{i=1}^{K} S_i \equiv S_{\text{target}}$ across any arbitrary tenant portfolio size ($N \in [10, \infty)$).

---

## 3. Dynamic Telemetry Data Model

The JSON schema for `financial_telemetry` and `global_payload` is standardized to support explicit scenario counts at the domain level while preserving backward compatibility via deterministic synthesis.

```json
{
  "financial_telemetry": {
    "portfolio_summary": {
      "currency": "EUR",
      "materiality_tiers": {
        "tier_1_critical": { "scenario_count": 7, "ale_share_pct": 62.4 },
        "tier_2_severe": { "scenario_count": 12, "ale_share_pct": 28.1 },
        "tier_3_moderate": { "scenario_count": 10, "ale_share_pct": 9.5 }
      }
    },
    "domain_exposure": {
      "T1": { "evaluated_scenarios": 3, "ale_mean": 420000, "pml_99": 1850000 },
      "T2": { "evaluated_scenarios": 4, "ale_mean": 890000, "pml_99": 3400000 },
      "T3": { "evaluated_scenarios": 3, "ale_mean": 510000, "pml_99": 2100000 },
      "T4": { "evaluated_scenarios": 2, "ale_mean": 640000, "pml_99": 2750000 },
      "T5": { "evaluated_scenarios": 4, "ale_mean": 1150000, "pml_99": 4900000 },
      "T6": { "evaluated_scenarios": 3, "ale_mean": 380000, "pml_99": 1420000 },
      "T7": { "evaluated_scenarios": 2, "ale_mean": 290000, "pml_99": 1100000 },
      "T8": { "evaluated_scenarios": 3, "ale_mean": 470000, "pml_99": 1950000 },
      "T9": { "evaluated_scenarios": 2, "ale_mean": 210000, "pml_99": 880000 },
      "T10": { "evaluated_scenarios": 3, "ale_mean": 340000, "pml_99": 1520000 }
    }
  }
}
```

---

## 4. Code Implementation Blueprint (`tomo_asis_ast_compiler.py`)

All Python constructs, variable names, docstrings, and exception messages strictly adhere to the **100% Technical English Codebase** mandate. Localized output strings are isolated exclusively within presentation rendering templates.

```python
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
import math


# Canonical baseline scenario allocation across the 10 standard technology domains.
# Note: Diagnostic subpillars are fixed at 4 per domain (40 total), whereas
# actuarial risk scenarios reflect discrete FAIR Monte Carlo models (29 baseline total).
CANONICAL_DOMAIN_SCENARIO_BASELINE: Dict[str, int] = {
    "T1": 3,
    "T2": 4,
    "T3": 3,
    "T4": 2,
    "T5": 4,
    "T6": 3,
    "T7": 2,
    "T8": 3,
    "T9": 2,
    "T10": 3,
}

CANONICAL_TIER_RATIO_BASELINE: Tuple[float, float, float] = (
    7 / 29.0,   # Tier 1: Critical / Existential
    12 / 29.0,  # Tier 2: Severe Operational
    10 / 29.0,  # Tier 3: Moderate / Tactical
)


@dataclass(frozen=True)
class PortfolioScenarioLedger:
    """
    Immutable actuarial ledger enforcing strict mathematical conservation
    between domain-level risk scenarios and materiality tier distributions.
    """
    domain_scenarios: Dict[str, int]
    tier_scenarios: Dict[str, int]
    total_evaluated_scenarios: int
    total_diagnostic_subpillars: int

    def validate_conservation_law(self) -> None:
        """Verifies that domain sum and tier sum strictly equal the portfolio total."""
        domain_sum = sum(self.domain_scenarios.values())
        tier_sum = sum(self.tier_scenarios.values())

        if domain_sum != self.total_evaluated_scenarios:
            raise ValueError(
                f"Actuarial reconciliation failure: sum of domain scenarios ({domain_sum}) "
                f"does not match portfolio total ({self.total_evaluated_scenarios})."
            )
        if tier_sum != self.total_evaluated_scenarios:
            raise ValueError(
                f"Actuarial reconciliation failure: sum of materiality tier scenarios ({tier_sum}) "
                f"does not match portfolio total ({self.total_evaluated_scenarios})."
            )


class ActuarialScenarioReconciler:
    """
    Resolves and reconciles risk scenario counts across domains and materiality tiers
    for multi-tenant telemetry payloads. Prevents ontological conflation between
    diagnostic subpillars (N=40) and actuarial risk scenarios (e.g., N=29).
    """

    @staticmethod
    def apportion_by_largest_remainder(
        target_total: int,
        weights: Dict[str, float],
        enforce_minimum_one: bool = True,
    ) -> Dict[str, int]:
        """
        Applies Hamilton's Largest Remainder Method to allocate an integer total
        across keys proportionally to their weights, guaranteeing exact summation.
        """
        keys = list(weights.keys())
        num_buckets = len(keys)

        if num_buckets == 0 or target_total <= 0:
            return {k: 0 for k in keys}

        weight_sum = sum(max(0.0, w) for w in weights.values())
        if weight_sum <= 0.0:
            normalized_weights = {k: 1.0 / num_buckets for k in keys}
        else:
            normalized_weights = {k: max(0.0, weights[k]) / weight_sum for k in keys}

        if enforce_minimum_one and target_total >= num_buckets:
            distributable_pool = target_total - num_buckets
            exact_quotas = {
                k: 1.0 + (normalized_weights[k] * distributable_pool) for k in keys
            }
        else:
            exact_quotas = {k: normalized_weights[k] * target_total for k in keys}

        floor_allocations = {k: int(math.floor( exact_quotas[k])) for k in keys}
        remainders = {k: exact_quotas[k] - floor_allocations[k] for k in keys}

        shortfall = target_total - sum(floor_allocations.values())
        sorted_keys_by_remainder = sorted(
            keys, key=lambda k: (remainders[k], normalized_weights[k]), reverse=True
        )

        for i in range(shortfall):
            floor_allocations[sorted_keys_by_remainder[i]] += 1

        return floor_allocations

    @classmethod
    def resolve_portfolio_ledger(
        cls,
        towers_payload: List[Dict[str, Any]],
        financial_telemetry: Optional[Dict[str, Any]] = None,
    ) -> PortfolioScenarioLedger:
        """
        Extracts or synthesizes reconciled scenario counts from tenant telemetry.
        Guarantees 100% dynamic summation across Table 4, Table 5, and narratives.
        """
        financial_telemetry = financial_telemetry or {}
        domain_exposure_map = financial_telemetry.get("domain_exposure", {})
        portfolio_summary = financial_telemetry.get("portfolio_summary", {})
        tier_telemetry = portfolio_summary.get("materiality_tiers", {})

        domain_ids: List[str] = []
        explicit_domain_scenarios: Dict[str, int] = {}
        domain_ale_weights: Dict[str, float] = {}
        total_subpillars = 0

        for idx, tower in enumerate(towers_payload, start=1):
            domain_id = str(tower.get("id") or f"T{idx}")
            domain_ids.append(domain_id)

            # Count diagnostic subpillars separately to preserve ontological clarity
            subpillars = tower.get("subpillars", [])
            total_subpillars += len(subpillars) if isinstance(subpillars, list) else 4

            # Inspect explicit scenario count in domain telemetry or tower payload
            domain_fin = domain_exposure_map.get(domain_id, {})
            raw_scenarios = domain_fin.get(
                "evaluated_scenarios", tower.get("evaluated_scenarios")
            )
            if isinstance(raw_scenarios, int) and raw_scenarios > 0:
                explicit_domain_scenarios[domain_id] = raw_scenarios

            # Extract ALE weight for proportional fallback apportionment
            ale_val = float(
                domain_fin.get("ale_mean", tower.get("ale_mean", 0.0)) or 0.0
            )
            domain_ale_weights[domain_id] = (
                ale_val
                if ale_val > 0.0
                else float(CANONICAL_DOMAIN_SCENARIO_BASELINE.get(domain_id, 3))
            )

        # Inspect explicit tier counts
        t1_raw = tier_telemetry.get("tier_1_critical", {}).get("scenario_count")
        t2_raw = tier_telemetry.get("tier_2_severe", {}).get("scenario_count")
        t3_raw = tier_telemetry.get("tier_3_moderate", {}).get("scenario_count")
        has_explicit_tiers = all(
            isinstance(x, int) and x >= 0 for x in (t1_raw, t2_raw, t3_raw)
        ) and sum((t1_raw, t2_raw, t3_raw)) > 0

        # Case 1: All domains have explicit scenario counts in telemetry
        if len(explicit_domain_scenarios) == len(domain_ids) and len(domain_ids) > 0:
            resolved_domain_scenarios = explicit_domain_scenarios
            portfolio_total = sum(resolved_domain_scenarios.values())
        # Case 2: Tier counts or global target are explicitly provided, apportion to domains
        elif has_explicit_tiers or isinstance(
            portfolio_summary.get("total_evaluated_scenarios"), int
        ):
            portfolio_total = (
                int(t1_raw + t2_raw + t3_raw)
                if has_explicit_tiers
                else int(portfolio_summary["total_evaluated_scenarios"])
            )
            # If target matches canonical 29 and 10 standard domains exist, use canonical baseline
            if portfolio_total == sum(CANONICAL_DOMAIN_SCENARIO_BASELINE.values()) and set(
                domain_ids
            ) == set(CANONICAL_DOMAIN_SCENARIO_BASELINE.keys()):
                resolved_domain_scenarios = {
                    d_id: CANONICAL_DOMAIN_SCENARIO_BASELINE[d_id] for d_id in domain_ids
                }
            else:
                resolved_domain_scenarios = cls.apportion_by_largest_remainder(
                    target_total=portfolio_total,
                    weights=domain_ale_weights,
                    enforce_minimum_one=True,
                )
        # Case 3: Default fallback to canonical baseline (sum = 29 for 10 domains)
        else:
            resolved_domain_scenarios = {
                d_id: CANONICAL_DOMAIN_SCENARIO_BASELINE.get(d_id, 3)
                for d_id in domain_ids
            }
            portfolio_total = sum(resolved_domain_scenarios.values())

        # Reconcile Materiality Tiers against the dynamic portfolio_total
        if has_explicit_tiers and (t1_raw + t2_raw + t3_raw) == portfolio_total:
            resolved_tiers = {
                "tier_1": int(t1_raw),
                "tier_2": int(t2_raw),
                "tier_3": int(t3_raw),
            }
        else:
            tier_weights = {
                "tier_1": CANONICAL_TIER_RATIO_BASELINE[0],
                "tier_2": CANONICAL_TIER_RATIO_BASELINE[1],
                "tier_3": CANONICAL_TIER_RATIO_BASELINE[2],
            }
            resolved_tiers = cls.apportion_by_largest_remainder(
                target_total=portfolio_total,
                weights=tier_weights,
                enforce_minimum_one=False,
            )

        ledger = PortfolioScenarioLedger(
            domain_scenarios=resolved_domain_scenarios,
            tier_scenarios=resolved_tiers,
            total_evaluated_scenarios=portfolio_total,
            total_diagnostic_subpillars=total_subpillars,
        )
        ledger.validate_conservation_law()
        return ledger


def compile_chapter_3_section_3_1_ast(
    towers_payload: List[Dict[str, Any]],
    financial_telemetry: Dict[str, Any],
    currency_symbol: str = "€",
) -> Dict[str, Any]:
    """
    Compiles the AST nodes for Section 3.1 (Introductory Bridge Narrative,
    Table 4: Annualized Financial Exposure by Domain, and Table 5: 3-Tier Portfolio).
    Enforces 100% dynamic summation with zero hardcoded scenario totals.
    """
    ledger = ActuarialScenarioReconciler.resolve_portfolio_ledger(
        towers_payload=towers_payload,
        financial_telemetry=financial_telemetry,
    )

    total_scenarios_sum = sum(ledger.domain_scenarios.values())
    total_domains_count = len(towers_payload)

    table_4_rows: List[List[str]] = []
    consolidated_ale_sum = 0.0
    consolidated_pml_sum = 0.0

    domain_exposure_map = financial_telemetry.get("domain_exposure", {})

    for idx, tower in enumerate(towers_payload, start=1):
        domain_id = str(tower.get("id") or f"T{idx}")
        domain_name = str(tower.get("name", f"Domain {domain_id}"))
        domain_fin = domain_exposure_map.get(domain_id, {})

        domain_scenario_count = ledger.domain_scenarios[domain_id]
        ale_value = float(domain_fin.get("ale_mean", tower.get("ale_mean", 0.0)) or 0.0)
        pml_value = float(domain_fin.get("pml_99", tower.get("pml_99", 0.0)) or 0.0)
        risk_rating = str(domain_fin.get("rating", tower.get("risk_level", "ALTO")))

        consolidated_ale_sum += ale_value
        consolidated_pml_sum += pml_value

        table_4_rows.append([
            f"{domain_id} - {domain_name}",
            str(domain_scenario_count),  # Dynamically bound to S_i (NEVER len(subpillars))
            f"{currency_symbol}{ale_value:,.0f}",
            f"{currency_symbol}{pml_value:,.0f}",
            risk_rating,
        ])

    # Apply portfolio diversification factor if present in telemetry, else raw sum
    diversified_pml = float(
        financial_telemetry.get("portfolio_summary", {}).get(
            "diversified_pml_99", consolidated_pml_sum
        )
    )

    # Table 4 Total Row: 100% dynamically computed from `total_scenarios_sum`
    table_4_total_row: List[str] = [
        "TOTAL CONSOLIDADO (PORTAFOLIO)",
        str(total_scenarios_sum),
        f"{currency_symbol}{consolidated_ale_sum:,.0f}",
        f"{currency_symbol}{diversified_pml:,.0f}",
        "CRÍTICO",
    ]

    # Introductory Bridge Narrative: Dynamically interpolates both scenario count and subpillar count
    introductory_narrative_es = (
        f"La cuantificación actuarial del portafolio consolida {total_scenarios_sum} escenarios "
        f"de riesgo evaluados a lo largo de los {total_domains_count} dominios tecnológicos "
        f"(estructurados sobre {ledger.total_diagnostic_subpillars} dimensiones diagnósticas). "
        f"La distribución de pérdida anual esperada (ALE) y pérdida máxima probable (PML P99) "
        f"refleja la densidad estocástica real de cada torre operativa."
    )

    # Table 5 (3-Tier Portfolio Table): Reconciled against the exact same ledger
    tier_1_count = ledger.tier_scenarios["tier_1"]
    tier_2_count = ledger.tier_scenarios["tier_2"]
    tier_3_count = ledger.tier_scenarios["tier_3"]
    table_5_total_scenarios = tier_1_count + tier_2_count + tier_3_count

    table_5_rows: List[List[str]] = [
        ["Tier 1 — Riesgos Existenciales / Sistémicos", str(tier_1_count)],
        ["Tier 2 — Riesgos Operacionales Severos", str(tier_2_count)],
        ["Tier 3 — Riesgos Tácticos / Moderados", str(tier_3_count)],
    ]
    table_5_total_row: List[str] = [
        "TOTAL PORTAFOLIO DE ESCENARIOS",
        str(table_5_total_scenarios),
    ]

    return {
        "section_id": "3.1",
        "introductory_narrative": introductory_narrative_es,
        "table_4_domain_exposure": {
            "headers": [
                "Dominio Tecnológico",
                "Escenarios Evaluados",
                "Exposición Anual (ALE)",
                "Evento Extremo (PML P99)",
                "Criticidad",
            ],
            "rows": table_4_rows,
            "total_row": table_4_total_row,
        },
        "table_5_materiality_tiers": {
            "headers": [
                "Nivel de Materialidad (Tier)",
                "Escenarios Evaluados",
            ],
            "rows": table_5_rows,
            "total_row": table_5_total_row,
        },
        "reconciliation_metadata": {
            "total_evaluated_scenarios": total_scenarios_sum,
            "total_diagnostic_subpillars": ledger.total_diagnostic_subpillars,
            "conservation_verified": total_scenarios_sum == table_5_total_scenarios,
        },
    }
```

---

## 5. Verification & Zero-Trust Audit Invariants

To prevent regression in CI/CD pipelines, the compiler's AST verification gate enforces three invariants prior to PDF/DOCX serialization:

1. **Column-to-Footer Summation Invariant (Table 4):**
   $$\sum_{r=1}^{K} \text{int}(\text{Table4}[r][\text{col\_scenarios}]) \equiv \text{int}(\text{Table4}_{\text{total}}[\text{col\_scenarios}])$$
2. **Cross-Table Portfolio Invariant (Table 4 $\leftrightarrow$ Table 5):**
   $$\text{int}(\text{Table4}_{\text{total}}[\text{col\_scenarios}]) \equiv \sum_{m=1}^{3} \text{int}(\text{Table5}[m][\text{col\_scenarios}]) \equiv \text{int}(\text{Table5}_{\text{total}}[\text{col\_scenarios}])$$
3. **Ontological Separation Invariant:**
   The diagnostic dimension cardinality ($\sum D_i = 40$) is strictly segregated into `total_diagnostic_subpillars` and must never be injected into the actuarial scenario vector $\mathbf{S}$.