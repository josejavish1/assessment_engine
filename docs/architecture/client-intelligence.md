---
status: Verified
owner: docs-governance
source_of_truth:
  - ../../src/assessment_engine/schemas/intelligence.py
  - ../../src/assessment_engine/scripts/lib/client_intelligence.py
  - ../../src/assessment_engine/scripts/run_intelligence_harvesting.py
  - ../../src/assessment_engine/scripts/build_case_input.py
  - ../../src/assessment_engine/scripts/run_tower_blueprint_engine.py
  - ../../src/assessment_engine/scripts/build_global_report_payload.py
  - ../../src/assessment_engine/scripts/run_executive_refiner.py
  - ../../src/assessment_engine/scripts/run_commercial_refiner.py
  - ../../src/assessment_engine/prompts/intelligence_prompts.py
  - ../../src/assessment_engine/prompts/global_prompts.py
  - ../../src/assessment_engine/prompts/commercial_prompts.py
last_verified_against: 2026-05-01
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Client intelligence architecture

`client_intelligence.json` es el **dossier estratégico compartido** del cliente. Su función ya no es solo aportar un bloque narrativo auxiliar, sino actuar como contexto reutilizable y trazable para:

- preparación por torre;
- generación de blueprint;
- consolidación global;
- activación comercial.

## Rol actual en la arquitectura

El dossier vive en `working/<client>/client_intelligence.json` y hoy se comporta como un input enriquecido transversal.

La ruta activa ya soporta tres capas de compatibilidad:

- legado plano (`industry`, `ceo_agenda`, `target_maturity_matrix`);
- `2.0`, centrada en estructura básica y `tower_overrides`;
- `3.0`, orientada a contexto operativo real, claims y reutilización en prompts.

La lógica de compatibilidad y derivación vive en `scripts/lib/client_intelligence.py`.

## Contrato pragmático v3

La versión `3.0` añade cinco bloques estructurales:

1. `metadata`
   - identidad del dossier;
   - timestamps de creación y modificación;
   - idioma;
   - timeliness básica;
   - rastro de generación.

2. `profile`
   - industria;
   - tier financiero;
   - modelo operativo;
   - regiones;
   - mercados prioritarios;
   - líneas de negocio.

3. `business_context` y `technology_context`
   - agenda del CEO;
   - prioridades estratégicas;
   - transformaciones activas;
   - vendors dominantes;
   - restricciones operativas;
   - señales de incidentes recientes;
   - horizonte de transformación.

4. `tower_overrides`
   - target maturity;
   - criticidad de negocio;
   - presión regulatoria;
   - urgencia de cambio;
   - restricciones por torre.

5. `claims` y `review`
   - separación entre hecho, inferencia y supuesto;
   - confianza numérica;
   - fuentes;
   - estado de revisión humana.

## Consumo real en los pipelines

### Torre

`build_case_input.py` ya incorpora:

- `target_maturity_default` derivado del dossier;
- `context_summary` desde el contexto real;
- `client_context`, un paquete resumido del dossier para la torre.

`run_tower_blueprint_engine.py` reutiliza ese paquete para alimentar el prompt del blueprint y deja además el contexto del cliente embebido en el payload resultante cuando existe.

### Global

`build_global_report_payload.py` ya carga el dossier si existe y añade un `intelligence_dossier` resumido al payload global.

`run_executive_refiner.py` conserva esa pieza para que el refinado ejecutivo pueda usar agenda, regulación, restricciones y claims en la narrativa final.

### Comercial

`run_commercial_refiner.py` mezcla ya tres capas de contexto:

- payload global estratégico;
- catálogo táctico derivado de blueprints;
- `client_intelligence` resumido.

Esto permite que el Account Action Plan conecte mejor oportunidades con:

- agenda del CEO;
- presión regulatoria;
- mercados prioritarios;
- vendors dominantes;
- restricciones operativas.

## Hoja de ruta aplicada

La evolución implementada en esta iteración queda así:

1. ampliar el contrato y mantener compatibilidad hacia atrás;
2. enriquecer harvesting y smoke con una estructura más rica;
3. llevar el dossier a `case_input`, blueprint, global y commercial;
4. exponer señales de negocio y operación de forma explícita en prompts;
5. cubrir la migración con tests de coerción, consumo y payloads.

## Qué mejora y qué no

Esta arquitectura mejora de forma directa:

- trazabilidad;
- consistencia entre outputs;
- capacidad de reutilizar contexto empresarial;
- calidad de priorización en global y commercial.

No garantiza por sí sola “más inteligencia” si las fuentes de entrada siguen siendo pobres. El siguiente tramo natural ya no es de contrato, sino de **ampliación de harvesting**:

- más señales por geografía y línea de negocio;
- más claims con fuentes diferenciadas;
- mejor cobertura de programas activos, M&A, restricciones y eventos operativos.
