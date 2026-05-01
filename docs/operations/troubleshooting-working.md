---
status: Verified
owner: docs-governance
source_of_truth:
  - ../../pytest.ini
  - ../../tests/test_contract_handover.py
  - ../../tests/test_t5_golden.py
  - ../../src/assessment_engine/scripts/run_tower_pipeline.py
  - ../../src/assessment_engine/scripts/run_global_pipeline.py
  - ../../src/assessment_engine/scripts/run_commercial_pipeline.py
  - ../architecture/working-artifacts.md
last_verified_against: 2026-05-01
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Troubleshooting `working/` and artifact-dependent validation

Esta guía explica qué hacer cuando faltan artefactos en `working/` o cuando los tests dependen de salidas todavía no generadas.

## Señal actual del baseline

En el estado actualmente validado del repositorio:

- `working/smoke_ivirma/T5/blueprint_t5_payload.json` existe;
- `working/smoke_ivirma/T5/approved_annex_t5.template_payload.json` existe;
- `working/smoke_ivirma/global_report_payload.json` existe;
- `working/smoke_ivirma/commercial_report_payload.json` existe;
- `working/smoke_ivirma/presentation/index.html` existe;
- la suite completa de `pytest` pasa.

Si en una sesión futura vuelven a faltar estos artefactos, entonces sí pueden reaparecer fallos de contrato o `skip` condicionados por ausencia de baseline.

## Qué significa esto

Parte de la suite sigue actuando como validación sobre artefactos previamente generados, no como test completamente autosuficiente. Por eso, cuando el baseline smoke está presente, la suite pasa; cuando desaparece o queda incompleto, algunos tests fallan o se saltan sin que eso implique necesariamente un bug lógico nuevo.

## Diagnóstico rápido

### 1. Verificar qué existe

```bash
find working -maxdepth 3 -type f | sort
```

### 2. Verificar una torre concreta

```bash
find working/<client>/<tower> -maxdepth 1 -type f | sort
```

### 3. Verificar cliente completo

```bash
find working/<client> -maxdepth 2 -type f | sort
```

## Cómo regenerar artefactos faltantes

### Faltan artefactos de torre

Ejecuta o reejecuta el pipeline por torre:

```bash
./.venv/bin/python -m assessment_engine.scripts.run_tower_pipeline \
  --tower T5 \
  --client ivirma \
  --context-file /ruta/al/contexto.docx \
  --responses-file /ruta/a/respuestas.txt
```

Si lo que falta es específicamente el baseline de `smoke_ivirma/T5`, usa mejor el runner reproducible:

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts
```

Si el problema está en la parte global y quieres respetar el comportamiento canónico actual del repo, usa el smoke con global tal como está:

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts --with-global
```

Y si antes quieres separar si el bloqueo es local o de Vertex AI:

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.regenerate_smoke_artifacts --local-only
```

### Faltan artefactos globales

```bash
./.venv/bin/python -m assessment_engine.scripts.run_global_pipeline <client_name>
```

### Faltan artefactos comerciales

```bash
./.venv/bin/python -m assessment_engine.scripts.run_commercial_pipeline <client_name>
```

## Qué tests dependen de artefactos

### Dependencia fuerte

- `tests/test_contract_handover.py`
- `tests/test_t5_golden.py`
- parte de `tests/test_payload_validation.py`

### Dependencia menor o ninguna

- `tests/test_environment.py`
- tests de schemas;
- tests de utilidades y render unitario que fabriquen sus propios datos.

## Regla práctica

Si falla una validación por ausencia de artefactos:

1. no asumas primero un bug lógico;
2. confirma si el JSON o DOCX esperado existe en `working/`;
3. si no existe, regenera la fase anterior del pipeline;
4. solo después interpreta el fallo como problema funcional.

Si el smoke global canónico (`--with-global`) falla, la lectura correcta ya no es “quizá faltó activar compatibilidad”: significa que hay una regresión o una dependencia real de artefactos legacy fuera del flujo principal.

## Relación con `pytest.ini`

`pytest.ini` excluye `working/` del descubrimiento de tests, pero no impide que los tests lean artefactos desde esa ruta cuando fueron diseñados para validar contratos o golden files.

## Recomendación de mantenimiento

Mientras la suite siga dependiendo de artefactos externos al propio test, documenta siempre:

- qué payload faltaba;
- qué pipeline debía generarlo;
- si el problema es ausencia de artefacto o invalidación real del contrato.
