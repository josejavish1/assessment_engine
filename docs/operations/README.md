---
status: Draft
owner: docs-governance
source_of_truth:
  - ../../pyproject.toml
  - ../../requirements.txt
  - ../../pytest.ini
  - ../../.github/workflows/ci.yml
  - ../../.github/workflows/quality.yml
  - ../../.github/workflows/typing.yml
  - ../../src/assessment_engine/scripts/tools/run_incremental_quality_gate.py
  - ../../src/assessment_engine/scripts/tools/run_incremental_typecheck.py
  - ../../tests/
last_verified_against: 2026-05-01
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Operations and validation

Esta carpeta reúne la documentación operativa mínima de `assessment-engine`: instalación, validación, CI y notas de mantenimiento que deben poder seguir tanto humanos como agentes.

## Documentos operativos actuales

- [`installation.md`](installation.md)
- [`signing-commits-policy.md`](signing-commits-policy.md)
- [`agentic-development-workflow.md`](agentic-development-workflow.md)
- [`engineering-quality-gates.md`](engineering-quality-gates.md)
- [`product-owner-orchestrator.md`](product-owner-orchestrator.md)
- [`pipeline-execution.md`](pipeline-execution.md)
- [`pipeline-controls-runbook.md`](pipeline-controls-runbook.md)
- [`smoke-regeneration.md`](smoke-regeneration.md)
- [`troubleshooting-working.md`](troubleshooting-working.md)

## Estado operativo observado

### Empaquetado

- el proyecto declara paquete instalable en `pyproject.toml`;
- usa `setuptools` con `src/` como `package-dir`;
- incluye plantillas HTML del paquete `assessment_engine`.

### Dependencias

- `pyproject.toml` define dependencias principales del paquete;
- `requirements.txt` fija un entorno más amplio de trabajo y validación;
- el workflow actual de CI instala dependencias desde `requirements.txt`.

### Tests y validación

- `pytest.ini` define `tests/` como raíz de tests;
- el workflow `Assessment Engine CI` ejecuta `pytest tests/`;
- el workflow `Incremental Quality Gate` ejecuta `ruff` solo sobre los ficheros Python cambiados en `src/assessment_engine/` y `tests/`;
- el workflow `Incremental Type Check` ejecuta `mypy` solo sobre los ficheros Python cambiados en `src/assessment_engine/` y `tests/`;
- la suite incluye ahora tests de coherencia transversal para score, banda, color y target del payload global;
- el flujo de trabajo con agentes ya tiene una guía canónica de spec mínima, alcance e invariantes antes de programar;
- ya existe un MVP de orquestador local PO-to-PR con planning, ejecución iterativa y PR automática sobre backend de agente configurable;
- existe `./bin/po-run` como entrypoint friendly para lanzar ese orquestador desde terminal sin recordar el path largo del runner;
- la suite actual incluye tests de entorno, contratos, schemas, render y utilidades.

## Flujo de validación actual

### Local

El entorno observado en este repo usa la virtualenv del proyecto:

```bash
./.venv/bin/python -m pytest tests/ -q
./.venv/bin/python src/assessment_engine/scripts/tools/run_incremental_quality_gate.py \
  --repo-root . \
  --path src/assessment_engine/scripts/tools/run_incremental_quality_gate.py
./.venv/bin/python src/assessment_engine/scripts/tools/run_incremental_typecheck.py \
  --repo-root . \
  --path src/assessment_engine/scripts/build_global_report_payload.py
```

### GitHub Actions

Los workflows operativos actuales residen en `.github/workflows/ci.yml`, `.github/workflows/quality.yml` y `.github/workflows/typing.yml`:

1. prepara Python 3.11;
2. instala dependencias con `pip install -r requirements.txt`;
3. instala el paquete en editable con `pip install -e .`;
4. ejecuta `pytest tests/` en CI;
5. ejecuta `ruff check` y `ruff format --check` sobre la superficie viva cambiada mediante el runner incremental.
6. ejecuta `mypy` sobre la superficie viva cambiada mediante el runner incremental.

## Observación relevante del baseline

En el estado validado más reciente del repo, la suite sí está en verde y `smoke_ivirma` ya dispone de baseline operativo para:

- torre T5;
- payload global;
- payload comercial.

En concreto, ya existen los artefactos de blueprint/anexo T5 y también:

- `working/smoke_ivirma/global_report_payload.json`
- `working/smoke_ivirma/commercial_report_payload.json`

La siguiente pieza con más retorno al retomar es verificar o regenerar también:

- `working/smoke_ivirma/presentation/index.html`

## Próximos documentos operativos recomendados

- promoción de `smoke-regeneration.md` y `pipeline-execution.md` cuando el baseline final quede contrastado;
- ampliación del tipado incremental y de los tests de coherencia transversales;
- endurecimiento del workflow spec-first y del review semántico para cambios asistidos por agentes;
- evolución del orquestador local hacia más métricas, clasificación de riesgo y backends de agente corporativos;
- endurecimiento de CI para smoke/golden artifacts;
- operación del modo servidor MCP;
- guía de troubleshooting de Vertex AI y credenciales.
