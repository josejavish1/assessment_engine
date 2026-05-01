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

También puede **reanudar una PR existente** para seguir la reconciliación:

```bash
python src/assessment_engine/scripts/tools/run_product_owner_orchestrator.py resume-pr \
  --pr-number 6 \
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
2. valida la configuración mínima del executor y hace un preflight cuando el backend lo soporta;
3. invoca un ejecutor externo configurable;
4. ejecuta validaciones estándar del repo;
5. si falla, reintenta pasando feedback de validación a la siguiente iteración.

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

Las PR creadas por este flujo incluyen un marcador oculto `<!-- orchestrator-managed -->`. Ese marcador permite que la automatización de GitHub identifique qué PRs puede reanudar sin ambigüedad.

### 5. Reconciliación post-PR

La fase post-PR **no sustituye** los controles del repo ni los rebaja. Su papel es:

1. leer el estado de la PR en GitHub;
2. distinguir entre checks pendientes, checks fallidos y review threads abiertos;
3. pasar ese feedback al executor para que haga una corrección acotada en la misma rama;
4. volver a ejecutar la validación estándar local del repo;
5. subir el follow-up commit;
6. si la rama está por detrás de `main`, sincronizarla primero y volver a validar;
7. reconsultar la PR;
8. mergear solo cuando GitHub deja de reportar checks pendientes/fallidos y no quedan conversaciones abiertas.

La sesión de reconciliación deja además artefactos de trazabilidad en `working/product_owner_requests/...`:

- `reconciliation_events.jsonl` con la secuencia de polls, syncs, reparaciones y cierres automáticos;
- `reconciliation_summary.json` con el estado final de la sesión;
- logs separados para preflight del executor, validaciones y rondas de reparación.

Por defecto puede resolver automáticamente **threads abiertos creados por bots** una vez que la rama ya no tiene checks rojos ni pendientes. Antes de cerrarlos deja una nota visible en el propio hilo explicando que el estado actual de la PR ya fue revalidado y por qué ese thread se considera cerrable. No auto-resuelve feedback humano implícitamente fuera de las reglas normales de GitHub: si la PR sigue bloqueada por requisitos externos de review o protección de rama, el merge no se fuerza.

La sincronización con la base ocurre dentro del mismo circuito controlado: el orquestador trae `origin/<base_branch>` a la rama activa, vuelve a ejecutar las validaciones locales y solo hace push si la rama sigue pasando los gates. Si esa sincronización introduce un fallo, ese fallo entra como feedback de la siguiente ronda de reparación; no se salta.

### 6. Watcher automático en GitHub

El repo puede ejecutar `.github/workflows/orchestrator-pr-reconcile.yml` para relanzar `resume-pr` cuando una PR gestionada:

1. recibe feedback de review o comentarios;
2. sale de draft con `ready_for_review`;
3. o se relanza manualmente con `workflow_dispatch`.

Reglas de seguridad del watcher:

- solo actúa sobre PRs **abiertas**, **no draft**, del **mismo repositorio**;
- exige que la PR tenga el marcador oculto del orquestador o la label `orchestrator-managed`;
- serializa la ejecución por número de PR para no correr dos reconciliaciones en paralelo;
- no se relanza por cada workflow verde intermedio: el run abierto por `pull_request` mantiene el polling de checks hasta que la PR queda lista para merge o necesita reparación;
- reutiliza `resume-pr`, así que sigue pasando por tests, quality, typing, docs-governance, sync con `main` y reglas de review;
- usa por defecto `./.github/scripts/orchestrator-gemini-executor.sh {repo_root} {task_prompt_file} {attempt}` como executor compatible con GitHub Actions;
- la regla operativa recomendada es mantener `ASSESSMENT_ORCHESTRATOR_EXECUTOR_CMD` configurado en GitHub Actions apuntando a ese wrapper del repo, para no depender de rutas locales o wrappers efímeros;
- el wrapper del repo ejecuta `gemini-2.5-pro` por defecto y fuerza la ruta Gemini de forma coherente con el resto de scripts;
- para que el executor pueda autenticarse de forma estable en GitHub Actions, el repo debe exponer una credencial Gemini o Google válida: `GEMINI_API_KEY`, `GOOGLE_API_KEY` o autenticación Google/Vertex habilitada con `GOOGLE_GENAI_USE_VERTEXAI=1` y credenciales de aplicación disponibles en el runner;
- si el preflight del executor falla por credenciales o configuración, la reconciliación aborta antes de entrar en rondas largas de reparación y deja el motivo clasificado en los artefactos de sesión.

## Política configurable

`engine_config/policies/orchestrator_policy.json` controla:

- raíz de sesiones de cambio;
- máximo de tareas;
- reintentos por tarea;
- rama base;
- modo de auto-merge;
- reconciliación post-PR (polling, rondas máximas, sync con base y resolución automática de threads de bot);
- watcher automático de reanudación para PRs gestionadas;
- validaciones estándar.

## Clasificación de fallos operativos

El orquestador separa explícitamente varias familias de fallo para evitar diagnósticos ambiguos:

- `executor_auth`: credenciales inválidas o sin permiso para que el backend de agente procese requests;
- `executor_config`: executor declarado pero mal configurado para el entorno actual;
- `executor_missing`: binario o wrapper ausente;
- `validation`: tests, quality, typing o docs-governance rojos;
- `command_failure`: otros errores no clasificados todavía.

La intención no es maquillar el error sino **fallar antes y con una causa accionable**.

## Pendiente para cierre end-to-end

El flujo ya puede operar de forma homogénea sobre Gemini también en la reconciliación automática de PRs, pero para considerar el circuito **realmente cerrado de punta a punta en GitHub Actions** sigue pendiente habilitar la credencial del executor en el repo:

1. configurar en GitHub Actions una credencial válida para Gemini o Google;
2. decidir si el watcher usará `GEMINI_API_KEY`, `GOOGLE_API_KEY` o autenticación Google/Vertex del runner;
3. verificar con una PR gestionada real que `resume-pr` completa preflight, reparación, validación y merge sin intervención manual.

## Limitaciones deliberadas del MVP

- no trabaja sobre worktree sucio salvo que se fuerce con `--allow-dirty`;
- no intenta editar código por sí mismo sin backend configurado;
- no salta la PR ni la validación;
- no bypassa tests, typing, quality, docs-governance ni conversaciones abiertas para forzar merge;
- no hace push de una sincronización con `main` sin revalidar primero la rama resultante;
- no mezcla el rol de planner con el de editor de código.

## Qué viene después

El siguiente endurecimiento natural sería:

1. registrar sesiones y métricas de éxito/reintentos;
2. clasificar riesgo para decidir cuándo auto-mergear;
3. añadir reviewers/owners automáticos por dominio;
4. soportar reanudación de sesiones abiertas;
5. integrar un backend de agente corporativo con permisos y trazabilidad más finos.
