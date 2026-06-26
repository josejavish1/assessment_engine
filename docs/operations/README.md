---
status: Needs Review
owner: docs-governance
source_of_truth:
- ../../.github/workflows/
- ../../src/assessment_engine/application/
- ../../src/assessment_engine/application/
- ./
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: workflow
---

# Manual de operaciones

Este directorio centraliza la documentación de instalación, operación y mantenimiento de `assessment-engine`.

Su valor principal es servir como **índice operativo**. No todas las guías aquí tienen el mismo nivel de verificación; el lector debe usar siempre el estado declarado de cada documento y contrastar con entrypoints reales, workflows y validadores.

## Alcance

Aquí deben vivir:

- instalación y preparación del entorno;
- ejecución de pipelines y controles operativos;
- validaciones de calidad y tipado;
- runbooks y troubleshooting;
- workflows de desarrollo asistido por agentes.

No debe leerse este índice como certificación de que todo `docs/operations/` está `Verified`.

## Piezas operativas especialmente estables hoy

- [`agentic-development-workflow.md`](./agentic-development-workflow.md)
- [`engineering-quality-gates.md`](./engineering-quality-gates.md)

Estas dos piezas son la base más fiable para trabajo asistido por agentes y para cambios de código con gates obligatorios.

## Piezas que requieren lectura más cuidadosa

- [`product-owner-orchestrator.md`](./product-owner-orchestrator.md): útil, pero aún mezclada con capacidad objetivo y capacidad realmente verificada.
- [`pipeline-execution.md`](./pipeline-execution.md), [`smoke-regeneration.md`](./smoke-regeneration.md) y otras guías de ejecución: deben contrastarse con entrypoints, helpers y validadores actuales si se van a usar como base de cambio.

## Índice operativo

| Área | Documento |
|---|---|
| entorno | [`installation.md`](./installation.md) |
| CI/CD | [`ci-cd-workflows.md`](./ci-cd-workflows.md) |
| workflow con agentes | [`agentic-development-workflow.md`](./agentic-development-workflow.md) |
| calidad y tipado | [`engineering-quality-gates.md`](./engineering-quality-gates.md) |
| ejecución de pipelines | [`pipeline-execution.md`](./pipeline-execution.md) |
| runbook operativo | [`pipeline-controls-runbook.md`](./pipeline-controls-runbook.md) |
| orquestación PO-to-PR | [`product-owner-orchestrator.md`](./product-owner-orchestrator.md) |
| troubleshooting | [`troubleshooting-working.md`](./troubleshooting-working.md) |
| smoke | [`smoke-regeneration.md`](./smoke-regeneration.md) |
| coherencia | [`assessment-coherence-remediation.md`](./assessment-coherence-remediation.md) |
| firma de commits | [`signing-commits-policy.md`](./signing-commits-policy.md) |

## Regla de uso

Si una operación concreta depende de comandos, rutas, variables de entorno o comportamiento de CI, usa esta carpeta solo como punto de entrada y valida el detalle contra:

- `src/assessment_engine/application/**`
- `src/assessment_engine/application/**`
- `.github/workflows/**`
- tests o herramientas de validación relacionados
