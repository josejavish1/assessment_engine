---
status: Verified
owner: docs-governance
source_of_truth:
  - docs/documentation-map.yaml
last_verified_against: "2026-06-04"
applies_to: ["humans", "ai-agents"]
doc_type: canonical
notes: "Project Master Entry."
---

# Assessment Engine

Este proyecto es una factoría industrial de evaluación de arquitectura tecnológica.

## Visión General
El motor utiliza IA generativa y una metodología estructurada por torres (T1-T10) para analizar el estado actual de los clientes y proponer planes de transformación.

## Arquitectura Hexagonal
El proyecto sigue los principios de Clean Architecture:
- **Domain:** Lógica de negocio y reglas de puntuación.
- **Application:** Orquestación de pipelines.
- **Adapters:** Conectores externos.

## Gobernanza Soberana
El desarrollo está gobernado por radares automáticos que garantizan:
1. Zero Vendor Lock-in.
2. Integridad de tipado Tier-1.
3. Disciplina de cambio absoluta.
