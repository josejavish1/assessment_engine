---
status: Verified
owner: docs-governance
source_of_truth:
- AGENTS.md
- docs/ai/documentation-governance.md
- docs/README.md
last_verified_against: 2026-06-26
applies_to:
- chatgpt
doc_type: operational
diataxis: how_to
verification_mode: editorial
---

# ChatGPT adapter

Usa este archivo como adaptador breve para trabajar con OpenAI / ChatGPT / Cursor en este repositorio.

## Herencia de Gobernanza (Estricto)

Como agente de OpenAI, **DEBES leer y someterte obligatoriamente a las Leyes de Ingeniería No Negociables y el Checklist de Disciplina de Cambio definidos en [AGENTS.md](AGENTS.md)**. Esas leyes de calidad son absolutas e inmutables para esta base de código.

## Orden de lectura

1. [`README.md`](README.md)
2. [`docs/README.md`](docs/README.md)
3. [`docs/ai/documentation-governance.md`](docs/ai/documentation-governance.md)
4. [`AGENTS.md`](AGENTS.md)

## Comportamiento esperado

- apóyate en la documentación canónica y en el repo ejecutable;
- no conviertas este archivo en una segunda documentación del proyecto;
- cuando hagas cambios que afecten arquitectura, contratos, CI u operación, actualiza también la documentación canónica correspondiente;
- deja las dudas como deuda documental explícita en vez de rellenarlas con suposiciones.
