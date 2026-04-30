# Documentación: `render_web_presentation.py` (y `generate_web_dashboard`)

## Resumen

Este script contiene una de las funcionalidades de presentación más potentes y de mayor valor de todo el proyecto: **la generación de un dashboard estratégico interactivo en un único fichero HTML autocontenido**. Este dashboard sirve como una alternativa dinámica y explorable a los estáticos documentos `.docx`, ideal para presentaciones ejecutivas y workshops de trabajo.

La funcionalidad principal reside dentro de la función `generate_web_dashboard`, que actúa como un completo motor de fusión de datos y renderizado web.

## Componentes Principales

### `generate_web_dashboard(client_id)`

Esta función es el núcleo del script y sigue un proceso de dos fases: un motor de datos y un motor de renderizado.

**1. Fase de Motor de Datos (Data Engine):**
-   **Punto de Partida:** Lee el `global_report_payload.json` como la base estratégica.
-   **Fusión de Datos ("Contrato Híbrido"):** Itera sobre cada torre tecnológica y lee su `blueprint_payload.json` correspondiente. A continuación, realiza una fusión de datos muy sofisticada:
    -   Toma la información de alto nivel del `global_report`.
    -   La enriquece con los detalles tácticos y técnicos de cada `blueprint` (riesgos estructurales, beneficios operativos, iniciativas detalladas, etc.).
    -   Aplica una **lógica de "fallback inteligente"**, donde si un dato no está en el blueprint (ej: complejidad), se deriva de otro (ej: la puntuación de madurez).
-   **Salida:** El resultado de esta fase es un único y masivo objeto de datos JSON, apodado `nexus_data`, que contiene toda la información necesaria, pre-procesada y lista para la visualización.

**2. Fase de Renderizado HTML:**
-   **Plantilla Embebida:** El script contiene una enorme cadena de texto multilínea que es una plantilla HTML completa. Esta plantilla ya incluye:
    -   El **CSS**, utilizando el framework **TailwindCSS** para un diseño moderno.
    -   El **JavaScript**, incluyendo librerías de visualización de datos de primer nivel como **Chart.js** (para los gráficos de radar) y **D3.js** (para el diagrama de Sankey).
-   **Inyección de Datos:** El objeto `nexus_data` se serializa como una cadena JSON y se inyecta directamente dentro de una etiqueta `<script type="application/json">` en el HTML. El JavaScript del lado del cliente lee entonces estos datos para construir dinámicamente toda la interfaz.
-   **Generación del Fichero:** El HTML final se guarda como un fichero `index.html` en el directorio `presentation/` del cliente.

## Funcionalidades del Dashboard Generado

La interfaz de usuario resultante es rica en funcionalidades interactivas:
-   **Vista Global:** Con score, resumen, "burning platform" y un radar de todas las torres.
-   **Heatmap y Modales:** Un mapa de torres interactivas. Al hacer clic en una, se abre una **ventana modal a pantalla completa** con el detalle de esa torre, incluyendo su propio radar, riesgos, plan de acción y un **diagrama de Gantt** de sus iniciativas.
-   **Roadmap Filtrable:** Permite hacer clic en los "Programas de Transformación" para filtrar y resaltar visualmente las iniciativas que pertenecen a ese programa.
-   **Nexo de Impacto (Sankey Diagram):** Una visualización avanzada que muestra el flujo desde las brechas de las torres, a través de los programas de transformación, hasta el impacto de negocio final.

## Rol en el Proyecto

Este script representa la **Capa de Presentación Estratégica e Interactiva**.

-   **Herramienta de Comunicación de Valor:** Es el artefacto que mejor comunica el valor del assessment. Permite a los consultores y a los clientes explorar los resultados de forma dinámica, entendiendo la conexión entre los hallazgos técnicos y la estrategia de negocio.
-   **Alternativa Avanzada al DOCX:** Mientras que los `.docx` son el entregable formal y estático, este dashboard es una herramienta de trabajo y presentación viva.
-   **Motor de Fusión de Datos:** Su lógica para combinar los datos del pipeline global y de los pipelines de torre es un componente crítico que habilita esta visión de 360 grados.
-   **Ejemplo de Producto de Datos:** Es la culminación del pipeline, transformando todos los JSON intermedios en un producto de datos final, usable y de alto impacto.
