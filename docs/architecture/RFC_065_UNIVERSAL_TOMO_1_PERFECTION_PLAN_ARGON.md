### 1. Architectural Design & Component Breakdown

The `TomoAsisASTCompiler` must operate as a pure, stateless functional transformer within the Assessment Engine pipeline. It ingests normalized domain payloads and externalized linguistic catalogs, emitting a strictly typed Abstract Syntax Tree (`DocumentAST`) ready for rendering into `.docx` and `.pdf` formats.

```text
                         +-----------------------------------+
                         |    SSOT Assessment Payloads       |
                         | (Global, Towers, Financial, I18n) |
                         +-----------------+-----------------+
                                           |
                                           v
+-------------------------------------------------------------------------------------+
|                           TomoAsisASTCompiler (Stateless)                           |
|                                                                                     |
|  +---------------------------+   +-----------------------------------------------+  |
|  |   ActuarialReconciler     |   |             StrictI18nResolver                |  |
|  | - Largest Remainder Alloc |   | - Zero-Fallback Key Resolution                |  |
|  | - SLE * LEF Exact Match   |   | - Locale-Aware Currency & Float Formatting    |  |
|  | - CMMI Weighted vs Mean   |   | - Multi-Tenant Token Interpolation            |  |
|  +-------------+-------------+   +-----------------------+-----------------------+  |
|                |                                         |                          |
|                +--------------------+--------------------+                          |
|                                     |                                               |
|                                     v                                               |
|  +-------------------------------------------------------------------------------+  |
|  |                       Section Builders (Pure Functions)                       |  |
|  |  1. _build_executive_summary()       4. _build_domain_diagnostics()           |  |
|  |  2. _build_maturity_assessment()     5. _build_operational_dependencies()     |  |
|  |  3. _build_actuarial_risk_analysis() 6. _build_appendices()                   |  |
|  +----------------------------------+--------------------------------------------+  |
+-------------------------------------|-----------------------------------------------+
                                      |
                                      v
                         +-------------------------+
                         |   Immutable DocumentAST |
                         | (Tables, Cards, Charts) |
                         +-------------------------+
```

#### 1.1 Class Structure & Dependency Injection
All natural language strings, tenant specifics, and financial thresholds are decoupled from the Python source code.

```python
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple


@dataclass(frozen=True)
class CompilerContext:
    doc_lang: str
    currency_code: str
    currency_symbol: str
    industry_vertical: str
    benchmark_score: Decimal
    global_payload: Mapping[str, Any]
    tower_payloads: Sequence[Mapping[str, Any]]
    financial_telemetry: Mapping[str, Any]
    i18n_catalog: Mapping[str, Mapping[str, str]]
    assets_dir: Path


class StrictI18nError(KeyError):
    """Raised when a required translation key or locale is missing from the catalog."""


class ActuarialReconciliationError(ValueError):
    """Raised when domain financial allocations fail closed-form reconciliation."""
```

#### 1.2 Core Compiler Interface & Helper Methods
Every method enforces explicit parameter passing. Default values for `doc_lang` or fallback strings in translation resolution are strictly prohibited.

```python
class TomoAsisASTCompiler:
    """
    Compiles the Consolidated Volume 1 (AS-IS Baseline Diagnostic) into an immutable DocumentAST.
    Enforces strict AS-IS boundaries, actuarial reconciliation, and zero-fallback i18n.
    """

    def __init__(self, context: CompilerContext) -> None:
        self._ctx = context
        self._validate_context()
        self._reconciled_telemetry = self._reconcile_actuarial_model()

    def compile(self) -> Dict[str, Any]:
        """Entrypoint generating the complete AST node hierarchy."""
        return {
            "document_type": "TOMO_1_AS_IS_DIAGNOSTIC",
            "metadata": self._build_metadata(),
            "sections": [
                self._build_executive_summary(),
                self._build_maturity_assessment(),
                self._build_actuarial_risk_analysis(),
                self._build_domain_diagnostics(),
                self._build_operational_dependencies(),
                self._build_appendices(),
            ],
        }

    def _t(self, key: str, **kwargs: Any) -> str:
        """
        Strict translation resolver. Zero default fallbacks. Zero language conditionals.
        """
        lang_map = self._ctx.i18n_catalog.get(self._ctx.doc_lang)
        if lang_map is None:
            raise StrictI18nError(f"Unsupported locale requested: {self._ctx.doc_lang}")
        template = lang_map.get(key)
        if template is None:
            raise StrictI18nError(f"Missing translation key '{key}' for locale '{self._ctx.doc_lang}'")
        return template.format(**kwargs) if kwargs else template

    def _fmt_currency(self, amount: int | Decimal) -> str:
        """Formats integer or Decimal currency deterministically according to locale rules."""
        # Uses locale-specific separators defined in locales.json
        thousands_sep = self._t("meta.format.thousands_separator")
        quantized = int(Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        formatted_num = f"{quantized:,}".replace(",", thousands_sep)
        symbol_pos = self._t("meta.format.currency_position")
        if symbol_pos == "PREFIX":
            return f"{self._ctx.currency_symbol}{formatted_num}"
        return f"{formatted_num} {self._ctx.currency_symbol}"

    def _fmt_decimal(self, value: Decimal, places: int = 2) -> str:
        """Formats decimal metrics (CMMI scores, frequencies) using locale decimal separator."""
        dec_sep = self._t("meta.format.decimal_separator")
        q_str = "0." + ("0" * places) if places > 0 else "0"
        quantized = value.quantize(Decimal(q_str), rounding=ROUND_HALF_UP)
        return str(quantized).replace(".", dec_sep)
```

#### 1.3 Section Builders & Telemetry Resolvers
*   `_build_executive_summary()`: Renders the high-level narrative using dynamic token interpolation (`{client_name}`, `{total_ale_p50}`, `{weighted_cmmi}`, `{recurring_opex_leakage}`). Emits the 4-metric Executive KPI Summary Table differentiating statistical exposure from realized cash leakage.
*   `_build_maturity_assessment()`: Embeds `global_radar_chart.png` (verifying path existence via `self._ctx.assets_dir / "global_radar_chart.png"`). Generates Table 3 (Domain Maturity vs. Industry Benchmark), calculating `Deviation = Current_Score - Benchmark_Score`. Appends the dual-row reconciliation footer for Weighted Average vs. Simple Arithmetic Mean.
*   `_build_actuarial_risk_analysis()`: Constructs the 5x5 Open FAIR Heatmap Mosaic Table by bucketing the stochastic scenarios across 5 impact tiers and 5 probability bands. Renders the Top Corporate Systemic Risk Cards in a 3-column AST grid where $\text{ALE} = \text{round}(\text{SLE} \times \text{LEF})$ is verified.
*   `_build_domain_diagnostics()`: Iterates dynamically over `self._ctx.tower_payloads`. For each domain, emits:
    1.  A 4-column KPI strip: `Current Score`, `Operational Status` (derived from score thresholds mapped to i18n keys), `Allocated ALE P50`, and `Exposure Band`.
    2.  Sober executive narrative summarizing architectural state and capacity thresholds.
    3.  A 2-column Deep-Dive Table pairing `Evaluated Sub-pillars` against `Observed Empirical Evidence`.
    4.  Consolidates the cross-domain `Single Points of Failure (SPOF) Matrix` at the chapter close.
*   `_build_operational_dependencies()`: Renders the Cross-Tower Operational Nexus table. Maps `Source Domain`, `Dependent Domain`, `Coupling Mechanism`, and `Cascading Operational Impact` under the current architecture.
*   `_build_appendices()`: Emits the actuarial methodology notes, Open FAIR definitions, CMMI scale taxonomy, and audit disclaimer.

---

### 2. Complete Internationalization (i18n) Strategy & Key Catalog

To guarantee zero hardcoding and 100% mathematical symmetry across `es`, `en`, `pt`, `fr`, `de`, and `ja`, all text lives in `engine_config/locales.json`.

#### 2.1 Canonical Key Catalog (`es` and `en` Reference Specification)

```json
{
  "es": {
    "meta.format.thousands_separator": ".",
    "meta.format.decimal_separator": ",",
    "meta.format.currency_position": "SUFFIX",
    "doc.tomo1.title": "Diagnóstico Tecnológico y Análisis de Riesgos Operativos (Línea Base AS-IS)",
    "doc.tomo1.subtitle": "Evaluación de Madurez, Exposición Actuarial y Dependencias de Arquitectura",
    "ch1.heading": "1. Resumen Ejecutivo",
    "ch1.lead_narrative": "El presente documento establece la línea base operativa y financiera de la arquitectura tecnológica de {client_name}. El análisis evalúa la capacidad instalada, los umbrales de diseño y la exposición estadística ante eventos de interrupción operativa en el estado actual (AS-IS).",
    "ch1.table.exec_kpi.title": "Tabla 1: Síntesis de Indicadores Ejecutivos y Exposición Financiera",
    "ch1.table.exec_kpi.col.metric": "Indicador Clave",
    "ch1.table.exec_kpi.col.value": "Valor Determinado",
    "ch1.table.exec_kpi.col.nature": "Naturaleza Financiera / Operativa",
    "ch1.kpi.cmmi_weighted": "Índice de Madurez Global (Ponderado)",
    "ch1.kpi.cmmi_weighted.desc": "Media ponderada por criticidad operativa de las áreas tecnológicas (Escala CMMI 1.0 - 5.0).",
    "ch1.kpi.ale_p50": "Exposición Anualizada al Riesgo (ALE P50)",
    "ch1.kpi.ale_p50.desc": "Pérdida estadística esperada anual agregada en los {scenario_count} escenarios evaluados.",
    "ch1.kpi.cash_leakage": "Ineficiencia Operativa Recurrente (OPEX)",
    "ch1.kpi.cash_leakage.desc": "Sobrecoste anual realizado con certeza del 100% por duplicidad contractual y licenciamiento.",
    "ch1.kpi.local_outage_p90": "Impacto de Incidente Mayor Local (P90)",
    "ch1.kpi.local_outage_p90.desc": "Pérdida discreta estimada ante una interrupción prolongada en un centro operativo principal.",
    "ch1.kpi.tail_risk_p90": "Riesgo de Cola de Cartera Anual (ALE P90)",
    "ch1.kpi.tail_risk_p90.desc": "Exposición estadística anual agregada en escenarios adversos extremos a nivel corporativo.",

    "ch2.heading": "2. Nivel de Madurez Tecnológica",
    "ch2.lead_narrative": "La evaluación de madurez mide el grado de estandarización, automatización y control operativo de cada área tecnológica frente al estándar de referencia del sector ({industry_benchmark}).",
    "ch2.chart.radar.caption": "Figura 1: Comparativa de Madurez Actual (AS-IS) frente al Estándar del Sector",
    "ch2.table.maturity.title": "Tabla 2: Desglose de Madurez por Área Tecnológica",
    "ch2.table.maturity.col.domain": "Área Tecnológica",
    "ch2.table.maturity.col.weight": "Peso Relativo",
    "ch2.table.maturity.col.score": "Nivel Actual (AS-IS)",
    "ch2.table.maturity.col.benchmark": "Referencia Sectorial",
    "ch2.table.maturity.col.deviation": "Desviación",
    "ch2.table.maturity.col.status": "Estado Operativo",
    "ch2.table.maturity.footer.simple_mean": "Media Aritmética Simple (No Ponderada)",
    "ch2.table.maturity.footer.weighted_mean": "Índice de Madurez Corporativo (Media Ponderada)",
    "ch2.table.maturity.footnote": "Nota metodológica: La media aritmética simple ({simple_mean}) otorga igual peso a todas las áreas. El índice corporativo ({weighted_mean}) pondera cada área según su criticidad para la continuidad del negocio y volumen de activos gestionados.",

    "ch3.heading": "3. Impacto Económico y Análisis de Riesgos",
    "ch3.lead_narrative": "La cuantificación económica utiliza el modelo estándar Open FAIR para distinguir entre la exposición actuarial latente (probabilística) y las ineficiencias presupuestarias recurrentes (deterministas).",
    "ch3.heatmap.title": "Tabla 3: Matriz de Distribución de Escenarios de Riesgo (Open FAIR 5x5)",
    "ch3.heatmap.axis.prob": "Frecuencia Anual de Eventos (LEF)",
    "ch3.heatmap.axis.impact": "Magnitud de Pérdida por Evento (SLE)",
    "ch3.heatmap.band.vlow": "Muy Baja",
    "ch3.heatmap.band.low": "Baja",
    "ch3.heatmap.band.med": "Moderada",
    "ch3.heatmap.band.high": "Alta",
    "ch3.heatmap.band.vhigh": "Muy Alta",
    "ch3.cards.title": "Principales Escenarios de Exposición Sistémica",
    "ch3.cards.label.sle": "Pérdida por Evento (SLE)",
    "ch3.cards.label.lef": "Frecuencia Anual (LEF)",
    "ch3.cards.label.ale": "Exposición Anual (ALE P50)",
    "ch3.cards.label.events_yr": "eventos/año",
    "ch3.table.reconciliation.title": "Tabla 4: Conciliación de Exposición Actuarial por Área Tecnológica",
    "ch3.table.reconciliation.col.domain": "Área Tecnológica",
    "ch3.table.reconciliation.col.scenarios": "Escenarios",
    "ch3.table.reconciliation.col.ale_p50": "Exposición Anual (ALE P50)",
    "ch3.table.reconciliation.col.share": "Proporción del Total",
    "ch3.table.reconciliation.footer.total": "Total Exposición Actuarial Corporativa (Conciliado)",

    "ch4.heading": "4. Situación Actual por Áreas Tecnológicas",
    "ch4.lead_narrative": "A continuación se detalla el estado operativo, los límites de capacidad observados y la evidencia técnica recopilada para cada una de las áreas evaluadas.",
    "ch4.strip.score": "Madurez Actual",
    "ch4.strip.status": "Estado Operativo",
    "ch4.strip.ale": "Exposición Anual (ALE P50)",
    "ch4.strip.exposure_level": "Nivel de Exposición",
    "ch4.table.deepdive.col.subpillar": "Sub-pilar Evaluado y Capacidad",
    "ch4.table.deepdive.col.evidence": "Evidencia Empírica y Límites de Diseño Observados",
    "ch4.spof.title": "Tabla 5: Registro Consolidado de Puntos Únicos de Fallo (SPOF)",
    "ch4.spof.col.id": "ID",
    "ch4.spof.col.domain": "Área",
    "ch4.spof.col.component": "Componente / Activo",
    "ch4.spof.col.threshold": "Límite de Capacidad o Ciclo de Vida",
    "ch4.spof.col.impact": "Efecto Operativo Directo",

    "ch5.heading": "5. Relaciones y Dependencias entre Áreas",
    "ch5.lead_narrative": "La arquitectura actual presenta acoplamientos operativos entre distintas áreas. La siguiente matriz describe cómo una degradación en un área de origen se propaga hacia áreas dependientes bajo la topología existente.",
    "ch5.table.nexus.title": "Tabla 6: Matriz de Acoplamiento Operativo y Propagación de Impacto",
    "ch5.table.nexus.col.source": "Área de Origen",
    "ch5.table.nexus.col.target": "Área Dependiente",
    "ch5.table.nexus.col.mechanism": "Mecanismo de Acoplamiento Técnico",
    "ch5.table.nexus.col.propagation": "Efecto de Propagación Operativa (Estado Actual)",

    "app.heading": "Anexo: Glosario Metodológico y Alcance del Diagnóstico",
    "app.glossary.title": "Definiciones de Términos Actuariales y Técnicos",
    "app.disclaimer.title": "Nota de Alcance y Límite Diagnóstico",
    "app.disclaimer.body": "Este volumen comprende exclusivamente la evaluación de la línea base actual (AS-IS). Las arquitecturas objetivo, hojas de ruta de remediación e inversiones asociadas se desarrollan de forma independiente en el Tomo 2.",

    "status.maturity.optimal": "Operación Optimizada",
    "status.maturity.managed": "Operación Gestionada",
    "status.maturity.defined": "Operación Estandarizada",
    "status.maturity.reactive": "Operación Reactiva / Límite de Capacidad",
    "status.maturity.initial": "Operación No Estandarizada",

    "status.exposure.low": "Exposición Controlada",
    "status.exposure.moderate": "Exposición Moderada",
    "status.exposure.elevated": "Exposición Elevada",
    "status.exposure.significant": "Exposición Significativa"
  },
  "en": {
    "meta.format.thousands_separator": ",",
    "meta.format.decimal_separator": ".",
    "meta.format.currency_position": "PREFIX",
    "doc.tomo1.title": "Technology Diagnostic & Operational Risk Analysis (AS-IS Baseline)",
    "doc.tomo1.subtitle": "Maturity Assessment, Actuarial Exposure, and Architectural Dependencies",
    "ch1.heading": "1. Executive Summary",
    "ch1.lead_narrative": "This document establishes the operational and financial baseline of the technology architecture for {client_name}. The assessment evaluates installed capacity, design thresholds, and statistical exposure to operational disruption events in the current state (AS-IS).",
    "ch1.table.exec_kpi.title": "Table 1: Executive Indicator Synthesis and Financial Exposure",
    "ch1.table.exec_kpi.col.metric": "Key Indicator",
    "ch1.table.exec_kpi.col.value": "Determined Value",
    "ch1.table.exec_kpi.col.nature": "Financial / Operational Nature",
    "ch1.kpi.cmmi_weighted": "Global Maturity Index (Weighted)",
    "ch1.kpi.cmmi_weighted.desc": "Weighted average by operational criticality across technology domains (CMMI Scale 1.0 - 5.0).",
    "ch1.kpi.ale_p50": "Annualized Loss Expectancy (ALE P50)",
    "ch1.kpi.ale_p50.desc": "Aggregate annual expected statistical loss across all {scenario_count} evaluated scenarios.",
    "ch1.kpi.cash_leakage": "Recurring Operational Inefficiency (OPEX)",
    "ch1.kpi.cash_leakage.desc": "Realized annual cost overhead with 100% certainty due to contractual and licensing duplication.",
    "ch1.kpi.local_outage_p90": "Major Local Incident Impact (P90)",
    "ch1.kpi.local_outage_p90.desc": "Estimated discrete loss resulting from an extended disruption at a primary operating facility.",
    "ch1.kpi.tail_risk_p90": "Annual Portfolio Tail Risk (ALE P90)",
    "ch1.kpi.tail_risk_p90.desc": "Aggregate annual statistical exposure under severe adverse scenarios at the corporate level.",

    "ch2.heading": "2. Technology Maturity Level",
    "ch2.lead_narrative": "The maturity assessment measures the degree of standardization, automation, and operational control within each technology domain against the industry reference benchmark ({industry_benchmark}).",
    "ch2.chart.radar.caption": "Figure 1: Current Maturity (AS-IS) vs. Industry Benchmark Comparison",
    "ch2.table.maturity.title": "Table 2: Maturity Breakdown by Technology Domain",
    "ch2.table.maturity.col.domain": "Technology Domain",
    "ch2.table.maturity.col.weight": "Relative Weight",
    "ch2.table.maturity.col.score": "Current Level (AS-IS)",
    "ch2.table.maturity.col.benchmark": "Industry Benchmark",
    "ch2.table.maturity.col.deviation": "Deviation",
    "ch2.table.maturity.col.status": "Operational Status",
    "ch2.table.maturity.footer.simple_mean": "Simple Arithmetic Mean (Unweighted)",
    "ch2.table.maturity.footer.weighted_mean": "Corporate Maturity Index (Weighted Mean)",
    "ch2.table.maturity.footnote": "Methodological note: The simple arithmetic mean ({simple_mean}) assigns equal weight to all domains. The corporate index ({weighted_mean}) weights each domain according to its business continuity criticality and managed asset volume.",

    "ch3.heading": "3. Economic Impact and Risk Analysis",
    "ch3.lead_narrative": "The economic quantification applies the standard Open FAIR model to distinguish between latent actuarial exposure (probabilistic) and recurring budgetary inefficiencies (deterministic).",
    "ch3.heatmap.title": "Table 3: Risk Scenario Distribution Matrix (Open FAIR 5x5)",
    "ch3.heatmap.axis.prob": "Annual Loss Event Frequency (LEF)",
    "ch3.heatmap.axis.impact": "Single Loss Expectancy (SLE)",
    "ch3.heatmap.band.vlow": "Very Low",
    "ch3.heatmap.band.low": "Low",
    "ch3.heatmap.band.med": "Moderate",
    "ch3.heatmap.band.high": "High",
    "ch3.heatmap.band.vhigh": "Very High",
    "ch3.cards.title": "Primary Systemic Exposure Scenarios",
    "ch3.cards.label.sle": "Single Loss Expectancy (SLE)",
    "ch3.cards.label.lef": "Annual Frequency (LEF)",
    "ch3.cards.label.ale": "Annual Exposure (ALE P50)",
    "ch3.cards.label.events_yr": "events/year",
    "ch3.table.reconciliation.title": "Table 4: Actuarial Exposure Reconciliation by Technology Domain",
    "ch3.table.reconciliation.col.domain": "Technology Domain",
    "ch3.table.reconciliation.col.scenarios": "Scenarios",
    "ch3.table.reconciliation.col.ale_p50": "Annual Exposure (ALE P50)",
    "ch3.table.reconciliation.col.share": "Share of Total",
    "ch3.table.reconciliation.footer.total": "Total Corporate Actuarial Exposure (Reconciled)",

    "ch4.heading": "4. Current State by Technology Domain",
    "ch4.lead_narrative": "The following sections detail the operational status, observed capacity thresholds, and empirical technical evidence collected for each evaluated domain.",
    "ch4.strip.score": "Current Maturity",
    "ch4.strip.status": "Operational Status",
    "ch4.strip.ale": "Annual Exposure (ALE P50)",
    "ch4.strip.exposure_level": "Exposure Level",
    "ch4.table.deepdive.col.subpillar": "Evaluated Sub-pillar & Capability",
    "ch4.table.deepdive.col.evidence": "Empirical Evidence & Observed Design Limits",
    "ch4.spof.title": "Table 5: Consolidated Single Points of Failure (SPOF) Registry",
    "ch4.spof.col.id": "ID",
    "ch4.spof.col.domain": "Domain",
    "ch4.spof.col.component": "Component / Asset",
    "ch4.spof.col.threshold": "Capacity Limit or Lifecycle Stage",
    "ch4.spof.col.impact": "Direct Operational Effect",

    "ch5.heading": "5. Cross-Domain Relationships and Dependencies",
    "ch5.lead_narrative": "The current architecture exhibits operational coupling across distinct domains. The following matrix describes how service degradation in a source domain propagates to dependent domains under the existing topology.",
    "ch5.table.nexus.title": "Table 6: Operational Coupling and Impact Propagation Matrix",
    "ch5.table.nexus.col.source": "Source Domain",
    "ch5.table.nexus.col.target": "Dependent Domain",
    "ch5.table.nexus.col.mechanism": "Technical Coupling Mechanism",
    "ch5.table.nexus.col.propagation": "Operational Propagation Effect (Current State)",

    "app.heading": "Appendix: Methodological Glossary and Diagnostic Scope",
    "app.glossary.title": "Actuarial and Technical Term Definitions",
    "app.disclaimer.title": "Scope Note and Diagnostic Boundary",
    "app.disclaimer.body": "This volume encompasses exclusively the assessment of the current baseline (AS-IS). Target architectures, remediation roadmaps, and associated capital investments are developed independently in Volume 2.",

    "status.maturity.optimal": "Optimized Operation",
    "status.maturity.managed": "Managed Operation",
    "status.maturity.defined": "Standardized Operation",
    "status.maturity.reactive": "Reactive Operation / Capacity Threshold",
    "status.maturity.initial": "Unstandardized Operation",

    "status.exposure.low": "Controlled Exposure",
    "status.exposure.moderate": "Moderate Exposure",
    "status.exposure.elevated": "Elevated Exposure",
    "status.exposure.significant": "Significant Exposure"
  }
}
```

#### 2.2 Deterministic Symmetry Enforcement Across All 6 Locales
To enforce 100% parity across `es`, `en`, `pt`, `fr`, `de`, and `ja`, the test suite executes an invariant verification gate at build time:

```python
import json
import re
from pathlib import Path

REQUIRED_LOCALES = ("es", "en", "pt", "fr", "de", "ja")
PLACEHOLDER_PATTERN = re.compile(r"\{([a-zA-Z0-9_]+)\}")


def verify_locales_symmetry(locales_path: Path) -> None:
    data = json.loads(locales_path.read_text(encoding="utf-8"))
    missing_locales = set(REQUIRED_LOCALES) - set(data.keys())
    if missing_locales:
        raise AssertionError(f"Missing required top-level locales: {sorted(missing_locales)}")

    reference_keys = set(data["en"].keys())
    for locale in REQUIRED_LOCALES:
        locale_keys = set(data[locale].keys())
        missing_keys = reference_keys - locale_keys
        extra_keys = locale_keys - reference_keys
        if missing_keys or extra_keys:
            raise AssertionError(
                f"Key asymmetry in locale '{locale}'. Missing: {sorted(missing_keys)}, Extra: {sorted(extra_keys)}"
            )
        for key in reference_keys:
            val = data[locale][key]
            if not isinstance(val, str) or not val.strip():
                raise AssertionError(f"Empty or non-string value for key '{key}' in locale '{locale}'")
            ref_placeholders = set(PLACEHOLDER_PATTERN.findall(data["en"][key]))
            loc_placeholders = set(PLACEHOLDER_PATTERN.findall(val))
            if ref_placeholders != loc_placeholders:
                raise AssertionError(
                    f"Placeholder mismatch in key '{key}' for locale '{locale}': "
                    f"expected {ref_placeholders}, got {loc_placeholders}"
                )
```

---

### 3. Actuarial & Financial Precision Engine

To eliminate financial discrepancies ("split-brain") between executive tables, risk cards, and domain headers, all monetary figures and maturity scores are processed through a single deterministic reconciliation pass before AST generation.

#### 3.1 Closed-Form Actuarial Equations

1.  **Scenario-Level Exact Arithmetic (Top Risk Cards & Domain Scenarios):**
    For each individual risk scenario $s \in \{1, \dots, M\}$, given Single Loss Expectancy $\text{SLE}_s \in \mathbb{Z}^+$ and Annual Loss Event Frequency $\text{LEF}_s \in \mathbb{Q}^+$ (quantized to 2 decimal places):
    $$\text{ALE}_{s}^{\text{raw}} = \text{SLE}_s \times \text{LEF}_s$$
    To guarantee that every risk card satisfies visual arithmetic verification ($\text{SLE}_s \times \text{LEF}_s = \text{ALE}_s$), the scenario's baseline integer exposure is defined as:
    $$\text{ALE}_s = \text{round\_half\_up}(\text{SLE}_s \times \text{LEF}_s)$$

2.  **Domain Aggregation & Largest Remainder Allocation (Hamilton Method):**
    When a corporate-wide Monte Carlo simulation provides an authoritative target P50 exposure $\text{ALE}_{\text{corp}}^{\text{P50}} \in \mathbb{Z}^+$, and each domain $d \in \{1, \dots, N\}$ has raw unrounded exposure $R_d = \sum_{s \in d} \text{ALE}_{s}^{\text{raw}}$, the integer allocation $A_d$ must satisfy:
    $$\sum_{d=1}^{N} A_d = \text{ALE}_{\text{corp}}^{\text{P50}}$$
    We compute exact quota $Q_d$ for each domain:
    $$Q_d = \text{ALE}_{\text{corp}}^{\text{P50}} \times \frac{R_d}{\sum_{k=1}^{N} R_k}$$
    Let $I_d = \lfloor Q_d \rfloor$ be the integer part and $f_d = Q_d - I_d$ be the fractional remainder. The residual integer units $\Delta = \text{ALE}_{\text{corp}}^{\text{P50}} - \sum_{d=1}^{N} I_d$ are distributed by adding $+1$ to the $\Delta$ domains with the largest fractional remainders $f_d$ (breaking ties deterministically by domain ID).

3.  **Distinction of Financial Categories (Zero Conflation):**
    The compiler strictly segregates four distinct financial metrics in `financial_telemetry`:
    *   $\text{ALE}_{\text{corp}}^{\text{P50}}$: Sum of reconciled domain exposures $\sum_{d=1}^{N} A_d$.
    *   $\text{OPEX}_{\text{leakage}}$: Deterministic annual recurring expenditure waste (e.g., redundant software licenses, overlapping maintenance contracts). Never added into $\text{ALE}_{\text{corp}}^{\text{P50}}$.
    *   $\text{Outage}_{\text{local}}^{\text{P90}}$: 90th percentile single-event loss at a primary operational site ($\max_s (\text{SLE}_{s}^{\text{P90}})$).
    *   $\text{ALE}_{\text{corp}}^{\text{P90}}$: 90th percentile annual aggregate portfolio loss derived from the stochastic distribution tail.

4.  **CMMI Maturity Score Reconciliation:**
    Given domain scores $C_d \in [1.00, 5.00]$ and domain criticality weights $W_d > 0$:
    $$\mu_{\text{simple}} = \text{round\_half\_up}\left(\frac{1}{N} \sum_{d=1}^{N} C_d, \, 2\right), \quad \mu_{\text{weighted}} = \text{round\_half\_up}\left(\frac{\sum_{d=1}^{N} W_d C_d}{\sum_{d=1}^{N} W_d}, \, 2\right)$$
    Both values are explicitly rendered in the footer of Table 2 alongside the methodological footnote (`ch2.table.maturity.footnote`), eliminating any ambiguity between simple and weighted averages.

#### 3.2 Reference Implementation of the Reconciliation Engine

```python
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
from typing import Any, Dict, List, Mapping, Sequence


class ActuarialReconciler:
    """Deterministic closed-form financial and maturity reconciler."""

    @staticmethod
    def reconcile_domain_allocations(
        target_corporate_ale: int,
        domain_raw_exposures: Sequence[Tuple[str, Decimal]],
    ) -> Dict[str, int]:
        total_raw = sum((raw for _, raw in domain_raw_exposures), Decimal("0"))
        if total_raw <= Decimal("0"):
            raise ActuarialReconciliationError("Total raw domain exposure must be strictly positive.")

        target_dec = Decimal(str(target_corporate_ale))
        quotas: List[Tuple[str, int, Decimal]] = []
        for domain_id, raw_val in domain_raw_exposures:
            exact_quota = (target_dec * raw_val) / total_raw
            floor_val = int(exact_quota.to_integral_value(rounding=ROUND_FLOOR))
            remainder = exact_quota - Decimal(str(floor_val))
            quotas.append((domain_id, floor_val, remainder))

        current_sum = sum(item[1] for item in quotas)
        residual = target_corporate_ale - current_sum

        # Sort by descending remainder, then ascending domain_id for deterministic tie-breaking
        sorted_for_remainder = sorted(quotas, key=lambda x: (-x[2], x[0]))
        allocated: Dict[str, int] = {domain_id: floor_val for domain_id, floor_val, _ in quotas}

        for i in range(residual):
            win_domain_id = sorted_for_remainder[i][0]
            allocated[win_domain_id] += 1

        if sum(allocated.values()) != target_corporate_ale:
            raise ActuarialReconciliationError("Largest remainder allocation failed exact sum invariant.")

        return allocated

    @staticmethod
    def reconcile_scenario_card(sle: int, lef: Decimal) -> Dict[str, Any]:
        quantized_lef = lef.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        reconciled_ale = int((Decimal(str(sle)) * quantized_lef).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return {
            "sle": sle,
            "lef": quantized_lef,
            "ale_p50": reconciled_ale,
        }
```

---

### 4. Step-by-Step Execution Plan

#### Phase 1: Linguistic Catalog Expansion & Symmetry Verification
1.  **Update `engine_config/locales.json`:**
    *   Insert all canonical `doc.tomo1.*`, `ch1.*` through `ch5.*`, `app.*`, and `status.*` keys across `es`, `en`, `pt`, `fr`, `de`, and `ja`.
    *   Audit all string values to ensure executive sobriety (zero alarmist adjectives) and strict AS-IS framing (zero references to H1/H2/H3 roadmaps or target scores).
2.  **Run Catalog Gate:**
    *   Execute `pytest tests/unit/test_i18n_symmetry.py` verifying 100% key parity, non-empty strings, and identical `{placeholder}` signatures across all 6 locales.

#### Phase 2: Actuarial & Maturity Reconciliation Module
1.  **Implement `ActuarialReconciler`:**
    *   Place in `assessment_engine/domain/actuarial_reconciler.py`.
    *   Implement `reconcile_domain_allocations()`, `reconcile_scenario_card()`, and `reconcile_cmmi_scores()`.
2.  **Unit Test Financial Edge Cases:**
    *   Test with 10 domains having identical remainders (verifying deterministic tie-breaking).
    *   Test across multiple currencies (`EUR`, `USD`, `JPY`, `CHF`) and enterprise scales ($50\text{M}$ to $50\text{B}$).
    *   Assert $\sum A_d == \text{ALE}_{\text{corp}}^{\text{P50}}$ to the exact integer.

#### Phase 3: Refactor `TomoAsisASTCompiler`
1.  **Purge Legacy Antipatterns:**
    *   Remove all Spanish identifiers, docstrings, or comments from `tomo_asis_compiler.py`.
    *   Remove all default language parameters (`doc_lang: str` is now mandatory).
    *   Remove all `if doc_lang == ...` branches and fallback strings in `_t()` calls.
    *   Remove any hardcoded client names, site names, or fixed scenario counts.
2.  **Implement Section Builders:**
    *   Wire Chapter 1 to emit the 5-row Executive KPI synthesis table clearly separating `ALE P50`, `Recurring OPEX Inefficiency`, `Local Major Incident (P90)`, and `Portfolio Tail Risk (ALE P90)`.
    *   Wire Chapter 2 to embed `global_radar_chart.png` and render Table 2 comparing `Current Level (AS-IS)` against `Industry Benchmark` and `Deviation`, including both `Simple Arithmetic Mean` and `Weighted Corporate Index` in the footer.
    *   Wire Chapter 3 to generate the 5x5 Open FAIR Heatmap Mosaic Table, the 3-column Systemic Risk Cards, and Table 4 (Domain Exposure Reconciliation).
    *   Wire Chapter 4 to iterate dynamically over `tower_payloads`, rendering the 4-column AS-IS KPI strip, sober narrative, 2-column Sub-pillar vs. Empirical Evidence table, and the consolidated SPOF Matrix.
    *   Wire Chapter 5 to render the Cross-Domain Operational Coupling and Propagation Matrix.

#### Phase 4: Automated AST & Source Code Hygiene Verification
1.  **Static Source Audit Test (`tests/quality/test_codebase_hygiene.py`):**
    *   Scan all `.py` files using Python's `ast` module and regex patterns:
        *   Verify zero Spanish diacritics (`[áéíóúñÁÉÍÓÚÑ¿¡]`) or Spanish keywords in code, comments, or docstrings.
        *   Verify zero `doc_lang\s*=\s*["']` default parameter assignments.
        *   Verify zero tenant-specific strings in source code.
2.  **AST Invariant Verification (`tests/integration/test_tomo1_ast_invariants.py`):**
    *   Compile Tomo 1 across all 6 locales (`es`, `en`, `pt`, `fr`, `de`, `ja`) using synthetic multi-tenant fixtures (e.g., Mid-Market Manufacturing EUR, Global Banking USD, Utilities JPY).
    *   Traverse the emitted AST and assert:
        *   Sum of Chapter 4 domain strip ALEs equals Chapter 1 `ALE P50` and Chapter 3 Table 4 total.
        *   Every Chapter 3 Risk Card satisfies $\text{round}(\text{SLE} \times \text{LEF}) == \text{ALE}$.
        *   Zero presence of prohibited FUD terms or TO-BE roadmap terms in rendered AST text nodes.

#### Phase 5: Document Compilation & Visual Artifact Validation
1.  **Render `.docx` and `.pdf` Deliverables:**
    *   Execute the document rendering pipeline to produce the final Word and PDF files from the compiled AST.
2.  **Visual & Structural Inspection:**
    *   Confirm `global_radar_chart.png` renders crisply in Chapter 2 with proper aspect ratio and localized caption.
    *   Confirm the 5x5 Open FAIR Heatmap table and 3-column Risk Cards do not overflow page margins or split awkwardly across page breaks (`keep_together = True` on card and strip AST containers).
    *   Confirm all table headers repeat across page boundaries (`repeat_header = True`) and right-align all numerical and monetary columns.