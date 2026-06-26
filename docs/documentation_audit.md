---
status: Needs Review
owner: docs-governance
source_of_truth:
- docs/documentation-map.yaml
- docs/README.md
- docs/ai/documentation-governance.md
last_verified_against: 2026-06-26
applies_to:
- docs
- humans
- ai-agents
doc_type: operational
diataxis: explanation
verification_mode: editorial
last_updated: 2026-06-26
---

# Auditoría de documentación del proyecto

Este documento registra la **lectura narrativa más reciente** del estado de la documentación. No sustituye a `docs/documentation-map.yaml`, y no debe afirmar completitud o cierre si el inventario o la clasificación todavía tienen deriva.

## Diagnóstico actual

A fecha de **2026-06-26**, la situación observable es esta:

- la documentación ya tiene una base estructural razonable;
- la principal brecha ya no es falta de texto, sino **gobernanza insuficientemente estricta**;
- el `documentation-map` cubre mucho, pero todavía mezcla piezas fiables con otras sobreclasificadas;
- varias páginas combinan descripción operativa con roadmap, histórico o visión futura;
- `docs/reference/generated/` y `docs/strategy/` deben leerse fuera de la capa operativa principal.

## Evaluación resumida por zonas

| Zona | Lectura recomendada |
|---|---|
| `docs/ai/` | base de gobernanza más estable |
| `docs/SYSTEM_ARCHITECTURE.md` | vista canónica de alto nivel razonablemente fiable |
| `docs/contracts/` | en general la parte más madura del corpus vivo |
| `docs/operations/` | útil, pero desigual; no todo merece el mismo nivel de confianza |
| `docs/architecture/` | mezcla piezas canónicas y piezas todavía en consolidación |
| `docs/audits/` | histórico y backlog, no verdad operativa |
| `docs/strategy/` | visión futura, no estado actual |
| `docs/reference/generated/` | referencia derivada y legado archivado |

## Reetiquetados que esta auditoría considera necesarios

| Ruta | Estado propuesto | Motivo |
|---|---|---|
| [`docs/documentation-map.yaml`](documentation-map.yaml) | Needs Review | cubre mucho, pero no debe venderse todavía como inventario plenamente fiable |
| [`docs/README.md`](README.md) | Needs Review | debe orientar sin mezclar estado actual con continuidad o visión |
| [`docs/operations/README.md`](operations/README.md) | Needs Review | debe actuar como índice, no como validación implícita de toda la carpeta |
| [`docs/documentation_audit.md`](documentation_audit.md) | Needs Review | no puede afirmar cierre ni completitud mientras el mapa siga en revisión |

## Prioridades siguientes

1. bajar a `Needs Review` o `Draft` cualquier página que describa capacidad operativa no contrastada;
2. seguir separando material operativo, histórico y estratégico;
3. endurecer la clasificación del legado bajo `docs/reference/generated/legacy-gemini/`;
4. hacer una pasada archivo por archivo en `docs/operations/` y `docs/architecture/` para consolidar `Verified` solo donde proceda.
