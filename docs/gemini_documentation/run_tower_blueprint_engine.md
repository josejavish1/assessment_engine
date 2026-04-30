# Documentación: `run_tower_blueprint_engine.py`

## Resumen

Este script es el **motor de análisis principal** para una torre tecnológica individual. Su función es orquestar a una serie de agentes de IA para transformar los datos en crudo de un `case_input.json` en el `BlueprintPayload`, el artefacto de datos más detallado y fundamental de todo el sistema. Implementa un sofisticado patrón de "equipo de IAs" (Arquitecto + Crítico) para asegurar la calidad del análisis técnico.

## Componentes Principales

### `main()`

Es la función de entrada que se ejecuta desde la línea de comandos, aceptando el nombre del `client` y el `tower_id` como argumentos para iniciar el proceso de análisis.

### `run_tower_blueprint(client_name, tower_id)`

Es el orquestador principal para la generación del blueprint de una torre.
**Flujo de trabajo:**
1.  **Carga de Datos:** Lee el `case_input.json` y el fichero de `client_intelligence.json` para obtener todo el contexto necesario.
2.  **Preparación de Datos:** Agrupa todas las respuestas del `case_input.json` por pilar tecnológico. Esto permite que cada pilar se analice de forma independiente pero con todo su contexto.
3.  **Procesamiento Secuencial de Pilares:** Itera sobre cada pilar y llama a la función `process_pilar_blueprint` para cada uno. El procesamiento se hace en serie (uno tras otro) para garantizar la máxima calidad en el análisis de cada pilar.
4.  **Agente de Cierre (Orquestador):** Una vez que todos los pilares han sido analizados, invoca a un agente de IA final. Este agente "Orquestador" recibe el análisis completo de todos los pilares y su tarea es generar las secciones transversales y de alto nivel del blueprint: el resumen ejecutivo (`executive_snapshot`), el análisis de capacidades comunes y el `roadmap`.
5.  **Ensamblaje y Guardado:** Junta los resultados de los análisis de los pilares y las secciones del orquestador en la estructura final del `BlueprintPayload`, añade metadatos de versión y guarda el fichero `blueprint_{tower_id}_payload.json`.

### `process_pilar_blueprint(...)`

Este es un sub-orquestador que implementa un patrón de **"Arquitecto + Crítico"** para analizar un único pilar tecnológico.
1.  **Agente Arquitecto:** Se invoca a un primer agente de IA ("El Arquitecto") con todo el contexto y las respuestas de ese pilar. Su tarea es generar un primer borrador del análisis técnico, cumpliendo con el esquema `PillarBlueprintDraft`.
2.  **Agente Crítico:** El resultado del Arquitecto se pasa inmediatamente a un segundo agente de IA ("El Crítico"). Su instrucción es revisar, refinar y mejorar la calidad del borrador inicial.
3.  **Resultado Final:** La salida del Crítico se considera el análisis final para ese pilar. Si el Crítico falla, el sistema utiliza el borrador del Arquitecto como fallback.

## Rol en el Proyecto

Este script es el **Núcleo del Motor de Análisis**. Es responsable de crear el contenido analítico más profundo y detallado del `assessment-engine`.

-   **Generador de Análisis Profundo:** Mientras otros scripts refinan, agregan o presentan datos, este script es el que **origina el análisis técnico detallado** que forma la base de todo el proceso.
-   **Equipo Multi-Agente:** Utiliza un patrón de IA avanzado (Arquitecto + Crítico) para mejorar la calidad y fiabilidad del contenido generado, simulando un proceso de revisión por pares.
-   **Fundamento del Pipeline:** El `BlueprintPayload` que produce es la "fuente de la verdad" para todos los demás artefactos (Anexo, Informe Global, Plan Comercial), cumpliendo estrictamente con el principio de arquitectura "Top-Down" del proyecto.
