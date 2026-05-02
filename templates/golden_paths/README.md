# Golden Paths: Índice de Plantillas

Este archivo actúa como un índice ("scaffolding registry") para que los agentes de IA sepan exactamente qué plantilla utilizar en cada situación, reduciendo la ambigüedad y el riesgo de alucinaciones arquitectónicas.

## Catálogo de Plantillas

| Propósito | Plantilla a utilizar | Cuándo usarla |
| :--- | :--- | :--- |
| **Aplicación FastAPI (Main)** | `fastapi_app.py.tpl` | Cuando se crea el entrypoint de un nuevo servicio web. Inicializa el logger JSON. |
| **Endpoint REST (API)** | `fastapi_endpoint.py.tpl` | Cuando la tarea requiere exponer funcionalidad vía HTTP. Incluye Pydantic schemas y manejo estándar de HTTPException. |
| **Worker / Job Asíncrono** | `async_worker.py.tpl` | Cuando la tarea requiere procesamiento en segundo plano, colas de mensajes o tareas cron programadas. |
| **Tests Unitarios / Integración** | `pytest_test.py.tpl` | Cuando se requiere añadir nueva cobertura de código. Fuerza el patrón Arrange-Act-Assert. |

## Instrucciones de uso para Agentes

1. Selecciona la plantilla adecuada del catálogo superior.
2. Lee el contenido de la plantilla para entender los bloques estructurales.
3. Crea el nuevo archivo en la ubicación correspondiente del repositorio (`src/...` o `tests/...`).
4. Copia el contenido de la plantilla y modifica **únicamente** la sección delimitada por `# --- START OF BUSINESS LOGIC ---`.
5. Si necesitas crear un archivo que no encaja en ninguna de estas categorías (ej. un `enums.py`, un `constants.py` o un modelo puramente de datos sin lógica), debes añadir el pragma `# golden-path: ignore` en la cabecera del archivo.