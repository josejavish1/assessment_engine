---
status: Verified
owner: docs-governance
source_of_truth:
  - ../../src/assessment_engine/schemas/annex_synthesis.py
last_verified_against: 2026-05-03
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Tower Annex Payload Contract

Este documento define la estructura y campos del artefacto `approved_annex_<tower>.template_payload.json`, que es una síntesis ejecutiva derivada del `blueprint_payload`.

El schema Pydantic que gobierna este contrato se encuentra en `src/assessment_engine/schemas/annex_synthesis.py`.

## Modelo Principal: `AnnexPayload`

Este es el objeto raíz del payload del anexo.

| Campo | Tipo | Descripción |
|---|---|---|
| `document_meta` | `dict` | Metadatos del documento (heredados del blueprint). |
| `executive_summary` | `ExecutiveSummaryAnnex` | Resumen ejecutivo de la torre. |
| `domain_introduction` | `DomainIntroduction` | Introducción al dominio tecnológico de la torre. |
| `pillar_score_profile` | `MaturityScoreProfile` | Perfil de madurez y puntuaciones por pilar. |
| `sections` | `AnnexSections` | Contenido detallado de las secciones del anexo. |
| `artifact_type` | `str` | Tipo de artefacto (`annex_payload`). Heredado de `VersionedPayload`. |
| `artifact_version` | `str` | Versión del artefacto (ej. `1.1.0`). Heredado de `VersionedPayload`. |

## Sub-modelos

### `ExecutiveSummaryAnnex`

Contiene el resumen de alto nivel para ejecutivos.

| Campo | Tipo | Descripción |
|---|---|---|
| `global_score` | `str` | Puntuación global de madurez de la torre. |
| `global_band` | `str` | Banda de madurez global (ej. "Estandarizado"). |
| `target_maturity` | `str` | Nivel de madurez objetivo. |
| `headline` | `str` | Titular o mensaje principal del assessment. |
| `summary_body` | `str` | Cuerpo del resumen ejecutivo. |
| `message_strength` | `str` | Mensaje clave sobre las fortalezas. |
| `message_gap` | `str` | Mensaje clave sobre las áreas de mejora. |
| `message_bottleneck`| `str` | Mensaje clave sobre los cuellos de botella. |
| `key_business_impacts` | `list[str]` | Impactos de negocio clave. |

### `DomainIntroduction`

Introduce el contexto de la torre evaluada.

| Campo | Tipo | Descripción |
|---|---|---|
| `introduction_paragraph`| `str` | Párrafo introductorio. |
| `technological_domain` | `str` | Dominio tecnológico de la torre. |
| `domain_objective` | `str` | Objetivo de negocio del dominio. |
| `evaluated_capabilities`| `list[str]` | Capacidades evaluadas en el assessment. |
| `included_components` | `list[str]` | Componentes o sistemas incluidos en el análisis. |

### `MaturityScoreProfile`

Presenta los resultados del scoring por pilar.

| Campo | Tipo | Descripción |
|---|---|---|
| `profile_intro` | `str` | Introducción al perfil de madurez. |
| `scoring_method_note` | `str` | Nota sobre la metodología de scoring. |
| `radar_chart` | `str` | (Reservado) Path o referencia al gráfico de radar. |
| `pillars` | `list[dict]` | Lista de pilares con sus puntuaciones (mapeado desde el blueprint). |

### `AnnexSections`

Agrupa todas las secciones de contenido del anexo.

| Campo | Tipo | Descripción |
|---|---|---|
| `asis` | `AsIsAnnex` | Sección sobre el estado actual. |
| `tobe` | `ToBeAnnex` | Sección sobre el estado objetivo. |
| `gap` | `GapAnnex` | Sección sobre las brechas (gaps). |
| `todo` | `TodoAnnex` | Sección sobre las iniciativas (To-Do). |
| `risks` | `RisksAnnex` | Sección sobre los riesgos. |
| `conclusion` | `ConclusionAnnex` | Sección de conclusiones. |

### `AsIsAnnex`

Describe el estado actual de la torre.

| Campo | Tipo | Descripción |
|---|---|---|
| `narrative` | `str` | Narrativa descriptiva del estado actual. |
| `strengths` | `list[str]` | Lista de fortalezas identificadas. |
| `gaps` | `list[str]` | Lista de brechas o debilidades. |
| `operational_impacts`| `list[str]` | Impactos operativos del estado actual. |

### `ToBeAnnex`

Describe la visión y principios del estado futuro.

| Campo | Tipo | Descripción |
|---|---|---|
| `vision` | `str` | Descripción de la visión de futuro. |
| `design_principles` | `list[str]` | Principios de diseño para la transformación. |

### `GapAnnex`

Detalla las brechas entre el estado actual y el objetivo.

| Campo | Tipo | Descripción |
|---|---|---|
| `introduction` | `str` | Introducción a la sección de brechas. |
| `target_capabilities`| `list[str]` | Capacidades objetivo a alcanzar. |
| `gap_rows` | `list[GapRowAnnex]` | Tabla de brechas por pilar. |
| `closing_summary` | `str` | Resumen de cierre de la sección. |

### `GapRowAnnex`

Fila en la tabla de análisis de brechas.

| Campo | Tipo | Descripción |
|---|---|---|
| `pillar` | `str` | Nombre del pilar. |
| `as_is_summary` | `str` | Resumen del estado actual del pilar. |
| `target_state` | `str` | Estado objetivo para el pilar. |
| `key_gap` | `str` | Brecha clave identificada. |

### `TodoAnnex`

Describe las iniciativas recomendadas.

| Campo | Tipo | Descripción |
|---|---|---|
| `introduction` | `str` | Introducción a la sección de iniciativas. |
| `priority_initiatives`| `list[InitiativeAnnex]` | Lista de iniciativas prioritarias. |
| `closing_summary` | `str` | Resumen de cierre de la sección. |

### `InitiativeAnnex`

Detalle de una iniciativa o proyecto.

| Campo | Tipo | Descripción |
|---|---|---|
| `sequence` | `int` | Número de secuencia. |
| `initiative` | `str` | Nombre de la iniciativa. |
| `objective` | `str` | Objetivo de la iniciativa. |
| `priority` | `str` | Nivel de prioridad (ej. "Alta"). |
| `expected_outcome` | `str` | Resultado esperado. |
| `dependencies_display`| `str` | Descripción de las dependencias. |

### `RisksAnnex`

Describe los riesgos identificados.

| Campo | Tipo | Descripción |
|---|---|---|
| `introduction` | `str` | Introducción a la sección de riesgos. |
| `risks` | `list[RiskItemAnnex]` | Lista de riesgos. |
| `closing_summary` | `str` | Resumen de cierre de la sección. |

### `RiskItemAnnex`

Detalle de un riesgo.

| Campo | Tipo | Descripción |
|---|---|---|
| `risk` | `str` | Descripción del riesgo. |
| `impact` | `str` | Impacto del riesgo. |
| `probability` | `str` | Probabilidad de ocurrencia. |
| `mitigation_summary` | `str` | Resumen de la estrategia de mitigación. |

### `ConclusionAnnex`

Cierre y conclusiones del informe.

| Campo | Tipo | Descripción |
|---|---|---|
| `final_assessment` | `str` | Valoración final de la torre. |
| `executive_message` | `str` | Mensaje final para ejecutivos. |
| `priority_focus_areas`| `list[str]`| Áreas de enfoque prioritarias. |
| `closing_statement` | `str` | Declaración de cierre. |
