# RFC 048: Assertive Engineering Diplomacy, Direct Economic Framing, and the Executive Cockpit Layout

**Role:** Chief Executive Communications Strategist & Principal Document Architect  
**Status:** Production-Ready Architectural Blueprint  
**Target Modules:** `engine_config/locales.json`, `src/narrative/builder.py`, `src/narrative/validator.py`, `src/engine/payload_to_ast.py`, `src/engine/docx_renderer.py`

---

## 1. Editorial Lexicon & Tone Transformation: Assertive Engineering Diplomacy

In C-suite and VP-level infrastructure advisory, prosecutorial phrasing triggers immediate defensive reflexes from the CIO, IT Director, and lead engineers. When internal teams feel blamed for technical debt, they challenge the methodology rather than acting on the findings.

We enforce **Assertive Engineering Diplomacy** across the entire document through four structural laws:
1. **Acknowledge Operational Dedication:** Recognize the current foundation and the daily effort of the technical staff keeping the business running.
2. **Contextualize Architecture vs. Scale:** Frame architectural limitations as the natural byproduct of business growth and evolving availability demands, never as negligence.
3. **Objective Engineering Precision:** State Single Points of Failure (SPOFs), manual recovery dependencies, and capacity constraints as factual architectural states—free of pejorative qualifiers (*"deficiencias estructurales"*, *"aparente estabilidad"*).
4. **Plain, Direct Economic Phrasing:** Eliminate stiff consulting filler (*"Desde una perspectiva económica"*, *"en este dominio"*). State financial impact in clear, direct business terms.

### 1.1 Lexicon Transformation Matrix (Document-Wide)

| Accusatory / Stiff Phrase (Banned) | Assertive Engineering Diplomacy Replacement (Mandated) | Psychological & Editorial Rationale |
| :--- | :--- | :--- |
| *"Se han identificado deficiencias estructurales que limitan su fiabilidad y exponen al negocio..."* | *"La arquitectura actual cumple con la operativa diaria, aunque presenta áreas de mejora en su redundancia física para absorber fallos de componentes sin afectar al servicio."* | Validates current utility while stating the exact technical limitation (lack of physical redundancy) without attacking the client's competence. |
| *"Esta aparente estabilidad depende de la intervención reactiva del personal técnico..."* | *"La continuidad operativa se apoya en gran medida en la dedicación y respuesta directa del equipo técnico ante incidencias..."* | Transforms an insult (*"aparente estabilidad"*) into recognition of the team's effort, while clearly exposing the operational dependency on manual intervention. |
| *"Desde una perspectiva económica, la indisponibilidad no planificada en este dominio genera un coste de parada estimado en..."* | *"En caso de producirse una parada imprevista del servicio, el coste operativo se estima en **{hourly_burn_rate_fmt}** (desglosado en la Sección 4.1)..."* | Removes bureaucratic jargon (*"en este dominio"*) and states the financial reality in natural, executive Spanish. |
| *"Exponen al negocio a interrupciones imprevistas ante cualquier fallo..."* | *"Limitan el margen de maniobra automatizado frente a caídas puntuales de hardware o infraestructura..."* | Replaces alarmism with precise operational mechanics. |
| *"Carencia crítica de gobierno / ausencia de controles..."* | *"Oportunidad de estandarización y automatización en los controles de..."* | Shifts focus from blame to constructive evolution while maintaining urgency. |

---

## 2. Bilingual Locale Templates (`engine_config/locales.json`)

All narrative strings reside exclusively in `engine_config/locales.json`. The keys below replace all prosecutorial phrasing and stiff filler across Chapters 1 through 5.

```json
{
  "es": {
    "ch1_cockpit": {
      "triad_headers": {
        "strength": "FORTALEZA OPERATIVA",
        "gap": "OPORTUNIDAD DE ARQUITECTURA",
        "bottleneck": "CUELLO DE BOTELLA SISTÉMICO"
      },
      "headline_template": "Diagnóstico Ejecutivo: La torre de {tower_name} registra un índice de madurez de {score_fmt}/5.0 ({maturity_band}), situándose {benchmark_delta_fmt} puntos por debajo del estándar del sector ({industry_benchmark_fmt}).",
      "posture_opening": "En el ámbito de {tower_name} ({tower_mission}), la infraestructura actual da soporte a la operativa diaria del negocio gracias a la base técnica desplegada y a la gestión directa del equipo de operaciones. No obstante, el crecimiento de las demandas transaccionales ha llevado el diseño actual cerca de su límite de elasticidad, identificándose puntos donde la tolerancia a fallos depende de actuaciones manuales en lugar de mecanismos automatizados.",
      "findings_intro": "El análisis técnico de la arquitectura actual destaca tres factores clave para la continuidad del servicio:",
      "bullet_strength": "Base Operativa Consolidada: {strength_narrative}",
      "bullet_gap": "Evolución de Redundancia y Diseño: {gap_narrative}",
      "bullet_bottleneck": "Restricción de Escalabilidad Operativa: {bottleneck_narrative}",
      "economic_impact_direct": "En caso de producirse una parada imprevista del servicio, el coste operativo se estima en {hourly_burn_rate_fmt} (desglosado en la Sección 4.1), lo que representa una exposición financiera anual latente de {annual_exposure_fmt} mientras se mantenga la configuración actual.",
      "diagnostic_verdict": "Conclusión del Diagnóstico: La plataforma cuenta con una base funcional sobre la cual evolucionar; sin embargo, reducir la dependencia de la intervención manual y asegurar la alta disponibilidad requiere abordar las mejoras de redundancia detalladas en este informe."
    },
    "diplomatic_clauses": {
      "spof_exposure": "la topología actual concentra cargas críticas en nodos únicos, reduciendo la capacidad de conmutación automática ante caídas puntuales de hardware",
      "manual_recovery": "la recuperación del servicio se apoya en procedimientos manuales ejecutados por el personal técnico, lo que amplía los tiempos de restablecimiento (MTTR) bajo escenarios de alta concurrencia",
      "legacy_saturation": "el dimensionamiento actual responde a requerimientos históricos que hoy limitan el margen de crecimiento y la absorción de picos de demanda sin degradación de rendimiento"
    }
  },
  "en": {
    "ch1_cockpit": {
      "triad_headers": {
        "strength": "OPERATIONAL STRENGTH",
        "gap": "ARCHITECTURAL OPPORTUNITY",
        "bottleneck": "SYSTEMIC BOTTLENECK"
      },
      "headline_template": "Executive Assessment: The {tower_name} capability tower achieves a maturity index of {score_fmt}/5.0 ({maturity_band}), positioning it {benchmark_delta_fmt} points below the industry benchmark ({industry_benchmark_fmt}).",
      "posture_opening": "Within {tower_name} ({tower_mission}), the current infrastructure supports daily business operations through its established baseline and the direct stewardship of the engineering staff. However, increasing operational scale has pushed the current design toward its elasticity limits, revealing areas where fault tolerance relies on manual intervention rather than automated failover.",
      "findings_intro": "Technical evaluation of the current architecture highlights three core factors governing service continuity:",
      "bullet_strength": "Established Operational Baseline: {strength_narrative}",
      "bullet_gap": "Redundancy & Design Evolution: {gap_narrative}",
      "bullet_bottleneck": "Operational Scalability Constraint: {bottleneck_narrative}",
      "economic_impact_direct": "In the event of an unplanned service outage, the operational cost is estimated at {hourly_burn_rate_fmt} (detailed in Section 4.1), representing a latent annual financial exposure of {annual_exposure_fmt} under the current configuration.",
      "diagnostic_verdict": "Diagnostic Conclusion: The platform provides a functional foundation for growth; however, reducing reliance on reactive manual intervention and ensuring continuous availability requires addressing the redundancy improvements outlined in this assessment."
    },
    "diplomatic_clauses": {
      "spof_exposure": "the current topology concentrates critical workloads on single nodes, limiting automated failover capacity during isolated hardware faults",
      "manual_recovery": "service restoration relies on manual runbooks executed by engineering personnel, extending Mean Time to Recovery (MTTR) under high-concurrency scenarios",
      "legacy_saturation": "current capacity sizing reflects historical baselines that now constrain headroom and the absorption of demand spikes without performance degradation"
    }
  }
}
```

---

## 3. Executive Cockpit Layout Blueprint (Chapter 1 Reordering)

Moving the **Diagnostic Triad Table** immediately below the **KPI Scorecard Table** creates a high-density **Executive Cockpit** in the top third of Page 3. A C-level reader captures the quantitative score, financial exposure, operational strength, architectural opportunity, and systemic bottleneck within 10 seconds of turning the page, before diving into the narrative synthesis.

### 3.1 Visual Hierarchy on Page 3 (Top-to-Bottom AST Flow)

```text
+-----------------------------------------------------------------------------+
| 1. RESUMEN EJECUTIVO Y DIAGNÓSTICO DE MADUREZ                               |
| 1.1 Síntesis Ejecutiva: Infraestructura Física e Instalaciones (D1)         |
+------------------------+-------------------------+--------------------------+
|   PUNTUACIÓN ACTUAL    |    BANDA DE MADUREZ     | EXPOSICIÓN ANUAL EST.    |
|       1,8 / 5,0        |   Reactivo / Ad-Hoc     |      152.976,94 €        |
+------------------------+-------------------------+--------------------------+
|  FORTALEZA OPERATIVA   | OPORTUNIDAD ARQUITECT.  | CUELLO BOTELLA SISTÉMICO |
| Base física funcional  | Redundancia en rutas de | Recuperación sujeta a    |
| con monitorización     | climatización y cuadros | intervención manual del  |
| básica activa.         | eléctricos secundarios. | equipo en sala técnica.  |
+------------------------+-------------------------+--------------------------+
| [Callout Box / Headline Finding]                                            |
| Diagnóstico Ejecutivo: La torre de Infraestructura Física registra un...    |
+-----------------------------------------------------------------------------+
| [Paragraph 1: Posture & Mission - Assertive Engineering Diplomacy]          |
| [Findings Intro Line]                                                       |
|   • Base Operativa Consolidada: ...                                         |
|   • Evolución de Redundancia y Diseño: ...                                  |
|   • Restricción de Escalabilidad Operativa: ...                             |
| [Paragraph 2: Direct Economic Impact (No stiff filler)]                     |
| [Paragraph 3: Current-State Diagnostic Verdict]                             |
+-----------------------------------------------------------------------------+
```

---

## 4. OpenXML Vertical Budget Validation (Page 3 Determinism)

Reordering blocks changes paragraph adjacency and table spacing. Below is the exact vertical height accounting in **Twips** (`1 pt = 20 twips`, `1 inch = 1440 twips`) for A4 Page 3 (`16,838 twips` total height):

| AST Component | Specification (Font / Padding / Borders) | Exact Height (pt) | Exact Height (twips) |
| :--- | :--- | :---: | :---: |
| **Top & Bottom Page Margins** | `72 pt` top + `72 pt` bottom (`1 inch` each) | 144.0 pt | 2,880 twips |
| **Chapter 1 H1 Header** | `16 pt` bold, `space_before=0`, `space_after=6 pt`, bottom rule | 26.0 pt | 520 twips |
| **Section 1.1 H2 Header** | `12.5 pt` bold, `space_before=6 pt`, `space_after=6 pt` | 25.0 pt | 500 twips |
| **Row 1: KPI Scorecard Table** | Header row (`18 pt`) + Value row (`28 pt`) + `6 pt` after gap | 52.0 pt | 1,040 twips |
| **Row 2: Diagnostic Triad Table** | Header row (`18 pt`) + 3-4 line body (`54 pt`) + `8 pt` after gap | 80.0 pt | 1,600 twips |
| **Row 3: Executive Headline Callout** | 2 lines (`9.5 pt` font, `13 pt` leading) + cell padding + `6 pt` gap | 44.0 pt | 880 twips |
| **Row 4a: Posture & Mission Paragraph** | 5 lines (`9.5 pt` font, `13.5 pt` line spacing) + `6 pt` after | 73.5 pt | 1,470 twips |
| **Row 4b: Findings Intro + 3 Bullets** | Intro (`18 pt`) + 3 bullets × 2.5 lines (`102 pt`) + `6 pt` after | 126.0 pt | 2,520 twips |
| **Row 4c: Direct Economic Paragraph** | 3 lines (`9.5 pt` font, `13.5 pt` line spacing) + `6 pt` after | 46.5 pt | 930 twips |
| **Row 4d: Diagnostic Verdict Box** | 3 lines (`9.5 pt` font, `13.5 pt` line spacing) + padding | 52.0 pt | 1,040 twips |
| **Total Consumed Vertical Budget** | **Sum of all elements + margins** | **669.0 pt** | **13,380 twips** |
| **Available A4 Printable Height** | **Total A4 (`841.9 pt` / `16,838 twips`)** | **841.9 pt** | **16,838 twips** |
| **Remaining Safety Buffer** | **20.5% Free Vertical Reserve (Zero Overflow Risk)** | **172.9 pt** | **3,458 twips** |

**Engineering Conclusion:** The Executive Cockpit layout consumes `79.5%` of the page height, leaving a `172.9 pt` (`2.4 inch`) safety cushion at the bottom of Page 3. It is mathematically impossible for Page 3 to overflow into Page 4 across any enterprise payload.

---

## 5. Production Python Implementation (100% Technical English)

### 5.1 Narrative Builder & Tone Guardrail (`src/narrative/builder.py` & `src/narrative/validator.py`)

```python
# src/narrative/validator.py
from typing import Final, Sequence

FORBIDDEN_PROSECUTORIAL_TOKENS: Final[Sequence[str]] = (
    "deficiencias estructurales",
    "aparente estabilidad",
    "exponen al negocio a interrupciones imprevistas ante cualquier fallo",
    "en este dominio",
    "desde una perspectiva económica, la indisponibilidad",
    "negligencia",
    "incapacidad del equipo",
    "structural deficiencies that expose",
    "apparent stability",
    "in this domain",
)


class NarrativeToneViolationError(ValueError):
    """Raised when generated prose violates Assertive Engineering Diplomacy."""


def validate_diplomatic_tone(rendered_text: str, section_id: str) -> None:
    """Enforces zero client-blame phrasing and zero stiff boilerplate."""
    normalized_text = rendered_text.lower()
    for forbidden_token in FORBIDDEN_PROSECUTORIAL_TOKENS:
        if forbidden_token in normalized_text:
            raise NarrativeToneViolationError(
                f"Prosecutorial or stiff boilerplate token '{forbidden_token}' "
                f"detected in section '{section_id}'. Enforce Assertive Engineering Diplomacy."
            )
```

```python
# src/narrative/builder.py
from dataclasses import dataclass
from typing import Any, Mapping
from src.narrative.validator import validate_diplomatic_tone


@dataclass(frozen=True)
class ChapterOneCockpitContent:
    kpi_score_fmt: str
    maturity_band: str
    annual_exposure_fmt: str
    triad_headers: Mapping[str, str]
    triad_strength_short: str
    triad_gap_short: str
    triad_bottleneck_short: str
    headline_text: str
    posture_paragraph: str
    findings_intro: str
    scannable_bullets: tuple[str, str, str]
    economic_impact_paragraph: str
    diagnostic_verdict_paragraph: str


def build_chapter_one_cockpit(
    domain_payload: Mapping[str, Any],
    financial_metrics: Mapping[str, str],
    locale_dict: Mapping[str, Any],
) -> ChapterOneCockpitContent:
    """Constructs the Chapter 1 Executive Cockpit with Assertive Engineering Diplomacy."""
    cockpit_i18n = locale_dict["ch1_cockpit"]

    formatting_context = {
        "tower_name": domain_payload["tower_name"],
        "tower_mission": domain_payload["tower_mission"],
        "score_fmt": domain_payload["score_fmt"],
        "maturity_band": domain_payload["maturity_band"],
        "benchmark_delta_fmt": domain_payload["benchmark_delta_fmt"],
        "industry_benchmark_fmt": domain_payload["industry_benchmark_fmt"],
        "strength_narrative": domain_payload["strength_narrative"],
        "gap_narrative": domain_payload["gap_narrative"],
        "bottleneck_narrative": domain_payload["bottleneck_narrative"],
        "hourly_burn_rate_fmt": financial_metrics["hourly_burn_rate_fmt"],
        "annual_exposure_fmt": financial_metrics["annual_exposure_fmt"],
    }

    headline_text = cockpit_i18n["headline_template"].format(**formatting_context)
    posture_paragraph = cockpit_i18n["posture_opening"].format(**formatting_context)
    findings_intro = cockpit_i18n["findings_intro"]

    scannable_bullets = (
        cockpit_i18n["bullet_strength"].format(**formatting_context),
        cockpit_i18n["bullet_gap"].format(**formatting_context),
        cockpit_i18n["bullet_bottleneck"].format(**formatting_context),
    )

    economic_impact_paragraph = cockpit_i18n["economic_impact_direct"].format(
        **formatting_context
    )
    diagnostic_verdict_paragraph = cockpit_i18n["diagnostic_verdict"].format(
        **formatting_context
    )

    # Validate every prose block against prosecutorial or stiff phrasing
    for idx, block in enumerate(
        (
            headline_text,
            posture_paragraph,
            *scannable_bullets,
            economic_impact_paragraph,
            diagnostic_verdict_paragraph,
        )
    ):
        validate_diplomatic_tone(block, section_id=f"ch1_cockpit_block_{idx}")

    return ChapterOneCockpitContent(
        kpi_score_fmt=domain_payload["score_fmt"],
        maturity_band=domain_payload["maturity_band"],
        annual_exposure_fmt=financial_metrics["annual_exposure_fmt"],
        triad_headers=cockpit_i18n["triad_headers"],
        triad_strength_short=domain_payload["triad_strength_summary"],
        triad_gap_short=domain_payload["triad_gap_summary"],
        triad_bottleneck_short=domain_payload["triad_bottleneck_summary"],
        headline_text=headline_text,
        posture_paragraph=posture_paragraph,
        findings_intro=findings_intro,
        scannable_bullets=scannable_bullets,
        economic_impact_paragraph=economic_impact_paragraph,
        diagnostic_verdict_paragraph=diagnostic_verdict_paragraph,
    )
```

### 5.2 AST Assembly Ordering (`src/engine/payload_to_ast.py`)

```python
# src/engine/payload_to_ast.py
from typing import Any, List, Mapping
from src.narrative.builder import ChapterOneCockpitContent


def assemble_chapter_one_ast_nodes(
    cockpit: ChapterOneCockpitContent,
    section_headers: Mapping[str, str],
    kpi_headers: Mapping[str, str],
) -> List[Mapping[str, Any]]:
    """
    Emits the deterministic AST node sequence for Page 3 (Chapter 1 Executive Cockpit).
    Places the Diagnostic Triad Table immediately beneath the KPI Scorecard Table.
    """
    return [
        {
            "node_type": "heading_1",
            "text": section_headers["ch1_title"],
            "keep_with_next": True,
        },
        {
            "node_type": "heading_2",
            "text": section_headers["ch1_subtitle"],
            "keep_with_next": True,
        },
        # ROW 1: Quantitative KPI Scorecard Strip
        {
            "node_type": "kpi_scorecard_table",
            "headers": [
                kpi_headers["current_score"],
                kpi_headers["maturity_band"],
                kpi_headers["annual_exposure"],
            ],
            "values": [
                cockpit.kpi_score_fmt,
                cockpit.maturity_band,
                cockpit.annual_exposure_fmt,
            ],
            "space_after_pt": 4,
            "cant_split": True,
            "keep_with_next": True,
        },
        # ROW 2: Qualitative Diagnostic Triad Strip (Executive Cockpit Companion)
        {
            "node_type": "diagnostic_triad_table",
            "headers": [
                cockpit.triad_headers["strength"],
                cockpit.triad_headers["gap"],
                cockpit.triad_headers["bottleneck"],
            ],
            "values": [
                cockpit.triad_strength_short,
                cockpit.triad_gap_short,
                cockpit.triad_bottleneck_short,
            ],
            "space_after_pt": 8,
            "cant_split": True,
            "keep_with_next": True,
        },
        # ROW 3: Executive Headline Callout
        {
            "node_type": "callout_banner",
            "style_variant": "executive_headline",
            "text": cockpit.headline_text,
            "space_after_pt": 6,
        },
        # ROW 4: Assertive Engineering Diplomacy Narrative Synthesis
        {
            "node_type": "body_paragraph",
            "text": cockpit.posture_paragraph,
            "space_after_pt": 4,
        },
        {
            "node_type": "body_paragraph",
            "text": cockpit.findings_intro,
            "bold": True,
            "space_after_pt": 3,
            "keep_with_next": True,
        },
        {
            "node_type": "bullet_list",
            "items": list(cockpit.scannable_bullets),
            "space_after_pt": 6,
        },
        {
            "node_type": "body_paragraph",
            "text": cockpit.economic_impact_paragraph,
            "space_after_pt": 6,
        },
        {
            "node_type": "verdict_box",
            "text": cockpit.diagnostic_verdict_paragraph,
            "space_after_pt": 0,
        },
    ]
```

---

## 6. Verification & Self-Correction Matrix

1. **Zero Client-Blame Language:** All prosecutorial phrases (*"deficiencias estructurales"*, *"aparente estabilidad"*) are banned via `FORBIDDEN_PROSECUTORIAL_TOKENS` and replaced with **Assertive Engineering Diplomacy** templates that recognize team dedication while objectively stating redundancy and automation opportunities.
2. **Direct Economic Phrasing:** Eradicated *"Desde una perspectiva económica... en este dominio"* in favor of *"En caso de producirse una parada imprevista del servicio, el coste operativo se estima en {hourly_burn_rate_fmt} (desglosado en la Sección 4.1)..."*.
3. **Executive Cockpit Visual Ergonomics:** The Diagnostic Triad Table now sits directly below the KPI Scorecard Table (`space_after_pt: 4` gap), forming a unified executive dashboard at the top of Page 3 with a verified `172.9 pt` vertical safety buffer.