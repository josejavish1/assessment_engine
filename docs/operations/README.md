---
status: Verified
owner: docs-governance
source_of_truth:
  - ../../.github/workflows/
  - ./
last_verified_against: 2026-05-03
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Manual de Operaciones

Este directorio es el centro de conocimiento para la instalación, operación y mantenimiento del `assessment-engine`. Actúa como un índice central que enlaza a guías detalladas, sirviendo como fuente única de verdad para desarrolladores y agentes de IA.

## Filosofía de Operaciones: Automatización, Calidad y Transparencia

Nuestra estrategia operativa se basa en los principios de **GitOps**, donde el repositorio de Git es la única fuente de verdad. La automatización a través de **GitHub Actions** garantiza que cada cambio cumpla con nuestros rigurosos estándares de calidad antes de ser integrado.

1.  **Git como Fuente Única de Verdad:** Todas las operaciones se derivan del estado del repositorio.
2.  **Calidad Continua Proactiva:** Los workflows de CI actúan como guardianes, ejecutando validaciones de linting, tipado y tests en cada Pull Request para prevenir la deuda técnica.
3.  **Transparencia y Trazabilidad:** Los flujos de trabajo son explícitos y están documentados en los ficheros YAML de GitHub Actions, permitiendo que cualquiera pueda entender y depurar el ciclo de vida del desarrollo.

## Arquitectura CI/CD Visual

El siguiente diagrama ilustra el flujo de nuestros pipelines de Integración Continua (CI). La mayoría se disparan ante un Pull Request y se ejecutan en paralelo como "status checks". Para una descripción técnica detallada de cada `job` y `workflow`, consulte el documento [`ci-cd-workflows.md`](./ci-cd-workflows.md).

```mermaid
graph TD
    subgraph Trigger
        A[Push or Open PR to main/develop]
    end

    subgraph "CI/CD Pipeline (Runs in Parallel)"
        A --> B[CI: Tests & Smoke Run];
        A --> C[Quality: Incremental Checks];
        A --> D[Typing: Incremental Type Check];
        A --> E[Docs: Governance Check];
        A --> F[Agent Evals (Conditional on file paths)];
    end
    
    subgraph "Other Triggers"
        G[Nightly Schedule] --> F;
        H[Merge to main] --> I[Auto-reconcile open PRs];
    end

    B --> Z{PR Status};
    C --> Z;
    D --> Z;
    E --> Z;
    F --> Z;
```

## Índice de Documentos Operativos

### 1. Entorno y Configuración
-   **[`installation.md`](./installation.md):** Guía completa para configurar el entorno de desarrollo local desde cero.
-   **[`ci-cd-workflows.md`](./ci-cd-workflows.md):** Descripción técnica detallada de los workflows de GitHub Actions.

### 2. Ciclo de Vida del Desarrollo
-   **[`agentic-development-workflow.md`](./agentic-development-workflow.md):** Proceso de desarrollo asistido por agentes, desde la especificación hasta el Pull Request.
-   **[`engineering-quality-gates.md`](./engineering-quality-gates.md):** Define los controles de calidad incrementales (Ruff, Mypy) que se aplican en el pipeline.
-   **[`signing-commits-policy.md`](./signing-commits-policy.md):** Política y guía para la firma de commits.

### 3. Ejecución y Orquestación
-   **[`pipeline-execution.md`](./pipeline-execution.md):** Instrucciones para ejecutar los pipelines de generación de artefactos.
-   **[`pipeline-controls-runbook.md`](./pipeline-controls-runbook.md):** Runbook para gestionar y monitorizar la ejecución de los pipelines.
-   **[`product-owner-orchestrator.md`](./product-owner-orchestrator.md):** Cómo utilizar el orquestador de alto nivel para automatizar tareas complejas.

### 4. Mantenimiento y Resolución de Problemas
-   **[`troubleshooting-working.md`](./troubleshooting-working.md):** Manual para diagnosticar y resolver problemas comunes.
-   **[`smoke-regeneration.md`](./smoke-regeneration.md):** Proceso para regenerar los datos de los `smoke tests`.
-   **[`assessment-coherence-remediation.md`](./assessment-coherence-remediation.md):** Guía para reparar problemas de coherencia en los datos generados.
