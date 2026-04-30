---
status: Verified
owner: docs-governance
source_of_truth:
  - ../../src/assessment_engine/schemas/blueprint.py
  - ../../src/assessment_engine/schemas/annex_synthesis.py
  - ../../src/assessment_engine/schemas/global_report.py
  - ../../src/assessment_engine/schemas/commercial.py
  - ../../src/assessment_engine/scripts/run_tower_blueprint_engine.py
  - ../../src/assessment_engine/scripts/run_executive_annex_synthesizer.py
  - ../../src/assessment_engine/scripts/build_global_report_payload.py
  - ../../src/assessment_engine/scripts/run_executive_refiner.py
  - ../../src/assessment_engine/scripts/run_commercial_refiner.py
  - ../../src/assessment_engine/scripts/render_tower_blueprint.py
  - ../../src/assessment_engine/scripts/render_tower_annex_from_template.py
  - ../../src/assessment_engine/scripts/render_global_report_from_template.py
  - ../../src/assessment_engine/scripts/render_commercial_report.py
  - ../../src/assessment_engine/scripts/render_web_presentation.py
  - ./payload-render-boundaries.md
last_verified_against: 2026-04-30
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Artifact contracts

Este documento complementa [`payload-render-boundaries.md`](payload-render-boundaries.md). Allí se explica la frontera técnica entre payload, schema y render. Aquí se fija la lectura **operativa y empresarial** de los artefactos: quién los produce, quién depende de ellos y cuándo deben considerarse suficientemente válidos para dejar avanzar el sistema.

## Regla operativa

Un artefacto importante no es solo “un archivo generado”. Debe poder responder a estas cuatro preguntas:

1. **quién lo produce**;
2. **qué verdad contiene**;
3. **qué etapa lo consume después**;
4. **qué riesgo aparece si falta o deriva**.

## Mapa principal de contratos

| Artefacto | Productor principal | Consumidor principal | Rol empresarial | Si falta o deriva |
|---|---|---|---|---|
| `case_input.json` | preparación por torre | scoring, findings, engine | fija el caso de trabajo | la torre nace con contexto pobre o ambiguo |
| `evidence_ledger.json` | preparación por torre | findings, auditoría, soporte | deja trazabilidad de evidencias | baja defendibilidad del assessment |
| `scoring_output.json` | scoring por torre | blueprint, annex, soporte | fija la base cuantitativa | se debilita la consistencia del diagnóstico |
| `findings.json` | análisis por torre | blueprint y soporte editorial | concentra hallazgos estructurados | se empobrece la lectura por pilar |
| `blueprint_<tower>_payload.json` | `run_tower_blueprint_engine.py` | annex, global builder, render blueprint, web | fuente de verdad por torre | aparece split-brain aguas abajo |
| `approved_annex_<tower>.template_payload.json` | `run_executive_annex_synthesizer.py` | render annex | traducción ejecutiva por torre | cae la legibilidad ejecutiva de la torre |
| `global_report_payload.json` | `build_global_report_payload.py` + `run_executive_refiner.py` | render global, comercial, web | agenda ejecutiva consolidada | la visión de dirección queda rota |
| `commercial_report_payload.json` | `run_commercial_refiner.py` | render comercial | activación comercial del assessment | se pierde explotabilidad de cuenta |
| `Blueprint_Transformacion_*.docx` | render blueprint | lector humano | entregable técnico visible | no debe usarse como fuente de verdad |
| `annex_*.docx` | render annex | lector humano | entregable ejecutivo por torre | puede quedar bonito o feo, pero no debe redefinir contenido |
| `Informe_Ejecutivo_Consolidado_*.docx` | render global | lector humano | entregable ejecutivo consolidado | degrada la comunicación con dirección |
| `Account_Action_Plan_*.docx` | render comercial | lector humano | entregable comercial interno | baja utilidad para cuenta y preventa |
| `presentation/index.html` | render web | lector humano | soporte visual y storytelling | la narrativa visual queda desalineada |

## Qué contratos mandan de verdad

### Contratos de base

- `case_input.json`
- `evidence_ledger.json`
- `scoring_output.json`
- `findings.json`

Son la base que permite que la torre sea explicable, trazable y defendible.

### Contratos canónicos de decisión

- `blueprint_<tower>_payload.json`
- `global_report_payload.json`
- `commercial_report_payload.json`

Estos artefactos son los que más se acercan a la **verdad operativa del sistema**.

### Contratos de presentación derivada

- `approved_annex_<tower>.template_payload.json`
- DOCX por torre/global/comercial
- `presentation/index.html`

Importan mucho para el lector final, pero su razón de ser es **traducir** una verdad previa, no sustituirla.

## Qué debe comprobar cada capa antes de avanzar

| Etapa | Señal mínima de salida sana |
|---|---|
| Torre base | existen `case_input.json`, `evidence_ledger.json`, `scoring_output.json` y `findings.json` |
| Blueprint | existe `blueprint_<tower>_payload.json` y la torre ya tiene verdad estructurada |
| Annex | existe `approved_annex_<tower>.template_payload.json` y no contradice el blueprint |
| Global | existe `global_report_payload.json` y reutiliza información de torres disponibles |
| Comercial | existe `commercial_report_payload.json` y se apoya en el global |
| Web | existe `presentation/index.html` y refleja global + torres, no una historia inventada |

## Reglas de interpretación si hay conflicto

1. Si un DOCX contradice a un payload, **manda el payload**.
2. Si un payload derivado contradice a su fuente inmediata, **manda la fuente anterior**.
3. Si un renderer necesita demasiada normalización, el problema real suele estar antes.
4. Si un artefacto existe pero no es consumible por la siguiente capa, el contrato está roto aunque el archivo esté presente.

## Riesgos contractuales visibles hoy

1. **Tolerancia de algunos renders**  
   `robust_load_payload(...)` protege continuidad, pero puede ocultar desviaciones de contrato.

2. **Capa web sin schema final explícito**  
   `render_web_presentation.py` compone una vista útil, pero su contrato está más implícito que en DOCX global/comercial.

3. **Convivencia de activo moderno y fallback legacy**  
   especialmente en la consolidación global, útil para resiliencia pero sensible a híbridos.

## Qué significa “contrato cumplido”

Un contrato se puede considerar cumplido cuando:

1. el artefacto correcto existe en la ubicación esperada;
2. su estructura es compatible con el schema o el consumidor real;
3. la siguiente etapa puede usarlo sin reinterpretar la verdad;
4. la historia que cuenta sigue alineada con la capa anterior.

## Uso recomendado de este documento

Úsalo cuando necesites decidir:

- si una incidencia es de **producción de artefacto** o de **presentación**;
- qué archivo revisar primero en una cadena rota;
- cuál es la **fuente de verdad** que manda en cada nivel;
- qué pieza debe validarse antes de promover una evolución del sistema.
