# Documentación: `tests/test_t5_golden.py`

## Resumen

Este es un módulo de tests de tipo **"Golden File"**. Su propósito es servir como la principal red de seguridad contra regresiones para el pipeline de la torre T5. No se centra en la lógica interna del código, sino en validar el **contenido, la forma y la calidad de los artefactos finales generados** (tanto los `payloads` JSON como los documentos `.docx`) contra un conjunto de resultados esperados conocidos y "dorados". Su existencia es una implementación directa de la estrategia de "Golden tests de T5" del plan de endurecimiento del proyecto.

## Tests Principales

Cada test valida una característica específica de los artefactos "golden" del caso de prueba `smoke_ivirma/T5`.

### `test_t5_blueprint_payload_schema_and_shape()`

-   **Propósito:** Valida que el `blueprint_t5_payload.json` es correcto tanto en estructura como en contenido.
-   **Método:** Valida el fichero contra el esquema `BlueprintPayload` y luego afirma (asserts) que ciertos valores clave son los esperados (ej: el código de torre es "T5", hay 5 pilares, los metadatos de versión existen, etc.).

### `test_t5_annex_payload_schema_and_executive_limits()`

-   **Propósito:** Valida que el `approved_annex_t5.template_payload.json` cumple con su esquema y con las reglas editoriales de un resumen ejecutivo.
-   **Método:** Valida contra el esquema `AnnexPayload` y luego afirma que el número de riesgos, gaps e iniciativas está dentro de los límites esperados para un anexo conciso. También comprueba que el texto del resumen contenga palabras clave orientadas a negocio (ej: "m&a", "ia", "datos"), asegurando el tono correcto.

### `test_t5_annex_docx_has_no_functional_placeholders()`

-   **Propósito:** Asegura que el documento `.docx` final del anexo no contiene ningún resto de los placeholders de la plantilla.
-   **Método:** Lee el contenido XML del fichero `.docx` y busca la presencia de cadenas de texto como `{{RISKS_TABLE}}` o `[Fecha]`, esperando no encontrarlas.

### `test_t5_annex_docx_embeds_real_radar_chart()`

-   **Propósito:** Un test muy sofisticado que verifica que la imagen del gráfico de radar dentro del `.docx` es la imagen correcta.
-   **Método:** Descomprime el fichero `.docx`, analiza sus ficheros de relaciones XML para encontrar la imagen incrustada, extrae los bytes de esa imagen y **compara su hash SHA256** con el hash del fichero de imagen original (`pillar_radar_chart.generated.png`). Esto prueba con certeza que la imagen correcta fue embebida.

### `test_t5_blueprint_and_annex_roles_are_distinct()`

-   **Propósito:** Valida la regla editorial de que el Blueprint debe ser un documento extenso y el Anexo un resumen corto.
-   **Método:** Calcula el número de palabras de ambos documentos `.docx` y afirma que el Blueprint es significativamente más largo que el Anexo y que ambos se mantienen dentro de unos rangos de tamaño razonables.

## Rol en el Proyecto

Este fichero es la **Red de Seguridad Primaria contra Regresiones** del pipeline.

-   **Aseguramiento de Calidad del Contenido:** A diferencia de otros tests, este se enfoca en la **calidad y el contenido** del producto final, no solo en la lógica del código o la estructura de los datos.
-   **Prevención de Regresiones Silenciosas:** Su rol más importante es detectar fallos que otros tests no verían. Un cambio en el código podría seguir generando un documento estructuralmente válido, pero que esté vacío, contenga la imagen incorrecta o esté lleno de placeholders. Este test suite captura esos fallos "silenciosos".
-   **Aplicación de Reglas de Negocio/Editoriales:** Automatiza la verificación de reglas que no están en el código, como el tono del lenguaje o la relación de tamaño entre documentos.
-   **Confianza para el Cambio:** Proporciona una alta confianza para refactorizar o modificar cualquier parte del pipeline, sabiendo que si estos tests pasan, el entregable final para T5 no se ha degradado.
