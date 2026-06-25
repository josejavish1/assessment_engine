# 🔄 Estrategia de Migración de Código: El Trasplante de Sistema Nervioso (Patrón Strangler Fig)

Este documento detalla **cómo** se llevará a cabo la transición del código actual (`assessment_engine`) al nuevo framework (`ntt_sovereign_engine`), garantizando la **preservación total del valor de negocio y la propiedad intelectual ya desarrollada**, sin reescrituras innecesarias.

## 1. El Principio Fundamental: Preservación de Valor
El objetivo del proyecto NO es reescribir la inteligencia del *Fast Assessment Tool*. El objetivo es **sustituir el sistema de control (el orquestador)** que actualmente es monolítico y frágil, por un motor resiliente basado en Grafos de Estado.

*   **Lo que cambia:** Cómo se coordinan las tareas, cómo se manejan los errores de red, cómo se limitan los tokens y dónde se ejecuta el código (Sandboxing).
*   **Lo que se conserva:** Cómo se evalúa el código de un cliente, qué criterios metodológicos aplican y cómo se dibujan los informes.

## 2. Mapeo de Activos: El Destino del Código Existente

La migración se basa en el principio de "encapsulación". El código actual pasará a ser la "Carga Útil" que transporta el nuevo motor.

| Componente Actual | Estado Futuro | Acción Técnica de Migración |
| :--- | :--- | :--- |
| **`engine_config/`** (Prompts, pesos metodológicos, reglas) | **Se conserva al 100%** | El nuevo motor `NttAgent` cargará estos archivos sin modificarlos. Actúan como el "Cerebro" externo del agente. |
| **Modelos `lib/`** (Pydantic schemas: `TowerBlueprint`, `Finding`) | **Se conserva al 100%** | Se convertirán en la definición estricta del "Estado de Memoria" (`State`) en LangGraph. Toda la validación estructural heredada sigue activa. |
| **Lógica Analítica Pura** (`run_scoring.py`, `client_intelligence.py`) | **Se conserva al 100%** | Se envolverán como "Tools" o Nodos deterministas en el grafo de LangGraph. El orquestador simplemente llamará a estas funciones importándolas. |
| **Renderizadores Documentales** (`docx_render_utils.py`, `render_tower_blueprint.py`) | **Se conservan al 100%** | Se mantienen como scripts independientes que el orquestador invocará en el nodo final del grafo, pasándoles el JSON final ya validado. |
| **Orquestadores Monolíticos** (`run_product_owner_orchestrator.py`, `run_tower_pipeline.py`) | **Se eliminan progresivamente** | Sus bucles `while`, gestión manual de reintentos y lógica de red son sustituidos por la orquestación nativa de LangGraph y las clases base del SDK. |

## 3. Plan de Ejecución: Patrón Strangler Fig

Para mitigar el riesgo operativo ("no romper lo que funciona"), la migración será iterativa, permitiendo que ambas versiones convivan durante la transición.

*   **Paso 1: Convivencia Pacífica.** El nuevo paquete `ntt_sovereign_engine` se construye en paralelo. El sistema actual sigue sirviendo evaluaciones en producción sin ser modificado.
*   **Paso 2: Migración del Componente Más Pequeño.** Se selecciona un único paso lógico (ej. la síntesis de hallazgos de una torre). Se crea un Grafo en LangGraph exclusivo para esa tarea, inyectando los *prompts* y modelos Pydantic existentes.
*   **Paso 3: Test A/B de Rendimiento.** Se ejecuta el mismo input de cliente en el script antiguo y en el nuevo micro-grafo. Si el resultado es estructural y semánticamente idéntico, la migración de ese componente es un éxito.
*   **Paso 4: Estrangulamiento.** El pipeline principal (`run_global_pipeline.py`) se modifica para delegar ese paso concreto al nuevo motor, mientras sigue ejecutando el resto a la manera antigua.
*   **Paso 5: Muerte del Monolito.** Se repite el proceso iterativamente hasta que el script orquestador original queda vacío, habiendo delegado toda su carga a los grafos del *Sovereign Engine*. En ese momento, se archiva.
