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
# 🏛️ Auditoría Neuro-Simbólica de la Base de Código

**Fecha:** Octubre 2026 | **Metodología:** Topología AST (NetworkX) + Trazabilidad Dinámica (`coverage.py`) + Árbitro Cognitivo (`gemini-4-argon`)

## 1. Resumen Ejecutivo de Salud del Código

- **Total de Archivos Auditados:** 174
- **Núcleo Canónico (Vital):** 46 (26.4%)
- **Hojas Activas / Adaptadores:** 127 (73.0%)
- **Módulos Sombra (Duplicados / Candidatos a Fusión):** 0
- **Huérfanos Confirmados (Código Muerto / Purga Segura):** 1

## 2. ⚠️ Huérfanos Confirmados (Blast Radius = 0)

| Archivo | LOC | Cobertura | In-Degree | Razón Técnica de Purga |
| :--- | :---: | :---: | :---: | :--- |
| `src/assessment_engine/application/validate_section_output.py` | 87 | 0.0% | 0 | Script obsoleto sin importadores ni cobertura que contiene rutas estáticas acopladas a un caso específico ('working/client/T5') en lugar de integrarse en el pipeline dinámico. |

## 4. 📋 Inventario Exhaustivo Archivo a Archivo

| Archivo | Veredicto | LOC | Cobertura | In-Deg | Dictamen Funcional |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `src/assessment_engine/adapters/compile_asis_docx_from_modules.py` | **ACTIVE_LEAF** | 2856 | 67.7% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/compilers/docx_compiler.py` | **ACTIVE_LEAF** | 565 | 79.2% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/compilers/payload_to_ast.py` | **ACTIVE_LEAF** | 1884 | 69.8% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/generate_asis_markdown_modules.py` | **ACTIVE_LEAF** | 1060 | 37.2% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/render_commercial_report.py` | **ACTIVE_LEAF** | 782 | 0.0% | 0 | Es un adaptador de salida final para renderizar el reporte comercial en DOCX consumiendo esquemas de dominio e infraestructura. |
| `src/assessment_engine/adapters/render_lineage_portal.py` | **ACTIVE_LEAF** | 138 | 0.0% | 0 | Actúa como script de generación estática de artefactos web (portal HTML Jinja2) invocado como hoja final del pipeline. |
| `src/assessment_engine/adapters/render_togaf_asis_annex.py` | **ACTIVE_LEAF** | 946 | 78.8% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/render_tower_annex_from_template.py` | **ACTIVE_LEAF** | 854 | 0.0% | 0 | Punto de salida específico encargado de ensamblar y exportar el documento anexo de cada torre a partir de plantillas DOCX. |
| `src/assessment_engine/adapters/render_tower_blueprint.py` | **ACTIVE_LEAF** | 1363 | 7.2% | 0 | Adaptador terminal de renderizado de blueprints por torre con cobertura dinámica verificada en pruebas de integración. |
| `src/assessment_engine/adapters/render_web_presentation.py` | **ACTIVE_LEAF** | 411 | 21.7% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/bootstrap/bootstrap_all_towers.py` | **ACTIVE_LEAF** | 125 | 0.0% | 0 | Script CLI de orquestación (`argparse`) diseñado como punto de entrada para inicializar en lote todas las torres del motor. |
| `src/assessment_engine/application/build_evidence_ledger.py` | **ACTIVE_LEAF** | 211 | 77.2% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/cli.py` | **ACTIVE_LEAF** | 382 | 0.0% | 0 | Punto de entrada principal de consola (CLI) que unifica y orquesta la ejecución end-to-end de todos los pipelines del sistema. |
| `src/assessment_engine/application/export_graph_state.py` | **ACTIVE_LEAF** | 291 | 0.0% | 0 | Script de exportación de estado (DigitalTwinExporter) que consolida y empaqueta la topología del grafo y métricas estratégicas para consumidores externos. |
| `src/assessment_engine/application/generate_executive_roadmap_image.py` | **ACTIVE_LEAF** | 148 | 0.0% | 0 | Script de renderizado visual independiente invocado dinámicamente para generar gráficos Gantt ejecutivos en PNG mediante Matplotlib. |
| `src/assessment_engine/application/generate_global_radar_chart.py` | **ACTIVE_LEAF** | 148 | 0.0% | 0 | Utilidad de visualización ejecutada como hoja del pipeline para renderizar gráficos de radar de madurez global desde payloads JSON. |
| `src/assessment_engine/application/generate_tower_radar_chart.py` | **ACTIVE_LEAF** | 138 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/run_commercial_pipeline.py` | **ACTIVE_LEAF** | 62 | 0.0% | 0 | Punto de entrada de línea de comandos encargado de orquestar secuencialmente los subprocesos del flujo comercial y generación del Account Action Plan. |
| `src/assessment_engine/application/run_evidence_analyst.py` | **ACTIVE_LEAF** | 330 | 64.0% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_executive_annex_synthesizer.py` | **ACTIVE_LEAF** | 842 | 23.0% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_executive_refiner.py` | **ACTIVE_LEAF** | 282 | 63.6% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_global_pipeline.py` | **ACTIVE_LEAF** | 141 | 0.0% | 0 | Punto de entrada CLI principal que orquesta la ejecución end-to-end del pipeline global mediante subprocesos aislados. |
| `src/assessment_engine/application/run_global_synthesizer_tobe.py` | **ACTIVE_LEAF** | 569 | 97.4% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_intelligence_harvesting.py` | **ACTIVE_LEAF** | 845 | 21.0% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_scoring.py` | **ACTIVE_LEAF** | 180 | 0.0% | 0 | Script ejecutable invocado por el orquestador (referenciado por string) para el cálculo determinista de puntuaciones y bandas de madurez. |
| `src/assessment_engine/application/run_sota_researcher.py` | **ACTIVE_LEAF** | 162 | 33.3% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_strategic_orchestrator.py` | **ACTIVE_LEAF** | 69 | 0.0% | 2 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_tower_blueprint_engine.py` | **ACTIVE_LEAF** | 1042 | 0.0% | 0 | Motor de ejecución invocado como subproceso por el pipeline de torres para el análisis con agentes IA y sincronización con el grafo de conocimiento. |
| `src/assessment_engine/application/run_tower_pipeline.py` | **ACTIVE_LEAF** | 584 | 0.0% | 0 | Orquestador CLI que define y ejecuta el DAG de etapas en subprocesos aislados para el procesamiento individual de cada torre. |
| `src/assessment_engine/application/tools/apex_dispatcher.py` | **ACTIVE_LEAF** | 513 | 0.0% | 0 | Herramienta CLI interactiva autónoma (basada en Rich) que actúa como punto de entrada para la gestión y despacho de tareas de mejora continua (APEX). |
| `src/assessment_engine/application/tools/build_docs_site.py` | **ACTIVE_LEAF** | 183 | 0.0% | 0 | Script utilitario de línea de comandos para el renderizado y construcción estática del sitio de documentación del proyecto. |
| `src/assessment_engine/application/tools/build_documentation_health_report.py` | **ACTIVE_LEAF** | 154 | 0.0% | 0 | Script CLI autónomo de gobernanza que evalúa y genera reportes de salud de la documentación del repositorio. |
| `src/assessment_engine/application/tools/check_docx_unresolved_placeholders.py` | **ACTIVE_LEAF** | 67 | 0.0% | 0 | Utilidad de validación de línea de comandos para pipelines CI/CD encargada de detectar marcadores no resueltos en documentos DOCX generados. |
| `src/assessment_engine/application/tools/check_vertex_ai_access.py` | **ACTIVE_LEAF** | 35 | 0.0% | 0 | Punto de entrada CLI para ejecutar verificaciones pre-flight de credenciales y conectividad hacia Google Vertex AI. |
| `src/assessment_engine/application/tools/compile_llms_full.py` | **ACTIVE_LEAF** | 104 | 75.0% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/corporate_project_aggregator.py` | **ACTIVE_LEAF** | 173 | 80.9% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/dynamic_tower_dispatcher.py` | **ACTIVE_LEAF** | 225 | 78.2% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/enforce_english_comments.py` | **ACTIVE_LEAF** | 398 | 0.0% | 0 | Herramienta CLI de mantenimiento y linting asistido por LLM para estandarizar comentarios y docstrings al idioma inglés. |
| `src/assessment_engine/application/tools/generate_smoke_data.py` | **ACTIVE_LEAF** | 347 | 0.0% | 1 | Generador determinista de datos sintéticos utilizado tanto por línea de comandos como por suites de pruebas de humo (smoke tests). |
| `src/assessment_engine/application/tools/ingest_documents.py` | **ACTIVE_LEAF** | 79 | 0.0% | 0 | Script ejecutable que actúa como punto de entrada para el pipeline de ingesta de documentos hacia los motores Evidence y Raptor. |
| `src/assessment_engine/application/tools/lint_documentation_style.py` | **ACTIVE_LEAF** | 64 | 0.0% | 0 | Script CLI de gobernanza y linting de documentación diseñado para ser invocado desde pipelines CI/CD sin importadores internos. |
| `src/assessment_engine/application/tools/regenerate_smoke_artifacts.py` | **ACTIVE_LEAF** | 284 | 0.0% | 0 | Herramienta CLI de orquestación para regenerar artefactos de pruebas de humo mediante la invocación directa del entorno de ejecución. |
| `src/assessment_engine/application/tools/run_golden_path_check.py` | **ACTIVE_LEAF** | 153 | 0.0% | 0 | Script CLI de validación arquitectónica para flujos de integración continua que verifica marcadores estructurales en nuevos commits de Git. |
| `src/assessment_engine/application/tools/run_incremental_typecheck.py` | **ACTIVE_LEAF** | 87 | 0.0% | 0 | Punto de entrada CLI para ejecutar chequeos de tipos incrementales con mypy basados en los diffs provistos por el quality gate. |
| `src/assessment_engine/application/tools/run_product_owner_orchestrator.py` | **ACTIVE_LEAF** | 2227 | 11.2% | 0 | Orquestador principal de alto nivel (CLI) con amplia integración de infraestructura y cobertura de pruebas activa. |
| `src/assessment_engine/application/tools/run_shadow_compilation.py` | **ACTIVE_LEAF** | 145 | 0.0% | 0 | Herramienta CLI de diagnóstico y renderizado que utiliza los compiladores AST/DOCX para aislar fallos en la generación de documentos. |
| `src/assessment_engine/application/tools/sign_dossier.py` | **ACTIVE_LEAF** | 52 | 0.0% | 0 | Utilidad CLI operativa para la firma criptográfica manual de archivos JSON de dossiers utilizando el motor de inteligencia de clientes. |
| `src/assessment_engine/application/tools/sync_sentinel.py` | **ACTIVE_LEAF** | 37 | 0.0% | 0 | Es un punto de entrada CLI válido para disparar manualmente la sincronización bajo demanda de la cola StreamingSentinel y la reconstrucción del árbol Raptor RAG. |
| `src/assessment_engine/application/tools/validate_contracts_schemas.py` | **ACTIVE_LEAF** | 307 | 39.1% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/validate_documentation_governance.py` | **ACTIVE_LEAF** | 693 | 59.0% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/validate_documentation_snippets.py` | **ACTIVE_LEAF** | 157 | 79.8% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/validate_semantic_drift.py` | **ACTIVE_LEAF** | 213 | 30.7% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/verify_exact_text.py` | **ACTIVE_LEAF** | 106 | 0.0% | 0 | Funciona como una herramienta utilitaria de auditoría y control de calidad para comparar la fidelidad textual entre documentos DOCX generados. |
| `src/assessment_engine/application/tools/visualize_doc_map.py` | **ACTIVE_LEAF** | 264 | 81.7% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/prompts/blueprint_prompts.py` | **ACTIVE_LEAF** | 245 | 30.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/prompts/product_owner_prompts.py` | **ACTIVE_LEAF** | 162 | 33.3% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/asis.py` | **ACTIVE_LEAF** | 47 | 95.2% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/commercial.py` | **ACTIVE_LEAF** | 232 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/conclusion.py` | **ACTIVE_LEAF** | 41 | 63.0% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/evidence.py` | **ACTIVE_LEAF** | 114 | 98.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/gap.py` | **ACTIVE_LEAF** | 48 | 95.5% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/global_report.py` | **ACTIVE_LEAF** | 254 | 100.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
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
| `src/assessment_engine/infrastructure/evidence_engine.py` | **ACTIVE_LEAF** | 421 | 53.9% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evidence_governance.py` | **ACTIVE_LEAF** | 257 | 55.9% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/ast_signature_guard.py` | **ACTIVE_LEAF** | 512 | 46.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/ast_signature_models.py` | **ACTIVE_LEAF** | 131 | 67.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/closure_tribunal.py` | **ACTIVE_LEAF** | 479 | 36.3% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/cognitive_arbiter.py` | **ACTIVE_LEAF** | 1171 | 10.3% | 0 | Orquestador principal de alto nivel (Out-Degree: 12) con cobertura de tests activa que actúa como punto de entrada del bucle de evolución de código aunque no tenga importadores directos. |
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
| `src/assessment_engine/infrastructure/raptor_engine.py` | **ACTIVE_LEAF** | 236 | 47.9% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/secrets_client.py` | **ACTIVE_LEAF** | 52 | 33.3% | 1 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/infrastructure/streaming_sentinel.py` | **ACTIVE_LEAF** | 424 | 72.4% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/vendor_intelligence.py` | **ACTIVE_LEAF** | 223 | 74.5% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/verification_agent.py` | **ACTIVE_LEAF** | 27 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/mcp_server.py` | **ACTIVE_LEAF** | 533 | 26.3% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/ports/document_compiler.py` | **ACTIVE_LEAF** | 8 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/ports/graph_analyzer.py` | **ACTIVE_LEAF** | 37 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/render_global_report_from_template.py` | **CANONICAL_CORE** | 1565 | 5.2% | 1 | Además de renderizar el reporte global con cobertura de tests activa, provee utilidades de formato reutilizadas directamente por otros adaptadores. |
| `src/assessment_engine/application/bootstrap/bootstrap_tower_from_matrix.py` | **CANONICAL_CORE** | 871 | 0.0% | 1 | Contiene la lógica central de extracción XML/DOCX e inicialización de matrices de configuración, siendo importado por el orquestador de bootstrap. |
| `src/assessment_engine/application/build_case_input.py` | **CANONICAL_CORE** | 319 | 13.1% | 1 | Componente crítico de ingesta en la capa de aplicación con cobertura de tests activa e importadores directos en el pipeline. |
| `src/assessment_engine/application/build_global_report_payload.py` | **CANONICAL_CORE** | 638 | 0.0% | 0 | Encapsula la lógica de negocio central para construir el payload global de reportes integrando el grafo epistémico y políticas de madurez, invocado vía subprocess. |
| `src/assessment_engine/application/generate_mermaid_gantt.py` | **CANONICAL_CORE** | 160 | 0.0% | 1 | Módulo funcional importado directamente por otros componentes del sistema (In-Degree: 1) para calcular dependencias de olas y renderizar diagramas Gantt vía Mermaid. |
| `src/assessment_engine/application/run_commercial_refiner.py` | **CANONICAL_CORE** | 334 | 0.0% | 0 | Motor de procesamiento multi-agente en Vertex AI esencial para la refinación de datos comerciales, ejecutado como paso modular por run_commercial_pipeline. |
| `src/assessment_engine/application/tools/actuarial_ledger_generator.py` | **CANONICAL_CORE** | 93 | 0.0% | 1 | Módulo de lógica de negocio importado activamente para la generación de expedientes de auditoría actuarial bajo la normativa SR 11-7. |
| `src/assessment_engine/application/tools/adversarial_consensus_engine.py` | **CANONICAL_CORE** | 236 | 0.0% | 1 | Componente esencial importado en el motor principal para ejecutar debates de consenso adversarial y evaluar la eficacia de controles de seguridad. |
| `src/assessment_engine/application/tools/context_tools.py` | **CANONICAL_CORE** | 206 | 8.6% | 1 | Módulo de herramientas de búsqueda y contexto importado activamente en el motor y con cobertura de pruebas dinámicas. |
| `src/assessment_engine/application/tools/financial_scale_calibrator.py` | **CANONICAL_CORE** | 309 | 0.0% | 1 | Componente de lógica de dominio importado por el sistema para la calibración estructurada de magnitudes de riesgo financiero. |
| `src/assessment_engine/application/tools/run_incremental_quality_gate.py` | **CANONICAL_CORE** | 167 | 0.0% | 1 | Módulo base de control de calidad incremental que además provee funciones esenciales de análisis de Git a otras herramientas del sistema. |
| `src/assessment_engine/application/validate_tower_definition.py` | **CANONICAL_CORE** | 203 | 0.0% | 1 | Módulo de validación estructural importado activamente en el sistema para garantizar la integridad de los esquemas de definición de torres. |
| `src/assessment_engine/domain/maturity_band.py` | **CANONICAL_CORE** | 76 | 86.4% | 8 | Módulo nuclear altamente acoplado (8 dependientes) y ejecutado dinámicamente (86.4%). |
| `src/assessment_engine/domain/ontology_registry.py` | **CANONICAL_CORE** | 49 | 0.0% | 1 | Componente central del dominio que gestiona y aplica las restricciones ontológicas (nodos y predicados) del grafo de conocimiento. |
| `src/assessment_engine/domain/prompts/commercial_prompts.py` | **CANONICAL_CORE** | 61 | 0.0% | 1 | Repositorio activo de conocimiento de dominio y catálogos de referencia utilizado en la generación de propuestas comerciales. |
| `src/assessment_engine/domain/prompts/intelligence_prompts.py` | **CANONICAL_CORE** | 320 | 78.3% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (78.3%). |
| `src/assessment_engine/domain/schemas/annex_synthesis.py` | **CANONICAL_CORE** | 189 | 100.0% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/domain/schemas/ast.py` | **CANONICAL_CORE** | 211 | 100.0% | 26 | Módulo nuclear altamente acoplado (26 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/domain/schemas/blueprint.py` | **CANONICAL_CORE** | 540 | 100.0% | 5 | Módulo nuclear altamente acoplado (5 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/domain/schemas/common.py` | **CANONICAL_CORE** | 153 | 39.5% | 12 | Módulo nuclear altamente acoplado (12 dependientes) y ejecutado dinámicamente (39.5%). |
| `src/assessment_engine/infrastructure/ai_client.py` | **CANONICAL_CORE** | 339 | 65.6% | 12 | Módulo nuclear altamente acoplado (12 dependientes) y ejecutado dinámicamente (65.6%). |
| `src/assessment_engine/infrastructure/apex_models.py` | **CANONICAL_CORE** | 59 | 0.0% | 1 | Define los contratos de datos estructurados con Pydantic indispensables para la orquestación y deliberación de agentes en el motor Apex. |
| `src/assessment_engine/infrastructure/auditor/models.py` | **CANONICAL_CORE** | 60 | 96.2% | 20 | Módulo nuclear altamente acoplado (20 dependientes) y ejecutado dinámicamente (96.2%). |
| `src/assessment_engine/infrastructure/auditor/probes/browser_accessibility.py` | **CANONICAL_CORE** | 183 | 16.0% | 1 | Sonda de auditoría activa, integrada y con cobertura de tests dinámicos que verifica el cumplimiento de estándares de accesibilidad WCAG 2.2 AA. |
| `src/assessment_engine/infrastructure/client_intelligence.py` | **CANONICAL_CORE** | 1265 | 17.6% | 9 | Módulo nuclear altamente acoplado (9 dependientes) y ejecutado dinámicamente (17.6%). |
| `src/assessment_engine/infrastructure/config_loader.py` | **CANONICAL_CORE** | 377 | 88.6% | 25 | Módulo nuclear altamente acoplado (25 dependientes) y ejecutado dinámicamente (88.6%). |
| `src/assessment_engine/infrastructure/contract_utils.py` | **CANONICAL_CORE** | 102 | 21.1% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (21.1%). |
| `src/assessment_engine/infrastructure/docx_render_utils.py` | **CANONICAL_CORE** | 1253 | 28.5% | 7 | Módulo nuclear altamente acoplado (7 dependientes) y ejecutado dinámicamente (28.5%). |
| `src/assessment_engine/infrastructure/entity_resolution.py` | **CANONICAL_CORE** | 128 | 0.0% | 1 | Componente de infraestructura esencial para la deduplicación semántica y resolución de entidades en la construcción del grafo de conocimiento. |
| `src/assessment_engine/infrastructure/epistemic_extractor.py` | **CANONICAL_CORE** | 69 | 0.0% | 1 | Módulo central para la extracción estructurada de tripletas epistémicas mediante agentes de Vertex AI y validación con Pydantic. |
| `src/assessment_engine/infrastructure/epistemic_graph.py` | **CANONICAL_CORE** | 268 | 80.9% | 15 | Módulo nuclear altamente acoplado (15 dependientes) y ejecutado dinámicamente (80.9%). |
| `src/assessment_engine/infrastructure/evolution/fault_localizer.py` | **CANONICAL_CORE** | 243 | 0.0% | 1 | Subsistema algorítmico (SBFL/Ochiai) requerido por el motor de evolución para el aislamiento determinista de fallos. |
| `src/assessment_engine/infrastructure/evolution/mcts_refactor_engine.py` | **CANONICAL_CORE** | 132 | 0.0% | 1 | Motor de búsqueda Monte Carlo sobre AST referenciado activamente para transformaciones estructurales de código sin regresiones. |
| `src/assessment_engine/infrastructure/evolution/mutation_ctf_probe.py` | **CANONICAL_CORE** | 299 | 18.3% | 1 | Puerta de certificación determinista con cobertura activa e importada directamente por el Cognitive Arbiter para pruebas de mutación AST. |
| `src/assessment_engine/infrastructure/evolution/trace_conditioner.py` | **CANONICAL_CORE** | 114 | 0.0% | 1 | Componente de diagnóstico que procesa telemetría W3C y cuellos de botella de latencia para alimentar al sintetizador cognitivo. |
| `src/assessment_engine/infrastructure/genai_client.py` | **CANONICAL_CORE** | 88 | 88.6% | 18 | Módulo nuclear altamente acoplado (18 dependientes) y ejecutado dinámicamente (88.6%). |
| `src/assessment_engine/infrastructure/global_maturity_policy.py` | **CANONICAL_CORE** | 68 | 35.0% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (35.0%). |
| `src/assessment_engine/infrastructure/governance.py` | **CANONICAL_CORE** | 155 | 18.4% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (18.4%). |
| `src/assessment_engine/infrastructure/json_from_model.py` | **CANONICAL_CORE** | 63 | 84.2% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (84.2%). |
| `src/assessment_engine/infrastructure/localization.py` | **CANONICAL_CORE** | 253 | 81.0% | 18 | Módulo nuclear altamente acoplado (18 dependientes) y ejecutado dinámicamente (81.0%). |
| `src/assessment_engine/infrastructure/logger_config.py` | **CANONICAL_CORE** | 112 | 15.0% | 1 | Configuración transversal de observabilidad y logging estructurado JSON para Google Cloud Ops con cobertura de pruebas activa. |
| `src/assessment_engine/infrastructure/pipeline_runtime.py` | **CANONICAL_CORE** | 173 | 27.7% | 5 | Módulo nuclear altamente acoplado (5 dependientes) y ejecutado dinámicamente (27.7%). |
| `src/assessment_engine/infrastructure/policies/base.py` | **CANONICAL_CORE** | 15 | 100.0% | 8 | Módulo nuclear altamente acoplado (8 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/infrastructure/runtime_env.py` | **CANONICAL_CORE** | 196 | 46.2% | 8 | Módulo nuclear altamente acoplado (8 dependientes) y ejecutado dinámicamente (46.2%). |
| `src/assessment_engine/infrastructure/runtime_paths.py` | **CANONICAL_CORE** | 155 | 69.5% | 30 | Módulo nuclear altamente acoplado (30 dependientes) y ejecutado dinámicamente (69.5%). |
| `src/assessment_engine/infrastructure/text_utils.py` | **CANONICAL_CORE** | 162 | 97.2% | 18 | Módulo nuclear altamente acoplado (18 dependientes) y ejecutado dinámicamente (97.2%). |
| `src/assessment_engine/application/validate_section_output.py` | **CONFIRMED_ORPHAN** | 87 | 0.0% | 0 | Script obsoleto sin importadores ni cobertura que contiene rutas estáticas acopladas a un caso específico ('working/client/T5') en lugar de integrarse en el pipeline dinámico. |
