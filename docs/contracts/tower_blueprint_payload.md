---
status: Verified
owner: docs-governance
source_of_truth:
  - ../../src/assessment_engine/schemas/blueprint.py
last_verified_against: 2026-05-03
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Tower Blueprint Payload Contract

Este documento define la estructura y campos del artefacto `blueprint_<tower>_payload.json`, que actúa como la **fuente de verdad** para el análisis de una torre tecnológica.

El schema Pydantic que gobierna este contrato se encuentra en `src/assessment_engine/schemas/blueprint.py`.

## Modelo Principal: `BlueprintPayload`

Este es el objeto raíz del payload.

| Campo | Tipo | Descripción |
|---|---|---|
| `document_meta` | `BlueprintDocumentMeta` | Metadatos del documento y del cliente. |
| `pillars_analysis` | `list[PillarBlueprintDraft]` | Análisis detallado por cada pilar de la torre. |
| `executive_snapshot` | `ExecutiveSnapshot` | Resumen ejecutivo para la toma de decisiones. |
| `cross_capabilities_analysis` | `CrossCapabilitiesAnalysis` | Análisis de patrones y deudas transversales. |
| `roadmap` | `list[RoadmapWave]` | Hoja de ruta de transformación propuesta. |
| `external_dependencies` | `list[ExternalDependency]` | Dependencias externas entre proyectos. |
| `artifact_type` | `str` | Tipo de artefacto (`blueprint_payload`). Heredado de `VersionedPayload`. |
| `artifact_version` | `str` | Versión del artefacto (ej. `1.1.0`). Heredado de `VersionedPayload`. |

## Sub-modelos

### `BlueprintDocumentMeta`

Metadatos que identifican el contexto del informe.

| Campo | Tipo | Descripción |
|---|---|---|
| `client_name` | `str` | Nombre del cliente. |
| `tower_name` | `str` | Nombre de la torre tecnológica. |
| `tower_code` | `str` | Código identificador de la torre. |
| `financial_tier` | `str` | Nivel financiero o de importancia del cliente. |
| `transformation_horizon` | `str` | Horizonte temporal de la transformación (ej. "3 años"). |

### `PillarBlueprintDraft`

Análisis detallado de un pilar tecnológico.

| Campo | Tipo | Descripción |
|---|---|---|
| `pilar_id` | `str` | Identificador único del pilar. |
| `pilar_name` | `str` | Nombre del pilar. |
| `score` | `float` | Puntuación de madurez del pilar. |
| `target_score` | `float` | Puntuación objetivo para el pilar. |
| `health_check_asis` | `list[HealthCheckAsIs]` | Diagnóstico del estado actual (AS-IS). |
| `target_architecture_tobe` | `TargetArchitectureToBe` | Visión de la arquitectura objetivo (TO-BE). |
| `projects_todo` | `list[ProjectToDo]` | Proyectos o iniciativas recomendadas. |

### `HealthCheckAsIs`

Describe un hallazgo específico en el estado actual de una capacidad.

| Campo | Tipo | Alias JSON | Descripción |
|---|---|---|---|
| `target_state` | `str` | `capability` | Capacidad o estado objetivo evaluado. |
| `risk_observed` | `str` | `finding` | Hallazgo o riesgo observado. |
| `impact` | `str` | `business_risk` | Impacto de negocio del riesgo. |

### `TargetArchitectureToBe`

Describe la visión y principios de la arquitectura futura.

| Campo | Tipo | Descripción |
|---|---|---|
| `vision` | `str` | Descripción de la visión de futuro. |
| `design_principles` | `list[str]` | Principios de diseño que guiarán la transformación. |

### `ProjectToDo`

Describe una iniciativa o proyecto recomendado.

| Campo | Tipo | Alias JSON | Descripción |
|---|---|---|---|
| `initiative` | `str` | `name` | Nombre de la iniciativa. |
| `expected_outcome` | `str` | `business_case` | Resultado de negocio esperado. |
| `objective` | `str` | `tech_objective` | Objetivo técnico de la iniciativa. |
| `deliverables` | `list[str]` | Entregables concretos del proyecto. |
| `sizing` | `str` | Estimación de tamaño (ej. "Grande", "Pequeño"). |
| `duration` | `str` | Duración estimada (ej. "3 meses"). |

### `ExecutiveSnapshot`

Resumen de alto nivel para ejecutivos.

| Campo | Tipo | Descripción |
|---|---|---|
| `bottom_line` | `str` | Conclusión principal y mensaje clave. |
| `decisions` | `list[str]` | Decisiones que se deben tomar. |
| `cost_of_inaction` | `str` | Coste o riesgo de no actuar. |
| `structural_risks` | `list[str]` | Riesgos estructurales identificados. |
| `business_impact` | `str` | Impacto general en el negocio. |
| `operational_benefits` | `list[str]` | Beneficios operativos esperados de la transformación. |
| `transformation_complexity` | `str` | Nivel de complejidad de la transformación. |

### `CrossCapabilitiesAnalysis`

Análisis de patrones que afectan a múltiples capacidades.

| Campo | Tipo | Descripción |
|---|---|---|
| `common_deficiency_patterns` | `list[str]` | Patrones de deficiencia comunes. |
| `transformation_paradigm` | `str` | Paradigma o enfoque de la transformación. |
| `critical_technical_debt` | `str` | Deuda técnica crítica que debe abordarse. |

### `RoadmapWave`

Agrupa proyectos en una ola o fase temporal del roadmap.

| Campo | Tipo | Descripción |
|---|---|---|
| `wave` | `str` | Nombre de la ola (ej. "Ola 1: Fundación"). |
| `projects` | `list[str]` | Nombres de los proyectos incluidos en la ola. |

### `ExternalDependency`

Describe una dependencia entre proyectos.

| Campo | Tipo | Descripción |
|---|---|---|
| `project` | `str` | Nombre del proyecto que tiene la dependencia. |
| `depends_on` | `str` | Nombre del proyecto del que depende. |
| `reason` | `str` | Razón de la dependencia. |
