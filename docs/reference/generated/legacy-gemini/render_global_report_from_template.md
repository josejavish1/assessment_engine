# Documentación: `render_global_report_from_template.py`

## Resumen

Este script es el **renderizador de documentos `.docx` para el Informe Ejecutivo Consolidado**, el entregable final de más alto nivel destinado al CIO y a la dirección del cliente. Su responsabilidad es tomar el `GlobalReportPayload`, que es el resultado de la agregación y refinamiento de todas las torres, y plasmarlo en un documento de Word con un formato y una maquetación de calidad profesional. Es la "imprenta" final del pipeline global.

## Componentes Principales

### `main()`

-   **Propósito:** La función principal que orquesta todo el proceso de renderizado.
-   **Flujo de Trabajo:**
    1.  **Validación de Contrato (Type-Safety):** Como primer paso, valida de forma estricta el fichero JSON de entrada contra el esquema Pydantic `GlobalReportPayload`. Si los datos no cumplen el contrato al 100%, el script aborta con un error.
    2.  **Carga y Limpieza de Plantilla:** Carga la plantilla `.docx` y borra todo su contenido (`clear_document_body`), conservando solo los estilos, cabeceras y pies de página.
    3.  **Renderizado Secuencial:** Llama a una serie de funciones `render_*` en secuencia, cada una encargada de construir una parte del documento (portada, resumen, riesgos, etc.).
    4.  **Configuración del Pie de Página:** Invoca a `create_page_number_footer` para añadir dinámicamente la numeración de página al documento.
    5.  **Guardado:** Guarda el documento final.

### Funciones de Renderizado (`render_*`)

Cada función se especializa en una sección del informe, utilizando la librería `python-docx` para crear y formatear el contenido.
-   `render_cover`: Crea la portada.
-   `render_executive_summary`: Construye el resumen ejecutivo, incluyendo el score global, la narrativa y la inserción del gráfico de radar.
-   `render_burning_platform`: Genera las tablas para la sección de "amenazas sistémicas".
-   `render_tower_bottom_lines`: Crea la tabla de diagnóstico que resume el estado de cada torre.
-   `render_target_vision`: Construye la sección de visión estratégica.
-   `render_execution_roadmap`: Genera las tablas del plan de implementación y los horizontes temporales.
-   `render_executive_decisions`: Crea la tabla final con las decisiones requeridas.

### Funciones de Saneamiento de Texto

Este renderizador aplica una capa de limpieza de texto adicional y específica para un informe de nivel ejecutivo:
-   **`clean_t_codes(text)`:** Elimina sistemáticamente todas las menciones a los códigos de torre internos (ej: "T5", "(T2, T3)"). Esto fuerza a que el informe hable en el lenguaje del negocio (ej: "Resiliencia", "Redes y Cómputo") en lugar de jerga interna del proyecto.
-   **`sanitize_client_name(text, client_name)`:** Reemplaza las menciones explícitas al nombre del cliente por un término más formal como "la organización". Esto contribuye a un tono de consultoría más objetivo y externo.

## Rol en el Proyecto

Este script es la **Capa de Presentación Final para el Nivel Ejecutivo**.

-   **Productor del Entregable para el CIO:** Es el componente final del pipeline global, responsable de crear uno de los entregables más importantes y visibles.
-   **Garantía de Calidad y Consistencia:** La validación Pydantic inicial y el uso de funciones de saneamiento de texto aseguran que el documento final sea robusto, consistente y tenga el tono profesional adecuado para su audiencia.
-   **Desacoplamiento de Presentación y Lógica:** Al igual que otros renderizadores, separa por completo la lógica de agregación de datos (realizada en `build_global_report_payload`) de la lógica de presentación. Mientras el `GlobalReportPayload` cumpla su contrato, la apariencia del informe se puede modificar de forma independiente en este script.
-   **Maquetación Avanzada:** El uso detallado de `python-docx` para controlar tablas, colores, fuentes y pies de página demuestra un enfoque en producir un artefacto final de alta calidad visual.
