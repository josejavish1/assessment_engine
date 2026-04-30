# Documentación: `schemas/global_report.py`

## Resumen

Este módulo define los esquemas de Pydantic para el `GlobalReportPayload`. Este es el contrato de datos que estructura el informe de más alto nivel, destinado a una audiencia ejecutiva (CIO), que consolida y resume los hallazgoss de todas las torres tecnológicas evaluadas. Este esquema es la plantilla de datos para la visión estratégica y transversal de todo el assessment.

## Estructura del Esquema

### `GlobalReportPayload` (Modelo Raíz)

Es el modelo principal que representa la totalidad del `global_report_payload.json`.
-   Hereda de `VersionedPayload` para incluir los metadatos de trazabilidad.
-   Agrega las secciones clave que componen un informe estratégico global:
    -   `meta`: Metadatos básicos del documento (cliente, fecha, versión).
    -   `executive_summary`: El resumen ejecutivo principal, con el titular y los impactos de negocio clave (`ExecutiveSummaryDraft`).
    -   `burning_platform`: Una lista que destaca los riesgos de negocio más críticos y urgentes ("la plataforma en llamas") que requieren acción inmediata (`BurningPlatformItem`).
    -   `heatmap`: Un campo flexible para pasar los datos de un mapa de calor que muestre el estado de todas las torres de un vistazo.
    -   `tower_bottom_lines`: Una lista con los resúmenes de una línea (bottom line) de cada una de las torres individuales (`TowerBottomLineItem`).
    -   `target_vision`: La visión estratégica general para la transformación tecnológica del cliente (`TargetVisionDraft`).
    -   `execution_roadmap`: El roadmap consolidado que organiza las iniciativas en programas y horizontes de tiempo (ej. 0-3 meses, 3-12 meses, etc.) (`ExecutionRoadmapDraft`).
    -   `executive_decisions`: Una lista de las decisiones clave que se requieren por parte de la dirección del cliente (`ExecutiveDecisionsDraft`).
    -   `visuals`: Un diccionario para las rutas a los gráficos y visuales globales.

### Modelos de Secciones Estratégicas

-   **`ExecutionRoadmapDraft`:** Un modelo detallado que estructura el plan de acción. Define `Programas` y luego asigna `Iniciativas` a diferentes `Horizontes` de tiempo, proporcionando una vista de planificación a largo plazo.
-   **`BurningPlatformItem`:** Estructura la sección más crítica del informe, enfocada en comunicar la urgencia del cambio.
-   **`TargetVisionDraft`:** Define la narrativa del estado futuro, con proposiciones de valor y principios estratégicos.
-   **`ExecutiveDecisionsDraft`:** Formaliza las llamadas a la acción para la dirección del cliente, especificando el impacto de retrasar dichas decisiones.

### Modelos de Borrador (`*Draft`)

-   **`GlobalReviewDraft`, `GlobalRefinerDraft`, etc.:** Al igual que en otros esquemas, la presencia de estos modelos sugiere la existencia (o planificación) de un flujo de trabajo de refinamiento por IA o revisión humana para el informe global, donde un borrador inicial es procesado antes de generar el `GlobalReportPayload` final.

## Rol en el Proyecto

Este fichero define el **contrato de datos canónico para el Informe Global del CIO**.

-   **Estructura para la Agregación:** Sirve como la estructura objetivo para el script `build_global_report_payload.py`. La tarea de ese agregador es recolectar información de todos los blueprints de torre y rellenar este esquema global.
-   **Entrada para el Renderizador Global:** El `GlobalReportPayload` es la entrada directa que espera el script `render_global_report_from_template.py` para generar el documento `.docx` final.
-   **Definición de la Narrativa Estratégica:** La propia estructura del esquema (con secciones como `BurningPlatform` o `ExecutiveDecisions`) define el flujo narrativo del informe final. No es solo un contenedor de datos, sino una plantilla para contar una historia estratégica.
-   **Desacoplamiento:** Desacopla la lógica de agregación de datos de la lógica de presentación, permitiendo que ambos procesos evolucionen de forma independiente siempre que se respete este contrato.
