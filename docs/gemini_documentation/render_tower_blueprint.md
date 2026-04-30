# Documentación: `render_tower_blueprint.py`

## Resumen

Este script es el responsable de generar el documento maestro de transformación, conocido como "Blueprint de Torre", en formato `.docx`. El blueprint es el artefacto técnico más detallado del `assessment-engine` y sirve como la fuente de verdad para otros documentos derivados.

## Componentes Principales

### `main(argv)`

Es la función principal que orquesta todo el proceso. Recibe dos argumentos desde la línea de comandos:
1.  La ruta al fichero `BlueprintPayload` en formato JSON, que contiene todos los datos.
2.  La ruta donde se guardará el fichero `.docx` generado.

El flujo de trabajo es el siguiente:
1.  **Carga de Datos:** Lee y valida el `BlueprintPayload` principal. Además, carga datos complementarios como la "inteligencia de cliente" y el payload del anexo ejecutivo asociado a la torre.
2.  **Preparación del Documento:** Crea un nuevo documento de Word en memoria.
3.  **Renderizado de Secciones:** Llama a una serie de funciones `render_*`, cada una especializada en construir una sección específica del documento.
4.  **Guardado:** Guarda el documento final en la ruta de salida especificada.

### Funciones de Renderizado

-   **`render_cover(doc, payload)`:** Genera la portada del documento.
-   **`render_snapshot_page(doc, payload, client_intelligence, annex_data)`:** Crea la página de resumen ejecutivo, incorporando datos de inteligencia y del anexo.
-   **`render_maturity_profile(doc, payload, annex_data)`:** Dibuja el perfil de madurez por pilar.
-   **`render_cross_capabilities_analysis(doc, payload)`:** Renderiza la sección de análisis de capacidades transversales.
-   **`render_pilar_detail(doc, pilar)`:** Itera sobre cada pilar analizado y genera su sección de detalle.
-   **`render_roadmap_page(doc, payload)`:** Construye la página que detalla el roadmap de transformación.
-   **`render_conclusion(doc, payload, annex_data)`:** Genera la sección final de conclusiones.

### Funciones de Utilidad

El script utiliza varias funciones auxiliares para manipular el documento de Word (añadir párrafos, cabeceras, viñetas, tablas, etc.). La mayoría de estas utilidades se importan desde otros módulos para fomentar la reutilización, como `text_utils.py` y `contract_utils.py`.

## Rol en el Proyecto

Dentro de la arquitectura del `assessment-engine`, este script cumple el rol de **Renderizador Final**. Su única responsabilidad es traducir un payload de datos estructurado y validado (`BlueprintPayload`) a un formato de presentación profesional (un documento de Word).

Según la documentación del proyecto (`GEMINI.md`), este es uno de los scripts monolíticos que se planea refactorizar en el futuro para separar mejor las responsabilidades de orquestación, lógica de negocio y renderizado puro.
