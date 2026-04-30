# Documentación: `prompts/section_prompts.py`

## Resumen

Este módulo define plantillas de prompts **genéricas y configurables** para los agentes de IA que generan y revisan secciones del informe que siguen un patrón similar, como la sección "AS-IS" (estado actual) o la de "Riesgos". En lugar de tener una función de prompt dedicada para cada sección, este módulo utiliza un enfoque de "fábrica" donde una única función puede generar el prompt para diferentes secciones basándose en un objeto de configuración.

## Componentes Principales

### `get_section_writer_prompt(...)`

-   **Rol:** Actúa como una fábrica de prompts para cualquier agente de IA "Escritor" de secciones.
-   **Parametrización:** Su comportamiento se define por los parámetros que recibe:
    -   `section_cfg`: Un diccionario de configuración que contiene la descripción de la tarea del escritor y las reglas específicas para la sección que se está generando (ej. "AS-IS").
    -   `document_profile`: Un perfil de documento que puede incluir una lista de **frases prohibidas** (`forbidden_phrases`) para esa sección en particular. Esta es una potente herramienta de control de calidad.
    -   `corrective_feedback`: Una lista opcional de correcciones. Si se proporciona, el prompt instruye explícitamente a la IA para que corrija los defectos de una versión anterior y genere una nueva. Esto habilita un **ciclo de revisión y corrección automatizado**.
-   **Estructura de Salida Forzada:** El prompt incluye bloques de texto con la estructura JSON exacta que la IA debe devolver, una técnica para reducir las "alucinaciones" de formato del modelo.

### `get_section_reviewer_prompt(...)`

-   **Rol:** Actúa como una fábrica de prompts para cualquier agente de IA "Revisor" de secciones.
-   **Parametrización:** Al igual que el escritor, recibe un objeto `section_cfg` que contiene la descripción de su trabajo y, lo más importante, una lista de los puntos a verificar (`review_checks`). Esto permite que el mismo prompt se adapte para revisar diferentes secciones con diferentes criterios.
-   **Salida Esperada:** La salida es el formato estándar de revisión, con un veredicto (`status`) y una lista de defectos estructurados.

## Flujo de Trabajo y Conceptos Clave

Este módulo implementa algunos de los conceptos más avanzados de ingeniería de prompts del proyecto:

1.  **Prompts Basados en Configuración:** El uso de un diccionario `section_cfg` para definir el comportamiento de los prompts es una decisión de diseño clave. Permite añadir nuevas secciones al pipeline que sigan este patrón (como una futura sección de "Seguridad") simplemente creando un nuevo fichero de configuración, sin necesidad de modificar este fichero de prompts. Esto hace que el sistema sea más extensible y mantenible.

2.  **Ciclo de Feedback Correctivo:** La existencia del parámetro `corrective_feedback` es la evidencia de un bucle de calidad iterativo. El flujo de trabajo implícito es:
    a.  El **Writer** genera una primera versión (`draft`).
    b.  El **Reviewer** la revisa y, si encuentra errores, genera una lista de `defects`.
    c.  El sistema vuelve a llamar al **Writer**, esta vez pasando los `defects` como `corrective_feedback`.
    d.  El **Writer** genera una segunda versión corregida.

3.  **Control de Calidad Dinámico:** El uso de `forbidden_phrases` cargadas desde un perfil de documento permite un control de calidad muy granular y adaptable. Se pueden definir diferentes reglas de estilo para diferentes tipos de informes o clientes.

## Rol en el Proyecto

Este fichero es la **Fábrica de Prompts de Secciones Reutilizables**.

-   **Reutilización y DRY (Don't Repeat Yourself):** Evita la duplicación de código de prompts que se vio en los ficheros más específicos. Centraliza la lógica de construcción de prompts para un patrón común.
-   **Extensibilidad:** Facilita la adición de nuevas secciones al proceso de generación de informes.
-   **Motor del Ciclo de Calidad Iterativo:** Proporciona el mecanismo de "feedback" que permite al sistema no solo generar contenido, sino también refinarlo automáticamente basándose en una revisión de calidad.
