---
status: Verified
owner: docs-governance
source_of_truth:
  - ../../src/assessment_engine/schemas/annex_synthesis.py
  - ../../src/assessment_engine/schemas/blueprint.py
  - ../../src/assessment_engine/schemas/global_report.py
  - ../../src/assessment_engine/schemas/commercial.py
  - ../../src/assessment_engine/scripts/lib/contract_utils.py
  - ../../src/assessment_engine/scripts/render_tower_annex_from_template.py
  - ../../src/assessment_engine/scripts/render_tower_blueprint.py
  - ../../src/assessment_engine/scripts/render_global_report_from_template.py
  - ../../src/assessment_engine/scripts/render_commercial_report.py
  - ../../src/assessment_engine/scripts/render_web_presentation.py
last_verified_against: 2026-05-02
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Payload, schema and renderer boundaries

Este documento fija la frontera entre:

1. **payloads JSON** que expresan la verdad estructurada;
2. **schemas Pydantic** que gobiernan esa verdad;
3. **renderizadores** que convierten esa verdad en DOCX o HTML.

## Regla principal

Los renderizadores **no deben ser la fuente de verdad** del sistema. Su responsabilidad es:

- cargar un payload;
- validarlo o normalizarlo;
- presentarlo como entregable final.

La lógica de negocio y el contrato deben vivir antes, en payloads y schemas.

## Niveles reales de enforcement

No todos los consumidores aplican el contrato con la misma dureza. A día de hoy existen tres niveles:

| Nivel | Comportamiento real | Casos |
|---|---|---|
| Estricto | valida con `model_validate(...)` y aborta si el payload no cumple | `render_tower_blueprint.py`, `render_global_report_from_template.py` |
| Tolerante | intenta validar, registra desviaciones y cae a `model_construct(...)` para seguir | rutas legacy o de compatibilidad explícita que aún no han sido endurecidas |
| Implícito | consume JSON sin schema Pydantic final de entrada/salida en el propio render | `render_web_presentation.py` |

Por tanto, el schema sigue siendo el **contrato deseado**, pero no todos los renderizadores lo **enfuerzan** de forma estricta en ejecución.

## Mapa principal

| Capa | Payload | Schema | Consumidor principal | Salida |
|---|---|---|---|---|
| Torre ejecutiva | `approved_annex_<tower>.template_payload.json` | `AnnexPayload` | `render_tower_annex_from_template.py` | `annex_<tower>_<client>_final.docx` |
| Torre estratégica | `blueprint_<tower>_payload.json` | `BlueprintPayload` | `render_tower_blueprint.py` | `Blueprint_Transformacion_<TOWER>_<client>.docx` |
| Global ejecutiva | `global_report_payload.json` | `GlobalReportPayload` | `render_global_report_from_template.py` | `Informe_Ejecutivo_Consolidado_<client>.docx` |
| Comercial interna | `commercial_report_payload.json` | `CommercialPayload` | `render_commercial_report.py` | `Account_Action_Plan_<client>.docx` |
| Dashboard web | `global_report_payload.json` + blueprints de torres | sin schema único estricto en render | `render_web_presentation.py` | `presentation/index.html` |

## Contratos por payload

### 1. Annex payload

- archivo: `approved_annex_<tower>.template_payload.json`
- schema: `AnnexPayload`
- render principal: `render_tower_annex_from_template.py`

Características de la frontera:

- el sintetizador del anexo parte de un `executive handover` derivado del blueprint con score, riesgos estructurales, decisiones e iniciativas;
- score global, bandas, gaps, riesgos e iniciativas prioritarias se fijan de forma determinista desde el blueprint antes del render;
- el render carga el JSON con `robust_load_payload(..., AnnexPayload, "Annex", mode="strict")`;
- el render DOCX del anexo usa por defecto la variante visual nueva (`semantic`) y deja el modo legacy solo como compatibilidad opt-in;
- después aplica `normalize_annex_payload(...)` para completar formas compatibles;
- el contrato objetivo y efectivo en render ya es `AnnexPayload` estricto.

Conclusión:

- el payload del anexo sigue siendo el contrato estructural esperado;
- el LLM del anexo aporta framing y lenguaje ejecutivo, pero ya no debería redefinir los hechos no negociables heredados del blueprint;
- el render puede adaptar detalles de forma tras validar, pero ya no acepta un payload inválido;
- la frontera contrato/presentación queda más alineada con el diseño documentado.

### 2. Blueprint payload

- archivo: `blueprint_<tower>_payload.json`
- schema: `BlueprintPayload`
- render principal: `render_tower_blueprint.py`

Características de la frontera:

- el render carga el JSON y lo normaliza con `normalize_blueprint_payload_dict(...)`;
- después valida con `BlueprintPayload.model_validate(...)`;
- además puede enriquecer la presentación usando:
  - `client_intelligence.json`
  - `approved_annex_<tower>.template_payload.json`

Conclusión:

- la verdad principal sigue estando en el blueprint;
- el render puede usar contexto adicional para presentación, pero no desplaza al blueprint como fuente principal de verdad por torre;
- este es hoy uno de los contratos con enforcement más estricto en la capa de render.

### 3. Global report payload

- archivo: `global_report_payload.json`
- schema: `GlobalReportPayload`
- render principal: `render_global_report_from_template.py`

Características de la frontera:

- el render valida directamente con `GlobalReportPayload.model_validate(...)`;
- si falla la validación, termina con error;
- consume secciones ejecutivas ya refinadas:
  - `executive_summary`
  - `burning_platform`
  - `tower_bottom_lines`
  - `target_vision`
  - `execution_roadmap`
  - `executive_decisions`

Conclusión:

- aquí la frontera es más estricta;
- el render global espera que el payload ya llegue con estructura ejecutiva coherente;
- junto con blueprint, es la referencia más clara de contrato estricto antes de renderizar.

### 4. Commercial payload

- archivo: `commercial_report_payload.json`
- schema: `CommercialPayload`
- render principal: `render_commercial_report.py`

Características de la frontera:

- el render usa `robust_load_payload(..., CommercialPayload, "Commercial Account Plan", mode="strict")`;
- consume:
  - `commercial_summary`
  - `gtm_strategy`
  - `stakeholder_matrix`
  - `opportunities_pipeline`
  - `proactive_proposals`
  - `intelligence_dossier`

Conclusión:

- el render comercial trabaja sobre un contrato explícito como diseño objetivo y ya lo exige en tiempo de render;
- el entregable DOCX sigue siendo derivado de un payload comercial ya resuelto.

### 5. Dashboard web

- entrada principal: `global_report_payload.json`
- entrada secundaria: `blueprint_<tower>_payload.json` por torre
- render principal: `render_web_presentation.py`

Características de la frontera:

- no valida ni `global_report_payload.json` ni los blueprints con un schema Pydantic en el propio render;
- no define un schema único de salida antes de renderizar;
- construye un objeto intermedio `nexus_data`;
- mezcla:
  - estrategia global,
  - heatmap,
  - roadmap,
  - detalles tácticos por torre desde blueprints.

Conclusión:

- el dashboard web es una **vista derivada compuesta**;
- su contrato efectivo está más implícito en el código del render que en un schema dedicado;
- conviene tratarlo como capa de presentación agregada, no como fuente de verdad.

## Qué artefactos deben gobernar a qué render

| Renderizador | Payload que manda | Comentario |
|---|---|---|
| `render_tower_annex_from_template.py` | `AnnexPayload` | Presenta el anexo ejecutivo; admite normalización menor |
| `render_tower_blueprint.py` | `BlueprintPayload` | Puede usar annex e inteligencia como apoyo de render |
| `render_global_report_from_template.py` | `GlobalReportPayload` | Valida de forma estricta antes de renderizar |
| `render_commercial_report.py` | `CommercialPayload` | Consume el contrato comercial ya cerrado |
| `render_web_presentation.py` | vista compuesta desde global + blueprints | No define hoy un schema Pydantic final propio |

## Fronteras que deben mantenerse

### Lo que debe decidir el payload/schema

- estructura del contenido;
- nombres y tipos de campos;
- relaciones entre secciones;
- metadata de versión y linaje.

### Lo que debe decidir el render

- layout;
- estilo visual;
- tablas, bullets, bloques de texto;
- composición final en DOCX o HTML.

### Lo que no debería decidir el render

- reglas de scoring;
- traducción de `score` a banda de madurez;
- significado de los campos;
- contrato entre etapas;
- verdad de negocio o arquitectura.

En la ruta activa, la traducción `score -> band` debe quedar resuelta antes o durante la construcción canónica del payload mediante helpers compartidos de dominio. Si un render necesita completar una banda ausente, debe hacerlo reutilizando esa misma policy compartida y no inventando una nueva semántica local.

## Tensiones actuales visibles

1. algunos consumidores todavía normalizan o rellenan campos para compatibilidad;
2. el dashboard web no tiene aún un schema final explícito propio;
3. `render_tower_blueprint.py` usa annex e inteligencia adicional para enriquecer presentación;
4. persisten rastros legacy en parte del ecosistema documental y de artefactos;
5. el sintetizador del anexo ya exige `BlueprintPayload` válido antes de construir el handover, pero otras rutas legacy aún pueden seguir siendo tolerantes.

Estas tensiones no invalidan el diseño actual, pero deben permanecer visibles para que la evolución futura no mueva la verdad desde los contracts hacia la capa de presentación.

## Observaciones de auditoría

1. Los schemas `AnnexPayload`, `BlueprintPayload`, `GlobalReportPayload` y `CommercialPayload` existen y están alineados con los nombres de payload descritos aquí.
2. Los tests de `tests/test_contract_handover.py` y `tests/test_payload_validation.py` validan los contratos principales a nivel de schema y el baseline smoke actual ya incluye artefactos reales para blueprint, annex, global y comercial.
3. La mayor desviación restante entre diseño y enforcement ya no está en los renderizadores finales de annex/commercial ni en el sintetizador del anexo, sino en las rutas legacy o de compatibilidad que todavía usan carga tolerante de forma explícita.

## Regla documental recomendada

Cuando se modifique un payload o un renderizador:

1. revisar primero el schema correspondiente;
2. después revisar el payload productor;
3. por último revisar el render consumidor;
4. actualizar este documento y `docs/documentation-map.yaml` si cambia la frontera entre contrato y presentación.
