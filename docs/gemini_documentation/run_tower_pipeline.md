# Documentación: `run_tower_pipeline.py`

## Resumen

Este script es el **orquestador principal del pipeline de análisis para una única torre tecnológica**. Actúa como el "director de orquesta" que define la secuencia de ejecución de todos los scripts necesarios para transformar los datos de entrada en crudo en los artefactos finales, incluyendo los `payloads` de datos y los documentos `.docx`. Implementa un flujo de trabajo basado en un DAG (Grafo Acíclico Dirigido) utilizando `asyncio` para gestionar tareas secuenciales y paralelas de forma eficiente.

## Componentes Principales

### `run_pipeline()`

Es la función asíncrona principal que define todo el flujo de trabajo.
-   **Parseo de Argumentos:** Acepta argumentos de línea de comandos para especificar el cliente, la torre y los ficheros de entrada. También incluye una opción `--start-from` que permite reanudar un pipeline fallido desde un paso específico.
-   **Configuración del Entorno:** Prepara un entorno de ejecución limpio, resolviendo la ruta al ejecutable de Python del entorno virtual y estableciendo variables de entorno (`PYTHONPATH`, etc.) que serán pasadas a cada subproceso.
-   **Definición del DAG de Tareas:** El cuerpo de la función es la definición explícita del pipeline, paso a paso.

### `run_step_async(...)`

Es una función de utilidad clave que ejecuta cada paso del pipeline en un **subproceso aislado**.
-   **Aislamiento:** Al usar `asyncio.create_subprocess_exec`, cada script se ejecuta como un proceso completamente nuevo. Esto es una práctica de diseño muy robusta que previene "race conditions" y evita que el estado global (como `sys.argv` o variables de entorno) de un script contamine al siguiente.
-   **Gestión de Errores:** Captura la salida estándar y el error de cada subproceso. Si un paso falla (devuelve un código de salida distinto de cero), la función lanza una excepción que detiene todo el pipeline, informando del error.
-   **Control de Flujo:** Gestiona la lógica de `SKIP_MODE` para saltar pasos hasta llegar al punto de reanudación especificado por `--start-from`.

## Flujo de Trabajo del Pipeline

El script define claramente las fases de ejecución:

1.  **Fase 1: Preparación Determinista (Secuencial):**
    -   `build_case_input`: Crea el `case_input.json` a partir de las fuentes.
    -   `build_evidence_ledger`: Crea un "libro de evidencias".
    -   `run_scoring`: Calcula las puntuaciones numéricas.
    -   `run_evidence_analyst`: Un primer análisis de las evidencias.

2.  **Fase 2: Flujo "Top-Down" (El Núcleo del Análisis):**
    -   **`run_tower_blueprint_engine`:** Ejecuta el motor principal para generar el `BlueprintPayload`. Este es el paso más importante, que crea la "fuente de la verdad".
    -   **`run_executive_annex_synthesizer`:** Ejecuta el sintetizador que lee el Blueprint y crea el `AnnexPayload` a partir de él.

3.  **Fase 3: Código Heredado (Comentado):**
    -   El script contiene un gran bloque de código comentado que revela la arquitectura anterior del sistema. Previamente, las secciones se generaban en paralelo y se "ensamblaban" al final. Este enfoque fue reemplazado por el flujo "Top-Down" para evitar la inconsistencia ("split-brain"), pero el código se ha mantenido como referencia histórica.

4.  **Fase 4: Renderizado Final (Paralelo):**
    -   Una vez generados los payloads principales, el script lanza en paralelo las tareas finales de renderizado:
        -   `render_tower_blueprint`: Crea el documento `.docx` del Blueprint.
        -   `render_tower_annex_from_template`: Crea el documento `.docx` del Anexo.

## Rol en el Proyecto

Este script es el **Corazón de la Orquestación de Torres**.

-   **Definición del Flujo de Trabajo:** Es la fuente de verdad sobre el orden y la dependencia de los pasos para analizar una torre.
-   **Ejecutor del Pipeline:** No es solo una definición, sino el programa que activamente ejecuta y monitoriza el pipeline completo.
-   **Resiliencia y Aislamiento:** El uso de subprocesos asíncronos aislados hace que el pipeline sea robusto y menos propenso a errores sutiles de estado compartido.
-   **Documentación Viva de la Arquitectura:** La propia estructura del script, incluyendo el código comentado, sirve como una documentación histórica y actual de la arquitectura del sistema y su evolución.
