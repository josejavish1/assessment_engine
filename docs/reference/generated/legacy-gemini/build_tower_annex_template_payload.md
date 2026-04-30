# Documentación: `build_tower_annex_template_payload.py`

## Resumen

Este script es un módulo de transformación y sanitización de datos. Su propósito principal es tomar varios ficheros JSON semi-estructurados (el resultado de análisis previos de la IA, como `approved_annex_refined.json` o `findings.json`) y convertirlos en un único `annex_template_payload.json`. Este payload final está meticulosamente limpio y estructurado para servir como la entrada directa al script que renderiza el documento `.docx` del Anexo de Torre.

## Componentes Principales

### `main()`

Es la función de entrada que maneja los argumentos de la línea de comandos. Acepta principalmente el fichero JSON de entrada y, opcionalmente, la ruta de salida y un "perfil" (`short` o `long`) que determina el nivel de detalle del contenido.

### `PROFILE_SETTINGS`

Un diccionario de configuración muy importante que define las reglas editoriales. Establece límites estrictos para la longitud de los textos (ej. máximo número de palabras, frases o caracteres para un resumen) y la cantidad de elementos en las listas (ej. mostrar solo los 5 riesgos más importantes). Esto permite generar una versión corta y ejecutiva (`short`) o una más detallada (`long`) del mismo anexo.

### Funciones `build_*`

El núcleo del script se divide en varias funciones `build_*` (ej: `build_executive_summary`, `build_sections`), cada una encargada de construir una parte específica del payload final.
-   **Leen y combinan** datos de múltiples ficheros JSON de entrada.
-   **Aplican reglas de limpieza:** Utilizan un extenso conjunto de funciones de utilidad para normalizar y sanear los textos.
-   **Aplican la política editorial:** Usan `PROFILE_SETTINGS` para truncar textos y limitar listas, asegurando que el contenido sea conciso y relevante.
-   **Derivan y calculan:** Crean nuevos datos a partir de los existentes, como calcular una banda de madurez a partir de una puntuación numérica.
-   **Manejan fallos:** Tienen lógica de *fallback* para buscar datos en diferentes lugares si no se encuentran donde se espera.

### Funciones de Utilidad

El script cuenta con una rica librería de funciones auxiliares (`clean_text`, `truncate_words`, `take_sentences`, etc.) dedicadas a la limpieza de datos. Estas se encargan de tareas como eliminar caracteres inválidos para Word, convertir textos a números de forma segura, o extraer un número específico de frases de un párrafo largo.

### Validación Pydantic

Al final del proceso, el script intenta validar el diccionario que ha construido contra el esquema Pydantic `AnnexPayload`. Este es un paso de control de calidad final para asegurar que el "contrato" con el renderizador se cumple a la perfección.

## Rol en el Proyecto

Este script desempeña el rol de **Refinador de Datos y Constructor de Payloads**. Es el último y crucial paso de preparación de datos antes de la capa de presentación.

-   **Capa Anti-Corrupción:** Protege al renderizador de la naturaleza a veces impredecible de los resultados de la IA. Actúa como un filtro que limpia, normaliza y estructura los datos.
-   **Aplicador de la Política Editorial:** Es el componente que asegura que el documento final cumpla con las reglas de negocio en cuanto a concisión y enfoque, gracias a los perfiles `short` y `long`.
-   **Transformador de Datos:** No se limita a limpiar; transforma activamente los datos, creando resúmenes, derivando valores y reestructurándolos para que encajen perfectamente en la plantilla del documento final.
-   **Desacoplamiento:** Desacopla por completo la generación de contenido (IA) de la presentación final (renderizador). La IA se enfoca en el contenido, este script en prepararlo, y el renderizador solo en "pintarlo".
