---
status: Draft
owner: docs-governance
source_of_truth:
  - docs/README.md
  - docs/ai/documentation-governance.md
  - pyproject.toml
  - src/assessment_engine/
  - .github/workflows/ci.yml
last_verified_against: 2026-04-30
applies_to:
  - repository
doc_type: canonical
---

# assessment-engine

`assessment-engine` es un motor de assessment tecnológico que genera entregables B2B a partir de evidencias, configuración metodológica y pipelines orquestados en Python.

La documentación canónica del proyecto empieza aquí:

- **Mapa maestro:** [`docs/README.md`](docs/README.md)
- **Política documental para humanos e IAs:** [`docs/ai/documentation-governance.md`](docs/ai/documentation-governance.md)
- **Arquitectura actual:** [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md)

## Qué encontrarás

- pipelines por torre, globales y comerciales;
- contratos de datos basados en esquemas;
- renderizado de entregables DOCX y HTML;
- modo pipeline y modo servidor de herramientas.

## Punto de entrada recomendado

1. Lee [`docs/README.md`](docs/README.md) para entender qué documentos son canónicos.
2. Revisa [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md) para la arquitectura vigente.
3. Consulta [`GEMINI.md`](GEMINI.md) solo como adaptador para Gemini y memoria operativa en transición, no como fuente única de verdad.

## Estado documental actual

La base de gobernanza documental ya está fijada, pero la auditoría de los documentos heredados sigue en curso. Consulta [`docs/documentation-map.yaml`](docs/documentation-map.yaml) para ver el estado de cada pieza (`Verified`, `Needs Review`, `Draft`, `Deprecated`).

Este proyecto incluye capacidades de orquestación automatizada PO-to-PR.

