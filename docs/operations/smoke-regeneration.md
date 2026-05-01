---
status: Draft
owner: docs-governance
source_of_truth:
  - ../../src/assessment_engine/scripts/tools/generate_smoke_data.py
  - ../../src/assessment_engine/scripts/tools/check_vertex_ai_access.py
  - ../../src/assessment_engine/scripts/tools/regenerate_smoke_artifacts.py
  - ../../src/assessment_engine/scripts/lib/runtime_env.py
  - ../../src/assessment_engine/scripts/lib/ai_client.py
  - ../../src/assessment_engine/scripts/run_tower_pipeline.py
  - ../../src/assessment_engine/scripts/run_global_pipeline.py
  - ../../src/assessment_engine/scripts/run_commercial_pipeline.py
  - ../../src/assessment_engine/scripts/render_web_presentation.py
  - ../../tests/test_contract_handover.py
  - ../../tests/test_t5_golden.py
  - ../../tests/test_payload_validation.py
last_verified_against: 2026-05-01
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Smoke artifact regeneration

Este playbook deja reproducible la regeneración del caso `smoke_ivirma`, que es la referencia usada por varios tests de contratos, payloads y golden DOCX.

## Estado de referencia actual

En la validación más reciente del repositorio ya quedaron regenerados y validados:

- `working/smoke_ivirma/T5/blueprint_t5_payload.json`
- `working/smoke_ivirma/T5/approved_annex_t5.template_payload.json`
- `working/smoke_ivirma/T5/Blueprint_Transformacion_T5_smoke_ivirma.docx`
- `working/smoke_ivirma/T5/annex_t5_smoke_ivirma_final.docx`
- `working/smoke_ivirma/global_report_payload.json`
- `working/smoke_ivirma/commercial_report_payload.json`
- `working/smoke_ivirma/presentation/index.html`

Además, la suite completa de `pytest` quedó en verde tras regenerar esos artefactos.

El siguiente tramo recomendado al retomar ya no es volver a depurar T5/global/commercial/web, sino mantener alineada la documentación operativa y seguir promoviendo documentos desde `Draft` hacia `Verified` cuando estén contrastados contra código y artefactos reales.

## Qué resuelve

Permite regenerar de forma trazable:

- inputs sintéticos locales en `working/smoke_ivirma/`;
- artefactos deterministas de preparación (`case_input.json`, `evidence_ledger.json`, `scoring_output.json`, `findings.json`);
- y, si hay acceso operativo a Vertex AI, los payloads y DOCX finales de T5, además de los outputs global/comercial/web.

## Prerrequisitos

### Entorno local

```bash
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m pip install -e .
```

### Para el tramo con IA

El tramo que genera:

- `blueprint_t5_payload.json`
- `approved_annex_t5.template_payload.json`
- DOCX de blueprint y annex

depende de los agentes de Vertex AI usados por:

- `run_tower_blueprint_engine.py`
- `run_executive_annex_synthesizer.py`
- `run_executive_refiner.py`
- `run_commercial_refiner.py`

Por tanto, para llegar al final del smoke necesitas credenciales operativas válidas para Vertex AI mediante el mecanismo de autenticación que use tu entorno.

Antes de lanzar el tramo IA, puedes validar el acceso base con:

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.check_vertex_ai_access
```

## Runner recomendado

El repo incorpora el entrypoint:

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts
```

El runner ya no resuelve de forma dispersa el bootstrap del runtime ni las rutas principales del caso smoke. La preparación del entorno compartido, la resolución de `working/`, `client_dir`, `case_dir` y varias rutas de artefactos/payloads viven ahora en helpers comunes (`pipeline_runtime.py` y `runtime_paths.py`), lo que reduce divergencias entre el flujo de torre, los pipelines global/commercial y el dashboard web.

Por defecto trabaja sobre:

- cliente: `smoke_ivirma`
- torre: `T5`
- seed: `42`

Si quieres probar un modelo más rápido para el rol `writer_fast`, puedes usar:

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts \
  --writer-model gemini-2.5-flash
```

## Modos útiles

### 1. Ver el flujo exacto sin ejecutar nada

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts --dry-run
```

### 1.b. Forzar diagnóstico rápido del tramo IA

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts \
  --writer-model gemini-2.5-flash \
  --vertex-query-timeout-seconds 30 \
  --ai-step-timeout-seconds 60
```

Esto no arregla Vertex AI, pero evita que un cuelgue se vea como silencio indefinido.

### 2. Regenerar solo la parte local y determinista

No requiere Vertex AI.

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts --local-only
```

Esto deja preparados:

- `working/smoke_ivirma/context.txt`
- `working/smoke_ivirma/responses.txt`
- `working/smoke_ivirma/T5/case_input.json`
- `working/smoke_ivirma/T5/evidence_ledger.json`
- `working/smoke_ivirma/T5/scoring_output.json`
- `working/smoke_ivirma/T5/findings.json`

### 3. Regenerar la torre T5 completa

Requiere Vertex AI operativo.

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts
```

El runner genera primero la parte local y después reanuda `run_tower_pipeline.py` desde:

- `Engine: Tower Strategic Blueprint`

Así evita repetir las fases deterministas y deja explícita la frontera entre preparación local y síntesis asistida por IA.

Además, el smoke conserva compatibilidad con la resolución legacy de `working/` cuando algún consumidor aún arranca desde rutas antiguas, pero la ruta preferida y documentada pasa a ser la capa común de helpers de runtime/path.

### 4. Extender el smoke a outputs globales, comerciales y web

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts \
  --with-global \
  --with-commercial \
  --with-web
```

Si quieres forzar que el tramo global use solo blueprints modernos:

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts \
  --with-global \
  --global-blueprint-only
```

Ese flag se propaga a `run_global_pipeline.py` como `--blueprint-only`, de modo que el builder global no consume `approved_annex_*.refined.json` aunque existan en el workspace.

## Artefactos esperados

### Torre T5

- `working/smoke_ivirma/T5/blueprint_t5_payload.json`
- `working/smoke_ivirma/T5/approved_annex_t5.template_payload.json`
- `working/smoke_ivirma/T5/Blueprint_Transformacion_T5_smoke_ivirma.docx`
- `working/smoke_ivirma/T5/annex_t5_smoke_ivirma_final.docx`

### Cliente completo

- `working/smoke_ivirma/global_report_payload.json`
- `working/smoke_ivirma/commercial_report_payload.json`
- `working/smoke_ivirma/presentation/index.html`

## Relación con la suite

Cuando faltan artefactos del baseline smoke, hoy fallan o se saltan principalmente:

- `tests/test_contract_handover.py`
- `tests/test_t5_golden.py`
- `tests/test_payload_validation.py`

Este playbook es la ruta preferida para distinguir entre:

1. ausencia de artefacto;
2. fallo real de contrato;
3. problema de credenciales o ejecución IA.

En la última regeneración validada, esos tests ya quedaron resueltos para `smoke_ivirma` porque el baseline T5 + global + comercial existe y el dashboard web final también está renderizado.

## Señal práctica de bloqueo

Si el runner:

- deja `case_input.json`, `evidence_ledger.json`, `scoring_output.json` y `findings.json`;
- pero no llega a crear `blueprint_t5_payload.json` ni `approved_annex_t5.template_payload.json`;

entonces el problema ya no está en la preparación local del smoke. El siguiente punto a revisar es la ejecución de Vertex AI en:

- `Engine: Tower Strategic Blueprint`
- `Engine: Executive Annex Synthesizer`

Con el preflight nuevo, primero deberías ver un fallo corto si hay problema de:

- autenticación;
- proyecto/location;
- acceso base al modelo publicado.

Y con `ASSESSMENT_VERTEX_QUERY_TIMEOUT_SECONDS` o `--vertex-query-timeout-seconds`, un cuelgue en consulta se convierte en timeout explícito.

Si el atasco ocurre antes incluso de que el agente empiece a responder, usa `ASSESSMENT_AI_STEP_TIMEOUT_SECONDS` o `--ai-step-timeout-seconds` para cortar el paso completo con un error visible.
