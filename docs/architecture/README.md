---
status: Verified
owner: docs-governance
source_of_truth:
- ../SYSTEM_ARCHITECTURE.md
- ../../src/assessment_engine/domain/
- ../../src/assessment_engine/application/
- ../../src/assessment_engine/mcp_server.py
- ../../src/assessment_engine/domain/schemas/
- ../../tests/
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
---

# Architecture

Esta carpeta inicia la **descomposición canónica** de la arquitectura de `assessment-engine`. Su objetivo es sustituir gradualmente la dependencia de un único documento narrativo y repartir la arquitectura en piezas más mantenibles.

## Qué problema de negocio resuelve esta capa

`assessment-engine` no es solo un conjunto de scripts de IA y renderizado. A nivel empresarial actúa como una **fábrica de entregables de assessment** con tres resultados esperados:

1. convertir respuestas, contexto y evidencias en una **lectura técnica defendible**;
2. elevar esa lectura a una **narrativa ejecutiva consistente**;
3. reutilizar la misma verdad estructural para **priorización comercial y comunicación visual**.

La función de esta carpeta es explicar **cómo se gobierna esa cadena de valor** sin obligar al lector a recorrer el código o los artefactos de `working/`.

## Estado actual

La referencia arquitectónica más completa sigue siendo [`../SYSTEM_ARCHITECTURE.md`](../SYSTEM_ARCHITECTURE.md), pero esta carpeta pasa a ser el destino canónico para la arquitectura viva del proyecto.

## Cómo leer esta carpeta según la audiencia

| Si necesitas entender... | Lee primero | Qué obtienes |
|---|---|---|
| la visión ejecutiva completa del proyecto | `../strategy/executive-project-guide.md` | una lectura rápida de valor, fuentes de verdad y riesgos |
| el recorrido empresarial extremo a extremo | `../SYSTEM_ARCHITECTURE.md` | vista global del sistema y sus capas |
| la generación de verdad por torre | `tower-pipeline.md` | cómo nace el activo canónico y qué controles lo sostienen |
| la evaluación de precisión y benchmarks | `rage-architecture.md` | cómo se investigan y auditan evidencias contra regulaciones |
| las reglas duras de seguridad y de-duplicación | `policy-engine-architecture.md` | cómo compila el motor las directivas y FAIR de riesgos |
| la persistencia de aserciones y base de datos | `epistemic-graph-architecture.md` | cómo funciona el Event Sourcing y la base CQRS en SQLite |
| la elevación a nivel dirección y ventas | `global-commercial-pipelines.md` | cómo se consolida la lectura ejecutiva y comercial |
| la inteligencia estratégica reutilizable del cliente | `client-intelligence.md` | cómo se estructura, migra y consume el dossier compartido |
| la superficie real de artefactos | `working-artifacts.md` | qué archivos mandan y cuáles son solo derivados |
| la exposición como servicio/integración | `mcp-mode.md` | qué parte del sistema es automatizable desde fuera |

## Núcleo arquitectónico observado en el repo

### Modos de operación

1. **Modo pipeline**
   - Orquestado desde scripts bajo `src/assessment_engine/application/`
   - Flujos principales:
     - `run_tower_pipeline.py`
     - `run_global_pipeline.py`
     - `run_commercial_pipeline.py`

2. **Modo servidor de herramientas**
   - Expuesto por `src/assessment_engine/mcp_server.py`
   - Permite que un supervisor externo orqueste capacidades del motor

### Áreas estructurales del código

| Área | Ruta principal | Rol |
|---|---|---|
| Orquestación | `src/assessment_engine/application/` | Secuencia de pipelines, refinadores y renderizadores |
| Contratos | `src/assessment_engine/domain/schemas/` | Esquemas Pydantic de payloads entre etapas |
| Presentación | `templates/` y renderizadores | Salida HTML y DOCX |
| Tests | `tests/` | Validación de entorno, contratos, render y lógica |

### Capacidades empresariales que emergen de esas áreas

| Capacidad | Soporte técnico principal | Valor empresarial |
|---|---|---|
| Normalización de entrada | `build_case_input.py`, `build_evidence_ledger.py` | reduce ambigüedad y mejora trazabilidad del assessment |
| Diagnóstico técnico canónico | `run_scoring.py`, `run_evidence_analyst.py`, `run_tower_blueprint_engine.py` | crea una base defendible para decisiones de transformación |
| Síntesis ejecutiva alineada | `run_executive_annex_synthesizer.py`, payloads y renderers | permite hablar a CTO/ejecutivo sin romper la verdad técnica |
| Consolidación multi-torre | `build_global_report_payload.py`, `run_executive_refiner.py` | traduce señales dispersas en agenda de dirección |
| Activación comercial | `run_commercial_refiner.py`, `render_commercial_report.py` | convierte hallazgos técnicos en conversación de cuenta |
| Presentación final | renderers DOCX/HTML y plantillas | materializa la propuesta en artefactos consumibles |

### Componentes visibles en la implementación actual

- preparación determinista de datos (`build_*`, `run_scoring.py`);
- evaluación de precisión en caliente RAGE (`agentic_benchmarker.py`);
- análisis por IA y síntesis (`run_tower_blueprint_engine.py`, refinadores);
- renderizadores de entregables (`render_*`);
- herramientas internas de control de calidad bajo `src/assessment_engine/application/tools/`.

## Prioridades documentales de esta carpeta

1. separar arquitectura conceptual de detalles operativos;
2. documentar límites entre pipelines, schemas y renderizadores;
3. dejar explícita la relación entre modo pipeline y modo servidor;
4. reemplazar paulatinamente partes de `SYSTEM_ARCHITECTURE.md` por piezas más específicas.

## Regla de lectura recomendada

Cuando esta carpeta describa una parte del sistema, debe dejar visibles siempre cuatro cosas:

1. **qué activo canónico nace en esa fase**;
2. **qué dependencias o contratos sostienen esa fase**;
3. **qué valor aporta al negocio o al delivery**;
4. **qué síntomas operativos aparecerían si esa fase se degrada**.

## Siguiente paso recomendado

Subdocumentos ya iniciados:

- [`tower-pipeline.md`](tower-pipeline.md)
- [`global-commercial-pipelines.md`](global-commercial-pipelines.md)
- [`client-intelligence.md`](client-intelligence.md)
- [`rage-architecture.md`](rage-architecture.md)
- [`policy-engine-architecture.md`](policy-engine-architecture.md)
- [`epistemic-graph-architecture.md`](epistemic-graph-architecture.md)
- [`critical-modules.md`](critical-modules.md)
- [`mcp-mode.md`](mcp-mode.md)
- [`working-artifacts.md`](working-artifacts.md)

Pendientes siguientes:

- coordinar esta carpeta con `docs/contracts/payload-render-boundaries.md`;
- guías más específicas de contratos entre payloads;
- migración del contenido más fiable desde `SYSTEM_ARCHITECTURE.md`.
