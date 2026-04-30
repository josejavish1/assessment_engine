# Documentación: `schemas/blueprint.py`

## Resumen

Este fichero define el "contrato de datos" para el artefacto más importante y detallado del sistema: el `BlueprintPayload`. Utilizando Pydantic, este módulo establece la estructura jerárquica y completa de toda la información necesaria para generar un documento "Blueprint de Torre".

## Estructura del Esquema

El fichero está compuesto por varios modelos Pydantic anidados, donde cada modelo representa una sección lógica del documento final.

### `BlueprintPayload` (Modelo Raíz)

Es el modelo principal que engloba todo el payload.
-   Hereda de `VersionedPayload` (a través de `OrchestratorBlueprintDraft`), por lo que incluye los metadatos de versionado (`_generation_metadata`).
-   Contiene dos componentes principales:
    -   `document_meta`: Un objeto `BlueprintDocumentMeta` con información general del documento (cliente, torre, etc.).
    -   `pillars_analysis`: Una lista de objetos `PillarBlueprintDraft`, que representa el núcleo del análisis técnico.
-   Además, incluye todas las secciones de alto nivel definidas en `OrchestratorBlueprintDraft`.

### `OrchestratorBlueprintDraft` (Secciones Globales)

Este modelo agrupa las secciones del blueprint que ofrecen una visión transversal, por encima de los pilares individuales.
-   `executive_snapshot`: Un `ExecutiveSnapshot` con el resumen ejecutivo.
-   `cross_capabilities_analysis`: Un `CrossCapabilitiesAnalysis` que analiza patrones y deudas técnicas comunes a varios pilares.
-   `roadmap`: Una lista de `RoadmapWave` que define el plan de transformación por fases.
-   `external_dependencies`: Una lista de `ExternalDependency` que mapea las dependencias entre proyectos.

### `PillarBlueprintDraft` (Análisis por Pilar)

Este es el modelo que define la estructura del análisis para un único pilar tecnológico (ej: Seguridad, Datos, Cloud).
-   `pilar_id`, `pilar_name`, `score`: Identificación y puntuación del pilar.
-   `health_check_asis`: Una lista de `HealthCheckAsIs` que describe el estado actual, con sus hallazgos, riesgos de negocio e impacto.
-   `target_architecture_tobe`: Un `TargetArchitectureToBe` que define la visión y los principios de diseño de la arquitectura objetivo.
-   `projects_todo`: Una lista de `ProjectToDo` con las iniciativas concretas propuestas para alcanzar el estado objetivo, incluyendo su caso de negocio, dimensionamiento y entregables.

### Otros Modelos (Hojas)

El resto de los modelos (`ExecutiveSnapshot`, `RoadmapWave`, etc.) definen los campos específicos para cada una de las sub-secciones, proporcionando una estructura granular y detallada para cada pieza de información.

## Rol en el Proyecto

Este fichero es la **definición canónica del contrato de datos del Blueprint**. Es uno de los esquemas más críticos de todo el `assessment-engine`.

-   **Fuente de Verdad:** Actúa como la única fuente de verdad sobre qué datos son necesarios para construir un blueprint. Cualquier proceso que genere o consuma estos datos debe adherirse a esta estructura.
-   **Guía para la IA y los Orquestadores:** Este esquema se utiliza para instruir a los agentes de IA sobre el formato de salida que deben producir. A su vez, los orquestadores de Python y los renderizadores de documentos lo usan para validar las entradas y procesar los datos de forma predecible.
-   **Desacoplamiento:** Permite que la lógica de generación de datos y la lógica de renderizado en el documento de Word (`render_tower_blueprint.py`) estén completamente desacopladas. Mientras el "contrato" (este esquema) se respete, ambas partes pueden evolucionar de forma independiente.
