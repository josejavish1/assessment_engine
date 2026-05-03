---
status: Verified
owner: docs-governance
source_of_truth:
  - docs/documentation-map.yaml
  - pyproject.toml
  - src/assessment_engine/
  - .github/workflows/ci.yml
last_verified_against: 2026-05-05
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
| [`../README.md`](../README.md) | Entrada rápida al proyecto |
| [`ai/documentation-governance.md`](ai/documentation-governance.md) | Política documental común para humanos e IAs |
| [`../AGENTS.md`](../AGENTS.md) | Puerta de entrada breve para cualquier agente |
| [`../CHATGPT.md`](../CHATGPT.md) | Adaptador breve para ChatGPT |
| [`../.github/copilot-instructions.md`](../.github/copilot-instructions.md) | Adaptador breve para Copilot |
| [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) | Arquitectura vigente del sistema |
| [`architecture/`](architecture/README.md) | Descomposición canónica progresiva de la arquitectura |
| [`architecture/elite-governance-2026.md`](architecture/elite-governance-2026.md) | Arquitectura de Gobernanza "The Apex" |
| [`operations/`](operations/README.md) | Operación, validación y CI |
| [`operations/signing-commits-policy.md`](operations/signing-commits-policy.md) | Política y guía para la firma de commits |
| [`operations/agentic-development-workflow.md`](operations/agentic-development-workflow.md) | Flujo canónico para programar con agentes |
| [`operations/engineering-quality-gates.md`](operations/engineering-quality-gates.md) | Política canónica de calidad de implementación |
| [`operations/product-owner-orchestrator.md`](operations/product-owner-orchestrator.md) | Orquestador local desde petición de negocio hasta PR |
| [`../bin/po-run`](../bin/po-run) | Wrapper friendly para lanzar el orquestador local desde terminal |
| [`../.github/workflows/orchestrator-pr-reconcile.yml`](../.github/workflows/orchestrator-pr-reconcile.yml) | Watcher automático que reanuda PRs gestionadas del orquestador |
| [`../.github/scripts/orchestrator-gemini-executor.sh`](../.github/scripts/orchestrator-gemini-executor.sh) | Wrapper de executor para usar Gemini CLI dentro de GitHub Actions |
| [`contracts/`](contracts/artifact-contracts.md) | Contratos, matrices y plantillas de diseño |
| [`reference/generated/`](reference/generated/legacy-gemini-index.md) | Referencia derivada o heredada no canónica |
| [`../GEMINI.md`](../GEMINI.md) | Adaptador para Gemini y memoria operativa en transición |
| [`documentation-map.yaml`](documentation-map.yaml) | Inventario máquina-legible del estado de la documentación |
| [`documentation_audit.md`](documentation_audit.md) | Seguimiento del estado de salud de la documentación |
| [`../.github/pull_request_template.md`](../.github/pull_request_template.md) | Checklist de PR para disciplina documental y coherencia |
| [`../.github/CODEOWNERS`](../.github/CODEOWNERS) | Ownership mínimo de la documentación y gobernanza |
| [`../.github/workflows/docs-governance.yml`](../.github/workflows/docs-governance.yml) | Validación automática de gobernanza documental |
| [`../.github/workflows/quality.yml`](../.github/workflows/quality.yml) | Gate incremental de calidad de implementación |
| [`../.github/workflows/typing.yml`](../.github/workflows/typing.yml) | Gate incremental de tipado |

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
- la semántica global de score, banda, color y target ya documenta que el builder consume `global_maturity_policy.py` y no una reinterpretación local propia;
- la plantilla de PR ya obliga también a explicitar checks de coherencia cuando un cambio toca semántica de assessment o salidas cliente-facing;
- ya existe un MVP de orquestador local PO-to-PR apoyado en backend de agente configurable;
- ya existe `./bin/po-run` como entrada corta e interactiva para lanzar ese flujo desde terminal;
- el orquestador local ya acota los `run` del executor con timeout explícito y evita que la propia ejecución ensucie el worktree con `__pycache__/`;
- ya existe un watcher de GitHub que puede reanudar PRs gestionadas del orquestador cuando fallan checks o aparece feedback nuevo;
- ya existe un executor del repo compatible con GitHub Actions para que el watcher no dependa de rutas locales;
- el baseline smoke de `smoke_ivirma` ya está cerrado para T5, global, comercial y web;
- la suite completa de `pytest` pasa.
