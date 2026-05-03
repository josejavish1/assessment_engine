---
status: "Verified"
owner: "documentation-team"
reviewers: []
last_updated: "2026-05-03"
doc_type: "operational"
applies_to: 
  - "docs"
last_verified_against: "2026-05-03"
source_of_truth: 
  - "Manual"
---

# Auditoría de Documentación del Proyecto

**Última auditoría:** 2026-05-03 - El inventario se ha verificado y se encuentra completo y actualizado.

Este documento realiza un seguimiento del estado de la documentación del proyecto `assessment-engine`. El objetivo es tener un inventario claro que nos permita priorizar los esfuerzos de actualización y garantizar que toda la documentación sea un reflejo fiel del estado actual del sistema.

## Definición de Estados

-   **Actualizado:** El documento refleja con precisión el estado actual del código y la arquitectura.
-   **Desactualizado:** El documento contiene información que ya no es correcta debido a cambios significatorios en el código o la arquitectura, o requiere una revisión.
-   **Obsoleto:** El documento ya no es relevante y debería ser archivado o eliminado.

---

## Inventario de Documentación

### Documentación Principal

| Fichero | Estado | Notas |
|---|---|---|
| [`README.md`](../README.md) | Desactualizado | Actúa como punto de entrada principal, pero necesita ser actualizado para reflejar el nuevo `documentation-map.yaml`. |
| [`A5_CHECKLIST.md`](../A5_CHECKLIST.md) | Desactualizado | La checklist es funcional, pero algunas referencias, como la del diario de `GEMINI.md`, están quedando obsoletas. |
| [`AGENTS.md`](../AGENTS.md) | Actualizado | Documento actualizado que establece las directrices para los agentes de IA y se alinea con la documentación canónica. |
| [`CHATGPT.md`](../CHATGPT.md) | Actualizado | Adaptador simple y actualizado para ChatGPT. |
| [`GEMINI.md`](../GEMINI.md) | Desactualizado | Marcado explícitamente como `Needs Review`. Contiene información valiosa, pero también partes obsoletas. Debe ser auditado y sincronizado. |
| [`docs/README.md`](README.md) | Actualizado | Mapa maestro de la documentación. Es la guía central para navegar la documentación canónica. |
| [`docs/SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) | Actualizado | Descripción de alto nivel de la arquitectura, actualizada y alineada con el modelo "Top-Down". |
| [`docs/documentation-map.yaml`](documentation-map.yaml) | Actualizado | Inventario máquina-legible del estado de la documentación. Pieza central de la gobernanza. |
| [`docs/ai/documentation-governance.md`](ai/documentation-governance.md) | Actualizado | Define la política y las reglas para mantener la documentación. Muy actualizado. |
| [`docs/documentation_audit.md`](documentation_audit.md) | Actualizado | Documento de seguimiento del estado de la documentación. |

### Arquitectura

| Fichero | Estado | Notas |
|---|---|---|
| [`docs/architecture/README.md`](architecture/README.md) | Actualizado | Punto de entrada a la documentación de arquitectura detallada. |
| [`docs/architecture/roadmap_vision.md`](architecture/roadmap_vision.md) | Actualizado | Documento estratégico que describe la visión a futuro del proyecto. |
| [`docs/architecture/critical-modules.md`](architecture/critical-modules.md) | Actualizado | Mapa de módulos críticos del sistema. Esencial para entender el impacto de los cambios. |
| [`docs/architecture/command-center-roadmap.md`](architecture/command-center-roadmap.md) | Actualizado | Roadmap para la futura interfaz gráfica del orquestador. |
| [`docs/architecture/tower-pipeline.md`](architecture/tower-pipeline.md) | Actualizado | Descripción detallada del pipeline de torre. |
| [`docs/architecture/global-commercial-pipelines.md`](architecture/global-commercial-pipelines.md) | Actualizado | Descripción detallada de los pipelines globales y comerciales. |
| [`docs/architecture/client-intelligence.md`](architecture/client-intelligence.md) | Actualizado | Explica el dossier `client_intelligence.json` y su contrato v3. |
| [`docs/architecture/executive-project-guide.md`](architecture/executive-project-guide.md) | Actualizado | Guía de alto nivel para audiencias no técnicas. |
| [`docs/architecture/mcp-mode.md`](architecture/mcp-mode.md) | Actualizado | Documenta el modo servidor MCP y su relación con la arquitectura principal. |
| [`docs/architecture/working-artifacts.md`](architecture/working-artifacts.md) | Actualizado | Mapa de los artefactos generados en el directorio `working/`. |

### Contratos y Diseño

| Fichero | Estado | Notas |
|---|---|---|
| [`docs/contracts/payload-render-boundaries.md`](contracts/payload-render-boundaries.md) | Actualizado | Define las fronteras entre payloads, schemas y renderizadores. |
| [`docs/contracts/artifact-contracts.md`](contracts/artifact-contracts.md) | Actualizado | Explica el rol empresarial de cada artefacto. |
| [`docs/contracts/tower_annex_design.md`](contracts/tower_annex_design.md) | Actualizado | Diseño de la v2 del anexo de torre, verificado contra implementación. |
| [`docs/contracts/tower_main_report_coverage_matrix.md`](contracts/tower_main_report_coverage_matrix.md) | Actualizado | Matriz de cobertura del informe principal, verificada contra la implementación. |
| [`docs/contracts/tower_main_report_long_template.md`](contracts/tower_main_report_long_template.md) | Actualizado | Plantilla del informe técnico largo, verificada contra la implementación. |

### Operaciones

| Fichero | Estado | Notas |
|---|---|---|
| [`docs/operations/README.md`](operations/README.md) | Actualizado | Punto de entrada para la documentación de operaciones. |
| [`docs/operations/signing-commits-policy.md`](operations/signing-commits-policy.md) | Actualizado | Política para la firma de commits. |
| [`docs/operations/ci-cd-workflows.md`](operations/ci-cd-workflows.md) | Actualizado | Documentación sobre los workflows de CI/CD. |
| [`docs/operations/engineering-quality-gates.md`](operations/engineering-quality-gates.md) | Actualizado | Describe las puertas de calidad para el código. |
| [`docs/operations/smoke-regeneration.md`](operations/smoke-regeneration.md) | Actualizado | Guía para regenerar los artefactos de smoke testing. |
| [`docs/operations/product-owner-orchestrator.md`](operations/product-owner-orchestrator.md) | Actualizado | Documentación del orquestador PO-to-PR. |
| [`docs/operations/pipeline-execution.md`](operations/pipeline-execution.md) | Actualizado | Guía para la ejecución de los pipelines. |
| [`docs/operations/pipeline-controls-runbook.md`](operations/pipeline-controls-runbook.md) | Actualizado | Runbook para la operación de los pipelines. |
| [`docs/operations/agentic-development-workflow.md`](operations/agentic-development-workflow.md) | Actualizado | Flujo de trabajo para el desarrollo con agentes de IA. |
| [`docs/operations/assessment-coherence-remediation.md`](operations/assessment-coherence-remediation.md) | Actualizado | Guía para la corrección de incoherencias en el sistema. |
| [`docs/operations/installation.md`](operations/installation.md) | Actualizado | Guía de instalación y configuración del entorno. |
| [`docs/operations/troubleshooting-working.md`](operations/troubleshooting-working.md) | Actualizado | Guía para la resolución de problemas en el directorio `working/`. |

### Código como Documentación

| Fichero | Estado | Notas |
|---|---|---|
| [`.github/copilot-instructions.md`](../.github/copilot-instructions.md) | Actualizado | Instrucciones específicas para GitHub Copilot. |
| [`.github/CODEOWNERS`](../.github/CODEOWNERS) | Actualizado | Fichero de configuración de ownership. |
| [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | Actualizado | Workflow de Integración Continua. |
| [`.github/workflows/quality.yml`](../.github/workflows/quality.yml) | Actualizado | Workflow de calidad de código. |
| [`.github/workflows/typing.yml`](../.github/workflows/typing.yml) | Actualizado | Workflow de chequeo de tipos. |
| [`.github/workflows/docs-governance.yml`](../.github/workflows/docs-governance.yml) | Actualizado | Workflow de gobernanza de la documentación. |
| [`.github/workflows/orchestrator-pr-reconcile.yml`](../.github/workflows/orchestrator-pr-reconcile.yml) | Actualizado | Workflow de reconciliación de PRs del orquestador. |
| [`.github/workflows/agent-evals.yml`](../.github/workflows/agent-evals.yml) | Actualizado | Workflow de evaluación de agentes. |
| [`src/business_command_center/README.md`](../src/business_command_center/README.md) | Actualizado | README de la aplicación frontend. Verificado 2026-05-03. |
| [`src/business_command_center/AGENTS.md`](../src/business_command_center/AGENTS.md) | Actualizado | Instrucciones para agentes de IA que trabajan en el frontend. Verificado 2026-05-03. |
| [`templates/golden_paths/README.md`](../templates/golden_paths/README.md) | Actualizado | Registro de plantillas de código para desarrollo asistido por IA. |
| [`src/assessment_engine/prompts/registry/blueprint_pilar_architect_prompt.yaml`](../src/assessment_engine/prompts/registry/blueprint_pilar_architect_prompt.yaml) | Desactualizado | Prompt de IA. |
| [`src/assessment_engine/prompts/registry/blueprint_architect_instruction.yaml`](../src/assessment_engine/prompts/registry/blueprint_architect_instruction.yaml) | Desactualizado | Prompt de IA. |
| [`src/assessment_engine/prompts/registry/annex_executive_synthesizer.yaml`](../src/assessment_engine/prompts/registry/annex_executive_synthesizer.yaml) | Desactualizado | Prompt de IA. |
| [`src/assessment_engine/prompts/registry/blueprint_closing_orchestrator_prompt.yaml`](../src/assessment_engine/prompts/registry/blueprint_closing_orchestrator_prompt.yaml) | Desactualizado | Prompt de IA. |


### Documentación Generada y de Referencia

| Fichero | Estado | Notas |
|---|---|---|
| [`docs/reference/generated/`](reference/generated/) | Obsoleto | Directorio con documentación generada, considerada obsoleta. |
