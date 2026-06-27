---
status: Verified
owner: docs-governance
source_of_truth:
- ../../src/assessment_engine/domain/
- ../../tests/
- ../../pyproject.toml
- ../../.github/workflows/ci.yml
- ../../docs/documentation-map.yaml
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
---
# Política de gobernanza documental

Esta política define cómo se lee, verifica y actualiza la documentación de `assessment-engine`. Es la **política central neutral** del proyecto para humanos y para cualquier IA que trabaje en el repo.

## Objetivo

Mantener una documentación única, auditable y reusable, evitando la duplicidad de fuentes de verdad entre operarios humanos y agentes de inteligencia artificial (Gemini, ChatGPT, Copilot, etc.).

## Principios

1. **Base documental unificada:** No existen bases de conocimiento paralelas. Humanos y agentes consumen y mantienen exactamente el mismo corpus técnico.
2. **Supremacía del repositorio ejecutable:** El código fuente, las suites de pruebas, las automatizaciones de CI/CD, los esquemas de validación y la configuración física constituyen la única fuente de verdad definitiva y prevalecen sobre cualquier descripción prosa.
3. **Inmutabilidad por adaptadores:** Los archivos específicos por agente (`GEMINI.md`, `AGENTS.md`, `CHATGPT.md`, `.github/copilot-instructions.md`) actúan únicamente como adaptadores operativos de contexto. No redefinen, extienden ni modifican las especificaciones declaradas en la documentación canónica.
4. **Verificación empírica rigurosa:** Queda estrictamente prohibida la asunción de capacidades no implementadas. Cualquier componente o flujo cuya coincidencia empírica no pueda certificarse debe clasificarse de inmediato como `Needs Review` o `Draft`.
5. **Trazabilidad determinista:** Cualquier cambio estructural o de comportamiento en el sistema debe verse reflejado de forma explícita en su correspondiente ruta de documentación técnica.

## Tipos documentales oficiales

| Tipo | Uso |
|---|---|
| `canonical` | Arquitectura, operación, contratos, onboarding y políticas oficiales |
| `operational` | Instrucciones de trabajo y mantenimiento |
| `reference_generated` | Inventarios o referencias derivadas del código o de artefactos |
| `archived` | Material histórico que no debe crecer |

## Estados documentales oficiales

| Estado | Significado |
|---|---|
| `Verified` | Verificado contra la realidad actual del repo |
| `Needs Review` | Útil, pero aún no verificado o con posibles derivas |
| `Draft` | Base inicial válida, todavía incompleta |
| `Deprecated` | Ya no debe crecer; existe reemplazo o migración definida |

## Metadata obligatoria

Todo documento crítico nuevo o reescrito debe declarar como mínimo:

```yaml
status: Draft|Verified|Needs Review|Deprecated
owner: logical-owner
source_of_truth:
  - path/or/source
last_verified_against: YYYY-MM-DD
applies_to:
  - humans
  - ai-agents
doc_type: canonical|operational|reference_generated|archived
diataxis: tutorial|how_to|reference|explanation
verification_mode: schema|code|workflow|observed_run|editorial|mixed
```

## Reglas de actualización

Actualiza o reverifica documentación cuando cambie cualquiera de estas áreas:

| Cambio en el repo | Revisión documental mínima |
|---|---|
| `src/assessment_engine/application/**`, `src/assessment_engine/mcp_server.py` | arquitectura y operación |
| `src/assessment_engine/domain/schemas/**` | contratos y docs de payloads |
| `.github/workflows/**` | operación y CI |
| `pyproject.toml`, `requirements.txt` | onboarding, instalación y validación |
| prompts o configuración de motor | operación y referencia técnica |

## Enforcement en GitHub

La gobernanza documental ya cuenta con tres guardarraíles explícitos en el repo:

- `.github/pull_request_template.md` para recordar el impacto documental en cada PR;
- `.github/CODEOWNERS` para ownership mínimo de la capa canónica y de la gobernanza;
- `.github/workflows/docs-governance.yml` para validar `docs/documentation-map.yaml`, la metadata documental básica y la trazabilidad declarada por reglas.

Además, el validador ya admite **source-linked review** para documentos concretos: cuando un documento declara revisión estricta frente a ciertos ficheros fuente, un cambio en esos ficheros debe venir acompañado por la revisión de **ese documento canónico** o de una ruta documental permitida explícitamente.

El validador también debe bloquear al menos estas derivas mecánicas:

- una entrada del `documentation-map` cuyo `status`, `doc_type` u `owner` ya no coincidan con el front matter real del archivo;
- una entrada del `documentation-map` cuyo `diataxis` o `verification_mode` ya no coincidan con el front matter real del archivo;
- documentos bajo `docs/strategy/` marcados como `Verified`;
- documentos bajo `docs/reference/generated/` clasificados como `canonical` u `operational`;
- adaptadores por agente clasificados fuera de `operational`;
- anchors Markdown rotos, imágenes locales inexistentes y enlaces externos inválidos cuando la comprobación de red esté activada;
- documentos `Verified` cuya fecha de reverificación haya caducado según el umbral de frescura declarado en `documentation-map.yaml`;
- snippets de shell que apunten a módulos Python o rutas del repo que ya no existen;
- documentos `Verified` con lenguaje aspiracional o hype impropio de una capa canónica.

## Taxonomía operativa

La gobernanza no distingue solo por `doc_type` y `status`. También clasifica cada pieza por:

- `diataxis`: forma principal del documento (`tutorial`, `how_to`, `reference`, `explanation`);
- `verification_mode`: cómo se mantiene alineado (`schema`, `code`, `workflow`, `observed_run`, `editorial`, `mixed`).

Esto permite endurecer reglas distintas para contratos, runbooks, arquitectura, material derivado y adaptadores por agente.

## Cobertura y observabilidad

`docs/documentation-map.yaml` debe declarar:

- `coverage.include` y `coverage.exclude` para definir el corpus gobernado;
- `freshness.verified_max_age_days` para limitar cuánto tiempo puede vivir un `Verified` sin reverificación explícitamente.

La pipeline documental debe producir al menos estos artefactos:

- un `health report` máquina-legible con conteos, piezas stale y documentos cubiertos solo por colecciones;
- una previsualización HTML ligera del corpus gobernado;
- validación de snippets y lint editorial de la capa `Verified`.

## Cómo deben trabajar los agentes de IA

1. Leer primero `README.md`, `docs/README.md` y este documento.
2. Buscar la fuente de verdad antes de redactar.
3. No introducir verdad nueva en archivos adaptadores por agente.
4. Marcar explícitamente cualquier duda o hueco de verificación.
5. Actualizar `docs/documentation-map.yaml` cuando cambie el estado o el destino de un documento.

## Source-linked review estricto

Cuando una entrada del `documentation-map` declare alguna de estas claves:

- `enforce_on_source_changes: true`
- `review_when_source_changes: [...]`
- `review_paths_on_source_change: [...]`

la revisión documental deja de ser genérica y pasa a ser **dirigida**:

1. si cambia uno de los ficheros fuente declarados;
2. debe cambiar también el documento canónico indicado o una de las rutas documentales permitidas;
3. tocar una carpeta `docs/` no relacionada ya no es suficiente.

Esta capa está pensada para las piezas donde la deriva documental es más peligrosa: arquitectura principal, contratos, operación y gobernanza.

En la práctica, esto también aplica a refactors internos que no cambian la funcionalidad visible pero sí la forma en que el sistema resuelve entorno, rutas o artefactos operativos. Si un cambio mueve esa lógica a helpers compartidos como `pipeline_runtime.py` o `runtime_paths.py`, la revisión documental sigue siendo obligatoria porque cambia la superficie real que sostienen los playbooks, la arquitectura operativa y las reglas de trazabilidad.

## Tratamiento del material heredado

- `GEMINI.md` se mantiene como adaptador operativo en transición.
- `AGENTS.md`, `CHATGPT.md` y `.github/copilot-instructions.md` son adaptadores breves y no deben acumular documentación canónica.
- `docs/reference/generated/legacy-gemini/` es el archivo neutral de la antigua documentación de Gemini y ya no forma parte de la capa estratégica.
- Los documentos heredados pueden seguir siendo útiles, pero deben quedar clasificados como `Needs Review` o `Deprecated` hasta su realineación.
