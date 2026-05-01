---
status: Verified
owner: docs-governance
source_of_truth:
  - ../../engine_config/policies/orchestrator_policy.json
  - ../../engine_config/runtime_manifest.json
  - ../../src/assessment_engine/scripts/lib/product_owner_models.py
  - ../../src/assessment_engine/scripts/tools/run_product_owner_orchestrator.py
  - ../../src/assessment_engine/prompts/product_owner_prompts.py
  - ../../.github/workflows/ci.yml
  - ../../.github/workflows/quality.yml
  - ../../.github/workflows/typing.yml
last_verified_against: 2026-05-01
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Product owner orchestrator

Esta pieza describe el MVP del **orquestador local PO-to-PR** del repo. Su objetivo es permitir que un product owner exprese una necesidad de negocio en lenguaje natural y que el sistema haga detrás el trabajo técnico repetible:

- traducir la intención a una spec mínima;
- desglosar el cambio en tareas pequeñas;
- ejecutar cada tarea con un backend de agente configurable;
- validar el resultado con los gates del repo;
- crear commit, PR y auto-merge si la política lo permite.

## Principio de arquitectura

El orquestador **no está acoplado a un vendor único de edición de código**. Mantiene la gobernanza, el desglose y la validación en el repo, pero delega la implementación concreta a un **executor command** configurable.

Esto sigue mejor el patrón enterprise de 2026:

- orquestación local y auditable;
- autonomía acotada;
- branch-per-change;
- PR-based workflow;
- validación estándar antes de merge.

## Entrada esperada

El CLI `run_product_owner_orchestrator.py` acepta una petición de negocio como texto o fichero:

```bash
python src/assessment_engine/scripts/tools/run_product_owner_orchestrator.py plan \
  --request "Quiero que el informe global priorice los riesgos críticos de continuidad"
```

o bien:

```bash
python src/assessment_engine/scripts/tools/run_product_owner_orchestrator.py run \
  --request-file ./request.txt \
  --executor-command "mi-agente-coder --repo {repo_root} --task-file {task_prompt_file}"
```

## Fases del MVP

### 1. Planificación

Usa el rol de modelo `product_owner_planner` para generar:

- spec mínima;
- branch name;
- commit title;
- PR title;
- nivel de riesgo;
- tareas pequeñas con source_of_truth, invariants y validation.

El bundle se guarda en `working/product_owner_requests/<timestamp>_<slug>/`.

### 2. Ejecución iterativa por tarea

Para cada tarea:

1. genera un prompt estructurado con el plan global y el task actual;
2. invoca un ejecutor externo configurable;
3. ejecuta validaciones estándar del repo;
4. si falla, reintenta pasando feedback de validación a la siguiente iteración.

### 3. Validación estándar

El MVP usa:

- `pytest tests/ -q`
- `validate_documentation_governance.py`
- `run_incremental_quality_gate.py`
- `run_incremental_typecheck.py`

La selección incremental de Python se calcula desde `git diff`.

### 4. Integración en GitHub

Si todas las tareas pasan:

1. hace commit;
2. crea PR con spec y checklist resumidos;
3. activa auto-merge si la policy lo permite y el usuario no lo desactiva.

## Política configurable

`engine_config/policies/orchestrator_policy.json` controla:

- raíz de sesiones de cambio;
- máximo de tareas;
- reintentos por tarea;
- rama base;
- modo de auto-merge;
- validaciones estándar.

## Limitaciones deliberadas del MVP

- no trabaja sobre worktree sucio salvo que se fuerce con `--allow-dirty`;
- no intenta editar código por sí mismo sin backend configurado;
- no salta la PR ni la validación;
- no mezcla el rol de planner con el de editor de código.

## Qué viene después

El siguiente endurecimiento natural sería:

1. registrar sesiones y métricas de éxito/reintentos;
2. clasificar riesgo para decidir cuándo auto-mergear;
3. añadir reviewers/owners automáticos por dominio;
4. soportar reanudación de sesiones abiertas;
5. integrar un backend de agente corporativo con permisos y trazabilidad más finos.
