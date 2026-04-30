# Documentación: `lib/text_utils.py`

## Resumen

Este módulo es una **librería de utilidades de texto centralizada**. Su propósito es proporcionar un conjunto de funciones para sanear, normalizar y transformar cadenas de texto que se utilizan a lo largo de todo el pipeline. La existencia de este módulo es una aplicación directa del principio de diseño **DRY (Don't Repeat Yourself)**, evitando que cada script implemente su propia lógica de limpieza de texto y asegurando que el tratamiento del texto sea consistente en todo el sistema.

## Componentes Principales

### `normalize_spaces(value: str) -> str`

-   **Propósito:** Realiza una limpieza básica de espaciado.
-   **Acción:** Reemplaza los saltos de línea (`
`) por espacios y luego colapsa cualquier secuencia de múltiples espacios en uno solo.
-   **Uso Típico:** Para obtener una versión de un texto en una sola línea sin espaciado irregular.

### `clean_text_for_word(value: str) -> str`

-   **Propósito:** Esta es una función de saneamiento crucial para la capa de presentación. Su objetivo es preparar el texto para que sea compatible con el formato XML de los documentos de Word (`.docx`).
-   **Acción:** Recorre la cadena de texto y elimina cualquier **carácter de control no imprimible** (aquellos con un código ASCII por debajo de 32), a excepción de los saltos de línea y tabuladores, que sí son válidos.
-   **Importancia:** Los modelos de IA a veces pueden generar caracteres de control invisibles. Si estos caracteres se intentan escribir en un fichero `.docx`, el proceso de guardado falla con un error de XML inválido. Esta función es una **medida de protección indispensable** para evitar que los renderizadores de documentos fallen.

### `normalize_tower_name(value: str) -> str`

-   **Propósito:** Limpiar el nombre de una torre tecnológica, eliminando "ruido" o texto sobrante que a veces es generado por los LLMs.
-   **Acción:** Utiliza una expresión regular para eliminar frases comunes que siguen al nombre de la torre, como "evalúa...", "cubre...", etc.
-   **Uso Típico:** Para obtener un nombre de torre limpio que pueda ser usado como etiqueta o título.

### `slugify(value: str) -> str`

-   **Propósito:** Convertir una cadena de texto arbitraria en un "slug", que es una versión segura para ser utilizada en nombres de fichero o URLs.
-   **Acción:** Normaliza el texto para eliminar acentos, lo convierte a minúsculas y reemplaza cualquier carácter que no sea alfanumérico por un guion bajo.
-   **Ejemplo:** "Informe Global para el Cliente (Año 2026)" se convertiría en `informe_global_para_el_cliente_ano_2026`.
-   **Uso Típico:** Se utiliza en los orquestadores para generar nombres de fichero dinámicos y predecibles.

## Rol en el Proyecto

Este módulo actúa como la **Caja de Herramientas de Limpieza de Texto** del proyecto.

-   **Robustez:** La función `clean_text_for_word` es un componente clave para la robustez del pipeline, ya que previene una causa común de fallos en la fase de renderizado de documentos.
-   **Consistencia:** Asegura que la normalización de texto y la generación de slugs se realicen de la misma manera en todo el sistema, evitando inconsistencias sutiles.
-   **Mantenibilidad:** Centraliza toda la lógica de manipulación de texto. Si se necesita añadir una nueva regla de limpieza o cambiar cómo funcionan los slugs, solo hay que modificar este fichero, en lugar de buscar y reemplazar el código en múltiples scripts.
