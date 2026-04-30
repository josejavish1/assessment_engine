# Documentación: `run_global_pipeline.py`

## Resumen

Este script es el **orquestador del pipeline a nivel global**, es decir, a nivel de cliente. Su responsabilidad es consolidar los resultados de los análisis de todas las torres tecnológicas individuales y orquestar los pasos necesarios para producir el "Informe Ejecutivo Consolidado" final, que es el entregable estratégico destinado a la alta dirección del cliente (CIO). A diferencia del orquestador de torres, este pipeline es **secuencial** y no utiliza paralelismo.

## Componentes Principales

### `main()`

Es la función principal que define el flujo de trabajo de principio a fin. Recibe el nombre del cliente como único argumento y, a partir de ahí, define la secuencia de pasos a ejecutar.

### `run_step(...)`

Es la función encargada de ejecutar cada paso del pipeline. A diferencia de su contraparte en `run_tower_pipeline.py`, este ejecutor no usa subprocesos. En su lugar:
-   **Importación Dinámica:** Importa el módulo de Python correspondiente a cada paso dinámicamente.
-   **Ejecución en el Mismo Proceso:** Llama a la función `main()` del módulo importado directamente, ejecutándolo en el mismo proceso que el orquestador.
-   **Simulación de Argumentos:** Utiliza `unittest.mock.patch` para modificar `sys.argv` al vuelo, pasando los argumentos necesarios a cada script que ejecuta. Este es el mecanismo que le permite "llamar" a otros scripts desde dentro de su propio código.

## Flujo de Trabajo del Pipeline Global

El pipeline se ejecuta de forma estrictamente secuencial:

1.  **Paso 1: `build_global_report_payload` (Construir el Payload Global):**
    -   **Acción:** Este script actúa como un agregador. Escanea los directorios de todas las torres del cliente, lee los `BlueprintPayloads` individuales y extrae la información más relevante (puntuaciones, riesgos, iniciativas clave) para consolidarla en un único `global_report_payload.json`.
    -   **Propósito:** Crear la primera versión del informe consolidado, uniendo los datos de los silos de cada torre.

2.  **Paso 2: `run_executive_refiner` (Refinamiento Ejecutivo):**
    -   **Acción:** Un agente de IA de alto nivel (el "Senior Partner") lee el payload agregado y lo refina. Reescribe las secciones para asegurar una narrativa coherente, un tono ejecutivo y una visión estratégica unificada.
    -   **Propósito:** Convertir una simple agregación de datos en una historia estratégica cohesiva, apta para un CIO.

3.  **Paso 3: Generación de Visuales:**
    -   **Acción:** Se ejecutan dos scripts en secuencia:
        1.  `generate_global_radar_chart`: Crea un gráfico de radar consolidado que muestra la madurez de todas las torres.
        2.  `generate_executive_roadmap_image`: Crea una visualización del roadmap estratégico global.
    -   **Propósito:** Producir los elementos visuales necesarios para enriquecer el informe final.

4.  **Paso 4: `render_global_report_from_template` (Renderizar el DOCX):**
    -   **Acción:** Es el paso final de "impresión". Toma el `global_report_payload.json` ya refinado, las imágenes generadas y una plantilla `.docx` para producir el "Informe Ejecutivo Consolidado" final.
    -   **Propósito:** Crear el entregable final para el cliente.

## Rol en el Proyecto

Este script es el **Orquestador de la Visión Estratégica Final**.

-   **Culminación del Flujo "Top-Down":** Representa la cima de la pirámide "Top-Down". Toma los análisis detallados de la base (blueprints de torre) y los sintetiza en la visión más alta y consolidada.
-   **Director del Informe del CIO:** Orquesta el proceso específico para crear el entregable de mayor nivel, asegurando que pase por una fase de refinamiento de IA para garantizar su calidad estratégica.
-   **Consolidador de Silos:** Su función principal es romper los silos de información de cada torre para presentar una imagen unificada del estado tecnológico y el plan de transformación del cliente.
