# Documentación: `render_tower_annex_from_template.py`

## Resumen

Este script es un **renderizador de documentos `.docx`** potente y flexible. Su única responsabilidad es tomar un fichero de datos estructurado (`annex_template_payload.json`) y una plantilla de Word (`.docx`), y combinar ambos para producir el documento final y pulido del "Anexo de Torre". Este módulo representa la capa de presentación final del pipeline, convirtiendo los datos estructurados en un informe profesional y legible.

## Componentes Principales

### `main()`

Es la función que orquesta todo el proceso de renderizado.
1.  **Carga los datos:** Utiliza `robust_load_payload` para cargar de forma segura el `annex_template_payload.json`.
2.  **Carga la plantilla:** Abre el documento `.docx` que sirve como plantilla.
3.  **Limpia la plantilla:** Ejecuta la función `clean_brackets_and_consultant_notes` para eliminar cualquier texto de instrucción o marcador de posición antiguo que pudiera quedar en la plantilla.
4.  **Renderiza sección por sección:** Llama a una serie de funciones `replace_*` y `render_*`, pasando a cada una la sección correspondiente de los datos del payload para que la inserte y formatee en el documento.
5.  **Guarda el documento final:** Guarda el documento `.docx` ya poblado en la ruta de salida especificada.

### Librería de Funciones de `python-docx`

El corazón de este script es su extensa colección de funciones auxiliares que manipulan el documento de Word a un nivel muy detallado. No es un simple "buscar y reemplazar".
-   **Reemplazo de Placeholders (`{{...}}`):**
    -   `replace_simple_placeholder`: Para reemplazar texto simple.
    -   `render_multi_paragraph_block`: Para insertar múltiples párrafos de texto en un único lugar.
    -   `render_list_at_placeholder`: Para generar listas con viñetas.
-   **Generación Dinámica de Tablas:**
    -   `render_pillar_score_table`, `render_risks_table`, `render_gap_table`: Crean tablas complejas a partir de listas de datos, aplicando formato a las cabeceras y a las celdas.
    -   `render_initiative_cards`: Utiliza tablas para crear un layout de "tarjetas" visualmente atractivo para cada iniciativa.
-   **Inserción de Imágenes:**
    -   `render_radar_chart`: Busca un placeholder y lo reemplaza por una imagen, como el gráfico de radar de madurez. Es capaz de manejar imágenes codificadas en base64.
-   **Formato de Bajo Nivel:**
    -   Contiene numerosas funciones para controlar cada aspecto del formato: `shade_cell` (colorear celdas), `set_cell_text` (escribir en celdas con formato), `apply_body_format` (aplicar estilos a párrafos).
    -   Incluso manipula directamente el XML subyacente (OOXML) para funcionalidades avanzadas como repetir cabeceras de tabla en múltiples páginas o evitar que una fila se parta entre dos páginas.

### Lógica de Renderizado Adicional

-   **Variante Extendida (`render_extended_variant`):** Tiene la capacidad de renderizar una versión "larga" y más detallada del informe si así se especifica en los metadatos del payload.

## Rol en el Proyecto

Este script es la **Capa de Presentación** para el Anexo de Torre. Es el último paso del pipeline de generación de este entregable.

-   **Separación de Responsabilidades:** Es el ejemplo perfecto del principio de separación de datos y presentación. Los scripts anteriores se preocupan por **qué** dicen los datos; este script solo se preocupa por **cómo se ven**.
-   **Motor de Plantillas para Word:** Actúa como un sofisticado motor de plantillas. El `.docx` define el esqueleto y los estilos, y este script lo viste con el contenido dinámico.
-   **Resultado de Alta Fidelidad:** El uso avanzado de la librería `python-docx` y la manipulación de OOXML le permiten producir documentos con una calidad de maquetación profesional, algo imposible con métodos más simples.
-   **Productor del Artefacto Final:** Genera uno de los entregables clave para el cliente: el documento del Anexo de Torre.
