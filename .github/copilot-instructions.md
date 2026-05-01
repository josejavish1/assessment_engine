---
status: Verified
owner: docs-governance
source_of_truth:
  - AGENTS.md
  - docs/ai/documentation-governance.md
  - docs/README.md
  - docs/operations/agentic-development-workflow.md
  - docs/operations/engineering-quality-gates.md
last_verified_against: 2026-05-01
applies_to:
  - copilot
doc_type: operational
---

# Copilot instructions

Esta guía adapta la política documental central para GitHub Copilot y otros flujos de trabajo basados en Copilot.

## Lee primero

1. [`../README.md`](../README.md)
2. [`../docs/README.md`](../docs/README.md)
3. [`../docs/ai/documentation-governance.md`](../docs/ai/documentation-governance.md)
4. [`../AGENTS.md`](../AGENTS.md)
5. [`../docs/operations/agentic-development-workflow.md`](../docs/operations/agentic-development-workflow.md) si vas a programar con ayuda de IA
6. [`../docs/operations/engineering-quality-gates.md`](../docs/operations/engineering-quality-gates.md) si vas a generar o editar código

## Reglas

- trata la documentación canónica del repo como fuente principal;
- no escribas verdad nueva sobre el sistema solo en este archivo;
- cuando cambien código, contracts, workflows o configuración, revisa también el documento canónico asociado;
- trabaja a partir de una spec mínima explícita, con alcance e invariantes claros;
- convierte reglas de implementación relevantes en helpers, schemas, tests o workflows en vez de dejarlas solo en prompts;
- usa `docs/documentation-map.yaml` como inventario de estado documental.
