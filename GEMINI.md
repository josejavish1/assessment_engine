---
status: Needs Review
owner: docs-governance
source_of_truth:
- docs/ai/documentation-governance.md
- docs/README.md
- docs/SYSTEM_ARCHITECTURE.md
- src/
last_verified_against: 2026-06-26
applies_to:
- gemini
doc_type: operational
diataxis: how_to
verification_mode: editorial
---

# Gemini adapter

Este archivo debe leerse como **adaptador operativo breve para Gemini**, no como documentacion canonica del proyecto.

## Orden de lectura

1. [README.md](README.md)
2. [docs/README.md](docs/README.md)
3. [docs/ai/documentation-governance.md](docs/ai/documentation-governance.md)
4. [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)
5. el documento canonico mas cercano al cambio

## Reglas

- no uses este archivo como fuente unica de verdad;
- apóyate en codigo, tests, schemas y workflows reales;
- cuando una afirmacion no pueda verificarse, trátala como `Needs Review`;
- no acumules aqui arquitectura detallada, roadmap ni memoria historica del proyecto;
- si el cambio toca arquitectura, contratos, operacion o gobernanza, actualiza la documentacion canonica correspondiente.

## Nota de transicion

`GEMINI.md` contenia memoria operativa historica util, pero parte de ese contenido mezclaba estado actual con vision futura. Esa lectura debe considerarse superada por la base comun en `docs/`.
