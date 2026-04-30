# Documentación: `generate_tower_radar_chart.py`

## Resumen

Este script es un **generador de visualizaciones de datos**. Su única responsabilidad es leer un fichero de payload (típicamente, el `annex_template_payload.json`), extraer las puntuaciones de madurez de cada pilar tecnológico y utilizar la librería `matplotlib` para crear un **gráfico de radar** en formato `.png`. Este gráfico es una de las visualizaciones más importantes del informe, ya que permite a los stakeholders ver de un solo vistazo el estado de madurez en las diferentes áreas.

## Componentes Principales

### `main()`

La función principal que orquesta la generación del gráfico.

-   **Entrada:** Acepta uno o dos argumentos desde la línea de comandos:
    1.  La ruta al fichero `template_payload_json` que contiene los datos.
    2.  (Opcional) La ruta donde se guardará el fichero `.png` de salida. Si no se proporciona, se guarda con un nombre estándar en el mismo directorio que el payload.
-   **Flujo de Trabajo:**
    1.  **Carga de Datos:** Lee el fichero JSON del payload y extrae los nombres de los pilares (`labels`) y sus puntuaciones (`values`) de la sección `pillar_score_profile`.
    2.  **Preparación de Datos:** Convierte los datos al formato numérico que `matplotlib` necesita y calcula los ángulos para cada eje del gráfico de radar.
    3.  **Configuración y Dibujo del Gráfico:** Utiliza `matplotlib.pyplot` para configurar y dibujar el gráfico, personalizando cada aspecto:
        -   Uso de coordenadas polares (`polar=True`).
        -   Orientación y dirección del gráfico.
        -   Posición y texto de las etiquetas de los ejes (los nombres de los pilares).
        -   Definición de la escala radial (de 0 a 5).
        -   Dibujo de la línea que conecta los valores y relleno del área resultante.
    4.  **Guardado de la Imagen:** Guarda la figura generada como un fichero `.png` en la ruta de salida.
    5.  **Actualización del Payload:** Realiza un paso crucial: **modifica el fichero de payload de entrada** para añadir una nueva clave, `radar_chart`, que contiene la ruta absoluta al fichero `.png` que acaba de crear.

## Rol en el Proyecto

Este script es un componente clave de la **Capa de Presentación y Visualización**.

-   **Traductor de Datos a Visualización:** Su función es convertir datos numéricos tabulares en una visualización intuitiva y fácil de interpretar para una audiencia ejecutiva.
-   **Generador de Artefactos de Soporte:** Produce un artefacto (`.png`) que no es un entregable final en sí mismo, sino un componente que será incrustado en otros entregables, como los documentos `.docx`.
-   **Enriquecedor de Payloads:** El paso de actualizar el payload de entrada es una pieza de diseño importante. Actúa como un "enriquecedor", añadiendo información al payload que será consumida por la siguiente etapa del pipeline (el renderizador del documento). Esto asegura que el renderizador no necesite adivinar el nombre del fichero del gráfico, sino que lo reciba como parte de su contrato de datos.
-   **Desacoplamiento:** Separa limpiamente la lógica de generación de gráficos de la lógica de renderizado de documentos. Si en el futuro se quisiera cambiar la apariencia del gráfico o usar una librería diferente, solo sería necesario modificar este script, sin afectar a los renderizadores.
