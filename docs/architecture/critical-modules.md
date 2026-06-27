---
status: Verified
owner: docs-governance
source_of_truth:
- ../../src/assessment_engine/application/run_tower_pipeline.py
- ../../src/assessment_engine/application/run_tower_blueprint_engine.py
- ../../src/assessment_engine/application/run_executive_annex_synthesizer.py
- ../../src/assessment_engine/adapters/render_tower_blueprint.py
- ../../src/assessment_engine/adapters/render_tower_annex_from_template.py
- ../../src/assessment_engine/application/run_global_pipeline.py
- ../../src/assessment_engine/application/build_global_report_payload.py
- ../../src/assessment_engine/application/run_executive_refiner.py
- ../../src/assessment_engine/adapters/render_global_report_from_template.py
- ../../src/assessment_engine/application/run_commercial_pipeline.py
- ../../src/assessment_engine/application/run_commercial_refiner.py
- ../../src/assessment_engine/adapters/render_commercial_report.py
- ../../src/assessment_engine/adapters/render_web_presentation.py
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
---
# Critical modules map

Este documento establece y cataloga el mapa de responsabilidades, flujos de datos e interrupciones operativas de los módulos de software críticos del motor. Su propósito es definir con precisión técnica:

1.  **Competencia Técnica:** El rol y alcance del componente en el flujo del negocio.
2.  **Interfaces de Entrada/Salida:** Definición de los contratos de datos que gobierna.
3.  **Criticidad Arquitectónica:** Su función e impacto en el acoplamiento global del sistema.
4.  **Impacto de Desviación (Riesgo):** Las interrupciones, estados parciales o inconsistencias lógicas que emergen en caso de fallos operacionales o deriva contractual.

## Taxonomía de Módulos

| Tipo | Competencia |
|---|---|
| **Orchestrator** | Gobierno de la secuencia de ejecución, dependencias topológicas e integridad transaccional. |
| **Engine / Refiner** | Síntesis, transformación semántica y validación de las invariantes lógicas del dominio. |
| **Builder** | Consolidación, agregación multidimensional y normalización de payloads intermedios. |
| **Renderer** | Compilación y mapeo de datos estructurados de payloads en canales de presentación física. |

---

## 1. Núcleo de Ejecución por Torre

| Módulo | Tipo | Responsabilidad principal | Entrada Dominante | Salida Dominante | Riesgo si falla |
|---|---|---|---|---|---|
| `run_tower_pipeline.py` | Orchestrator | Orquesta la ejecución de la torre; gestiona aprovisionamiento de entorno, reanudación transaccional y temporizadores de llamadas LLM. | Respuestas del cliente y parámetros de ejecución. | Integración de artefactos en `working/<client>/<tower>/`. | Interrupción del pipeline; la torre tecnológica queda en estado parcial o huérfana de artefactos. |
| `agentic_benchmarker.py` | Engine | Realiza la auditoría en vivo (RAGE), localizando evidencias reguladoras mediante OSINT y umbrales matemáticos. | Rúbricas declarativas y datos de la torre. | `benchmarks_snapshot.json` y PDFs en `evidence_cache/`. | Sesgo de madurez o falta de fundamento legal en la justificación. |
| `run_tower_blueprint_engine.py` | Engine | Sintetiza y consolida el **activo canónico por torre (Blueprint)** a partir del caso, scoring y evidencias. | `case_input.json`, definición metodológica y `client_intelligence.json`. | `blueprint_<tower>_payload.json` (Fuente única de verdad). | Pérdida absoluta de la fuente única de verdad para el dominio tecnológico. |
| `run_executive_annex_synthesizer.py` | Engine | Deriva la síntesis de negocio a partir de la especificación técnica del blueprint, forzando invariantes y metas cualitativas. | `blueprint_<tower>_payload.json`. | `approved_annex_<tower>.template_payload.json`. | Resurgimiento de contradicciones y fragmentación narrativa (*split-brain*) en la capa ejecutiva. |
| `render_tower_blueprint.py` | Renderer | Compila el blueprint estructurado en una especificación OpenXML de arquitectura legible para equipos técnicos. | Blueprint payload e integraciones contextuales secundarias. | `Blueprint_Transformacion_<tower>_<client>.docx`. | Degradación en la calidad del entregable OpenXML técnico. |
| `render_tower_annex_from_template.py` | Renderer | Proyecta el payload del anexo en un entregable OpenXML directivo, aplicando el formato visual semántico. | Annex payload y plantilla OpenXML base. | `annex_<tower>_<client>_final.docx`. | Degradación de la interfaz de presentación de negocio y pérdida de alineación con el cliente. |

### Fundamentación Estratégica del Bloque

La torre constituye el epicentro de la generación de valor estructural del sistema: la producción del **blueprint**. El resto del andamiaje adyacente tiene como exclusiva función:
-   El aprovisionamiento de datos empíricos de entrada;
-   La extracción formal de aserciones de diagnóstico;
-   La traducción semántica para diferentes audiencias corporativas;
-   La compilación estética en formatos estándar del mercado.

---

## 2. Capa de Consolidación Global

| Módulo | Tipo | Responsabilidad principal | Entrada Dominante | Salida Dominante | Riesgo si falla |
|---|---|---|---|---|---|
| `run_global_pipeline.py` | Orchestrator | Orquesta la consolidación global extremo a extremo. | Catálogo de directorios en `working/<client>/` por torre. | Payload global consolidado y reporte directivo OpenXML. | Pérdida de coherencia agregada y degradación de la visibilidad directiva de la cuenta. |
| `build_global_report_payload.py` | Builder | Agrega el catálogo técnico de torres, privilegiando los payloads canónicos estructurados v3. | Blueprints por torre tecnológica activa. | `global_report_payload.json` inicial. | Agregación inconsistente o híbrida sin aserciones claras de fallo. |
| `run_executive_refiner.py` | Engine | Refina y editorializa las secciones transversales del payload global consolidado bajo directrices directivas. | `global_report_payload.json`. | `global_report_payload.json` refinado *in-place*. | El entregable global adquiere un carácter técnico pero carece de palancas accionables de dirección. |
| `render_global_report_from_template.py` | Renderer | Compila y mapea el payload de síntesis global refinado en el template OpenXML corporativo. | Payload global refinado y plantilla OpenXML consolidada. | `Informe_Ejecutivo_Consolidado_<client>.docx`. | Vulneración de la credibilidad y desalineación con la dirección ejecutiva del cliente. |

### Fundamentación Estratégica del Bloque

En esta capa de elevación, el sistema trasciende el análisis de dominios tecnológicos aislados para formalizar la **agenda de transformación estratégica del cliente**. El builder y el refinador global no ejecutan una mera sumatoria aritmética de iniciativas: seleccionan, priorizan, ponderan y editorializan los hallazgos bajo una visión corporativa unificada.

---

## 3. Capa de Activación Comercial

| Módulo | Tipo | Responsabilidad principal | Entrada Dominante | Salida Dominante | Riesgo si falla |
|---|---|---|---|---|---|
| `run_commercial_pipeline.py` | Orchestrator | Gobierna el flujo comercial interno a partir del estado de la síntesis ejecutiva global. | `global_report_payload.json` refinado. | Payload de cuenta comercial y Account Action Plan. | Pérdida de oportunidades de preventa y desalineación de la estrategia comercial de la cuenta. |
| `run_commercial_refiner.py` | Engine | Correlaciona la síntesis estratégica global con el catálogo de proyectos tácticos de las torres, formulando propuestas de inversión proactivas. | Payload global y blueprints de torres activas. | `commercial_report_payload.json`. | Desacoplamiento de las propuestas comerciales y de inversión de la realidad arquitectónica del diagnóstico. |
| `render_commercial_report.py` | Renderer | Proyecta la estrategia y planes de inversión de la cuenta en el entregable OpenXML correspondiente. | Payload comercial y plantilla OpenXML de cuenta. | `Account_Action_Plan_<client>.docx`. | Inutilidad del activo de cuenta para equipos de preventa, ingeniería de preventa y entrega (*delivery*). |

### Fundamentación Estratégica del Bloque

A diferencia de la capa ejecutiva global, la capa comercial no tiene como propósito la comunicación hacia dirección, sino la **movilización de la cuenta y estructuración de la cartera de oportunidades**. El refinador comercial unifica el relato estratégico global con la telemetría táctica de cada torre para formular un pipeline de iniciativas de inversión debidamente dimensionado y justificado técnicamente.

---

## 4. Capa de Visualización Web

| Módulo | Tipo | Responsabilidad principal | Entrada Dominante | Salida Dominante | Riesgo si falla |
|---|---|---|---|---|---|
| `render_web_presentation.py` | Renderer | Compila una interfaz HTML estratégica interactiva amalgamando el payload global y la telemetría técnica de los blueprints. | `global_report_payload.json` y catálogo de blueprints. | `working/<client>/presentation/index.html`. | Pérdida de sincronía entre el storytelling visual del dashboard y los datos canónicos consolidados en los payloads. |

### Particularidad Operacional

Este componente actúa de forma desacoplada de la jerarquía estándar: no consume una interfaz simplificada unidimensional, sino que compone una vista de síntesis web unificando dinámicamente el reporte global con la telemetría detallada de cada torre activa. Su función es estrictamente de soporte de presentación e interactividad, prohibiéndose su uso como origen de datos para etapas ulteriores.

---

## 5. Acoplamientos Estructurales Críticos

La estabilidad semántica del motor exige la observancia estricta del flujo de herencia y trazabilidad entre las siguientes interfaces técnicas:

```
[ blueprint_payload.json ] (Verdad Primaria por Torre)
    ├──> [ approved_annex_payload.json ] (Handover Directivo) ──> [ render_annex ]
    └──> [ global_report_payload.json ] (Agregador Estratégico)
             ├──> [ commercial_report_payload.json ] (Activación) ──> [ render_commercial ]
             └──> [ render_global ]
```

---

## 6. Zonas de Fragilidad e Interrupción del Flujo

Para asegurar la robustez del sistema en producción, el equipo de ingeniería debe monitorear prioritariamente las siguientes zonas de riesgo:
1.  **Dependencia de APIs Generativas:** Si la conexión, el entorno de llamadas de Vertex AI o el ADK sufren latencias o fallas en la autenticación, se detendrán las etapas de generación y refinamiento del pipeline.
2.  **Transición de Modelos de Datos:** El soporte residual de mecanismos de agregación híbridos con compatibilidad de datos heredados en `build_global_report_payload.py` añade complejidad de interpretación lógicas.
3.  **Límites de Tolerancia en Renderers:** La flexibilidad excepcional de formateo y normalización de datos implementada en renderizadores facilita la robustez visual, pero corre el riesgo de ocultar desalineaciones tempranas frente a los esquemas estrictos de Pydantic.

## 7. Criterios para el Control de Cambios

Cualquier cambio propuesto sobre un módulo catalogado como crítico debe someterse a la evaluación de las siguientes preguntas fundamentales de diseño antes de autorizar su integración:
1.  ¿La mutación altera la **fuente de verdad canónica** o se limita de forma aislada a la capa de presentación?
2.  ¿Se modifica el esquema de tipado o la cardinalidad del **contrato del payload**?
3.  ¿La alteración impacta a un componente que hereda o deriva datos de un módulo de origen precedente?
4.  ¿Se respeta la **semántica y valor de negocio** definido por la arquitectura de datos del sistema?

Esta segmentación determinista garantiza la coherencia técnica del motor y previene el surgimiento de deudas de acoplamiento indeseadas en el repositorio.
