# Matriz de Cobertura - Plantilla Larga de Torre

## Objetivo
Mapear la nueva plantilla `tower_main_report` contra los artefactos actuales del motor para identificar:
- que ya se puede generar con evidencia disponible
- que solo se puede generar parcialmente
- que hoy no esta cubierto

## Base analizada
La matriz se ha construido sobre los artefactos actuales disponibles en un caso real del motor:
- `case_input.json`
- `scoring_output.json`
- `findings.json`
- `evidence_ledger.json`
- `approved_asis.generated.json`
- `approved_risks.generated.json`
- `approved_tobe.generated.json`
- `approved_gap.generated.json`
- `approved_todo.generated.json`
- `approved_conclusion.generated.json`
- `approved_annex_*.template_payload_extended.json`

## Leyenda
- `Alta`: la seccion puede generarse de forma bastante fiable con el material actual.
- `Media`: la seccion puede generarse, pero necesitara composicion o inferencia controlada.
- `Baja`: la seccion solo puede rellenarse de forma muy parcial.
- `No cubierta`: hoy no hay datos ni estructura suficientes.

## Matriz

| Seccion nueva | Cobertura | Estado | Fuentes actuales | Observacion |
|---|---|---|---|---|
| Portada | Alta | Cubierta | `document_meta`, `case_input.json`, template actual | Ya existe toda la metadata basica para torre, cliente y variante. Faltarian solo campos formales como clasificacion o autor si se quieren poblar automaticamente. |
| Control documental | Baja | Parcial | Ninguna fuente funcional actual | Se puede crear una tabla minima con version y fecha de generacion, pero no hay workflow real de aprobaciones o distribucion. |
| Resumen tecnico ejecutivo | Alta | Cubierta | `executive_summary`, `approved_conclusion.generated.json`, `findings.json`, `scoring_output.json` | Esta muy bien cubierto por el payload actual. |
| Objeto del documento | Media | Parcial | `case_input.json`, `tower_definition_*.json` | El proposito de la torre existe, pero no el proposito formal del documento ni las decisiones que habilita. |
| Alcance y limites del analisis | Media | Parcial | `case_input.json`, `source_documents`, `validation_state`, `evidence_ledger.json` | Se puede construir alcance basico y restricciones de evidencia. Faltan exclusiones explicitas y limites metodologicos mas formales. |
| Contexto de la torre | Media | Parcial | `case_input.json`, `tower_definition_*.json` | Existe el `tower_purpose`, pero faltan dependencias, stakeholders y encaje en arquitectura cliente. |
| Metodologia de evaluacion | Alta | Parcial alta | `case_input.json`, `scoring_output.json`, `source_docs/methodology`, `tower_definition_*.json` | La metodologia del modelo y del scoring esta disponible. Faltaria explicitar en payload el resumen metodologico final para render directo. |
| Vision global del estado de la torre | Alta | Cubierta | `approved_asis.generated.json`, `findings.json`, `executive_summary` | Muy bien cubierta. |
| Grafico radial de evaluacion | Alta | Cubierta | `pillar_score_profile`, `scoring_output.json`, grafico generado | Totalmente soportado hoy. |
| Analisis detallado por dimension | Media | Parcial | `findings.json`, `approved_asis`, `approved_gap`, `approved_tobe`, `evidence_ledger.json` | Hay mucha materia prima por pilar, pero no existe un bloque narrativo unificado por dimension con objetivo, evidencia, riesgos, impacto y recomendaciones en un solo contrato. |
| Diagnostico consolidado | Media | Parcial alta | `approved_asis`, `approved_gap`, `approved_conclusion`, `findings.json` | Se puede generar bien con sintesis transversal. No existe como artefacto dedicado. |
| Estado objetivo de referencia | Alta | Cubierta | `approved_tobe.generated.json` | Muy bien cubierta, con capacidades objetivo por pilar y principios. |
| Brechas respecto al estado objetivo | Alta | Cubierta | `approved_gap.generated.json`, `approved_tobe.generated.json` | Muy bien cubierta. |
| Riesgos tecnicos y de continuidad | Alta | Cubierta | `approved_risks.generated.json`, `findings.json` | Muy bien cubierta. |
| Lineas de actuacion | Media | Parcial | Derivable desde `approved_todo.generated.json`, `approved_gap.generated.json` | Se puede derivar agrupando iniciativas, pero hoy no existe una capa intermedia entre gaps y proyectos. |
| Cartera de proyectos recomendados | Media | Parcial | `approved_todo.generated.json`, `findings.json` | Ya existen iniciativas con objetivo, prioridad, dependencias y resultado esperado. Faltan campos de alcance, complejidad, horizonte, riesgos de ejecucion e indicadores de exito. |
| Priorizacion de iniciativas | Media | Parcial | `approved_todo.generated.json`, `scoring_output.json`, `approved_gap.generated.json` | Hay prioridad declarada y dependencias, pero no criterios formales de priorizacion ni clasificacion quick wins / habilitadoras / estructurales. |
| Hoja de ruta de evolucion | Baja | Parcial baja | Derivable de `todo_items` si se enriquecen | No hay hoy horizonte temporal ni secuencia por tramos. Requiere logica nueva. |
| Recomendaciones finales para el responsable tecnico | Media | Parcial alta | `approved_conclusion.generated.json`, `approved_todo.generated.json`, `approved_gap.generated.json` | Se puede componer una buena version, pero no hay bloque especifico de decisiones recomendadas o validaciones pendientes. |
| Conclusiones | Alta | Cubierta | `approved_conclusion.generated.json` | Totalmente soportada. |
| Anexo A. Modelo de evaluacion y scoring | Alta | Cubierta | `scoring_output.json`, `source_docs/methodology`, `tower_definition_*.json` | Existe base suficiente. |
| Anexo B. Evidencias revisadas | Alta | Cubierta | `evidence_ledger.json` | Directamente soportado. |
| Anexo C. Hallazgos ampliados por dimension | Alta | Cubierta | `findings.json`, `approved_*` | Existe material suficiente por pilar. |
| Anexo D. Matriz de brechas | Alta | Cubierta | `approved_gap.generated.json` | Directamente soportado. |
| Anexo E. Matriz de riesgos | Alta | Cubierta | `approved_risks.generated.json` | Directamente soportado. |
| Anexo F. Fichas detalladas de proyectos | Media | Parcial | `approved_todo.generated.json` | Hay base clara, pero faltan varios campos para ficha completa. |
| Anexo G. Roadmap visual | Baja | No cubierta funcionalmente | No existe artefacto de roadmap | Requiere nueva logica de generacion. |
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
- Conclusiones
- Evidencias y anexos tecnicos basicos

### Lo que se puede construir con composicion controlada
- Objeto del documento
- Alcance y limites
- Contexto de la torre
- Metodologia
- Analisis detallado por dimension
- Diagnostico consolidado
- Lineas de actuacion
- Recomendaciones finales

### Lo que hoy requiere logica nueva o enriquecimiento
- Control documental formal
- Cartera de proyectos verdaderamente completa
- Priorizacion con criterios explicitos
- Hoja de ruta temporal
- Roadmap visual
- Glosario
- Registro formal de sesiones y entrevistas

## Conclusiones practicas
- La informacion actual es suficiente para generar una `v1` muy solida del documento largo.
- El nucleo tecnico del informe esta cubierto.
- Las mayores carencias no estan en el analisis de la torre, sino en la capa de transformacion: proyectos, priorizacion y roadmap.
- El siguiente paso razonable es construir un payload `tower_main_report` en version inicial, marcando como `parcial` las secciones de proyectos, priorizacion y roadmap.
