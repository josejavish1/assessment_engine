---
status: Verified
owner: docs-governance
source_of_truth:
- ../../src/assessment_engine/domain/schemas/annex_synthesis.py
- ../../src/assessment_engine/domain/schemas/blueprint.py
- ../../src/assessment_engine/domain/schemas/global_report.py
- ../../src/assessment_engine/domain/schemas/commercial.py
- ../../src/assessment_engine/infrastructure/contract_utils.py
- ../../src/assessment_engine/adapters/render_tower_annex_from_template.py
- ../../src/assessment_engine/adapters/render_tower_blueprint.py
- ../../src/assessment_engine/adapters/render_global_report_from_template.py
- ../../src/assessment_engine/adapters/render_commercial_report.py
- ../../src/assessment_engine/adapters/render_web_presentation.py
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: schema
---

# Payload, schema and renderer boundaries

Este documento establece y delimita formalmente las fronteras técnicas y de responsabilidad entre:

1.  **Payloads JSON** que expresan la verdad estructurada;
2.  **Esquemas Pydantic** que gobiernan y tipan esa verdad;
3.  **Renderizadores** que convierten esa verdad en archivos de presentación (DOCX o HTML).

## Regla principal

Los módulos de renderizado e interfaces de presentación no constituyen fuentes de verdad del sistema. Su alcance operacional se limita estrictamente a:

-   Cargar el payload estructurado;
-   Validarlo, normalizarlo y asegurar su conformidad semántica;
-   Compilar y formatear los datos bajo reglas de diseño estético para el entregable final.

La lógica de negocio y la validación de interfaces deben vivir de forma desacoplada y precedente, en la definición de payloads y esquemas de validación.

## Esquemas de Rigor de Validación (*Enforcement*)

El rigor en la validación de contratos varía según el canal de renderizado y el estado de transición del componente. Se definen tres niveles de tolerancia operativa:

| Nivel | Comportamiento real | Casos de uso |
|---|---|---|
| **Estricto** | Invocación obligatoria de `model_validate(...)` o similar; interrupción inmediata del flujo (*transaction abort*) ante inconsistencias sintácticas o de tipado. | `render_tower_blueprint.py`, `render_global_report_from_template.py` |
| **Tolerante** | Validación parcial mediante `model_construct(...)` con registro de desviaciones (*warning logs*), permitiendo la continuidad transitoria para compatibilidad con datos heredados. | Rutas heredadas o de compatibilidad explícita aún no endurecidas. |
| **Implícito** | Consumo y mapeo dinámico del payload JSON sin instanciación formal de esquemas Pydantic en la capa de presentación. | `render_web_presentation.py` |

Por consiguiente, el esquema Pydantic representa la definición de interfaz técnica objetivo, si bien ciertos presentadores admiten estados intermedios por requerimientos de retrocompatibilidad.

## Mapa principal de acoplamiento

| Capa | Payload | Esquema | Consumidor principal | Salida de presentación |
|---|---|---|---|---|
| Torre ejecutiva | `approved_annex_<tower>.template_payload.json` | `AnnexPayload` | `render_tower_annex_from_template.py` | `annex_<tower>_<client>_final.docx` |
| Torre estratégica | `blueprint_<tower>_payload.json` | `BlueprintPayload` | `render_tower_blueprint.py` | `Blueprint_Transformacion_<TOWER>_<client>.docx` |
| Global ejecutiva | `global_report_payload.json` | `GlobalReportPayload` | `render_global_report_from_template.py` | `Informe_Ejecutivo_Consolidado_<client>.docx` |
| Comercial interna | `commercial_report_payload.json` | `CommercialPayload` | `render_commercial_report.py` | `Account_Action_Plan_<client>.docx` |
| Dashboard web | `global_report_payload.json` + blueprints de torres | Sin esquema único en capa de render | `render_web_presentation.py` | `presentation/index.html` |

## Contratos de interfaz por payload

### 1. Annex payload

-   **Archivo:** `approved_annex_<tower>.template_payload.json`
-   **Esquema:** `AnnexPayload`
-   **Render principal:** `render_tower_annex_from_template.py`

Características de la frontera:
-   El sintetizador del anexo consume un subconjunto estructurado (*handover*) derivado del blueprint, el cual incluye puntuaciones cuantitativas, riesgos, directrices de inversión e iniciativas clave.
-   Métricas globales, alineaciones de madurez, brechas y propuestas críticas se computan determinísticamente a partir del blueprint antes del renderizado.
-   El renderizador carga el JSON con `robust_load_payload(..., AnnexPayload, "Annex", mode="strict")`.
-   La compilación OpenXML del anexo emplea por defecto la variante de diseño semántico, dejando el modo de diseño heredado solo como opción de compatibilidad manual.
-   El linter interno aplica `normalize_annex_payload(...)` para uniformizar estructuras de datos.

Conclusión:
-   `AnnexPayload` rige el contrato estructural estricto de la etapa.
-   La síntesis asistida por LLM aporta encuadre y lenguaje directivo, pero tiene estrictamente prohibido redefinir los hechos lógicos y técnicos heredados de la capa de blueprint.
-   El renderizador rechaza de forma determinista payloads inválidos.

### 2. Blueprint payload

-   **Archivo:** `blueprint_<tower>_payload.json`
-   **Esquema:** `BlueprintPayload`
-   **Render principal:** `render_tower_blueprint.py`

Características de la frontera:
-   El renderizador carga el JSON y aplica la función `normalize_blueprint_payload_dict(...)`.
-   Posteriormente, valida la integridad del payload contra el esquema `BlueprintPayload.model_validate(...)`.
-   La presentación puede enriquecerse agregando datos de contexto desde `client_intelligence.json` y `approved_annex_<tower>.template_payload.json`.

Conclusión:
-   El modelo de datos del blueprint tecnológico se consolida como la fuente de verdad primaria.
-   La agregación de contexto adicional asiste al formateo, pero en ningún caso altera la definición canónica del blueprint.

### 3. Global report payload

-   **Archivo:** `global_report_payload.json`
-   **Esquema:** `GlobalReportPayload`
-   **Render principal:** `render_global_report_from_template.py`

Características de la frontera:
-   Validación estricta sin tolerancia de fallos a través de `GlobalReportPayload.model_validate(...)`.
-   Consumo de secciones de síntesis previamente consolidadas y refinadas (`executive_summary`, `burning_platform`, `tower_bottom_lines`, `target_vision`, `execution_roadmap`, `executive_decisions`).

Conclusión:
-   Representa la compuerta de calidad de mayor rigidez del pipeline.
-   El renderizador procesa el payload presumiendo coherencia directiva absoluta previa.

### 4. Commercial payload

-   **Archivo:** `commercial_report_payload.json`
-   **Esquema:** `CommercialPayload`
-   **Render principal:** `render_commercial_report.py`

Características de la frontera:
-   Carga estricta mediante `robust_load_payload(..., CommercialPayload, "Commercial Account Plan", mode="strict")`.
-   Estructuración semántica del plan de cuenta (`commercial_summary`, `gtm_strategy`, `stakeholder_matrix`, `opportunities_pipeline`, `proactive_proposals`, `intelligence_dossier`).

Conclusión:
-   El renderizador comercial opera bajo un contrato explícito e inmutable, limitándose a proyectar la estrategia de cuenta consolidada en el payload.

### 5. Dashboard web

-   **Entrada principal:** `global_report_payload.json`
-   **Entrada secundaria:** `blueprint_<tower>_payload.json` por torre activa
-   **Render principal:** `render_web_presentation.py`

Características de la frontera:
-   No realiza validación estructural de esquemas mediante Pydantic en tiempo de renderizado.
-   Carece actualmente de una clase Pydantic de salida dedicada en la capa de renderizado.
-   Compone dinámicamente un grafo de datos intermedio (`nexus_data`) que amalgama la estrategia global, el mapa térmico de madurez, el cronograma estratégico de ejecución y la telemetría táctica de las torres.

Conclusión:
-   La capa web constituye una vista derivada compuesta.
-   Su interfaz técnica permanece implícita en la lógica de compilación del renderizador; debe considerarse estrictamente como capa de presentación agregada y no como origen de datos.

## Matriz de Gobierno de Renders

| Renderizador | Payload rector | Directriz técnica |
|---|---|---|
| `render_tower_annex_from_template.py` | `AnnexPayload` | Formatea el anexo ejecutivo; admite normalizaciones semánticas no destructivas. |
| `render_tower_blueprint.py` | `BlueprintPayload` | Proyecta el blueprint canónico; admite agregación pasiva de contexto. |
| `render_global_report_from_template.py` | `GlobalReportPayload` | Validación de esquema al 100% libre de fallos (*strict parsing*). |
| `render_commercial_report.py` | `CommercialPayload` | Consume la síntesis del plan de cuenta cerrado sin alteración lógica. |
| `render_web_presentation.py` | Vista compuesta (Global + Blueprints) | Agregador dinámico de vistas; prohibido su uso como fuente de verdad. |

## Reglas de Asignación de Responsabilidades

### Competencias del Payload/Esquema
-   Definición estructural del contenido y cardinalidad de datos.
-   Tipado estricto y nombres de propiedades de transporte.
-   Gobernanza de metadatos de linaje, firma y versión.

### Competencias del Renderizador
-   Diseño estético y de interfaz de usuario (*layout*, espaciados).
-   Estructuración tipográfica (bloques, viñetas, tablas de datos).
-   Ensamblado y compilación de binarios (OpenXML, HTML semántico).

### Decisiones Prohibidas en el Renderizador
-   Determinación de lógicas cuantitativas o algoritmos de puntuación (*scoring*).
-   Resolución de políticas de madurez (`score -> band`).
-   Significado conceptual de los campos o interfaces de dominio.

La resolución de métricas y traducción semántica (`score -> band`) debe ocurrir de forma determinista previa a la conformación del payload, consumiendo la política de madurez compartida de la plataforma. Si un renderizador detecta una propiedad faltante, debe resolverla invocando las utilidades compartidas del dominio, prohibiéndose la redefinición lógica local.

## Desviaciones y Desafíos de Alineación

1.  **Persistencia de normalizaciones transitorias:** Ciertos consumidores finales aplican transformaciones estructurales para subsanar vacíos o inconsistencias de datos heredados.
2.  **Ausencia de validador de esquema explícito en capa web:** `render_web_presentation.py` procesa los datos basándose en contratos implícitos, careciendo de un esquema de salida validado por un modelo formal.
3.  **Transición de Arquitectura:** El soporte residual de rutas de compatibilidad tolerante convive con la arquitectura estrictamente tipada del motor modernizado.

Estas tensiones no invalidan el diseño canónico, pero constituyen el backlog de refactorización necesario para blindar completamente la frontera frente a capas estéticas.

## Conclusiones de Auditoría

1.  Los esquemas `AnnexPayload`, `BlueprintPayload`, `GlobalReportPayload` y `CommercialPayload` se encuentran definidos y plenamente alineados con los payloads descritos.
2.  La cobertura de pruebas unitarias (`tests/test_contract_handover.py` y `tests/test_payload_validation.py`) certifica la correspondencia estructural de las interfaces técnicas.
3.  La suite de humo (*smoke-tests*) valida exitosamente la compilación y consistencia lógica de los artefactos.

## Protocolo ante Cambios en Interfaces

Ante cualquier modificación de contratos o interfaces estéticas:
1.  **Esquema Primero (Contract-First):** Modificar y validar la clase Pydantic correspondiente en `src/assessment_engine/domain/schemas/`.
2.  **Origen (Productor):** Actualizar el script de preparación u orquestador que produce el payload de datos.
3.  **Destino (Consumidor):** Adaptar y certificar las rutinas de compilación en el renderizador.
4.  **Consistencia de Gobierno:** Actualizar este documento y la traza correspondiente en `docs/documentation-map.yaml`.
