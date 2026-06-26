---
status: Draft
owner: docs-governance
source_of_truth:
- docs/README.md
- docs/ai/documentation-governance.md
- pyproject.toml
- src/
- .github/workflows/ci.yml
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: editorial
notes: Project entry point.
---

# Assessment Engine

`assessment-engine` es una fabrica de artefactos de assessment tecnologico. Su flujo principal transforma contexto de cliente, respuestas, evidencias y scoring en payloads estructurados y entregables ejecutivos, comerciales y web.

## Que leer primero

1. [docs/README.md](docs/README.md)
2. [docs/ai/documentation-governance.md](docs/ai/documentation-governance.md)
3. [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)

## Jerarquia de verdad

1. codigo, tests, schemas, workflows y configuracion real;
2. documentacion canonica en `docs/`;
3. referencia derivada o historica;
4. adaptadores por agente.

## Estructura observable del repo

- `src/application/`: entrypoints de pipelines, render y herramientas
- `src/domain/`: prompts y schemas de dominio
- `src/infrastructure/`: helpers compartidos de runtime, contratos y soporte
- `docs/`: arquitectura, operaciones, contratos y gobernanza documental
- `tests/`: validacion automatica del comportamiento vivo

## Estado documental

Este fichero es una entrada corta. No intenta describir por si solo el sistema ni certificar su estado operativo completo.

Si hay contradiccion entre este resumen y el repo ejecutable, manda el repo.
