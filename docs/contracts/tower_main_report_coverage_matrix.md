---
status: Draft
owner: docs-governance
source_of_truth:
  - ../../working/
  - ../../src/assessment_engine/schemas/blueprint.py
  - ../../src/assessment_engine/schemas/annex_synthesis.py
  - ../../src/assessment_engine/scripts/run_tower_pipeline.py
  - ../../src/assessment_engine/scripts/run_tower_blueprint_engine.py
last_verified_against: 2026-04-30
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Matriz de Cobertura - Plantilla Larga de Torre

## Objetivo
Mapear la nueva plantilla `tower_main_report` contra los artefactos actuales del motor para identificar:
- que ya se puede generar con evidencia disponible
- que solo se puede generar parcialmente
- que hoy no esta cubierto

## Base analizada
La matriz se ha construido sobre los artefactos actuales disponibles en un caso real del motor:
- `blueprint_<tower>_payload.json`
- `approved_annex_<tower>.template_payload.json`
- `case_input.json`
- `scoring_output.json`
- `findings.json`
- `evidence_ledger.json`

## Jerarquia de fuentes observada

Para el flujo vigente del repo, la lectura correcta no parte de los JSON legacy por seccion, sino de esta jerarquia:

1. `blueprint_<tower>_payload.json` como fuente principal de verdad por torre.
2. `approved_annex_<tower>.template_payload.json` como sintesis ejecutiva derivada del blueprint.
3. `case_input.json`, `evidence_ledger.json`, `scoring_output.json` y `findings.json` como artefactos de soporte y trazabilidad.
4. Los JSON `approved_asis/gap/tobe/todo/...generated.json` deben tratarse como legado y no como base canónica para nuevos contratos.

## Leyenda
- `Alta`: la seccion puede generarse de forma bastante fiable con el material actual.
- `Media`: la seccion puede generarse, pero necesitara composicion o inferencia controlada.
- `Baja`: la seccion solo puede rellenarse de forma muy parcial.
- `No cubierta`: hoy no hay datos ni estructura suficientes.

## Matriz

| Seccion nueva | Cobertura | Estado | Fuentes actuales | Observacion |
|---|---|---|---|---|
| Portada | Alta | Cubierta | `blueprint.document_meta`, `annex.document_meta`, template actual | Ya existe la metadata base de torre, cliente y variante. Faltan solo campos formales como clasificacion o autor si se quieren poblar automaticamente. |
| Control documental | Baja | Parcial | Ninguna fuente funcional actual | Se puede crear una tabla minima con version y fecha de generacion, pero no hay workflow real de aprobaciones o distribucion. |
| Resumen tecnico ejecutivo | Alta | Cubierta | `annex.executive_summary`, `blueprint.executive_snapshot`, `findings.json`, `scoring_output.json` | Esta bien cubierto en el flujo actual: el anexo ya resume la torre y el blueprint aporta el cierre estrategico. |
| Objeto del documento | Media | Parcial | `case_input.json`, `tower_definition_*.json` | El proposito de la torre existe, pero no el proposito formal del documento ni las decisiones que habilita. |
| Alcance y limites del analisis | Media | Parcial | `case_input.json`, `source_documents`, `validation_state`, `evidence_ledger.json` | Se puede construir alcance basico y restricciones de evidencia. Faltan exclusiones explicitas y limites metodologicos mas formales. |
| Contexto de la torre | Media | Parcial | `case_input.json`, `tower_definition_*.json` | Existe el `tower_purpose`, pero faltan dependencias, stakeholders y encaje en arquitectura cliente. |
| Metodologia de evaluacion | Alta | Parcial alta | `case_input.json`, `scoring_output.json`, `source_docs/methodology`, `tower_definition_*.json` | La metodologia del modelo y del scoring esta disponible. Faltaria explicitar en payload el resumen metodologico final para render directo. |
| Vision global del estado de la torre | Alta | Cubierta | `blueprint.executive_snapshot`, `blueprint.cross_capabilities_analysis`, `annex.sections.asis` | Hoy ya existe una lectura transversal de la torre sin depender del antiguo `approved_asis.generated.json`. |
| Grafico radial de evaluacion | Alta | Cubierta | `annex.pillar_score_profile`, `scoring_output.json`, grafico generado | Totalmente soportado hoy. |
| Analisis detallado por dimension | Alta | Parcial alta | `blueprint.pillars_analysis`, `findings.json`, `evidence_ledger.json` | El blueprint ya concentra objetivo, riesgo observado, impacto, target y proyectos por pilar. Sigue faltando un contrato dedicado para presentarlo como bloque largo unificado. |
| Diagnostico consolidado | Alta | Cubierta | `blueprint.executive_snapshot`, `blueprint.cross_capabilities_analysis`, `findings.json` | El blueprint ya ofrece una sintesis transversal suficiente para esta seccion. |
| Estado objetivo de referencia | Alta | Cubierta | `blueprint.pillars_analysis[].target_architecture_tobe`, `annex.sections.tobe` | Muy bien cubierta con capacidades objetivo por pilar y principios de diseno. |
| Brechas respecto al estado objetivo | Alta | Cubierta | `annex.sections.gap`, `blueprint.pillars_analysis` | Muy bien cubierta por la sintesis del anexo y el detalle del blueprint. |
| Riesgos tecnicos y de continuidad | Alta | Cubierta | `annex.sections.risks`, `blueprint.executive_snapshot.structural_risks`, `findings.json` | Muy bien cubierta. |
| Lineas de actuacion | Alta | Cubierta | `annex.sections.todo`, `blueprint.pillars_analysis[].projects_todo` | Ya se pueden agrupar iniciativas sin recurrir al `approved_todo.generated.json` legacy. |
| Cartera de proyectos recomendados | Media | Parcial alta | `blueprint.pillars_analysis[].projects_todo`, `annex.sections.todo` | Ya existen iniciativa, objetivo, deliverables, sizing y duracion. Faltan campos como indicadores de exito, riesgos de ejecucion y ownership formal. |
| Priorizacion de iniciativas | Media | Parcial | `annex.sections.todo.priority_initiatives`, `blueprint.roadmap`, `blueprint.external_dependencies` | Hay prioridad visible y secuencia por olas, pero no criterios formales de priorizacion ni taxonomia quick wins/habilitadoras/estructurales. |
| Hoja de ruta de evolucion | Media | Parcial alta | `blueprint.roadmap`, `blueprint.external_dependencies` | Ya existe secuencia por waves y dependencias externas. Sigue faltando una traduccion a roadmap visual/ejecutivo largo con horizontes y hitos homogéneos. |
| Recomendaciones finales para el responsable tecnico | Alta | Cubierta | `blueprint.executive_snapshot.decisions`, `annex.sections.conclusion` | Se puede construir una version solida combinando decisiones del blueprint y cierre ejecutivo del anexo. |
| Conclusiones | Alta | Cubierta | `annex.sections.conclusion`, `blueprint.executive_snapshot` | Totalmente soportada. |
| Anexo A. Modelo de evaluacion y scoring | Alta | Cubierta | `scoring_output.json`, `source_docs/methodology`, `tower_definition_*.json` | Existe base suficiente. |
| Anexo B. Evidencias revisadas | Alta | Cubierta | `evidence_ledger.json` | Directamente soportado. |
| Anexo C. Hallazgos ampliados por dimension | Alta | Cubierta | `blueprint.pillars_analysis`, `findings.json`, `evidence_ledger.json` | Existe material suficiente por pilar. |
| Anexo D. Matriz de brechas | Alta | Cubierta | `annex.sections.gap`, `blueprint.pillars_analysis` | Directamente soportado. |
| Anexo E. Matriz de riesgos | Alta | Cubierta | `annex.sections.risks`, `blueprint.executive_snapshot.structural_risks` | Directamente soportado. |
| Anexo F. Fichas detalladas de proyectos | Media | Parcial alta | `blueprint.pillars_analysis[].projects_todo`, `blueprint.roadmap` | Hay base clara, pero faltan varios campos para ficha completa. |
| Anexo G. Roadmap visual | Media | Parcial | `blueprint.roadmap`, `blueprint.external_dependencies` | Ya existe materia prima para generar una vista visual, pero no un artefacto canónico renderizado hoy para este informe largo. |
| Anexo H. Glosario y acronimos | Baja | Parcial baja | Derivable de metodologia y textos | No hay glosario estructurado. |
| Anexo I. Relacion de sesiones, entrevistas y fuentes | Baja | Parcial | `source_documents`, trazas de input | Hay fuentes, pero no sesiones ni entrevistas estructuradas. |

## Lectura ejecutiva de cobertura

### Lo que ya esta bastante resuelto
- Resumen tecnico
- Vision global
- Grafico radial y perfil por pilar
- Estado objetivo
- Brechas
- Riesgos
- Lineas de actuacion
- Conclusiones
- Evidencias y anexos tecnicos basicos

### Lo que se puede construir con composicion controlada
- Objeto del documento
- Alcance y limites
- Contexto de la torre
- Metodologia
- Analisis detallado por dimension
- Cartera de proyectos
- Priorizacion
- Hoja de ruta visual
- Recomendaciones finales

### Lo que hoy requiere logica nueva o enriquecimiento
- Control documental formal
- Criterios formales de priorizacion
- Fichas de proyecto con gobierno, ownership e indicadores
- Glosario
- Registro formal de sesiones y entrevistas

## Conclusiones practicas
- La informacion actual es suficiente para generar una `v1` muy solida del documento largo.
- El nucleo tecnico del informe esta cubierto.
- Las mayores carencias ya no estan en AS-IS/TO-BE/GAP por separado, sino en la capa de empaquetado editorial y gobierno del documento largo.
- El siguiente paso razonable es construir un payload `tower_main_report` inicial derivado de `blueprint + annex + artifacts deterministas`, sin reintroducir dependencias sobre JSON legacy por secciones.
