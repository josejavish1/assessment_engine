---
status: Verified
owner: docs-governance
source_of_truth:
  - ../../src/assessment_engine/scripts/run_tower_pipeline.py
  - ../../src/assessment_engine/scripts/run_tower_blueprint_engine.py
  - ../../src/assessment_engine/scripts/run_executive_annex_synthesizer.py
  - ../../src/assessment_engine/scripts/render_tower_blueprint.py
  - ../../src/assessment_engine/scripts/render_tower_annex_from_template.py
  - ../../src/assessment_engine/scripts/run_global_pipeline.py
  - ../../src/assessment_engine/scripts/build_global_report_payload.py
  - ../../src/assessment_engine/scripts/run_executive_refiner.py
  - ../../src/assessment_engine/scripts/render_global_report_from_template.py
  - ../../src/assessment_engine/scripts/run_commercial_pipeline.py
  - ../../src/assessment_engine/scripts/run_commercial_refiner.py
  - ../../src/assessment_engine/scripts/render_commercial_report.py
  - ../../src/assessment_engine/scripts/render_web_presentation.py
last_verified_against: 2026-04-30
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Critical modules map

Este documento identifica los **módulos críticos** que sostienen el flujo principal de `assessment-engine`. No pretende describir cada función interna, sino dejar claro:

1. qué responsabilidad empresarial tiene cada módulo;
2. qué inputs y outputs controla;
3. por qué es crítico para el sistema;
4. qué riesgo operativo aparece si falla o deriva.

## Cómo leer este mapa

| Tipo de módulo | Qué decide |
|---|---|
| Orchestrator | qué secuencia se ejecuta y con qué dependencias |
| Engine / Refiner | qué contenido estructural se genera o transforma |
| Builder | cómo se consolida o normaliza un payload |
| Renderer | cómo un payload se convierte en entregable visible |

## 1. Núcleo por torre

| Módulo | Tipo | Responsabilidad principal | Input dominante | Output dominante | Riesgo si falla |
|---|---|---|---|---|---|
| `run_tower_pipeline.py` | orchestrator | coordina la ejecución por torre, prepara entorno, reanudación y tiempos límite de pasos IA | `--tower`, `--client`, contexto, respuestas | ejecución completa sobre `working/<client>/<tower>/` | la torre no produce activos o queda en estado parcial |
| `run_tower_blueprint_engine.py` | engine | genera el **activo canónico por torre** a partir del caso y los pilares | `case_input.json`, definición de torre, `client_intelligence.json` opcional | `blueprint_<tower>_payload.json` | se pierde la fuente de verdad estructural |
| `run_executive_annex_synthesizer.py` | refiner / synthesizer | deriva la lectura ejecutiva desde el blueprint y fuerza no-negotiables | `blueprint_<tower>_payload.json` | `approved_annex_<tower>.template_payload.json` | reaparece incoherencia entre lectura técnica y ejecutiva |
| `render_tower_blueprint.py` | renderer | convierte el blueprint en un DOCX técnico legible | blueprint payload y annex derivado de apoyo | `Blueprint_Transformacion_<tower>_<client>.docx` | cae la calidad del entregable técnico, no debería redefinir lógica |
| `render_tower_annex_from_template.py` | renderer | convierte el annex payload en un DOCX ejecutivo | annex payload y plantilla DOCX | `annex_<tower>_<client>_final.docx` | deterioro de presentación o desalineación visible al cliente |

### Lectura empresarial de este bloque

La torre es el sitio donde se fabrica el activo más importante del sistema: el **blueprint**. Todo lo demás por torre debería leerse como:

- preparación de base;
- construcción de verdad;
- traducción de audiencia;
- presentación final.

## 2. Elevación global

| Módulo | Tipo | Responsabilidad principal | Input dominante | Output dominante | Riesgo si falla |
|---|---|---|---|---|---|
| `run_global_pipeline.py` | orchestrator | ejecuta la consolidación global extremo a extremo | `working/<client>/` con torres disponibles | payload global refinado + DOCX ejecutivo global | la dirección pierde visión consolidada |
| `build_global_report_payload.py` | builder | agrega torres, priorizando blueprints modernos y tolerando fallback legacy | blueprints por torre y legacy residual | `global_report_payload.json` inicial | la agregación queda sesgada o híbrida de forma poco visible |
| `run_executive_refiner.py` | refiner | reescribe el payload global como narrativa ejecutiva de dirección | `global_report_payload.json` | `global_report_payload.json` refinado in place | el output global queda técnico pero no accionable |
| `render_global_report_from_template.py` | renderer | genera el entregable DOCX global a partir del payload refinado | payload global + plantilla | `Informe_Ejecutivo_Consolidado_<client>.docx` | erosiona credibilidad de la capa ejecutiva |

### Qué hace especial a esta capa

Aquí el sistema deja de hablar de una torre y empieza a hablar de la **agenda de transformación del cliente**. Por eso el builder y el refiner global no solo agregan: **seleccionan, priorizan y editorializan**.

## 3. Explotación comercial

| Módulo | Tipo | Responsabilidad principal | Input dominante | Output dominante | Riesgo si falla |
|---|---|---|---|---|---|
| `run_commercial_pipeline.py` | orchestrator | ejecuta el flujo comercial interno a partir del contexto global | `global_report_payload.json` | payload comercial + Account Action Plan | se rompe la activación comercial del assessment |
| `run_commercial_refiner.py` | refiner / orchestrator | mezcla contexto global con catálogo táctico de blueprints y orquesta agentes de propuesta | payload global + blueprints por torre | `commercial_report_payload.json` | la narrativa comercial se desacopla de la realidad técnica |
| `render_commercial_report.py` | renderer | materializa el plan comercial interno en DOCX | payload comercial + plantilla | `Account_Action_Plan_<client>.docx` | baja utilidad para equipos de cuenta, preventa y delivery |

### Qué distingue este bloque del global

La capa comercial no consolida para dirección; consolida para **movilizar cuenta y propuesta**. Por eso el refinador comercial:

- reutiliza el relato global;
- vuelve a mirar blueprints por torre;
- genera pipeline, oportunidades y propuestas proactivas.

## 4. Superficie web

| Módulo | Tipo | Responsabilidad principal | Input dominante | Output dominante | Riesgo si falla |
|---|---|---|---|---|---|
| `render_web_presentation.py` | renderer / composer | construye una vista web estratégica combinando payload global y blueprints | `global_report_payload.json` + blueprints de torres | `working/<client>/presentation/index.html` | la capa visual web queda fuera de sincronía con la verdad canónica |

### Particularidad de este renderer

No actúa como simple conversor de un único payload: compone una vista híbrida a partir de la capa global y de los blueprints disponibles. Eso lo hace útil para storytelling visual, pero también más sensible a drift entre capas.

## 5. Dependencias estructurales que conviene vigilar

| Dependencia | Por qué importa |
|---|---|
| blueprints por torre -> annex | es la protección principal contra split-brain |
| blueprints por torre -> global builder | la capa global ya depende de la verdad top-down |
| payload global -> commercial refiner | la capa comercial reutiliza y reinterpreta la agenda ejecutiva |
| blueprints por torre -> commercial refiner | evita una propuesta comercial sin anclaje técnico |
| payloads -> renderers | los DOCX/HTML no deben ser nunca la fuente de verdad |

## 6. Puntos frágiles reales del sistema

1. **Dependencia de Vertex / ADK en módulos de generación y refinado**  
   Si la autenticación o el entorno IA fallan, se cae la parte más valiosa del flujo.

2. **Convivencia de flujo moderno y fallback legacy**  
   `build_global_report_payload.py` aún tolera artefactos antiguos. Es útil operativamente, pero introduce complejidad y riesgo de interpretación híbrida.

3. **Renderers con capacidad de normalización**  
   Son necesarios para robustez, pero si asumen demasiada lógica pueden ocultar desviaciones del contrato.

4. **Acoplamiento indirecto entre capas**  
   El blueprint manda, pero varias capas reutilizan datos o contextos derivados. Cuando eso no se documenta, el sistema parece más lineal de lo que realmente es.

## 7. Regla práctica para futuras decisiones

Si un cambio afecta a un módulo crítico, la revisión debería responder siempre a estas cuatro preguntas:

1. ¿cambia la **fuente de verdad** o solo la presentación?
2. ¿rompe algún **payload contrato**?
3. ¿afecta a una capa que **deriva** de otra ya existente?
4. ¿altera la **lectura empresarial** del sistema o solo su implementación técnica?

Ese filtro ayuda a decidir si el cambio pertenece a arquitectura, contratos, operaciones o presentación.
