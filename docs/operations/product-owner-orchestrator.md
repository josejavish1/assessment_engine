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
- crear commit, PR y merge automático solo cuando la PR queda realmente limpia.

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
3. inspecciona checks y conversaciones de review en GitHub;
4. si detecta fallos o feedback abierto, entra en un ciclo de reconciliación;
5. solo mergea cuando la PR queda verde y sin conversaciones bloqueantes.

### 5. Reconciliación post-PR

La fase post-PR **no sustituye** los controles del repo ni los rebaja. Su papel es:

1. leer el estado de la PR en GitHub;
2. distinguir entre checks pendientes, checks fallidos y review threads abiertos;
3. pasar ese feedback al executor para que haga una corrección acotada en la misma rama;
4. volver a ejecutar la validación estándar local del repo;
5. subir el follow-up commit;
6. reconsultar la PR;
7. mergear solo cuando GitHub deja de reportar checks pendientes/fallidos y no quedan conversaciones abiertas.

Por defecto puede resolver automáticamente **threads abiertos creados por bots** una vez que la rama ya no tiene checks rojos ni pendientes. No auto-resuelve feedback humano implícitamente fuera de las reglas normales de GitHub: si la PR sigue bloqueada por requisitos externos de review o protección de rama, el merge no se fuerza.

## Política configurable

`engine_config/policies/orchestrator_policy.json` controla:

- raíz de sesiones de cambio;
- máximo de tareas;
- reintentos por tarea;
- rama base;
- modo de auto-merge;
- reconciliación post-PR (polling, rondas máximas y resolución automática de threads de bot);
- validaciones estándar.

## Limitaciones deliberadas del MVP

- no trabaja sobre worktree sucio salvo que se fuerce con `--allow-dirty`;
- no intenta editar código por sí mismo sin backend configurado;
- no salta la PR ni la validación;
- no bypassa tests, typing, quality, docs-governance ni conversaciones abiertas para forzar merge;
- no mezcla el rol de planner con el de editor de código.

## Qué viene después

El siguiente endurecimiento natural sería:

1. registrar sesiones y métricas de éxito/reintentos;
2. clasificar riesgo para decidir cuándo auto-mergear;
3. añadir reviewers/owners automáticos por dominio;
4. soportar reanudación de sesiones abiertas;
5. integrar un backend de agente corporativo con permisos y trazabilidad más finos.
