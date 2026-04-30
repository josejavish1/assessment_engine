---
status: Verified
owner: docs-governance
source_of_truth:
  - ../SYSTEM_ARCHITECTURE.md
  - ../../src/assessment_engine/scripts/run_tower_pipeline.py
  - ../../src/assessment_engine/scripts/run_global_pipeline.py
  - ../../src/assessment_engine/scripts/run_commercial_pipeline.py
  - ../../src/assessment_engine/scripts/render_web_presentation.py
  - ../../src/assessment_engine/schemas/
  - ./tower-pipeline.md
  - ./global-commercial-pipelines.md
  - ./critical-modules.md
last_verified_against: 2026-04-30
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Executive project guide

Este documento explica `assessment-engine` como lo leería una dirección de delivery, preventa o transformación: **qué fabrica, qué verdad gobierna el sistema, qué piezas son críticas y cómo entender el proyecto sin recorrer todo el código**.

## Qué es realmente este proyecto

`assessment-engine` es una **fábrica de entregables de assessment**. Su función no es solo generar documentos, sino transformar:

- respuestas e inputs del cliente;
- evidencias y scoring;
- interpretación por torre;
- consolidación ejecutiva y comercial;

en una cadena de activos que soporta decisiones de transformación.

## Qué valor aporta

| Capacidad | Resultado visible | Valor empresarial |
|---|---|---|
| Diagnóstico por torre | blueprint por torre | crea una verdad técnica defendible |
| Traducción ejecutiva | annex por torre y reporte global | hace legible la verdad técnica para decisión |
| Activación comercial | account action plan | convierte hallazgos en conversación de cuenta |
| Presentación visual | web presentation | acelera lectura, narrativa y socialización |

## Cómo leer el sistema en 15 minutos

1. **Empieza por la lógica de valor, no por los renderers.**  
   El proyecto manda por payloads y pipelines, no por DOCX u HTML.

2. **Entiende la jerarquía de verdad.**  
   Por torre manda el `blueprint_<tower>_payload.json`. Después vienen annex, global, comercial y web como derivaciones por audiencia.

3. **Distingue bien las capas.**  
   Torre = diagnóstico; global = agenda ejecutiva; comercial = activación de cuenta; web = superficie visual.

4. **Lee los renderers como consumidores.**  
   Un renderer puede normalizar o tolerar desviaciones, pero no debería redefinir el contrato del sistema.

## La cadena principal de valor

| Fase | Activo dominante | Qué decide |
|---|---|---|
| Torre | `blueprint_<tower>_payload.json` | estado, gaps, riesgos, objetivo y roadmap por torre |
| Torre ejecutiva | `approved_annex_<tower>.template_payload.json` | lectura ejecutiva derivada del blueprint |
| Global | `global_report_payload.json` | agenda consolidada de transformación |
| Comercial | `commercial_report_payload.json` | explotación comercial y plan de cuenta |
| Presentación | `presentation/index.html` y DOCX | comunicación final al lector |

## Regla de oro del proyecto

Si dos capas parecen decir cosas distintas, la lectura correcta es:

1. **manda el payload estructural más cercano a la fuente**;
2. después manda el schema;
3. el entregable final solo debe presentar esa verdad.

Eso significa, por ejemplo, que:

- el **blueprint** gobierna la verdad por torre;
- el **global payload** gobierna la verdad ejecutiva consolidada;
- el **comercial payload** gobierna la explotación comercial;
- los **DOCX/HTML** no son la fuente de verdad.

## Qué módulos sostienen el negocio

| Familia | Papel empresarial |
|---|---|
| Orchestrators | ordenan la cadena de producción y la continuidad operativa |
| Engines / Builders | fabrican la verdad estructural que luego reutilizan otras capas |
| Refiners | traducen una verdad previa a otra audiencia sin romper su base |
| Renderers | convierten payloads en entregables consumibles |

La pieza detallada está en [`critical-modules.md`](critical-modules.md).

## Qué dependencias externas sí importan de verdad

| Dependencia | Impacto |
|---|---|
| Vertex AI / agentes | afecta a blueprint, annex, global y comercial |
| Plantillas DOCX | afectan a calidad y consistencia visual, no a la verdad de negocio |
| `working/<client>/...` | actúa como superficie operativa real de artefactos |
| Tests y baseline smoke | protegen contratos, golden files y continuidad del sistema |

## Qué riesgos hay que explicar a negocio o delivery

1. **Drift entre contratos y presentación**  
   aparece cuando el renderer compensa demasiado y oculta un problema real de payload.

2. **Dependencia de IA para tramos críticos**  
   sin acceso operativo a Vertex AI, la parte con más valor del sistema no se completa.

3. **Convivencia con legado**  
   algunas capas aún toleran fallback legacy; eso protege continuidad, pero añade complejidad.

4. **Confundir output bonito con output confiable**  
   la calidad visual importa, pero no sustituye a contrato, linaje y coherencia entre capas.

## Qué significa que el proyecto esté “bien” o “mal”

### Señales sanas

- el blueprint nace y se valida por torre;
- el annex no contradice al blueprint;
- global y comercial reutilizan la verdad previa;
- el smoke baseline existe y la validación pasa;
- la documentación canónica deja claras responsabilidades y contratos.

### Señales de degradación

- faltan payloads en `working/`;
- se rompe el baseline smoke;
- un renderer necesita corregir demasiado contenido;
- global o comercial cuentan una historia que ya no encaja con las torres;
- la documentación empresarial deja de reflejar el flujo real.

## Qué debería leer cada audiencia

| Audiencia | Documento recomendado |
|---|---|
| Dirección / sponsor interno | este documento + `global-commercial-pipelines.md` |
| Delivery / arquitectura | `tower-pipeline.md` + `critical-modules.md` |
| Gobierno técnico / contratos | `../contracts/payload-render-boundaries.md` |
| Operación / soporte | `../operations/pipeline-controls-runbook.md` |

## Decisión documental recomendada

Si el proyecto sigue creciendo, la documentación premium debería proteger siempre estas cuatro vistas:

1. **qué valor empresarial fabrica el sistema**;
2. **qué activo gobierna cada capa**;
3. **qué módulo es crítico y por qué**;
4. **qué hacer cuando una fase no produce su artefacto esperado**.

Mientras esas cuatro preguntas estén contestadas, el proyecto seguirá siendo legible a nivel empresarial aunque cambie la implementación.
