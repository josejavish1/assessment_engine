---
status: Verified
owner: docs-governance
source_of_truth:
- ../../scripts/audit_neurosymbolic_codebase.py
- ../../src/assessment_engine/
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: operational
diataxis: explanation
verification_mode: editorial
---
# 🏛️ Auditoría Neuro-Simbólica de la Base de Código

**Fecha:** Octubre 2026 | **Metodología:** Topología AST (NetworkX) + Trazabilidad Dinámica (`coverage.py`) + Árbitro Cognitivo (`gemini-4-argon`)

## 1. Resumen Ejecutivo de Salud del Código

- **Total de Archivos Auditados:** 202
- **Núcleo Canónico (Vital):** 48 (23.8%)
- **Hojas Activas / Adaptadores:** 126 (62.4%)
- **Módulos Sombra (Duplicados / Candidatos a Fusión):** 5
- **Huérfanos Confirmados (Código Muerto / Purga Segura):** 23

## 2. ⚠️ Huérfanos Confirmados (Blast Radius = 0)

| Archivo | LOC | Cobertura | In-Degree | Razón Técnica de Purga |
| :--- | :---: | :---: | :---: | :--- |
| `src/assessment_engine/adapters/render_togaf_consolidated_asis.py` | 840 | 0.0% | 0 | Script legacy sin cobertura, importadores ni referencias dinámicas (String Refs: 0) que no utiliza los esquemas de dominio de validación (Pydantic) del motor actual. |
| `src/assessment_engine/adapters/render_togaf_consolidated_tobe.py` | 967 | 0.0% | 0 | Código muerto sin referencias estáticas ni dinámicas ni cobertura de tests, que además reimplementa localmente funciones de infraestructura como 'shade_cell'. |
| `src/assessment_engine/adapters/render_togaf_consolidated_todo.py` | 331 | 0.0% | 0 | Módulo huérfano sin referencias ni cobertura de pruebas, desconectado de la capa de dominio y con duplicación de lógica de bajo nivel OOXML ('shade_cell'). |
| `src/assessment_engine/adapters/tobe_document_builder.py` | 130 | 0.0% | 0 | Módulo completamente aislado (In-Degree: 0, Out-Degree: 0, String Refs: 0) y sin cobertura de pruebas que realiza agregaciones redundantes desconectadas del grafo principal. |
| `src/assessment_engine/application/generate_fair_heatmap.py` | 145 | 0.0% | 0 | Módulo de visualización aislado sin referencias de cadena ni importadores activos en ninguno de los pipelines de ejecución. |
| `src/assessment_engine/application/run_global_synthesizer.py` | 186 | 0.0% | 0 | Script de síntesis desconectado que define esquemas inline redundantes y carece tanto de importadores como de invocaciones por subproceso (0 referencias). |
| `src/assessment_engine/application/tools/audit_tower_annex.py` | 252 | 0.0% | 0 | Script desconectado (In-Degree: 0, String Refs: 0) para inspeccionar XML de archivos DOCX sin referencias en el motor de ejecución. |
| `src/assessment_engine/application/tools/check_xml.py` | 37 | 0.0% | 0 | Script de diagnóstico ad-hoc sin importadores, sin cobertura de tests y sin interfaz CLI estructurada. |
| `src/assessment_engine/application/tools/compare_documents.py` | 141 | 0.0% | 0 | Utilidad de inspección manual con heurísticas hardcodeadas que no es invocada por ningún módulo ni pipeline. |
| `src/assessment_engine/application/tools/compare_docx_xml.py` | 85 | 0.0% | 0 | Código muerto de comparación XML con artefactos de autogeneración corruptos en el docstring y cero referencias en el grafo. |
| `src/assessment_engine/application/tools/context_grounder.py` | 46 | 0.0% | 0 | Módulo de extracción de texto truncado e incompleto que ha quedado huérfano sin consumidores ni pruebas asociadas. |
| `src/assessment_engine/application/tools/ingest_eurovision.py` | 23 | 0.0% | 0 | Script de ingesta ad-hoc roto que utiliza rutas de importación obsoletas ('from src.infrastructure...') y carece de referencias en el sistema. |
| `src/assessment_engine/application/tools/repair_tower_payload_scores.py` | 389 | 0.0% | 0 | Script utilitario de reparación sin referencias entrantes, sin cobertura de pruebas y con signos evidentes de corrupción por generación automática (imports duplicados y docstrings malformados). |
| `src/assessment_engine/application/tools/test_tui.py` | 78 | 0.0% | 0 | Script prototipo de interfaz gráfica en consola (Rich) sin integraciones entrantes ni referencias en el motor principal. |
| `src/assessment_engine/domain/prompts/conclusion_prompts.py` | 176 | 0.0% | 0 | Módulo generador de prompts para conclusiones con grado de entrada cero y sin referencias dinámicas, indicando código muerto. |
| `src/assessment_engine/domain/prompts/gap_prompts.py` | 140 | 0.0% | 0 | Módulo de plantillas de prompts para análisis GAP completamente desconectado del flujo de ejecución actual (In-Degree: 0). |
| `src/assessment_engine/domain/prompts/global_prompts.py` | 117 | 0.0% | 0 | Módulo de plantillas de prompts estáticos completamente desconectado del grafo de ejecución (0 importadores, 0 referencias y 0% de cobertura). |
| `src/assessment_engine/domain/prompts/section_prompts.py` | 165 | 0.0% | 0 | Generador de prompts para secciones sin consumidores activos ni cobertura de pruebas, indicando una refactorización o abandono del flujo. |
| `src/assessment_engine/domain/prompts/tobe_prompts.py` | 161 | 0.0% | 0 | Repositorio de prompts TO-BE aislado sin referencias entrantes ni salientes en todo el motor de arquitectura. |
| `src/assessment_engine/domain/prompts/todo_prompts.py` | 153 | 0.0% | 0 | Módulo de generación de prompts TO-DO huérfano, sin llamadas activas ni cobertura en las pruebas del sistema. |
| `src/assessment_engine/infrastructure/editorial_autofix.py` | 40 | 0.0% | 0 | Código muerto sin importadores cuya implementación interna (_walk) es un no-op que clona estructuras recursivamente sin aplicar ninguna transformación real. |
| `src/assessment_engine/infrastructure/remediation_playbooks.py` | 45 | 0.0% | 0 | Carece por completo de referencias entrantes, salientes o cobertura de pruebas, conteniendo únicamente utilidades genéricas de subprocesos Git desconectadas del motor de evaluación. |
| `src/assessment_engine/infrastructure/review_resilience.py` | 113 | 0.0% | 0 | Módulo completamente aislado (0 grados de entrada/salida y 0% de cobertura) que además contiene código roto e inalcanzable como la llamada inválida a `{}.model_dump()`. |

## 3. 👥 Módulos Sombra (Candidatos a Fusión / Refactor)

| Archivo | LOC | Cobertura | In-Degree | Diagnóstico de Fusión |
| :--- | :---: | :---: | :---: | :--- |
| `src/assessment_engine/application/tools/check_docx_quality_flags.py` | 92 | 0.0% | 0 | Duplica exactamente la validación de expresiones regulares de plantillas rota que ya realiza audit_tower_annex.py pero usando python-docx, además de estar huérfano. |
| `src/assessment_engine/application/tools/generate_inputs.py` | 39 | 0.0% | 0 | Script procedural obsoleto con valores hardcodeados para 'ivirma' que ha sido completamente reemplazado por la versión determinista y estructurada en generate_smoke_data.py. |
| `src/assessment_engine/application/tools/ingest_molins.py` | 32 | 0.0% | 0 | Clon de script de ingesta con rutas hardcodeadas para un cliente específico, duplicando la lógica de inicialización del Evidence y Raptor Engine en lugar de usar un CLI parametrizado. |
| `src/assessment_engine/application/tools/ingest_redeia.py` | 26 | 0.0% | 0 | Duplicado exacto del flujo de ingesta manual adaptado para el cliente 'redeia', violando el principio DRY frente a otros scripts de ingesta idénticos. |
| `src/assessment_engine/infrastructure/maturity_band.py` | 62 | 0.0% | 0 | Define constantes y lógica de negocio central (bandas de madurez) mal ubicadas en la capa de infraestructura que tienen 0 importadores directos pero 10 referencias por string, lo que indica que fue desplazado por una implementación canónica en la capa de dominio. |

## 4. 📋 Inventario Exhaustivo Archivo a Archivo

| Archivo | Veredicto | LOC | Cobertura | In-Deg | Dictamen Funcional |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `src/assessment_engine/adapters/compile_asis_docx_from_modules.py` | **ACTIVE_LEAF** | 3036 | 67.7% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/compilers/docx_compiler.py` | **ACTIVE_LEAF** | 565 | 79.2% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/compilers/payload_to_ast.py` | **ACTIVE_LEAF** | 1884 | 69.8% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/generate_asis_markdown_modules.py` | **ACTIVE_LEAF** | 1060 | 37.2% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/render_commercial_report.py` | **ACTIVE_LEAF** | 782 | 0.0% | 0 | Actúa como un adaptador de salida válido para el reporte comercial, integrándose con esquemas de dominio actuales, utilidades de infraestructura y referencias dinámicas (String Refs: 2). |
| `src/assessment_engine/adapters/render_lineage_portal.py` | **ACTIVE_LEAF** | 138 | 0.0% | 0 | Script de punto de entrada independiente para la generación del portal HTML de linaje, referenciado dinámicamente en el pipeline y acoplado a las rutas de ejecución actuales. |
| `src/assessment_engine/adapters/render_togaf_asis_annex.py` | **ACTIVE_LEAF** | 946 | 78.8% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/render_tower_annex_from_template.py` | **ACTIVE_LEAF** | 854 | 0.0% | 0 | Adaptador de renderizado activo invocado dinámicamente (String Refs: 2) que consume esquemas de dominio ('AnnexPayload'), casos de uso de aplicación y utilidades estándar. |
| `src/assessment_engine/adapters/render_tower_blueprint.py` | **ACTIVE_LEAF** | 1363 | 7.2% | 0 | Punto de entrada de renderizado clave con cobertura de pruebas activa (7.2%), alto acoplamiento saliente hacia el dominio e infraestructura (Out-Degree: 9) y referencias dinámicas. |
| `src/assessment_engine/adapters/render_web_presentation.py` | **ACTIVE_LEAF** | 411 | 21.7% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/bootstrap/bootstrap_all_towers.py` | **ACTIVE_LEAF** | 125 | 0.0% | 0 | Script CLI de nivel superior diseñado para inicializar masivamente la configuración de todas las torres consumiendo el motor de bootstrap subyacente. |
| `src/assessment_engine/application/build_evidence_ledger.py` | **ACTIVE_LEAF** | 211 | 77.2% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/build_global_report_payload.py` | **ACTIVE_LEAF** | 444 | 0.0% | 0 | Script de aplicación invocado por referencia (String Refs: 1) que orquesta múltiples módulos de infraestructura para ensamblar el payload de reporte global. |
| `src/assessment_engine/application/cli.py` | **ACTIVE_LEAF** | 382 | 0.0% | 0 | Punto de entrada principal (Control Panel CLI) que unifica y ejecuta los pipelines del motor mediante subprocesos del sistema. |
| `src/assessment_engine/application/export_graph_state.py` | **ACTIVE_LEAF** | 291 | 0.0% | 0 | Exportador de estado del Digital Twin que actúa como nodo hoja activo (String Refs: 1, Out-Degree: 6) integrando el grafo epistémico y análisis de red para consumidores externos. |
| `src/assessment_engine/application/generate_executive_roadmap_image.py` | **ACTIVE_LEAF** | 148 | 0.0% | 0 | Utilidad de renderizado visual independiente invocada por línea de comandos (String Refs: 1) para generar diagramas de Gantt mediante Matplotlib. |
| `src/assessment_engine/application/generate_global_radar_chart.py` | **ACTIVE_LEAF** | 148 | 0.0% | 0 | Script de renderizado gráfico invocado dinámicamente como subproceso mediante referencias de cadena durante la etapa de visualización del pipeline global. |
| `src/assessment_engine/application/generate_mermaid_gantt.py` | **ACTIVE_LEAF** | 160 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/generate_tower_radar_chart.py` | **ACTIVE_LEAF** | 138 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/run_commercial_pipeline.py` | **ACTIVE_LEAF** | 62 | 0.0% | 0 | Punto de entrada CLI principal encargado de orquestar la ejecución de subprocesos para el flujo de evaluación comercial. |
| `src/assessment_engine/application/run_commercial_refiner.py` | **ACTIVE_LEAF** | 334 | 0.0% | 0 | Módulo trabajador de ejecución multi-agente invocado dinámicamente como paso de subproceso por el orquestador del pipeline comercial. |
| `src/assessment_engine/application/run_evidence_analyst.py` | **ACTIVE_LEAF** | 330 | 64.0% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_executive_annex_synthesizer.py` | **ACTIVE_LEAF** | 842 | 23.0% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_executive_refiner.py` | **ACTIVE_LEAF** | 282 | 63.6% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_global_pipeline.py` | **ACTIVE_LEAF** | 141 | 0.0% | 0 | Punto de entrada CLI de nivel superior que coordina extremo a extremo las etapas del pipeline estratégico global. |
| `src/assessment_engine/application/run_global_synthesizer_tobe.py` | **ACTIVE_LEAF** | 569 | 97.4% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_intelligence_harvesting.py` | **ACTIVE_LEAF** | 770 | 21.0% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_scoring.py` | **ACTIVE_LEAF** | 180 | 0.0% | 0 | Utilidad CLI independiente para el cálculo de puntuaciones y bandas de madurez, referenciada y ejecutada dinámicamente dentro del flujo del motor. |
| `src/assessment_engine/application/run_sota_researcher.py` | **ACTIVE_LEAF** | 162 | 33.3% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_strategic_orchestrator.py` | **ACTIVE_LEAF** | 69 | 0.0% | 2 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_tower_pipeline.py` | **ACTIVE_LEAF** | 577 | 0.0% | 0 | Es el punto de entrada principal (CLI) que orquesta el DAG de ejecución de todo el pipeline mediante subprocesos aislados. |
| `src/assessment_engine/application/tools/apex_dispatcher.py` | **ACTIVE_LEAF** | 513 | 0.0% | 0 | Herramienta CLI interactiva basada en Rich que funciona como punto de entrada autónomo para despachar tareas del backlog APEX. |
| `src/assessment_engine/application/tools/build_docs_site.py` | **ACTIVE_LEAF** | 183 | 0.0% | 0 | Script utilitario de línea de comandos (con argparse y directiva golden-path: ignore) diseñado para compilar el sitio de documentación. |
| `src/assessment_engine/application/tools/build_documentation_health_report.py` | **ACTIVE_LEAF** | 154 | 0.0% | 0 | Herramienta CLI de gobernanza (con argparse y directiva golden-path: ignore) utilizada como tarea de CI/CD para auditar la salud documental. |
| `src/assessment_engine/application/tools/check_docx_unresolved_placeholders.py` | **ACTIVE_LEAF** | 67 | 0.0% | 0 | Script CLI autónomo con punto de entrada explícito diseñado para validación de plantillas DOCX en pipelines CI/CD. |
| `src/assessment_engine/application/tools/check_vertex_ai_access.py` | **ACTIVE_LEAF** | 35 | 0.0% | 0 | Punto de entrada CLI con argparse que invoca diagnósticos de infraestructura para verificar acceso pre-flight a Vertex AI. |
| `src/assessment_engine/application/tools/compile_llms_full.py` | **ACTIVE_LEAF** | 104 | 75.0% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/corporate_project_aggregator.py` | **ACTIVE_LEAF** | 173 | 80.9% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/dynamic_tower_dispatcher.py` | **ACTIVE_LEAF** | 225 | 78.2% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/enforce_english_comments.py` | **ACTIVE_LEAF** | 398 | 0.0% | 0 | Herramienta CLI de gobernanza de código y linting asistido por LLM, configurada con shebang y argparse para ejecución directa. |
| `src/assessment_engine/application/tools/lint_documentation_style.py` | **ACTIVE_LEAF** | 64 | 0.0% | 0 | Herramienta CLI de gobernanza y CI/CD diseñada como punto de entrada independiente para auditar el estilo de la documentación. |
| `src/assessment_engine/application/tools/regenerate_smoke_artifacts.py` | **ACTIVE_LEAF** | 284 | 0.0% | 0 | Orquestador CLI de nivel superior que ejecuta la regeneración reproducible de artefactos de prueba consumiendo generate_smoke_data y el runtime del pipeline. |
| `src/assessment_engine/application/tools/run_golden_path_check.py` | **ACTIVE_LEAF** | 153 | 0.0% | 0 | Punto de entrada CLI diseñado para ejecutarse en pipelines de CI/CD para validar la adherencia arquitectónica mediante git diff, por lo que no requiere importadores internos. |
| `src/assessment_engine/application/tools/run_incremental_typecheck.py` | **ACTIVE_LEAF** | 87 | 0.0% | 0 | Punto de entrada CLI para la ejecución incremental de mypy en CI/CD que consume las funciones base de detección de cambios del quality gate. |
| `src/assessment_engine/application/tools/run_shadow_compilation.py` | **ACTIVE_LEAF** | 145 | 0.0% | 0 | Herramienta CLI de diagnóstico y renderizado para compilar variantes del AST a DOCX, referenciada externamente y conectada a los compiladores principales. |
| `src/assessment_engine/application/tools/sign_dossier.py` | **ACTIVE_LEAF** | 52 | 0.0% | 0 | Script operativo CLI con referencias activas en el proyecto encargado de la firma criptográfica o validación de payloads JSON de clientes. |
| `src/assessment_engine/application/tools/sync_sentinel.py` | **ACTIVE_LEAF** | 37 | 0.0% | 0 | Punto de entrada CLI para forzar manualmente la sincronización de la cola de StreamingSentinel y la reconstrucción del árbol RAG bajo demanda. |
| `src/assessment_engine/application/tools/validate_contracts_schemas.py` | **ACTIVE_LEAF** | 307 | 39.1% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/validate_documentation_governance.py` | **ACTIVE_LEAF** | 693 | 59.0% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/validate_documentation_snippets.py` | **ACTIVE_LEAF** | 157 | 79.8% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/validate_semantic_drift.py` | **ACTIVE_LEAF** | 213 | 30.7% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/verify_exact_text.py` | **ACTIVE_LEAF** | 106 | 0.0% | 0 | Herramienta CLI independiente para auditoría y verificación de fidelidad textual entre documentos DOCX generados. |
| `src/assessment_engine/application/tools/visualize_doc_map.py` | **ACTIVE_LEAF** | 264 | 81.7% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/validate_section_output.py` | **ACTIVE_LEAF** | 87 | 0.0% | 0 | Punto de entrada CLI con función main definida para validar reglas de negocio sobre los archivos JSON de salida por sección. |
| `src/assessment_engine/domain/prompts/blueprint_prompts.py` | **ACTIVE_LEAF** | 245 | 30.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/prompts/product_owner_prompts.py` | **ACTIVE_LEAF** | 162 | 33.3% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/asis.py` | **ACTIVE_LEAF** | 47 | 95.2% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/commercial.py` | **ACTIVE_LEAF** | 235 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/conclusion.py` | **ACTIVE_LEAF** | 41 | 63.0% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/evidence.py` | **ACTIVE_LEAF** | 114 | 98.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/gap.py` | **ACTIVE_LEAF** | 48 | 95.5% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/global_report.py` | **ACTIVE_LEAF** | 234 | 100.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/intelligence.py` | **ACTIVE_LEAF** | 481 | 32.4% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/risks.py` | **ACTIVE_LEAF** | 38 | 95.0% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/rubric.py` | **ACTIVE_LEAF** | 38 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/tobe.py` | **ACTIVE_LEAF** | 121 | 86.4% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/todo.py` | **ACTIVE_LEAF** | 38 | 79.3% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/agentic_benchmarker.py` | **ACTIVE_LEAF** | 508 | 58.3% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/apex_sentinel.py` | **ACTIVE_LEAF** | 111 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/mutation_probe.py` | **ACTIVE_LEAF** | 124 | 39.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/ai_safety_llm.py` | **ACTIVE_LEAF** | 150 | 50.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/ast_complexity.py` | **ACTIVE_LEAF** | 470 | 82.6% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/autonomous_ux_critic.py` | **ACTIVE_LEAF** | 416 | 0.0% | 0 | Sonda de auditoría autónoma basada en Playwright que actúa como hoja de ejecución o plugin (aunque presenta un bug de importación faltante para 'os'). |
| `src/assessment_engine/infrastructure/auditor/probes/code_hygiene.py` | **ACTIVE_LEAF** | 188 | 58.8% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/comment_quality.py` | **ACTIVE_LEAF** | 496 | 38.4% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/concurrency_stress.py` | **ACTIVE_LEAF** | 308 | 51.8% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/contract_drift.py` | **ACTIVE_LEAF** | 175 | 40.4% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/documentation_quality.py` | **ACTIVE_LEAF** | 190 | 28.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/hardcoded_artifacts.py` | **ACTIVE_LEAF** | 205 | 51.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/legal_compliance.py` | **ACTIVE_LEAF** | 179 | 76.1% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/mutation_gate.py` | **ACTIVE_LEAF** | 89 | 65.2% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/performance_finops.py` | **ACTIVE_LEAF** | 140 | 40.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/resilience_chaos.py` | **ACTIVE_LEAF** | 167 | 51.4% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/security_dast.py` | **ACTIVE_LEAF** | 136 | 24.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/security_sast.py` | **ACTIVE_LEAF** | 338 | 68.1% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/sre_observability.py` | **ACTIVE_LEAF** | 139 | 57.6% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/structural_smells.py` | **ACTIVE_LEAF** | 180 | 66.7% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/supply_chain.py` | **ACTIVE_LEAF** | 238 | 48.3% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/reporter.py` | **ACTIVE_LEAF** | 249 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/scanner.py` | **ACTIVE_LEAF** | 126 | 93.3% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/chassis/context.py` | **ACTIVE_LEAF** | 68 | 54.7% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/deterministic_enricher.py` | **ACTIVE_LEAF** | 188 | 93.5% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/doctor_agent.py` | **ACTIVE_LEAF** | 23 | 87.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/document_ai_client.py` | **ACTIVE_LEAF** | 38 | 100.0% | 2 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/infrastructure/epistemic_graph_service.py` | **ACTIVE_LEAF** | 421 | 89.5% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evidence_governance.py` | **ACTIVE_LEAF** | 257 | 55.9% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/ast_signature_guard.py` | **ACTIVE_LEAF** | 512 | 46.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/ast_signature_models.py` | **ACTIVE_LEAF** | 131 | 67.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/closure_tribunal.py` | **ACTIVE_LEAF** | 479 | 36.3% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/cognitive_arbiter.py` | **ACTIVE_LEAF** | 1171 | 10.3% | 0 | Orquestador principal de nivel superior del subsistema de evolución que coordina sub-módulos con cobertura de pruebas activa pese a no tener importadores directos. |
| `src/assessment_engine/infrastructure/evolution/complexity_guard.py` | **ACTIVE_LEAF** | 249 | 67.1% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/epistemic_distiller.py` | **ACTIVE_LEAF** | 902 | 21.8% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/reflexion_ledger.py` | **ACTIVE_LEAF** | 329 | 46.7% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/worktree_runner.py` | **ACTIVE_LEAF** | 139 | 62.7% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/http_client.py` | **ACTIVE_LEAF** | 113 | 88.4% | 1 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/infrastructure/liability_signer.py` | **ACTIVE_LEAF** | 40 | 85.7% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/mcda_sensitivity_engine.py` | **ACTIVE_LEAF** | 171 | 90.4% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/networkx_analyzer.py` | **ACTIVE_LEAF** | 151 | 81.5% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/parser_strategy.py` | **ACTIVE_LEAF** | 35 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/policies/archimate.py` | **ACTIVE_LEAF** | 51 | 77.6% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/policies/business_case.py` | **ACTIVE_LEAF** | 58 | 78.4% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/policies/client_sanitization.py` | **ACTIVE_LEAF** | 30 | 100.0% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/infrastructure/policies/deduplication.py` | **ACTIVE_LEAF** | 94 | 89.9% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/policies/fair_risk.py` | **ACTIVE_LEAF** | 900 | 82.6% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/policies/ot_perimeter.py` | **ACTIVE_LEAF** | 78 | 64.6% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/policies/reverse_traceability.py` | **ACTIVE_LEAF** | 146 | 80.8% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/policies/sequencing.py` | **ACTIVE_LEAF** | 47 | 95.3% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/policy_engine.py` | **ACTIVE_LEAF** | 83 | 81.4% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/product_owner_models.py` | **ACTIVE_LEAF** | 47 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/secrets_client.py` | **ACTIVE_LEAF** | 52 | 33.3% | 1 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/infrastructure/streaming_sentinel.py` | **ACTIVE_LEAF** | 424 | 72.4% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/vendor_intelligence.py` | **ACTIVE_LEAF** | 223 | 74.5% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/verification_agent.py` | **ACTIVE_LEAF** | 27 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/mcp_server.py` | **ACTIVE_LEAF** | 533 | 26.3% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/ports/document_compiler.py` | **ACTIVE_LEAF** | 8 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/ports/graph_analyzer.py` | **ACTIVE_LEAF** | 37 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/render_global_report_from_template.py` | **CANONICAL_CORE** | 1313 | 5.2% | 1 | Componente central de renderizado con cobertura de pruebas activa (5.2%), importado por otros módulos de reportes y fuertemente acoplado a los esquemas de dominio principales. |
| `src/assessment_engine/application/bootstrap/bootstrap_tower_from_matrix.py` | **CANONICAL_CORE** | 871 | 0.0% | 1 | Componente central de ingesta con alta densidad lógica (871 LOC) importado directamente para transformar matrices documentales en configuraciones de torres. |
| `src/assessment_engine/application/build_case_input.py` | **CANONICAL_CORE** | 319 | 13.1% | 1 | Módulo esencial del pipeline de entrada de datos con cobertura de pruebas activa (13.1%), dependencias de infraestructura y referencias directas en el sistema. |
| `src/assessment_engine/application/run_tower_blueprint_engine.py` | **CANONICAL_CORE** | 1042 | 0.0% | 0 | Motor central de procesamiento arquitectónico que concentra la lógica crítica de negocio, validación ontológica y sincronización con el grafo de conocimiento (Out-Degree: 18). |
| `src/assessment_engine/application/tools/actuarial_ledger_generator.py` | **CANONICAL_CORE** | 93 | 0.0% | 1 | Componente central activo (In-Degree: 1) encargado de generar el expediente de validación actuarial bajo la normativa SR 11-7. |
| `src/assessment_engine/application/tools/adversarial_consensus_engine.py` | **CANONICAL_CORE** | 236 | 0.0% | 1 | Motor algorítmico esencial (In-Degree: 1) que ejecuta el debate adversarial con modelos fundacionales para auditar controles de seguridad. |
| `src/assessment_engine/application/tools/context_tools.py` | **CANONICAL_CORE** | 206 | 8.6% | 1 | Componente activo del motor que provee herramientas de búsqueda y contexto, contando con importadores directos y cobertura de ejecución. |
| `src/assessment_engine/application/tools/financial_scale_calibrator.py` | **CANONICAL_CORE** | 304 | 0.0% | 1 | Módulo de dominio activo con referencias entrantes que estructura y calibra el riesgo financiero mediante Pydantic y GenAI. |
| `src/assessment_engine/application/tools/generate_smoke_data.py` | **CANONICAL_CORE** | 347 | 0.0% | 1 | Componente esencial del arnés de pruebas (importado por el orquestador de artefactos) que genera datasets sintéticos deterministas. |
| `src/assessment_engine/application/tools/run_incremental_quality_gate.py` | **CANONICAL_CORE** | 167 | 0.0% | 1 | Actúa simultáneamente como script de control de calidad incremental en CI y como módulo proveedor de utilidades git para otras herramientas de verificación. |
| `src/assessment_engine/application/tools/run_product_owner_orchestrator.py` | **CANONICAL_CORE** | 2227 | 11.2% | 0 | Orquestador principal de agentes de 2227 líneas con alta integración hacia la infraestructura del motor y cobertura dinámica activa en pruebas. |
| `src/assessment_engine/application/validate_tower_definition.py` | **CANONICAL_CORE** | 184 | 0.0% | 1 | Módulo esencial de validación de esquemas y consistencia jerárquica de torres, activamente importado en el pipeline. |
| `src/assessment_engine/domain/maturity_band.py` | **CANONICAL_CORE** | 76 | 86.4% | 8 | Módulo nuclear altamente acoplado (8 dependientes) y ejecutado dinámicamente (86.4%). |
| `src/assessment_engine/domain/ontology_registry.py` | **CANONICAL_CORE** | 49 | 0.0% | 1 | Componente central del dominio que gestiona y aplica las restricciones ontológicas del grafo de conocimiento. |
| `src/assessment_engine/domain/prompts/commercial_prompts.py` | **CANONICAL_CORE** | 61 | 0.0% | 1 | Módulo de dominio activo que suministra catálogos de referencia comercial y prompts utilizados por otros componentes del sistema. |
| `src/assessment_engine/domain/prompts/intelligence_prompts.py` | **CANONICAL_CORE** | 320 | 78.3% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (78.3%). |
| `src/assessment_engine/domain/schemas/annex_synthesis.py` | **CANONICAL_CORE** | 189 | 100.0% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/domain/schemas/ast.py` | **CANONICAL_CORE** | 211 | 100.0% | 26 | Módulo nuclear altamente acoplado (26 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/domain/schemas/blueprint.py` | **CANONICAL_CORE** | 540 | 100.0% | 5 | Módulo nuclear altamente acoplado (5 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/domain/schemas/common.py` | **CANONICAL_CORE** | 153 | 39.5% | 12 | Módulo nuclear altamente acoplado (12 dependientes) y ejecutado dinámicamente (39.5%). |
| `src/assessment_engine/infrastructure/ai_client.py` | **CANONICAL_CORE** | 339 | 65.6% | 13 | Módulo nuclear altamente acoplado (13 dependientes) y ejecutado dinámicamente (65.6%). |
| `src/assessment_engine/infrastructure/apex_models.py` | **CANONICAL_CORE** | 59 | 0.0% | 1 | Define contratos de datos estructurados con Pydantic que son importados activamente por otros componentes de la infraestructura. |
| `src/assessment_engine/infrastructure/auditor/models.py` | **CANONICAL_CORE** | 60 | 96.2% | 21 | Módulo nuclear altamente acoplado (21 dependientes) y ejecutado dinámicamente (96.2%). |
| `src/assessment_engine/infrastructure/auditor/probes/browser_accessibility.py` | **CANONICAL_CORE** | 183 | 16.0% | 1 | Sonda de validación de accesibilidad WCAG integrada activamente en el motor de auditoría y respaldada por cobertura de pruebas. |
| `src/assessment_engine/infrastructure/client_intelligence.py` | **CANONICAL_CORE** | 1265 | 17.6% | 9 | Módulo nuclear altamente acoplado (9 dependientes) y ejecutado dinámicamente (17.6%). |
| `src/assessment_engine/infrastructure/config_loader.py` | **CANONICAL_CORE** | 377 | 88.6% | 29 | Módulo nuclear altamente acoplado (29 dependientes) y ejecutado dinámicamente (88.6%). |
| `src/assessment_engine/infrastructure/contract_utils.py` | **CANONICAL_CORE** | 102 | 21.1% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (21.1%). |
| `src/assessment_engine/infrastructure/docx_render_utils.py` | **CANONICAL_CORE** | 1253 | 28.5% | 8 | Módulo nuclear altamente acoplado (8 dependientes) y ejecutado dinámicamente (28.5%). |
| `src/assessment_engine/infrastructure/entity_resolution.py` | **CANONICAL_CORE** | 128 | 0.0% | 1 | Motor de resolución semántica de entidades activamente referenciado para evitar duplicación de nodos en el grafo de arquitectura. |
| `src/assessment_engine/infrastructure/epistemic_extractor.py` | **CANONICAL_CORE** | 69 | 0.0% | 1 | Componente de infraestructura esencial que integra Vertex AI y Google ADK para la extracción estructurada de tripletas de conocimiento. |
| `src/assessment_engine/infrastructure/epistemic_graph.py` | **CANONICAL_CORE** | 268 | 80.9% | 15 | Módulo nuclear altamente acoplado (15 dependientes) y ejecutado dinámicamente (80.9%). |
| `src/assessment_engine/infrastructure/evidence_engine.py` | **CANONICAL_CORE** | 421 | 53.9% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (53.9%). |
| `src/assessment_engine/infrastructure/evolution/fault_localizer.py` | **CANONICAL_CORE** | 243 | 0.0% | 1 | Módulo especializado de diagnóstico SBFL (algoritmo Ochiai) requerido e importado directamente por el bucle de arbitraje evolutivo. |
| `src/assessment_engine/infrastructure/evolution/mcts_refactor_engine.py` | **CANONICAL_CORE** | 132 | 0.0% | 1 | Motor de búsqueda Monte Carlo sobre AST (RFC-019) integrado activamente en la tubería de transformación estructural de código. |
| `src/assessment_engine/infrastructure/evolution/mutation_ctf_probe.py` | **CANONICAL_CORE** | 299 | 18.3% | 1 | Validador determinista de pruebas de mutación AST importado directamente por el Cognitive Arbiter y respaldado por cobertura de tests. |
| `src/assessment_engine/infrastructure/evolution/trace_conditioner.py` | **CANONICAL_CORE** | 114 | 0.0% | 1 | Componente de telemetría forense W3C acoplado al registro de métricas del chasis y consumido por el sintetizador cognitivo. |
| `src/assessment_engine/infrastructure/genai_client.py` | **CANONICAL_CORE** | 88 | 88.6% | 19 | Módulo nuclear altamente acoplado (19 dependientes) y ejecutado dinámicamente (88.6%). |
| `src/assessment_engine/infrastructure/global_maturity_policy.py` | **CANONICAL_CORE** | 68 | 35.0% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (35.0%). |
| `src/assessment_engine/infrastructure/governance.py` | **CANONICAL_CORE** | 155 | 18.4% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (18.4%). |
| `src/assessment_engine/infrastructure/json_from_model.py` | **CANONICAL_CORE** | 63 | 84.2% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (84.2%). |
| `src/assessment_engine/infrastructure/localization.py` | **CANONICAL_CORE** | 253 | 81.0% | 19 | Módulo nuclear altamente acoplado (19 dependientes) y ejecutado dinámicamente (81.0%). |
| `src/assessment_engine/infrastructure/logger_config.py` | **CANONICAL_CORE** | 112 | 15.0% | 1 | Configurador transversal de observabilidad y logging estructurado JSON para Google Cloud con cobertura activa en tiempo de ejecución. |
| `src/assessment_engine/infrastructure/pipeline_runtime.py` | **CANONICAL_CORE** | 173 | 27.7% | 5 | Módulo nuclear altamente acoplado (5 dependientes) y ejecutado dinámicamente (27.7%). |
| `src/assessment_engine/infrastructure/policies/base.py` | **CANONICAL_CORE** | 15 | 100.0% | 8 | Módulo nuclear altamente acoplado (8 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/infrastructure/raptor_engine.py` | **CANONICAL_CORE** | 236 | 47.9% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (47.9%). |
| `src/assessment_engine/infrastructure/runtime_env.py` | **CANONICAL_CORE** | 196 | 46.2% | 8 | Módulo nuclear altamente acoplado (8 dependientes) y ejecutado dinámicamente (46.2%). |
| `src/assessment_engine/infrastructure/runtime_paths.py` | **CANONICAL_CORE** | 155 | 69.5% | 32 | Módulo nuclear altamente acoplado (32 dependientes) y ejecutado dinámicamente (69.5%). |
| `src/assessment_engine/infrastructure/text_utils.py` | **CANONICAL_CORE** | 162 | 97.2% | 22 | Módulo nuclear altamente acoplado (22 dependientes) y ejecutado dinámicamente (97.2%). |
| `src/assessment_engine/adapters/render_togaf_consolidated_asis.py` | **CONFIRMED_ORPHAN** | 840 | 0.0% | 0 | Script legacy sin cobertura, importadores ni referencias dinámicas (String Refs: 0) que no utiliza los esquemas de dominio de validación (Pydantic) del motor actual. |
| `src/assessment_engine/adapters/render_togaf_consolidated_tobe.py` | **CONFIRMED_ORPHAN** | 967 | 0.0% | 0 | Código muerto sin referencias estáticas ni dinámicas ni cobertura de tests, que además reimplementa localmente funciones de infraestructura como 'shade_cell'. |
| `src/assessment_engine/adapters/render_togaf_consolidated_todo.py` | **CONFIRMED_ORPHAN** | 331 | 0.0% | 0 | Módulo huérfano sin referencias ni cobertura de pruebas, desconectado de la capa de dominio y con duplicación de lógica de bajo nivel OOXML ('shade_cell'). |
| `src/assessment_engine/adapters/tobe_document_builder.py` | **CONFIRMED_ORPHAN** | 130 | 0.0% | 0 | Módulo completamente aislado (In-Degree: 0, Out-Degree: 0, String Refs: 0) y sin cobertura de pruebas que realiza agregaciones redundantes desconectadas del grafo principal. |
| `src/assessment_engine/application/generate_fair_heatmap.py` | **CONFIRMED_ORPHAN** | 145 | 0.0% | 0 | Módulo de visualización aislado sin referencias de cadena ni importadores activos en ninguno de los pipelines de ejecución. |
| `src/assessment_engine/application/run_global_synthesizer.py` | **CONFIRMED_ORPHAN** | 186 | 0.0% | 0 | Script de síntesis desconectado que define esquemas inline redundantes y carece tanto de importadores como de invocaciones por subproceso (0 referencias). |
| `src/assessment_engine/application/tools/audit_tower_annex.py` | **CONFIRMED_ORPHAN** | 252 | 0.0% | 0 | Script desconectado (In-Degree: 0, String Refs: 0) para inspeccionar XML de archivos DOCX sin referencias en el motor de ejecución. |
| `src/assessment_engine/application/tools/check_xml.py` | **CONFIRMED_ORPHAN** | 37 | 0.0% | 0 | Script de diagnóstico ad-hoc sin importadores, sin cobertura de tests y sin interfaz CLI estructurada. |
| `src/assessment_engine/application/tools/compare_documents.py` | **CONFIRMED_ORPHAN** | 141 | 0.0% | 0 | Utilidad de inspección manual con heurísticas hardcodeadas que no es invocada por ningún módulo ni pipeline. |
| `src/assessment_engine/application/tools/compare_docx_xml.py` | **CONFIRMED_ORPHAN** | 85 | 0.0% | 0 | Código muerto de comparación XML con artefactos de autogeneración corruptos en el docstring y cero referencias en el grafo. |
| `src/assessment_engine/application/tools/context_grounder.py` | **CONFIRMED_ORPHAN** | 46 | 0.0% | 0 | Módulo de extracción de texto truncado e incompleto que ha quedado huérfano sin consumidores ni pruebas asociadas. |
| `src/assessment_engine/application/tools/ingest_eurovision.py` | **CONFIRMED_ORPHAN** | 23 | 0.0% | 0 | Script de ingesta ad-hoc roto que utiliza rutas de importación obsoletas ('from src.infrastructure...') y carece de referencias en el sistema. |
| `src/assessment_engine/application/tools/repair_tower_payload_scores.py` | **CONFIRMED_ORPHAN** | 389 | 0.0% | 0 | Script utilitario de reparación sin referencias entrantes, sin cobertura de pruebas y con signos evidentes de corrupción por generación automática (imports duplicados y docstrings malformados). |
| `src/assessment_engine/application/tools/test_tui.py` | **CONFIRMED_ORPHAN** | 78 | 0.0% | 0 | Script prototipo de interfaz gráfica en consola (Rich) sin integraciones entrantes ni referencias en el motor principal. |
| `src/assessment_engine/domain/prompts/conclusion_prompts.py` | **CONFIRMED_ORPHAN** | 176 | 0.0% | 0 | Módulo generador de prompts para conclusiones con grado de entrada cero y sin referencias dinámicas, indicando código muerto. |
| `src/assessment_engine/domain/prompts/gap_prompts.py` | **CONFIRMED_ORPHAN** | 140 | 0.0% | 0 | Módulo de plantillas de prompts para análisis GAP completamente desconectado del flujo de ejecución actual (In-Degree: 0). |
| `src/assessment_engine/domain/prompts/global_prompts.py` | **CONFIRMED_ORPHAN** | 117 | 0.0% | 0 | Módulo de plantillas de prompts estáticos completamente desconectado del grafo de ejecución (0 importadores, 0 referencias y 0% de cobertura). |
| `src/assessment_engine/domain/prompts/section_prompts.py` | **CONFIRMED_ORPHAN** | 165 | 0.0% | 0 | Generador de prompts para secciones sin consumidores activos ni cobertura de pruebas, indicando una refactorización o abandono del flujo. |
| `src/assessment_engine/domain/prompts/tobe_prompts.py` | **CONFIRMED_ORPHAN** | 161 | 0.0% | 0 | Repositorio de prompts TO-BE aislado sin referencias entrantes ni salientes en todo el motor de arquitectura. |
| `src/assessment_engine/domain/prompts/todo_prompts.py` | **CONFIRMED_ORPHAN** | 153 | 0.0% | 0 | Módulo de generación de prompts TO-DO huérfano, sin llamadas activas ni cobertura en las pruebas del sistema. |
| `src/assessment_engine/infrastructure/editorial_autofix.py` | **CONFIRMED_ORPHAN** | 40 | 0.0% | 0 | Código muerto sin importadores cuya implementación interna (_walk) es un no-op que clona estructuras recursivamente sin aplicar ninguna transformación real. |
| `src/assessment_engine/infrastructure/remediation_playbooks.py` | **CONFIRMED_ORPHAN** | 45 | 0.0% | 0 | Carece por completo de referencias entrantes, salientes o cobertura de pruebas, conteniendo únicamente utilidades genéricas de subprocesos Git desconectadas del motor de evaluación. |
| `src/assessment_engine/infrastructure/review_resilience.py` | **CONFIRMED_ORPHAN** | 113 | 0.0% | 0 | Módulo completamente aislado (0 grados de entrada/salida y 0% de cobertura) que además contiene código roto e inalcanzable como la llamada inválida a `{}.model_dump()`. |
| `src/assessment_engine/application/tools/check_docx_quality_flags.py` | **SHADOW_DUPLICATE** | 92 | 0.0% | 0 | Duplica exactamente la validación de expresiones regulares de plantillas rota que ya realiza audit_tower_annex.py pero usando python-docx, además de estar huérfano. |
| `src/assessment_engine/application/tools/generate_inputs.py` | **SHADOW_DUPLICATE** | 39 | 0.0% | 0 | Script procedural obsoleto con valores hardcodeados para 'ivirma' que ha sido completamente reemplazado por la versión determinista y estructurada en generate_smoke_data.py. |
| `src/assessment_engine/application/tools/ingest_molins.py` | **SHADOW_DUPLICATE** | 32 | 0.0% | 0 | Clon de script de ingesta con rutas hardcodeadas para un cliente específico, duplicando la lógica de inicialización del Evidence y Raptor Engine en lugar de usar un CLI parametrizado. |
| `src/assessment_engine/application/tools/ingest_redeia.py` | **SHADOW_DUPLICATE** | 26 | 0.0% | 0 | Duplicado exacto del flujo de ingesta manual adaptado para el cliente 'redeia', violando el principio DRY frente a otros scripts de ingesta idénticos. |
| `src/assessment_engine/infrastructure/maturity_band.py` | **SHADOW_DUPLICATE** | 62 | 0.0% | 0 | Define constantes y lógica de negocio central (bandas de madurez) mal ubicadas en la capa de infraestructura que tienen 0 importadores directos pero 10 referencias por string, lo que indica que fue desplazado por una implementación canónica en la capa de dominio. |
