---
status: Verified
owner: docs-governance
source_of_truth:
  - docs/ai/documentation-governance.md
  - docs/README.md
  - docs/documentation-map.yaml
last_verified_against: 2026-04-30
applies_to:
  - ai-agents
doc_type: operational
---

# AGENTS

Este fichero es la **puerta de entrada corta para cualquier agente de IA** que trabaje en `assessment-engine`.

## Lee en este orden

1. [`README.md`](README.md)
2. [`docs/README.md`](docs/README.md)
3. [`docs/ai/documentation-governance.md`](docs/ai/documentation-governance.md)
4. el documento canónico más cercano al cambio que vayas a hacer

## Reglas mínimas

- no trates este archivo como fuente de verdad del proyecto;
- no introduzcas aquí arquitectura, contratos ni operación detallada;
- usa el código, tests, schemas y workflows como verdad primaria;
- actualiza `docs/documentation-map.yaml` si cambia el estado o el destino de un documento;
- si una afirmación no puede verificarse, márcala como `Needs Review` en vez de inventarla.

## Dónde escribir

- arquitectura: `docs/SYSTEM_ARCHITECTURE.md` o futura `docs/architecture/`
- contratos: `docs/contracts/`
- política documental: `docs/ai/documentation-governance.md`
- índice y estado: `docs/README.md` y `docs/documentation-map.yaml`

Los archivos específicos por agente, como `GEMINI.md`, `CHATGPT.md` o `.github/copilot-instructions.md`, solo adaptan esta misma base común.
