---
status: Draft
owner: docs-governance
source_of_truth:
  - ../../src/assessment_engine/scripts/run_tower_pipeline.py
  - ../../src/assessment_engine/scripts/run_tower_blueprint_engine.py
  - ../../src/assessment_engine/scripts/run_executive_annex_synthesizer.py
  - ../../src/assessment_engine/scripts/lib/pipeline_runtime.py
  - ../../src/assessment_engine/schemas/blueprint.py
  - ../../src/assessment_engine/schemas/annex_synthesis.py
last_verified_against: 2026-04-30
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Tower pipeline

El pipeline por torre es el **núcleo operativo** de `assessment-engine`. Ejecuta preparación determinista, análisis top-down con IA y renderizado final para una torre tecnológica concreta.

## Lectura empresarial

Visto desde negocio y delivery, este pipeline cumple cuatro funciones:

1. **absorber información heterogénea** del cliente sin perder trazabilidad;
2. **construir una verdad técnica defendible** para una torre concreta;
3. **traducir esa verdad** a una voz ejecutiva sin crear contradicciones;
4. **emitir entregables reutilizables** por dirección, preventa y equipos de transformación.

No es solo una secuencia técnica: es la unidad que transforma inputs de assessment en un **activo de decisión**.

## Entrada principal

El orquestador actual es:

- `src/assessment_engine/scripts/run_tower_pipeline.py`

Recibe:

- `--tower`
- `--client`
- `--context-file`
- `--responses-file`
- `--start-from` opcional para reanudar desde un paso

## Directorio de trabajo

Cada ejecución trabaja en:

`working/<client_slug>/<TOWER_ID>/`

El orquestador fija variables de entorno como:

- `ASSESSMENT_CLIENT_ID`
- `ASSESSMENT_TOWER_ID`
- `ASSESSMENT_CASE_DIR`
- `PYTHONPATH`

Además, la torre comparte ya con las capas global y comercial una base común de runtime para:

- resolver el intérprete Python;
- bootstrap de entorno;
- defaults de ejecución.

Además exige configuración de Vertex AI mediante:

- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`

## Qué entra, qué sale y qué gana la organización

| Capa | Activos principales | Resultado empresarial |
|---|---|---|
| Entrada | contexto, respuestas, configuración metodológica y opcionalmente `client_intelligence.json` | visión unificada del caso a evaluar |
| Base determinista | `case_input.json`, `evidence_ledger.json`, `scoring_output.json`, `findings.json` | trazabilidad y explicabilidad del diagnóstico |
| Verdad canónica | `blueprint_<tower>_payload.json` | lectura técnica estructural de la torre |
| Síntesis ejecutiva | `approved_annex_<tower>.template_payload.json` | mensaje apto para dirección sin romper la lógica técnica |
| Render final | DOCX de annex y blueprint | entregables consumibles por cliente y equipos internos |

## Fases reales del flujo

### 1. Preparación determinista

Se ejecuta en secuencia:

1. `build_case_input`
2. `build_evidence_ledger`
3. `run_scoring`
4. `run_evidence_analyst`

Artefactos principales:

| Paso | Artefacto esperado |
|---|---|
| `build_case_input` | `case_input.json` |
| `build_evidence_ledger` | `evidence_ledger.json` |
| `run_scoring` | `scoring_output.json` |
| `run_evidence_analyst` | hallazgos derivados de evidencias |

### 2. Flujo top-down con blueprint

La fase top-down reemplaza el enfoque legacy por secciones paralelas.

Paso central:

- `run_tower_blueprint_engine`

Salida principal:

- `blueprint_<tower>_payload.json`

Este payload actúa como **fuente principal de verdad** para el análisis de la torre. El motor:

- carga `case_input.json`;
- incorpora `client_intelligence.json` si existe;
- agrupa respuestas por pilar usando la definición de torre en `engine_config/towers/<tower>/`;
- procesa pilares con agentes de IA;
- genera un cierre ejecutivo y roadmap;
- valida el resultado contra `BlueprintPayload`.

### Por qué el blueprint es el activo clave

El blueprint no es solo un payload técnico intermedio. Es el punto donde quedan fijadas:

- la lectura AS-IS de la torre;
- la arquitectura objetivo;
- las brechas materiales;
- el backlog de iniciativas;
- el cierre ejecutivo técnico.

Eso lo convierte en el **activo empresarial de mayor valor por torre**, porque evita que distintos entregables compitan por definir la realidad.

### 3. Síntesis ejecutiva del anexo

Desde el blueprint se ejecuta:

- `run_executive_annex_synthesizer`

Salida principal:

- `approved_annex_<tower>.template_payload.json`

Este paso:

- carga el blueprint validado;
- usa `AnnexPayload` como contrato;
- añade `generation_metadata` con `run_id`;
- construye un handover ejecutivo explícito con hechos no negociables desde `executive_snapshot`, `roadmap` y proyectos del blueprint;
- deriva de forma determinista score global, bandas, gaps, riesgos e iniciativas prioritarias;
- reserva al LLM la capa de framing, headline y redacción ejecutiva;
- enriquece además el anexo con perfil de scores y referencias al radar si existe.

### Qué control empresarial introduce esta síntesis

Esta fase desacopla **audiencia** de **verdad**:

- el responsable técnico sigue leyendo el blueprint;
- el sponsor/CTO recibe un annex más corto y ejecutivo;
- ambos documentos quedan anclados al mismo diagnóstico estructural.

El beneficio empresarial directo es reducir el riesgo de tener un discurso técnico y otro ejecutivo que se contradigan.

### 4. Renderizado final

El orquestador renderiza en paralelo:

- el anexo ejecutivo DOCX;
- el blueprint estratégico DOCX.

Salidas visibles:

- `annex_<tower>_<client>_final.docx`
- `Blueprint_Transformacion_<TOWER>_<client>.docx`

## Contratos principales

| Artefacto | Contrato |
|---|---|
| `blueprint_<tower>_payload.json` | `BlueprintPayload` |
| `approved_annex_<tower>.template_payload.json` | `AnnexPayload` |

## Puntos de control y riesgo operativo

| Punto | Qué protege | Riesgo si falla |
|---|---|---|
| `build_case_input` y `build_evidence_ledger` | calidad y trazabilidad de entrada | el diagnóstico nace ambiguo o no auditable |
| `run_scoring` y `run_evidence_analyst` | consistencia de señales y hallazgos | el blueprint pierde base objetiva |
| `run_tower_blueprint_engine` | verdad estructural top-down | se rompe la columna vertebral de la torre |
| `run_executive_annex_synthesizer` | alineación ejecutivo-técnica | reaparece el riesgo de “split-brain” |
| renderers | presentación final | afecta percepción, no debería redefinir lógica |

## Regla de alineación blueprint -> annex

Aunque blueprint y annex hablan a audiencias distintas, el flujo actual fija esta regla:

1. el **blueprint** decide la verdad estructural de la torre;
2. el **annex** puede reinterpretar el mensaje para CTO/ejecutivo, pero no redefinir score, gaps, riesgos ni prioridades;
3. el **renderer** no debe compensar contradicciones semánticas entre ambos.

## Reanudación y comportamiento ante fallo

- `--start-from` permite saltar pasos previos hasta un step concreto;
- el blueprint es un punto crítico: si falla, el flujo se detiene;
- el renderizado del blueprint DOCX se trata como fallo no bloqueante;
- el código legacy sigue comentado para evitar el problema de `split-brain`.

## Nota arquitectónica

El diseño actual deja claro que:

1. la verdad detallada se construye en el blueprint;
2. el anexo ejecutivo se deriva de esa verdad;
3. el renderizado es una capa final, no el lugar donde se define la lógica.

## Qué debería entender un lector no técnico al terminar este documento

1. que una torre genera primero un **diagnóstico canónico** y después sus resúmenes;
2. que los DOCX son salidas finales, no la fuente de verdad;
3. que la gobernanza real del pipeline está en los payloads y contratos;
4. que la principal protección contra incoherencia documental es la regla `blueprint -> annex`.
