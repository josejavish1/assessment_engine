---
status: Draft
owner: docs-governance
source_of_truth:
  - ../../src/assessment_engine/mcp_server.py
  - ../../src/assessment_engine/scripts/
last_verified_against: 2026-04-30
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# MCP mode

Además del modo pipeline, `assessment-engine` puede exponerse como servidor MCP para que un agente supervisor externo invoque capacidades del motor bajo demanda.

## Implementación actual

El servidor vive en:

- `src/assessment_engine/mcp_server.py`

Usa:

- `FastMCP`

Y ejecuta scripts internos mediante:

- `python -m assessment_engine.scripts.<module>`

## Rol arquitectónico

El modo MCP no sustituye al pipeline completo. Su papel es:

- exponer operaciones concretas como herramientas;
- permitir orquestación dinámica por un supervisor externo;
- ofrecer inspección de estado y renderizado puntual sin obligar a ejecutar todo el pipeline.

## Herramientas expuestas actualmente

| Tool | Propósito |
|---|---|
| `build_tower_payload` | Construye payload intermedio para anexo de torre |
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

La tool `get_tower_state` inspecciona un directorio de caso y busca artefactos legacy de secciones:

- `approved_asis.generated.json`
- `approved_risks.generated.json`
- `approved_gap.generated.json`
- `approved_tobe.generated.json`
- `approved_todo.generated.json`
- `approved_conclusion.generated.json`

Esto sugiere que el modo MCP actual mantiene compatibilidad con una visión más antigua del proceso, aunque la arquitectura principal haya migrado al flujo top-down basado en blueprint.

## Relación con la arquitectura vigente

Hay una tensión útil que conviene mantener visible:

1. el modo pipeline actual está claramente orientado a `blueprint -> annex`;
2. parte del servidor MCP y de su inspección de estado todavía refleja secciones legacy;
3. la evolución futura debería decidir si MCP:
   - se adapta plenamente al modelo top-down actual, o
   - conserva herramientas legacy como compatibilidad explícita.

## Uso recomendado en documentación

Trata el modo MCP como:

- **capacidad de servicio y automatización**, no como la narrativa principal del flujo canónico;
- una capa útil para supervisores externos, integraciones y tooling;
- una superficie que necesita documentación adicional cuando se definan mejor sus herramientas, contratos y flujos top-down equivalentes.
