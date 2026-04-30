---
status: Draft
owner: docs-governance
source_of_truth:
  - ../../pyproject.toml
  - ../../requirements.txt
  - ../../tests/test_environment.py
  - ../../.github/workflows/ci.yml
  - ../../src/assessment_engine/scripts/lib/runtime_env.py
last_verified_against: 2026-04-30
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Installation and environment setup

Esta guía recoge el flujo de instalación más alineado con el estado actual del repo.

## Supuestos operativos actuales

- la CI usa **Python 3.11**;
- el proyecto es instalable como paquete Python desde `pyproject.toml`;
- la validación local observada usa una virtualenv en `.venv/`;
- los pipelines con IA necesitan `GOOGLE_CLOUD_PROJECT` y `GOOGLE_CLOUD_LOCATION`.

## Preparación recomendada

El flujo práctico más alineado con el repo es trabajar con una virtualenv local en `.venv`.

```bash
python3.11 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt
./.venv/bin/pip install -e .
```

## Por qué instalar en editable

La suite incluye una comprobación explícita de que el paquete `assessment_engine` es importable sin hacks de `sys.path`. El modo editable encaja con ese modelo de trabajo y con el empaquetado actual del proyecto.

## Variables de entorno de Google Cloud

Los pipelines por torre validan:

- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`

El repo define además defaults en `runtime_env.py`:

- `GOOGLE_CLOUD_PROJECT=sub403o4u0q5`
- `GOOGLE_CLOUD_LOCATION=europe-west1`

Si tu entorno ya tiene esos valores, los scripts los reutilizan. Si no, el runtime actual puede poblar esos defaults para el flujo por torre.

## Validación mínima del entorno

### Import y tests

```bash
./.venv/bin/python -m pytest tests/test_environment.py -q
```

### Suite general

```bash
./.venv/bin/python -m pytest tests/ -q
```

## Diferencia entre `pyproject.toml` y `requirements.txt`

- `pyproject.toml` describe el paquete y sus dependencias principales;
- `requirements.txt` fija un entorno de trabajo más amplio, alineado con la CI actual;
- hoy la CI se apoya en `requirements.txt`, no solo en `pyproject.toml`.

## Resultado esperado tras instalar

Deberías poder:

1. importar `assessment_engine`;
2. ejecutar tests locales con `./.venv/bin/python`;
3. lanzar scripts `python -m assessment_engine.scripts.<modulo>`;
4. renderizar plantillas incluidas en el paquete.
