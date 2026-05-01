---
status: Verified
owner: docs-governance
source_of_truth:
  - docs/documentation-map.yaml
  - pyproject.toml
  - src/assessment_engine/
  - .github/workflows/ci.yml
last_verified_against: 2026-05-01
applies_to:
  - repository
doc_type: canonical
---

# Mapa maestro de documentación

Este directorio es la **entrada principal** para entender y mantener la documentación de `assessment-engine`. La misma base documental debe servir a humanos y a agentes de IA; los archivos por agente solo adaptan cómo consumirla.

## Jerarquía de verdad

1. **Código, tests, schemas, workflows y configuración real**
2. **Documentación canónica del repo**
3. **Referencia generada o heredada**
4. **Adaptadores por agente**

Si un documento narrativo contradice al código o a los contratos, **manda el repo ejecutable**.

## Dónde leer

| Documento o carpeta | Rol |
|---|---|
| `../README.md` | Entrada rápida al proyecto |
| `ai/documentation-governance.md` | Política documental común para humanos e IAs |
| `../AGENTS.md` | Puerta de entrada breve para cualquier agente |
| `../CHATGPT.md` | Adaptador breve para ChatGPT |
| `../.github/copilot-instructions.md` | Adaptador breve para Copilot |
| `SYSTEM_ARCHITECTURE.md` | Arquitectura vigente del sistema |
| `architecture/` | Descomposición canónica progresiva de la arquitectura |
| `operations/` | Operación, validación y CI |
| `operations/agentic-development-workflow.md` | Flujo canónico para programar con agentes |
| `operations/engineering-quality-gates.md` | Política canónica de calidad de implementación |
| `operations/product-owner-orchestrator.md` | Orquestador local desde petición de negocio hasta PR |
| `../.github/workflows/orchestrator-pr-reconcile.yml` | Watcher automático que reanuda PRs gestionadas del orquestador |
| `contracts/` | Contratos, matrices y plantillas de diseño |
| `reference/generated/` | Referencia derivada o heredada no canónica |
| `../GEMINI.md` | Adaptador para Gemini y memoria operativa en transición |
| `documentation-map.yaml` | Inventario máquina-legible, estado y trazabilidad |
| `../.github/pull_request_template.md` | Checklist de PR para disciplina documental |
| `../.github/CODEOWNERS` | Ownership mínimo de la documentación y gobernanza |
| `../.github/workflows/docs-governance.yml` | Validación automática de gobernanza documental |
| `../.github/workflows/quality.yml` | Gate incremental de calidad de implementación |
| `../.github/workflows/typing.yml` | Gate incremental de tipado |

## Tipos documentales

- **canónica:** describe comportamiento, arquitectura, operación o reglas oficiales;
- **operativa:** guía de trabajo o mantenimiento;
- **reference_generated:** documentación derivada o inventariada desde código;
- **archived:** material conservado solo por contexto histórico.

## Estados documentales

- `Verified`: contrastado contra la realidad del repo;
- `Needs Review`: útil, pero pendiente de verificación o realineación;
- `Draft`: válido como base inicial, aún incompleto;
- `Deprecated`: ya no debe crecer y tiene reemplazo o destino de migración.

## Auditoría inicial

| Ruta | Estado | Tipo | Observación inicial |
|---|---|---|---|
| `../README.md` | Draft | canónica | Nueva entrada del proyecto; necesita crecer con onboarding y operación |
| `ai/documentation-governance.md` | Verified | canónica | Contrato documental central |
| `SYSTEM_ARCHITECTURE.md` | Verified | canónica | Vista de alto nivel ya contrastada contra pipelines, schemas, MCP y artefactos reales |
| `architecture/` | Draft | canónica | Capa viva en expansión: ya incluye flujo empresarial, artefactos y mapa de módulos críticos contrastados |
| `operations/` | Draft | canónica | Base operativa ya separada en instalación, ejecución, controles, troubleshooting, calidad incremental, tipado y workflow con agentes |
| `contracts/` | Draft | canónica | Colección mixta: ya incluye fronteras de payload/render y contratos de artefactos, pero mantiene piezas aún en diseño |
| `reference/generated/` | Draft | reference_generated | Capa neutral para referencia derivada y para el archivo documental heredado |
| `../AGENTS.md` | Verified | operativa | Entrada corta común para cualquier agente |
| `../CHATGPT.md` | Verified | operativa | Adaptador específico para ChatGPT |
| `../.github/copilot-instructions.md` | Verified | operativa | Adaptador específico para Copilot |
| `../.github/pull_request_template.md` | Draft | operativa | Checklist de PR para forzar trazabilidad documental |
| `../.github/CODEOWNERS` | Draft | operativa | Ownership mínimo para docs y gobernanza |
| `../.github/workflows/docs-governance.yml` | Draft | operativa | Workflow de validación de metadata y reglas documentales |
| `../GEMINI.md` | Needs Review | operativa | Pasa a ser adaptador; contiene verdad útil mezclada con memoria histórica |
| `reference/generated/legacy-gemini/` | Deprecated | reference_generated | Archivo de la documentación heredada de Gemini; ya no compite con la capa canónica |

## Qué viene después

1. auditar documento por documento contra código y tests;
2. decidir qué partes del archivo heredado en `reference/generated/legacy-gemini/` pasan a canónico y cuáles siguen siendo derivadas;
3. seguir limpiando referencias antiguas que puedan inducir a leer el archivo como verdad principal;
4. refinar la auditoría de arquitectura, contratos y operación;
5. endurecer la nueva capa de calidad hacia más tipado y coherencia transversal;
6. institucionalizar mejor el workflow spec-first y el review semántico en los cambios con agentes;
7. convertir las reglas del `documentation-map` en checks automáticos de CI.

## Estado de continuidad actual

Si una sesión nueva necesita reanudar el trabajo sin contexto previo, el estado operativo relevante es este:

- la gobernanza documental pasa;
- la puerta incremental de calidad ya puede bloquear deuda nueva en la superficie viva;
- la puerta incremental de tipado ya puede bloquear deuda nueva en la superficie viva;
- ya existe una guía canónica para exigir spec mínima y alcance explícito en cambios asistidos por agentes;
- ya existe un MVP de orquestador local PO-to-PR apoyado en backend de agente configurable;
- ya existe un watcher de GitHub que puede reanudar PRs gestionadas del orquestador cuando fallan checks o aparece feedback nuevo;
- el baseline smoke de `smoke_ivirma` ya está cerrado para T5, global, comercial y web;
- la suite completa de `pytest` pasa.

El siguiente tramo natural ya no es regenerar artefactos del smoke, sino seguir en paralelo dos líneas:

- promover y mantener verificada la documentación operativa del smoke en `docs/documentation-map.yaml`;
- continuar la revisión de arquitectura, contratos y adaptadores que siguen en `Draft` o `Needs Review`;
- ampliar los checks de coherencia a más dominios y endurecer el tipado incremental hacia módulos completos;
- bajar el workflow spec-first a plantillas, hábitos de review y cambios más pequeños por iteración;
- evolucionar el orquestador PO-to-PR hacia clasificación de riesgo y sesiones reanudables.
