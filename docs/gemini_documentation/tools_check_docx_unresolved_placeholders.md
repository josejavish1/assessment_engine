# Documentación: `tools/check_docx_unresolved_placeholders.py`

## Resumen

Este script es una **herramienta de validación y control de calidad final**. Su única responsabilidad es escanear un documento de Word (`.docx`) ya generado y verificar que no contenga ningún "placeholder" o marcador de posición sin resolver. Los placeholders (ej: `{{CLIENT_NAME}}`) son utilizados en las plantillas y deben ser reemplazados por datos reales durante el proceso de renderizado. La presencia de uno en el documento final indica un fallo en el pipeline.

## Componentes Principales

### `main()`

La función principal orquesta el proceso de validación.

-   **Entrada:** Acepta una única entrada desde la línea de comandos: la ruta al fichero `.docx` que se quiere verificar.
-   **Lógica de Escaneo:**
    1.  Utiliza la librería `python-docx` para abrir y leer el documento.
    2.  Define una expresión regular (`PLACEHOLDER_RE`) para detectar cualquier texto que siga el patrón `{{...}}`.
    3.  Recorre de forma exhaustiva todos los elementos del documento: primero todos los **párrafos** del cuerpo principal y luego cada una de las **celdas** de todas las **tablas**.
    4.  En cada elemento, busca coincidencias con la expresión regular.
-   **Lógica de Salida:**
    1.  Si se encuentra al menos un placeholder sin resolver:
        -   Imprime en la consola la línea `UNRESOLVED_PLACEHOLDERS=YES`.
        -   Imprime una lista de los placeholders encontrados y el contexto en el que aparecieron.
        -   El script termina con un **código de salida de error (`SystemExit(1)`)**.
    2.  Si no se encuentra ningún placeholder:
        -   Imprime en la consola la línea `UNRESOLVED_PLACEHOLDERS=NO`.
        -   El script termina con un código de salida de éxito (0).

## Rol en el Proyecto

Este script es una **Herramienta de Integración Continua (CI) y Aseguramiento de Calidad (QA)**.

-   **Guardia de Calidad Final:** Actúa como la última línea de defensa para garantizar la calidad del documento generado. Evita que se entreguen al cliente informes incompletos o con errores de formato evidentes.
-   **Detector de Regresiones:** Su principal utilidad es en flujos de trabajo automatizados. Un sistema de CI puede ejecutar este script automáticamente después de cada ejecución del pipeline. El código de salida de error (`1`) permite que el sistema de CI detecte el fallo y marque la "build" o el "test" como fallido, alertando inmediatamente a los desarrolladores de que un cambio reciente ha roto la lógica de renderizado.
-   **Complemento a los Tests Unitarios:** Mientras que los tests de `pytest` (como los "Golden File tests") se ejecutan en un entorno de desarrollo, esta herramienta puede usarse en cualquier entorno (desarrollo, staging, producción) directamente sobre los artefactos generados, proporcionando una capa de validación adicional e independiente.
-   **Simplicidad y Robustez:** Su enfoque es simple y robusto. No necesita conocer la lógica del pipeline, simplemente aplica una regla clara y universal a cualquier documento `.docx`, lo que lo hace muy reutilizable y fácil de mantener.
