---
status: Verified
owner: docs-governance
source_of_truth:
- ../../src/assessment_engine/infrastructure/agentic_benchmarker.py
- ../../src/assessment_engine/domain/schemas/rubric.py
- ../../engine_config/frameworks/
- ../../tests/test_agentic_benchmarker.py
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: code
---
# RAGE (Runtime Agentic Grounding & Evaluation) Architecture

Este documento detalla la especificación técnica de la arquitectura de evaluación de precisión **RAGE (Runtime Agentic Grounding & Evaluation)** implementada en el motor.

Su objetivo de diseño es erradicar de raíz el "vibe-scoring" (puntuación probabilística o estimaciones sesgadas de los modelos de lenguaje) sustituyéndolo por un **flujo de auditoría determinista, basado en evidencias físicas en tiempo real y gobernado por reglas matemáticas puras en Python**.

---

## 1. El Flujo de Ejecución RAGE (Paso a Paso)

El motor opera de forma asíncrona y está estructurado en cuatro fases robustas e independientes:

```
===================================================================================================
| 1. OSINT SEARCH (Investigador) ➔ 2. EVIDENCE VAULT (Failsafe) ➔ 3. CROSS-EXAM (Forense) ➔ 4. SCORING |
===================================================================================================
|                                                                                                 |
|   1. Búsqueda en Vivo (Google Search):                                                          |
|      - El Agente Investigador formula consultas estructuradas basadas en las rúbricas JSON       |
|        (ej. "ENS categoría alta requisitos oficiales BOE") según país/sector del cliente.        |
|                                                                                                 |
|   2. Descarga y Almacenamiento Seguro (EvidenceSnapshotter):                                    |
|      - Las evidencias oficiales localizadas (PDFs, HTMLs del gobierno) se descargan físicamente  |
|        en local bajo `working/{client}/evidence_cache/` para evitar el "Link-Rot".              |
|                                                                                                 |
|   3. Juicio de No Alucinación (Cross-Examination):                                               |
|      - Un Agente Forense lee de forma aislada el texto extraído del PDF local de la bóveda      |
|        y verifica si el hallazgo reportado por el investigador es 100% verídico y exacto.        |
|                                                                                                 |
|   4. Evaluación Matemática Determinista (Python Puro):                                          |
|      - El motor de Python lee la regla matemática del JSON (ej: `score >= 60.0`) y calcula el    |
|        score final de madurez de forma exacta sin intervención de la IA, guardando el estado     |
|        en `benchmarks_snapshot.json`.                                                            |
|                                                                                                 |
`-------------------------------------------------------------------------------------------------'
```

---

## 2. Componentes Críticos del Sistema

La arquitectura RAGE está desacoplada en tres capas lógicas bajo el patrón hexagonal:

### A. Capa de Dominio (Esquemas Pydantic Estrictos)
*   **Fichero:** `src/assessment_engine/domain/schemas/rubric.py`
*   **Rol:** Define las clases de datos que estructuran las rúbricas matemáticas:
    *   `FrameworkRubric`: El contenedor raíz de la norma regulatoria (ej: DORA, ENS, DAMA).
    *   `RubricRule`: Las reglas de evaluación, incluyendo umbrales numéricos de aprobación (`ThresholdMapping`).
    *   `RageBenchmarkSnapshot`: El estado final e inmutable de la evaluación de todas las torres, con URL de origen, rastro de evidencia local y estado de validación forense.

### B. Capa de Infraestructura (Ejecutor Asíncrono)
*   **Fichero:** `src/assessment_engine/infrastructure/agentic_benchmarker.py`
*   **Rol:** El motor core asíncrono (`AgenticRageBenchmarker`):
    *   Gestiona las llamadas asíncronas a Vertex AI para los agentes de investigación y forense.
    *   Utiliza `EvidenceSnapshotter` para descargar y persistir de forma aséptica las evidencias en tu disco duro local.
    *   Lanza la evaluación cruzada (*Cross-Examination*) y aplica la lógica matemática de umbrales en Python puro.

### C. Capa Declarativa (Rúbricas JSON)
*   **Ficheros:** `engine_config/frameworks/{ens_alta, google_dora, dama_dmbok}.json`
*   **Rol:** Definiciones puramente declarativas que aíslan la lógica regulatoria del código de Python. Permite añadir nuevos estándares o ajustar umbrales numéricos sin modificar una sola línea de código fuente.

---

## 3. Mitigación de Riesgos y Resiliencia (Failsafe Layers)

La arquitectura incorpora tres capas de tolerancia a fallos extremas para asegurar el delivery comercial continuo:

1.  **Caché de Evidencias Local:** Si el sitio web oficial de la norma (ej: FNMT Ceres) se cae en tiempo de ejecución, el motor lee el archivo pre-descargado de la carpeta `evidence_cache/` para garantizar la resiliencia offline.
2.  **Límite de Presupuesto (FinOps Circuit Breaker):** Integrado nativamente con `ApexSentinel`. Si las llamadas de búsqueda o validación de los agentes superan el umbral en USD configurado, el motor detiene la ejecución de forma segura antes de incurrir en costos elevados de API.
3.  **Mecanismo de Caída Seguro (Graceful Fallback):** Si un agente de búsqueda no puede conectarse a internet o el servicio de OSINT falla por completo, el motor activa la rúbrica de reserva (`fallback`), elevando un aviso de advertencia (`Needs Review`) y permitiendo que el pipeline de generación del Word continúe sin bloquearse.
