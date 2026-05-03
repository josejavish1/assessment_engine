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

Este directorio contiene la documentación esencial para instalar, operar, validar y mantener el `assessment-engine`. Está diseñado para ser la fuente única de verdad tanto para desarrolladores humanos como para agentes de IA.

## Filosofía de Operaciones

Nuestra estrategia operativa se fundamenta en tres pilares clave, alineados con las mejores prácticas de **GitOps y la automatización CI/CD**:

1.  **Git como Fuente Única de Verdad:** Todas las operaciones, desde la ejecución de tests hasta los despliegues, se derivan del estado del repositorio. La configuración y la infraestructura se tratan como código.
2.  **Automatización y Calidad Continua:** Los workflows de GitHub Actions actúan como guardianes de la calidad. Cada cambio es sometido a un riguroso proceso de validación (linting, tipado, tests) antes de ser considerado para integración, previniendo la deuda técnica de forma proactiva.
3.  **Transparencia y Trazabilidad:** Los procesos están documentados y los flujos de trabajo son explícitos en los ficheros YAML de GitHub Actions. Esto asegura que cualquier miembro del equipo (humano o IA) pueda entender, replicar y depurar el ciclo de vida del desarrollo.

## Índice de Documentos Operativos

-   **Workflow de Desarrollo y Calidad:**
    -   [`agentic-development-workflow.md`](agentic-development-workflow.md): Proceso de desarrollo asistido por agentes, desde la especificación hasta el Pull Request.
    -   [`engineering-quality-gates.md`](engineering-quality-gates.md): Descripción de los controles de calidad incrementales (Ruff, Mypy).
    -   [`signing-commits-policy.md`](signing-commits-policy.md): Política de firma de commits para garantizar la autoría y seguridad.
-   **Instalación y Entorno:**
    -   [`installation.md`](installation.md): Guía para configurar el entorno de desarrollo local.
    -   [`ci-cd-workflows.md`](ci-cd-workflows.md): (Este documento) Detalles técnicos sobre la arquitectura CI/CD.
-   **Ejecución de Pipelines:**
    -   [`pipeline-execution.md`](pipeline-execution.md): Cómo ejecutar los pipelines de generación de artefactos.
    -   [`pipeline-controls-runbook.md`](pipeline-controls-runbook.md): Guía para gestionar y controlar la ejecución de los pipelines.
    -   [`product-owner-orchestrator.md`](product-owner-orchestrator.md): Uso del orquestador para automatizar tareas complejas.
-   **Mantenimiento y Troubleshooting:**
    -   [`smoke-regeneration.md`](smoke-regeneration.md): Proceso para regenerar los datos de prueba (`smoke tests`).
    -   [`troubleshooting-working.md`](troubleshooting-working.md): Manual para diagnosticar y resolver problemas comunes.
    -   [`assessment-coherence-remediation.md`](assessment-coherence-remediation.md): Guía para reparar problemas de coherencia en los artefactos generados.

## Arquitectura CI/CD

El sistema de Integración Continua y Despliegue Continuo (CI/CD) se orquesta a través de GitHub Actions. El siguiente diagrama ilustra el flujo de validación que se activa ante un Pull Request o un `push` a una rama principal:

```mermaid
graph TD
    subgraph "Desarrollo Local"
        A[Desarrollador o Agente crea un commit] --> B{Push a GitHub};
    end

    subgraph "GitHub Actions Workflow"
        B --> C{Trigger: Pull Request / Push};
        C --> D[Paso 1: Setup Environment];
        D --> E[Instalar Dependencias (`pip install -e .`)];
        E --> F[Paso 2: Ejecutar Quality Gates];
        F --> G[Ruff Check & Format];
        F --> H[Mypy Type Check];
        E --> I[Paso 3: Ejecutar Tests Unitarios];
        I --> J[Pytest];
    end

    subgraph "Resultado"
        G --> K{¿Éxito?};
        H --> K;
        J --> K;
        K -- Si Falla --> L[Notificar Fallo en PR];
        K -- Si Pasa --> M[Permitir Merge];
    end

    style A fill:#D5F5E3
    style B fill:#EAF2F8
    style M fill:#D5F5E3
    style L fill:#FADBD8
```
