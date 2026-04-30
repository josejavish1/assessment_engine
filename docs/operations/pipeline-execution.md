---
status: Draft
owner: docs-governance
source_of_truth:
  - ../../src/assessment_engine/scripts/run_tower_pipeline.py
  - ../../src/assessment_engine/scripts/run_global_pipeline.py
  - ../../src/assessment_engine/scripts/run_commercial_pipeline.py
  - ../../src/assessment_engine/scripts/run_intelligence_harvesting.py
  - ../../src/assessment_engine/scripts/render_web_presentation.py
  - ../architecture/tower-pipeline.md
  - ../architecture/global-commercial-pipelines.md
last_verified_against: 2026-04-30
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Pipeline execution guide

Esta guía resume cómo lanzar los flujos principales del proyecto usando los entrypoints reales del repo.

## 1. Inteligencia de cliente

Genera:

- `working/<client>/client_intelligence.json`

Comando:

```bash
./.venv/bin/python -m assessment_engine.scripts.run_intelligence_harvesting <client_name>
```

Úsalo cuando quieras enriquecer el contexto estratégico antes del análisis por torre.

## 2. Pipeline por torre

Genera la cadena principal por torre:

- `case_input.json`
- `evidence_ledger.json`
- `scoring_output.json`
- `findings.json`
- `blueprint_<tower>_payload.json`
- `approved_annex_<tower>.template_payload.json`
- entregables DOCX

Comando:

```bash
./.venv/bin/python -m assessment_engine.scripts.run_tower_pipeline \
  --tower T5 \
  --client ivirma \
  --context-file /ruta/al/contexto.docx \
  --responses-file /ruta/a/respuestas.txt
```

Reanudación opcional:

```bash
./.venv/bin/python -m assessment_engine.scripts.run_tower_pipeline \
  --tower T5 \
  --client ivirma \
  --context-file /ruta/al/contexto.docx \
  --responses-file /ruta/a/respuestas.txt \
  --start-from "Engine: Executive Annex Synthesizer"
```

## 3. Pipeline global ejecutivo

Parte de los blueprints y/o artefactos de torre disponibles en `working/<client>/`.

Genera:

- `global_report_payload.json`
- `Informe_Ejecutivo_Consolidado_<client>.docx`

Comando:

```bash
./.venv/bin/python -m assessment_engine.scripts.run_global_pipeline <client_name>
```

## 4. Pipeline comercial

Parte de `global_report_payload.json` y usa además blueprints por torre para construir contexto híbrido.

Genera:

- `commercial_report_payload.json`
- `Account_Action_Plan_<client>.docx`

Comando:

```bash
./.venv/bin/python -m assessment_engine.scripts.run_commercial_pipeline <client_name>
```

## 5. Dashboard web

Parte de:

- `global_report_payload.json`
- blueprints disponibles por torre

Genera:

- `working/<client>/presentation/index.html`

Comando:

```bash
./.venv/bin/python -m assessment_engine.scripts.render_web_presentation <client_name>
```

## 6. Smoke reproducible para `smoke_ivirma`

Para regenerar el caso que usan los tests de contratos y golden files, usa el runner dedicado:

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts
```

Variantes útiles:

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts --dry-run
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts --local-only
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts --with-global --with-commercial --with-web
```

La guía detallada está en [`smoke-regeneration.md`](smoke-regeneration.md).

Si necesitas validar Vertex AI antes de lanzar cualquier pipeline con agentes:

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.check_vertex_ai_access
```

## Orden operativo recomendado

1. preparar o generar `client_intelligence.json` si necesitas contexto estratégico;
2. ejecutar una o varias torres;
3. lanzar el pipeline global;
4. lanzar el pipeline comercial;
5. generar el dashboard web si necesitas una vista interactiva.

## Validación mínima tras cada fase

- tras torre: comprobar que existe `blueprint_<tower>_payload.json`;
- tras global: comprobar que existe `global_report_payload.json`;
- tras comercial: comprobar que existe `commercial_report_payload.json`;
- tras web: comprobar que existe `working/<client>/presentation/index.html`.
