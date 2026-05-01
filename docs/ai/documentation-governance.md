---
status: Verified
owner: docs-governance
source_of_truth:
  - src/assessment_engine/
  - tests/
  - pyproject.toml
  - .github/workflows/ci.yml
  - docs/documentation-map.yaml
last_verified_against: 2026-04-30
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Política de gobernanza documental

Esta política define cómo se lee, verifica y actualiza la documentación de `assessment-engine`. Es la **política central neutral** del proyecto para humanos y para cualquier IA que trabaje en el repo.

## Objetivo

Mantener una documentación única, auditable y reutilizable, sin duplicar la verdad entre humanos, Gemini, ChatGPT, Copilot u otros agentes.

## Principios

1. **Una sola base documental.** No existen dos documentaciones paralelas, una para humanos y otra para IAs.
2. **El repo ejecutable manda.** Código, tests, workflows, schemas y configuración real prevalecen sobre cualquier narrativa.
3. **Los adaptadores por agente no redefinen la verdad.** `GEMINI.md`, `AGENTS.md`, `CHATGPT.md` o `.github/copilot-instructions.md` solo explican cómo consumir y actualizar la base común.
4. **Sin invenciones.** Si algo no puede verificarse, debe marcarse como duda o `Needs Review`.
5. **Trazabilidad obligatoria.** Todo cambio relevante debe tener una ruta documental obvia.

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
```

## Reglas de actualización

Actualiza o reverifica documentación cuando cambie cualquiera de estas áreas:

| Cambio en el repo | Revisión documental mínima |
|---|---|
| `src/assessment_engine/scripts/**`, `src/assessment_engine/mcp_server.py` | arquitectura y operación |
| `src/assessment_engine/schemas/**` | contratos y docs de payloads |
| `.github/workflows/**` | operación y CI |
| `pyproject.toml`, `requirements.txt`, `pytest.ini` | onboarding, instalación y validación |
| prompts o configuración de motor | operación y referencia técnica |

## Enforcement en GitHub

La gobernanza documental ya cuenta con tres guardarraíles explícitos en el repo:

- `.github/pull_request_template.md` para recordar el impacto documental en cada PR;
- `.github/CODEOWNERS` para ownership mínimo de la capa canónica y de la gobernanza;
- `.github/workflows/docs-governance.yml` para validar `docs/documentation-map.yaml`, la metadata documental básica y la trazabilidad declarada por reglas.

Además, el validador ya admite **source-linked review** para documentos concretos: cuando un documento declara revisión estricta frente a ciertos ficheros fuente, un cambio en esos ficheros debe venir acompañado por la revisión de **ese documento canónico** o de una ruta documental permitida explícitamente.

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
