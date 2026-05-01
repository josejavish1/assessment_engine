---
status: Draft
owner: docs-governance
source_of_truth:
  - ../../src/assessment_engine/scripts/run_global_pipeline.py
  - ../../src/assessment_engine/scripts/build_global_report_payload.py
  - ../../src/assessment_engine/scripts/run_executive_refiner.py
  - ../../src/assessment_engine/scripts/run_commercial_pipeline.py
  - ../../src/assessment_engine/scripts/run_commercial_refiner.py
  - ../../src/assessment_engine/scripts/lib/pipeline_runtime.py
  - ../../src/assessment_engine/schemas/global_report.py
  - ../../src/assessment_engine/schemas/commercial.py
last_verified_against: 2026-05-01
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Global and commercial pipelines

Tras completar una o varias torres, `assessment-engine` eleva el análisis hacia una vista ejecutiva global y luego hacia una explotación comercial interna.

## Lectura empresarial

Estas dos capas convierten diagnósticos técnicos dispersos en dos productos distintos:

1. una **lectura de dirección** para priorizar transformación, riesgo y decisiones;
2. una **lectura comercial interna** para convertir esa agenda de transformación en narrativa de cuenta y propuestas.

Su objetivo no es descubrir una verdad nueva, sino **reagrupar y explotar** la verdad ya producida por las torres.

## Pipeline global

El orquestador principal es:

- `src/assessment_engine/scripts/run_global_pipeline.py`

Trabaja sobre:

- `working/<client>/`

### Qué valor aporta esta capa

| Resultado | Para quién | Valor |
|---|---|---|
| `global_report_payload.json` | dirección / liderazgo tecnológico | consolida una lectura transversal del cliente |
| `Informe_Ejecutivo_Consolidado_<client>.docx` | sponsor, CIO, programa de transformación | convierte múltiples torres en una agenda ejecutiva coherente |

### Fases reales

1. **Build Global Payload**
   - script: `build_global_report_payload`
   - salida: `global_report_payload.json`

2. **Strategic Executive Refinement**
   - script: `run_executive_refiner`
   - reescribe el mismo `global_report_payload.json`

3. **Generate Global Radar Chart**
   - script: `generate_global_radar_chart`

4. **Generate Executive Roadmap Visual**
   - script: `generate_executive_roadmap_image`

5. **Render Global DOCX**
   - script: `render_global_report_from_template`
   - salida final: `Informe_Ejecutivo_Consolidado_<client>.docx`

### Nota operativa actual

El orquestador global ya comparte con la capa comercial una base común de:

- resolución de intérprete Python;
- bootstrap de entorno;
- propagación explícita del entorno validado a cada paso del pipeline.

## Cómo se construye el payload global

`build_global_report_payload.py` prioriza:

1. blueprints modernos: `T*/blueprint_*_payload.json`
2. fallback legacy: `T*/approved_annex_*.refined.json`

El builder:

- consolida `tower_summaries` y `heatmap`;
- deriva riesgos estratégicos;
- agrega iniciativas;
- extrae principios de arquitectura e implicaciones operativas si existen;
- genera una vista híbrida mientras coexisten artefactos nuevos y antiguos.

### Decisión arquitectónica relevante

El builder prefiere los blueprints modernos y solo conserva fallback legacy para no bloquear workspaces mixtos. Empresarialmente esto significa:

- la consolidación global ya está pensada para descansar sobre la **verdad top-down por torre**;
- el legado sigue presente como red de seguridad, no como modelo objetivo a largo plazo.

### Señalización operativa actual

La consolidación global ya deja visible qué mezcla de fuentes está usando:

- `blueprint-only`
- `mixed-blueprint-legacy`
- `legacy-only`

Ese lineage queda reflejado en `_generation_metadata.source_version` y en `meta.version` del `global_report_payload.json`.

Además, `run_global_pipeline.py` ya expone `--blueprint-only` para forzar el camino canónico puro cuando quieras detectar dependencias legacy reales en un workspace o en smoke/CI.

## Refinado ejecutivo global

`run_executive_refiner.py` toma el payload agregado y lo refina mediante varias iteraciones LLM:

- `executive_summary`
- `burning_platform`
- `tower_bottom_lines`
- `target_vision`
- `execution_roadmap`
- `executive_decisions`

El resultado final sobrescribe el mismo archivo `global_report_payload.json`.

### Qué traduce esta fase

La refinación ejecutiva convierte señales técnicas agregadas en:

- narrativa de plataforma de cambio;
- riesgos sistémicos;
- bottom lines por torre;
- decisiones inmediatas para dirección;
- visión objetivo y roadmap ejecutivo.

Su aporte empresarial es hacer que el output deje de ser un simple agregado técnico y pase a ser un **vehículo de priorización**.

## Pipeline comercial

El orquestador principal es:

- `src/assessment_engine/scripts/run_commercial_pipeline.py`

Parte de:

- `global_report_payload.json`

Y genera:

- `commercial_report_payload.json`
- `Account_Action_Plan_<client>.docx`

### Qué valor aporta la capa comercial

| Resultado | Para quién | Valor |
|---|---|---|
| `commercial_report_payload.json` | equipos de cuenta y preventa | traduce el assessment a hipótesis comerciales accionables |
| `Account_Action_Plan_<client>.docx` | stakeholders internos de venta/entrega | materializa narrativa, pipeline y propuestas proactivas |

### Fases reales

1. **Multi-Agent Commercial Refinement**
   - script: `run_commercial_refiner`

2. **Render Account Action Plan**
   - script: `render_commercial_report`

Igual que en la capa global, la ejecución actual reutiliza un runner común para evitar deriva entre preflight, variables de entorno y pasos hijos.

## Contexto híbrido comercial

`run_commercial_refiner.py` no se apoya solo en el payload global. También:

- busca todos los `blueprint_*_payload.json` de torres;
- construye un catálogo táctico por torre;
- mezcla contexto estratégico global con detalle técnico por blueprint.

Eso permite que la capa comercial cruce:

- grandes iniciativas del roadmap global;
- quick wins e iniciativas detectadas en torres;
- deuda técnica y bottom lines ejecutivos por torre.

En términos empresariales, esta mezcla evita dos extremos pobres:

- una narrativa comercial desconectada de la realidad técnica;
- un catálogo técnico sin traducción a oportunidad de cuenta.

## Orquestación multi-agente comercial

El refinador comercial organiza varias capas:

1. **Global Account Director**
   - estrategia de cuenta y resumen comercial
2. **Enterprise Presales Architect**
   - pipeline de oportunidades
3. **Proposal orchestration**
   - `Engagement Manager`
   - `Lead Solutions Architect`
   - `Delivery & Risk Director`
   - `Sales Partner`

El resultado incluye:

- `intelligence_dossier`
- `opportunities_pipeline`
- `proactive_proposals`

## Contratos principales

| Artefacto | Contrato |
|---|---|
| `global_report_payload.json` | payload global refinado sobre esquemas de `global_report.py` |
| `commercial_report_payload.json` | payload comercial basado en `commercial.py` |

## Puntos de control y riesgo operativo

| Punto | Qué protege | Riesgo si falla |
|---|---|---|
| `build_global_report_payload.py` | consolidación fiel de torres | la dirección recibe una visión parcial o distorsionada |
| `run_executive_refiner.py` | calidad de narrativa ejecutiva | el output global queda técnico pero no accionable |
| `run_commercial_refiner.py` | traducción a contexto de cuenta | la explotación comercial se desacopla del diagnóstico real |
| renderers global/commercial | consistencia final de presentación | erosiona credibilidad, aunque no debería cambiar la verdad |

## Relación con el flujo por torre

El diseño actual depende de que las torres produzcan artefactos fiables. En especial:

- el pipeline global prefiere blueprints por encima de artefactos legacy;
- el pipeline comercial aprovecha los blueprints como catálogo táctico;
- cuanto más completa y verificada sea la salida por torre, más coherente será la capa global/comercial.

## Qué debería retener un lector empresarial

1. la capa global **agrega y prioriza**;
2. la capa comercial **explota y activa**;
3. ninguna de las dos debería redefinir la realidad que ya fijó cada blueprint por torre;
4. la calidad de estas capas depende directamente de la calidad y completitud del flujo top-down por torre.
