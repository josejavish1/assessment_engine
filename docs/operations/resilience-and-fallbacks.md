---
path: docs/operations/resilience-and-fallbacks.md
kind: document
title: Resilience Playbook and FMEA
doc_type: operational
status: Verified
owner: docs-governance
applies_to:
- humans
- ai-agents
source_of_truth:
- ../../src/assessment_engine/infrastructure/review_resilience.py
- ../../src/assessment_engine/application/tools/regenerate_smoke_artifacts.py
last_verified_against: 2026-06-26
notes: Runbook de mitigación, políticas de tolerancia a fallos y FMEA simple para la ejecución con APIs.
diataxis: how_to
verification_mode: code
---

# Resilience Playbook and FMEA (Failure Mode and Effects Analysis)

Este manual de operaciones cataloga los modos de fallo identificados al interactuar con APIs de modelos fundacionales externos (Vertex AI / Gemini) y proporciona instrucciones accionables de mitigación y políticas de conmutación por error (*failover*).

---

## 1. Análisis de Modos de Fallo (FMEA)

| Modo de Fallo | Efecto en el Sistema | Severidad | Mitigación Automatizada | Acción Operativa Humana |
|---|---|---|---|---|
| **Límites de Cuota (HTTP 429)** | El agente de recolección de evidencias se detiene en seco. | Alta | Reintento exponencial progresivo (`tenacity` con backoff exponencial, min 2s, max 30s, hasta 5 intentos). | Ajustar el límite de concurrencia `VERTEX_CONCURRENCY_LIMIT` en `ai_client.py` a un valor menor (ej. 3). |
| **Timeout de Conexión (Red/API)** | El subproceso de IA se congela o tarda indefinidamente. | Crítica | Cancelación asíncrona mediante timeout controlado (`asyncio.timeout(timeout_seconds)`). Lanzamiento de `VertexQueryTimeoutError`. | Habilitar el flag `--local-only` en el comando de ejecución para realizar una compilación puramente determinista sin llamadas externas. |
| **Respuesta del Modelo Truncada** | El payload JSON final del agente no es válido sintácticamente. | Alta | Captura y auto-reparación sintáctica mediante `parse_json_from_text`. Intento de cierre de llaves rotas. | Ejecutar la herramienta operativa `repair_tower_payload_scores.py` para regenerar y corregir estructuralmente las puntuaciones en el JSON local. |

---

## 2. Estrategias de Degradación Elegante (*Failover Policies*)

El motor cuenta con planes de contingencia para mantener la operatividad incluso ante caídas completas del servicio de la API externa:

### 2.1 Conmutación a Ejecución Local-Only
Si el servicio de red está completamente caído o el cliente opera en una red altamente restringida sin acceso a internet (*air-gapped*), el motor permite compilar el reporte basándose en las plantillas y los hallazgos ya recolectados de forma determinista.

*   **Comando de Emergencia:**
    ```bash
    python src/assessment_engine/application/tools/regenerate_smoke_artifacts.py --local-only
    ```
*   **Comportamiento:** El motor desactiva la fase de pre-vuelo de Vertex AI y utiliza el caché de hallazgos almacenados de forma segura en `templates/` o payloads locales en lugar de realizar consultas dinámicas al LLM.

### 2.2 Conmutación a Modo Dry-Run (Prueba de Humo en Seco)
Para probar la consistencia del pipeline sin consumir tokens de la API de Vertex AI, el motor ofrece un modo de simulación rápida.

*   **Comando de Simulación:**
    ```bash
    python src/assessment_engine/application/tools/regenerate_smoke_artifacts.py --dry-run
    ```
*   **Comportamiento:** Se omiten todas las llamadas costosas de generación de texto del modelo y se devuelven estructuras sintácticamente perfectas vacías para validar que el pipeline de compilación no tenga roturas lógicas.

---

## 3. Resolución de Problemas en Producción

### Escenario A: Excepciones de Autenticación de Google Cloud
*   **Error Común:** `GoogleDefaultCredentialsError` / `PermissionDenied`.
*   **Solución:** 
    1.  Verificar que las credenciales de la cuenta de servicio local estén activas:
        ```bash
        gcloud auth application-default login
        ```
    2.  Si la red corporativa bloquea el acceso de red directo de Google, conmutar la ejecución a `--local-only`.

### Escenario B: Bloqueo de Merge en CI por Desajuste Semántico
*   **Error Común:** El validador AI Semantic Drift falla arrojando un reporte con estado de alarma.
*   **Solución:**
    1.  Leer el informe generado en `.artifacts/docs/semantic_drift_report.md`.
    2.  Aplicar las sugerencias de cambios en los documentos Markdown correspondientes para alinearlos con la nueva lógica implementada en las clases de Python.
    3.  Confirmar y empujar los cambios para re-ejecutar el pipeline de CI.
