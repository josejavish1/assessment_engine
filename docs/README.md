---
status: Needs Review
owner: docs-governance
source_of_truth:
- docs/documentation-map.yaml
- src/
- .github/workflows/ci.yml
- .github/workflows/docs-governance.yml
last_verified_against: 2026-06-26
applies_to:
- repository
doc_type: canonical
diataxis: explanation
verification_mode: editorial
---

# Mapa maestro de documentación

Este directorio es la **entrada principal** para entender y mantener la documentación de `assessment-engine`.

Su trabajo es orientar al lector hacia la capa correcta y dejar visible qué piezas describen el estado actual, cuáles son material operativo y cuáles deben leerse como referencia derivada, histórico o visión futura.

## Jerarquía de verdad

1. **Código, tests, schemas, workflows y configuración real**
2. **Documentación canónica del repo**
3. **Referencia generada o heredada**
4. **Adaptadores por agente**

Si un documento narrativo contradice al código o a los contratos, **manda el repo ejecutable**.

## Cómo leer el árbol documental

| Si necesitas... | Lee primero |
|---|---|
| ubicar la política documental | [`ai/documentation-governance.md`](ai/documentation-governance.md) |
| entender la arquitectura actual a alto nivel | [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) |
| bajar a piezas arquitectónicas más concretas | [`architecture/`](architecture/README.md) |
| entender operación, CI y calidad | [`operations/`](operations/README.md) |
| entender contratos y payloads | [`contracts/`](contracts/artifact-contracts.md) |
| consultar referencia derivada o material heredado | [`reference/generated/`](reference/generated/README.md) |
| ver el inventario máquina-legible y sus estados declarados | [`documentation-map.yaml`](documentation-map.yaml) |
| ver la auditoría narrativa más reciente | [`documentation_audit.md`](documentation_audit.md) |

## Tipos documentales

- **canónica:** describe comportamiento, arquitectura, operación o reglas oficiales;
- **operativa:** guía de trabajo o mantenimiento;
- **reference_generated:** documentación derivada del código, inventarios o legado técnico;
- **archived:** material histórico que no debe crecer.

## Estados documentales

- `Verified`: contrastado contra la realidad del repo;
- `Needs Review`: útil, pero pendiente de verificación o realineación;
- `Draft`: base inicial válida, todavía incompleta;
- `Deprecated`: ya no debe crecer y tiene reemplazo o destino de migración.

## Estado de gobernanza hoy

La base documental ya no está desordenada, pero **todavía no puede considerarse completamente fiable como corpus SOTA**. El problema principal actual es de gobernanza:

- el inventario máquina-legible existe, pero mezcla piezas bien contrastadas con otras todavía sobreclasificadas;
- varios documentos combinan descripción del estado actual con roadmap, visión futura o histórico;
- `Verified` debe reservarse para piezas realmente contrastadas contra código, tests, contratos o workflows;
- `docs/reference/generated/` y `docs/strategy/` no deben leerse como verdad operativa por defecto.

## Lectura operativa recomendada

| Capa | Regla de lectura |
|---|---|
| `README.md` y esta página | entrada y orientación, no contrato suficiente por sí solos |
| `ai/`, `SYSTEM_ARCHITECTURE.md`, `contracts/`, piezas operativas verificadas | base preferente para cambios reales |
| `architecture/` | usar primero las piezas verificadas; el resto puede seguir en consolidación |
| `operations/` | usar para ejecución y mantenimiento, comprobando el estado declarado de cada guía |
| `audits/` | histórico útil y backlog de mejora, no verdad operativa directa |
| `strategy/` | visión futura o posicionamiento, no descripción del sistema actual |
| `reference/generated/` | referencia derivada y legado archivado, no fuente principal |

## Qué hacer cuando haya duda

1. comprobar `docs/documentation-map.yaml`;
2. leer el front matter del documento concreto;
3. contrastar contra código, tests, schemas o workflows declarados en `source_of_truth`;
4. si el contraste no es claro, tratar el documento como `Needs Review`.
