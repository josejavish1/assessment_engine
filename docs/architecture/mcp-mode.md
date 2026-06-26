---
status: Verified
owner: docs-governance
source_of_truth:
- ../../src/assessment_engine/mcp_server.py
- ../../src/assessment_engine/application/
last_verified_against: 2026-05-01
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
---

# MCP mode

Además del modo pipeline, `assessment-engine` puede exponerse como servidor MCP para que un agente supervisor externo invoque capacidades del motor bajo demanda.

## Implementación actual

El servidor vive en:

- `src/assessment_engine/mcp_server.py`

Usa:

- `FastMCP`

Y ejecuta scripts internos mediante:

- `python -m assessment_engine.application.<module>`

## Rol arquitectónico

El modo MCP no sustituye al pipeline completo. Su papel es:

- exponer operaciones concretas como herramientas;
- permitir orquestación dinámica por un supervisor externo;
- ofrecer inspección de estado y renderizado puntual sin obligar a ejecutar todo el pipeline.

## Herramientas expuestas actualmente

| Tool | Propósito |
|---|---|
| `build_tower_payload` | Construye un payload intermedio **legacy** para anexo de torre a partir de un annex refined heredado |
| `render_tower_docx` | Renderiza el DOCX final del anexo |
| `generate_radar_chart` | Genera el radar global desde payload global |
| `render_commercial_docx` | Renderiza el documento comercial final |
| `get_tower_state` | Inspecciona artefactos de una torre y resume su estado |

## Modelo de ejecución

Cada tool:

- llama a un script interno aislado;
- propaga `PYTHONPATH`;
- captura `stdout` y `stderr`;
- falla explícitamente si el subproceso devuelve código distinto de cero.

## Estado e inspección

La tool `get_tower_state` prioriza ya el flujo canónico y devuelve un bloque `canonical` con:

- `blueprint_*_payload.json`
- `approved_annex_*.template_payload.json`
- DOCX derivados cuando existen

Además, valida esos payloads contra `BlueprintPayload` y `AnnexPayload`, y degrada de forma estructurada a `invalid` o `error` si encuentra contratos rotos, JSON corrupto o artefactos no decodificables.

El detalle legacy por secciones (`asis`, `risks`, `gap`, `tobe`, `todo`, `conclusion`) sigue expuesto como superficie diagnóstica secundaria, no como lectura principal del estado operativo.

## Relación con la arquitectura vigente

Hay una tensión útil que conviene mantener visible:

1. el modo pipeline actual está claramente orientado a `blueprint -> annex`;
2. la inspección MCP ya refleja primero ese flujo canónico;
3. `build_tower_payload` y el detalle legacy restante en `get_tower_state` deben entenderse como compatibilidad explícita para superficies heredadas, no como modelo principal.

## Uso recomendado en documentación

Trata el modo MCP como:

- **capacidad de servicio y automatización**, no como la narrativa principal del flujo canónico;
- una capa útil para supervisores externos, integraciones y tooling;
- una superficie ya alineada en su inspección principal con el flujo top-down vigente, aunque conserve adaptadores legacy puntuales.
