---
status: Verified
owner: docs-governance
source_of_truth:
  - ../../docs/operations/agentic-development-workflow.md
  - ../../pyproject.toml
  - ../../requirements.txt
  - ../../.github/workflows/quality.yml
  - ../../.github/workflows/typing.yml
  - ../../.github/pull_request_template.md
  - ../../AGENTS.md
  - ../../.github/copilot-instructions.md
  - ../../src/assessment_engine/scripts/lib/global_maturity_policy.py
  - ../../src/assessment_engine/scripts/tools/run_incremental_quality_gate.py
  - ../../src/assessment_engine/scripts/tools/run_incremental_typecheck.py
  - ../../tests/test_global_coherence.py
last_verified_against: 2026-05-01
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Engineering quality gates

Esta pieza define cómo `assessment-engine` obliga a que los cambios nuevos sigan una disciplina de implementación coherente con el proyecto, más allá de que `pytest` pase o la documentación se haya tocado.

## Qué protege esta capa

La puerta de calidad actual se aplica a la **superficie viva** del repo:

- `src/assessment_engine/`
- `tests/`

Queda fuera el material archivado o meramente histórico, como `_PROJECT_ARCHIVE_/` o `docs/reference/generated/legacy-gemini/`, para no bloquear la evolución del código activo por deuda no operativa.

## Regla central

Las reglas importantes del sistema no deben vivir solo en prompts, memoria del equipo o checklists manuales. Deben materializarse en una o más de estas capas ejecutables:

- helpers o políticas compartidas;
- schemas y validaciones;
- tests automáticos;
- workflows y checks de CI.

Si una decisión es importante para scoring, contratos, render, coherencia narrativa u operación, no puede depender solo de “acordarse”.

Esta capa supone además que el cambio partió de una **spec mínima** y de un alcance explícito, tal como se describe en `agentic-development-workflow.md`.

## Gates ejecutables actuales

### Calidad incremental

El workflow `.github/workflows/quality.yml` ejecuta `src/assessment_engine/scripts/tools/run_incremental_quality_gate.py`.

Ese runner:

1. calcula los ficheros Python cambiados entre `base_sha` y `head_sha`;
2. filtra solo la superficie viva del proyecto (`src/assessment_engine/**` y `tests/**`);
3. ejecuta `ruff check` sobre esos ficheros;
4. ejecuta `ruff format --check` sobre esos mismos ficheros.

La adopción es **incremental**: el gate bloquea deuda nueva o modificada sin exigir sanear en esta misma iteración todo el histórico del repo.

### Tipado incremental

El workflow `.github/workflows/typing.yml` ejecuta `src/assessment_engine/scripts/tools/run_incremental_typecheck.py`.

Ese runner reutiliza la misma selección incremental de ficheros vivos y ejecuta `mypy` solo sobre los `.py` cambiados en `src/assessment_engine/**` y `tests/**`.

El objetivo de esta capa no es exigir ahora un repo 100% tipado, sino impedir que la superficie viva siga creciendo sin verificación estática básica.

### Coherencia de dominio

Las reglas transversales de score, banda, color y target no deben quedar duplicadas entre builder, renderizadores y dashboard.

La política compartida vive ahora en `src/assessment_engine/scripts/lib/global_maturity_policy.py`, y la suite incluye tests de coherencia (`tests/test_global_coherence.py`) para bloquear derivas entre:

- blueprints;
- payload global;
- render DOCX;
- y dashboard web.

## Reglas de implementación del proyecto

- reutiliza helpers, schemas y utilidades compartidas antes de duplicar lógica;
- no escondas lógica de negocio o de reporting importante solo en prompts;
- si cambian contratos o payloads, alinea también tests y documentación canónica asociada;
- si cambian score, banda, color, target o semántica cliente-facing, revisa también los tests de coherencia;
- si una regla transversal no cabe en un linter genérico, conviértela en test de coherencia o en validación explícita;
- no uses capas legacy o archivadas como nuevo source of truth.

## Relación con la revisión humana

La automatización no sustituye la revisión de PR:

- el checklist de `.github/pull_request_template.md` obliga a revisar impacto documental y de calidad;
- `AGENTS.md` y `.github/copilot-instructions.md` remiten a esta política antes de programar con agentes;
- la gobernanza documental sigue exigiendo actualizar la documentación canónica cuando cambian reglas, workflows o validadores.

## Ejecución local recomendada

Para validar los ficheros tocados en una rama:

```bash
./.venv/bin/python src/assessment_engine/scripts/tools/run_incremental_quality_gate.py \
  --repo-root . \
  --path src/assessment_engine/scripts/tools/run_incremental_quality_gate.py \
  --path tests/test_run_incremental_quality_gate.py

./.venv/bin/python src/assessment_engine/scripts/tools/run_incremental_typecheck.py \
  --repo-root . \
  --path src/assessment_engine/scripts/build_global_report_payload.py \
  --path tests/test_global_coherence.py

./.venv/bin/python -m pytest \
  tests/test_global_coherence.py \
  tests/test_build_global_report_payload.py -q
```

La suite completa de `pytest` sigue siendo obligatoria aparte.

## Próximo endurecimiento natural

Cuando la superficie viva tenga menos deuda histórica, el siguiente salto natural es endurecer esta capa con:

1. elevar el tipado incremental hacia módulos completos y no solo ficheros tocados;
2. ampliar los tests de coherencia a scoring, severidad narrativa y dominios commercial/client-facing;
3. reglas de arquitectura o dependencia más explícitas;
4. rulesets/protecciones de rama en GitHub para exigir también `typing`.
