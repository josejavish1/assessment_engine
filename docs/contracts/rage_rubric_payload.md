---
status: Verified
owner: docs-governance
source_of_truth:
- ../../src/assessment_engine/domain/schemas/rubric.py
- ../../engine_config/frameworks/
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: schema
---
# RAGE Framework Rubric JSON Contract

Este documento establece la especificación técnica del contrato de datos JSON para las rúbricas declarativas del motor **RAGE (Runtime Agentic Grounding & Evaluation)**.

Cualquier archivo de norma regulatoria inyectado bajo `engine_config/frameworks/` (ej. `ens_alta.json`, `google_dora.json`, `dama_dmbok.json`) debe cumplir de forma matemática y estricta con esta estructura de interfaz, la cual es validada en el preflight por la clase Pydantic `FrameworkRubric`.

---

## 1. Estructura Jerárquica del JSON

El payload de la rúbrica está estructurado en tres niveles de datos:

```
===================================================================================================
| FRAMEWORK_RUBRIC (Raíz) ➔ 1. METADATA (framework, version) ➔ 2. RULES (List of RubricRule)     |
===================================================================================================
|                                                                                                 |
|   Desglose del Objeto RubricRule:                                                               |
|   - `rule_id`: Código táctico único (ej: "ENS.T6.1").                                            |
|   - `name`: Nombre formal del control.                                                          |
|   - `criteria_prompt`: Directriz semántica para el Agente Investigador.                        |
|   - `thresholds`: Regla condicional numérica de umbrales (ThresholdMapping).                    |
|   - `fallback`: Puntuación de reserva por defecto ante fallos de OSINT.                         |
|                                                                                                 |
`-------------------------------------------------------------------------------------------------'
```

---

## 2. Especificación Detallada de Campos

### A. Objeto Raíz (`FrameworkRubric`)

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :---: | :--- |
| `framework` | `str` | **SÍ** | Nombre canónico de la norma reguladora (ej: "ENS Alta", "Google DORA"). |
| `version` | `str` | **SÍ** | Versión de la rúbrica (ej: "v1.0", "v2.0"). |
| `rules` | `list[RubricRule]` | **SÍ** | Lista ordenada de controles y reglas de evaluación fácticas. |

---

### B. Objeto de Regla (`RubricRule`)

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :---: | :--- |
| `rule_id` | `str` | **SÍ** | Identificador alfanumérico único del control (ej: "DORA.T1.P2"). |
| `name` | `str` | **SÍ** | Título descriptivo e institucional del control regulador. |
| `criteria_prompt` | `str` | **SÍ** | Prompt técnico especializado de extracción que utiliza el Agente Investigador RAGE para analizar la evidencia. |
| `thresholds` | `ThresholdMapping` | **SÍ** | Objeto condicional que define los límites matemáticos para asignar la nota. |
| `fallback` | `float` | **SÍ** | Puntuación de madurez (0.0 a 5.0) por defecto si la búsqueda OSINT se degrada. |

---

### C. Objeto de Umbrales (`ThresholdMapping`)

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :---: | :--- |
| `condition` | `str` | **SÍ** | Operación matemática en Python que se evaluará en caliente (ej: `value >= threshold`). |
| `values` | `dict[str, float]` | **SÍ** | Mapeo de niveles de madurez asociados a sus respectivos límites numéricos (claves: `"Level_1"`, `"Level_2"`, `"Level_3"`, `"Level_4"`, `"Level_5"`). |

---

## 3. Ejemplo de Payload Homologado y Válido

A continuación se muestra un fragmento de esquema real, aséptico y conforme con la clase de validación de Pydantic:

```json
{
  "framework": "Google DORA",
  "version": "1.0",
  "rules": [
    {
      "rule_id": "DORA.T1.P1",
      "name": "Frecuencia de Despliegue (Deployment Frequency)",
      "criteria_prompt": "Extraer la tasa de despliegue en entornos productivos reportada oficialmente. Buscar palabras clave como 'despliegues al día', 'deployments per day' o frecuencia semanal.",
      "thresholds": {
        "condition": "value >= threshold",
        "values": {
          "Level_1": 0.1,
          "Level_2": 1.0,
          "Level_3": 3.0,
          "Level_4": 10.0,
          "Level_5": 30.0
        }
      },
      "fallback": 2.5
    }
  ]
}
```
