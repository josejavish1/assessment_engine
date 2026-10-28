---
status: Verified
owner: docs-governance
source_of_truth:
- ../../scripts/audit_neurosymbolic_codebase.py
- ../../src/assessment_engine/
last_verified_against: '2026-06-26'
applies_to:
- humans
- ai-agents
doc_type: operational
diataxis: explanation
verification_mode: editorial
---
# Auditoría Neuro-Simbólica de la Base de Código

**Fecha:** Octubre 2026 | **Metodología:** Topología AST (NetworkX) + Trazabilidad Dinámica (`coverage.py`) + Árbitro Cognitivo (`gemini-4-argon`)

## 1. Resumen Ejecutivo de Salud del Código

- **Total de Archivos Auditados:** 177
- **Núcleo Canónico (Vital):** 81 (45.8%)
- **Hojas Activas / Adaptadores:** 85 (48.0%)
- **Módulos Sombra (Duplicados / Candidatos a Fusión):** 3
- **Huérfanos Confirmados (Código Muerto / Purga Segura):** 8

## 2. ⚠️ Huérfanos Confirmados (Blast Radius = 0)

| Archivo | LOC | Cobertura | In-Degree | Razón Técnica de Purga |
| :--- | :---: | :---: | :---: | :--- |
| `src/assessment_engine/application/run_global_synthesizer_tobe.py` | 569 | 0.0% | 0 | Módulo aislado con cero importadores y cero referencias dinámicas que define esquemas inline redundantes fuera de la capa de dominio, evidenciando ser un prototipo abandonado. |
| `src/assessment_engine/application/tools/dynamic_tower_dispatcher.py` | 225 | 0.0% | 0 | Módulo completamente aislado (In-Degree 0, Out-Degree 0, sin cobertura) que intenta importar dinámicamente servicios inexistentes mediante rutas especulativas. |
| `src/assessment_engine/domain/schemas/asis.py` | 47 | 0.0% | 0 | Esquema Pydantic sin importadores activos (In-Degree 0) ni cobertura de pruebas, indicando un modelo de datos obsoleto o no integrado. |
| `src/assessment_engine/domain/schemas/conclusion.py` | 41 | 0.0% | 0 | Modelo de datos aislado con cero dependencias entrantes y sin cobertura de ejecución, constituyendo código muerto en la capa de esquemas. |
| `src/assessment_engine/domain/schemas/gap.py` | 48 | 0.0% | 0 | Esquema de análisis GAP huérfano sin ningún módulo que lo importe directamente ni cobertura en tests. |
| `src/assessment_engine/infrastructure/doctor_agent.py` | 23 | 0.0% | 1 | Clase stub de 23 líneas sin dependencias salientes, sin cobertura de pruebas y con docstrings corruptos autogenerados (diccionario serializado). |
| `src/assessment_engine/infrastructure/policies/archimate.py` | 54 | 0.0% | 0 | Política de entregables ArchiMate sin importadores directos, referencias dinámicas ni cobertura de pruebas que justifiquen su retención. |
| `src/assessment_engine/infrastructure/vendor_intelligence.py` | 223 | 0.0% | 0 | Módulo de síntesis de blueprints de fabricantes sin importadores (In-Degree: 0), sin referencias dinámicas y con 0% de cobertura de pruebas. |

## 3. 👥 Módulos Sombra (Candidatos a Fusión / Refactor)

| Archivo | LOC | Cobertura | In-Degree | Diagnóstico de Fusión |
| :--- | :---: | :---: | :---: | :--- |
| `src/assessment_engine/adapters/compile_asis_docx_from_modules.py` | 2884 | 0.0% | 1 | Monolito procedural heredado de casi 3000 líneas que acopla la manipulación directa de DOCX con la lógica de negocio, habiendo sido reemplazado arquitectónicamente por el pipeline modular basado en AST (payload_to_ast y docx_compiler). |
| `src/assessment_engine/adapters/generate_asis_markdown_modules.py` | 1072 | 0.0% | 0 | Script sin importadores que duplica funciones exactas de limpieza de texto presentes en payload_to_ast.py y pertenece al flujo obsoleto de generación por módulos intermedios en Markdown. |
| `src/assessment_engine/domain/prompts/product_owner_prompts.py` | 162 | 0.0% | 1 | Aunque tiene un importador activo, reimplementa de forma redundante la lógica de carga de archivos YAML de la carpeta 'registry' que ya existe en blueprint_prompts.py. |

## 4. 📋 Inventario Exhaustivo Archivo a Archivo

| Archivo | Veredicto | LOC | Cobertura | In-Deg | Dictamen Funcional |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `src/assessment_engine/adapters/compilers/ast_table_builders.py` | **ACTIVE_LEAF** | 241 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/render_commercial_report.py` | **ACTIVE_LEAF** | 782 | 0.0% | 0 | Punto de entrada CLI y script de renderizado final para reportes comerciales que consume esquemas de dominio validados y utilidades compartidas, justificando su grado de entrada cero. |
| `src/assessment_engine/adapters/render_lineage_portal.py` | **ACTIVE_LEAF** | 138 | 0.0% | 0 | Script autónomo de generación de artefactos estáticos HTML mediante Jinja2 para el portal de linaje, diseñado para ejecutarse como hoja activa del pipeline (evidenciado por la inyección de sys.path). |
| `src/assessment_engine/adapters/render_tower_annex_from_template.py` | **ACTIVE_LEAF** | 856 | 0.0% | 0 | Script adaptador de salida para la generación de documentos DOCX de anexos desde plantillas, invocado como proceso hoja mediante referencias dinámicas (In-Degree: 0, String Refs: 2). |
| `src/assessment_engine/adapters/render_web_presentation.py` | **ACTIVE_LEAF** | 411 | 0.0% | 0 | Adaptador terminal de serialización para la capa de presentación web que consume esquemas validados y es referenciado externamente en el pipeline (In-Degree: 0, String Refs: 2). |
| `src/assessment_engine/application/bootstrap/bootstrap_all_towers.py` | **ACTIVE_LEAF** | 125 | 0.0% | 0 | Punto de entrada CLI (usa argparse) diseñado para orquestar la inicialización masiva y validación de todas las torres del motor. |
| `src/assessment_engine/application/build_evidence_ledger.py` | **ACTIVE_LEAF** | 211 | 0.0% | 0 | Script CLI de aplicación para la construcción del registro de evidencias, ejecutado como tarea independiente del pipeline (In-Degree: 0, String Refs: 3). |
| `src/assessment_engine/application/build_global_report_payload.py` | **ACTIVE_LEAF** | 674 | 0.0% | 0 | Script orquestador de etapa final que consolida el grafo epistémico y las políticas de madurez para generar el payload del reporte global (In-Degree: 0, Out-Degree: 7, String Refs: 2). |
| `src/assessment_engine/application/cli.py` | **ACTIVE_LEAF** | 426 | 0.0% | 0 | Es el punto de entrada principal (CLI) que unifica y orquesta la ejecución de los pipelines desde la consola, por lo que su In-Degree de 0 es arquitectónicamente esperado. |
| `src/assessment_engine/application/export_graph_state.py` | **ACTIVE_LEAF** | 291 | 0.0% | 0 | Actúa como un exportador de estado de borde (DigitalTwinExporter) que consume el grafo epistémico y el orquestador estratégico, siendo invocado dinámicamente mediante referencias de texto. |
| `src/assessment_engine/application/generate_executive_roadmap_image.py` | **ACTIVE_LEAF** | 148 | 0.0% | 0 | Script autónomo de renderizado visual (Gantt vía Matplotlib) diseñado para ejecutarse como subproceso CLI, evidenciado por su función main y sus 2 referencias por string. |
| `src/assessment_engine/application/generate_global_radar_chart.py` | **ACTIVE_LEAF** | 148 | 0.0% | 0 | Utilidad de hoja para la generación de gráficos de radar con Matplotlib invocada dinámicamente por el motor de reportes (3 referencias por string). |
| `src/assessment_engine/application/generate_tower_radar_chart.py` | **ACTIVE_LEAF** | 138 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/run_commercial_pipeline.py` | **ACTIVE_LEAF** | 62 | 0.0% | 0 | Punto de entrada de orquestación para el pipeline comercial que ejecuta fases modulares mediante subprocesos (`run_module_step`). |
| `src/assessment_engine/application/run_commercial_refiner.py` | **ACTIVE_LEAF** | 334 | 0.0% | 0 | Módulo de ejecución multi-agente (ADK/Vertex AI) que no se importa estáticamente porque es invocado como proceso independiente desde `run_commercial_pipeline.py`. |
| `src/assessment_engine/application/run_evidence_analyst.py` | **ACTIVE_LEAF** | 330 | 0.0% | 0 | Script CLI de análisis de evidencias basado en agentes IA, ejecutado dinámicamente como paso de pipeline (3 referencias por string y parser de argumentos propio). |
| `src/assessment_engine/application/run_executive_refiner.py` | **ACTIVE_LEAF** | 282 | 0.0% | 0 | Script CLI autónomo invocado mediante subprocesos (3 referencias de cadena) encargado de la etapa de refinamiento estilístico y tono ejecutivo con IA. |
| `src/assessment_engine/application/run_global_pipeline.py` | **ACTIVE_LEAF** | 141 | 0.0% | 0 | Punto de entrada principal de línea de comandos que orquesta la ejecución secuencial de subprocesos para todo el pipeline estratégico global. |
| `src/assessment_engine/application/run_intelligence_harvesting.py` | **ACTIVE_LEAF** | 845 | 0.0% | 0 | Punto de entrada de ingesta invocado dinámicamente para la extracción inicial y estructuración de inteligencia estratégica del cliente. |
| `src/assessment_engine/application/run_scoring.py` | **ACTIVE_LEAF** | 180 | 0.0% | 0 | Utilidad CLI ejecutada como paso de pipeline mediante subprocesos (3 referencias de cadena) para el cálculo aritmético de puntuaciones y bandas de madurez. |
| `src/assessment_engine/application/run_sota_researcher.py` | **ACTIVE_LEAF** | 162 | 0.0% | 0 | Script de enriquecimiento invocado vía subproceso (2 referencias de cadena) que ejecuta búsquedas web paralelas con GenAI para fundamentar hallazgos técnicos. |
| `src/assessment_engine/application/run_strategic_orchestrator.py` | **ACTIVE_LEAF** | 69 | 0.0% | 2 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_tower_pipeline.py` | **ACTIVE_LEAF** | 624 | 0.0% | 0 | Punto de entrada CLI principal que orquesta el DAG de ejecución del pipeline mediante subprocesos aislados, justificando su grado de entrada cero. |
| `src/assessment_engine/application/tools/apex_dispatcher.py` | **ACTIVE_LEAF** | 513 | 0.0% | 0 | Aplicación de consola interactiva (Rich TUI) y punto de entrada autónomo para la gestión y despacho del backlog de tareas APEX. |
| `src/assessment_engine/application/tools/build_docs_site.py` | **ACTIVE_LEAF** | 183 | 0.0% | 0 | Script utilitario de línea de comandos (marcado con golden-path: ignore) diseñado para el renderizado y construcción del sitio de documentación en CI/CD. |
| `src/assessment_engine/application/tools/build_documentation_health_report.py` | **ACTIVE_LEAF** | 154 | 0.0% | 0 | Herramienta CLI independiente utilizada en flujos de gobernanza para generar reportes de salud y cobertura de la documentación del repositorio. |
| `src/assessment_engine/application/tools/check_docx_unresolved_placeholders.py` | **ACTIVE_LEAF** | 67 | 0.0% | 0 | Script de validación CLI diseñado para ejecutarse como etapa de control de calidad en pipelines o subprocesos para detectar plantillas DOCX incompletas. |
| `src/assessment_engine/application/tools/check_vertex_ai_access.py` | **ACTIVE_LEAF** | 35 | 0.0% | 0 | Utilidad CLI de pre-flight check para validar credenciales y conectividad con Vertex AI de forma aislada antes de la ejecución de agentes. |
| `src/assessment_engine/application/tools/compile_llms_full.py` | **ACTIVE_LEAF** | 104 | 0.0% | 0 | Script CLI autónomo con shebang y argparse diseñado como herramienta de desarrollo para compilar documentación en un archivo llms-full.txt. |
| `src/assessment_engine/application/tools/enforce_english_comments.py` | **ACTIVE_LEAF** | 398 | 0.0% | 0 | Herramienta CLI de linting y traducción asistida por IA (marcada con shebang y golden-path: ignore) que actúa como punto de entrada para control de calidad de código. |
| `src/assessment_engine/application/tools/generate_smoke_data.py` | **ACTIVE_LEAF** | 347 | 0.0% | 1 | Generador determinista de datos sintéticos con soporte CLI e integración en pruebas de humo para validar el pipeline de extremo a extremo. |
| `src/assessment_engine/application/tools/ingest_documents.py` | **ACTIVE_LEAF** | 79 | 0.0% | 0 | Punto de entrada CLI parametrizado que orquesta la ingesta de documentos de clientes conectando directamente con EvidenceEngine y RaptorEngine. |
| `src/assessment_engine/application/tools/lint_documentation_style.py` | **ACTIVE_LEAF** | 64 | 0.0% | 0 | Script CLI autónomo para validación de gobernanza y estilo de documentación en pipelines de CI/CD. |
| `src/assessment_engine/application/tools/regenerate_smoke_artifacts.py` | **ACTIVE_LEAF** | 284 | 0.0% | 0 | Herramienta CLI de orquestación para la regeneración reproducible de artefactos de pruebas de humo (smoke tests). |
| `src/assessment_engine/application/tools/run_golden_path_check.py` | **ACTIVE_LEAF** | 153 | 0.0% | 0 | Punto de entrada CLI utilizado en CI para verificar la adherencia de nuevos archivos a la plantilla arquitectónica (Golden Path). |
| `src/assessment_engine/application/tools/run_incremental_typecheck.py` | **ACTIVE_LEAF** | 87 | 0.0% | 0 | Script ejecutable de CI que invoca mypy de forma incremental apoyándose en el módulo de quality gate. |
| `src/assessment_engine/application/tools/run_product_owner_orchestrator.py` | **ACTIVE_LEAF** | 2227 | 0.0% | 0 | Punto de entrada principal y orquestador de agentes (Product Owner) con alta integración hacia la infraestructura del motor. |
| `src/assessment_engine/application/tools/run_shadow_compilation.py` | **ACTIVE_LEAF** | 145 | 0.0% | 0 | Utilidad CLI de diagnóstico para compilación AST y renderizado aislado de variantes DOCX. |
| `src/assessment_engine/application/tools/sign_dossier.py` | **ACTIVE_LEAF** | 52 | 0.0% | 0 | Script CLI operativo para la firma criptográfica y actualización de metadatos de dossiers de clientes en formato JSON. |
| `src/assessment_engine/application/tools/sync_sentinel.py` | **ACTIVE_LEAF** | 37 | 0.0% | 0 | Script CLI de punto de entrada para sincronizar manualmente la cola de StreamingSentinel y reconstruir el árbol RAG. |
| `src/assessment_engine/application/tools/validate_contracts_schemas.py` | **ACTIVE_LEAF** | 307 | 0.0% | 0 | Herramienta CLI de validación CI/CD que verifica la compatibilidad de tipos entre esquemas Pydantic y la documentación. |
| `src/assessment_engine/application/tools/validate_documentation_snippets.py` | **ACTIVE_LEAF** | 157 | 0.0% | 0 | Script CLI de validación estática que comprueba la validez de rutas y bloques de comandos dentro de archivos Markdown. |
| `src/assessment_engine/application/tools/validate_semantic_drift.py` | **ACTIVE_LEAF** | 213 | 0.0% | 0 | Herramienta CLI para hooks de git o CI/CD que evalúa la deriva semántica inspeccionando diffs entre ramas. |
| `src/assessment_engine/application/tools/visualize_doc_map.py` | **ACTIVE_LEAF** | 264 | 0.0% | 0 | Script ejecutable de renderizado que genera una visualización interactiva en HTML/D3.js a partir del mapa de documentación YAML. |
| `src/assessment_engine/domain/maturity_band.py` | **ACTIVE_LEAF** | 76 | 0.0% | 8 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/prompts/intelligence_prompts.py` | **ACTIVE_LEAF** | 320 | 0.0% | 3 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/annex_synthesis.py` | **ACTIVE_LEAF** | 189 | 0.0% | 3 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/ast.py` | **ACTIVE_LEAF** | 211 | 0.0% | 30 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/blueprint.py` | **ACTIVE_LEAF** | 544 | 0.0% | 6 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/commercial.py` | **ACTIVE_LEAF** | 232 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/common.py` | **ACTIVE_LEAF** | 153 | 0.0% | 12 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/evidence.py` | **ACTIVE_LEAF** | 114 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/global_report.py` | **ACTIVE_LEAF** | 254 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/ai_client.py` | **ACTIVE_LEAF** | 339 | 0.0% | 12 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/infrastructure/auditor/models.py` | **ACTIVE_LEAF** | 60 | 0.0% | 23 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/ast_complexity.py` | **ACTIVE_LEAF** | 470 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/code_hygiene.py` | **ACTIVE_LEAF** | 188 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/sre_observability.py` | **ACTIVE_LEAF** | 139 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/chassis/context.py` | **ACTIVE_LEAF** | 68 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/client_intelligence.py` | **ACTIVE_LEAF** | 1279 | 0.0% | 9 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/infrastructure/config_loader.py` | **ACTIVE_LEAF** | 386 | 0.0% | 26 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/contract_utils.py` | **ACTIVE_LEAF** | 102 | 0.0% | 3 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/deterministic_enricher.py` | **ACTIVE_LEAF** | 225 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/document_ai_client.py` | **ACTIVE_LEAF** | 38 | 0.0% | 2 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/infrastructure/docx_render_utils.py` | **ACTIVE_LEAF** | 1253 | 0.0% | 6 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/epistemic_graph.py` | **ACTIVE_LEAF** | 268 | 0.0% | 15 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/epistemic_graph_service.py` | **ACTIVE_LEAF** | 421 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evidence_engine.py` | **ACTIVE_LEAF** | 437 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evidence_governance.py` | **ACTIVE_LEAF** | 257 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/closure_tribunal.py` | **ACTIVE_LEAF** | 479 | 0.0% | 0 | Actúa como el punto de entrada y gatekeeper final de calidad y seguridad (RFC-015 Phase 4), integrando el dossier estratégico sin requerir importadores directos. |
| `src/assessment_engine/infrastructure/evolution/cognitive_arbiter.py` | **ACTIVE_LEAF** | 1171 | 0.0% | 0 | Funciona como el orquestador principal de alto nivel para el bucle dialéctico (Out-Degree: 12), coordinando las sondas de mutación, complejidad y AST. |
| `src/assessment_engine/infrastructure/evolution/reflexion_ledger.py` | **ACTIVE_LEAF** | 329 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/genai_client.py` | **ACTIVE_LEAF** | 88 | 0.0% | 19 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/infrastructure/global_maturity_policy.py` | **ACTIVE_LEAF** | 68 | 0.0% | 3 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/governance.py` | **ACTIVE_LEAF** | 155 | 0.0% | 3 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/json_from_model.py` | **ACTIVE_LEAF** | 63 | 0.0% | 3 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/localization.py` | **ACTIVE_LEAF** | 338 | 0.0% | 18 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/networkx_analyzer.py` | **ACTIVE_LEAF** | 151 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/pipeline_runtime.py` | **ACTIVE_LEAF** | 173 | 0.0% | 5 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/policies/base.py` | **ACTIVE_LEAF** | 15 | 0.0% | 8 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/raptor_engine.py` | **ACTIVE_LEAF** | 236 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/runtime_env.py` | **ACTIVE_LEAF** | 196 | 0.0% | 8 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/runtime_paths.py` | **ACTIVE_LEAF** | 155 | 0.0% | 29 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/text_utils.py` | **ACTIVE_LEAF** | 162 | 0.0% | 17 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/mcp_server.py` | **ACTIVE_LEAF** | 533 | 0.0% | 0 | Actúa como punto de entrada principal del servidor FastMCP para exponer las capacidades del motor a agentes supervisores externos. |
| `src/assessment_engine/adapters/compilers/ast_appendices_builder.py` | **CANONICAL_CORE** | 303 | 0.0% | 1 | Submódulo especializado y limpio dentro del nuevo pipeline de compilación que construye nodos tipados del AST para los apéndices del documento. |
| `src/assessment_engine/adapters/compilers/docx_compiler.py` | **CANONICAL_CORE** | 565 | 0.0% | 1 | Implementación principal del puerto DocumentCompiler en la arquitectura hexagonal que transforma el árbol de sintaxis abstracta (DocumentAST) en un documento Word físico. |
| `src/assessment_engine/adapters/compilers/payload_to_ast.py` | **CANONICAL_CORE** | 1236 | 0.0% | 1 | Transformador central del motor de compilación que desacopla los datos de entrada de la vista, convirtiendo los payloads crudos en una representación intermedia estandarizada (DocumentAST). |
| `src/assessment_engine/adapters/render_global_report_from_template.py` | **CANONICAL_CORE** | 1565 | 0.0% | 1 | Motor de renderizado para el reporte ejecutivo global que, además de generar dicho entregable, actúa como librería base exportando primitivas de formato consumidas por render_commercial_report.py. |
| `src/assessment_engine/adapters/render_tower_blueprint.py` | **CANONICAL_CORE** | 1368 | 0.0% | 1 | Motor principal de renderizado de blueprints DOCX activamente importado en el grafo de ejecución (In-Degree: 1) y altamente acoplado a las utilidades de infraestructura y esquemas de dominio. |
| `src/assessment_engine/application/bootstrap/bootstrap_tower_from_matrix.py` | **CANONICAL_CORE** | 871 | 0.0% | 1 | Módulo esencial de lógica de aplicación que implementa el parseo XML/DOCX para inicializar configuraciones de torres, requerido directamente por el orquestador de bootstrap (In-Degree: 1). |
| `src/assessment_engine/application/build_case_input.py` | **CANONICAL_CORE** | 319 | 0.0% | 1 | Componente central del pipeline de ingesta de datos e inteligencia de cliente, importado directamente por otros módulos (In-Degree: 1) y referenciado en la configuración del flujo (String Refs: 4). |
| `src/assessment_engine/application/generate_mermaid_gantt.py` | **CANONICAL_CORE** | 160 | 0.0% | 1 | Módulo funcional de generación de diagramas Mermaid que posee importadores directos activos (In-Degree: 1) dentro del flujo de reportes. |
| `src/assessment_engine/application/run_executive_annex_synthesizer.py` | **CANONICAL_CORE** | 842 | 0.0% | 1 | Motor esencial del flujo Top-Down que transforma el Blueprint en el Anexo del CTO, contando tanto con importadores directos como referencias dinámicas en el pipeline. |
| `src/assessment_engine/application/run_tower_blueprint_engine.py` | **CANONICAL_CORE** | 1055 | 0.0% | 1 | Componente arquitectónico central de alta complejidad (1055 LOC, Out-Degree 18) que procesa los pilares de arquitectura, valida esquemas y sincroniza el grafo de conocimiento. |
| `src/assessment_engine/application/tools/actuarial_ledger_generator.py` | **CANONICAL_CORE** | 93 | 0.0% | 1 | Componente activo e importado por el motor para la generación de expedientes de validación actuarial y auditoría de riesgos (SR 11-7). |
| `src/assessment_engine/application/tools/adversarial_consensus_engine.py` | **CANONICAL_CORE** | 236 | 0.0% | 1 | Módulo esencial de dominio importado activamente para ejecutar la evaluación de eficacia de controles mediante consenso adversarial con modelos generativos. |
| `src/assessment_engine/application/tools/context_tools.py` | **CANONICAL_CORE** | 206 | 0.0% | 1 | Módulo de utilidades activamente importado en el motor que provee capacidades esenciales de búsqueda externa y trazabilidad en tiempo de ejecución. |
| `src/assessment_engine/application/tools/corporate_project_aggregator.py` | **CANONICAL_CORE** | 173 | 0.0% | 1 | Componente de lógica de aplicación importado activamente para modelar y agregar iniciativas estratégicas y paquetes de trabajo con integración a la configuración. |
| `src/assessment_engine/application/tools/financial_scale_calibrator.py` | **CANONICAL_CORE** | 309 | 0.0% | 1 | Módulo esencial de calibración de riesgo financiero mediante GenAI que posee consumidores activos dentro de la arquitectura del sistema. |
| `src/assessment_engine/application/tools/run_incremental_quality_gate.py` | **CANONICAL_CORE** | 167 | 0.0% | 1 | Módulo base para control de calidad incremental en Git que además exporta utilidades consumidas por otros scripts de validación. |
| `src/assessment_engine/application/tools/validate_documentation_governance.py` | **CANONICAL_CORE** | 693 | 0.0% | 0 | Módulo central del subsistema de gobernanza documental, referenciado e importado activamente por el resto de validadores de documentación. |
| `src/assessment_engine/application/validate_tower_definition.py` | **CANONICAL_CORE** | 203 | 0.0% | 1 | Componente de aplicación importado en el motor principal para validar la estructura e integridad de las definiciones de torres. |
| `src/assessment_engine/domain/ontology_registry.py` | **CANONICAL_CORE** | 49 | 0.0% | 1 | Entidad de dominio fundamental e importada activamente que gestiona las restricciones ontológicas (nodos y predicados) del grafo. |
| `src/assessment_engine/domain/prompts/blueprint_prompts.py` | **CANONICAL_CORE** | 246 | 0.0% | 1 | Componente activo del dominio encargado de la carga y resolución de configuraciones de prompts desde el registro YAML. |
| `src/assessment_engine/domain/prompts/commercial_prompts.py` | **CANONICAL_CORE** | 61 | 0.0% | 1 | Módulo de dominio en uso que centraliza el catálogo de referencia comercial (TCV) y argumentos de venta para la generación de propuestas. |
| `src/assessment_engine/domain/schemas/context.py` | **CANONICAL_CORE** | 126 | 0.0% | 0 | Contenedor de estado en memoria central para el ciclo de vida del motor (51 referencias de cadenas indican uso intensivo mediante tipado diferido o inyección dinámica). |
| `src/assessment_engine/domain/schemas/intelligence.py` | **CANONICAL_CORE** | 481 | 0.0% | 1 | Módulo esencial de esquemas y sanitización de salidas de IA con alta densidad de clases (12) e integración activa en el pipeline. |
| `src/assessment_engine/domain/schemas/risks.py` | **CANONICAL_CORE** | 38 | 0.0% | 0 | Define esquemas Pydantic de dominio fundamentales para la evaluación de riesgos y cuenta con 22 referencias dinámicas por nombre (String Refs) a pesar de no tener importaciones directas en el grafo estático. |
| `src/assessment_engine/domain/schemas/rubric.py` | **CANONICAL_CORE** | 38 | 0.0% | 1 | Esquema de dominio crítico activamente importado por la infraestructura de benchmarking para modelar reglas declarativas y umbrales de puntuación. |
| `src/assessment_engine/domain/schemas/tobe.py` | **CANONICAL_CORE** | 121 | 0.0% | 0 | Modelo de dominio principal para el estado objetivo (To-Be) con múltiples validadores de negocio y 7 referencias en cadenas de configuración o carga dinámica. |
| `src/assessment_engine/domain/schemas/todo.py` | **CANONICAL_CORE** | 38 | 0.0% | 0 | Esquema estructural para el plan de acción (To-Do) requerido en la generación de entregables del motor, respaldado por 12 referencias dinámicas en el código. |
| `src/assessment_engine/infrastructure/agentic_benchmarker.py` | **CANONICAL_CORE** | 508 | 0.0% | 1 | Componente central de infraestructura que integra Vertex AI, ADK y gobernanza de evidencias para ejecutar el benchmarking dinámico. |
| `src/assessment_engine/infrastructure/apex_models.py` | **CANONICAL_CORE** | 59 | 0.0% | 1 | Define los contratos de datos estructurados esenciales para las respuestas de deliberación y control de flujo del subsistema Apex, con uso activo verificado. |
| `src/assessment_engine/infrastructure/apex_sentinel.py` | **CANONICAL_CORE** | 111 | 0.0% | 1 | Módulo activo de auditoría transaccional y seguimiento de costes del ciclo de vida de tareas en el motor de ejecución Apex. |
| `src/assessment_engine/infrastructure/auditor/mutation_probe.py` | **CANONICAL_CORE** | 124 | 0.0% | 1 | Primitiva de pruebas de mutación AST integrada activamente en el subsistema auditor para validar la efectividad de las suites de pruebas. |
| `src/assessment_engine/infrastructure/auditor/probes/ai_safety_llm.py` | **CANONICAL_CORE** | 150 | 0.0% | 1 | Sonda de auditoría esencial e integrada en el orquestador (In-Degree: 1) encargada de verificar el cumplimiento de OWASP Top 10 para LLMs mediante análisis AST. |
| `src/assessment_engine/infrastructure/auditor/probes/assertion_quality.py` | **CANONICAL_CORE** | 71 | 0.0% | 1 | Componente nuclear del motor de evaluación importado activamente para auditar la densidad e invariantes de las aserciones en la suite de pruebas. |
| `src/assessment_engine/infrastructure/auditor/probes/browser_accessibility.py` | **CANONICAL_CORE** | 183 | 0.0% | 1 | Módulo de evaluación canónico acoplado al motor de auditoría para validar normativas de accesibilidad web WCAG 2.2 AA y cumplimiento EAA. |
| `src/assessment_engine/infrastructure/auditor/probes/comment_quality.py` | **CANONICAL_CORE** | 496 | 0.0% | 1 | Sonda determinista fundamental para el análisis de contratos semánticos, calidad de docstrings y soberanía lingüística del código. |
| `src/assessment_engine/infrastructure/auditor/probes/concurrency_stress.py` | **CANONICAL_CORE** | 308 | 0.0% | 1 | Componente crítico de infraestructura que evalúa el rendimiento bajo estrés concurrente, latencia de cola y contención de bloqueos SQLite. |
| `src/assessment_engine/infrastructure/auditor/probes/contract_drift.py` | **CANONICAL_CORE** | 175 | 0.0% | 1 | Sonda arquitectónica esencial que previene la deriva de esquemas entre sentencias DDL en SQLite, modelos Pydantic v2 y contratos OpenAPI. |
| `src/assessment_engine/infrastructure/auditor/probes/documentation_quality.py` | **CANONICAL_CORE** | 190 | 0.0% | 1 | Módulo central de validación documental que asegura la trazabilidad arquitectónica y la integridad de enlaces según ISO/IEC/IEEE 26514. |
| `src/assessment_engine/infrastructure/auditor/probes/hardcoded_artifacts.py` | **CANONICAL_CORE** | 205 | 0.0% | 1 | Sonda de seguridad indispensable que utiliza análisis de entropía de Shannon y AST para detectar secretos expuestos, PII y fugas de dominio. |
| `src/assessment_engine/infrastructure/auditor/probes/legal_compliance.py` | **CANONICAL_CORE** | 179 | 0.0% | 1 | Componente esencial del subsistema de sondas de auditoría (In-Degree: 1) encargado de verificar el cumplimiento normativo GDPR y licencias copyleft. |
| `src/assessment_engine/infrastructure/auditor/probes/mutation_gate.py` | **CANONICAL_CORE** | 89 | 0.0% | 1 | Sonda activa e integrada en el motor de evaluación para medir la efectividad de la suite de pruebas mediante mutation testing (ISO/IEC/IEEE 29119). |
| `src/assessment_engine/infrastructure/auditor/probes/neurosymbolic_topology.py` | **CANONICAL_CORE** | 132 | 0.0% | 1 | Módulo núcleo del auditor responsable del análisis topológico mediante grafos AST con NetworkX para la detección de deuda estructural y código muerto. |
| `src/assessment_engine/infrastructure/auditor/probes/performance_finops.py` | **CANONICAL_CORE** | 140 | 0.0% | 1 | Sonda de auditoría integrada que inspecciona el AST en busca de antipatrones de rendimiento (N+1 queries) y configuraciones de eficiencia en bases de datos. |
| `src/assessment_engine/infrastructure/auditor/probes/resilience_chaos.py` | **CANONICAL_CORE** | 167 | 0.0% | 1 | Componente activo del motor de auditoría que valida patrones de tolerancia a fallos, timeouts de red y resiliencia mediante análisis estático AST. |
| `src/assessment_engine/infrastructure/auditor/probes/security_dast.py` | **CANONICAL_CORE** | 136 | 0.0% | 1 | Sonda esencial de seguridad dinámica (DAST) conectada al orquestador para ejecutar pruebas de penetración en memoria bajo el estándar OWASP ASVS. |
| `src/assessment_engine/infrastructure/auditor/probes/security_sast.py` | **CANONICAL_CORE** | 338 | 0.0% | 1 | Módulo primario de análisis estático de seguridad (SAST) e identificación de secretos por entropía de Shannon, importado activamente por el motor. |
| `src/assessment_engine/infrastructure/auditor/probes/structural_smells.py` | **CANONICAL_CORE** | 180 | 0.0% | 1 | Sonda fundamental del auditor encargada de detectar code smells arquitectónicos, clases monolíticas y violaciones de entropía estructural. |
| `src/assessment_engine/infrastructure/auditor/probes/supply_chain.py` | **CANONICAL_CORE** | 238 | 0.0% | 1 | Sonda de seguridad crítica para análisis de dependencias (SCA) y generación de SBOM integrada directamente en el escáner de auditoría. |
| `src/assessment_engine/infrastructure/auditor/probes/test_coverage.py` | **CANONICAL_CORE** | 74 | 0.0% | 1 | Sonda estándar del subsistema de auditoría encargada de validar las métricas de cobertura de código frente a los umbrales de calidad. |
| `src/assessment_engine/infrastructure/auditor/reporter.py` | **CANONICAL_CORE** | 249 | 0.0% | 1 | Motor de renderizado esencial para la generación de reportes ejecutivos y certificados HTML del subsistema de auditoría. |
| `src/assessment_engine/infrastructure/auditor/scanner.py` | **CANONICAL_CORE** | 138 | 0.0% | 1 | Orquestador central del motor de auditoría que agrega y ejecuta todas las sondas de certificación (Out-Degree: 23). |
| `src/assessment_engine/infrastructure/entity_resolution.py` | **CANONICAL_CORE** | 128 | 0.0% | 1 | Motor funcional de resolución de entidades y deduplicación de nodos para el grafo de conocimiento, a pesar de tener artefactos de generación en su docstring. |
| `src/assessment_engine/infrastructure/epistemic_extractor.py` | **CANONICAL_CORE** | 69 | 0.0% | 1 | Componente central de extracción de conocimiento que integra modelos estructurados Pydantic con Google ADK y Vertex AI. |
| `src/assessment_engine/infrastructure/evolution/ast_signature_guard.py` | **CANONICAL_CORE** | 512 | 0.0% | 1 | Módulo de infraestructura robusto y de alta complejidad (512 LOC) indispensable para la detección de regresiones en contratos de API mediante análisis AST. |
| `src/assessment_engine/infrastructure/evolution/ast_signature_models.py` | **CANONICAL_CORE** | 131 | 0.0% | 1 | Define los modelos de datos y enums fundamentales (como VerdictStatus y FunctionSignature) utilizados activamente por el validador de firmas AST. |
| `src/assessment_engine/infrastructure/evolution/complexity_guard.py` | **CANONICAL_CORE** | 249 | 0.0% | 1 | Componente esencial importado por el Cognitive Arbiter para auditar y hacer cumplir las restricciones de complejidad ciclomática y cognitiva. |
| `src/assessment_engine/infrastructure/evolution/epistemic_distiller.py` | **CANONICAL_CORE** | 902 | 0.0% | 1 | Módulo central de la Fase 1 (RFC-015) que destila invariantes y genera el ProductStrategyDossier consumido directamente por el Closure Tribunal. |
| `src/assessment_engine/infrastructure/evolution/fault_localizer.py` | **CANONICAL_CORE** | 243 | 0.0% | 1 | Proporciona capacidades críticas de aislamiento de fallos mediante el algoritmo Ochiai (SBFL) y mantiene referencias activas dentro del motor de evolución. |
| `src/assessment_engine/infrastructure/evolution/mcts_refactor_engine.py` | **CANONICAL_CORE** | 132 | 0.0% | 1 | Implementa el motor de búsqueda de árbol Monte Carlo (RFC-019) para refactorización estructural sobre AST, siendo consumido activamente en el pipeline. |
| `src/assessment_engine/infrastructure/evolution/mutation_ctf_probe.py` | **CANONICAL_CORE** | 299 | 0.0% | 1 | Sonda de pruebas de mutación requerida directamente por el Cognitive Arbiter para certificar la robustez de los tests generados. |
| `src/assessment_engine/infrastructure/evolution/trace_conditioner.py` | **CANONICAL_CORE** | 114 | 0.0% | 1 | Módulo esencial de diagnóstico forense y telemetría W3C integrado activamente en el subsistema de evolución y métricas. |
| `src/assessment_engine/infrastructure/evolution/worktree_runner.py` | **CANONICAL_CORE** | 139 | 0.0% | 1 | Primitiva de infraestructura crítica para el aislamiento efímero de Git durante la experimentación y ejecución segura de ramas. |
| `src/assessment_engine/infrastructure/http_client.py` | **CANONICAL_CORE** | 113 | 0.0% | 1 | Cliente HTTP soberano que garantiza resiliencia de red, timeouts acotados y propagación de contexto de traza en toda la arquitectura. |
| `src/assessment_engine/infrastructure/liability_signer.py` | **CANONICAL_CORE** | 40 | 0.0% | 1 | Componente central de auditoría y cumplimiento encargado de la firma criptográfica no repudiable de artefactos operativos. |
| `src/assessment_engine/infrastructure/logger_config.py` | **CANONICAL_CORE** | 112 | 0.0% | 1 | Configuración base de observabilidad para la emisión de logs estructurados en JSON compatibles con Google Cloud Logging. |
| `src/assessment_engine/infrastructure/mcda_sensitivity_engine.py` | **CANONICAL_CORE** | 171 | 0.0% | 1 | Motor matemático central que ejecuta el análisis de sensibilidad global (Sobol/Monte Carlo) para el modelo de decisión MCDA. |
| `src/assessment_engine/infrastructure/parser_strategy.py` | **CANONICAL_CORE** | 35 | 0.0% | 1 | Implementación del patrón Strategy para desacoplar la extracción de documentos entre el parser legado y Google Document AI. |
| `src/assessment_engine/infrastructure/policies/business_case.py` | **CANONICAL_CORE** | 58 | 0.0% | 0 | Implementa BusinessCaseGroundingPolicy, política esencial exportada a través de policies/__init__.py y registrada activamente en el POLICY_REGISTRY del motor de políticas. |
| `src/assessment_engine/infrastructure/policies/client_sanitization.py` | **CANONICAL_CORE** | 30 | 0.0% | 0 | Define ClientSanitizationPolicy y las utilidades de sanitización de texto/árbol que son importadas y ejecutadas directamente por SovereignPolicyEngine. |
| `src/assessment_engine/infrastructure/policies/deduplication.py` | **CANONICAL_CORE** | 94 | 0.0% | 0 | Contiene la implementación de DeduplicationPolicy para consolidar iniciativas de Platform Engineering, registrada y orquestada en el motor central de políticas. |
| `src/assessment_engine/infrastructure/policies/fair_risk.py` | **CANONICAL_CORE** | 900 | 0.0% | 0 | Componente crítico que implementa la simulación de Monte Carlo (FairRiskPolicy) para la cuantificación de riesgos, integrado en el registro del motor de políticas. |
| `src/assessment_engine/infrastructure/policies/ot_perimeter.py` | **CANONICAL_CORE** | 78 | 0.0% | 0 | Implementa OTPerimeterPolicy para la evaluación de perímetros industriales e infraestructura crítica, requerido por el registro activo de políticas en policy_engine.py. |
| `src/assessment_engine/infrastructure/policies/reverse_traceability.py` | **CANONICAL_CORE** | 146 | 0.0% | 0 | Provee la lógica de ReverseTraceabilityPolicy para vincular hallazgos arquitectónicos con proyectos de mitigación, consumido directamente por SovereignPolicyEngine. |
| `src/assessment_engine/infrastructure/policies/sequencing.py` | **CANONICAL_CORE** | 47 | 0.0% | 0 | Define SequencingPolicy para la planificación de horizontes temporales de transformación, re-exportado por el paquete policies y activo en POLICY_REGISTRY. |
| `src/assessment_engine/infrastructure/policy_engine.py` | **CANONICAL_CORE** | 83 | 0.0% | 1 | Orquestador central (SovereignPolicyEngine) con importadores activos que registra, instancia y ejecuta secuencialmente todas las políticas soberanas sobre el EpistemicGraph. |
| `src/assessment_engine/infrastructure/product_owner_models.py` | **CANONICAL_CORE** | 47 | 0.0% | 1 | Define esquemas Pydantic esenciales para la matriz de riesgos y planificación de tareas que son consumidos activamente por la lógica de infraestructura. |
| `src/assessment_engine/infrastructure/secrets_client.py` | **CANONICAL_CORE** | 52 | 0.0% | 1 | Proporciona el adaptador de infraestructura necesario para la recuperación segura de secretos desde Google Cloud Secret Manager. |
| `src/assessment_engine/infrastructure/streaming_sentinel.py` | **CANONICAL_CORE** | 424 | 0.0% | 1 | Implementa el daemon de ingesta RAG en tiempo real y almacenamiento en doble capa (SQLite WAL), siendo un componente central del motor de datos. |
| `src/assessment_engine/infrastructure/verification_agent.py` | **CANONICAL_CORE** | 27 | 0.0% | 1 | Establece la clase base abstracta y el contrato de interfaz requerido por los agentes de verificación de integridad de archivos. |
| `src/assessment_engine/ports/document_compiler.py` | **CANONICAL_CORE** | 8 | 0.0% | 1 | Define el puerto de arquitectura hexagonal (interfaz ABC) indispensable para desacoplar la compilación de árboles AST a formatos de documento. |
| `src/assessment_engine/ports/graph_analyzer.py` | **CANONICAL_CORE** | 37 | 0.0% | 1 | Define el puerto arquitectónico abstracto para el análisis estratégico basado en grafos, aislando el dominio de las implementaciones concretas. |
| `src/assessment_engine/application/run_global_synthesizer_tobe.py` | **CONFIRMED_ORPHAN** | 569 | 0.0% | 0 | Módulo aislado con cero importadores y cero referencias dinámicas que define esquemas inline redundantes fuera de la capa de dominio, evidenciando ser un prototipo abandonado. |
| `src/assessment_engine/application/tools/dynamic_tower_dispatcher.py` | **CONFIRMED_ORPHAN** | 225 | 0.0% | 0 | Módulo completamente aislado (In-Degree 0, Out-Degree 0, sin cobertura) que intenta importar dinámicamente servicios inexistentes mediante rutas especulativas. |
| `src/assessment_engine/domain/schemas/asis.py` | **CONFIRMED_ORPHAN** | 47 | 0.0% | 0 | Esquema Pydantic sin importadores activos (In-Degree 0) ni cobertura de pruebas, indicando un modelo de datos obsoleto o no integrado. |
| `src/assessment_engine/domain/schemas/conclusion.py` | **CONFIRMED_ORPHAN** | 41 | 0.0% | 0 | Modelo de datos aislado con cero dependencias entrantes y sin cobertura de ejecución, constituyendo código muerto en la capa de esquemas. |
| `src/assessment_engine/domain/schemas/gap.py` | **CONFIRMED_ORPHAN** | 48 | 0.0% | 0 | Esquema de análisis GAP huérfano sin ningún módulo que lo importe directamente ni cobertura en tests. |
| `src/assessment_engine/infrastructure/doctor_agent.py` | **CONFIRMED_ORPHAN** | 23 | 0.0% | 1 | Clase stub de 23 líneas sin dependencias salientes, sin cobertura de pruebas y con docstrings corruptos autogenerados (diccionario serializado). |
| `src/assessment_engine/infrastructure/policies/archimate.py` | **CONFIRMED_ORPHAN** | 54 | 0.0% | 0 | Política de entregables ArchiMate sin importadores directos, referencias dinámicas ni cobertura de pruebas que justifiquen su retención. |
| `src/assessment_engine/infrastructure/vendor_intelligence.py` | **CONFIRMED_ORPHAN** | 223 | 0.0% | 0 | Módulo de síntesis de blueprints de fabricantes sin importadores (In-Degree: 0), sin referencias dinámicas y con 0% de cobertura de pruebas. |
| `src/assessment_engine/adapters/compile_asis_docx_from_modules.py` | **SHADOW_DUPLICATE** | 2884 | 0.0% | 1 | Monolito procedural heredado de casi 3000 líneas que acopla la manipulación directa de DOCX con la lógica de negocio, habiendo sido reemplazado arquitectónicamente por el pipeline modular basado en AST (payload_to_ast y docx_compiler). |
| `src/assessment_engine/adapters/generate_asis_markdown_modules.py` | **SHADOW_DUPLICATE** | 1072 | 0.0% | 0 | Script sin importadores que duplica funciones exactas de limpieza de texto presentes en payload_to_ast.py y pertenece al flujo obsoleto de generación por módulos intermedios en Markdown. |
| `src/assessment_engine/domain/prompts/product_owner_prompts.py` | **SHADOW_DUPLICATE** | 162 | 0.0% | 1 | Aunque tiene un importador activo, reimplementa de forma redundante la lógica de carga de archivos YAML de la carpeta 'registry' que ya existe en blueprint_prompts.py. |
