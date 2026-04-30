# Documentación: `schemas/common.py`

## Resumen

Este fichero define los modelos (esquemas) de Pydantic que son comunes y reutilizables a lo largo de todo el proyecto `assessment-engine`. Sirve como la base para los "contratos de datos", asegurando que las diferentes partes del sistema se comuniquen de forma consistente y predecible.

## Componentes Principales

### `VersionMetadata` y `VersionedPayload`

Estos dos modelos son cruciales para la trazabilidad y la observabilidad del sistema.

-   **`VersionMetadata`:** Define la estructura de los metadatos que acompañan a cada artefacto de datos. Incluye:
    -   `artifact_type`: El tipo de artefacto (ej: "blueprint_payload").
    -   `artifact_version`: La versión del esquema del artefacto.
    -   `source_version`: La versión del artefacto del que se originó (ej: la versión del `Blueprint` que se usó para crear un `Annex`).
    -   `timestamp_utc`: La fecha y hora de generación.
    -   `run_id`: Un identificador único para la ejecución del pipeline.
-   **`VersionedPayload`:** Es un modelo base muy simple del que deben heredar otros payloads. Su única función es añadir el campo `_generation_metadata` (que contiene un objeto `VersionMetadata`) a cualquier artefacto que lo necesite.

### `BaseDraftModel`

Es un modelo base para cualquier sección de un documento que se considere un "borrador".

-   **`validate_forbidden_phrases`:** Su característica más importante es un validador que permite a las clases que hereden de ella definir una lista de "frases prohibidas". El validador revisará automáticamente todos los campos de texto del objeto y lanzará un error si encuentra alguna de estas frases. Esta es una herramienta potente para el control de calidad automático, evitando que la IA use textos de placeholder (ej: "Lorem Ipsum", "TODO") o frases no deseadas en la versión final.

### `Defect` y `SectionReview`

Estos modelos definen un formato estructurado para la revisión de secciones, probablemente para un futuro sistema de validación con intervención humana.

-   **`Defect`:** Representa un único error o defecto encontrado en una sección, con su severidad, tipo, mensaje y una sugerencia de corrección.
-   **`SectionReview`:** Agrupa el estado de la revisión de una sección (`aprobado`, `requiere revisión`, etc.), una evaluación general y una lista de `Defect`s.

## Rol en el Proyecto

Este fichero es uno de los pilares del principio de diseño **"Contract-First"** (El Contrato Primero). Proporciona los bloques de construcción fundamentales para los contratos de datos que se utilizan en todo el pipeline.

-   **Consistencia:** Asegura que todos los artefactos principales compartan la misma estructura para metadatos, facilitando su seguimiento y depuración.
-   **Control de Calidad:** Ofrece mecanismos, como el validador de frases prohibidas, para automatizar la calidad de los contenidos generados por la IA.
-   **Reusabilidad:** Centraliza la definición de estas estructuras de datos, evitando la duplicación de código y asegurando que todos los componentes del sistema "hablen el mismo idioma".
