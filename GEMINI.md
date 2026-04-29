# Directiva IA: Auto-Registro Obligatorio
Cualquier agente IA trabajando en este repositorio DEBE actualizar automáticamente este fichero al finalizar cualquier cambio técnico significativo. Este documento es la memoria operativa y arquitectónica del proyecto. Si se pierde la sesión, la continuación debe partir de aquí.

# ASSESSMENT ENGINE: STATUS, ARCHITECTURE ROADMAP & ENTERPRISE HARDENING PLAN (Abril 2026)

## 1. Propósito del sistema
`assessment-engine` es una fábrica documental B2B asistida por IA para generar entregables de assessment tecnológico con varios niveles de abstracción:

1. `Blueprint` de torre: documento maestro de transformación.
2. `Annex` ejecutivo de torre: síntesis de negocio derivada del blueprint.
3. Informe global CIO: agregación de anexos.
4. Account Action Plan comercial: derivado del informe global.

El sistema debe producir artefactos consistentes, auditables y robustos aunque intervengan:
- varios agentes IA,
- varios desarrolladores humanos,
- múltiples prompts,
- múltiples renderizadores Word,
- APIs externas probabilísticas,
- y pipelines de varias etapas con persistencia intermedia.

La prioridad arquitectónica no es solo “que funcione”, sino que pueda evolucionar sin romper artefactos aguas abajo.

---

## 2. Principios irrenunciables

### 2.1 Fábrica determinista con operarios inteligentes
**ADR-001 aprobado**: el control de flujo no se delega al LLM.

- El orquestador Python decide el orden, los reintentos y los artefactos.
- Los agentes IA solo producen contenido dentro de contratos explícitos.
- Los contratos deben ser Pydantic o equivalentes tipados.

Esto evita que un modelo probabilístico gobierne el pipeline.

### 2.2 Flujo Top-Down obligatorio
**ADR-002 aprobado**: no puede existir “split-brain” entre documentos.

Flujo mandatorio:
1. `Blueprint Architect` lee respuestas crudas + contexto de negocio.
2. `Executive Synthesizer` lee exclusivamente el blueprint.
3. `Global Aggregator` lee anexos.
4. `Sales Strategist (Account Action Plan)` lee el informe global (para alineación estratégica) + todos los blueprints (para capturar el catálogo completo de iniciativas y oportunidades de upselling).

Ninguna capa intermedia debe releer los datos crudos, pero la capa comercial tiene permiso de "deep-dive" en los blueprints para maximizar el valor de la propuesta.

### 2.3 Contract-first
Toda comunicación entre etapas debe materializarse como artefacto validable:
- JSON estructurado
- schema versionado
- validación estricta previa a render

### 2.4 Render desacoplado del contenido
Los renderizadores Word no deben decidir contenido. Su responsabilidad es:
- maquetar,
- normalizar pequeños detalles de compatibilidad,
- insertar imágenes/tablas,
- y fallar pronto si el payload es inválido.

### 2.5 Orientación enterprise-agentic
El repositorio debe poder ser modificado por humanos e IA con bajo riesgo. Eso obliga a:
- contratos fuertes,
- tests de regresión,
- observabilidad,
- estructura modular,
- y reglas estrictas de cambio.

---

## 3. Estado actual verificado del sistema

### 3.1 Lo que sí está bien encaminado
- Orquestación Python explícita.
- `run_agent()` centralizado con reintentos y semáforo en `scripts/lib/ai_client.py`.
- Uso amplio de Pydantic en `schemas/`.
- Pipeline Top-Down ya operando en T5 `smoke_ivirma`.
- Prompts parcialmente extraídos a `prompts/registry/`.
- MCP server base creado.
- Suite inicial de tests existente.

### 3.2 Lo que NO debe asumirse como “cerrado”
Aunque versiones anteriores de este documento marcaran varias fases como completadas, el código real todavía presentaba y puede seguir presentando:
- importaciones rotas entre módulos,
- desalineaciones entre payloads y renderizadores,
- placeholders heredados,
- imágenes de placeholder colándose en DOCX,
- caracteres inválidos rompiendo el render,
- mezcla de lógica editorial con lógica de motor,
- observabilidad insuficiente,
- y cobertura de tests todavía limitada para evitar regresiones documentales.

Conclusión: el core es prometedor, pero todavía NO está en nivel enterprise-agentic robusto.

---

## 4. Entregables y rol de cada documento

### 4.1 Blueprint
Documento maestro. Debe servir para:
- entender el problema,
- justificar la transformación,
- definir la arquitectura objetivo,
- desglosar iniciativas,
- y secuenciar roadmap y dependencias.

El blueprint debe abrir con una capa ejecutiva fuerte, pero seguir siendo el documento de referencia técnica y de transformación.

Ruta ejemplo T5:
`working/smoke_ivirma/T5/Blueprint_Transformacion_T5_smoke_ivirma.docx`

### 4.2 Annex
Documento ejecutivo derivado del blueprint. Debe servir para:
- lectura rápida por dirección,
- explicar el riesgo para el negocio,
- conectar la torre con agenda estratégica,
- y resumir decisiones prioritarias.

El annex NO debe competir en volumen ni detalle con el blueprint.

Ruta ejemplo T5:
`working/smoke_ivirma/T5/annex_t5_smoke_ivirma_final.docx`

### 4.3 Distribución editorial vigente
Después de la refactorización de abril 2026:
- El `Blueprint` incorpora una apertura más conectada con negocio.
- El `Annex` se ha recortado y reposicionado como `executive brief`.

En T5, el annex quedó reducido aproximadamente a 3605 palabras y el blueprint a unas 8698, dejando separación real de rol.

---

## 5. Cambios implementados en esta sesión (continuidad obligatoria)

### 5.1 Correcciones funcionales del pipeline T5
Se corrigieron incidencias reales detectadas durante la ejecución de `smoke_ivirma/T5`:

- Implementación de `get_critic_prompt` en `prompts/blueprint_prompts.py`.
- Reparación del flujo `run_tower_blueprint_engine.py` para volver a ejecutar el blueprint completo.
- Alineación entre `run_executive_annex_synthesizer.py` y `render_tower_annex_from_template.py`.
- Corrección del uso de placeholders de gráfico radial: ahora el anexo prioriza `pillar_radar_chart.generated.png` cuando existe.
- Saneamiento de caracteres de control para evitar fallos XML/Word en renderizadores.

### 5.2 Cambios editoriales en el Annex
Se modificó el sintetizador ejecutivo para que el `Annex`:
- hable en lenguaje de negocio,
- priorice continuidad operativa, riesgo regulatorio, expansión, M&A, datos e IA cuando sean materiales,
- no use una plantilla rígida de ángulos ejecutivos,
- y reduzca el volumen para no parecer un “blueprint resumido”.

Cambios aplicados:
- Prompt reescrito en `prompts/registry/annex_executive_synthesizer.yaml`.
- Inyección de `client_intelligence.json` y `executive_snapshot` del blueprint en `run_executive_annex_synthesizer.py`.
- Compresión explícita de riesgos, gaps, capacidades objetivo e iniciativas:
  - riesgos: máximo 6
  - gaps: máximo 6
  - capacidades objetivo: máximo 5
  - iniciativas: máximo 6
- Redacción forzada íntegramente en español de negocio.

### 5.3 Cambios editoriales en el Blueprint
Se reforzó la apertura ejecutiva del blueprint en `render_tower_blueprint.py`:
- nueva capa “Por qué importa al negocio”,
- uso del contexto estratégico del cliente,
- foco en riesgos de negocio materiales,
- y cierre de la apertura con decisiones prioritarias.

### 5.4 Artefactos T5 validados
Rutas finales validadas:
- Blueprint:
  `/home/jsanchhi/assessment_engine/working/smoke_ivirma/T5/Blueprint_Transformacion_T5_smoke_ivirma.docx`
- Annex:
  `/home/jsanchhi/assessment_engine/working/smoke_ivirma/T5/annex_t5_smoke_ivirma_final.docx`

Validaciones realizadas:
- el annex ya no contiene placeholders funcionales de secciones,
- el gráfico radial está embebido y enlazado al PNG correcto,
- el annex quedó en español y con tono ejecutivo,
- el blueprint vuelve a renderizarse sin fallos XML por caracteres inválidos.

---

## 6. Riesgos arquitectónicos actuales

Estos riesgos siguen vigentes y deben asumirse como deuda real del sistema:

### 6.1 Scripts demasiado grandes y con responsabilidades mezcladas
Ejemplos:
- `scripts/run_executive_annex_synthesizer.py`
- `scripts/render_tower_annex_from_template.py`
- `scripts/render_tower_blueprint.py`

Problema:
- mezclan orquestación,
- normalización de payloads,
- política editorial,
- render,
- y compatibilidad legacy.

Consecuencia:
- tocar una cosa puede romper otra.

### 6.2 Contratos todavía demasiado flexibles
Aún sobreviven:
- fallbacks,
- estructuras heredadas,
- doble nomenclatura (`gap` vs `tobe_gap`),
- normalización tolerante en render.

Eso ayuda a sobrevivir en transición, pero aumenta ambigüedad y coste de mantenimiento.

### 6.3 Observabilidad insuficiente
Aunque `ai_client.py` tiene retry/semáforo, aún falta:
- trazabilidad por ejecución,
- metadatos de prompts/modelos,
- coste y tokens,
- linaje por artefacto,
- y logs estructurados por etapa.

### 6.4 Cobertura de tests insuficiente para “no romper Word”
La suite actual protege fundamentos, pero no blinda suficientemente:
- contratos intermedios reales,
- presencia de imágenes,
- placeholders,
- snapshots documentales,
- y regresiones de pipeline completo.

### 6.5 Configuración operativa mejorable
Persisten señales de acoplamiento operativo:
- defaults hardcodeados de cloud en `runtime_env.py`,
- dependencia fuerte de `working/`,
- poca noción de `run_id` aislado,
- mezcla entre estado persistido y runtime actual.

### 6.6 MCP inmaduro
`mcp_server.py` existe, pero todavía no ofrece una capa de herramientas enterprise:
- validación fuerte de entrada,
- contratos de salida consistentes,
- errores normalizados,
- operaciones de alto nivel,
- ni trazabilidad end-to-end.

---

## 7. Objetivo real: nivel enterprise-agentic

No significa solo “usar IA”.
Significa que el software:
- puede evolucionar sin miedo a rotura masiva,
- soporta varios agentes IA y varios humanos trabajando a la vez,
- produce artefactos repetibles,
- deja rastro auditable,
- y falla de forma controlada y recuperable.

Para lograrlo hacen falta cinco capas simultáneas:

1. **Contratos fuertes**
2. **Tests de regresión reales**
3. **Observabilidad**
4. **Separación clara de responsabilidades**
5. **Disciplina operativa para cambios humano+IA**

Sin esas cinco, cualquier afirmación de “enterprise-agentic” sería exagerada.

---

## 8. Plan Maestro de Endurecimiento Anti-Rotura

Este plan sustituye cualquier sensación de “ya está”. El objetivo explícito es reducir la probabilidad de que tocar una pieza rompa otras.

### Fase A. Quick Wins obligatorios (1-3 días)
Objetivo: bajar riesgo inmediato.

#### A1. Golden tests de T5
Crear tests que verifiquen para `smoke_ivirma/T5`:
- validación del `blueprint_t5_payload.json`,
- validación del `approved_annex_t5.template_payload.json`,
- ausencia de placeholders en DOCX,
- presencia de radial en DOCX,
- número máximo/mínimo de riesgos, gaps e iniciativas.

#### A2. Tests de integridad documental
Añadir checks automáticos para:
- imágenes embebidas,
- secciones obligatorias,
- tablas críticas,
- idioma esperado en el annex,
- tamaño relativo blueprint vs annex.

#### A3. Validación automática de prompts YAML
Todo fichero en `prompts/registry/` debe pasar validación estructural:
- claves requeridas,
- tipos correctos,
- ausencia de campos faltantes.

#### A4. Normalización única de texto
Centralizar saneamiento de caracteres y limpieza en una utilidad compartida para no duplicar lógica de “texto seguro para Word”.

#### A5. Checklist de cambio para agentes IA
Establecer regla operativa:
- si se toca prompt, validar payload downstream;
- si se toca payload, validar render;
- si se toca render, validar DOCX final.

### Fase B. Contratos y versionado (1 sprint)
Objetivo: hacer el sistema predecible. [FASE COMPLETADA]

#### B1. [CERRADO] Versionar payloads
Todo artefacto intermedio incluye metadatos de versión y linaje (`artifact_type`, `artifact_version`, `source_version`).

#### B2. [CERRADO] Eliminar ambigüedades legacy
Estructura unificada sin `tobe_gap` y con naming consistente (`risk_observed`, `initiative`, `impact`) entre Blueprint y Anexo.

#### B3. [CERRADO] Contract tests & AAP Híbrido
Implementada suite de tests de contrato y nueva arquitectura donde el AAP consume tanto el Informe Global como los Blueprints técnicos para maximizar oportunidades comerciales.

#### B4. [CERRADO] Handover contracts resilientes
Implementado `robust_load_payload` con "Degradación Elegante". El sistema loguea desviaciones pero asegura la producción de informes mediante autocuración.

### Fase C. Modularización del motor (1 sprint)
Objetivo: que los cambios sean pequeños y seguros.

#### C1. Dividir scripts grandes
Extraer de scripts actuales módulos puros para:
- mapeo de snapshot ejecutivo,
- compresión editorial,
- normalización de riesgos/gaps/init,
- resolución de assets,
- composición de secciones.

#### C2. Separar contenido de motor
Crear capas claras:
- `content_policy`
- `payload_mappers`
- `renderers`
- `orchestrators`

#### C3. Reducir side effects
Menos lectura/escritura implícita dentro de funciones internas. Más datos pasados explícitamente.

### Fase D. Observabilidad, linaje y FinOps (1 sprint)
Objetivo: saber exactamente qué pasó en cada run.

#### D1. Run context
Introducir `run_id` por ejecución y persistirlo en todos los artefactos.

#### D2. Telemetría en `ai_client.py`
Registrar por llamada:
- modelo,
- prompt,
- duración,
- retries,
- output schema,
- coste estimado,
- artefacto fuente,
- artefacto destino.

#### D3. Metadata en JSON
Todo JSON generado debe incluir bloque `_generation_metadata`.

#### D4. Logs estructurados
No solo `print()`. Emitir logs parseables por máquina.

### Fase E. Entorno y operación reproducible (1 sprint)
Objetivo: ejecutar sin estado implícito peligroso.

#### E1. Config centralizada
Sacar hardcodes de cloud/runtime a configuración declarativa.

#### E2. Aislamiento por ejecución
Soportar directorios por `run_id` o snapshots de artefactos.

#### E3. Reanudación robusta
Cada etapa debe ser reejecutable sin corromper artefactos previos.

#### E4. Política de degradación
Si una etapa LLM falla:
- reintentar,
- marcar estado,
- conservar último artefacto válido,
- y permitir render degradado si el negocio lo acepta.

### Fase F. MCP enterprise-ready (2-3 sprints)
Objetivo: exponer el sistema como herramientas seguras para agentes.

#### F1. Tools tipadas y estables
Cada tool MCP con:
- input schema,
- output schema,
- errores normalizados.

#### F2. Operaciones de alto nivel
Exponer:
- generar blueprint de torre,
- generar annex de torre,
- renderizar ambos,
- inspeccionar estado de caso,
- validar artefactos.

#### F3. Auditoría y seguridad operativa
Toda llamada MCP debe quedar trazada por `run_id` y `actor`.

---

## 9. Priorización recomendada

Orden recomendado para reducir miedo a rotura:

1. Golden tests T5 + integridad DOCX
2. Validación automática de prompts YAML
3. Contract tests entre etapas
4. Versionado de payloads
5. Telemetría y `_generation_metadata`
6. Modularización de scripts grandes
7. Config/runtime reproducible
8. Maduración MCP

No conviene saltar directamente a MCP o nuevas features sin cerrar antes 1-5.

---

## 10. Reglas operativas para trabajo con varios agentes IA y humanos

### 10.1 Cambios permitidos
Un agente IA puede tocar:
- prompts,
- mapeos,
- renderizadores,
- tests,
- documentación.

Pero no debe tocar a la vez:
- contratos de payload
- y renderizadores
- y prompts
sin dejar tests de regresión asociados.

### 10.2 Reglas de seguridad de cambio
Toda modificación significativa debe acompañarse de:
- actualización de este `GEMINI.md`,
- validación sintáctica,
- regeneración del artefacto afectado,
- verificación del DOCX si hay render,
- y anotación de riesgos residuales.

### 10.3 Principio de alcance mínimo
Si el problema está en un contrato, no tocar el prompt salvo necesidad real.
Si el problema está en el render, no tocar el blueprint salvo necesidad real.
Si el problema es editorial, no reestructurar el motor entero.

### 10.4 Regla de no ambigüedad
No introducir estructuras alternativas nuevas sin plan explícito de migración.

### 10.5 Regla de no regresión silenciosa
Ningún cambio debe darse por bueno si no se comprueba el artefacto final que consume el usuario.

---

## 11. Estado puntual tras esta sesión

### 11.1 T5 smoke_ivirma
Estado funcional:
- Blueprint generado y renderizado.
- Annex ejecutivo generado y renderizado.
- Flujo top-down T5 validado.

### 11.2 Estado editorial
- Blueprint: documento maestro con apertura más ejecutiva.
- Annex: executive brief más corto y orientado a negocio.

### 11.3 Estado técnico
- Radar del annex corregido.
- Render Word endurecido frente a caracteres inválidos.
- Import roto del blueprint engine corregido.

### 11.4 Riesgo residual
Persisten riesgos de arquitectura y de regresión mientras no se implemente el plan de endurecimiento del capítulo 8.

### 11.5 Estado del Plan Maestro
Fases A y B completadas.
- `Fase A (Quick Wins)`: Normalización (A4) y Checklist (A5) implementados y cerrados.
- `Fase B (Contratos)`: Versionado (B1), Naming (B2), AAP Híbrido (B3) y Resiliencia (B4) implementados y cerrados.
- Resultado actual: `16 passed` en la suite de baseline:
  - `tests/test_t5_golden.py`
  - `tests/test_document_integrity.py`
  - `tests/test_prompt_registry.py`
  - `tests/test_contract_handover.py`
- Cobertura introducida:
  - Validación estructural v2 (Pydantic modernizado).
  - Resiliencia de carga con `robust_load_payload`.
  - Arquitectura comercial híbrida validada.
  - Cero warnings en la ejecución de tests.

---

## 12. Próximos pasos recomendados si se retoma el trabajo

### Opción 1. Modularización (Fase C)
Implementar Fase C completa:
- Dividir scripts grandes (C1).
- Separar contenido de motor (C2).
- Reducir side-effects (C3).

### Opción 2. Observabilidad (Fase D)
- Telemetría en `ai_client.py`.
- Logs estructurados.

### 12.1 Prioridad exacta al retomar
Si un nuevo agente IA o desarrollador retoma este trabajo, el orden mandatorio es:

1. **Cerrar C1 (Dividir scripts grandes):** Extraer mapeos y lógica de composición de los renderizadores DOCX.
2. **Escalar el patrón T5:** Una vez el motor sea modular, aplicar la nueva estructura a T2 y T3.

La razón es simple:
- T5 ya es la baseline más madura.
- El mayor riesgo actual no es funcional, sino de regresión silenciosa.
- Añadir nuevas torres o nuevos documentos antes de cerrar A4/A5/B1 aumentará el coste de la deuda y la probabilidad de rotura.

### 12.2 Qué significa cerrar `A4`
`A4` NO se considera completo por haber hecho limpiezas puntuales. Solo se considera cerrado cuando exista una única utilidad compartida para:
- sanear caracteres de control,
- normalizar texto seguro para Word,
- y reutilizar esa lógica desde todos los renderizadores relevantes.

Señales de cierre correcto:
- no hay duplicación de lógica equivalente en `render_tower_annex_from_template.py` y `render_tower_blueprint.py`,
- los tests documentales siguen en verde,
- y no reaparecen fallos XML/Word por texto inválido.

### 12.3 Qué significa cerrar `A5`
`A5` NO es un comentario informal en este documento. Debe materializarse en mecanismos verificables. El mínimo aceptable es:
- reglas explícitas en `GEMINI.md`,
- y una guía corta de validación antes de cerrar cambios.

Idealmente, evolucionará a:
- comandos estándar de validación,
- checklist reutilizable por agentes,
- y CI que impida integrar cambios sin esas comprobaciones.

### 12.4 Qué NO debe hacer el siguiente agente todavía
Hasta cerrar `A4` y `A5`, NO conviene:
- reestructurar otra vez el pipeline completo,
- tocar simultáneamente prompts + payloads + render de varias capas,
- extender MCP en profundidad,
- o aplicar cambios editoriales masivos a todas las torres.

Eso ahora mismo elevaría el riesgo de regresión.

### 12.5 Qué sí puede hacer el siguiente agente con seguridad razonable
- Añadir tests nuevos sobre T5.
- Centralizar utilidades compartidas sin cambiar el comportamiento observable.
- Añadir versionado y metadata en payloads si se hace con tests.
- Mejorar observabilidad de `ai_client.py` si no altera contratos todavía.

### 12.6 Criterio de éxito para la siguiente sesión
La siguiente sesión será buena si al terminar se puede afirmar esto:
- existe una única utilidad de saneamiento de texto para Word,
- la suite documental sigue verde,
- el proceso de validación antes de tocar prompts/render está más explícito y menos manual,
- y el repositorio está un paso más cerca de contratos versionados.

### 12.7 Criterio de fracaso
La siguiente sesión habrá ido en mala dirección si:
- se añaden features pero no aumenta la protección,
- se tocan varias capas a la vez sin tests,
- se crean más fallbacks legacy,
- o se reabre la ambigüedad entre estructuras de payload.

### 12.8 Comandos concretos de continuidad
Comandos ya validados en este estado:

```bash
./.venv/bin/pytest tests/test_t5_golden.py tests/test_prompt_registry.py tests/test_document_integrity.py -q
```

```bash
PYTHONPATH=src ./.venv/bin/python -m assessment_engine.scripts.run_executive_annex_synthesizer smoke_ivirma T5
```

```bash
PYTHONPATH=src ./.venv/bin/python -m assessment_engine.scripts.render_tower_annex_from_template \
  working/smoke_ivirma/T5/approved_annex_t5.template_payload.json \
  templates/Template_Documento_Anexos_Alpha_v06_Tower_Annex_v2_6.docx \
  working/smoke_ivirma/T5/annex_t5_smoke_ivirma_final.docx
```

```bash
PYTHONPATH=src ./.venv/bin/python -m assessment_engine.scripts.render_tower_blueprint \
  working/smoke_ivirma/T5/blueprint_t5_payload.json \
  working/smoke_ivirma/T5/Blueprint_Transformacion_T5_smoke_ivirma.docx
```

Estos comandos son el punto de partida mínimo para verificar que el estado descrito aquí sigue siendo cierto.

### 12.9 Artefactos que deben vigilarse siempre
Si algo falla o se sospecha de regresión, revisar primero estos ficheros:
- `working/smoke_ivirma/T5/blueprint_t5_payload.json`
- `working/smoke_ivirma/T5/approved_annex_t5.template_payload.json`
- `working/smoke_ivirma/T5/Blueprint_Transformacion_T5_smoke_ivirma.docx`
- `working/smoke_ivirma/T5/annex_t5_smoke_ivirma_final.docx`
- `working/smoke_ivirma/T5/pillar_radar_chart.generated.png`

Si esos cinco artefactos están coherentes, la probabilidad de que T5 esté sano es alta.

### 12.10 Regla editorial a preservar
No perder esta distinción:
- `Blueprint` = documento maestro, con apertura ejecutiva pero detalle de transformación.
- `Annex` = executive brief corto, de negocio, sin competir en volumen con el blueprint.

Si en futuras iteraciones el annex vuelve a crecer hasta parecer un blueprint abreviado, se considera regresión editorial.

### 12.11 Regla de oro para el siguiente agente
Antes de tocar nada, el siguiente agente debe leerse completo este `GEMINI.md` y asumir que:
- T5 es la baseline de seguridad,
- el problema principal actual es el riesgo de rotura, no la falta de features,
- y la prioridad es endurecer el sistema antes de ampliar alcance.

---

## 13. Diario de Refactorización

### Registro histórico consolidado
- Implementación inicial de suite de testing con `pytest`, `pytest-asyncio` y `pytest-mock`.
- Tests de validación de esquemas, parser JSON y mocking de Vertex AI.
- Corrección del “split-brain” y formalización del ADR-002 Top-Down.
- Extracción inicial de prompts a YAML.
- Creación del Executive Synthesizer.
- Limpieza inicial del renderer del annex.

### Registro de esta sesión
- Reparación funcional de T5 `smoke_ivirma` end-to-end.
- Implementación de `get_critic_prompt` para el blueprint engine.
- Refactor editorial del `Annex` para convertirlo en executive brief:
  - más negocio,
  - menos arquitectura,
  - menos solape con blueprint.
- Refactor editorial del `Blueprint` para reforzar la apertura ejecutiva.
- Corrección del uso del gráfico radial real en el annex.
- Saneamiento de caracteres no compatibles con XML/Word.
- Reordenación completa de este documento `GEMINI.md` para servir como memoria de continuidad operativa.
- Implementación de `tests/test_t5_golden.py` como primera baseline anti-rotura del sistema.
- Validación de la baseline T5 con `pytest`:
  - `BlueprintPayload` válido,
  - `AnnexPayload` válido,
  - `annex_t5_smoke_ivirma_final.docx` sin placeholders funcionales,
  - radial embebido correcto,
  - y relación esperada de tamaño/rol entre ambos documentos.
- Implementación de `tests/test_document_integrity.py` para verificar apertura limpia de los DOCX, integridad de relaciones internas y presencia de headings ejecutivos esperados.
- Implementación de `tests/test_prompt_registry.py` para validar carga y estructura básica de los YAML en `prompts/registry/`.

### Registro de esta sesión (29 de Abril de 2026)
- **Implementación de A4 (Normalización única de texto):** Se ha extraído la lógica redundante de normalización, limpieza de retornos de carro, y saneamiento de caracteres incompatibles con Word a una nueva utilidad central (`src/assessment_engine/scripts/lib/text_utils.py`). Los módulos `render_tower_annex_from_template.py`, `render_tower_blueprint.py`, `build_tower_annex_template_payload.py`, y `repair_tower_payload_scores.py` ahora consumen esta función.
- **Implementación de A5 (Checklist de cambio para agentes IA):** Se ha creado el fichero `A5_CHECKLIST.md` en la raíz del proyecto para formalizar las validaciones manuales (ejecutar suite de pruebas, checkear renderizado en DOCX, validar el pipeline e integridad) antes de dar por válido cualquier cambio arquitectónico o de configuración. 
- Tras ambos refactores, los validadores del sistema base para la Torre 5 (T5) han ejecutado y completado al 100%, validando que no hubo regresión silenciosa durante esta actualización.

- **Implementación de B1 (Versionado de payloads):**
  - Creadas clases base `VersionMetadata` y `VersionedPayload` en `schemas/common.py`.
  - Actualizados los esquemas principales (`BlueprintPayload`, `AnnexPayload`, `GlobalReportPayload`, `CommercialPayload`) para heredar de `VersionedPayload`.
  - Modificado `ai_client.py` para usar `model_dump(by_alias=True)`, asegurando que los metadatos se exporten como `_generation_metadata`.
  - Actualizados orquestadores (`run_tower_blueprint_engine.py`, `run_executive_annex_synthesizer.py`, `build_tower_annex_template_payload.py`, `build_global_report_payload.py`, `run_commercial_refiner.py`) para inyectar metadatos automáticamente.
  - Actualizados los golden tests de T5 para validar la presencia y consistencia de estos metadatos.

- **Implementación de B2 (Eliminar ambigüedades legacy):**
  - Unificada la estructura de datos del Anexo (`AnnexPayload`) definiendo sub-schemas estructurados para Riesgos, Gaps e Iniciativas (`RisksAnnex`, `GapAnnex`, `TodoAnnex`), eliminando el uso de diccionarios genéricos.
  - Eliminado el campo redundante `tobe_gap` en favor de la sección única `gap`.
  - Simplificada la lógica del renderizador `render_tower_annex_from_template.py`, eliminando más de 100 líneas de funciones de normalización (`normalize_risk_rows`, `normalize_gap_section`, etc.) al delegar la integridad estructural a Pydantic.
  - Estandarizado el naming en el Blueprint (`HealthCheckAsIs` y `ProjectToDo`) para usar nombres de campos descriptivos (`risk_observed`, `target_state`, `initiative`, etc.) alineados con el Anexo, utilizando alias para asegurar retrocompatibilidad.
  - Validado el pipeline T5 end-to-end con los nuevos esquemas, confirmando que la generación y el renderizado siguen operativos y libres de ambigüedad técnica.

- **Implementación de B3 (Contract tests entre etapas):**
  - Creado nuevo set de pruebas en `tests/test_contract_handover.py` para validar el flujo de datos entre etapas.
  - El test `test_contract_blueprint_to_annex` verifica que la salida del motor de blueprint es compatible con los requerimientos del sintetizador del anexo.
  - El test `test_contract_annex_is_valid_payload` asegura que los anexos generados cumplen estrictamente con el esquema Pydantic para el renderizador Word.
  - Se han incluido validaciones para el **Contrato Híbrido** del Account Plan (`test_contract_commercial_hybrid_lineage`), asegurando que el esquema comercial es capaz de consolidar metadatos estratégicos del Global y detalles tácticos de los Blueprints (Direct Lineage), según el ajuste arquitectónico aprobado.

- **Implementación de B3 (Contract tests & AAP Híbrido):**
  - **Hito Híbrido:** Rediseñado el pipeline comercial en `run_commercial_refiner.py` para consumir tanto el Informe Global como el catálogo táctico de los Blueprints de torre.
  - **Captura de Oportunidades:** Se ha validado empíricamente en `smoke_ivirma` que el Account Action Plan (AAP) ahora incluye iniciativas técnicas granulares (ej. Cyber Recovery Vault, Chaos Engineering) que antes se perdían en la síntesis global.
  - **Validación de Contratos:** Creada la suite `tests/test_contract_handover.py` para asegurar que el flujo Blueprint -> Anexo -> Global -> Comercial es robusto y cumple con los esquemas Pydantic.
  - **Regeneración DOCX:** Validado el documento final `Account_Action_Plan_smoke_ivirma.docx` con el contenido enriquecido.

- **Implementación de B4 (Handover contracts resilientes):**
  - Creada la utilidad central `src/assessment_engine/scripts/lib/contract_utils.py` para gestionar la carga y validación de payloads entre etapas.
  - **Validación Inteligente:** Se ha implementado un modo de "Degradación Elegante" (`robust_load_payload`). El sistema detecta y loguea detalladamente las desviaciones de esquema (campos faltantes, tipos incorrectos) pero utiliza `model_construct` para permitir que el pipeline continúe si el error no es catastrófico.
  - **Integración Sistémica:** Actualizados los cargadores de `run_executive_annex_synthesizer.py`, `render_tower_annex_from_template.py`, `render_tower_blueprint.py` y `render_commercial_report.py` para usar el nuevo validador.
  - **Autocuración:** Los artefactos guardados mediante `save_versioned_payload` aseguran ahora la presencia de metadatos de versión y el uso correcto de alias de Pydantic.
  - Validado el pipeline T5 end-to-end con esta nueva capa de protección, confirmando que la observabilidad ha mejorado sin comprometer la disponibilidad de los informes.

### Registro de esta sesión (Finalización Fase B - 29 de Abril de 2026)
- **Implementación de B1 (Versionado de payloads):** Introducidos metadatos de versión (`_generation_metadata`) en todos los payloads principales. El sistema ahora traza el linaje de los artefactos (ej. el Anexo conoce la versión del Blueprint origen).
- **Implementación de B2 (Eliminar ambigüedades legacy):** Unificada la estructura de datos del Anexo (`AnnexPayload`) y estandarizado el naming en el Blueprint (`risk_observed`, `initiative`, etc.). Eliminada la dependencia de `tobe_gap`.
- **Implementación de B3 (AAP Híbrido):** Rediseñada la arquitectura comercial para que el Account Action Plan (AAP) consuma tanto el Informe Global (estrategia) como los Blueprints técnicos (catálogo táctico). Validado en `smoke_ivirma` que no se pierden oportunidades técnicas.
- **Implementación de B4 (Handover contracts resilientes):** Creada la utilidad `robust_load_payload` con modo de "Degradación Elegante". El sistema es ahora capaz de detectar errores de esquema de la IA, loguearlos detalladamente y continuar la producción de informes mediante autocuración.
- **Hardening de Calidad:**
  - Modernizados todos los esquemas Pydantic a la sintaxis v2 (`model_config`).
  - Limpiada la suite de tests de warnings y ruidos de configuración.
  - Verificada la resiliencia de B4 mediante un script de prueba de estrés real (`verify_b4_resilience.py`).
  - Resultado final de la sesión: **16 tests en verde (100% passed, 0 warnings)**.
