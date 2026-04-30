---
status: Draft
owner: docs-governance
source_of_truth:
  - ../../pyproject.toml
  - ../../requirements.txt
  - ../../pytest.ini
  - ../../.github/workflows/ci.yml
  - ../../tests/
last_verified_against: 2026-04-30
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Operations and validation

Esta carpeta reúne la documentación operativa mínima de `assessment-engine`: instalación, validación, CI y notas de mantenimiento que deben poder seguir tanto humanos como agentes.

## Documentos operativos actuales

- [`installation.md`](installation.md)
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
- la suite actual incluye tests de entorno, contratos, schemas, render y utilidades.

## Flujo de validación actual

### Local

El entorno observado en este repo usa la virtualenv del proyecto:

```bash
./.venv/bin/python -m pytest tests/ -q
```

### GitHub Actions

El workflow actual reside en `.github/workflows/ci.yml` y:

1. prepara Python 3.11;
2. instala dependencias con `pip install -r requirements.txt`;
3. instala el paquete en editable con `pip install -e .`;
4. instala utilidades de test;
5. ejecuta `pytest tests/`.

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
- endurecimiento de CI para smoke/golden artifacts;
- operación del modo servidor MCP;
- guía de troubleshooting de Vertex AI y credenciales.
