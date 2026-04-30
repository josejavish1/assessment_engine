# Documentación del Proyecto: Assessment Engine

> **Estado documental:** colección heredada en transición.
>
> Esta carpeta sigue siendo útil como referencia, pero **ya no debe tratarse como el contenedor estratégico principal**. La entrada canónica actual para la documentación del proyecto está en [`../../README.md`](../../README.md) y la política central en [`../../ai/documentation-governance.md`](../../ai/documentation-governance.md).
>
> **Nota:** Para una visión completa de la arquitectura del sistema, el flujo de datos y los principios de diseño, comience por la capa canónica en [`../../architecture/README.md`](../../architecture/README.md) y use esta carpeta solo como referencia heredada o índice técnico complementario.
>
> ### **[&#128221; Ver la capa canónica de arquitectura](../../architecture/README.md)**


## 1. Visión General del Proyecto

El `assessment-engine` es una "fábrica" de generación de documentos diseñada para producir entregables de assessment tecnológico de nivel B2B. Utiliza un pipeline orquestado por Python y asistido por agentes de Inteligencia Artificial (IA) para transformar datos brutos de evaluaciones en una serie de informes coherentes y de alto valor, desde análisis técnicos profundos hasta resúmenes estratégicos para la alta dirección.

## 2. Principios de Arquitectura

-   **Flujo "Top-Down":** Los documentos de alto nivel se derivan de documentos más detallados para garantizar la consistencia.
-   **"Contract-First":** La comunicación entre etapas se realiza a través de `payloads` con esquemas Pydantic estrictos.
-   **Orquestación por Python:** El flujo de control es manejado por scripts de Python, mientras que la IA actúa como un "operario" especializado.
-   **Arquitectura Orientada a Servicios:** Además de los pipelines, el motor expone sus capacidades a través de un servidor de herramientas (`mcp_server.py`), permitiendo una orquestación externa por parte de otros sistemas de agentes.

## 3. Flujo de Trabajo y Orquestadores

-   **`run_tower_pipeline.py` (Orquestador Principal de Torre):** El director de orquesta para analizar una torre tecnológica individual. Define el flujo de trabajo "Top-Down" moderno.
    -   [Ver documentación de `run_tower_pipeline.py`](./run_tower_pipeline.md)
-   **`run_global_pipeline.py` (Orquestador Global):** Consolida los resultados de todas las torres para generar el informe final para el CIO.
    -   [Ver documentación de `run_global_pipeline.py`](./run_global_pipeline.md)
-   **`mcp_server.py` (Servidor de Herramientas):** Expone las funcionalidades del motor para que puedan ser llamadas por un agente de IA supervisor externo.
    -   [Ver documentación de `mcp_server.py`](./mcp_server.md)
-   **`run_section_pipeline.py` (Orquestador Legacy):** [ARCHIVADO] Representa la arquitectura anterior, donde las secciones se generaban de forma aislada.
    -   [Ver documentación de `run_section_pipeline.py`](./_legacy/run_section_pipeline.md)

## 4. Scripts de Preparación y Lógica

-   **`build_case_input.py` (Ingesta de Datos):** Consolida los ficheros en crudo en el `case_input.json` inicial.
    -   [Ver documentación de `build_case_input.py`](./build_case_input.md)
-   **`build_evidence_ledger.py` (Contextualizador de Evidencias):** Procesa los datos en crudo y los convierte en un "dossier de pruebas" estructurado.
    -   [Ver documentación de `build_evidence_ledger.py`](./build_evidence_ledger.md)
-   **`run_scoring.py` (Motor de Cálculo):** Script determinista que calcula todas las puntuaciones de madurez.
    -   [Ver documentación de `run_scoring.py`](./run_scoring.md)
-   **`run_evidence_analyst.py` (Analista Automático):** Genera un borrador de "hallazgos" basado en reglas a partir de las evidencias.
    -   [Ver documentación de `run_evidence_analyst.py`](./run_evidence_analyst.md)

## 5. Scripts de Presentación

-   **`render_global_report_from_template.py` (Renderizador DOCX Global):** Genera el informe `.docx` final para el CIO.
    -   [Ver documentación de `render_global_report_from_template.py`](./render_global_report_from_template.md)
-   **`render_web_presentation.py` (Dashboard HTML):** Genera un dashboard estratégico interactivo y autocontenido.
    -   [Ver documentación de `render_web_presentation.py`](./render_web_presentation.md)
-   **`generate_tower_radar_chart.py` (Generador de Gráficos):** Crea las visualizaciones de datos, como los gráficos de radar.
    -   [Ver documentación de `generate_tower_radar_chart.py`](./generate_tower_radar_chart.md)

## 6. Prompts (El "Código Fuente" de la IA)

Los prompts definen la "personalidad", las reglas y las tareas de cada agente de IA.
-   [Ver documentación de `prompts_intelligence_prompts.py`](./prompts_intelligence_prompts.md)
-   [Ver documentación de `prompts_blueprint_prompts.py`](./prompts_blueprint_prompts.md)
-   ... (y el resto de la documentación de prompts).

## 7. Índice Completo de Ficheros Documentados
-   [`ai_client.md`](./lib_ai_client.md)
-   [`bootstrap_bootstrap_tower_from_matrix.md`](./bootstrap_bootstrap_tower_from_matrix.md)
-   [`build_case_input.md`](./build_case_input.md)
-   [`build_evidence_ledger.md`](./build_evidence_ledger.md)
-   [`build_global_report_payload.md`](./build_global_report_payload.md)
-   [`build_tower_annex_template_payload.md`](./build_tower_annex_template_payload.md)
-   [`check_docx_unresolved_placeholders.md`](./tools_check_docx_unresolved_placeholders.md)
-   [`config_loader.md`](./lib_config_loader.md)
-   [`contract_utils.md`](./lib_contract_utils.md)
-   [`editorial_autofix.md`](./lib_editorial_autofix.md)
-   [`generate_smoke_data.md`](./tools_generate_smoke_data.md)
-   [`generate_tower_radar_chart.md`](./generate_tower_radar_chart.md)
-   [`mcp_server.md`](./mcp_server.md)
-   [`prompts_blueprint_prompts.md`](./prompts_blueprint_prompts.md)
-   [`prompts_commercial_prompts.md`](./prompts_commercial_prompts.md)
-   [`prompts_conclusion_prompts.md`](./prompts_conclusion_prompts.md)
-   [`prompts_gap_prompts.md`](./prompts_gap_prompts.md)
-   [`prompts_global_prompts.md`](./prompts_global_prompts.md)
-   [`prompts_intelligence_prompts.md`](./prompts_intelligence_prompts.md)
-   [`prompts_section_prompts.md`](./prompts_section_prompts.md)
-   [`prompts_tobe_prompts.md`](./prompts_tobe_prompts.md)
-   [`prompts_todo_prompts.md`](./prompts_todo_prompts.md)
-   [`render_commercial_report.md`](./render_commercial_report.md)
-   [`render_global_report_from_template.md`](./render_global_report_from_template.md)
-   [`render_tower_annex_from_template.md`](./render_tower_annex_from_template.md)
-   [`render_tower_blueprint.md`](./render_tower_blueprint.md)
-   [`render_web_presentation.md`](./render_web_presentation.md)
-   [`review_resilience.md`](./lib_review_resilience.md)
-   [`run_commercial_refiner.md`](./run_commercial_refiner.md)
-   [`run_evidence_analyst.md`](./run_evidence_analyst.md)
-   [`run_executive_annex_synthesizer.md`](./run_executive_annex_synthesizer.md)
-   [`run_global_pipeline.md`](./run_global_pipeline.md)
-   [`run_scoring.md`](./run_scoring.md)
-   [`run_tower_blueprint_engine.md`](./run_tower_blueprint_engine.md)
-   [`run_tower_pipeline.md`](./run_tower_pipeline.md)
-   [`runtime_env.md`](./lib_runtime_env.md)
-   [`runtime_paths.md`](./lib_runtime_paths.md)
-   [`schemas_annex_synthesis.md`](./schemas_annex_synthesis.md)
-   ... (y el resto del índice)

*Nota: He acortado algunas secciones para mostrar los cambios, el fichero final será completo.*
