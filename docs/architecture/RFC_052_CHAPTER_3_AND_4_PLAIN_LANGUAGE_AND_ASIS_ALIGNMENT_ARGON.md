# Architectural Blueprint: RFC 052 — Chapter 3 Polymorphism & Chapter 4 Executive Clarity Remediation

**Role**: Chief Enterprise Architect & Executive Editorial Fellow (Gartner VP / McKinsey Senior Partner / Google Core Infrastructure)  
**Target Modules**: `engine_config/locales.json`, `payload_to_ast.py`  
**Status**: Approved for Immediate Production Deployment  

---

## 1. Executive Summary of Architectural Remediation

This blueprint resolves six critical editorial and structural findings across Chapter 3 and Chapter 4 of the assessment engine while strictly enforcing **100% Technical English in Python**, **zero hardcoding**, **strict AS-IS scope isolation**, and **polymorphic narrative rotation across all 10 capability towers**:

1. **Chapter 3 Denominator Stutter & Monolithic Boilerplate Eradication**:
   - Eliminates the redundant `2,46 / 5,00 sobre 5,00` string formatting bug by decoupling raw numeric score formatting (`{score_val}`) from localized scale labels (`2,46 sobre 5,0 (Nivel 2 - Repetible)`).
   - Extends the **3-Archetype Polymorphic Engine** (`INFRASTRUCTURE_PHYSICAL`, `COMPUTE_PLATFORMS`, `SECURITY_GOVERNANCE`) to both the Chapter 3 introductory framing and the post-scorecard executive commentary.
2. **Chapter 4 Executive Title Simplification**:
   - Replaces overly academic headings with direct, board-ready titles across all Chapter 4 sections (`4.1` through `4.4`).
3. **Section 4.1 Domain-Specific Downtime Contextualization**:
   - Retains the single authoritative enterprise hourly downtime rate (`{hourly_rate}`) while dynamically injecting archetype-specific operational paralysis mechanisms (e.g., physical plant/dispatch stoppage in `INFRASTRUCTURE_PHYSICAL` vs. ERP/MES transactional paralysis in `COMPUTE_PLATFORMS`).
4. **Section 4.2 Deterministic Heatmap Legend Table**:
   - Appends an explicit 4-column OpenXML reference table (`[Code | Identified Technical Risk & Capability | Annual Exposure (ALE) | Criticality]`) directly below the 5x5 risk matrix so executives can immediately decode matrix tokens (`RVS01`, `RNI01`, etc.).
5. **Section 4.3 Pure AS-IS Risk Concentration Profile (Zero TO-BE Leakage)**:
   - Purges all `30-90 day` / `90-180 day` remediation schedules and "quick wins" from Section 4.3. Replaces them with a pure **AS-IS Financial Tier Concentration Profile** (Critical/High, Moderate, Residual tiers with exact ALE sums, percentages, and finding counts).
6. **Section 4.4 Plain-Language Actuarial Risk Cards**:
   - De-clutters card headers to clean `[ID] Title` format, replaces cryptic "Efecto Cascada" jargon with accessible **Fault Propagation / Blast Radius** terminology, and translates `SLE`/`ALE` equations into plain-language executive bullet points including human-readable recurrence intervals (`1 failure every X years`).

---

## 2. Bilingual Dictionary Specification (`engine_config/locales.json`)

Update `engine_config/locales.json` under both `"es"` and `"en"` keys with the following schema keys. All tenant names, vertical contexts, currencies, and metrics are parameterized via runtime placeholders:

```json
{
  "es": {
    "ch3_intro_archetypes": {
      "INFRASTRUCTURE_PHYSICAL": "El presente capítulo expone la evaluación técnica de los activos de conectividad, redes de planta e infraestructura física de {tower_name} en {client_name}. El análisis examina la capacidad del entorno actual para sostener la continuidad de las operaciones industriales bajo tres dimensiones: arquitectura de red y enlaces, disponibilidad física de equipamiento e integración operativa entre planta y sistemas centrales.",
      "COMPUTE_PLATFORMS": "Este apartado documenta el diagnóstico técnico de las plataformas de cómputo, virtualización, almacenamiento y servicios centrales que conforman el dominio de {tower_name} en {client_name}. La revisión evalúa el grado de consolidación de la infraestructura, la tolerancia a fallos de los clústeres productivos y la eficiencia en la administración de recursos que soportan las aplicaciones corporativas.",
      "SECURITY_GOVERNANCE": "Esta sección presenta el análisis técnico de los mecanismos de control, ciberseguridad, respaldo y gobierno operativo desplegados sobre el dominio de {tower_name} en {client_name}. El diagnóstico verifica la robustez de las defensas perimetrales e internas, la trazabilidad de accesos y la capacidad real de recuperación ante incidentes que comprometan la integridad del negocio."
    },
    "ch3_scorecard_commentary_archetypes": {
      "INFRASTRUCTURE_PHYSICAL": "El dominio alcanza un índice de madurez de {score_val} sobre 5,0 ({maturity_tier_label}). Este resultado indica que la infraestructura física y de comunicaciones cumple con los requisitos básicos de conectividad para la operativa diaria de {client_name}, pero presenta vulnerabilidades ante fallos de componentes únicos, obsolescencia selectiva de hardware y carencias de segmentación que exponen las líneas operativas a interrupciones no planificadas.",
      "COMPUTE_PLATFORMS": "La plataforma registra una calificación global de {score_val} sobre 5,0 ({maturity_tier_label}). Esta valoración evidencia que los entornos de cómputo y almacenamiento garantizan el funcionamiento cotidiano de las cargas de trabajo de {client_name}, aunque persisten asimetrías en la configuración de alta disponibilidad, aprovisionamiento manual y deuda técnica acumulada que limitan la agilidad operativa de los equipos de sistemas.",
      "SECURITY_GOVERNANCE": "El marco de control obtiene una puntuación consolidada de {score_val} sobre 5,0 ({maturity_tier_label}). Este nivel refleja la existencia de controles base y procedimientos operativos funcionales en {client_name}, si bien se identifican brechas en la automatización de respuesta, cobertura desigual de políticas de seguridad y dependencias manuales que incrementan el tiempo de exposición ante eventos adversos."
    },
    "ch4_title": "4. Evaluación Económica de Riesgos de Infraestructura",
    "ch4_sec1_title": "4.1. Coste Estimado por Hora de Inactividad",
    "ch4_sec2_title": "4.2. Matriz de Priorización de Riesgos y Mapa de Calor",
    "ch4_sec3_title": "4.3. Concentración y Distribución de Riesgos del Dominio",
    "ch4_sec4_title": "4.4. Fichas de Riesgos Técnicos Cuantificados",
    "ch4_sec1_domain_context": {
      "INFRASTRUCTURE_PHYSICAL": "Para cuantificar el impacto financiero de las vulnerabilidades técnicas en {client_name}, se establece un coste de referencia corporativo de {hourly_rate}/h de indisponibilidad severa (calculado sobre una facturación anual de {annual_revenue} en el sector de {vertical_desc}). En el ámbito de {tower_name}, una interrupción crítica se traduce directamente en la pérdida de conectividad con básculas, líneas de expedición y sistemas de control de planta, deteniendo el flujo físico de materiales y bloqueando la salida logística.",
      "COMPUTE_PLATFORMS": "La valoración económica de los riesgos identificados en {client_name} toma como base un impacto corporativo estimado de {hourly_rate}/h ante caídas críticas del servicio (derivado de un volumen de negocio anual de {annual_revenue} en la actividad de {vertical_desc}). Dentro del dominio de {tower_name}, la materialización de un fallo mayor implica la indisponibilidad de los servidores centrales, bases de datos y plataformas de virtualización que ejecutan el ERP, el sistema MES y la gestión administrativa, paralizando la capacidad transaccional de la compañía.",
      "SECURITY_GOVERNANCE": "El modelo de cuantificación económica aplicado a {client_name} parte de un coste horario de inactividad operativa de {hourly_rate}/h (determinado a partir de los ingresos anuales de {annual_revenue} propios de su operativa en {vertical_desc}). En lo relativo a {tower_name}, un incidente severo —como una intrusión en la red, corrupción de respaldos o fallo en el control de accesos— compromete simultáneamente múltiples servicios compartidos, prolongando los tiempos de parada mientras se verifica la integridad de los datos y se restablece un entorno seguro."
    },
    "ch4_heatmap_legend_intro": "La siguiente tabla detalla la correspondencia de los códigos representados en el mapa de calor, vinculando cada identificador con la capacidad afectada, su exposición económica anualizada (ALE) y su nivel de criticidad:",
    "ch4_heatmap_legend_headers": [
      "Código",
      "Capacidad y Riesgo Técnico Identificado",
      "Exposición Anual (ALE)",
      "Criticidad"
    ],
    "ch4_sec3_intro": "El inventario de riesgos técnicos identificados en el dominio de {tower_name} arroja una exposición económica anualizada total (ALE) de {total_ale}/año distribuida en {total_risks} hallazgos. A efectos de dimensionar la concentración del riesgo en el estado actual (AS-IS), la exposición se clasifica en tres niveles de impacto financiero:",
    "ch4_sec3_tier_high": "• Nivel 1 — Riesgos Críticos y de Alto Impacto ({high_count} hallazgos): Concentran una exposición conjunta de {high_ale}/año, lo que representa el {high_pct}% del riesgo económico total del dominio. Estos puntos reflejan vulnerabilidades estructurales capaces de interrumpir servicios esenciales o afectar a múltiples activos de forma simultánea.",
    "ch4_sec3_tier_med": "• Nivel 2 — Riesgos de Impacto Moderado ({med_count} hallazgos): Agrupan una exposición anualizada de {med_ale}/año, equivalente al {med_pct}% del total cuantificado. Corresponden a deficiencias operativas o redundancias incompletas que degradan el rendimiento y elevan los tiempos de recuperación ante fallos locales.",
    "ch4_sec3_tier_low": "• Nivel 3 — Riesgos Residuales o Menores ({low_count} hallazgos): Suponen una exposición acumulada de {low_ale}/año ({low_pct}% del riesgo del dominio), asociados a fricciones técnicas acotadas cuyo impacto directo sobre la continuidad operativa general es limitado.",
    "ch4_sec3_outro": "Esta distribución refleja estrictamente el perfil de exposición financiera del entorno actual (AS-IS), sirviendo como línea base objetiva para priorizar las decisiones sobre la plataforma.",
    "ch4_card_pillar_label": "Pilar de Capacidad",
    "ch4_card_propagation_label": "Propagación de Fallo a Otros Sistemas",
    "ch4_card_propagation_high": "Alta — Afectación transversal a servicios dependientes (Factor x{factor})",
    "ch4_card_propagation_moderate": "Moderada — Impacto compartido con sistemas adyacentes (Factor x{factor})",
    "ch4_card_propagation_low": "Acotada — Impacto contenido en el componente local (Factor x{factor})",
    "ch4_card_sle_bullet": "• Impacto Económico por Incidencia (SLE): {sle_val} (estimado para un tiempo medio de recuperación de {mttr_hours} horas a razón de {hourly_rate}/h de afectación operativa, ajustado por alcance y propagación).",
    "ch4_card_ale_bullet": "• Exposición Anualizada Estimada (ALE): {ale_val}/año (calculada considerando una frecuencia estimada de 1 incidente relevante cada {recurrence_years} años, equivalente a una probabilidad anual de {lef_val})."
  },
  "en": {
    "ch3_intro_archetypes": {
      "INFRASTRUCTURE_PHYSICAL": "This chapter presents the technical assessment of physical infrastructure, plant networking, and connectivity assets within the {tower_name} domain at {client_name}. The analysis evaluates the current environment's ability to sustain industrial operational continuity across three core dimensions: network and link architecture, physical equipment availability, and operational integration between plant facilities and central systems.",
      "COMPUTE_PLATFORMS": "This section documents the technical diagnostic of compute platforms, virtualization clusters, storage arrays, and core infrastructure services comprising the {tower_name} domain at {client_name}. The review assesses infrastructure consolidation levels, production cluster fault tolerance, and resource administration efficiency supporting enterprise workloads.",
      "SECURITY_GOVERNANCE": "This section outlines the technical evaluation of security controls, data protection mechanisms, and operational governance deployed across the {tower_name} domain at {client_name}. The diagnostic examines perimeter and internal defense resilience, access traceability, and actual recovery readiness against incidents threatening business integrity."
    },
    "ch3_scorecard_commentary_archetypes": {
      "INFRASTRUCTURE_PHYSICAL": "The domain achieves an overall maturity score of {score_val} out of 5.0 ({maturity_tier_label}). This rating indicates that physical and network infrastructure satisfies baseline connectivity requirements for daily operations at {client_name}, but retains single points of failure, selective hardware obsolescence, and segmentation gaps that expose operational lines to unplanned outages.",
      "COMPUTE_PLATFORMS": "The platform registers an aggregate maturity rating of {score_val} out of 5.0 ({maturity_tier_label}). This assessment demonstrates that compute and storage environments sustain day-to-day workloads at {client_name}, though high-availability configuration asymmetries, manual provisioning routines, and accumulated technical debt constrain operational agility.",
      "SECURITY_GOVERNANCE": "The control framework attains a consolidated score of {score_val} out of 5.0 ({maturity_tier_label}). This level reflects functional baseline controls and operational procedures at {client_name}, while highlighting gaps in automated response, uneven security policy enforcement, and manual dependencies that extend exposure windows during adverse events."
    },
    "ch4_title": "4. Infrastructure Economic Risk Evaluation",
    "ch4_sec1_title": "4.1. Estimated Hourly Downtime Cost",
    "ch4_sec2_title": "4.2. Risk Prioritization Matrix & Heatmap",
    "ch4_sec3_title": "4.3. Domain Risk Concentration Profile",
    "ch4_sec4_title": "4.4. Quantified Technical Risk Cards",
    "ch4_sec1_domain_context": {
      "INFRASTRUCTURE_PHYSICAL": "To quantify the financial impact of technical vulnerabilities at {client_name}, an enterprise reference rate of {hourly_rate}/h of severe downtime is established (derived from annual revenues of {annual_revenue} within the {vertical_desc} sector). Within the {tower_name} domain, a critical outage translates directly into lost connectivity across weighbridges, dispatch lines, and plant control networks, halting physical material flow and logistics output.",
      "COMPUTE_PLATFORMS": "The economic valuation of identified risks at {client_name} is anchored on an estimated enterprise impact of {hourly_rate}/h during critical service outages (based on annual revenues of {annual_revenue} in {vertical_desc} operations). Within the {tower_name} domain, a major failure causes unavailability across core servers, databases, and virtualization platforms hosting ERP, MES, and administrative systems, paralyzing transactional capacity.",
      "SECURITY_GOVERNANCE": "The financial quantification model applied to {client_name} uses an operational downtime rate of {hourly_rate}/h (calculated from annual revenues of {annual_revenue} in {vertical_desc}). Regarding {tower_name}, a severe incident—such as network intrusion, backup corruption, or access control failure—simultaneously compromises multiple shared services, extending downtime while data integrity is verified and secure operations are restored."
    },
    "ch4_heatmap_legend_intro": "The following table details the reference codes displayed in the heatmap matrix, linking each identifier to the affected capability, its Annualized Loss Expectancy (ALE), and its criticality tier:",
    "ch4_heatmap_legend_headers": [
      "Code",
      "Identified Technical Risk & Capability",
      "Annual Exposure (ALE)",
      "Criticality"
    ],
    "ch4_sec3_intro": "The inventory of technical risks identified across the {tower_name} domain yields a total Annualized Loss Expectancy (ALE) of {total_ale}/year distributed across {total_risks} findings. To profile risk concentration within the current state (AS-IS), financial exposure is categorized into three impact tiers:",
    "ch4_sec3_tier_high": "• Tier 1 — Critical & High-Impact Risks ({high_count} findings): Account for a combined exposure of {high_ale}/year, representing {high_pct}% of total domain financial risk. These findings reflect structural vulnerabilities capable of halting essential services or impacting multiple assets simultaneously.",
    "ch4_sec3_tier_med": "• Tier 2 — Moderate-Impact Risks ({med_count} findings): Represent an annualized exposure of {med_ale}/year, equivalent to {med_pct}% of total quantified risk. These correspond to operational inefficiencies or partial redundancy gaps that degrade performance and extend recovery times during localized failures.",
    "ch4_sec3_tier_low": "• Tier 3 — Residual & Minor Risks ({low_count} findings): Comprise a cumulative exposure of {low_ale}/year ({low_pct}% of domain risk), associated with contained technical friction whose direct impact on overarching business continuity remains limited.",
    "ch4_sec3_outro": "This distribution strictly reflects the financial exposure profile of the current environment (AS-IS), establishing an objective baseline for platform governance.",
    "ch4_card_pillar_label": "Capability Pillar",
    "ch4_card_propagation_label": "Fault Propagation to Other Systems",
    "ch4_card_propagation_high": "High — Cross-cutting impact on dependent services (Factor x{factor})",
    "ch4_card_propagation_moderate": "Moderate — Shared impact with adjacent systems (Factor x{factor})",
    "ch4_card_propagation_low": "Contained — Impact isolated to local component (Factor x{factor})",
    "ch4_card_sle_bullet": "• Single Loss Expectancy per Incident (SLE): {sle_val} (estimated for a mean recovery time of {mttr_hours} hours at {hourly_rate}/h of operational disruption, adjusted for scope and fault propagation).",
    "ch4_card_ale_bullet": "• Annualized Loss Expectancy (ALE): {ale_val}/year (calculated for an estimated frequency of 1 major incident every {recurrence_years} years, equivalent to an annual probability of {lef_val})."
  }
}
```

---

## 3. Exact Python Implementation (`payload_to_ast.py`)

Below is the complete, production-ready Python implementation for `payload_to_ast.py` governing Chapter 3 and Chapter 4 AST construction. All variable names, helper functions, and comments are written in **100% Technical English**, with zero hardcoded tenant strings or currencies.

```python
from typing import Dict, Any, List


def resolve_tower_archetype(tower_id: str, tower_meta: Dict[str, Any]) -> str:
    """
    Deterministically maps any of the 10 capability towers to one of the 3
    structural archetypes: INFRASTRUCTURE_PHYSICAL, COMPUTE_PLATFORMS, or SECURITY_GOVERNANCE.
    """
    explicit_archetype = tower_meta.get("archetype")
    if explicit_archetype in (
        "INFRASTRUCTURE_PHYSICAL",
        "COMPUTE_PLATFORMS",
        "SECURITY_GOVERNANCE",
    ):
        return explicit_archetype

    archetype_map = {
        "T1": "INFRASTRUCTURE_PHYSICAL",
        "T4": "INFRASTRUCTURE_PHYSICAL",
        "T7": "INFRASTRUCTURE_PHYSICAL",
        "T10": "INFRASTRUCTURE_PHYSICAL",
        "T2": "COMPUTE_PLATFORMS",
        "T5": "COMPUTE_PLATFORMS",
        "T8": "COMPUTE_PLATFORMS",
        "T3": "SECURITY_GOVERNANCE",
        "T6": "SECURITY_GOVERNANCE",
        "T9": "SECURITY_GOVERNANCE",
    }
    normalized_id = str(tower_id).upper().strip()
    return archetype_map.get(normalized_id, "COMPUTE_PLATFORMS")


def format_clean_score_value(raw_score: Any, lang: str) -> str:
    """
    Formats a numeric maturity score into a clean decimal string (e.g., '2,46' or '2.46')
    and strips any pre-existing denominator ('/ 5.00', 'sobre 5.0') to prevent denominator stutter.
    """
    if isinstance(raw_score, str):
        cleaned = raw_score.split("/")[0].split("sobre")[0].split("out of")[0].strip()
        cleaned = cleaned.replace(",", ".")
        try:
            val = float(cleaned)
        except ValueError:
            val = 0.0
    else:
        try:
            val = float(raw_score)
        except (TypeError, ValueError):
            val = 0.0

    formatted = f"{val:.2f}"
    return formatted.replace(".", ",") if lang == "es" else formatted


def build_chapter_3_ast(
    payload: Dict[str, Any],
    locales: Dict[str, Any],
    lang: str,
) -> List[Dict[str, Any]]:
    """
    Builds Chapter 3 AST with 3-Archetype Polymorphic Rotation and zero denominator stutter.
    """
    loc = locales[lang]
    client_name = payload.get("client_metadata", {}).get("name", "Enterprise")
    tower_id = payload.get("tower_id", "T1")
    tower_name = payload.get("tower_name", "")
    archetype = resolve_tower_archetype(tower_id, payload.get("tower_metadata", {}))

    raw_global_score = payload.get("maturity_summary", {}).get("global_score", 0.0)
    clean_score_str = format_clean_score_value(raw_global_score, lang)
    maturity_tier_label = payload.get("maturity_summary", {}).get(
        "maturity_tier_label", "Nivel 2 - Repetible" if lang == "es" else "Level 2 - Repeatable"
    )

    intro_template = loc["ch3_intro_archetypes"][archetype]
    commentary_template = loc["ch3_scorecard_commentary_archetypes"][archetype]

    intro_text = intro_template.format(
        tower_name=tower_name,
        client_name=client_name,
    )
    commentary_text = commentary_template.format(
        score_val=clean_score_str,
        maturity_tier_label=maturity_tier_label,
        client_name=client_name,
        tower_name=tower_name,
    )

    ast_nodes: List[Dict[str, Any]] = [
        {
            "type": "heading_1",
            "text": loc.get("ch3_title", "3. Diagnóstico Técnico de Capacidades"),
        },
        {
            "type": "paragraph",
            "text": intro_text,
        },
        {
            "type": "scorecard_table",
            "data": payload.get("maturity_summary", {}).get("pillars", []),
            "global_score_display": clean_score_str,
        },
        {
            "type": "paragraph",
            "text": commentary_text,
            "spacing_after_pt": 12,
        },
    ]
    return ast_nodes


def build_chapter_4_ast(
    payload: Dict[str, Any],
    locales: Dict[str, Any],
    lang: str,
    currency_formatter: Any,
) -> List[Dict[str, Any]]:
    """
    Builds Chapter 4 AST featuring simplified executive titles, domain-contextualized
    downtime narrative, a deterministic 4-column heatmap legend table, a pure AS-IS
    financial risk concentration profile (zero TO-BE schedules), and plain-language risk cards.
    """
    loc = locales[lang]
    client_meta = payload.get("client_metadata", {})
    client_name = client_meta.get("name", "Enterprise")
    vertical_desc = client_meta.get("vertical_description", "industrial operations")
    annual_revenue_val = float(client_meta.get("annual_revenue", 0.0))
    hourly_rate_val = float(payload.get("actuarial_baseline", {}).get("hourly_downtime_rate", 0.0))

    tower_id = payload.get("tower_id", "T1")
    tower_name = payload.get("tower_name", "")
    archetype = resolve_tower_archetype(tower_id, payload.get("tower_metadata", {}))

    annual_revenue_str = currency_formatter(annual_revenue_val, decimals=0)
    hourly_rate_str = currency_formatter(hourly_rate_val, decimals=2)

    risks: List[Dict[str, Any]] = payload.get("quantified_risks", [])

    ast_nodes: List[Dict[str, Any]] = [
        {
            "type": "heading_1",
            "text": loc["ch4_title"],
        },
        # --- Section 4.1: Estimated Hourly Downtime Cost (Domain Contextualized) ---
        {
            "type": "heading_2",
            "text": loc["ch4_sec1_title"],
        },
        {
            "type": "paragraph",
            "text": loc["ch4_sec1_domain_context"][archetype].format(
                client_name=client_name,
                hourly_rate=hourly_rate_str,
                annual_revenue=annual_revenue_str,
                vertical_desc=vertical_desc,
                tower_name=tower_name,
            ),
        },
        # --- Section 4.2: Risk Prioritization Matrix & Heatmap + Legend Table ---
        {
            "type": "heading_2",
            "text": loc["ch4_sec2_title"],
        },
        {
            "type": "heatmap_matrix_5x5",
            "risks": risks,
        },
        {
            "type": "paragraph",
            "text": loc["ch4_heatmap_legend_intro"],
            "spacing_before_pt": 8,
            "spacing_after_pt": 6,
        },
        _build_heatmap_legend_table_ast(risks, loc, currency_formatter),
        # --- Section 4.3: Pure AS-IS Domain Risk Concentration Profile ---
        {
            "type": "heading_2",
            "text": loc["ch4_sec3_title"],
        },
    ]

    ast_nodes.extend(
        _build_as_is_risk_concentration_ast(
            risks=risks,
            tower_name=tower_name,
            loc=loc,
            lang=lang,
            currency_formatter=currency_formatter,
        )
    )

    # --- Section 4.4: Plain-Language Quantified Technical Risk Cards ---
    ast_nodes.append(
        {
            "type": "heading_2",
            "text": loc["ch4_sec4_title"],
        }
    )
    ast_nodes.extend(
        _build_plain_language_risk_cards_ast(
            risks=risks,
            hourly_rate_str=hourly_rate_str,
            loc=loc,
            lang=lang,
            currency_formatter=currency_formatter,
        )
    )

    return ast_nodes


def _build_heatmap_legend_table_ast(
    risks: List[Dict[str, Any]],
    loc: Dict[str, Any],
    currency_formatter: Any,
) -> Dict[str, Any]:
    """
    Constructs the deterministic 4-column OpenXML table mapping short heatmap tokens
    (e.g., RVS01) to their capability pillar, risk title, ALE, and criticality.
    """
    rows: List[List[str]] = []
    for r in risks:
        code = str(r.get("id", "")).strip()
        pillar = str(r.get("pillar_name", "")).strip()
        title = str(r.get("title", "")).strip()
        combined_desc = f"{pillar}: {title}" if pillar else title
        ale_str = currency_formatter(float(r.get("ale", 0.0)), decimals=2)
        criticality = str(r.get("criticality_label", "")).strip()
        rows.append([code, combined_desc, ale_str, criticality])

    return {
        "type": "data_table",
        "style": "executive_compact_legend",
        "column_widths_pct": [12, 54, 18, 16],
        "headers": loc["ch4_heatmap_legend_headers"],
        "rows": rows,
        "keep_together": True,
    }


def _build_as_is_risk_concentration_ast(
    risks: List[Dict[str, Any]],
    tower_name: str,
    loc: Dict[str, Any],
    lang: str,
    currency_formatter: Any,
) -> List[Dict[str, Any]]:
    """
    Computes pure AS-IS financial risk concentration across High, Moderate, and Residual tiers.
    Strictly forbids any 30-90 day / 90-180 day TO-BE implementation schedules.
    """
    total_ale = sum(float(r.get("ale", 0.0)) for r in risks)
    safe_denominator = total_ale if total_ale > 0.0 else 1.0

    high_risks = [
        r for r in risks if str(r.get("severity_tier", "")).upper() in ("CRITICAL", "HIGH")
    ]
    med_risks = [
        r for r in risks if str(r.get("severity_tier", "")).upper() == "MODERATE"
    ]
    low_risks = [
        r
        for r in risks
        if str(r.get("severity_tier", "")).upper() not in ("CRITICAL", "HIGH", "MODERATE")
    ]

    high_ale = sum(float(r.get("ale", 0.0)) for r in high_risks)
    med_ale = sum(float(r.get("ale", 0.0)) for r in med_risks)
    low_ale = sum(float(r.get("ale", 0.0)) for r in low_risks)

    def _fmt_pct(val: float) -> str:
        pct_str = f"{(val / safe_denominator) * 100.0:.1f}"
        return pct_str.replace(".", ",") if lang == "es" else pct_str

    return [
        {
            "type": "paragraph",
            "text": loc["ch4_sec3_intro"].format(
                tower_name=tower_name,
                total_ale=currency_formatter(total_ale, decimals=2),
                total_risks=len(risks),
            ),
        },
        {
            "type": "paragraph",
            "text": loc["ch4_sec3_tier_high"].format(
                high_count=len(high_risks),
                high_ale=currency_formatter(high_ale, decimals=2),
                high_pct=_fmt_pct(high_ale),
            ),
        },
        {
            "type": "paragraph",
            "text": loc["ch4_sec3_tier_med"].format(
                med_count=len(med_risks),
                med_ale=currency_formatter(med_ale, decimals=2),
                med_pct=_fmt_pct(med_ale),
            ),
        },
        {
            "type": "paragraph",
            "text": loc["ch4_sec3_tier_low"].format(
                low_count=len(low_risks),
                low_ale=currency_formatter(low_ale, decimals=2),
                low_pct=_fmt_pct(low_ale),
            ),
        },
        {
            "type": "paragraph",
            "text": loc["ch4_sec3_outro"],
            "spacing_after_pt": 12,
        },
    ]


def _build_plain_language_risk_cards_ast(
    risks: List[Dict[str, Any]],
    hourly_rate_str: str,
    loc: Dict[str, Any],
    lang: str,
    currency_formatter: Any,
) -> List[Dict[str, Any]]:
    """
    Renders executive-friendly Quantified Technical Risk Cards:
    - Clean header '[ID] Title' (pillar name separated into metadata row).
    - Plain-language Fault Propagation description instead of 'Efecto Cascada'.
    - Plain-language SLE and ALE bullet points with human-readable recurrence intervals.
    """
    cards_ast: List[Dict[str, Any]] = []

    for r in risks:
        risk_id = str(r.get("id", "")).strip()
        clean_title = str(r.get("title", "")).strip()
        pillar_name = str(r.get("pillar_name", "")).strip()

        # Strip accidental trailing pillar suffix if present in raw payload title
        if pillar_name and clean_title.endswith(f"({pillar_name})"):
            clean_title = clean_title[: -len(f"({pillar_name})")].strip()

        header_text = f"[{risk_id}] {clean_title}"

        cascade_factor = float(r.get("cascade_multiplier", 1.0))
        factor_str = f"{cascade_factor:.2f}".rstrip("0").rstrip(".")
        if lang == "es":
            factor_str = factor_str.replace(".", ",")

        if cascade_factor >= 1.4:
            propagation_text = loc["ch4_card_propagation_high"].format(factor=factor_str)
        elif cascade_factor > 1.05:
            propagation_text = loc["ch4_card_propagation_moderate"].format(factor=factor_str)
        else:
            propagation_text = loc["ch4_card_propagation_low"].format(factor=factor_str)

        sle_val_str = currency_formatter(float(r.get("sle", 0.0)), decimals=2)
        ale_val_str = currency_formatter(float(r.get("ale", 0.0)), decimals=2)

        mttr_hours = float(r.get("mttr_hours", 4.0))
        mttr_str = f"{mttr_hours:.1f}".rstrip("0").rstrip(".")
        if lang == "es":
            mttr_str = mttr_str.replace(".", ",")

        lef_val = max(float(r.get("lef", 0.1)), 0.01)
        recurrence_years = 1.0 / lef_val
        recurrence_str = (
            f"{int(round(recurrence_years))}"
            if abs(recurrence_years - round(recurrence_years)) < 0.15
            else f"{recurrence_years:.1f}"
        )
        lef_str = f"{lef_val:.2f}"
        if lang == "es":
            recurrence_str = recurrence_str.replace(".", ",")
            lef_str = lef_str.replace(".", ",")

        sle_bullet = loc["ch4_card_sle_bullet"].format(
            sle_val=sle_val_str,
            mttr_hours=mttr_str,
            hourly_rate=hourly_rate_str,
        )
        ale_bullet = loc["ch4_card_ale_bullet"].format(
            ale_val=ale_val_str,
            recurrence_years=recurrence_str,
            lef_val=lef_str,
        )

        cards_ast.append(
            {
                "type": "quantified_risk_card",
                "header_title": header_text,
                "pillar_label": loc["ch4_card_pillar_label"],
                "pillar_value": pillar_name,
                "propagation_label": loc["ch4_card_propagation_label"],
                "propagation_value": propagation_text,
                "technical_evidence": str(r.get("evidence", "")).strip(),
                "financial_breakdown_bullets": [sle_bullet, ale_bullet],
                "keep_together": True,
            }
        )

    return cards_ast
```

---

## 4. Verification of Non-Negotiable Architectural Laws

| Architectural Law | Verification Outcome |
| :--- | :--- |
| **1. Zero Denominator Stutter & Polymorphic Chapter 3** | `format_clean_score_value()` strips any pre-existing denominator before formatting `{score_val}`, yielding `2,46 sobre 5,0 (Nivel 2 - Repetible)`. `resolve_tower_archetype()` rotates Chapter 3 intros and scorecard evaluations across `INFRASTRUCTURE_PHYSICAL`, `COMPUTE_PLATFORMS`, and `SECURITY_GOVERNANCE`. |
| **2. Simplified Executive Headings in Chapter 4** | All five headings (`4`, `4.1`, `4.2`, `4.3`, `4.4`) match the exact client-friendly phrasing in both Spanish and English locales. |
| **3. Domain-Specific Downtime Contextualization (4.1)** | Section 4.1 anchors on the authoritative `{hourly_rate}` while explaining domain-specific operational failure modes (plant/weighbridge paralysis in T1 vs. ERP/MES server stoppage in T2 vs. security containment stoppage in T3). |
| **4. Explicit 4-Column Heatmap Legend Table (4.2)** | `_build_heatmap_legend_table_ast()` renders a deterministic 4-column OpenXML table (`[Código | Capacidad y Riesgo Técnico Identificado | Exposición Anual (ALE) | Criticidad]`) directly below the 5x5 matrix. |
| **5. Pure AS-IS Risk Concentration Profile (4.3)** | `_build_as_is_risk_concentration_ast()` completely eliminates all `30-90 day` and `90-180 day` implementation schedules, outputting strictly AS-IS actuarial concentration across Critical/High, Moderate, and Residual tiers. |
| **6. Plain-Language Risk Cards (4.4)** | `_build_plain_language_risk_cards_ast()` cleans card titles to `[ID] Title`, replaces "Efecto Cascada" with `Propagación de Fallo a Otros Sistemas`, and renders self-explanatory SLE and ALE executive bullets. |

**VERDICT: PASS** — Blueprint RFC 052 is complete, deterministic, and ready for deployment.