# Documentación: `run_scoring.py`

## Resumen

Este script es el **motor de cálculo cuantitativo** del `assessment-engine`. Su única función es procesar las respuestas numéricas del `case_input.json` y, aplicando la metodología y los pesos definidos en el `tower_definition.json`, calcular todas las puntuaciones de madurez. Es un script puramente **determinista** (no utiliza IA) que transforma las entradas en métricas objetivas. El resultado de su ejecución es el fichero `scoring_output.json`.

## Componentes Principales

### `main()`

-   **Propósito:** Es la función principal que orquesta el proceso.
-   **Lógica:**
    1.  Recibe la ruta al `case_input.json` como argumento de línea de comandos.
    2.  Carga tanto el `case_input.json` como el `tower_definition.json` correspondiente.
    3.  Llama a la función `build_scoring` para realizar todos los cálculos.
    4.  Guarda el resultado en un nuevo fichero, `scoring_output.json`, en el mismo directorio.

### `build_scoring(case_input, tower_definition) -> dict`

Esta es la función que contiene toda la lógica de negocio para el cálculo de las puntuaciones. Sigue un proceso de **agregación ascendente (bottom-up)**:

1.  **Agregación por KPI:**
    -   Recorre todas las respuestas del `case_input` y las agrupa por su `kpi_id`.
    -   Calcula la puntuación media para cada KPI (utilizando la función `average`).

2.  **Agregación por Pilar:**
    -   Recorre los pilares definidos en la `tower_definition`.
    -   Para cada pilar, recoge las puntuaciones medias de todos sus KPIs.
    -   Calcula la puntuación media del pilar como el promedio de las puntuaciones de sus KPIs.

3.  **Cálculo de la Puntuación de la Torre (Ponderada):**
    -   Realiza el cálculo más importante: la puntuación final de la torre.
    -   Itera sobre las puntuaciones de cada pilar y las multiplica por el peso porcentual (`weight_pct`) que tiene ese pilar en la metodología.
    -   La suma de estos valores ponderados da como resultado el `tower_score_exact`.

4.  **Resolución de la Banda de Madurez (`resolve_band`):**
    -   Toma la puntuación exacta de la torre (`tower_score_exact`).
    -   La compara con los rangos definidos en la sección `score_bands` de la `tower_definition` (ej: min: 1.0, max: 1.8, label: "Nivel 1 - Inicial").
    -   Devuelve la banda de madurez cualitativa correspondiente.

5.  **Ensamblaje del Resultado:**
    -   Construye un diccionario final que contiene no solo los resultados, sino también metadatos sobre cómo se calcularon (ej: `aggregation_method`), las puntuaciones exactas y redondeadas, la banda de madurez y el "gap" o brecha con respecto a un nivel objetivo.

## Rol en el Proyecto

Este script es la **Fuente de Verdad Cuantitativa**.

-   **Traductor de Datos a Métricas:** Su función principal es convertir los datos en bruto (las respuestas) en las métricas clave (puntuaciones de pilar y de torre) que sustentan todo el análisis cuantitativo del informe.
-   **Motor Determinista:** Al ser un script basado en reglas matemáticas y no en IA, sus resultados son 100% predecibles y auditables. Dada una misma entrada, siempre producirá la misma salida. Esto es crucial para la consistencia y fiabilidad de los assessments.
-   **Proveedor de Contexto para la IA:** El `scoring_output.json` que genera es una de las entradas más importantes para los agentes de IA en las fases posteriores. La IA utiliza estas puntuaciones como un contexto fundamental para entender las fortalezas y debilidades del cliente y así generar un análisis narrativo coherente.
-   **Desacoplamiento de la Lógica de Cálculo:** Centraliza toda la lógica de scoring en un único lugar. Si la fórmula para calcular la madurez cambiara, solo sería necesario modificar este script.
