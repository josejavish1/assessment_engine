# RFC 066: Universal Executive Architecture & Visual Parity Specification for Consolidated Tomo 1 AS-IS

**Status:** Definitive Architectural Blueprint  
**Target System:** Universal Multi-Tenant Enterprise Architecture Compiler  
**Scope:** Consolidated Tomo 1 AS-IS Technical Diagnostic (`tomo_asis_ast_compiler.py`, `locales.json`, Domain Data Contracts)  
**Compliance Invariants:** 100% Technical English Codebase | Zero Hardcoded Tenant Constants | 6-Locale Mathematical Symmetry (`es`, `en`, `pt`, `fr`, `de`, `ja`) | Strict Mandatory `doc_lang: str` Propagation

---

## 1. Visual Cover Page Specification (Observation 1: FNMT CERES Parity)

### 1.1 Forensic Visual Deconstruction & Typographic Tokens
To eradicate the academic, centered, gray-boxed layout and achieve exact visual parity with the Tier-1 benchmark (`fnmt_ceres_as_is_consolidated_report_v1.1.pdf`), the cover page AST builder (`_build_cover_page`) must enforce asymmetrical left-aligned editorial geometry with calibrated vertical rhythm.

#### Design Token Definitions (`CoverTypographyTokens`):
* **Page Margins:** Left `54.0 pt` (19.05 mm), Right `54.0 pt`, Top `36.0 pt`, Bottom `36.0 pt`.
* **Header Band (Dual Branding):**
  * Top-Left: Advisory Firm Logo (`max_height: 32.0 pt`, left-aligned).
  * Top-Right: Client Entity Logo (`max_height: 36.0 pt`, right-aligned).
* **Primary Vertical Offset:** `Spacer(height_pt=142.0)` (~28.5% down an A4 page of `841.89 pt` height).
* **Main Title Block (`cover_title_line_1..3`):**
  * Alignment: `LEFT`
  * Font Family: `Arial-Bold` / `Helvetica-Bold` (Clean Sans-Serif)
  * Font Size: `31.0 pt`
  * Line Height / Leading: `36.0 pt` (`1.16x` ratio)
  * Color: `#0072BC` (Corporate Primary Blue, dynamically overridable via `tenant_profile.brand_primary_hex`)
  * Spacing After Title Block: `18.0 pt`
* **Entity Subtitle Hierarchy:**
  * **Line 1 (Client Legal Entity Name):**
    * Alignment: `LEFT` | Font: `Arial-Bold` | Size: `14.0 pt` | Leading: `18.0 pt` | Color: `#1A1A1A` (Deep Charcoal)
  * **Line 2 (Division / Organisational Scope):**
    * Alignment: `LEFT` | Font: `Arial-Regular` | Size: `12.0 pt` | Leading: `16.0 pt` | Color: `#333333` (Muted Charcoal)
* **Primary Whitespace Chasm:**
  * `Spacer(height_pt=258.0)` (Pushes the metadata line down to ~79% of the vertical page height).
* **Minimalist Single-Line Metadata:**
  * Alignment: `LEFT` | Font: `Arial-Regular` | Size: `11.0 pt` | Leading: `14.0 pt` | Color: `#333333`
  * Format String: `"{formatted_date} | {version_label} {document_version}"` (e.g., `"02 diciembre 2025 | Version 1.1"`).
  * **Strict Prohibition:** Zero background shading, zero borders, zero tables, zero left accent bars.

---

### 1.2 AST Node Hierarchy & Dynamic Payload Bindings (`tomo_asis_ast_compiler.py`)

```python
def _build_cover_page(
    self,
    payload: ConsolidatedAsIsPayload,
    doc_lang: str,
) -> list[ASTNode]:
    """Build the Tier-1 asymmetrical left-aligned executive cover page AST."""
    tr = self._locale_service.get_namespace(doc_lang)
    brand_primary = payload.tenant_metadata.primary_color_hex or "#0072BC"

    nodes: list[ASTNode] = [
        # 1. Dual Corporate Branding Header (Top-Left Advisory, Top-Right Client)
         DualBrandHeaderNode(
             advisory_logo_path=payload.tenant_metadata.advisory_logo_path,
             client_logo_path=payload.tenant_metadata.client_logo_path,
             advisory_max_height_pt=32.0,
             client_max_height_pt=36.0,
         ),
        # 2. Upper Vertical Offset (~28.5% down A4 page)
        SpacerNode(height_pt=142.0),
        # 3. 3-Line Left-Aligned Primary Title Block (#0072BC, 31pt, 1.16 line-height)
        ParagraphNode(
            text=tr["tomo_cover_title_line_1"],
            style=ParagraphStyleSpec(
                font_name="Helvetica-Bold",
                font_size_pt=31.0,
                leading_pt=36.0,
                text_color_hex=brand_primary,
                alignment="LEFT",
                space_after_pt=0.0,
            ),
        ),
        ParagraphNode(
            text=tr["tomo_cover_title_line_2"],
            style=ParagraphStyleSpec(
                font_name="Helvetica-Bold",
                font_size_pt=31.0,
                leading_pt=36.0,
                text_color_hex=brand_primary,
                alignment="LEFT",
                space_after_pt=0.0,
            ),
        ),
        ParagraphNode(
            text=payload.tenant_metadata.assessment_scope_title,
            style=ParagraphStyleSpec(
                font_name="Helvetica-Bold",
                font_size_pt=31.0,
                leading_pt=36.0,
                text_color_hex=brand_primary,
                alignment="LEFT",
                space_after_pt=18.0,
            ),
        ),
        # 4. Entity Subtitle Hierarchy (Legal Entity + Organizational Division)
        ParagraphNode(
            text=payload.tenant_metadata.client_legal_name,
            style=ParagraphStyleSpec(
                font_name="Helvetica-Bold",
                font_size_pt=14.0,
                leading_pt=18.0,
                text_color_hex="#1A1A1A",
                alignment="LEFT",
                space_after_pt=4.0,
            ),
        ),
        ParagraphNode(
            text=payload.tenant_metadata.client_division_scope,
            style=ParagraphStyleSpec(
                font_name="Helvetica",
                font_size_pt=12.0,
                leading_pt=16.0,
                text_color_hex="#333333",
                alignment="LEFT",
                space_after_pt=0.0,
            ),
        ),
        # 5. Editorial Whitespace Chasm (~258pt)
        SpacerNode(height_pt=258.0),
        # 6. Minimalist Borderless Single-Line Metadata (~79% down page)
        ParagraphNode(
            text=(
                f"{payload.tenant_metadata.formatted_publication_date} | "
                f"{tr['tomo_cover_version_prefix']} {payload.tenant_metadata.document_version}"
            ),
            style=ParagraphStyleSpec(
                font_name="Helvetica",
                font_size_pt=11.0,
                leading_pt=14.0,
                text_color_hex="#333333",
                alignment="LEFT",
                space_after_pt=0.0,
            ),
        ),
        PageBreakNode(),
    ]
    return nodes
```

### 1.3 Multi-Modal Visual Verification Loop (`pdftoppm` Parity Gate)
To guarantee that the rendered PDF cover matches the FNMT CERES reference visually and structurally:
1. **Rasterization Step:**
   ```bash
   pdftoppm -png -r 150 -f 1 -l 1 output/tomo_1_as_is_consolidated.pdf output/audit_cover_rendered
   pdftoppm -png -r 150 -f 1 -l 1 source_docs/reference_reports/fnmt_ceres_as_is_consolidated_report_v1.1.pdf output/ref_fnmt_cover
   ```
2. **Automated Geometric & Bounding-Box Assertions (`tests/visual/test_cover_layout_parity.py`):**
   * Extract text bounding boxes via `pypdf`/`pdfplumber` on page 1.
   * Assert `x0` of all title, subtitle, and metadata lines equals `54.0 pt ± 0.5 pt` (strict left alignment).
   * Assert title `y0` starts within `[220.0 pt, 260.0 pt]` from top edge.
   * Assert metadata `y0` sits within `[640.0 pt, 690.0 pt]` from top edge.
   * Assert zero rectangular fill/stroke graphics (`len(page.rects) == 0`) exist in the bottom half of page 1 (confirming eradication of the legacy gray metadata box).

---

## 2. Itemized Systemic Remediation Plan (Observations 2 through 9)

### Observation 2: Chapter 1 (Executive Summary) — Local Facility vs. Consolidated Group Hourly Downtime

* **Root Cause:** The executive summary juxtaposed two distinct financial impact velocities (`local_site_hourly_burn_eur` and `consolidated_group_hourly_burn_eur`) in a single clause without explaining the architectural boundary separating an isolated site outage from a central core ERP/billing outage.
* **Compiler & Data Contract Update:**
  * Inject dynamic parameters `{local_site_hourly_rate}` and `{consolidated_hourly_rate}` into `tomo_ch1_continuity_bullet_body` in `locales.json`.
* **Localized Wording Specification:**
  * **Spanish (`es`):**
    > *"Continuidad Operativa en Centros Operativos y Expedición: Los sistemas locales de pesaje, control de accesos y despacho operan con dependencias directas de conectividad y equipamiento próximo al fin de soporte. Una interrupción aislada en un centro operativo detiene físicamente la báscula y la expedición local de mercancía, generando un impacto directo estimado de {local_site_hourly_rate}/h por planta afectada. Por su parte, una caída de los servicios centrales (ERP corporativo, facturación y gestión consolidada de pedidos) paraliza la capacidad transaccional de toda la organización, elevando el impacto operativo a {consolidated_hourly_rate}/h a nivel consolidado de grupo."*
  * **English (`en`):**
    > *"Operational Continuity at Operating Facilities and Dispatch: Local weighing, access control, and dispatch systems operate with direct connectivity dependencies and hardware approaching end-of-support. An isolated outage at a single operating facility physically halts weighbridges and local goods dispatch, generating an estimated direct impact of {local_site_hourly_rate}/h per affected site. Conversely, an outage of central corporate services (core ERP, billing, and consolidated order management) halts transactional capacity across the entire enterprise, elevating the operational burn rate to {consolidated_hourly_rate}/h at the consolidated group level."*

---

### Observation 3: Chapter 2 (Maturity Radiography) — Industry Benchmark Source & Methodological Credibility

* **Root Cause:** Table 2 displayed `"Desviación vs. Sector"` against a `3.50` target baseline without citing the empirical reference framework, peer group criteria, or standard maturity taxonomy.
* **Compiler & Data Contract Update:**
  * Add `BenchmarkMethodologyMetadata` to the domain model (`benchmark_framework_name`, `benchmark_target_score`, `industry_vertical_label`, `peer_sample_description`).
  * Update `_build_chapter_2_maturity_radiography` to render a dedicated methodological justification paragraph immediately preceding the Maturity Table.
* **Localized Wording Specification (`tomo_ch2_benchmark_methodology_note`):**
  * **Spanish (`es`):**
    > *"Nota Metodológica sobre el Benchmark Sectorial: El umbral de referencia establecido en {benchmark_score} puntos (sobre una escala de 5,00) se fundamenta en el marco internacional CMMI v2.0 (Capability Maturity Model Integration, Nivel 3 — Definido y Estandarizado) cruzado con las métricas comparativas de Gartner IT Key Metrics Data e ISO/IEC 20000/27001 para organizaciones industriales y de distribución de escala equivalente ({industry_vertical_label}). Este nivel representa el estándar exigible para garantizar operaciones predecibles, resiliencia ante fallos sin dependencia de esfuerzos individuales y trazabilidad documental completa."*
  * **English (`en`):**
    > *"Methodological Note on the Industry Benchmark: The reference baseline established at {benchmark_score} points (on a 5.00 scale) is grounded in the international CMMI v2.0 framework (Capability Maturity Model Integration, Level 3 — Defined and Standardized) cross-referenced with comparative metrics from Gartner IT Key Metrics Data and ISO/IEC 20000/27001 for industrial and distribution enterprises of equivalent scale ({industry_vertical_label}). This threshold represents the required operational standard to ensure predictable service delivery, fault resilience independent of individual heroics, and full documentary traceability."*

---

### Observation 4 & Observation 6: Chapter 3 & Section 3.2.1 — Plain-Language Executive Restructuring & Transparent Decomposition of Emergency Recovery Costs (224.452 €)

* **Root Cause:** Chapter 3 relied on dense actuarial terminology (Open FAIR, SLE, TEF, loss exceedance curves) and presented the `224.452 €` emergency response figure as an unitemized lump sum, raising CFO/CIO skepticism.
* **Empirical Decomposition of the Emergency Response Figure (`EmergencyRecoveryBreakdown`):**
  The `224.452 €` figure in a severe major incident (P95/P99 multi-tower outage) is no longer presented as a black-box constant. The compiler dynamically decomposes `emergency_response_total_eur` across three transparent, contract-grounded operational buckets configured in the tenant risk model:
  1. **Activación de Ingeniería de Emergencia y Soporte Crítico de Fabricante (OEM 24x7 Fuera de SLA Estándar) — ~42% (`94.270 €`):** Tarifas de intervención inmediata ("Best-Effort Emergency Escalation") para activos sin cobertura 24x7 o en Fin de Soporte (EoL), incluyendo ingenieros de guardia de nivel 3 de los fabricantes de almacenamiento, virtualización y red.
  2. **Logística Urgente de Hardware y Sustitución de Componentes Críticos en Caliente — ~33% (`74.069 €`):** Adquisición de emergencia a precio spot, transporte dedicado en el mismo día (couriers críticos) y despliegue en campo de nodos de cómputo, fuentes de alimentación industriales, switches de planta o electrónicas de báscula no cubiertas por stock local de repuestos.
  3. **Servicios Especializados de Recuperación, Reconstrucción de Datos y Triaje Forense — ~25% (`56.113 €`):** Intervención de equipos externos de respuesta a incidentes (DFIR), restauración de bases de datos transaccionales corruptas, validación de integridad de backups y horas extraordinarias de reconfiguración de red en todas las sedes afectadas.
  * **Total Exacto:** `94.270 € + 74.069 € + 56.113 € = 224.452 €`.
* **Restructured Chapter 3 Narrative Architecture:**
  * **Section 3.0 (Executive Introduction):** Translates stochastic modeling into three executive questions:
    1. *¿Cuál es el coste anual oculto de mantener la infraestructura actual sin cambios?* (Coste de la Inacción / Exposición Anualizada).
    2. *¿Cuál es la factura real si sufrimos una caída grave en un sistema crítico?* (Anatomía de un Incidente Mayor: Negocio Interrumpido + Gastos de Emergencia).
    3. *¿Dónde genera mayor retorno cada euro invertido en remediación?* (Priorización de Capital por Dominio).
* **Localized Wording Specification for Section 3.2.1 (`tomo_ch3_major_incident_anatomy_body`):**
  * **Spanish (`es`):**
    > *"En caso de materializarse una interrupción severa sobre los sistemas centrales o de expedición (escenario de estrés con una duración estimada de {outage_hours} horas), el impacto financiero total asciende a {total_event_loss}, dividido en dos bloques claramente diferenciados:*
    > *1. Lucro Cesante y Paralización Operativa ({operational_interruption_loss}): Pérdida directa de margen comercial y penalizaciones operativas derivadas de la imposibilidad de pesar, facturar y expedir mercancía durante la ventana de caída ({consolidated_hourly_rate}/h).*
    > *2. Costes Extraordinarios de Recuperación de Emergencia ({emergency_response_cost}): Gasto directo de bolsillo necesario para restituir el servicio de forma urgente cuando los equipos carecen de redundancia automática o soporte preventivo vigente. Este importe se desglosa en: (a) {oem_escalation_cost} por contratación de emergencia de ingeniería de Nivel 3 del fabricante fuera de contrato estándar; (b) {urgent_hardware_logistics_cost} por compra urgente y transporte dedicado de equipamiento de reemplazo (servidores, electrónica de red o pesaje); y (c) {forensic_recovery_services_cost} en servicios externos de recuperación de bases de datos, validación de integridad y despliegue intensivo en planta."*
  * **English (`en`):**
    > *"Should a severe outage materialize across central or dispatch systems (stress scenario with an estimated duration of {outage_hours} hours), the total financial impact reaches {total_event_loss}, divided into two distinct categories:*
    > *1. Business Interruption and Lost Operating Margin ({operational_interruption_loss}): Direct loss of commercial margin and operational penalties resulting from the inability to weigh, bill, and dispatch goods during the downtime window ({consolidated_hourly_rate}/h).*
    > *2. Extraordinary Emergency Recovery Costs ({emergency_response_cost}): Direct out-of-pocket expenditure required to restore service urgently when systems lack automated failover or active preventive support. This expenditure breaks down into: (a) {oem_escalation_cost} for emergency engagement of Level-3 OEM manufacturer engineering outside standard SLA coverage; (b) {urgent_hardware_logistics_cost} for spot procurement and dedicated courier dispatch of replacement hardware (compute nodes, network switches, or industrial weighing electronics); and (c) {forensic_recovery_services_cost} for external database recovery specialists, integrity validation, and intensive on-site engineering deployment."*

---

### Observation 5: Section 3.1 — Reconciling 29 Evaluated Risk Scenarios with the 10 Displayed Domain Rows

* **Root Cause:** The prose stated that 29 discrete risk scenarios were evaluated, while Table 4 displayed 10 rows (one per technology tower T1–T10), causing apparent discrepancy for first-time executive readers.
* **Compiler Update:**
  * Inject `{total_scenarios_count}` (e.g., `29`) and `{total_domains_count}` (e.g., `10`) into the introductory paragraph of Section 3.1, and ensure Table 4 includes an explicit column `"Escenarios Evaluados"` (`"Evaluated Scenarios"`) whose sum across the 10 rows equals `29` in the table footer row (`TOTAL CONSOLIDADO`).
* **Localized Wording Specification (`tomo_ch3_sec31_reconciliation_bridge`):**
  * **Spanish (`es`):**
    > *"El modelo de simulación evalúa {total_scenarios_count} escenarios de fallo técnico específicos (tales como caída de enlaces WAN en plantas, saturación de almacenamiento hiperconvergente o fallo en básculas de expedición) distribuidos a través de toda la infraestructura de la organización. Para facilitar la asignación presupuestaria y la toma de decisiones ejecutivas, la Tabla 4 agrupa y consolida estos {total_scenarios_count} escenarios individuales dentro de los {total_domains_count} dominios tecnológicos principales, detallando cuántos escenarios activos concentra cada área y su impacto económico anualizado acumulado."*
  * **English (`en`):**
    > *"The simulation model evaluates {total_scenarios_count} specific technical failure scenarios (such as plant WAN link outages, hyperconverged storage saturation, or dispatch weighbridge failures) distributed across the enterprise infrastructure. To streamline budget allocation and executive decision-making, Table 4 aggregates and consolidates these {total_scenarios_count} individual scenarios into the {total_domains_count} core technology domains, detailing the number of active scenarios per domain and their cumulative annualized economic impact."*

---

### Observation 7: Chapter 4 (Domain Cards) — Intuitive Risk Labeling, Highlighting Operational Strengths, and Richer Narrative

* **Root Cause:**
  1. KPI Strip used opaque actuarial shorthand (`"Exposición ALE"`).
  2. Domain diagnostic cards only listed deficiencies/gaps, ignoring operational strengths, stabilized platforms, and internal team capabilities.
* **Compiler & Schema Update (`_build_chapter_4_domain_cards`):**
  1. **KPI Strip Header Rename:** Replace `"Exposición ALE"` / `"ALE Anual"` with `tr["tomo_ch4_kpi_annual_risk_exposure"]`:
     * `es`: `"Impacto Económico Anual Estimado (Riesgo Activo)"`
     * `en`: `"Estimated Annual Economic Impact (Active Risk)"`
  2. **Balanced Two-Part Narrative Block per Tower Card:**
     Every tower card in Chapter 4 now renders two structured executive callout blocks above the Subpillar Deep-Dive Table:
     * **Block A (`tomo_ch4_strengths_heading`):** *"Capacidades Operativas y Fortalezas Observadas"* / *"Observed Operational Capabilities & Strengths"* (Rendered with subtle Emerald/Teal left accent border `#1E7E34`, highlighting active standards, working platforms, recent modernizations, and operational resilience).
     * **Block B (`tomo_ch4_friction_heading`):** *"Límites de Capacidad, Obsolescencia y Puntos de Fricción"* / *"Capacity Limits, Obsolescence & Operational Friction Points"* (Rendered with Amber/Slate accent border `#B45309`, detailing objective technical debt, EoL hardware, and single points of failure).
  3. **Enriched 3-Column Subpillar Table:**
     Expand the domain table columns to:
     `[Subpilar Evaluado | Capacidades Actuales y Controles Activos | Puntos de Fricción y Riesgo Operativo]`.

---

### Observation 8: Section 4.11 (SPOF Matrix) — Deterministic Sorting by Descending Criticality

* **Root Cause:** `_build_spof_matrix` iterated over SPOF records in ascending numerical/tower order (`SPOF-01` to `SPOF-10`), burying `CRÍTICA` items below `MEDIA` items.
* **Algorithmic Specification (`tomo_asis_ast_compiler.py`):**
  Define a canonical, language-independent criticality severity rank map in the domain layer (`CriticalityLevel` enum) and sort before rendering the table:

```python
CRITICALITY_SORT_RANK: Final[dict[str, int]] = {
    "CRITICAL": 0,
    "CRÍTICA": 0,
    "CRITICA": 0,
    "HIGH": 1,
    "ALTA": 1,
    "MEDIUM": 2,
    "MEDIA": 2,
    "LOW": 3,
    "BAJA": 3,
}

def _sort_spof_entries(
    entries: Sequence[SpofMatrixEntry],
) -> list[SpofMatrixEntry]:
    """Sort SPOF entries deterministically by descending criticality, then by descending financial impact, then by ID."""
    return sorted(
        entries,
        key=lambda item: (
            CRITICALITY_SORT_RANK.get(item.criticality_code.upper().strip(), 99),
            -item.annualized_impact_eur,
            item.spof_id,
        ),
    )
```
* **Visual Enhancement:** Ensure the `Criticidad` badge cell uses semantic executive styling (`CRÍTICA`: `#991B1B` bold text on `#FEE2E2` pill; `ALTA`: `#9A3412` on `#FFEDD5`; `MEDIA`: `#854D0E` on `#FEF9C3`).

---

### Observation 9: Unified Legal Liability Disclaimer Across All Deliverables

* **Root Cause:** `_build_unified_appendix` in `tomo_asis_ast_compiler.py` referenced bespoke locale keys (`tomo_app_disclaimer_p1..p3`), diverging from the canonical 4-paragraph legal disclaimer (`disclaimer_text_1` through `disclaimer_text_4`) used in the 20 individual tower annexes.
* **Compiler Remediation:**
  * Refactor `_build_unified_appendix` in `tomo_asis_ast_compiler.py` to iterate over `("disclaimer_text_1", "disclaimer_text_2", "disclaimer_text_3", "disclaimer_text_4")` from `engine_config/locales.json`, dynamically formatting `{client_name}` / `{organization_name}` identically to `annex_ast_compiler.py`.
  * Deprecate and remove `tomo_app_disclaimer_p1..p3` to eliminate Single-Source-of-Truth duplication.

---

## 3. Step-by-Step Implementation & Verification Sequence

### Phase 1: Multi-Lingual Catalog Synchronization (`engine_config/locales.json`)
1. Add/update all new and revised locale keys across all **6 supported languages** (`es`, `en`, `pt`, `fr`, `de`, `ja`) with 100% key-set parity:
   * `tomo_cover_title_line_1`, `tomo_cover_title_line_2`, `tomo_cover_version_prefix`
   * `tomo_ch1_continuity_bullet_body`
   * `tomo_ch2_benchmark_methodology_note`
   * `tomo_ch3_exec_intro_p1`, `tomo_ch3_sec31_reconciliation_bridge`, `tomo_ch3_major_incident_anatomy_body`
   * `tomo_ch4_kpi_annual_risk_exposure`, `tomo_ch4_strengths_heading`, `tomo_ch4_friction_heading`
2. Run locale symmetry verification test (`pytest tests/unit/test_locales_symmetry.py`) to confirm zero missing keys and identical placeholder signatures (`{...}`) across `es`, `en`, `pt`, `fr`, `de`, `ja`.

### Phase 2: Domain Data Contracts & Payload Hydrators
1. Extend `TenantMetadata` and `ConsolidatedAsIsPayload` in the domain schema (100% Technical English) to carry:
   * `assessment_scope_title: str`
   * `client_legal_name: str`
   * `client_division_scope: str`
   * `formatted_publication_date: str`
   * `local_site_hourly_rate_formatted: str`
   * `consolidated_hourly_rate_formatted: str`
   * `emergency_recovery_breakdown: EmergencyRecoveryBreakdown` (`oem_escalation_cost`, `urgent_hardware_logistics_cost`, `forensic_recovery_services_cost`)
   * `observed_strengths_narrative: str` and `subpillar_strengths: list[str]` per domain card.

### Phase 3: AST Compiler Refactoring (`tomo_asis_ast_compiler.py`)
1. Replace `_build_cover_page` with the asymmetrical left-aligned FNMT CERES specification.
2. Update `_build_chapter_1_executive_summary` to bind local vs. consolidated hourly downtime rates.
3. Update `_build_chapter_2_maturity_radiography` to inject the CMMI v2.0 / Gartner / ISO methodological paragraph.
4. Refactor `_build_chapter_3_economic_impact` to use plain-language executive structure, reconcile the 29 evaluated scenarios with the 10 domain rows in Table 4, and render the 3-part emergency recovery cost breakdown in Section 3.2.1.
5. Refactor `_build_chapter_4_domain_cards` to rename the ALE label, render the *"Capacidades Operativas y Fortalezas Observadas"* block alongside the friction block, and sort Section 4.11 SPOF Matrix via `_sort_spof_entries`.
6. Refactor `_build_unified_appendix` to render canonical `disclaimer_text_1..4`.

### Phase 4: Verification & Quality Gates
1. **Static & Architectural Invariant Audit:**
   * Verify zero hardcoded tenant strings, zero inline language conditionals (`if doc_lang ==`), and 100% Technical English identifiers.
2. **Full Test Suite Execution:**
   * Execute `pytest` across all 706+ unit, integration, and AST contract tests; enforce 100% pass rate.
3. **Visual Parity Inspection (`pdftoppm`):**
   * Compile the consolidated Tomo 1 PDF, convert page 1 to PNG via `pdftoppm -png -r 150`, and verify exact visual alignment against `fnmt_ceres_as_is_consolidated_report_v1.1.pdf`.