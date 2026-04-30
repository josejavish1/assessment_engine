---
status: Draft
owner: docs-governance
source_of_truth:
  - ../../docs/contracts/tower_main_report_coverage_matrix.md
  - ../../src/assessment_engine/schemas/blueprint.py
  - ../../src/assessment_engine/schemas/annex_synthesis.py
  - ../../src/assessment_engine/scripts/render_tower_blueprint.py
  - ../../src/assessment_engine/scripts/render_tower_annex_from_template.py
last_verified_against: 2026-04-30
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Plantilla Base - Informe Tecnico Extendido de Torre

## Objetivo
Definir la plantilla operativa del documento largo para responsables tecnicos del cliente.

Este documento no es una ampliacion del anexo corto. Es el documento principal de analisis de la torre.

## Estado contractual actual

- hoy **no existe** un payload `tower_main_report` implementado ni un renderizador canónico para este documento largo;
- esta plantilla define el destino editorial deseado para una futura implementación;
- si se implementa, debe derivarse del flujo vigente `blueprint-first`, no del modelo legacy por secciones.

## Jerarquia de fuentes recomendada

1. `blueprint_<tower>_payload.json` como contrato principal.
2. `approved_annex_<tower>.template_payload.json` como sintesis ejecutiva derivada.
3. `case_input.json`, `evidence_ledger.json`, `scoring_output.json` y `findings.json` como soporte, trazabilidad y detalle.
4. Los ficheros `approved_asis/gap/tobe/todo/...generated.json` no deben volver a introducirse como dependencia canónica.

## Directriz visual
- Reutilizar la identidad visual de la version short.
- Mantener tipografia, jerarquia de titulos, cajas de nota y tablas del template `Template_Documento_Anexos_Alpha_v06_Tower_Annex_v2_6.docx`.
- Mantener el grafico radial dentro del cuerpo principal.
- Mantener tablas con cabecera azul claro y cuerpo blanco, con el mismo lenguaje visual del short.
- Priorizar legibilidad tecnica y densidad informativa sobre decoracion.

## Reglas editoriales
- Tono tecnico, formal y orientado a toma de decision.
- El lector objetivo es el responsable tecnico de la torre en cliente.
- Evitar repetir literalmente el mismo mensaje en resumen, diagnostico y conclusiones.
- Cada seccion debe responder a una pregunta distinta.
- No introducir roadmap detallado salvo en la seccion de hoja de ruta.
- No introducir proyectos salvo en lineas de actuacion, cartera y anexos relacionados.
- Explicar el estado actual con evidencia y el estado objetivo con criterios tecnicos, no con adjetivos vagos.

## Portada
**Titulo**
`Informe tecnico extendido de evaluacion de torre`

**Placeholders**
- `{{DOC_TITLE}}`
- `{{TOWER_CODE}}`
- `{{TOWER_NAME}}`
- `{{CLIENT_NAME}}`
- `{{REPORT_VERSION}}`
- `{{REPORT_DATE}}`
- `{{DOCUMENT_CLASSIFICATION}}`
- `{{AUTHORING_TEAM}}`

## 1. Control documental
**Proposito**
Dar trazabilidad al documento.

**Contenido**
- Versionado
- Historial de cambios
- Revisores
- Aprobadores
- Estado documental

**Placeholders**
- `{{DOC_CONTROL_TABLE}}`

## 1.1 Identificacion del documento
**Proposito**
Introducir formalmente la naturaleza del informe, su alcance general y el valor que aporta al lector tecnico.

**Texto base reutilizable**
El presente documento constituye el informe tecnico extendido de resultados del Fast Infrastructure Assessment realizado sobre la torre `{{TOWER_CODE}} - {{TOWER_NAME}}` del cliente `{{CLIENT_NAME}}`.

Este informe recoge de forma estructurada los resultados obtenidos a partir del modelo de evaluacion de madurez aplicado a la torre, proporcionando una vision clara y accionable de:
- el estado actual de la torre derivado del blueprint y de la sintesis ejecutiva
- el estado objetivo recomendado por capacidad y por pilar
- y las iniciativas de evolucion necesarias para avanzar hacia dicho estado

El documento se ha disenado para ofrecer una vision simultaneamente tecnica y ejecutiva, permitiendo a responsables de infraestructura, operaciones, continuidad, seguridad, arquitectura y gobierno tecnologico comprender con claridad:
- el nivel actual de madurez de la torre
- los riesgos asociados al estado actual
- las brechas existentes frente al estado objetivo
- y las acciones necesarias para evolucionar hacia un modelo mas resiliente, eficiente y gobernado

**Placeholders**
- `{{DOCUMENT_IDENTIFICATION_INTRO}}`
- `{{EVALUATED_TOWERS_COUNT}}`
- `{{EVALUATED_TOWERS_LIST}}`

## 1.2 Disclaimer del analisis
**Proposito**
Dejar explicitas las limitaciones del assessment y evitar que el documento se interprete como una auditoria formal.

**Texto base reutilizable**
El analisis se basa exclusivamente en la informacion, respuestas y evidencias facilitadas durante el proceso de evaluacion.

No se ha realizado una auditoria tecnica completa ni una validacion exhaustiva de configuraciones, controles o evidencias formales de todos los sistemas implicados.

Por tanto, este documento debe interpretarse como una evaluacion estructurada de alto nivel del estado de madurez de la torre, no como una auditoria tecnica detallada.

**Placeholders**
- `{{ANALYSIS_DISCLAIMER}}`

## 2. Resumen tecnico ejecutivo
**Proposito**
Dar una lectura inicial de la torre en una o dos paginas.

**Contenido**
- Valoracion global
- Principales hallazgos
- Riesgos prioritarios
- Brechas principales
- Mensaje final para el responsable tecnico

**Placeholders**
- `{{GLOBAL_SCORE}}`
- `{{GLOBAL_BAND}}`
- `{{TARGET_MATURITY}}`
- `{{EXEC_SUMMARY_BODY}}`
- `{{MSG_STRENGTH_VALUE}}`
- `{{MSG_GAP_VALUE}}`
- `{{MSG_BOTTLENECK_VALUE}}`

## 3. Objeto del documento
**Proposito**
Explicar para que existe el informe y que decisiones soporta.

**Placeholders**
- `{{DOCUMENT_PURPOSE}}`
- `{{DECISION_SUPPORT_SCOPE}}`
- `{{TARGET_AUDIENCE_NOTE}}`

## 4. Alcance y limites del analisis
**Proposito**
Delimitar el perimetro del informe.

**Placeholders**
- `{{ANALYSIS_SCOPE}}`
- `{{ANALYSIS_LIMITATIONS}}`
- `{{ANALYSIS_ASSUMPTIONS}}`
- `{{OUT_OF_SCOPE_LIST}}`

## 5. Contexto de la torre
**Proposito**
Situar la torre en el ecosistema tecnologico del cliente.

**Placeholders**
- `{{TOWER_CONTEXT}}`
- `{{SUPPORTED_CAPABILITIES_LIST}}`
- `{{KEY_DEPENDENCIES_LIST}}`
- `{{TECH_STAKEHOLDERS_LIST}}`

## 6. Metodologia de evaluacion
**Proposito**
Describir como se ha realizado el analisis y con que criterios.

**Texto base reutilizable**
El modelo de evaluacion utilizado en este Fast Infrastructure Assessment se basa en una estructura jerarquica de varios niveles que permite descomponer la madurez de la infraestructura en componentes medibles y accionables.

Dentro de cada torre tecnologica, los pilares representan las areas funcionales que agrupan capacidades afines. Cada pilar tiene un peso especifico en el score total de la torre, reflejando su importancia relativa.

Cada pilar se evalua mediante un conjunto de KPIs que miden el grado de implantacion de capacidades concretas. Los KPIs se puntuan en una escala de 1 a 5.

La lectura de madurez puede expresarse con el siguiente marco:
1. Inicial
2. En desarrollo
3. Estandarizado
4. Optimizado
5. Excelencia

La puntuacion de la torre se obtiene mediante:
- score por pilar: promedio ponderado de los KPIs que lo componen
- score de la torre: promedio ponderado de los pilares segun su peso asignado

Este enfoque permite no solo obtener una calificacion numerica, sino tambien localizar con precision fortalezas, brechas y prioridades de evolucion.

**Placeholders**
- `{{METHODOLOGY_OVERVIEW}}`
- `{{EVIDENCE_SOURCES_LIST}}`
- `{{SCORING_METHOD_NOTE}}`
- `{{METHODOLOGY_LIMITATIONS}}`
- `{{PILLAR_DESCRIPTIONS_LIST}}`
- `{{MATURITY_SCALE_TABLE}}`

## 7. Vision global del estado de la torre
**Proposito**
Ofrecer una lectura sintetica del punto de partida.

**Placeholders**
- `{{CURRENT_STATE_OVERVIEW}}`
- `{{STRUCTURAL_STRENGTHS_LIST}}`
- `{{STRUCTURAL_WEAKNESSES_LIST}}`
- `{{CROSS_CUTTING_CONSTRAINTS_LIST}}`

## 8. Grafico radial de evaluacion
**Proposito**
Incorporar el artefacto visual principal de la evaluacion.

**Contenido**
- Grafico radial
- Lectura global
- Pilar mas fuerte
- Pilar mas debil
- Lectura estructural

**Placeholders**
- `{{RADAR_CHART_BLOCK}}`
- `{{PILLAR_PROFILE_INTRO}}`
- `{{PILLAR_SCORE_TABLE}}`
- `{{STRONGEST_PILLAR}}`
- `{{WEAKEST_PILLARS}}`
- `{{STRUCTURAL_READING}}`

## 9. Analisis detallado por dimension
**Proposito**
Desarrollar el cuerpo tecnico principal del documento.

**Estructura por dimension**
- Objetivo de la dimension
- Situacion actual
- Evidencias relevantes
- Valoracion tecnica
- Riesgos asociados
- Impacto sobre la torre
- Gap frente al objetivo
- Recomendaciones especificas

**Placeholders**
- `{{DIMENSION_ANALYSIS_BLOCKS}}`

**Contrato esperado por bloque**
- `dimension_name`
- `dimension_objective`
- `current_state`
- `evidence_points`
- `technical_assessment`
- `associated_risks`
- `tower_impact`
- `target_gap`
- `recommendations`

## 10. Diagnostico consolidado
**Proposito**
Integrar los hallazgos en una vision transversal.

**Placeholders**
- `{{CONSOLIDATED_DIAGNOSIS}}`
- `{{STRUCTURAL_ISSUES_LIST}}`
- `{{POINT_ISSUES_LIST}}`
- `{{LIMITING_FACTORS_LIST}}`

## 11. Estado objetivo de referencia
**Proposito**
Definir como deberia ser la torre en el escenario objetivo.

**Placeholders**
- `{{TOBE_INTRO}}`
- `{{TARGET_CAPABILITIES_LIST}}`
- `{{ARCHITECTURE_PRINCIPLES_LIST}}`
- `{{OPERATING_MODEL_IMPLICATIONS_LIST}}`
- `{{TARGET_STATE_BY_DIMENSION_TABLE}}`

## 12. Brechas respecto al estado objetivo
**Proposito**
Expresar la distancia real entre el estado actual y el estado objetivo.

**Placeholders**
- `{{GAP_INTRO}}`
- `{{CROSS_CUTTING_GAP_SUMMARY_LIST}}`
- `{{GAP_TABLE}}`
- `{{DETAILED_GAP_CARDS}}`

## 13. Riesgos tecnicos y de continuidad
**Proposito**
Formalizar los riesgos que se derivan del estado actual y de la no actuacion.

**Placeholders**
- `{{RISKS_INTRO}}`
- `{{RISKS_TABLE}}`
- `{{RISKS_DETAILED_CARDS}}`
- `{{RISKS_CLOSING}}`

## 14. Lineas de actuacion
**Proposito**
Agrupar las respuestas recomendadas en bloques coherentes.

**Placeholders**
- `{{ACTION_LINES_INTRO}}`
- `{{ACTION_LINES_TABLE}}`

## 15. Cartera de proyectos recomendados
**Proposito**
Traducir el diagnostico en iniciativas concretas y defendibles.

**Contenido por proyecto**
- Nombre
- Objetivo
- Problema que resuelve
- Alcance
- Beneficio esperado
- Dependencias
- Prioridad
- Complejidad estimada
- Horizonte temporal
- Riesgos de ejecucion
- Indicadores de exito

**Placeholders**
- `{{PROJECT_PORTFOLIO_INTRO}}`
- `{{PRIORITY_INITIATIVES_CARDS}}`
- `{{PROJECT_PORTFOLIO_TABLE}}`

## 16. Priorizacion de iniciativas
**Proposito**
Ordenar la cartera con criterios tecnicos y de implantacion.

**Placeholders**
- `{{PRIORITIZATION_CRITERIA_LIST}}`
- `{{QUICK_WINS_LIST}}`
- `{{ENABLING_INITIATIVES_LIST}}`
- `{{STRUCTURAL_INITIATIVES_LIST}}`
- `{{PRIORITIZATION_RATIONALE}}`

## 17. Hoja de ruta de evolucion
**Proposito**
Proponer una secuencia temporal de transformacion.

**Placeholders**
- `{{ROADMAP_INTRO}}`
- `{{ROADMAP_TABLE}}`
- `{{ROADMAP_VISUAL_BLOCK}}`
- `{{ROADMAP_MILESTONES_LIST}}`
- `{{CRITICAL_DEPENDENCIES_LIST}}`

## 18. Recomendaciones finales para el responsable tecnico
**Proposito**
Cerrar el informe con orientacion accionable y concreta.

**Placeholders**
- `{{FINAL_RECOMMENDATIONS}}`
- `{{DECISIONS_RECOMMENDED_LIST}}`
- `{{VALIDATION_NEEDS_LIST}}`

## 19. Conclusiones
**Proposito**
Emitir el juicio tecnico final sobre la torre.

**Placeholders**
- `{{FINAL_ASSESSMENT}}`
- `{{EXECUTIVE_MESSAGE}}`
- `{{PRIORITY_AREAS_LIST}}`
- `{{CLOSING_STATEMENT}}`

## 20. Anexos
**Proposito**
Incorporar soporte tecnico sin romper la narrativa principal.

**Anexos recomendados**
- Anexo A. Modelo de evaluacion y criterios de scoring
- Anexo B. Evidencias revisadas
- Anexo C. Hallazgos ampliados por dimension
- Anexo D. Matriz de brechas
- Anexo E. Matriz de riesgos
- Anexo F. Fichas detalladas de proyectos
- Anexo G. Roadmap visual
- Anexo H. Glosario y acronimos
- Anexo I. Relacion de sesiones, entrevistas y fuentes

**Placeholders**
- `{{ANNEX_SCORING_MODEL}}`
- `{{ANNEX_EVIDENCE_LOG}}`
- `{{ANNEX_DIMENSION_FINDINGS}}`
- `{{ANNEX_GAP_MATRIX}}`
- `{{ANNEX_RISK_MATRIX}}`
- `{{ANNEX_PROJECT_SHEETS}}`
- `{{ANNEX_ROADMAP_VISUAL}}`
- `{{ANNEX_GLOSSARY}}`
- `{{ANNEX_SOURCES}}`

## Notas de implementacion
- La plantilla larga debe renderizarse con el mismo template visual base de la version short.
- La diferencia no debe estar en la identidad grafica, sino en la arquitectura del contenido.
- Si una seccion no tiene informacion suficiente, el sistema debe marcarla como `pendiente de completar` o generar una version parcial basada en evidencia, sin inventar.
- La futura implementación debe construir el documento desde `blueprint_<tower>_payload.json` como fuente principal, usando `approved_annex_<tower>.template_payload.json` solo como capa de sintesis ejecutiva.
- No debe depender de `approved_asis.generated.json`, `approved_gap.generated.json`, `approved_tobe.generated.json`, `approved_todo.generated.json` ni otros artefactos legacy como fuente primaria.
