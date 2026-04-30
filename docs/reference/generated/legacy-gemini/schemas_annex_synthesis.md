# Documentación: `schemas/annex_synthesis.py`

## Resumen

Este módulo define el esquema Pydantic para el `AnnexPayload`. Este payload es el "contrato de datos" que representa la estructura de un "Anexo Ejecutivo", el cual es un resumen de alto nivel sintetizado a partir de un `BlueprintPayload`. Este fichero es la fuente de verdad para la estructura de datos que se utiliza para generar el documento `.docx` del Anexo de Torre.

## Estructura del Esquema

Al igual que otros esquemas del proyecto, está compuesto por una serie de modelos Pydantic anidados que se corresponden con las secciones del documento final.

### `AnnexPayload` (Modelo Raíz)

Es el modelo principal que engloba todo el contenido del anexo.
-   Hereda de `VersionedPayload`, por lo que siempre incluye metadatos de versionado (`_generation_metadata`).
-   Agrega las principales secciones del documento:
    -   `document_meta`: Un diccionario con metadatos básicos (nombre del cliente, código de la torre).
    -   `executive_summary`: Un objeto `ExecutiveSummaryAnnex` que contiene la narrativa principal, puntuaciones y mensajes clave.
    -   `domain_introduction`: Un objeto `DomainIntroduction` con el contexto del dominio tecnológico evaluado.
    -   `pillar_score_profile`: Un objeto `MaturityScoreProfile` con los datos para el perfil de madurez por pilar, incluyendo la ruta al gráfico de radar.
    -   `sections`: El contenedor principal para todas las secciones de análisis detallado (`AnnexSections`).

### `AnnexSections` (Contenedor de Secciones)

Este modelo agrupa las diferentes partes del análisis del anexo, cada una definida en su propio sub-modelo:
-   `asis`: El análisis del estado actual (`AsIsAnnex`).
-   `tobe`: La visión del estado futuro (`ToBeAnnex`).
-   `gap`: El análisis de las brechas entre el estado actual y el futuro (`GapAnnex`).
-   `todo`: El plan de acción con las iniciativas recomendadas (`TodoAnnex`).
-   `risks`: Un resumen de los riesgos identificados (`RisksAnnex`).
-   `conclusion`: Las conclusiones y recomendaciones finales (`ConclusionAnnex`).

### Sub-Modelos y Modelos "Hoja"

Cada sección se descompone en modelos más pequeños y específicos para asegurar una alta estructuración. Por ejemplo:
-   `RisksAnnex` contiene una lista de objetos `RiskItemAnnex`.
-   `TodoAnnex` contiene una lista de objetos `InitiativeAnnex`.
-   `GapAnnex` contiene una lista de objetos `GapRowAnnex`.

Esta granularidad garantiza que los datos generados por los agentes de IA sean predecibles y consistentes.

## Rol en el Proyecto

Este fichero define el **contrato de datos canónico para el Anexo Ejecutivo**.

-   **Aplicación del Contrato:** Es el esquema que se le proporciona al agente de IA en `run_executive_annex_synthesizer.py` como el `output_schema` que debe cumplir obligatoriamente. Esto fuerza a la IA a generar una salida JSON que se adhiere perfectamente a esta estructura.
-   **Entrada para el Renderizador:** Un `AnnexPayload` válido es la entrada directa y esperada por el script `render_tower_annex_from_template.py`. El renderizador confía en que los datos tendrán esta estructura, lo que simplifica su lógica y lo hace más robusto.
-   **Desacoplamiento y Claridad:** Separa la lógica de síntesis (quién crea los datos) de la de renderizado (quién los presenta). El propio esquema sirve como una documentación clara y auto-aplicable del flujo de datos entre estas dos etapas.
