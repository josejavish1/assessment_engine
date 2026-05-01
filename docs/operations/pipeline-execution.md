---
status: Draft
owner: docs-governance
source_of_truth:
  - ../../src/assessment_engine/scripts/run_tower_pipeline.py
  - ../../src/assessment_engine/scripts/run_global_pipeline.py
  - ../../src/assessment_engine/scripts/run_commercial_pipeline.py
  - ../../src/assessment_engine/scripts/run_intelligence_harvesting.py
  - ../../src/assessment_engine/scripts/render_web_presentation.py
  - ../../src/assessment_engine/scripts/lib/pipeline_runtime.py
  - ../architecture/tower-pipeline.md
  - ../architecture/global-commercial-pipelines.md
last_verified_against: 2026-05-01
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

El dossier generado hoy puede existir en formato legacy, `2.0` o `3.0`. La ruta activa ya consume la versión `3.0` como contrato rico y mantiene compatibilidad hacia atrás mediante adaptadores.

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

El entrypoint por torre comparte ya el mismo bootstrap base de runtime que usan los pipelines global y comercial.

Además del contexto y las respuestas, la preparación por torre ya incorpora:

- `context_summary` desde el contexto real;
- `client_context` derivado de `client_intelligence.json` cuando existe;
- target maturity por torre desde el dossier estratégico.

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

El entrypoint global ya ejecuta la consolidación canónica desde blueprints disponibles. No necesita un flag adicional para desactivar fallback legacy porque esa compatibilidad ya no forma parte de la ruta activa.

El entrypoint global ya comparte con el comercial el mismo bootstrap de entorno y de resolución del intérprete Python, para que el preflight y los pasos internos trabajen con el mismo contexto efectivo.

El payload global ya embebe un `intelligence_dossier` resumido si existe `client_intelligence.json`, para que el refinado ejecutivo no pierda señales de negocio, regulación y restricciones.

## 4. Pipeline comercial

Parte de `global_report_payload.json` y usa además blueprints por torre para construir contexto híbrido.

La fase comercial ya mezcla contexto global, catálogos tácticos de blueprint y `client_intelligence` resumido.

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
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts --client vodafone_demo --scenario vodafone-public --towers T2 T3 T5 --with-global --with-commercial --with-web
```

Ahora `--with-global` ya ejercita directamente la consolidación canónica desde blueprints.

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
