---
status: Verified
owner: docs-governance
source_of_truth:
- ../../src/assessment_engine/domain/schemas/blueprint.py
- ../../src/assessment_engine/domain/schemas/annex_synthesis.py
- ../../src/assessment_engine/domain/schemas/global_report.py
- ../../src/assessment_engine/domain/schemas/commercial.py
- ../../src/assessment_engine/application/run_tower_blueprint_engine.py
- ../../src/assessment_engine/application/run_executive_annex_synthesizer.py
- ../../src/assessment_engine/application/build_global_report_payload.py
- ../../src/assessment_engine/application/run_executive_refiner.py
- ../../src/assessment_engine/application/run_commercial_refiner.py
- ../../src/assessment_engine/adapters/render_tower_blueprint.py
- ../../src/assessment_engine/adapters/render_tower_annex_from_template.py
- ../../src/assessment_engine/adapters/render_global_report_from_template.py
- ../../src/assessment_engine/adapters/render_commercial_report.py
- ../../src/assessment_engine/adapters/render_web_presentation.py
- ./payload-render-boundaries.md
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: schema
---

# Artifact contracts

Este documento complementa a [`payload-render-boundaries.md`](payload-render-boundaries.md) al definir la semántica operativa y de negocio de los artefactos de datos en el ciclo de vida del motor: trazabilidad de origen (producción), dependencias de consumo y criterios de validación de compuertas de calidad (*quality gates*).

## Criterio de Identificación de Artefactos Críticos

Todo artefacto de datos catalogado dentro del motor no constituye un mero residuo de salida; debe caracterizarse determinísticamente bajo cuatro dimensiones:

1.  **Origen (Productor):** Entidad o módulo que genera y firma el artefacto.
2.  **Contenido Semántico (Verdad):** Datos y contratos estructurados que valida y encapsula.
3.  **Destino (Consumidor):** Etapas subsecuentes de la tubería (*pipeline*) que dependen de su presencia.
4.  **Impacto en el Negocio (Riesgo):** Vulnerabilidades operacionales o lógicas que emergen en caso de ausencia o deriva contractual.

## Mapa principal de contratos

| Artefacto | Productor principal | Consumidor principal | Rol empresarial | Si falta o deriva |
|---|---|---|---|---|
| `case_input.json` | módulos de preparación de torre | scoring, findings, engine | Delimitación de contexto de la organización | La torre nace con contexto pobre o ambiguo |
| `evidence_ledger.json` | módulos de preparación de torre | findings, auditoría, soporte | Deja trazabilidad de evidencias | Pérdida de trazabilidad de origen y vulnerabilidad en auditoría |
| `scoring_output.json` | scoring por torre | blueprint, annex, soporte | Parámetros cuantitativos de evaluación | Desalineación entre el análisis prosa y los umbrales cualitativos |
| `findings.json` | análisis por torre | blueprint y soporte editorial | Concentra hallazgos estructurados | Degradación del detalle en la especificación técnica |
| `benchmarks_snapshot.json` | `agentic_benchmarker.py` (RAGE) | `run_tower_blueprint_engine.py`, web | Evidencias y benchmarks fácticos y reguladores verificados | Pérdida de fundamentación científica y retroceso a notas de reserva sin trazabilidad |
| `blueprint_<tower>_payload.json` | `run_tower_blueprint_engine.py` | annex, global builder, render blueprint, web | Fuente única de verdad de la torre tecnológica | Inconsistencia lógica y contradicción narrativa en la síntesis consolidada |
| `approved_annex_<tower>.template_payload.json` | `run_executive_annex_synthesizer.py` | render annex | Síntesis de negocio y recomendaciones operativas de la torre | Degradación en la comunicación técnica con la dirección del cliente |
| `global_report_payload.json` | `build_global_report_payload.py` + `run_executive_refiner.py` | render global, comercial, web | Síntesis directiva estratégica consolidada | Disrupción en la gobernanza y pérdida de alineación estratégica |
| `commercial_report_payload.json` | `run_commercial_refiner.py` | render comercial | Definición de palancas y priorización de inversión comercial | Degradación en el alineamiento estratégico de la cuenta |
| `Blueprint_Transformacion_*.docx` | render blueprint | operario de cuenta / cliente final | Documento técnico de transformación | Archivo de salida no modificable; prohibido su consumo por automatizaciones |
| `annex_*.docx` | render annex | operario de cuenta / cliente final | Entregable ejecutivo por torre | Capa de presentación; no debe alterar el modelo de datos canónico |
| `Informe_Ejecutivo_Consolidado_*.docx` | render global | operario de cuenta / cliente final | Entregable ejecutivo consolidado | Degrada la comunicación con dirección |
| `Account_Action_Plan_*.docx` | render comercial | operario de cuenta / cliente final | Entregable comercial interno | Baja utilidad para cuenta y preventa |
| `presentation/index.html` | render web | operario de cuenta / cliente final | Soporte visual y storytelling | La narrativa visual queda desalineada |

## Qué contratos mandan de verdad

### Contratos de Telemetría y Entrada
- `case_input.json`
- `evidence_ledger.json`
- `scoring_output.json`
- `findings.json`
- `benchmarks_snapshot.json`

Constituyen el cimiento empírico del diagnóstico. Garantizan explicabilidad, trazabilidad estructural y defendibilidad técnica ante auditorías.

### Contratos de Síntesis Canónica
- `blueprint_<tower>_payload.json`
- `global_report_payload.json`
- `commercial_report_payload.json`

Modelos definitivos que gobiernan el estado del diagnóstico. Representan la verdad de negocio consolidada.

### Artefactos de Presentación Derivada
- `approved_annex_<tower>.template_payload.json`
- DOCX por torre/global/comercial
- `presentation/index.html`

Canales de transmisión de información estratégica. Su única función es proyectar el modelo de datos sin alterar la verdad del sistema.

## Qué debe comprobar cada capa antes de avanzar

| Etapa | Señal mínima de salida sana |
|---|---|
| Torre base | Presencia de artefactos basales de preparación |
| Blueprint | Presencia y consistencia de `blueprint_payload` |
| Annex | Presencia de `approved_annex_payload` con herencia íntegra |
| Global | Agregación sin pérdidas de blueprints de torre activos |
| Comercial | Alineación de objetivos de cuenta con el payload de síntesis global |
| Web | Presentación web congruente con el estado del mapa maestro |

## Contratos Detallados

Para una descripción exhaustiva de los campos de los contratos principales, consulte los siguientes documentos:

- [`tower_blueprint_payload.md`](./tower_blueprint_payload.md): Define la estructura del artefacto `blueprint_payload`, la fuente de verdad de cada torre.
- [`tower_annex_payload.md`](./tower_annex_payload.md): Define la estructura del `annex_payload`, la síntesis ejecutiva para los informes de anexo.

## Reglas de interpretación si hay conflicto

1. Si un DOCX contradice a un payload, **manda el payload**.
2. Si un payload derivado contradice a su fuente inmediata, **manda la fuente anterior**.
3. Si un renderer necesita demasiada normalización, el problema real suele estar antes.
4. Si un artefacto existe pero no es consumible por la siguiente capa, el contrato está roto aunque el archivo esté presente.

## Riesgos contractuales visibles hoy

1.  **Flexibilidad excesiva de carga de payloads:** El uso de `robust_load_payload(...)` mitiga fallos en ejecución, pero corre el riesgo de enmascarar derivas frente a la definición estricta de esquemas Pydantic.
2.  **Ausencia de validador de esquema explícito en capa web:** `render_web_presentation.py` procesa los datos basándose en contratos implícitos, careciendo de un esquema Pydantic de salida dedicado como en los reportes global y comercial.
3.  **Convivencia de arquitecturas (Transición Top-Down / Bottom-Up):** La existencia de lógicas heredadas en coexistencia con el flujo moderno blueprint-first expone al sistema a combinaciones híbridas.

## Qué significa “contrato cumplido”

Un contrato se certifica como cumplido cuando:

1.  **Integridad Física:** Existencia verificada del artefacto en la ruta determinista especificada por el entorno.
2.  **Compatibilidad Estructural:** Validación sintáctica y semántica exitosa frente al esquema de Pydantic correspondiente.
3.  **Transparencia de Consumo:** El consumidor subsiguiente ingiere el payload directamente sin requerir normalizaciones excepcionales de datos.
4.  **Coherencia Narrativa:** Alineación de contenido técnica y cualitativamente congruente con la etapa que le precede.

## Uso recomendado de este documento

Úsalo cuando necesites decidir:

- si una incidencia es de **producción de artefacto** o de **presentación**;
- qué archivo revisar primero en una cadena rota;
- cuál es la **fuente de verdad** que manda en cada nivel;
- qué pieza debe validarse antes de promover una evolución del sistema.
