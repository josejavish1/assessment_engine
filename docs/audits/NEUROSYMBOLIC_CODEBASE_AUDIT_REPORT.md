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

- **Total de Archivos Auditados:** 176
- **Núcleo Canónico (Vital):** 50 (28.4%)
- **Hojas Activas / Adaptadores:** 124 (70.5%)
- **Módulos Sombra (Duplicados / Candidatos a Fusión):** 0
- **Huérfanos Confirmados (Código Muerto / Purga Segura):** 2

## 2. ⚠️ Huérfanos Confirmados (Blast Radius = 0)

| Archivo | LOC | Cobertura | In-Degree | Razón Técnica de Purga |
| :--- | :---: | :---: | :---: | :--- |
| `src/assessment_engine/application/tools/verify_exact_text.py` | 106 | 0.0% | 0 | Script de verificación ad-hoc con rutas estáticas codificadas, sin importadores ni integración con el motor central, constituyendo deuda técnica desechable. |
| `src/assessment_engine/application/validate_section_output.py` | 87 | 0.0% | 0 | Validador obsoleto desconectado del pipeline principal (In-Degree 0) que depende de directorios estáticos de prueba ('working/client/T5'). |

## 4. 📋 Inventario Exhaustivo Archivo a Archivo

| Archivo | Veredicto | LOC | Cobertura | In-Deg | Dictamen Funcional |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `src/assessment_engine/adapters/compile_asis_docx_from_modules.py` | **ACTIVE_LEAF** | 2884 | 67.7% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/compilers/ast_table_builders.py` | **ACTIVE_LEAF** | 241 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/compilers/docx_compiler.py` | **ACTIVE_LEAF** | 565 | 79.2% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/compilers/payload_to_ast.py` | **ACTIVE_LEAF** | 1236 | 69.8% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/generate_asis_markdown_modules.py` | **ACTIVE_LEAF** | 1072 | 37.2% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/render_commercial_report.py` | **ACTIVE_LEAF** | 782 | 0.0% | 0 | Adaptador de salida y punto de entrada final (In-Degree 0, con referencias por string) dedicado a la generación de reportes comerciales en DOCX. |
| `src/assessment_engine/adapters/render_lineage_portal.py` | **ACTIVE_LEAF** | 138 | 0.0% | 0 | Script generador independiente que actúa como hoja activa para hidratar y exportar el portal estático HTML de linaje mediante Jinja2. |
| `src/assessment_engine/adapters/render_tower_annex_from_template.py` | **ACTIVE_LEAF** | 856 | 0.0% | 0 | Adaptador de renderizado final invocado dinámicamente para generar el documento DOCX de anexos técnicos por torre a partir de su esquema. |
| `src/assessment_engine/adapters/render_web_presentation.py` | **ACTIVE_LEAF** | 411 | 21.7% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/bootstrap/bootstrap_all_towers.py` | **ACTIVE_LEAF** | 125 | 0.0% | 0 | Script CLI de punto de entrada (usa argparse y tiene In-Degree 0) diseñado para orquestar la inicialización masiva de todas las torres. |
| `src/assessment_engine/application/build_evidence_ledger.py` | **ACTIVE_LEAF** | 211 | 77.2% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/build_global_report_payload.py` | **ACTIVE_LEAF** | 674 | 0.0% | 0 | Script de aplicación ejecutado como subproceso del pipeline (referenciado por string) encargado de ensamblar el payload global de reporte. |
| `src/assessment_engine/application/cli.py` | **ACTIVE_LEAF** | 382 | 0.0% | 0 | Punto de entrada principal de línea de comandos (CLI) para la orquestación y control de ejecución del motor. |
| `src/assessment_engine/application/export_graph_state.py` | **ACTIVE_LEAF** | 291 | 0.0% | 0 | Script de exportación de fin de flujo para serializar el estado del gemelo digital y grafo epistémico hacia consumidores externos. |
| `src/assessment_engine/application/generate_executive_roadmap_image.py` | **ACTIVE_LEAF** | 148 | 0.0% | 0 | Script de renderizado gráfico independiente invocado dinámicamente por CLI para generar el diagrama de Gantt con Matplotlib. |
| `src/assessment_engine/application/generate_global_radar_chart.py` | **ACTIVE_LEAF** | 148 | 0.0% | 0 | Utilidad de generación de gráficos de radar ejecutada como proceso hoja dentro del flujo de construcción de reportes. |
| `src/assessment_engine/application/generate_tower_radar_chart.py` | **ACTIVE_LEAF** | 138 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/run_commercial_pipeline.py` | **ACTIVE_LEAF** | 62 | 0.0% | 0 | Orquestador de nivel superior y punto de entrada específico para la ejecución del flujo de evaluación comercial. |
| `src/assessment_engine/application/run_commercial_refiner.py` | **ACTIVE_LEAF** | 334 | 0.0% | 0 | Script de ejecución invocado dinámicamente como etapa del pipeline comercial para orquestar agentes de IA sobre el payload. |
| `src/assessment_engine/application/run_evidence_analyst.py` | **ACTIVE_LEAF** | 330 | 64.0% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_executive_annex_synthesizer.py` | **ACTIVE_LEAF** | 842 | 23.0% | 1 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_executive_refiner.py` | **ACTIVE_LEAF** | 282 | 63.6% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_global_pipeline.py` | **ACTIVE_LEAF** | 141 | 0.0% | 0 | Punto de entrada principal (CLI) que orquesta el pipeline de evaluación estratégica global mediante subprocesos aislados. |
| `src/assessment_engine/application/run_global_synthesizer_tobe.py` | **ACTIVE_LEAF** | 569 | 97.4% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_intelligence_harvesting.py` | **ACTIVE_LEAF** | 845 | 21.0% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_scoring.py` | **ACTIVE_LEAF** | 180 | 0.0% | 0 | Módulo de procesamiento invocado como subproceso por el orquestador para el cálculo cuantitativo de madurez y bandas de puntuación. |
| `src/assessment_engine/application/run_sota_researcher.py` | **ACTIVE_LEAF** | 162 | 33.3% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_strategic_orchestrator.py` | **ACTIVE_LEAF** | 69 | 0.0% | 2 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_tower_pipeline.py` | **ACTIVE_LEAF** | 624 | 0.0% | 0 | Punto de entrada CLI que define y ejecuta el DAG de etapas del pipeline de evaluación por torre en subprocesos aislados. |
| `src/assessment_engine/application/tools/apex_dispatcher.py` | **ACTIVE_LEAF** | 513 | 0.0% | 0 | Herramienta CLI autónoma con interfaz en terminal (Rich) para despachar tareas del backlog y gestionar agentes de mejora continua. |
| `src/assessment_engine/application/tools/build_docs_site.py` | **ACTIVE_LEAF** | 183 | 0.0% | 0 | Script CLI autónomo (marcado con golden-path: ignore) diseñado para compilar y renderizar la documentación del proyecto en flujos de CI/CD. |
| `src/assessment_engine/application/tools/build_documentation_health_report.py` | **ACTIVE_LEAF** | 154 | 0.0% | 0 | Utilidad CLI de gobernanza documental que genera reportes de estado sin requerir ser importada por el motor principal. |
| `src/assessment_engine/application/tools/check_docx_unresolved_placeholders.py` | **ACTIVE_LEAF** | 67 | 0.0% | 0 | Punto de entrada CLI para validación de calidad en pipelines CI/CD que verifica placeholders sin resolver en archivos DOCX generados. |
| `src/assessment_engine/application/tools/check_vertex_ai_access.py` | **ACTIVE_LEAF** | 35 | 0.0% | 0 | Script de verificación previa (preflight check) ejecutable por línea de comandos para validar credenciales y acceso a Vertex AI antes de iniciar el motor. |
| `src/assessment_engine/application/tools/compile_llms_full.py` | **ACTIVE_LEAF** | 104 | 75.0% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/corporate_project_aggregator.py` | **ACTIVE_LEAF** | 173 | 80.9% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/dynamic_tower_dispatcher.py` | **ACTIVE_LEAF** | 225 | 78.2% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/enforce_english_comments.py` | **ACTIVE_LEAF** | 398 | 0.0% | 0 | Herramienta CLI de linting y gobernanza de código asistida por LLM para detectar y traducir comentarios en español. |
| `src/assessment_engine/application/tools/ingest_documents.py` | **ACTIVE_LEAF** | 79 | 0.0% | 0 | Script CLI de punto de entrada para ejecutar el pipeline de ingesta parametrizada de documentos con EvidenceEngine y RaptorEngine. |
| `src/assessment_engine/application/tools/lint_documentation_style.py` | **ACTIVE_LEAF** | 64 | 0.0% | 0 | Herramienta CLI de gobernanza y CI/CD para validar el estilo y evitar lenguaje no técnico en la documentación del repositorio. |
| `src/assessment_engine/application/tools/regenerate_smoke_artifacts.py` | **ACTIVE_LEAF** | 284 | 0.0% | 0 | Orquestador CLI que ejecuta subprocesos para regenerar artefactos de pruebas de humo (smoke tests) de forma reproducible. |
| `src/assessment_engine/application/tools/run_golden_path_check.py` | **ACTIVE_LEAF** | 153 | 0.0% | 0 | Script de validación arquitectónica para CI/CD que verifica que los nuevos archivos de Git cumplan con las plantillas estructurales obligatorias. |
| `src/assessment_engine/application/tools/run_incremental_typecheck.py` | **ACTIVE_LEAF** | 87 | 0.0% | 0 | Punto de entrada CLI para ejecutar chequeo estático de tipos (mypy) de manera incremental sobre archivos modificados en Git. |
| `src/assessment_engine/application/tools/run_shadow_compilation.py` | **ACTIVE_LEAF** | 145 | 0.0% | 0 | Herramienta CLI de diagnóstico y compilación AST que genera variantes de documentos DOCX para depurar el motor de renderizado. |
| `src/assessment_engine/application/tools/sign_dossier.py` | **ACTIVE_LEAF** | 52 | 0.0% | 0 | Script CLI de utilidad operativa válido como punto de entrada manual para re-firmar archivos JSON de dossiers utilizando el módulo de infraestructura. |
| `src/assessment_engine/application/tools/sync_sentinel.py` | **ACTIVE_LEAF** | 37 | 0.0% | 0 | Punto de entrada CLI operativo diseñado para forzar la sincronización bajo demanda de la cola de StreamingSentinel y reconstruir el árbol RAG. |
| `src/assessment_engine/application/tools/validate_contracts_schemas.py` | **ACTIVE_LEAF** | 307 | 39.1% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/validate_documentation_governance.py` | **ACTIVE_LEAF** | 693 | 59.0% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/validate_documentation_snippets.py` | **ACTIVE_LEAF** | 157 | 79.8% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/tools/validate_semantic_drift.py` | **ACTIVE_LEAF** | 213 | 30.7% | 0 | Módulo hoja auxiliar o adaptador secundario. |
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
| `src/assessment_engine/infrastructure/deterministic_enricher.py` | **ACTIVE_LEAF** | 225 | 93.5% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/doctor_agent.py` | **ACTIVE_LEAF** | 23 | 87.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/document_ai_client.py` | **ACTIVE_LEAF** | 38 | 100.0% | 2 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/infrastructure/epistemic_graph_service.py` | **ACTIVE_LEAF** | 421 | 89.5% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evidence_engine.py` | **ACTIVE_LEAF** | 437 | 53.9% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evidence_governance.py` | **ACTIVE_LEAF** | 257 | 55.9% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/ast_signature_guard.py` | **ACTIVE_LEAF** | 512 | 46.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/ast_signature_models.py` | **ACTIVE_LEAF** | 131 | 67.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/closure_tribunal.py` | **ACTIVE_LEAF** | 479 | 36.3% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/cognitive_arbiter.py` | **ACTIVE_LEAF** | 1171 | 10.3% | 0 | Orquestador de alto nivel del bucle dialéctico evolutivo que actúa como punto de entrada (In-Degree 0, Out-Degree 12) y cuenta con ejecución verificada en pruebas. |
| `src/assessment_engine/infrastructure/evolution/complexity_guard.py` | **ACTIVE_LEAF** | 249 | 67.1% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/epistemic_distiller.py` | **ACTIVE_LEAF** | 902 | 21.8% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/reflexion_ledger.py` | **ACTIVE_LEAF** | 329 | 46.7% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/worktree_runner.py` | **ACTIVE_LEAF** | 139 | 62.7% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/http_client.py` | **ACTIVE_LEAF** | 113 | 88.4% | 1 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/infrastructure/liability_signer.py` | **ACTIVE_LEAF** | 40 | 85.7% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/mcda_sensitivity_engine.py` | **ACTIVE_LEAF** | 171 | 90.4% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/networkx_analyzer.py` | **ACTIVE_LEAF** | 151 | 81.5% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/parser_strategy.py` | **ACTIVE_LEAF** | 35 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/policies/archimate.py` | **ACTIVE_LEAF** | 54 | 77.6% | 0 | Módulo hoja auxiliar o adaptador secundario. |
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
| `src/assessment_engine/adapters/compilers/ast_appendices_builder.py` | **CANONICAL_CORE** | 303 | 0.0% | 1 | Componente estructural del compilador AST encargado de construir los nodos de apéndices y glosarios, activamente importado en el pipeline principal. |
| `src/assessment_engine/adapters/render_global_report_from_template.py` | **CANONICAL_CORE** | 1565 | 5.2% | 1 | Motor central de renderizado para el reporte global ejecutivo con cobertura de tests activa y funciones reutilizadas por otros adaptadores. |
| `src/assessment_engine/adapters/render_tower_blueprint.py` | **CANONICAL_CORE** | 1368 | 7.2% | 1 | Módulo esencial de generación de blueprints por torre con cobertura de pruebas activa e integración directa en el flujo de renderizado. |
| `src/assessment_engine/application/bootstrap/bootstrap_tower_from_matrix.py` | **CANONICAL_CORE** | 871 | 0.0% | 1 | Módulo base de la capa de aplicación que provee la lógica de extracción XML/DOCX e inicialización, requerido directamente por el orquestador de bootstrap. |
| `src/assessment_engine/application/build_case_input.py` | **CANONICAL_CORE** | 319 | 13.1% | 1 | Módulo central para la ingesta y normalización de entradas de casos con cobertura de pruebas activa e importadores directos en el pipeline. |
| `src/assessment_engine/application/generate_mermaid_gantt.py` | **CANONICAL_CORE** | 160 | 0.0% | 1 | Componente activo importado directamente por otros módulos para transformar estructuras de roadmap en diagramas Gantt vía Mermaid. |
| `src/assessment_engine/application/run_tower_blueprint_engine.py` | **CANONICAL_CORE** | 1051 | 0.0% | 1 | Motor central de análisis arquitectónico con alta cohesión e integración en el grafo de conocimiento, esencial para generar los blueprints por torre. |
| `src/assessment_engine/application/tools/actuarial_ledger_generator.py` | **CANONICAL_CORE** | 93 | 0.0% | 1 | Componente activo e importado dentro del motor para generar dossieres de auditoría de riesgo financiero compatibles con SR 11-7. |
| `src/assessment_engine/application/tools/adversarial_consensus_engine.py` | **CANONICAL_CORE** | 236 | 0.0% | 1 | Módulo esencial de validación de controles de seguridad mediante consenso adversarial, activamente integrado en el flujo de evaluación. |
| `src/assessment_engine/application/tools/context_tools.py` | **CANONICAL_CORE** | 206 | 8.6% | 1 | Módulo de herramientas de búsqueda y contexto importado activamente en el sistema y con cobertura de pruebas dinámicas registrada. |
| `src/assessment_engine/application/tools/financial_scale_calibrator.py` | **CANONICAL_CORE** | 309 | 0.0% | 1 | Componente de lógica de negocio que define esquemas financieros (Pydantic) e integración con GenAI, siendo importado activamente por otros módulos del sistema. |
| `src/assessment_engine/application/tools/generate_smoke_data.py` | **CANONICAL_CORE** | 347 | 0.0% | 1 | Generador determinista de datos sintéticos acoplado a los modelos de infraestructura y referenciado activamente para pruebas de humo. |
| `src/assessment_engine/application/tools/run_incremental_quality_gate.py` | **CANONICAL_CORE** | 167 | 0.0% | 1 | Módulo base de control de calidad incremental que además provee utilidades de inspección de Git reutilizadas por otras herramientas de CI. |
| `src/assessment_engine/application/tools/run_product_owner_orchestrator.py` | **CANONICAL_CORE** | 2227 | 11.2% | 0 | Orquestador principal de alta complejidad (2227 LOC) con cobertura de pruebas activa e integración profunda con los motores de IA e infraestructura. |
| `src/assessment_engine/application/validate_tower_definition.py` | **CANONICAL_CORE** | 203 | 0.0% | 1 | Módulo esencial de validación de esquemas para definiciones de torres, activamente importado en el sistema y ejecutable como herramienta de verificación. |
| `src/assessment_engine/domain/maturity_band.py` | **CANONICAL_CORE** | 76 | 86.4% | 8 | Módulo nuclear altamente acoplado (8 dependientes) y ejecutado dinámicamente (86.4%). |
| `src/assessment_engine/domain/ontology_registry.py` | **CANONICAL_CORE** | 49 | 0.0% | 1 | Componente central del dominio que gestiona y aplica las restricciones ontológicas del grafo de conocimiento, activamente referenciado por el motor. |
| `src/assessment_engine/domain/prompts/commercial_prompts.py` | **CANONICAL_CORE** | 61 | 0.0% | 1 | Repositorio activo del dominio que provee plantillas de prompts y catálogos de referencia comercial consumidos por los generadores del sistema. |
| `src/assessment_engine/domain/prompts/intelligence_prompts.py` | **CANONICAL_CORE** | 320 | 78.3% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (78.3%). |
| `src/assessment_engine/domain/schemas/annex_synthesis.py` | **CANONICAL_CORE** | 189 | 100.0% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/domain/schemas/ast.py` | **CANONICAL_CORE** | 211 | 100.0% | 28 | Módulo nuclear altamente acoplado (28 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/domain/schemas/blueprint.py` | **CANONICAL_CORE** | 540 | 100.0% | 6 | Módulo nuclear altamente acoplado (6 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/domain/schemas/common.py` | **CANONICAL_CORE** | 153 | 39.5% | 12 | Módulo nuclear altamente acoplado (12 dependientes) y ejecutado dinámicamente (39.5%). |
| `src/assessment_engine/domain/schemas/context.py` | **CANONICAL_CORE** | 126 | 0.0% | 0 | Esquema Pydantic fundamental para el estado en memoria (AssessmentContext), con altísima referencia en anotaciones de tipo diferidas (51 String Refs). |
| `src/assessment_engine/infrastructure/ai_client.py` | **CANONICAL_CORE** | 339 | 65.6% | 12 | Módulo nuclear altamente acoplado (12 dependientes) y ejecutado dinámicamente (65.6%). |
| `src/assessment_engine/infrastructure/apex_models.py` | **CANONICAL_CORE** | 59 | 0.0% | 1 | Define esquemas de datos esenciales en Pydantic para estructurar las decisiones del sistema de deliberación, siendo activamente importado en la arquitectura. |
| `src/assessment_engine/infrastructure/auditor/models.py` | **CANONICAL_CORE** | 60 | 96.2% | 20 | Módulo nuclear altamente acoplado (20 dependientes) y ejecutado dinámicamente (96.2%). |
| `src/assessment_engine/infrastructure/auditor/probes/browser_accessibility.py` | **CANONICAL_CORE** | 183 | 16.0% | 1 | Sonda de auditoría especializada en cumplimiento WCAG 2.2 AA / EAA integrada en el subsistema de auditoría y respaldada por cobertura de pruebas. |
| `src/assessment_engine/infrastructure/client_intelligence.py` | **CANONICAL_CORE** | 1279 | 17.6% | 9 | Módulo nuclear altamente acoplado (9 dependientes) y ejecutado dinámicamente (17.6%). |
| `src/assessment_engine/infrastructure/config_loader.py` | **CANONICAL_CORE** | 386 | 88.6% | 26 | Módulo nuclear altamente acoplado (26 dependientes) y ejecutado dinámicamente (88.6%). |
| `src/assessment_engine/infrastructure/contract_utils.py` | **CANONICAL_CORE** | 102 | 21.1% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (21.1%). |
| `src/assessment_engine/infrastructure/docx_render_utils.py` | **CANONICAL_CORE** | 1253 | 28.5% | 6 | Módulo nuclear altamente acoplado (6 dependientes) y ejecutado dinámicamente (28.5%). |
| `src/assessment_engine/infrastructure/entity_resolution.py` | **CANONICAL_CORE** | 128 | 0.0% | 1 | Motor de resolución de entidades necesario para la deduplicación semántica de nodos en el grafo de conocimiento, referenciado activamente por el sistema. |
| `src/assessment_engine/infrastructure/epistemic_extractor.py` | **CANONICAL_CORE** | 69 | 0.0% | 1 | Componente de extracción de tripletas de conocimiento epistémico integrado con Vertex AI y el cliente de IA de la infraestructura principal. |
| `src/assessment_engine/infrastructure/epistemic_graph.py` | **CANONICAL_CORE** | 268 | 80.9% | 15 | Módulo nuclear altamente acoplado (15 dependientes) y ejecutado dinámicamente (80.9%). |
| `src/assessment_engine/infrastructure/evolution/fault_localizer.py` | **CANONICAL_CORE** | 243 | 0.0% | 1 | Implementación algorítmica SBFL (Ochiai) para el aislamiento de fallos en trazas de ejecución, importada como dependencia dentro del motor de evolución. |
| `src/assessment_engine/infrastructure/evolution/mcts_refactor_engine.py` | **CANONICAL_CORE** | 132 | 0.0% | 1 | Motor de búsqueda Monte Carlo (MCTS) sobre AST para transformaciones estructurales de código (RFC-019), consumido por el subsistema de evolución. |
| `src/assessment_engine/infrastructure/evolution/mutation_ctf_probe.py` | **CANONICAL_CORE** | 299 | 18.3% | 1 | Componente crítico de certificación mediante pruebas de mutación en AST, invocado directamente por el árbitro cognitivo y con cobertura dinámica activa. |
| `src/assessment_engine/infrastructure/evolution/trace_conditioner.py` | **CANONICAL_CORE** | 114 | 0.0% | 1 | Componente de infraestructura referenciado activamente (In-Degree: 1) para el diagnóstico forense de trazas W3C y acoplado al registro de métricas global, requiriendo cobertura de pruebas pero no eliminación. |
| `src/assessment_engine/infrastructure/genai_client.py` | **CANONICAL_CORE** | 88 | 88.6% | 19 | Módulo nuclear altamente acoplado (19 dependientes) y ejecutado dinámicamente (88.6%). |
| `src/assessment_engine/infrastructure/global_maturity_policy.py` | **CANONICAL_CORE** | 68 | 35.0% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (35.0%). |
| `src/assessment_engine/infrastructure/governance.py` | **CANONICAL_CORE** | 155 | 18.4% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (18.4%). |
| `src/assessment_engine/infrastructure/json_from_model.py` | **CANONICAL_CORE** | 63 | 84.2% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (84.2%). |
| `src/assessment_engine/infrastructure/localization.py` | **CANONICAL_CORE** | 338 | 81.0% | 18 | Módulo nuclear altamente acoplado (18 dependientes) y ejecutado dinámicamente (81.0%). |
| `src/assessment_engine/infrastructure/logger_config.py` | **CANONICAL_CORE** | 112 | 15.0% | 1 | Módulo fundacional de observabilidad transversal con cobertura activa (15%) e importadores directos, indispensable para la emisión de logs estructurados en formato JSON hacia Google Cloud. |
| `src/assessment_engine/infrastructure/pipeline_runtime.py` | **CANONICAL_CORE** | 173 | 27.7% | 5 | Módulo nuclear altamente acoplado (5 dependientes) y ejecutado dinámicamente (27.7%). |
| `src/assessment_engine/infrastructure/policies/base.py` | **CANONICAL_CORE** | 15 | 100.0% | 8 | Módulo nuclear altamente acoplado (8 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/infrastructure/runtime_env.py` | **CANONICAL_CORE** | 196 | 46.2% | 8 | Módulo nuclear altamente acoplado (8 dependientes) y ejecutado dinámicamente (46.2%). |
| `src/assessment_engine/infrastructure/runtime_paths.py` | **CANONICAL_CORE** | 155 | 69.5% | 29 | Módulo nuclear altamente acoplado (29 dependientes) y ejecutado dinámicamente (69.5%). |
| `src/assessment_engine/infrastructure/text_utils.py` | **CANONICAL_CORE** | 162 | 97.2% | 17 | Módulo nuclear altamente acoplado (17 dependientes) y ejecutado dinámicamente (97.2%). |
| `src/assessment_engine/application/tools/verify_exact_text.py` | **CONFIRMED_ORPHAN** | 106 | 0.0% | 0 | Script de verificación ad-hoc con rutas estáticas codificadas, sin importadores ni integración con el motor central, constituyendo deuda técnica desechable. |
| `src/assessment_engine/application/validate_section_output.py` | **CONFIRMED_ORPHAN** | 87 | 0.0% | 0 | Validador obsoleto desconectado del pipeline principal (In-Degree 0) que depende de directorios estáticos de prueba ('working/client/T5'). |
