---
status: Draft
owner: docs-governance
source_of_truth:
  - ../../src/assessment_engine/scripts/build_case_input.py
  - ../../src/assessment_engine/scripts/build_evidence_ledger.py
  - ../../src/assessment_engine/scripts/run_scoring.py
  - ../../src/assessment_engine/scripts/run_evidence_analyst.py
  - ../../src/assessment_engine/scripts/run_tower_pipeline.py
  - ../../src/assessment_engine/scripts/run_tower_blueprint_engine.py
  - ../../src/assessment_engine/scripts/run_executive_annex_synthesizer.py
  - ../../src/assessment_engine/scripts/run_global_pipeline.py
  - ../../src/assessment_engine/scripts/build_global_report_payload.py
  - ../../src/assessment_engine/scripts/run_commercial_pipeline.py
  - ../../src/assessment_engine/scripts/run_commercial_refiner.py
  - ../../src/assessment_engine/scripts/run_intelligence_harvesting.py
  - ../../src/assessment_engine/scripts/generate_tower_radar_chart.py
last_verified_against: 2026-04-30
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Working artifacts map

El árbol `working/` es la **superficie de artefactos de ejecución** de `assessment-engine`. Aquí se acumulan inputs enriquecidos, payloads intermedios, salidas canónicas de cada pipeline y entregables renderizados.

## Estructura general observada

```text
working/
  <client>/
    client_intelligence.json
    global_report_payload.json
    commercial_report_payload.json
    Informe_Ejecutivo_Consolidado_<client>.docx
    Account_Action_Plan_<client>.docx
    T1/
    T2/
    ...
    Tn/
      case_input.json
      evidence_ledger.json
      scoring_output.json
      findings.json
      blueprint_<tower>_payload.json
      approved_annex_<tower>.template_payload.json
      pillar_radar_chart.generated.png
      annex_<tower>_<client>_final.docx
      Blueprint_Transformacion_<TOWER>_<client>.docx
```

## Nivel cliente

### `client_intelligence.json`

- ubicación: `working/<client>/client_intelligence.json`
- origen: `run_intelligence_harvesting.py`
- rol: dossier estratégico reutilizable para enriquecer pipelines por torre y renderizadores
- estado arquitectónico: **input enriquecido compartido**

### `global_report_payload.json`

- ubicación: `working/<client>/global_report_payload.json`
- origen: `build_global_report_payload.py`, luego refinado por `run_executive_refiner.py`
- rol: payload global consolidado para la capa ejecutiva
- estado arquitectónico: **artefacto canónico de la capa global**

### `commercial_report_payload.json`

- ubicación: `working/<client>/commercial_report_payload.json`
- origen: `run_commercial_refiner.py`
- rol: payload comercial interno derivado del contexto global y de blueprints por torre
- estado arquitectónico: **artefacto canónico de la capa comercial**

### DOCX globales

- `Informe_Ejecutivo_Consolidado_<client>.docx`
- `Account_Action_Plan_<client>.docx`

Rol:

- entregables renderizados finales;
- derivados de payloads JSON previos;
- no deben tratarse como fuente de verdad del sistema.

## Nivel torre

### 1. Preparación determinista

| Artefacto | Origen | Rol | Tipo |
|---|---|---|---|
| `case_input.json` | `build_case_input.py` | input normalizado de caso y respuestas | base determinista |
| `evidence_ledger.json` | `build_evidence_ledger.py` | ledger de evidencias trazables por pilar y KPI | base determinista |
| `scoring_output.json` | `run_scoring.py` | scoring y bandas de madurez | base determinista |
| `findings.json` | `run_evidence_analyst.py` | hallazgos estructurados basados en scoring y evidencias | derivado analítico |

### 2. Núcleo top-down por torre

| Artefacto | Origen | Rol | Tipo |
|---|---|---|---|
| `blueprint_<tower>_payload.json` | `run_tower_blueprint_engine.py` | análisis detallado y fuente principal de verdad por torre | **canónico** |
| `approved_annex_<tower>.template_payload.json` | `run_executive_annex_synthesizer.py` | resumen ejecutivo estructurado derivado del blueprint | derivado canónico para render |

### 3. Visuales y render

| Artefacto | Origen | Rol | Tipo |
|---|---|---|---|
| `pillar_radar_chart.generated.png` | `generate_tower_radar_chart.py` | visual de scores por pilar; actualiza además el payload del anexo | derivado visual |
| `annex_<tower>_<client>_final.docx` | `render_tower_annex_from_template` | entregable ejecutivo final | render final |
| `Blueprint_Transformacion_<TOWER>_<client>.docx` | `render_tower_blueprint.py` | representación DOCX del blueprint | render final |

## Linaje resumido

### Torre

```text
context-file + responses-file
  -> case_input.json
  -> evidence_ledger.json
  -> scoring_output.json
  -> findings.json
  -> blueprint_<tower>_payload.json
  -> approved_annex_<tower>.template_payload.json
  -> pillar_radar_chart.generated.png
  -> annex_<tower>_<client>_final.docx
  -> Blueprint_Transformacion_<TOWER>_<client>.docx
```

### Cliente

```text
client_intelligence.json + blueprints de torres
  -> global_report_payload.json
  -> Informe_Ejecutivo_Consolidado_<client>.docx
  -> commercial_report_payload.json
  -> Account_Action_Plan_<client>.docx
```

## Qué artefactos mandan hoy

### Fuente principal de verdad

- por torre: `blueprint_<tower>_payload.json`
- a nivel global: `global_report_payload.json`
- a nivel comercial: `commercial_report_payload.json`

### Artefactos de soporte

- `case_input.json`
- `evidence_ledger.json`
- `scoring_output.json`
- `findings.json`
- `client_intelligence.json`

### Artefactos derivados

- `approved_annex_<tower>.template_payload.json`
- `pillar_radar_chart.generated.png`
- todos los `.docx` renderizados

## Superficie legacy todavía visible

Persisten referencias legacy en:

- tests que buscan artefactos concretos en `working/smoke_ivirma/T5/`;
- scripts `_legacy/`;
- partes del modo MCP que inspeccionan secciones antiguas (`asis`, `risks`, `gap`, `tobe`, `todo`, `conclusion`).

Esto significa que `working/` convive todavía con:

1. un flujo actual top-down basado en blueprint;
2. rastros de un modelo anterior por secciones.

## Regla documental recomendada

Cuando documentes o revises artefactos en `working/`:

- trata los payloads JSON canónicos como verdad antes que los DOCX;
- distingue siempre entre artefactos de base, canónicos y derivados;
- marca como legacy cualquier referencia a secciones antiguas que ya no definan el flujo principal.
