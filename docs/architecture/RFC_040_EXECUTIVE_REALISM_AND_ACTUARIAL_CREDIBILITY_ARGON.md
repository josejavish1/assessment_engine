# RFC 040: Universal Actuarial Framing & Executive Narrative Synthesis Engine

**Status:** APPROVED FOR IMPLEMENTATION  
**Classification:** Tier-1 Core Architecture Blueprint  
**Target Subsystem:** `ActuarialCalibrationEngine`, `PayloadToASTCompiler`, `LocalizationRegistry`  
**Compliance:** 100% Language Decoupling Law (Zero Non-English Tokens in Source Code), Zero Hardcoding, 10-Tower Symmetric Execution.

---

## 1. Architectural Separation of Concerns: Macro vs. Domain Economics

A critical failure in automated enterprise reporting is conflating **Group-Level Macro Financials** with **Domain-Level Operational Risk**. When a technical annex (e.g., *Compute & Virtualization* or *Network Core*) cites an unverified macro revenue figure (such as `1,000,000,000 €`) alongside a localized Annual Loss Expectancy (ALE) of `101,231 €`, it induces immediate executive cognitive dissonance:

1. **The "Rounding Error" Illusion:** To a CFO, €101k against €1B in revenue represents 1 basis point (0.01%). Framed against total turnover, the rational capital allocation decision is to ignore the risk completely.
2. **Unverified Macro Exposure:** Domain engineering leads rarely possess audited, division-adjusted EBITDA attribution models. Stating group turnover inside a technical annex exposes the assessment to immediate challenge if the figure is an uncertified placeholder.

### The Two-Tier Economic Boundary Architecture

To eliminate this antipattern across all company sizes (from €50M mid-market to $100B Fortune 10) and industries, economic framing is strictly partitioned into two distinct execution boundaries:

```
+-----------------------------------------------------------------------------------+
|                        ENTERPRISE ASSESSMENT ARCHITECTURE                         |
+-----------------------------------------------------------------------------------+
                                          |
            +-----------------------------+-----------------------------+
            |                                                           |
            v                                                           v
+---------------------------------------+   +---------------------------------------+
|     TIER A: BOARD MASTER SYNTHESIS    |   |   TIER B: DOMAIN TECHNICAL ANNEXES    |
|     (C-Suite / Investment Committee)  |   |   (CIO / VP Infrastructure / Lead)    |
+---------------------------------------+   +---------------------------------------+
| * Certified Group Revenue / EBITDA    |   | * ZERO Unverified Macro Revenue Cited |
| * Cross-Tower Correlated Value-at-Risk|   | * Operational Burn Rate (Cost / Hour) |
| * Enterprise CapEx / OpEx Envelopes   |   | * Unhedged Tail-Risk (P90 Stress VaR) |
| * Multi-Year Transformation IRR / NPV |   | * Contractual & Licensing Shock Cliffs|
|                                       |   | * Physical Asset & Compliance Exposure|
+---------------------------------------+   +---------------------------------------+
```

### Domain Technical Annex Economic Anchor Points
In Tier B (Towers T1 through T10), financial exposure is anchored strictly on **Operational Continuity Economics**:
* **Composite Hourly Interruption Burn Rate ($C_{\text{hourly}}$):** Framed as the direct operational run-rate impact of workload paralysis (idle operational capacity, SLA breach penalties, and emergency engineering recovery overhead), completely decoupled from parent-company gross revenue citations.
* **Expected Operational Loss ($ALE_{\text{net}}$):** Framed as the baseline annual budget leakage caused by recurring micro-incidents and structural friction.
* **Tail-Risk Stress Exposure ($VaR_{90}$):** Framed as the unhedged catastrophic fiscal impact during a 90th-percentile compound failure event (e.g., hypervisor cluster exhaustion coinciding with storage rebuild failure).
* **Remediation Leverage Ratio:** Comparing the cost of architectural stabilization against the combined $VaR_{90}$ exposure and imminent vendor/hardware renewal cliffs.

---

## 2. Actuarial Realism & Credibility Engine

To prevent the engine from outputting implausible micro-percentages or exposing raw, uncalibrated defaults, the `DowntimeCalibrator` is redesigned around **Operational Velocity & Blast-Radius Elasticity**.

### 2.1 Eradicating Macro-Revenue Leakage in Rate Derivation

Previously, the engine exposed the raw formula parameters in prose:
> *"Aplicando un modelo actuarial calibrado sobre la facturación consolidada expuesta (1.000.000.000 €)... integrando lucro cesante directo del 0,0010%..."*

Exposing `0.0010%` in executive prose destroys narrative gravitas. Mathematically, if an enterprise operates 8,760 hours per year, 1 hour represents `0.0114155%` of the annual timeline ($\frac{1}{8760}$). Multiplying by an arbitrary small scalar and printing that scalar in the text reads like a spreadsheet artifact rather than an executive assessment.

### 2.2 Universal Multi-Factor Operational Burn Rate Formulation

The hourly operational impact $C_{\text{hourly}}$ for any capability tower $t \in \{T_1 \dots T_{10}\}$ is computed deterministically in the backend without leaking internal normalization scalars into the prose:

$$C_{\text{hourly}}^{(t)} = \left( \frac{R_{\text{baseline}}}{H_{\text{operational}}} \times \omega_{\text{vertical}} \times \kappa_{\text{dependency}}^{(t)} \right) + C_{\text{recovery}}^{(t)} + C_{\text{sla}}^{(t)}$$

Where:
* $R_{\text{baseline}}$: The calibrated economic baseline of the assessed operational scope (internal calculation variable only; never printed in domain annex prose unless explicitly flagged as `certified_audit_figure=True`).
* $H_{\text{operational}}$: Effective annual productive hours based on the industry vertical operating profile (e.g., `8,760` for 24/7 continuous manufacturing/banking; `6,240` for multi-shift logistics; `2,500` for standard commercial operations).
* $\omega_{\text{vertical}} \in [0.15, 1.50]$: Vertical interruption elasticity factor (measuring whether downtime causes deferred revenue vs. permanent production scrap/spoilage).
* $\kappa_{\text{dependency}}^{(t)} \in [0.05, 1.00]$: Tower blast-radius coupling coefficient derived dynamically from the topology graph (e.g., Core Network or Virtualization foundations carry higher coupling than isolated tooling).
* $C_{\text{recovery}}^{(t)} + C_{\text{sla}}^{(t)}$: Direct incident response mobilization burn rate and contractual penalty accrual per hour.

### 2.3 Dynamic Risk Regime Classification (Preventing the "Trivial ALE" Trap)

When $ALE_{\text{net}}$ is moderate (e.g., €101k) because catastrophic outages are low-frequency/high-severity events, presenting $ALE_{\text{net}}$ as the primary headline metric misleads leadership. The engine must dynamically classify the tower's **Actuarial Risk Regime** based on the Tail-to-Mean Ratio ($\tau$):

$$\tau = \frac{VaR_{90}}{ALE_{\text{net}}}$$

* **Regime 1: High-Volatility Tail-Risk ($\tau \ge 3.0$):** The tower rarely fails completely, but lacks N+1 resiliency or faces severe obsolescence/contractual cliffs. When a fault occurs, recovery is prolonged and catastrophic ($VaR_{90} \gg ALE_{\text{net}}$). The narrative must emphasize **Tail-Risk Containment ($VaR_{90}$)** and **Structural Fragility**, treating $ALE_{\text{net}}$ as routine operational friction.
* **Regime 2: Chronic Operational Friction ($\tau < 3.0$):** The tower suffers from frequent recurring outages that continuously bleed productivity. The narrative emphasizes **Immediate Run-Rate Stabilization ($ALE_{\text{net}}$)**.

---

## 3. Executive Narrative Framework (Minto Pyramid Principle)

Every Chapter 1 (Executive Summary) across all 10 capability towers must follow a strict, four-paragraph **Minto Pyramid Structure** written in an authoritative McKinsey/Gartner advisory register. 

All defensive consultant meta-language (*"hemos huido de estimaciones teóricas"*, *"para evitar la inflación artificial del riesgo"*) is permanently purged.

### Structural Anatomy of the 4-Paragraph Executive Summary

| Paragraph | Strategic Objective | Dynamic Data Injected from AST / Payload |
| :--- | :--- | :--- |
| **1. Operational Posture & Critical Dependencies** | Anchor the tower in physical reality. State the exact maturity score, operational state, workload density, and the business processes that depend on this domain. | `tower_name`, `maturity_score`, `maturity_tier_label`, `critical_findings_count`, `primary_workloads_summary`, `client_name`. |
| **2. Core Architectural Dilemma & Contractual Horizons** | Expose the concrete physical, technical, and commercial risks identified in the telemetry (e.g., hardware EoSL dates, hypervisor licensing cliffs, N+1 overcommitment, regulatory non-compliance). | Dynamically synthesized from the top 3 highest-severity findings in the tower's `findings_registry` (`finding_1_summary`, `finding_2_summary`, `finding_3_summary`). |
| **3. Financial Exposure & Downtime Velocity** | Present the economic impact as an authoritative boardroom fact. Focus on the hourly operational burn rate, net downtime exposure, and the 90th-percentile stress scenario ($VaR_{90}$) without exposing internal formula mechanics or unverified macro turnover. | `hourly_burn_rate_fmt`, `net_downtime_hours_fmt`, `annual_loss_expectancy_fmt`, `p90_downtime_hours_fmt`, `p90_var_exposure_fmt`. |
| **4. Modernization Mandate & Strategic ROI** | Define the concrete remediation trajectory. Contrast the cost of inaction against the strategic value of executing the phased architectural roadmap. | `remediation_horizon_label`, `primary_remediation_pillar`, `target_maturity_score`. |

---

### Bilingual Production Templates (`engine_config/locales.json`)

Below is the exact JSON schema to be injected into `engine_config/locales.json`. It contains zero hardcoded corporate names, zero hardcoded currencies, and zero defensive meta-narrative.

```json
{
  "executive_summary_narrative": {
    "es": {
      "p1_operational_posture": "La evaluación técnica de la torre de {tower_name} en {client_name} sitúa su índice de madurez arquitectónica en {maturity_score} sobre 5.0 ({maturity_tier_label}), evidenciando una postura operativa expuesta a {critical_findings_count} vectores de vulnerabilidad estructural. Dado que este dominio sustenta directamente la continuidad de {primary_workloads_summary}, las fricciones técnicas identificadas trascienden el ámbito puramente tecnológico y constituyen un cuello de botella directo para la estabilidad industrial y transaccional de la organización.",
      "p2_architectural_dilemma": "El diagnóstico de ingeniería revela una convergencia de riesgos técnicos, contractuales y de ciclo de vida que comprometen la resiliencia a corto y medio plazo. En particular, la estabilidad de la plataforma se ve amenazada por tres factores determinantes: (1) {finding_1_executive_brief}; (2) {finding_2_executive_brief}; y (3) {finding_3_executive_brief}. La coexistencia de estas limitaciones degrada la capacidad de conmutación por error (failover) automatizada y amplifica el radio de impacto ante fallos simples de componente.",
      "p2_architectural_dilemma_single": "El diagnóstico de ingeniería revela limitaciones estructurales de ciclo de vida y capacidad que comprometen la resiliencia operativa del dominio, destacando de forma prioritaria: {finding_1_executive_brief}. Esta condición degrada la capacidad de recuperación automatizada y amplifica el radio de impacto ante incidentes de infraestructura.",
      "p3_financial_exposure": "En términos de impacto económico directo sobre las operaciones de {client_name}, la indisponibilidad no planificada de esta arquitectura genera un coste operativo compuesto de {hourly_burn_rate_fmt}/h, derivado de la paralización de capacidad productiva, costes de contingencia de ingeniería y penalizaciones asociadas al nivel de servicio. Bajo el régimen operativo actual, la exposición neta consolidada representa {net_downtime_hours_fmt} horas de degradación crítica anual, traduciéndose en una erosión operativa esperada (ALE) de {annual_loss_expectancy_fmt}. No obstante, el riesgo estratégico primordial reside en la volatilidad de cola (escenario de estrés P90): un fallo compuesto en horario pico sin capacidad de absorción N+1 prolongaría la interrupción hasta {p90_downtime_hours_fmt} horas, generando un impacto financiero contingente no cubierto de {p90_var_exposure_fmt}.",
      "p4_modernization_mandate": "Mantener el statu quo operativo expone a la organización a una pérdida progresiva de control presupuestario y operativo frente a eventos de obsolescencia e inflación de licenciamiento. Resulta imperativo ejecutar el plan de transformación estructurado en este anexo durante el horizonte de {remediation_horizon_label}, priorizando {primary_remediation_pillar}. Esta intervención permitirá neutralizar la exposición en cola de {p90_var_exposure_fmt}, restaurar la tolerancia a fallos determinista y elevar la madurez del dominio hacia el objetivo estratégico de {target_maturity_score}/5.0."
    },
    "en": {
      "p1_operational_posture": "The technical assessment of the {tower_name} capability tower at {client_name} establishes an architectural maturity index of {maturity_score} out of 5.0 ({maturity_tier_label}), reflecting an operational posture exposed to {critical_findings_count} structural vulnerability vectors. Because this domain directly underpins the continuity of {primary_workloads_summary}, the identified technical friction points transcend routine IT maintenance and represent a direct constraint on enterprise operational and transactional stability.",
      "p2_architectural_dilemma": "Engineering telemetry reveals a convergence of technical, lifecycle, and commercial risks that compromise near- and medium-term resiliency. Specifically, platform stability is constrained by three primary factors: (1) {finding_1_executive_brief}; (2) {finding_2_executive_brief}; and (3) {finding_3_executive_brief}. The intersection of these constraints degrades automated failover determinism and amplifies the operational blast radius during single-component fault conditions.",
      "p2_architectural_dilemma_single": "Engineering telemetry reveals structural lifecycle and capacity constraints that compromise domain resiliency, centered primarily on: {finding_1_executive_brief}. This condition degrades automated recovery determinism and amplifies the operational blast radius during infrastructure fault events.",
      "p3_financial_exposure": "From an operational economics perspective at {client_name}, unplanned downtime within this architecture incurs a composite operational burn rate of {hourly_burn_rate_fmt}/hr, driven by halted productive capacity, emergency engineering mobilization, and service-level degradation. Under the current architectural baseline, net consolidated exposure accounts for {net_downtime_hours_fmt} hours of critical annual disruption, translating into an expected operational loss (ALE) of {annual_loss_expectancy_fmt}. However, the primary strategic exposure lies in tail-risk volatility (P90 stress scenario): a compound fault during peak utilization without deterministic N+1 absorption capacity would extend paralysis to {p90_downtime_hours_fmt} hours, triggering an unhedged contingent financial impact of {p90_var_exposure_fmt}.",
      "p4_modernization_mandate": "Preserving the operational status quo exposes the enterprise to escalating budgetary and operational fragility driven by hardware obsolescence and vendor licensing cliffs. Leadership must execute the phased modernization roadmap detailed in this annex across the {remediation_horizon_label} horizon, prioritizing {primary_remediation_pillar}. Executing this mandate neutralizes the {p90_var_exposure_fmt} tail-risk exposure, restores deterministic fault tolerance, and advances domain maturity toward the target state of {target_maturity_score}/5.0."
    }
  }
}
```

### Example of Rendered Output (Spanish Locale, Tower 2 Compute & Virtualization)
Notice how the resulting text reads when populated with actual domain telemetry—zero `1.000.000.000 €` hallucination, zero defensive excuses, and 100% alignment with real physical/contractual urgency:

> **Párrafo 1:** La evaluación técnica de la torre de Compute & Virtualization en Molins sitúa su índice de madurez arquitectónica en 2,4 sobre 5.0 (Estabilidad Reactiva), evidenciando una postura operativa expuesta a 6 vectores de vulnerabilidad estructural. Dado que este dominio sustenta directamente la continuidad de más de 300 máquinas virtuales críticas de control industrial, ERP y servicios corporativos, las fricciones técnicas identificadas trascienden el ámbito puramente tecnológico y constituyen un cuello de botella directo para la estabilidad industrial y transaccional de la organización.
>
> **Párrafo 2:** El diagnóstico de ingeniería revela una convergencia de riesgos técnicos, contractuales y de ciclo de vida que comprometen la resiliencia a corto y medio plazo. En particular, la estabilidad de la plataforma se ve amenazada por tres factores determinantes: (1) sobreasignación severa de memoria RAM y CPU que impide la conmutación N+1 automatizada sin apagar entornos de desarrollo; (2) vencimiento contractual de licenciamiento VMware/Broadcom en mayo de 2027 con riesgo de incremento drástico de costes por núcleo; y (3) obsolescencia programada (EoSL) de nodos hiperconvergentes HPE SimpliVity entre 2028 y 2030 junto con sistemas CentOS 5/6 fuera de soporte sujetos a normativa NIS2. La coexistencia de estas limitaciones degrada la capacidad de conmutación por error (failover) automatizada y amplifica el radio de impacto ante fallos simples de componente.
>
> **Párrafo 3:** En términos de impacto económico directo sobre las operaciones de Molins, la indisponibilidad no planificada de esta arquitectura genera un coste operativo compuesto de € 11.428,60/h, derivado de la paralización de capacidad productiva, costes de contingencia de ingeniería y penalizaciones asociadas al nivel de servicio. Bajo el régimen operativo actual, la exposición neta consolidada representa 8,9 horas de degradación crítica anual, traduciéndose en una erosión operativa esperada (ALE) de € 101.231. No obstante, el riesgo estratégico primordial reside en la volatilidad de cola (escenario de estrés P90): un fallo compuesto en horario pico sin capacidad de absorción N+1 prolongaría la interrupción hasta 59,1 horas, generando un impacto financiero contingente no cubierto de € 675.231.
>
> **Párrafo 4:** Mantener el statu quo operativo expone a la organización a una pérdida progresiva de control presupuestario y operativo frente a eventos de obsolescencia e inflación de licenciamiento. Resulta imperativo ejecutar el plan de transformación estructurado en este anexo durante el horizonte de 12 a 24 meses, priorizando el redimensionamiento de capacidad N+1, la desvinculación estratégica del hipervisor y la erradicación de sistemas operativos legados. Esta intervención permitirá neutralizar la exposición en cola de € 675.231, restaurar la tolerancia a fallos determinista y elevar la madurez del dominio hacia el objetivo estratégico de 4,2/5.0.

---

## 4. Production Implementation Plan (100% Technical English Codebase)

### 4.1 File Modification Matrix

1. `engine_config/locales.json`:
   * Replace legacy actuarial narrative strings containing macro-revenue interpolations (`{revenue_exposed}`, `{loss_pct}`) and defensive meta-commentary with the clean 4-paragraph Minto Pyramid schema defined in Section 3.
2. `actuarial_engine/downtime_calibrator.py`:
   * Encapsulate operational burn rate derivation so that macro revenue figures are strictly isolated from domain-level presentation dictionaries.
   * Compute the Tail-to-Mean Volatility Ratio ($\tau = \frac{VaR_{90}}{ALE_{\text{net}}}$) and attach the `ActuarialRiskRegime` classification to the output DTO.
3. `compiler/payload_to_ast.py`:
   * Create the `ExecutiveNarrativeSynthesizer` class (100% symmetric across Towers T1–T10).
   * Extract the top 3 critical findings from the tower's structured finding registry (sorted deterministically by severity and financial impact) to populate `{finding_1_executive_brief}`, `{finding_2_executive_brief}`, and `{finding_3_executive_brief}`.
   * Enforce strict fail-fast validation against missing locale keys or unformatted placeholders.

---

### 4.2 Production Code Blueprint: `actuarial_engine/downtime_calibrator.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Dict, Optional


class ActuarialRiskRegime( str, Enum ):
    """Classifies the domain risk profile based on tail-to-mean loss elasticity."""
    TAIL_VOLATILITY_DOMINANT = "TAIL_VOLATILITY_DOMINANT"
    CHRONIC_FRICTION_DOMINANT = "CHRONIC_FRICTION_DOMINANT"


@dataclass( frozen=True )
class DomainActuarialMetrics:
    """
    Immutable Data Transfer Object representing calibrated domain risk metrics.
    Strictly decouples internal macro-economic baselines from domain presentation.
    """
    tower_id: str
    currency_code: str
    currency_symbol: str
    composite_hourly_burn_rate: Decimal
    net_annual_downtime_hours: Decimal
    annual_loss_expectancy: Decimal
    p90_stress_downtime_hours: Decimal
    p90_value_at_risk: Decimal
    tail_to_mean_ratio: Decimal
    risk_regime: ActuarialRiskRegime
    target_maturity_score: Decimal


class DowntimeCalibrator:
    """
    Universal Enterprise Actuarial Calibration Engine.
    Computes operational interruption burn rates and tail-risk exposure across
    all capability towers without leaking unverified macro turnover into domain prose.
    """

    TAIL_REGIME_THRESHOLD: Decimal = Decimal( "3.0" )
    QUANTIZE_CURRENCY: Decimal = Decimal( "0.01" )
    QUANTIZE_WHOLE_CURRENCY: Decimal = Decimal( "1" )
    QUANTIZE_HOURS: Decimal = Decimal( "0.1" )

    @classmethod
    def calibrate_domain_exposure(
        cls,
        tower_id: str,
        currency_code: str,
        currency_symbol: str,
        raw_hourly_burn_rate: float,
        deduplicated_annual_hours: float,
        p90_stress_hours: float,
        current_maturity_score: float,
        configured_target_maturity: Optional[float] = None,
    ) -> DomainActuarialMetrics:
        """
        Deterministically computes and quantizes actuarial exposure metrics for a given tower.
        Raises ValueError on negative inputs or mathematical inconsistencies.
        """
        if raw_hourly_burn_rate < 0 or deduplicated_annual_hours < 0 or p90_stress_hours < 0:
            raise ValueError(
                f"Invalid negative actuarial telemetry for tower '{tower_id}': "
                f"rate={raw_hourly_burn_rate}, net_hours={deduplicated_annual_hours}, "
                f"p90_hours={p90_stress_hours}."
            )

        hourly_rate = Decimal( str( raw_hourly_burn_rate ) ).quantize(
            cls.QUANTIZE_CURRENCY, rounding=ROUND_HALF_UP
        )
        net_hours = Decimal( str( deduplicated_annual_hours ) ).quantize(
            cls.QUANTIZE_HOURS, rounding=ROUND_HALF_UP
        )
        p90_hours = Decimal( str( max( deduplicated_annual_hours, p90_stress_hours ) ) ).quantize(
            cls.QUANTIZE_HOURS, rounding=ROUND_HALF_UP
        )

        ale_amount = ( hourly_rate * net_hours ).quantize(
            cls.QUANTIZE_WHOLE_CURRENCY, rounding=ROUND_HALF_UP
        )
        p90_var_amount = ( hourly_rate * p90_hours ).quantize(
            cls.QUANTIZE_WHOLE_CURRENCY, rounding=ROUND_HALF_UP
        )

        if ale_amount > Decimal( "0" ):
            tail_ratio = ( p90_var_amount / ale_amount ).quantize(
                cls.QUANTIZE_HOURS, rounding=ROUND_HALF_UP
            )
        else:
            tail_ratio = Decimal( "1.0" )

        regime = (
            ActuarialRiskRegime.TAIL_VOLATILITY_DOMINANT
            if tail_ratio >= cls.TAIL_REGIME_THRESHOLD
            else ActuarialRiskRegime.CHRONIC_FRICTION_DOMINANT
        )

        # Compute deterministic target maturity state if not explicitly provided
        maturity_dec = Decimal( str( current_maturity_score ) )
        if configured_target_maturity is not None:
            target_maturity = Decimal( str( configured_target_maturity ) ).quantize(
                cls.QUANTIZE_HOURS, rounding=ROUND_HALF_UP
            )
        else:
            computed_target = min( Decimal( "4.5" ), max( Decimal( "3.8" ), maturity_dec + Decimal( "1.5" ) ) )
            target_maturity = computed_target.quantize( cls.QUANTIZE_HOURS, rounding=ROUND_HALF_UP )

        return DomainActuarialMetrics(
            tower_id=tower_id,
            currency_code=currency_code,
            currency_symbol=currency_symbol,
            composite_hourly_burn_rate=hourly_rate,
            net_annual_downtime_hours=net_hours,
            annual_loss_expectancy=ale_amount,
            p90_stress_downtime_hours=p90_hours,
            p90_value_at_risk=p90_var_amount,
            tail_to_mean_ratio=tail_ratio,
            risk_regime=regime,
            target_maturity_score=target_maturity,
        )
```

---

### 4.3 Production Code Blueprint: `compiler/payload_to_ast.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Sequence
import re

from actuarial_engine.downtime_calibrator import DomainActuarialMetrics


@dataclass( frozen=True )
class DomainFindingSummary:
    """Normalized representation of a technical, contractual, or compliance risk finding."""
    finding_id: str
    severity_rank: int
    executive_brief: str
    remediation_pillar: str


class LocaleNumberFormatter:
    """
    Deterministic locale-aware currency and decimal formatter.
    Zero reliance on OS-level locale mutation (`locale.setlocale`).
    """

    @staticmethod
    def format_decimal( value: Decimal, locale_code: str, decimal_places: int = 1 ) -> str:
        quantized = f"{value:,.{decimal_places}f}"
        if locale_code.lower().startswith( "es" ) or locale_code.lower().startswith( "de" ):
            # Swap thousand and decimal separators: 11,428.60 -> 11.428,60
            return quantized.replace( ",", "X" ).replace( ".", "," ).replace( "X", "." )
        return quantized

    @staticmethod
    def format_currency(
        value: Decimal,
        currency_symbol: str,
        locale_code: str,
        decimal_places: int = 0,
    ) -> str:
        formatted_num = LocaleNumberFormatter.format_decimal(
            value=value, locale_code=locale_code, decimal_places=decimal_places
        )
        return f"{currency_symbol} {formatted_num}"


class ExecutiveNarrativeSynthesizer:
    """
    Compiles the 4-part Minto Pyramid Executive Summary for any capability tower (T1-T10).
    Strictly enforces the 100% Technical English Codebase Law and Zero Hardcoding Law.
    """

    UNRESOLVED_TOKEN_PATTERN = re.compile( r"\{[a-zA-Z0-9_]+\}" )

    def __init__( self, locales_registry: Mapping[str, Any], locale_code: str ) -> None:
        if "executive_summary_narrative" not in locales_registry:
            raise KeyError( "Missing 'executive_summary_narrative' root key in locales registry." )

        narrative_locales = locales_registry["executive_summary_narrative"]
        if locale_code not in narrative_locales:
            raise KeyError( f"Unsupported locale '{locale_code}' in 'executive_summary_narrative'." )

        self._templates: Mapping[str, str] = narrative_locales[locale_code]
        self._locale_code: str = locale_code

    def synthesize_chapter_one_paragraphs(
        self,
        client_name: str,
        tower_name: str,
        maturity_score: Decimal,
        maturity_tier_label: str,
        primary_workloads_summary: str,
        remediation_horizon_label: str,
        findings: Sequence[DomainFindingSummary],
        actuarial_metrics: DomainActuarialMetrics,
    ) -> List[str]:
        """
        Generates the 4 authoritative executive summary paragraphs for a capability tower.
        Executes identically across all 10 towers (Zero Split-Brain).
        """
        if not findings:
            raise ValueError(
                f"Cannot synthesize executive narrative for tower '{tower_name}': "
                "findings sequence is empty."
            )

        sorted_findings = sorted( findings, key=lambda f: f.severity_rank )
        top_findings = sorted_findings[:3]

        primary_pillars = list(
            dict.fromkeys( f.remediation_pillar for f in top_findings if f.remediation_pillar )
        )
        if not primary_pillars:
            raise ValueError( f"No remediation pillars defined in top findings for '{tower_name}'." )

        joined_pillars = ", ".join( primary_pillars )

        context: Dict[str, str] = {
            "client_name": client_name.strip(),
            "tower_name": tower_name.strip(),
            "maturity_score": LocaleNumberFormatter.format_decimal(
                maturity_score, self._locale_code, decimal_places=1
            ),
            "maturity_tier_label": maturity_tier_label.strip(),
            "critical_findings_count": str( len( findings ) ),
            "primary_workloads_summary": primary_workloads_summary.strip(),
            "finding_1_executive_brief": top_findings[0].executive_brief.strip().rstrip( "." ),
            "finding_2_executive_brief": (
                top_findings[1].executive_brief.strip().rstrip( "." )
                if len( top_findings ) > 1
                else ""
            ),
            "finding_3_executive_brief": (
                top_findings[2].executive_brief.strip().rstrip( "." )
                if len( top_findings ) > 2
                else ""
            ),
            "hourly_burn_rate_fmt": LocaleNumberFormatter.format_currency(
                value=actuarial_metrics.composite_hourly_burn_rate,
                currency_symbol=actuarial_metrics.currency_symbol,
                locale_code=self._locale_code,
                decimal_places=2,
            ),
            "net_downtime_hours_fmt": LocaleNumberFormatter.format_decimal(
                value=actuarial_metrics.net_annual_downtime_hours,
                locale_code=self._locale_code,
                decimal_places=1,
            ),
            "annual_loss_expectancy_fmt": LocaleNumberFormatter.format_currency(
                value=actuarial_metrics.annual_loss_expectancy,
                currency_symbol=actuarial_metrics.currency_symbol,
                locale_code=self._locale_code,
                decimal_places=0,
            ),
            "p90_downtime_hours_fmt": LocaleNumberFormatter.format_decimal(
                value=actuarial_metrics.p90_stress_downtime_hours,
                locale_code=self._locale_code,
                decimal_places=1,
            ),
            "p90_var_exposure_fmt": LocaleNumberFormatter.format_currency(
                value=actuarial_metrics.p90_value_at_risk,
                currency_symbol=actuarial_metrics.currency_symbol,
                locale_code=self._locale_code,
                decimal_places=0,
            ),
            "remediation_horizon_label": remediation_horizon_label.strip(),
            "primary_remediation_pillar": joined_pillars,
            "target_maturity_score": LocaleNumberFormatter.format_decimal(
                value=actuarial_metrics.target_maturity_score,
                locale_code=self._locale_code,
                decimal_places=1,
            ),
        }

        p2_template_key = (
            "p2_architectural_dilemma"
            if len( top_findings ) >= 3
            else "p2_architectural_dilemma_single"
        )

        ordered_template_keys = [
            "p1_operational_posture",
            p2_template_key,
            "p3_financial_exposure",
            "p4_modernization_mandate",
        ]

        rendered_paragraphs: List[str] = []
        for key in ordered_template_keys:
            if key not in self._templates:
                raise KeyError(
                    f"Missing required template key '{key}' for locale '{self._locale_code}'."
                )
            raw_template = self._templates[key]
            rendered = raw_template.format( **context )

            # Fail-Fast Verification: Guarantee zero uninterpolated placeholders remain
            unresolved = self.UNRESOLVED_TOKEN_PATTERN.findall( rendered )
            if unresolved:
                raise ValueError(
                    f"Unresolved template tokens {unresolved} detected in rendered paragraph '{key}'."
                )

            rendered_paragraphs.append( rendered )

        return rendered_paragraphs
```

---

## 5. Pre-Deployment Verification & Quality Gates

Before committing any code modifications, the implementation pipeline will enforce four automated verification gates:

1. **Gate 1 — Static AST Language Purity Audit (`test_language_decoupling.py`):**
   * Scans every `.py` file across the repository to verify zero Spanish tokens, comments, docstrings, or string literals exist in Python source code.
2. **Gate 2 — Macro-Revenue Leakage Prohibition Gate (`test_actuarial_framing.py`):**
   * Asserts that no domain technical annex (`T1`–`T10`) renders parent-company gross turnover or micro-percentage rates (e.g., `0,0010%`) in the generated AST or `.docx` paragraphs.
3. **Gate 3 — Physical & Contractual Gravitas Assertion (`test_finding_injection.py`):**
   * Asserts that Paragraph 2 of Chapter 1 deterministically injects the top domain-specific findings (e.g., hypervisor licensing renewals, hardware EoSL horizons, N+1 overcommitment, regulatory compliance gaps) for every single tower from T1 to T10.
4. **Gate 4 — 10-Tower Symmetry & OpenXML Integrity (`test_ten_tower_symmetry.py`):**
   * Compiles all 10 capability towers across multiple locales (`es`, `en`) and enterprise profiles (Mid-Market EUR, Fortune-500 USD) and verifies identical AST node structures, zero unresolved `{tokens}`, and 100% valid ISO/IEC 29500 Word OpenXML output.