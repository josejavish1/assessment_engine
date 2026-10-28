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
- **Núcleo Canónico (Vital):** 44 (24.9%)
- **Hojas Activas / Adaptadores:** 128 (72.3%)
- **Módulos Sombra (Duplicados / Candidatos a Fusión):** 0
- **Huérfanos Confirmados (Código Muerto / Purga Segura):** 5

## 2. ⚠️ Huérfanos Confirmados (Blast Radius = 0)

| Archivo | LOC | Cobertura | In-Degree | Razón Técnica de Purga |
| :--- | :---: | :---: | :---: | :--- |
| `src/assessment_engine/application/tools/dynamic_tower_dispatcher.py` | 225 | 0.0% | 0 | Módulo de orquestación desconectado (In-Degree 0, sin referencias ni punto de entrada CLI) que evidencia ser un prototipo abandonado con rutas de importación especulativas. |
| `src/assessment_engine/infrastructure/evolution/ast_signature_guard.py` | 512 | 0.0% | 1 | Módulo de validación de firmas AST sin cobertura de pruebas cuyo único importador es el orquestador huérfano cognitive_arbiter.py. |
| `src/assessment_engine/infrastructure/evolution/ast_signature_models.py` | 131 | 0.0% | 1 | Modelos de datos acoplados exclusivamente a ast_signature_guard.py, formando parte de una cadena de dependencias muerta sin cobertura. |
| `src/assessment_engine/infrastructure/evolution/closure_tribunal.py` | 479 | 0.0% | 0 | Módulo de validación de entrega completamente aislado, con grado de entrada cero, sin referencias dinámicas y 0% de cobertura de tests. |
| `src/assessment_engine/infrastructure/evolution/cognitive_arbiter.py` | 1171 | 0.0% | 0 | Orquestador monolítico de bucle dialéctico sin puntos de entrada CLI ni importadores en el sistema, constituyendo código muerto no probado. |

## 4. 📋 Inventario Exhaustivo Archivo a Archivo

| Archivo | Veredicto | LOC | Cobertura | In-Deg | Dictamen Funcional |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `src/assessment_engine/adapters/compile_asis_docx_from_modules.py` | **ACTIVE_LEAF** | 2884 | 70.6% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/compilers/ast_appendices_builder.py` | **ACTIVE_LEAF** | 303 | 80.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/compilers/ast_table_builders.py` | **ACTIVE_LEAF** | 241 | 76.3% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/compilers/docx_compiler.py` | **ACTIVE_LEAF** | 565 | 79.2% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/compilers/payload_to_ast.py` | **ACTIVE_LEAF** | 1236 | 65.6% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/generate_asis_markdown_modules.py` | **ACTIVE_LEAF** | 1072 | 72.7% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/render_commercial_report.py` | **ACTIVE_LEAF** | 782 | 92.7% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/render_global_report_from_template.py` | **ACTIVE_LEAF** | 1565 | 79.6% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/render_lineage_portal.py` | **ACTIVE_LEAF** | 138 | 78.8% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/render_tower_annex_from_template.py` | **ACTIVE_LEAF** | 856 | 61.8% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/render_tower_blueprint.py` | **ACTIVE_LEAF** | 1368 | 69.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/adapters/render_web_presentation.py` | **ACTIVE_LEAF** | 411 | 21.7% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/bootstrap/bootstrap_all_towers.py` | **ACTIVE_LEAF** | 125 | 0.0% | 0 | Script CLI de inicialización masiva que actúa como punto de entrada para configurar todas las torres del motor. |
| `src/assessment_engine/application/build_case_input.py` | **ACTIVE_LEAF** | 319 | 76.6% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/build_evidence_ledger.py` | **ACTIVE_LEAF** | 211 | 77.2% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/build_global_report_payload.py` | **ACTIVE_LEAF** | 674 | 69.5% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/cli.py` | **ACTIVE_LEAF** | 426 | 87.3% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/export_graph_state.py` | **ACTIVE_LEAF** | 291 | 0.0% | 0 | Punto de entrada de exportación (DigitalTwinExporter) que agrega el grafo epistémico y la orquestación estratégica para consumidores externos. |
| `src/assessment_engine/application/generate_executive_roadmap_image.py` | **ACTIVE_LEAF** | 148 | 89.6% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/generate_global_radar_chart.py` | **ACTIVE_LEAF** | 148 | 86.4% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/generate_mermaid_gantt.py` | **ACTIVE_LEAF** | 160 | 85.1% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/generate_tower_radar_chart.py` | **ACTIVE_LEAF** | 138 | 72.6% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/run_commercial_pipeline.py` | **ACTIVE_LEAF** | 62 | 88.5% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_commercial_refiner.py` | **ACTIVE_LEAF** | 334 | 50.0% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_evidence_analyst.py` | **ACTIVE_LEAF** | 330 | 90.6% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_executive_annex_synthesizer.py` | **ACTIVE_LEAF** | 860 | 63.5% | 1 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_executive_refiner.py` | **ACTIVE_LEAF** | 282 | 63.6% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_global_pipeline.py` | **ACTIVE_LEAF** | 141 | 90.0% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_global_synthesizer_tobe.py` | **ACTIVE_LEAF** | 569 | 97.4% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_intelligence_harvesting.py` | **ACTIVE_LEAF** | 845 | 40.0% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_scoring.py` | **ACTIVE_LEAF** | 180 | 75.9% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_sota_researcher.py` | **ACTIVE_LEAF** | 162 | 87.9% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_strategic_orchestrator.py` | **ACTIVE_LEAF** | 69 | 75.9% | 2 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_tower_blueprint_engine.py` | **ACTIVE_LEAF** | 1055 | 40.3% | 1 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/run_tower_pipeline.py` | **ACTIVE_LEAF** | 624 | 48.6% | 0 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/application/tools/apex_dispatcher.py` | **ACTIVE_LEAF** | 513 | 0.0% | 0 | Aplicación CLI interactiva basada en Rich que funciona como orquestador autónomo de tareas y agentes APEX. |
| `src/assessment_engine/application/tools/build_docs_site.py` | **ACTIVE_LEAF** | 183 | 0.0% | 0 | Herramienta CLI de automatización (excluida del golden-path) para renderizar la documentación técnica en HTML. |
| `src/assessment_engine/application/tools/build_documentation_health_report.py` | **ACTIVE_LEAF** | 154 | 0.0% | 0 | Script CLI utilitario de CI/CD para auditar y generar reportes de salud y gobernanza sobre el mapa de documentación. |
| `src/assessment_engine/application/tools/check_docx_unresolved_placeholders.py` | **ACTIVE_LEAF** | 67 | 0.0% | 0 | Script CLI independiente diseñado para pipelines de CI/CD que valida la ausencia de placeholders sin resolver en entregables DOCX. |
| `src/assessment_engine/application/tools/check_vertex_ai_access.py` | **ACTIVE_LEAF** | 35 | 0.0% | 0 | Punto de entrada CLI utilizado como pre-flight check operativo para verificar credenciales y conectividad con Vertex AI antes de ejecutar el motor. |
| `src/assessment_engine/application/tools/compile_llms_full.py` | **ACTIVE_LEAF** | 104 | 0.0% | 0 | Herramienta CLI de desarrollo que empaqueta la documentación del repositorio en un único archivo de contexto para ingesta en LLMs. |
| `src/assessment_engine/application/tools/enforce_english_comments.py` | **ACTIVE_LEAF** | 398 | 0.0% | 0 | Script CLI de gobernanza de código (linter/traductor asistido por IA) que se ejecuta de forma autónoma para forzar comentarios en inglés. |
| `src/assessment_engine/application/tools/ingest_documents.py` | **ACTIVE_LEAF** | 79 | 0.0% | 0 | Punto de entrada CLI parametrizado para ejecutar el pipeline de ingesta de documentos de clientes mediante EvidenceEngine y RaptorEngine. |
| `src/assessment_engine/application/tools/lint_documentation_style.py` | **ACTIVE_LEAF** | 64 | 0.0% | 0 | Herramienta CLI de gobernanza y CI/CD para validar el estilo de la documentación técnica contra patrones de lenguaje prohibidos. |
| `src/assessment_engine/application/tools/regenerate_smoke_artifacts.py` | **ACTIVE_LEAF** | 284 | 0.0% | 0 | Script orquestador de alto nivel que actúa como punto de entrada para regenerar de forma reproducible todos los artefactos de smoke test. |
| `src/assessment_engine/application/tools/run_golden_path_check.py` | **ACTIVE_LEAF** | 153 | 0.0% | 0 | Script CLI de validación arquitectónica para pipelines de CI que verifica marcadores estructurales obligatorios en archivos nuevos mediante git diff. |
| `src/assessment_engine/application/tools/run_incremental_typecheck.py` | **ACTIVE_LEAF** | 87 | 0.0% | 0 | Punto de entrada CLI para ejecutar mypy de forma incremental sobre archivos modificados en el flujo de integración continua. |
| `src/assessment_engine/application/tools/run_product_owner_orchestrator.py` | **ACTIVE_LEAF** | 2227 | 0.0% | 0 | Orquestador principal y punto de entrada autónomo de gran escala (2227 LOC) que integra múltiples motores de infraestructura y agentes de IA para ejecutar el flujo de Product Owner. |
| `src/assessment_engine/application/tools/run_shadow_compilation.py` | **ACTIVE_LEAF** | 145 | 0.0% | 0 | Script CLI de entrada para compilar y depurar variantes del AST hacia DOCX usando componentes centrales del motor. |
| `src/assessment_engine/application/tools/sign_dossier.py` | **ACTIVE_LEAF** | 52 | 0.0% | 0 | Utilidad de línea de comandos para firmar criptográficamente archivos JSON de dossiers invocando la capa de infraestructura. |
| `src/assessment_engine/application/tools/sync_sentinel.py` | **ACTIVE_LEAF** | 37 | 0.0% | 0 | Punto de entrada operativo para forzar la sincronización bajo demanda de la cola StreamingSentinel y actualizar el árbol RAG. |
| `src/assessment_engine/application/tools/validate_contracts_schemas.py` | **ACTIVE_LEAF** | 307 | 0.0% | 0 | Herramienta CLI de CI/CD para validar la compatibilidad de tipos entre esquemas Pydantic y la documentación técnica. |
| `src/assessment_engine/application/tools/validate_documentation_snippets.py` | **ACTIVE_LEAF** | 157 | 0.0% | 0 | Script de verificación automatizada para validar rutas y bloques de código embebidos en archivos Markdown. |
| `src/assessment_engine/application/tools/validate_semantic_drift.py` | **ACTIVE_LEAF** | 213 | 0.0% | 0 | Herramienta de análisis estático y git-diff ejecutable en pipelines para detectar deriva semántica en cambios de código. |
| `src/assessment_engine/application/tools/visualize_doc_map.py` | **ACTIVE_LEAF** | 264 | 0.0% | 0 | Generador autónomo de artefactos de visualización HTML/D3.js a partir del mapa de configuración YAML de documentación. |
| `src/assessment_engine/application/validate_tower_definition.py` | **ACTIVE_LEAF** | 203 | 65.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/ontology_registry.py` | **ACTIVE_LEAF** | 49 | 31.8% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/prompts/blueprint_prompts.py` | **ACTIVE_LEAF** | 246 | 49.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/prompts/commercial_prompts.py` | **ACTIVE_LEAF** | 61 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/prompts/product_owner_prompts.py` | **ACTIVE_LEAF** | 162 | 33.3% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/asis.py` | **ACTIVE_LEAF** | 47 | 95.2% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/commercial.py` | **ACTIVE_LEAF** | 232 | 98.1% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/conclusion.py` | **ACTIVE_LEAF** | 41 | 92.6% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/context.py` | **ACTIVE_LEAF** | 126 | 62.9% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/evidence.py` | **ACTIVE_LEAF** | 114 | 98.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/gap.py` | **ACTIVE_LEAF** | 48 | 95.5% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/global_report.py` | **ACTIVE_LEAF** | 254 | 100.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/intelligence.py` | **ACTIVE_LEAF** | 481 | 53.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/risks.py` | **ACTIVE_LEAF** | 38 | 95.0% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/rubric.py` | **ACTIVE_LEAF** | 38 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/tobe.py` | **ACTIVE_LEAF** | 121 | 86.4% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/domain/schemas/todo.py` | **ACTIVE_LEAF** | 38 | 79.3% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/agentic_benchmarker.py` | **ACTIVE_LEAF** | 508 | 58.3% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/apex_sentinel.py` | **ACTIVE_LEAF** | 111 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/mutation_probe.py` | **ACTIVE_LEAF** | 124 | 39.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/ai_safety_llm.py` | **ACTIVE_LEAF** | 150 | 50.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/assertion_quality.py` | **ACTIVE_LEAF** | 71 | 87.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/ast_complexity.py` | **ACTIVE_LEAF** | 470 | 82.6% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/code_hygiene.py` | **ACTIVE_LEAF** | 188 | 58.8% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/comment_quality.py` | **ACTIVE_LEAF** | 496 | 38.4% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/concurrency_stress.py` | **ACTIVE_LEAF** | 308 | 51.8% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/contract_drift.py` | **ACTIVE_LEAF** | 175 | 40.4% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/documentation_quality.py` | **ACTIVE_LEAF** | 190 | 28.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/hardcoded_artifacts.py` | **ACTIVE_LEAF** | 205 | 51.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/legal_compliance.py` | **ACTIVE_LEAF** | 179 | 76.1% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/mutation_gate.py` | **ACTIVE_LEAF** | 89 | 65.2% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/neurosymbolic_topology.py` | **ACTIVE_LEAF** | 132 | 73.2% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/performance_finops.py` | **ACTIVE_LEAF** | 140 | 40.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/resilience_chaos.py` | **ACTIVE_LEAF** | 167 | 51.4% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/security_dast.py` | **ACTIVE_LEAF** | 136 | 24.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/security_sast.py` | **ACTIVE_LEAF** | 338 | 68.1% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/sre_observability.py` | **ACTIVE_LEAF** | 139 | 57.6% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/structural_smells.py` | **ACTIVE_LEAF** | 180 | 66.7% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/supply_chain.py` | **ACTIVE_LEAF** | 238 | 48.3% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/probes/test_coverage.py` | **ACTIVE_LEAF** | 74 | 34.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/reporter.py` | **ACTIVE_LEAF** | 249 | 92.9% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/auditor/scanner.py` | **ACTIVE_LEAF** | 138 | 96.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/chassis/context.py` | **ACTIVE_LEAF** | 68 | 54.7% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/deterministic_enricher.py` | **ACTIVE_LEAF** | 225 | 84.2% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/doctor_agent.py` | **ACTIVE_LEAF** | 23 | 87.5% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/document_ai_client.py` | **ACTIVE_LEAF** | 38 | 100.0% | 2 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/infrastructure/epistemic_graph_service.py` | **ACTIVE_LEAF** | 421 | 89.5% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evidence_engine.py` | **ACTIVE_LEAF** | 437 | 85.4% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evidence_governance.py` | **ACTIVE_LEAF** | 257 | 55.9% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/evolution/reflexion_ledger.py` | **ACTIVE_LEAF** | 329 | 0.0% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/http_client.py` | **ACTIVE_LEAF** | 113 | 88.4% | 1 | Punto de entrada CLI o script de fase de orquestación. |
| `src/assessment_engine/infrastructure/liability_signer.py` | **ACTIVE_LEAF** | 40 | 85.7% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/mcda_sensitivity_engine.py` | **ACTIVE_LEAF** | 171 | 92.8% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/networkx_analyzer.py` | **ACTIVE_LEAF** | 151 | 82.9% | 2 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/parser_strategy.py` | **ACTIVE_LEAF** | 35 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/policies/archimate.py` | **ACTIVE_LEAF** | 54 | 77.6% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/infrastructure/policies/business_case.py` | **ACTIVE_LEAF** | 58 | 100.0% | 0 | Módulo hoja auxiliar o adaptador secundario. |
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
| `src/assessment_engine/mcp_server.py` | **ACTIVE_LEAF** | 533 | 91.1% | 0 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/ports/document_compiler.py` | **ACTIVE_LEAF** | 8 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/ports/graph_analyzer.py` | **ACTIVE_LEAF** | 37 | 100.0% | 1 | Módulo hoja auxiliar o adaptador secundario. |
| `src/assessment_engine/application/bootstrap/bootstrap_tower_from_matrix.py` | **CANONICAL_CORE** | 871 | 0.0% | 1 | Módulo central de ingesta y parseo de matrices DOCX/XML requerido directamente por el proceso de bootstrapping. |
| `src/assessment_engine/application/tools/actuarial_ledger_generator.py` | **CANONICAL_CORE** | 93 | 0.0% | 1 | Componente activo del dominio que genera dossieres de auditoría de riesgo financiero bajo normativa SR 11-7. |
| `src/assessment_engine/application/tools/adversarial_consensus_engine.py` | **CANONICAL_CORE** | 236 | 0.0% | 1 | Motor esencial de evaluación de controles de seguridad mediante consenso adversarial con modelos generativos e integración en el flujo. |
| `src/assessment_engine/application/tools/context_tools.py` | **CANONICAL_CORE** | 206 | 0.0% | 1 | Módulo de herramientas activamente referenciado e importado por el motor para dotar a los agentes de capacidades de búsqueda externa y trazabilidad. |
| `src/assessment_engine/application/tools/corporate_project_aggregator.py` | **CANONICAL_CORE** | 173 | 0.0% | 1 | Componente de lógica de aplicación integrado en el flujo principal para normalizar y agregar iniciativas estratégicas y estimaciones de CAPEX. |
| `src/assessment_engine/application/tools/financial_scale_calibrator.py` | **CANONICAL_CORE** | 309 | 0.0% | 1 | Módulo esencial de dominio y aplicación importado activamente para calibrar magnitudes de riesgo financiero y costes operativos mediante modelos estructurados. |
| `src/assessment_engine/application/tools/generate_smoke_data.py` | **CANONICAL_CORE** | 347 | 0.0% | 1 | Módulo base y CLI generador de datos sintéticos deterministas, importado activamente por el orquestador de regeneración de artefactos de smoke test. |
| `src/assessment_engine/application/tools/run_incremental_quality_gate.py` | **CANONICAL_CORE** | 167 | 0.0% | 1 | Componente central para el control de calidad incremental en CI/CD que además provee funciones utilitarias de resolución de rutas de git a otros scripts como el typechecker. |
| `src/assessment_engine/application/tools/validate_documentation_governance.py` | **CANONICAL_CORE** | 693 | 0.0% | 0 | Módulo base de gobernanza documental que actúa como librería central importada por el resto de las herramientas de validación. |
| `src/assessment_engine/domain/maturity_band.py` | **CANONICAL_CORE** | 76 | 92.4% | 8 | Módulo nuclear altamente acoplado (8 dependientes) y ejecutado dinámicamente (92.4%). |
| `src/assessment_engine/domain/prompts/intelligence_prompts.py` | **CANONICAL_CORE** | 320 | 78.3% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (78.3%). |
| `src/assessment_engine/domain/schemas/annex_synthesis.py` | **CANONICAL_CORE** | 189 | 100.0% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/domain/schemas/ast.py` | **CANONICAL_CORE** | 211 | 100.0% | 30 | Módulo nuclear altamente acoplado (30 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/domain/schemas/blueprint.py` | **CANONICAL_CORE** | 544 | 100.0% | 6 | Módulo nuclear altamente acoplado (6 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/domain/schemas/common.py` | **CANONICAL_CORE** | 153 | 96.3% | 12 | Módulo nuclear altamente acoplado (12 dependientes) y ejecutado dinámicamente (96.3%). |
| `src/assessment_engine/infrastructure/ai_client.py` | **CANONICAL_CORE** | 339 | 65.6% | 12 | Módulo nuclear altamente acoplado (12 dependientes) y ejecutado dinámicamente (65.6%). |
| `src/assessment_engine/infrastructure/apex_models.py` | **CANONICAL_CORE** | 59 | 0.0% | 1 | Define esquemas de datos esenciales en Pydantic para estructurar decisiones y respuestas de debates, siendo importado activamente en el motor. |
| `src/assessment_engine/infrastructure/auditor/models.py` | **CANONICAL_CORE** | 60 | 96.2% | 23 | Módulo nuclear altamente acoplado (23 dependientes) y ejecutado dinámicamente (96.2%). |
| `src/assessment_engine/infrastructure/auditor/probes/browser_accessibility.py` | **CANONICAL_CORE** | 183 | 16.0% | 1 | Sonda de auditoría de accesibilidad web (WCAG 2.2) integrada y respaldada por cobertura de pruebas dinámicas. |
| `src/assessment_engine/infrastructure/client_intelligence.py` | **CANONICAL_CORE** | 1279 | 65.4% | 9 | Módulo nuclear altamente acoplado (9 dependientes) y ejecutado dinámicamente (65.4%). |
| `src/assessment_engine/infrastructure/config_loader.py` | **CANONICAL_CORE** | 386 | 89.1% | 26 | Módulo nuclear altamente acoplado (26 dependientes) y ejecutado dinámicamente (89.1%). |
| `src/assessment_engine/infrastructure/contract_utils.py` | **CANONICAL_CORE** | 102 | 33.3% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (33.3%). |
| `src/assessment_engine/infrastructure/docx_render_utils.py` | **CANONICAL_CORE** | 1253 | 79.5% | 6 | Módulo nuclear altamente acoplado (6 dependientes) y ejecutado dinámicamente (79.5%). |
| `src/assessment_engine/infrastructure/entity_resolution.py` | **CANONICAL_CORE** | 128 | 16.3% | 1 | Motor central de resolución de entidades para evitar nodos duplicados en el grafo, con referencias activas y cobertura de tests. |
| `src/assessment_engine/infrastructure/epistemic_extractor.py` | **CANONICAL_CORE** | 69 | 0.0% | 1 | Componente de infraestructura conectado a Vertex AI y ADK para la extracción de tripletas de conocimiento epistémico, referenciado en el sistema. |
| `src/assessment_engine/infrastructure/epistemic_graph.py` | **CANONICAL_CORE** | 268 | 84.3% | 15 | Módulo nuclear altamente acoplado (15 dependientes) y ejecutado dinámicamente (84.3%). |
| `src/assessment_engine/infrastructure/evolution/complexity_guard.py` | **CANONICAL_CORE** | 249 | 0.0% | 1 | Componente activo del subsistema de evolución (In-Degree: 1) encargado de auditar la complejidad ciclomática y cognitiva delegando el cálculo base al módulo auditor. |
| `src/assessment_engine/infrastructure/evolution/epistemic_distiller.py` | **CANONICAL_CORE** | 902 | 0.0% | 1 | Motor estratégico principal (902 LOC, In-Degree: 1) que implementa la síntesis de invariantes y oráculos de verificación especificados en los RFC-015 y RFC-018. |
| `src/assessment_engine/infrastructure/evolution/fault_localizer.py` | **CANONICAL_CORE** | 243 | 0.0% | 1 | Módulo especializado activo (In-Degree: 1) que provee localización de fallos basada en espectro (algoritmo Ochiai) para el ciclo de reparación autónoma. |
| `src/assessment_engine/infrastructure/evolution/mcts_refactor_engine.py` | **CANONICAL_CORE** | 132 | 0.0% | 1 | Componente algorítmico esencial (RFC-019, In-Degree: 1) que ejecuta búsqueda de árboles Monte Carlo (MCTS) sobre el AST para refactorizaciones estructurales. |
| `src/assessment_engine/infrastructure/evolution/mutation_ctf_probe.py` | **CANONICAL_CORE** | 299 | 0.0% | 1 | Sonda de pruebas de mutación AST activa en el pipeline de evolución (In-Degree: 1) para garantizar la fortaleza de las aserciones según ISO 29119. |
| `src/assessment_engine/infrastructure/evolution/trace_conditioner.py` | **CANONICAL_CORE** | 114 | 0.0% | 1 | Adaptador de diagnóstico activo (In-Degree: 1) que transforma telemetría W3C y métricas del chasis en reportes prescriptivos de cuellos de botella. |
| `src/assessment_engine/infrastructure/evolution/worktree_runner.py` | **CANONICAL_CORE** | 139 | 0.0% | 1 | Primitiva de infraestructura crítica (In-Degree: 1) que gestiona el aislamiento efímero mediante Git worktrees para la ejecución segura de experimentos de código. |
| `src/assessment_engine/infrastructure/genai_client.py` | **CANONICAL_CORE** | 88 | 88.6% | 19 | Módulo nuclear altamente acoplado (19 dependientes) y ejecutado dinámicamente (88.6%). |
| `src/assessment_engine/infrastructure/global_maturity_policy.py` | **CANONICAL_CORE** | 68 | 80.0% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (80.0%). |
| `src/assessment_engine/infrastructure/governance.py` | **CANONICAL_CORE** | 155 | 18.4% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (18.4%). |
| `src/assessment_engine/infrastructure/json_from_model.py` | **CANONICAL_CORE** | 63 | 84.2% | 3 | Módulo nuclear altamente acoplado (3 dependientes) y ejecutado dinámicamente (84.2%). |
| `src/assessment_engine/infrastructure/localization.py` | **CANONICAL_CORE** | 338 | 77.0% | 18 | Módulo nuclear altamente acoplado (18 dependientes) y ejecutado dinámicamente (77.0%). |
| `src/assessment_engine/infrastructure/logger_config.py` | **CANONICAL_CORE** | 112 | 15.0% | 1 | Módulo transversal de observabilidad con cobertura dinámica activa (15.0% y 1 importador) que estandariza la salida de logs estructurados en JSON para Cloud Logging. |
| `src/assessment_engine/infrastructure/pipeline_runtime.py` | **CANONICAL_CORE** | 173 | 43.6% | 5 | Módulo nuclear altamente acoplado (5 dependientes) y ejecutado dinámicamente (43.6%). |
| `src/assessment_engine/infrastructure/policies/base.py` | **CANONICAL_CORE** | 15 | 100.0% | 8 | Módulo nuclear altamente acoplado (8 dependientes) y ejecutado dinámicamente (100.0%). |
| `src/assessment_engine/infrastructure/runtime_env.py` | **CANONICAL_CORE** | 196 | 53.8% | 8 | Módulo nuclear altamente acoplado (8 dependientes) y ejecutado dinámicamente (53.8%). |
| `src/assessment_engine/infrastructure/runtime_paths.py` | **CANONICAL_CORE** | 155 | 83.1% | 29 | Módulo nuclear altamente acoplado (29 dependientes) y ejecutado dinámicamente (83.1%). |
| `src/assessment_engine/infrastructure/text_utils.py` | **CANONICAL_CORE** | 232 | 50.0% | 17 | Módulo nuclear altamente acoplado (17 dependientes) y ejecutado dinámicamente (50.0%). |
| `src/assessment_engine/application/tools/dynamic_tower_dispatcher.py` | **CONFIRMED_ORPHAN** | 225 | 0.0% | 0 | Módulo de orquestación desconectado (In-Degree 0, sin referencias ni punto de entrada CLI) que evidencia ser un prototipo abandonado con rutas de importación especulativas. |
| `src/assessment_engine/infrastructure/evolution/ast_signature_guard.py` | **CONFIRMED_ORPHAN** | 512 | 0.0% | 1 | Módulo de validación de firmas AST sin cobertura de pruebas cuyo único importador es el orquestador huérfano cognitive_arbiter.py. |
| `src/assessment_engine/infrastructure/evolution/ast_signature_models.py` | **CONFIRMED_ORPHAN** | 131 | 0.0% | 1 | Modelos de datos acoplados exclusivamente a ast_signature_guard.py, formando parte de una cadena de dependencias muerta sin cobertura. |
| `src/assessment_engine/infrastructure/evolution/closure_tribunal.py` | **CONFIRMED_ORPHAN** | 479 | 0.0% | 0 | Módulo de validación de entrega completamente aislado, con grado de entrada cero, sin referencias dinámicas y 0% de cobertura de tests. |
| `src/assessment_engine/infrastructure/evolution/cognitive_arbiter.py` | **CONFIRMED_ORPHAN** | 1171 | 0.0% | 0 | Orquestador monolítico de bucle dialéctico sin puntos de entrada CLI ni importadores en el sistema, constituyendo código muerto no probado. |
