# Documentación: `schemas/commercial.py`

## Resumen

Este módulo define los esquemas Pydantic para el `CommercialPayload` y sus componentes asociados, que juntos forman el "Account Action Plan". Su diseño es un reflejo directo del sistema multi-agente que lo genera (`run_commercial_refiner.py`). No solo define la estructura del artefacto final, sino también los **contratos de datos para la salida de cada agente de IA especializado** que participa en el proceso.

## Estructura del Esquema

### `CommercialPayload` (Modelo Raíz)

Es el modelo principal que representa la totalidad del `commercial_report_payload.json`.
-   Hereda de `VersionedPayload` para incluir metadatos de trazabilidad.
-   Agrega los resultados finales del proceso de refinamiento comercial:
    -   `commercial_summary`: El resumen de alto nivel del acuerdo.
    -   `gtm_strategy`: La estrategia Go-To-Market.
    -   `opportunities_pipeline`: La lista de oportunidades de venta calificadas.
    -   `proactive_proposals`: Una lista de borradores de propuestas de venta detalladas.
    -   `intelligence_dossier`: Un diccionario para metadatos adicionales, como los blueprints que se usaron como fuente.

### Esquemas de Salida para Agentes de IA

Esta es la parte más característica del módulo. Cada uno de los siguientes modelos es el `output_schema` que se le exige a un agente de IA específico, definiendo así su responsabilidad y el formato de su entregable.

-   **`AccountDirectorOutput`:** El contrato para el agente "Global Account Director", que debe producir el resumen, la estrategia GTM y el mapa de stakeholders.
-   **`PresalesArchitectOutput`:** El contrato para el agente "Enterprise Presales Architect", que debe entregar el pipeline de oportunidades.
-   **`EngagementManagerOutput`**, **`LeadSolutionsArchitectOutput`**, **`DeliveryAndRiskDirectorOutput`**, y **`SalesPartnerOutput`:** Un conjunto de contratos para los cuatro agentes especializados que colaboran en la construcción de una única propuesta de venta. Cada esquema define una pieza del puzzle (el porqué, el cómo, los riesgos, el cierre, etc.).

### `ProposalDraft` (Esquema Agregador)

Este es un modelo de datos complejo que sirve como la plantilla para una propuesta de venta completa. Su estructura está diseñada para agregar las salidas de los cuatro agentes especializados en propuestas en un único documento coherente. Es el esquema que permite al sub-orquestador `build_proactive_proposal` ensamblar el resultado final.

## Rol en el Proyecto

Este fichero es el **Contrato de Datos para el Sistema Comercial Multi-Agente**. Su función va más allá de definir un simple payload.

-   **Definición de Responsabilidades de Agentes:** Los esquemas `*Output` actúan como "descripciones de puesto" para cada agente de IA, estableciendo claramente qué se espera de ellos.
-   **Habilitador de la Orquestación:** La existencia de estos esquemas granulares es lo que permite al `run_commercial_refiner.py` orquestar un flujo de trabajo complejo, sabiendo qué pedir a cada agente y cómo combinar sus respuestas validadas.
-   **"Contract-First" a Nivel de Agente:** Aplica el principio de "Contrato Primero" no solo al resultado final, sino a cada paso intermedio del proceso de refinamiento, imponiendo estructura y previsibilidad en un sistema inherentemente creativo.
-   **Documentación del Flujo de Trabajo:** La propia estructura de los esquemas sirve como una documentación clara de la división de tareas y el flujo de información entre los diferentes roles de IA que componen el "equipo" comercial.
