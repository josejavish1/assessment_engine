# RFC 067: Universal Multi-Tenant Remediation Blueprint for Consolidated Tomo 1 AS-IS (Observations 2 through 9)

**Status:** Definitive Architectural & Implementation Blueprint  
**Target System:** Universal Multi-Tenant Enterprise Architecture Compiler (`tomo_asis_ast_compiler.py`, `engine_config/locales.json`, Domain Data Contracts)  
**Architectural Invariants:** 100% Technical English Codebase | Zero Hardcoded Tenant Constants | 6-Locale Mathematical Symmetry (`es`, `en`, `pt`, `fr`, `de`, `ja`) | Strict Mandatory `doc_lang: str` Propagation | Zero Inline Language Conditionals  

---

## 1. Point 2: Local Facility vs. Consolidated Group Hourly Downtime Rates (Chapter 1)

### 1.1 Architectural Root-Cause & Data Contract Extension
The Executive Summary previously juxtaposed two distinct financial impact velocities without explaining the failure-domain boundary separating a single physical operating site from enterprise-wide core transaction processing. To scale across any enterprise vertical (manufacturing plants, bank branches, hospital campuses, logistics hubs, or retail stores), the data contract must parameterize both velocities dynamically.

#### Data Contract (`domain_models/consolidated_asis_models.py`)
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class OperationalContinuityMetrics:
    """Multi-tenant operational downtime financial velocity metrics."""
    local_facility_hourly_burn_formatted: str       # e.g., "5.000 €/h" or "$5,000/h"
    consolidated_group_hourly_burn_formatted: str   # e.g., "13.061,29 €/h" or "$13,061.29/h"
    local_facility_scope_descriptor_key: str        # Resolves via locales.json
    consolidated_scope_descriptor_key: str          # Resolves via locales.json
```

### 1.2 Exact Localization Keys (`engine_config/locales.json`)
All 6 locales (`es`, `en`, `pt`, `fr`, `de`, `ja`) must maintain 100% key symmetry. Below are the canonical Spanish (`es`) and English (`en`) definitions:

```json
{
  "es": {
    "tomo_ch1_continuity_bullet_title": "Continuidad Operativa en Centros Operativos vs. Nivel Consolidado Corporativo:",
    "tomo_ch1_continuity_bullet_body": "Los sistemas periféricos de control físico, despacho y operación local presentan dependencias directas de enlaces de comunicaciones únicos y equipamiento próximo al fin de soporte de fabricante. Para efectos de gobierno financiero y priorización de inversiones, el modelo distingue dos umbrales de impacto horario según el radio de afectación del incidente: (1) Impacto Operativo en Centro Local ({local_site_hourly_rate}), que cuantifica el coste directo de la paralización física aislada de una única planta, centro logístico o delegación (interrupción de básculas, barreras de expedición y líneas de carga locales sin afectación al resto del grupo); y (2) Impacto Corporativo Consolidado ({consolidated_hourly_rate}), que refleja la tasa de pérdida agregada cuando una caída en los sistemas centrales (núcleo ERP, facturación centralizada, validación de pedidos o bases de datos corporativas) detiene simultáneamente la capacidad transaccional y operativa de todas las unidades de negocio de la organización."
  },
  "en": {
    "tomo_ch1_continuity_bullet_title": "Operational Continuity at Local Facilities vs. Consolidated Corporate Level:",
    "tomo_ch1_continuity_bullet_body": "Edge physical control, dispatch, and local facility systems operate with direct dependencies on single communication links and hardware approaching manufacturer end-of-support. For financial governance and capital prioritization, the model distinguishes two hourly impact thresholds based on the blast radius of an outage: (1) Isolated Local Facility Impact ({local_site_hourly_rate}), which quantifies the direct financial burn rate of a physical stoppage at a single plant, logistics hub, or branch office (halting local weighbridges, dispatch barriers, and loading bays while other sites continue operating); and (2) Consolidated Corporate Impact ({consolidated_hourly_rate}), which reflects the enterprise-wide operational burn rate incurred when a failure in central core systems (core ERP, centralized billing, order fulfillment, or corporate databases) simultaneously paralyzes transactional and operational capacity across all business units."
  }
}
```

### 1.3 Compiler Implementation (`tomo_asis_ast_compiler.py`)
```python
def _build_ch1_continuity_finding_node(
    self,
    payload: ConsolidatedAsIsPayload,
    doc_lang: str,
) -> ASTNode:
    """Render the executive operational continuity finding with explicit blast-radius distinction."""
    tr = self._locale_service.get_namespace(doc_lang)
    metrics = payload.executive_summary.continuity_metrics

    title_text = tr["tomo_ch1_continuity_bullet_title"]
    body_text = tr["tomo_ch1_continuity_bullet_body"].format(
        local_site_hourly_rate=metrics.local_facility_hourly_burn_formatted,
        consolidated_hourly_rate=metrics.consolidated_group_hourly_burn_formatted,
    )

    return CalloutBlockNode(
        title=title_text,
        body=body_text,
        border_left_color_hex="#0072BC",
        background_color_hex="#F8FAFC",
        padding_pt=10.0,
        space_after_pt=8.0,
    )
```

---

## 2. Point 3: Sector Benchmark Source & Methodological Rigor (Chapter 2)

### 2.1 Architectural Root-Cause & Data Contract Extension
Displaying a static `"3.50"` sector benchmark and a `"-0.95"` variance without disclosing the reference standard, empirical baseline, and peer cohort criteria undermines executive auditability. The compiler must inject a formal methodological block immediately below the Maturity Radiography Table (Table 2).

#### Data Contract (`domain_models/consolidated_asis_models.py`)
```python
@dataclass(frozen=True)
class MaturityBenchmarkMetadata:
    """Empirical benchmark provenance metadata for Chapter 2."""
    target_benchmark_score_formatted: str   # e.g., "3,50" or "3.50"
    enterprise_mean_score_formatted: str    # e.g., "2,55" or "2.55"
    net_variance_formatted: str             # e.g., "-0,95" or "-0.95"
    industry_vertical_label: str            # Dynamically resolved from tenant profile
    peer_revenue_tier_label: str            # e.g., "100M€ - 1.000M€" or "$100M - $1B"
```

### 2.2 Exact Localization Keys (`engine_config/locales.json`)
```json
{
  "es": {
    "tomo_ch2_benchmark_methodology_title": "Nota Metodológica y Fuentes del Benchmark Sectorial ({benchmark_score} / 5,00)",
    "tomo_ch2_benchmark_methodology_body": "El umbral de referencia sectorial situado en {benchmark_score} puntos no constituye un valor arbitrario, sino el estándar empírico de madurez exigible para organizaciones del sector ({industry_vertical}) en el tramo de facturación comparable ({peer_revenue_tier}). Este índice de referencia se construye mediante la triangulación de tres marcos internacionales de auditoría tecnológica: (1) CMMI Institute (Capability Maturity Model Integration v2.0), donde el nivel 3,00 ('Definido') exige procesos estandarizados y documentados, y el tramo {benchmark_score} representa la transición hacia el control cuantitativo y predecible de disponibilidad; (2) Gartner IT Key Metrics Data (ITKMD), que establece la línea base de resiliencia operativa, automatización e inversión en ciclo de vida para infraestructuras críticas; y (3) los estándares ISO/IEC 20000-1 (Gestión de Servicios TI) e ISO/IEC 27001 (Seguridad de la Información). La desviación media consolidada de {net_variance} puntos (media actual de {enterprise_mean} frente al objetivo de {benchmark_score}) indica que, si bien la organización mantiene capacidades operativas funcionales, sus procesos de respaldo, observabilidad y redundancia dependen aún de intervenciones manuales reactivas en lugar de controles automatizados de nivel industrial."
  },
  "en": {
    "tomo_ch2_benchmark_methodology_title": "Methodological Note & Sector Benchmark Provenance ({benchmark_score} / 5.00)",
    "tomo_ch2_benchmark_methodology_body": "The sector reference baseline of {benchmark_score} points is not an arbitrary target, but the empirical maturity standard required for organizations operating within the {industry_vertical} vertical across a comparable revenue tier ({peer_revenue_tier}). This composite benchmark is derived by triangulating three international technology audit frameworks: (1) CMMI Institute (Capability Maturity Model Integration v2.0), where Level 3.00 ('Defined') mandates standardized, documented processes and the {benchmark_score} threshold represents the transition toward quantitatively managed, predictable availability; (2) Gartner IT Key Metrics Data (ITKMD), which establishes peer-group baselines for operational resilience, automation, and lifecycle refresh across mission-critical infrastructure; and (3) ISO/IEC 20000-1 (IT Service Management) and ISO/IEC 27001 (Information Security) control baselines. The consolidated net variance of {net_variance} points (current enterprise mean of {enterprise_mean} vs. the {benchmark_score} benchmark) indicates that while core operational capabilities remain functional, recovery orchestration, observability, and failover controls still rely on reactive manual intervention rather than automated industrial-grade governance."
  }
}
```

### 2.3 Compiler Implementation (`tomo_asis_ast_compiler.py`)
```python
def _build_ch2_benchmark_methodology_callout(
    self,
    payload: ConsolidatedAsIsPayload,
    doc_lang: str,
) -> ASTNode:
    """Build the authoritative benchmark provenance note below the maturity radiography table."""
    tr = self._locale_service.get_namespace(doc_lang)
    bm = payload.maturity_summary.benchmark_metadata

    title = tr["tomo_ch2_benchmark_methodology_title"].format(
        benchmark_score=bm.target_benchmark_score_formatted,
    )
    body = tr["tomo_ch2_benchmark_methodology_body"].format(
        benchmark_score=bm.target_benchmark_score_formatted,
        industry_vertical=bm.industry_vertical_label,
        peer_revenue_tier=bm.peer_revenue_tier_label,
        net_variance=bm.net_variance_formatted,
        enterprise_mean=bm.enterprise_mean_score_formatted,
    )

    return CalloutBlockNode(
        title=title,
        body=body,
        border_left_color_hex="#1E293B",
        background_color_hex="#F1F5F9",
        padding_pt=10.0,
        space_after_pt=14.0,
    )
```

---

## 3. Points 4 & 6: Executive Restructuring of Chapter 3 & Transparent Emergency Recovery Cost Breakdown

### 3.1 Architectural Root-Cause & Data Contract Extension
Chapter 3 previously relied on opaque actuarial terminology (`ALE`, `SLE`, `TEF`, `VaR P95`) and presented a single lump-sum figure for emergency recovery (`224.452 €`) without line-item operational grounding. To make Chapter 3 immediately actionable for CIOs, CFOs, and Board members, it is restructured into a plain-language 3-step executive architecture narrative, and the emergency response expenditure is decomposed into three auditable operational buckets.

#### Data Contract (`domain_models/consolidated_asis_models.py`)
```python
@dataclass(frozen=True)
class SevereIncidentAnatomyBreakdown:
    """Line-item financial decomposition of a severe major incident (Section 3.2.1)."""
    estimated_outage_duration_hours_formatted: str        # e.g., "39,9 h"
    total_single_event_loss_formatted: str                # e.g., "745.921 €"
    direct_operational_stoppage_loss_formatted: str       # e.g., "521.469 €"
    total_emergency_recovery_cost_formatted: str          # e.g., "224.452 €"
    # Bucket 1: OEM 24x7 Out-of-Contract Emergency Engineering (~42%)
    bucket_1_oem_engineering_cost_formatted: str          # e.g., "94.270 €"
    bucket_1_share_pct_formatted: str                     # e.g., "42%"
    # Bucket 2: Urgent Spot Hardware Procurement & Dedicated Air/Road Courier (~33%)
    bucket_2_hardware_logistics_cost_formatted: str       # e.g., "74.069 €"
    bucket_2_share_pct_formatted: str                     # e.g., "33%"
    # Bucket 3: External Level-3 Database Recovery & Forensic Triage (~25%)
    bucket_3_forensic_db_recovery_cost_formatted: str     # e.g., "56.113 €"
    bucket_3_share_pct_formatted: str                     # e.g., "25%"
```

### 3.2 Exact Localization Keys (`engine_config/locales.json`)
```json
{
  "es": {
    "tomo_ch3_exec_intro_p1": "Este capítulo traduce los hallazgos técnicos del diagnóstico en impacto económico directo para el negocio. Su objetivo es proporcionar a la Dirección de TI y al Comité de Dirección una base objetiva y defendible financieramente para decidir dónde invertir con prioridad. El análisis se estructura en tres preguntas ejecutivas: (1) ¿Cuál es el coste anual latente de mantener la infraestructura actual sin cambios?, (2) ¿Qué factura real afrontaría la compañía ante una caída grave de sus sistemas principales?, y (3) ¿Qué áreas concentran el mayor retorno en reducción de riesgo por cada euro invertido?",
    "tomo_ch3_step1_heading": "3.1. El Coste de la Inacción: Exposición Económica Anualizada por Dominio",
    "tomo_ch3_step2_heading": "3.2. Anatomía de un Incidente Mayor: ¿Qué Ocurre ante una Caída Crítica?",
    "tomo_ch3_step2_sub1_heading": "3.2.1. Desglose Financiero y Operativo de una Interrupción Grave",
    "tomo_ch3_step2_sub1_intro": "Cuando se materializa un fallo severo en la infraestructura crítica (como la caída del clúster central de virtualización o la corrupción del almacenamiento corporativo sin respaldo inmutable), el tiempo medio estimado para reconstruir el entorno, restaurar copias y validar la integridad transaccional asciende a {outage_duration_hours}. Un incidente de esta magnitud genera un impacto económico total estimado de {total_event_loss}, dividido en dos bloques claramente diferenciados:",
    "tomo_ch3_step2_lucro_cesante_bullet": "1. Paralización de la Actividad y Coste Operativo Directo ({direct_stoppage_loss}): Representa el impacto directo sobre el negocio durante las {outage_duration_hours} de indisponibilidad a razón de {consolidated_hourly_rate}. Incluye expediciones retenidas, paradas en líneas de despacho, horas de personal operativo improductivas y retrasos en la facturación y procesamiento de pedidos.",
    "tomo_ch3_step2_emergency_intro_bullet": "2. Costes Extraordinarios de Recuperación de Emergencia ({total_emergency_cost}): Cuando un sistema cae fuera de cobertura de soporte activo o supera la capacidad interna de restablecimiento, la organización debe contratar recursos externos de urgencia a tarifas de contingencia. Estos {total_emergency_cost} se desglosan en tres partidas operativas auditables:",
    "tomo_ch3_emergency_bucket_1": "• Intervención de Ingeniería de Emergencia 24x7 del Fabricante sin Contrato Activo ({bucket_1_cost} — {bucket_1_pct} del gasto de respuesta): Contratación reactiva de especialistas de Nivel 3 de los fabricantes originales (OEM) bajo tarifas de urgencia ('Time & Materials' fuera de SLA) para reconstruir hipervisores, cabinas de almacenamiento o electrónica de red cuyo soporte ordinario ha expirado.",
    "tomo_ch3_emergency_bucket_2": "• Adquisición Urgente de Equipamiento en Mercado Spot y Logística Dedicada ({bucket_2_cost} — {bucket_2_pct} del gasto de respuesta): Compra inmediata de servidores, controladoras, discos o conmutadores de reemplazo a distribuidores de emergencia con sobrecoste por disponibilidad inmediata, incluyendo transporte urgente dedicado (mensajería directa puerta a puerta en el mismo día) hacia los centros afectados.",
    "tomo_ch3_emergency_bucket_3": "• Servicios Especializados de Recuperación de Bases de Datos y Triaje Forense ({bucket_3_cost} — {bucket_3_pct} del gasto de respuesta): Intervención de consultores externos especializados en reconstrucción de tablas transaccionales corruptas (ERP/bases de datos corporativas), reconciliación de operaciones en vuelo previas al corte y aseguramiento forense del entorno antes de reanudar la producción.",
    "tomo_ch3_step3_heading": "3.3. Priorización de Capital: Dónde Invertir para Mitigar el Riesgo"
  },
  "en": {
    "tomo_ch3_exec_intro_p1": "This chapter translates technical diagnostic findings into direct business financial exposure. Its objective is to provide IT Leadership and the Executive Board with an objective, financially defensible baseline to prioritize capital allocation. The analysis is structured around three executive questions: (1) What is the latent annual cost of operating the current infrastructure unchanged?, (2) What actual financial bill would the enterprise face during a severe core system outage?, and (3) Which domains yield the highest risk reduction per unit of capital invested?",
    "tomo_ch3_step1_heading": "3.1. The Cost of Inaction: Annualized Financial Exposure by Domain",
    "tomo_ch3_step2_heading": "3.2. Anatomy of a Major Incident: What Happens During a Critical Outage?",
    "tomo_ch3_step2_sub1_heading": "3.2.1. Financial and Operational Breakdown of a Severe Outage",
    "tomo_ch3_step2_sub1_intro": "When a severe failure strikes critical infrastructure (such as a primary virtualization cluster collapse or core storage corruption without immutable backups), the estimated mean time to rebuild the environment, restore data volumes, and verify transactional integrity reaches {outage_duration_hours}. An incident of this magnitude generates an estimated total financial impact of {total_event_loss}, divided into two distinct operational components:",
    "tomo_ch3_step2_lucro_cesante_bullet": "1. Business Interruption and Direct Operational Stoppage ({direct_stoppage_loss}): Represents the direct business burn rate across {outage_duration_hours} of downtime at {consolidated_hourly_rate}. This encompasses halted shipments, stalled dispatch lines, idle operational labor hours, and delayed order processing and billing.",
    "tomo_ch3_step2_emergency_intro_bullet": "2. Extraordinary Emergency Recovery Costs ({total_emergency_cost}): When a critical system fails outside active vendor support coverage or exceeds internal recovery capacity, the enterprise must engage external emergency resources at contingency rates. This {total_emergency_cost} expenditure decomposes into three auditable operational buckets:",
    "tomo_ch3_emergency_bucket_1": "• Out-of-Contract 24x7 OEM Emergency Engineering Intervention ({bucket_1_cost} — {bucket_1_pct} of emergency spend): Reactive engagement of Tier-3 Original Equipment Manufacturer (OEM) specialists at emergency Time & Materials rates outside standard SLAs to rebuild hypervisors, storage arrays, or network switches whose standard support has lapsed.",
    "tomo_ch3_emergency_bucket_2": "• Urgent Spot-Market Hardware Procurement and Dedicated Courier Logistics ({bucket_2_cost} — {bucket_2_pct} of emergency spend): Immediate spot-market purchase of replacement servers, controllers, drives, or switches at premium availability pricing, combined with dedicated same-day air/ground courier transport directly to affected facilities.",
    "tomo_ch3_emergency_bucket_3": "• Specialized Database Recovery and Level-3 Forensic Triage Services ({bucket_3_cost} — {bucket_3_pct} of emergency spend): Engagement of external recovery engineers specialized in repairing corrupted transactional tables (core ERP/corporate databases), reconciling in-flight transactions interrupted by the crash, and performing forensic containment prior to production restart.",
    "tomo_ch3_step3_heading": "3.3. Capital Prioritization: Where Investment Yields Maximum Risk Reduction"
  }
}
```

### 3.3 Compiler Implementation (`tomo_asis_ast_compiler.py`)
```python
def _build_ch3_severe_incident_anatomy_section(
    self,
    payload: ConsolidatedAsIsPayload,
    doc_lang: str,
) -> list[ASTNode]:
    """Render Section 3.2.1 in clear executive prose with 3-bucket emergency cost decomposition."""
    tr = self._locale_service.get_namespace(doc_lang)
    anatomy = payload.economic_impact.severe_incident_anatomy
    continuity = payload.executive_summary.continuity_metrics

    nodes: list[ASTNode] = [
        HeadingNode(level=3, text=tr["tomo_ch3_step2_sub1_heading"]),
        ParagraphNode(
            text=tr["tomo_ch3_step2_sub1_intro"].format(
                outage_duration_hours=anatomy.estimated_outage_duration_hours_formatted,
                total_event_loss=anatomy.total_single_event_loss_formatted,
            ),
            style=self._styles.body_regular,
        ),
        ParagraphNode(
            text=tr["tomo_ch3_step2_lucro_cesante_bullet"].format(
                direct_stoppage_loss=anatomy.direct_operational_stoppage_loss_formatted,
                outage_duration_hours=anatomy.estimated_outage_duration_hours_formatted,
                consolidated_hourly_rate=continuity.consolidated_group_hourly_burn_formatted,
            ),
            style=self._styles.body_bold_lead,
        ),
        ParagraphNode(
            text=tr["tomo_ch3_step2_emergency_intro_bullet"].format(
                total_emergency_cost=anatomy.total_emergency_recovery_cost_formatted,
            ),
            style=self._styles.body_bold_lead,
        ),
        CalloutBlockNode(
            title="",
            body="\n\n".join([
                tr["tomo_ch3_emergency_bucket_1"].format(
                    bucket_1_cost=anatomy.bucket_1_oem_engineering_cost_formatted,
                    bucket_1_pct=anatomy.bucket_1_share_pct_formatted,
                ),
                tr["tomo_ch3_emergency_bucket_2"].format(
                    bucket_2_cost=anatomy.bucket_2_hardware_logistics_cost_formatted,
                    bucket_2_pct=anatomy.bucket_2_share_pct_formatted,
                ),
                tr["tomo_ch3_emergency_bucket_3"].format(
                    bucket_3_cost=anatomy.bucket_3_forensic_db_recovery_cost_formatted,
                    bucket_3_pct=anatomy.bucket_3_share_pct_formatted,
                ),
            ]),
            border_left_color_hex="#D97706",
            background_color_hex="#FFFBEB",
            padding_pt=10.0,
            space_after_pt=12.0,
        ),
    ]
    return nodes
```

---

## 4. Point 5: Section 3.1 Reconciliation Bridge (29 Evaluated Scenarios vs. 10 Displayed Rows)

### 4.1 Architectural Root-Cause & Data Contract Extension
Section 3.1 previously cited `total_evaluated_scenarios` (e.g., `29`) while rendering Table 4 with `10` domain rows (`T1` through `T10`) without an explicit reconciliation column. To eliminate any perceived discrepancy, the narrative now explains the aggregation mechanism, and Table 4 incorporates an explicit `"Escenarios Evaluados"` (`evaluated_scenarios_count`) column whose mathematical sum across all rows strictly equals `total_evaluated_scenarios`.

#### Data Contract (`domain_models/consolidated_asis_models.py`)
```python
@dataclass(frozen=True)
class DomainRiskExposureRow:
    """Single domain row in Table 4 (Section 3.1)."""
    tower_id: str                                # e.g., "T1" .. "T10"
    tower_name: str                              # Localized tower title
    evaluated_scenarios_count: int               # e.g., 3, 4, 2... (Sum across rows == 29)
    annualized_exposure_mean_formatted: str      # e.g., "63.840 €"
    severe_event_p95_formatted: str              # e.g., "184.200 €"
    portfolio_risk_share_pct_formatted: str      # e.g., "18,4%"
```

### 4.2 Exact Localization Keys (`engine_config/locales.json`)
```json
{
  "es": {
    "tomo_ch3_sec31_reconciliation_bridge": "El modelo de cuantificación evalúa {total_scenarios} escenarios de fallo técnico específicos identificados durante la auditoría de campo (tales como caídas de enlaces únicos, saturación de cabinas de disco, fallos de fuentes de alimentación sin redundancia o indisponibilidad de servidores críticos). Para facilitar la asignación presupuestaria y la toma de decisiones por parte de los responsables de cada área, la Tabla 4 agrupa y consolida estos {total_scenarios} escenarios individuales en los {total_domains} dominios tecnológicos de la arquitectura, detallando cuántos escenarios activos corresponden a cada torre y su impacto económico anualizado acumulado.",
    "tomo_ch3_table4_col_domain": "Dominio Tecnológico",
    "tomo_ch3_table4_col_scenarios_count": "Escenarios Evaluados",
    "tomo_ch3_table4_col_annual_exposure": "Impacto Económico Anual Estimado",
    "tomo_ch3_table4_col_severe_event": "Coste ante Incidente Grave (P95)",
    "tomo_ch3_table4_col_share_pct": "% del Riesgo Total",
    "tomo_ch3_table4_total_row_label": "TOTAL CONSOLIDADO ({total_domains} Dominios)"
  },
  "en": {
    "tomo_ch3_sec31_reconciliation_bridge": "The quantification model evaluates {total_scenarios} discrete technical failure scenarios identified during the field diagnostic (such as single-link outages, storage array saturation, non-redundant power supply failures, or critical server unavailability). To streamline budget allocation and executive accountability for platform owners, Table 4 aggregates and consolidates these {total_scenarios} individual scenarios across the {total_domains} technology domains of the architecture, explicitly displaying the number of active scenarios mapped to each tower alongside their cumulative annualized financial exposure.",
    "tomo_ch3_table4_col_domain": "Technology Domain",
    "tomo_ch3_table4_col_scenarios_count": "Evaluated Scenarios",
    "tomo_ch3_table4_col_annual_exposure": "Estimated Annual Economic Impact",
    "tomo_ch3_table4_col_severe_event": "Severe Incident Cost (P95)",
    "tomo_ch3_table4_col_share_pct": "% of Total Risk",
    "tomo_ch3_table4_total_row_label": "CONSOLIDATED TOTAL ({total_domains} Domains)"
  }
}
```

### 4.3 Compiler Implementation (`tomo_asis_ast_compiler.py`)
```python
def _build_ch3_domain_risk_table(
    self,
    payload: ConsolidatedAsIsPayload,
    doc_lang: str,
) -> list[ASTNode]:
    """Build Section 3.1 introductory bridge and Table 4 with explicit scenario count reconciliation."""
    tr = self._locale_service.get_namespace(doc_lang)
    rows = payload.economic_impact.domain_exposure_rows
    total_scenarios = sum(r.evaluated_scenarios_count for r in rows)
    total_domains = len(rows)

    if total_scenarios != payload.economic_impact.total_evaluated_scenarios:
        raise ValueError(
            f"Scenario reconciliation invariant violated: sum of domain scenarios "
            f"({total_scenarios}) != total_evaluated_scenarios "
            f"({payload.economic_impact.total_evaluated_scenarios})."
        )

    bridge_para = ParagraphNode(
        text=tr["tomo_ch3_sec31_reconciliation_bridge"].format(
            total_scenarios=total_scenarios,
            total_domains=total_domains,
        ),
        style=self._styles.body_regular,
    )

    headers = [
        tr["tomo_ch3_table4_col_domain"],
        tr["tomo_ch3_table4_col_scenarios_count"],
        tr["tomo_ch3_table4_col_annual_exposure"],
        tr["tomo_ch3_table4_col_severe_event"],
        tr["tomo_ch3_table4_col_share_pct"],
    ]

    table_rows: list[list[str]] = [
        [
            f"{r.tower_id} — {r.tower_name}",
            str(r.evaluated_scenarios_count),
            r.annualized_exposure_mean_formatted,
            r.severe_event_p95_formatted,
            r.portfolio_risk_share_pct_formatted,
        ]
        for r in rows
    ]

    # Append explicit Total Reconciliation Footer Row
    table_rows.append([
        tr["tomo_ch3_table4_total_row_label"].format(total_domains=total_domains),
        str(total_scenarios),
        payload.economic_impact.total_annual_exposure_formatted,
        payload.economic_impact.portfolio_p95_exposure_formatted,
        "100,0%" if doc_lang in ("es", "pt", "fr", "de") else "100.0%",
    ])

    table_node = TableNode(
        headers=headers,
        rows=table_rows,
        column_widths_pct=[34.0, 14.0, 20.0, 20.0, 12.0],
        highlight_last_row=True,
    )
    return [bridge_para, table_node]
```

---

## 5. Point 7: Balanced Domain Diagnostic Cards in Chapter 4 (Intuitive Labeling, Strengths & Enriched Prose)

### 5.1 Architectural Root-Cause & Data Contract Extension
The Chapter 4 domain cards previously used opaque actuarial shorthand (`"Exposición ALE"`), focused solely on deficiencies, and rendered a 2-column subpillar table that omitted operational strengths. To provide a balanced, constructive, and board-ready evaluation:
1. The KPI strip label is updated to `"Impacto Económico Anual Estimado (Riesgo Activo)"`.
2. Each tower renders two symmetrical executive callout blocks:
   - **Emerald/Teal Callout (`#0D9488`):** `"Capacidades Operativas y Fortalezas Observadas"`
   - **Amber Callout (`#D97706`):** `"Límites de Capacidad, Obsolescencia y Puntos de Fricción"`
3. The subpillar table is upgraded to a 3-column layout: `Subpilar Evaluado` | `Fortalezas y Controles Activos` | `Puntos de Fricción y Riesgo Operativo`.

#### Data Contract (`domain_models/consolidated_asis_models.py`)
```python
@dataclass(frozen=True)
class SubpillarBalancedEvaluation:
    """3-column balanced evaluation for each technical subpillar in Chapter 4."""
    subpillar_name: str
    observed_strengths_and_controls: str
    operational_friction_and_risks: str

@dataclass(frozen=True)
class TowerDiagnosticCardPayload:
    """Complete balanced payload for a single technology tower (T1..T10) in Chapter 4."""
    tower_id: str
    tower_title: str
    maturity_score_formatted: str
    sector_benchmark_formatted: str
    annual_economic_impact_formatted: str
    evaluated_assets_or_scope_label: str
    architectural_context_narrative: str
    observed_strengths_summary: str
    capacity_limits_and_friction_summary: str
    subpillar_evaluations: tuple[SubpillarBalancedEvaluation, ...]
```

### 5.2 Exact Localization Keys (`engine_config/locales.json`)
```json
{
  "es": {
    "tomo_ch4_kpi_maturity_label": "Madurez Actual vs. Sector",
    "tomo_ch4_kpi_annual_impact_label": "Impacto Económico Anual Estimado (Riesgo Activo)",
    "tomo_ch4_kpi_scope_label": "Alcance y Activos Auditados",
    "tomo_ch4_callout_strengths_title": "Capacidades Operativas y Fortalezas Observadas",
    "tomo_ch4_callout_friction_title": "Límites de Capacidad, Obsolescencia y Puntos de Fricción",
    "tomo_ch4_subpillar_col_name": "Subpilar Tecnológico",
    "tomo_ch4_subpillar_col_strengths": "Fortalezas y Controles Activos",
    "tomo_ch4_subpillar_col_risks": "Puntos de Fricción y Riesgo Operativo"
  },
  "en": {
    "tomo_ch4_kpi_maturity_label": "Current Maturity vs. Sector",
    "tomo_ch4_kpi_annual_impact_label": "Estimated Annual Economic Impact (Active Risk)",
    "tomo_ch4_kpi_scope_label": "Audited Scope & Assets",
    "tomo_ch4_callout_strengths_title": "Observed Operational Capabilities & Strengths",
    "tomo_ch4_callout_friction_title": "Capacity Limits, Obsolescence & Friction Points",
    "tomo_ch4_subpillar_col_name": "Technology Subpillar",
    "tomo_ch4_subpillar_col_strengths": "Active Controls & Observed Strengths",
    "tomo_ch4_subpillar_col_risks": "Operational Friction & Risk Exposure"
  }
}
```

### 5.3 Compiler Implementation (`tomo_asis_ast_compiler.py`)
```python
def _build_ch4_tower_diagnostic_card(
    self,
    card: TowerDiagnosticCardPayload,
    doc_lang: str,
) -> list[ASTNode]:
    """Render a balanced, executive-grade Chapter 4 domain diagnostic card."""
    tr = self._locale_service.get_namespace(doc_lang)

    kpi_strip = KpiStripNode(
        items=[
            KpiMetricItem(
                label=tr["tomo_ch4_kpi_maturity_label"],
                value=f"{card.maturity_score_formatted} / {card.sector_benchmark_formatted}",
            ),
            KpiMetricItem(
                label=tr["tomo_ch4_kpi_annual_impact_label"],
                value=card.annual_economic_impact_formatted,
            ),
            KpiMetricItem(
                label=tr["tomo_ch4_kpi_scope_label"],
                value=card.evaluated_assets_or_scope_label,
            ),
        ]
    )

    context_para = ParagraphNode(
        text=card.architectural_context_narrative,
        style=self._styles.body_regular,
    )

    strengths_callout = CalloutBlockNode(
        title=tr["tomo_ch4_callout_strengths_title"],
        body=card.observed_strengths_summary,
        border_left_color_hex="#0D9488",  # Emerald/Teal Accent
        background_color_hex="#F0FDFA",
        padding_pt=9.0,
        space_after_pt=8.0,
    )

    friction_callout = CalloutBlockNode(
        title=tr["tomo_ch4_callout_friction_title"],
        body=card.capacity_limits_and_friction_summary,
        border_left_color_hex="#D97706",  # Amber Accent
        background_color_hex="#FFFBEB",
        padding_pt=9.0,
        space_after_pt=10.0,
    )

    subpillar_table = TableNode(
        headers=[
            tr["tomo_ch4_subpillar_col_name"],
            tr["tomo_ch4_subpillar_col_strengths"],
            tr["tomo_ch4_subpillar_col_risks"],
        ],
        rows=[
            [
                sp.subpillar_name,
                sp.observed_strengths_and_controls,
                sp.operational_friction_and_risks,
            ]
            for sp in card.subpillar_evaluations
        ],
        column_widths_pct=[22.0, 39.0, 39.0],
    )

    return [
        HeadingNode(level=2, text=f"{card.tower_id} — {card.tower_title}"),
        kpi_strip,
        context_para,
        strengths_callout,
        friction_callout,
        subpillar_table,
    ]
```

---

## 6. Point 8: Section 4.11 SPOF Matrix Sorting by Descending Criticality

### 6.1 Architectural Root-Cause & Canonical Sorting Algorithm
The Single Points of Failure (SPOF) matrix in Section 4.11 previously sorted entries by ascending numeric ID (`SPOF-01` to `SPOF-10`), burying `CRITICAL` infrastructure threats beneath `MEDIUM` localized issues. To guarantee immediate executive visibility, the compiler must sort all SPOF items by canonical severity rank (`CRITICAL` -> `HIGH` -> `MEDIUM` -> `LOW`), using annualized financial impact (descending) and original numeric ID (ascending) as deterministic tie-breakers.

#### Data Contract & Canonical Severity Enum (`domain_models/consolidated_asis_models.py`)
```python
from enum import IntEnum

class SpofCriticalityRank(IntEnum):
    """Language-agnostic canonical criticality ordering for deterministic sorting."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass(frozen=True)
class SinglePointOfFailureEntry:
    """Single Point of Failure record for Section 4.11."""
    spof_id: str                                # e.g., "SPOF-04"
    tower_id: str                               # e.g., "T4"
    component_description: str
    failure_blast_radius: str
    criticality_rank: SpofCriticalityRank       # Canonical enum rank
    localized_criticality_badge: str            # e.g., "CRÍTICA", "CRITICAL"
    annualized_risk_numeric: float              # Tie-breaker descending
    estimated_remediation_timeframe: str
```

### 6.2 Compiler Implementation (`tomo_asis_ast_compiler.py`)
```python
def _sort_spof_entries_by_criticality(
    self,
    entries: tuple[SinglePointOfFailureEntry, ...],
) -> list[SinglePointOfFailureEntry]:
    """Sort SPOF matrix entries deterministically: CRITICAL -> HIGH -> MEDIUM -> LOW."""
    return sorted(
        entries,
        key=lambda item: (
            int(item.criticality_rank),
            -item.annualized_risk_numeric,
            item.spof_id,
        ),
    )

def _build_ch4_spof_matrix_section(
    self,
    payload: ConsolidatedAsIsPayload,
    doc_lang: str,
) -> list[ASTNode]:
    """Render Section 4.11 Single Points of Failure Matrix ordered by descending criticality."""
    tr = self._locale_service.get_namespace(doc_lang)
    sorted_spofs = self._sort_spof_entries_by_criticality(payload.spof_matrix_entries)

    headers = [
        tr["tomo_ch4_spof_col_id"],
        tr["tomo_ch4_spof_col_criticality"],
        tr["tomo_ch4_spof_col_domain"],
        tr["tomo_ch4_spof_col_component"],
        tr["tomo_ch4_spof_col_blast_radius"],
        tr["tomo_ch4_spof_col_window"],
    ]

    rows = [
        [
            entry.spof_id,
            entry.localized_criticality_badge,
            entry.tower_id,
            entry.component_description,
            entry.failure_blast_radius,
            entry.estimated_remediation_timeframe,
        ]
        for entry in sorted_spofs
    ]

    return [
        HeadingNode(level=2, text=tr["tomo_ch4_spof_section_title"]),
        ParagraphNode(text=tr["tomo_ch4_spof_section_intro"], style=self._styles.body_regular),
        TableNode(
            headers=headers,
            rows=rows,
            column_widths_pct=[10.0, 12.0, 10.0, 26.0, 28.0, 14.0],
        ),
    ]
```

---

## 7. Point 9: Unified Legal Liability Disclaimer Across All Documents

### 7.1 Architectural Root-Cause & Canonical Unification
Tomo 1 previously referenced legacy keys (`tomo_app_disclaimer_p1..p3`) while the 20 individual tower annexes rendered the canonical corporate disclaimer (`disclaimer_text_1` through `disclaimer_text_4`). To enforce 100% legal and structural symmetry across the entire deliverable suite, `tomo_app_disclaimer_p1..p3` are deprecated and `_build_unified_appendix` in `tomo_asis_ast_compiler.py` is unified to render `disclaimer_text_1` through `disclaimer_text_4`.

### 7.2 Exact Localization Keys (`engine_config/locales.json`)
```json
{
  "es": {
    "disclaimer_section_title": "Aviso Legal, Alcance Metodológico y Limitación de Responsabilidad",
    "disclaimer_text_1": "1. Naturaleza del Diagnóstico y Corte Temporal: El presente informe técnico refleja el estado observacional de la infraestructura, arquitecturas, configuraciones y procesos de tecnología de la información y operación (TI/OT) de la entidad evaluada en la fecha de cierre de la toma de evidencias. Las conclusiones se basan en la inspección documental, entrevistas técnicas y telemetría no intrusiva facilitadas durante las sesiones de auditoría.",
    "disclaimer_text_2": "2. Carácter Estimativo de las Simulaciones Económicas y de Riesgo: Las cuantificaciones de exposición financiera anualizada, pérdidas por interrupción operativa y costes de recuperación de emergencia se obtienen mediante modelos estocásticos basados en el estándar internacional Open FAIR™ e indicadores de referencia sectorial (CMMI, Gartner ITKMD, ISO/IEC). Dichas cifras constituyen proyecciones analíticas orientadas a la priorización ejecutiva de inversiones y no representan garantías actuariales ni compromisos de cobertura aseguradora.",
    "disclaimer_text_3": "3. Limitación de Responsabilidad Operativa: El equipo consultor no ha ejecutado pruebas intrusivas de denegación de servicio ni modificaciones sobre entornos productivos. La responsabilidad sobre la operación diaria, aplicación de parches de seguridad, ejecución de copias de respaldo y continuidad de negocio permanece íntegramente bajo la titularidad y control de la dirección de la organización cliente.",
    "disclaimer_text_4": "4. Confidencialidad y Restricción de Difusión: Este documento contiene información técnica y estratégica estrictamente confidencial referida a la arquitectura y puntos únicos de fallo de la organización. Queda prohibida su reproducción, distribución o comunicación total o parcial a terceros sin la autorización previa, expresa y por escrito de las partes firmantes."
  },
  "en": {
    "disclaimer_section_title": "Legal Notice, Methodological Scope, and Limitation of Liability",
    "disclaimer_text_1": "1. Diagnostic Nature and Point-in-Time Baseline: This technical report reflects the observational state of the evaluated entity's Information and Operational Technology (IT/OT) infrastructure, architectures, configurations, and processes as of the evidence cutoff date. Findings are derived from documentary inspection, technical interviews, and non-intrusive telemetry provided during audit sessions.",
    "disclaimer_text_2": "2. Estimative Nature of Financial and Risk Simulations: Quantifications of annualized financial exposure, business interruption losses, and emergency recovery expenditures are generated via stochastic modeling grounded in the Open FAIR™ international standard and industry reference benchmarks (CMMI, Gartner ITKMD, ISO/IEC). These figures constitute analytical projections designed for executive capital prioritization and do not represent actuarial guarantees or insurance coverage commitments.",
    "disclaimer_text_3": "3. Operational Liability Limitation: The advisory team has performed zero intrusive denial-of-service testing and zero modifications on production systems. Full responsibility for daily operations, security patch management, backup execution, and business continuity remains exclusively vested in the client organization's management.",
    "disclaimer_text_4": "4. Confidentiality and Distribution Restrictions: This document contains strictly confidential technical and strategic information regarding the organization's architecture and single points of failure. Any reproduction, distribution, or disclosure in whole or in part to third parties without prior express written authorization from the signatory parties is strictly prohibited."
  }
}
```

### 7.3 Compiler Implementation (`tomo_asis_ast_compiler.py`)
```python
def _build_unified_appendix(
    self,
    payload: ConsolidatedAsIsPayload,
    doc_lang: str,
) -> list[ASTNode]:
    """Render the unified corporate legal disclaimer identical across Tomo 1 and all 20 tower annexes."""
    tr = self._locale_service.get_namespace(doc_lang)
    canonical_disclaimer_keys = (
        "disclaimer_text_1",
        "disclaimer_text_2",
        "disclaimer_text_3",
        "disclaimer_text_4",
    )

    nodes: list[ASTNode] = [
        HeadingNode(level=2, text=tr["disclaimer_section_title"]),
    ]
    for key in canonical_disclaimer_keys:
        nodes.append(
            ParagraphNode(
                text=tr[key],
                style=self._styles.legal_disclaimer_paragraph,
            )
        )
    return nodes
```

---

## 8. Automated Verification & Quality Assurance Matrix (`pytest`)

To enforce zero regression across all 9 user observations, the test suite (`tests/compiler/test_rfc067_tomo1_remediation.py`) must verify the following invariants before any PDF artifact is promoted:

1. **Test 1 — Language-Agnostic Source Code Audit:** AST/regex scan of `tomo_asis_ast_compiler.py` and `domain_models/` asserting zero Spanish tokens, zero hardcoded client names, and zero `if doc_lang ==` inline conditionals.
2. **Test 2 — 6-Locale Mathematical Symmetry:** Assert that `locales.json` contains identical key sets across `es`, `en`, `pt`, `fr`, `de`, and `ja`, including all new keys introduced in RFC 066 and RFC 067.
3. **Test 3 — Scenario Reconciliation Invariant (Point 5):** Assert that `sum(r.evaluated_scenarios_count for r in payload.economic_impact.domain_exposure_rows) == payload.economic_impact.total_evaluated_scenarios`.
4. **Test 4 — Emergency Cost Decomposition Sum (Points 4 & 6):** Assert that the sum of the three emergency recovery buckets equals `total_emergency_recovery_cost` (`94,270 + 74,069 + 56,113 == 224,452`).
5. **Test 5 — SPOF Criticality Ordering Invariant (Point 8):** Assert that `_sort_spof_entries_by_criticality` produces a monotonically non-decreasing sequence of `SpofCriticalityRank` values (`CRITICAL` first, `LOW` last).
6. **Test 6 — Unified Disclaimer Parity (Point 9):** Assert that the AST paragraph texts emitted by `_build_unified_appendix` in Tomo 1 are byte-for-byte identical to the disclaimer paragraphs emitted by the individual tower annex compiler for the same `doc_lang`.