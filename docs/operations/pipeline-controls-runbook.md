---
status: Verified
owner: docs-governance
source_of_truth:
  - ../../src/assessment_engine/scripts/run_tower_pipeline.py
  - ../../src/assessment_engine/scripts/run_global_pipeline.py
  - ../../src/assessment_engine/scripts/run_commercial_pipeline.py
  - ../../src/assessment_engine/scripts/render_web_presentation.py
  - ../../src/assessment_engine/scripts/tools/check_vertex_ai_access.py
  - ../../src/assessment_engine/scripts/tools/regenerate_smoke_artifacts.py
  - ./pipeline-execution.md
  - ./smoke-regeneration.md
  - ./troubleshooting-working.md
last_verified_against: 2026-04-30
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Pipeline controls runbook

Este runbook resume la **operación real** del sistema: qué controles conviene pasar antes de ejecutar, qué señales deben aparecer en cada fase y cómo reaccionar cuando la cadena se rompe.

## Qué intenta proteger

1. continuidad de generación;
2. coherencia entre capas;
3. capacidad de diagnóstico rápido;
4. distinción clara entre problema de credenciales, problema de contrato y problema de render.

## Checklist previo de operación

| Control | Qué confirma |
|---|---|
| entorno Python activo (`./.venv`) | que ejecutas contra el entorno esperado |
| dependencias instaladas | que el repo puede correr scripts y tests |
| acceso a Vertex AI | que los tramos IA no van a fallar por autenticación base |
| inputs/cliente disponibles | que la fase tiene material para producir artefactos |
| `working/<client>/...` legible | que la superficie operativa existe y es consistente |

## Orden recomendado de ejecución

1. **preflight IA** si vas a tocar tramos con agentes;  
2. **pipeline por torre** para crear la verdad base;  
3. **pipeline global** para consolidar;  
4. **pipeline comercial** para activar cuenta;  
5. **render web** para superficie visual;  
6. **smoke y tests** cuando necesites validar baseline o regresiones.

## Señales mínimas de salud por fase

| Fase | Señal mínima |
|---|---|
| Preflight IA | el chequeo de Vertex AI pasa |
| Torre | existe `blueprint_<tower>_payload.json` |
| Annex | existe `approved_annex_<tower>.template_payload.json` |
| Global | existe `global_report_payload.json` |
| Comercial | existe `commercial_report_payload.json` |
| Web | existe `working/<client>/presentation/index.html` |
| Baseline smoke | los artefactos `smoke_ivirma` existen y la validación pasa |

## Primer diagnóstico según síntoma

| Síntoma | Primera lectura correcta | Acción inicial |
|---|---|---|
| no nace ningún payload IA | fallo de acceso o entorno IA | ejecutar `check_vertex_ai_access` |
| existen inputs base pero no blueprint | bloqueo en el engine de torre | revisar `run_tower_pipeline.py` y Vertex AI |
| existe blueprint pero no annex | fallo del sintetizador ejecutivo | revisar `run_executive_annex_synthesizer.py` |
| existe tower pero no global | problema de consolidación entre torres | revisar `build_global_report_payload.py` |
| existe global pero no comercial | fallo en refino comercial | revisar `run_commercial_refiner.py` |
| existe payload pero el DOCX sale mal | problema de render o plantilla | revisar renderer y plantilla, no la verdad base |
| fallan tests ligados a `working/` | puede faltar baseline, no necesariamente hay bug nuevo | verificar artefactos antes de depurar código |

## Árbol corto de respuesta

### 1. Falla antes de producir artefactos IA

Piensa primero en:

- credenciales;
- proyecto o location;
- acceso base al modelo;
- timeout del paso completo.

La acción correcta suele ser:

```bash
./.venv/bin/python -m assessment_engine.scripts.tools.check_vertex_ai_access
```

### 2. Falla una capa derivada pero la anterior existe

Piensa primero en:

- contrato roto entre etapas;
- payload incompleto o desalineado;
- normalización excesiva en render;
- dependencia previa no regenerada.

### 3. Falla la presentación pero no el payload

Piensa primero en:

- renderer;
- plantilla DOCX;
- estilo o composición;
- diferencias entre modo legacy y semántico.

## Controles de recuperación recomendados

| Escenario | Recuperación preferida |
|---|---|
| baseline smoke perdido | usar `regenerate_smoke_artifacts` |
| duda entre problema local o IA | ejecutar primero `--local-only` |
| bloqueo largo en IA | usar timeouts explícitos del runner |
| artefacto de torre ausente | relanzar torre o reanudar desde el paso apropiado |
| artefacto global/comercial ausente | relanzar la fase consumidora inmediata |

## Qué no hacer

1. No asumir bug lógico solo porque falle un test que depende de `working/`.
2. No usar un DOCX bonito como prueba de verdad estructural.
3. No corregir en render un problema que pertenece al payload productor.
4. No tratar el flujo legacy como si fuera la única referencia si ya existe payload moderno.

## Señales de que la operación está bajo control

- los payloads clave aparecen donde toca;
- el baseline smoke es reproducible;
- los errores distinguen bien entre IA, contrato y render;
- la documentación canónica coincide con lo que realmente hace el repo.

## Dónde profundizar

- ejecución: [`pipeline-execution.md`](pipeline-execution.md)
- regeneración smoke: [`smoke-regeneration.md`](smoke-regeneration.md)
- incidencias sobre `working/`: [`troubleshooting-working.md`](troubleshooting-working.md)
- contratos: [`../contracts/artifact-contracts.md`](../contracts/artifact-contracts.md)
