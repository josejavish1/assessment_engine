# Documentación: `prompts/todo_prompts.py`

## Resumen

Este módulo define las plantillas de prompts para los agentes de IA responsables de generar y revisar la **sección "TO-DO"**. Esta es la sección del plan de acción, donde el análisis de las secciones anteriores se traduce en un conjunto de iniciativas concretas y priorizadas. Es el paso final para convertir el diagnóstico en una recomendación accionable. Se mantiene el patrón de IA de "Writer + Reviewer" (Escritor + Revisor).

## Componentes Principales

### Agente "Writer" (Escritor)

-   **`get_todo_writer_prompt(...)`:**
    -   **Rol:** Actuar como el agente Escritor, especializado en la creación de planes de acción.
    -   **Tarea Principal:** Redactar la sección TO-DO. Recibe como contexto todas las secciones de análisis previas (`AS-IS`, `TO-BE`, `GAP`, etc.) para poder proponer un plan de acción coherente.
    -   **Salida Esperada:** El prompt le exige un JSON que contenga una lista de `todo_items`. Cada ítem representa una iniciativa y debe estar estructurado con campos clave:
        1.  **`initiative`:** El nombre de la iniciativa (ej: "Implementar un plan de Disaster Recovery").
        2.  **`objective`:** El objetivo que persigue esta acción.
        3.  **`priority`:** Su nivel de prioridad (Alta, Media o Baja).
        4.  **`related_pillars`:** Los pilares tecnológicos a los que afecta.
        5.  **`expected_outcome`:** El resultado tangible que se espera obtener.
        6.  **`dependencies`:** Otras iniciativas o condiciones de las que depende.
    -   **Reglas Cruciales:** La regla fundamental es que **"las iniciativas deben ser creíbles, accionables y directamente trazables a los gaps"**. Esto asegura que el plan de acción no contenga recomendaciones genéricas, sino soluciones específicas para los problemas detectados. También se le prohíbe crear un "roadmap temporal detallado", enfocándose en la priorización en lugar de la calendarización.

### Agente "Reviewer" (Revisor)

-   **`get_todo_reviewer_prompt(...)`:**
    -   **Rol:** Actuar como el agente Revisor, especializado en validar la lógica y la calidad del plan de acción.
    -   **Tarea Principal:** Revisar el borrador de la sección TO-DO.
    -   **Criterios de Revisión:** La revisión se centra en la trazabilidad y la coherencia:
        -   **Trazabilidad:** ¿Cada iniciativa propuesta se corresponde con una brecha real identificada en la sección GAP?
        -   **Coherencia:** ¿La prioridad asignada a cada iniciativa es lógica en función del análisis de riesgos y gaps?
        -   **Calidad:** ¿Están bien definidos el objetivo y el resultado esperado?
        -   **Cumplimiento de Reglas:** ¿Se ha evitado incluir un calendario detallado?
    -   **Salida Esperada:** Un JSON con el veredicto (`status`: "approve", "revise") y una lista de defectos con sugerencias de corrección.

## Rol en el Proyecto

Este fichero es el **Motor de Planificación y Acción**.

-   **Traducción de Análisis a Acción:** Su función principal es cerrar el ciclo del análisis, convirtiendo los problemas (identificados en AS-IS y GAP) en un plan de soluciones concretas (TO-DO).
-   **Garantía de Trazabilidad:** El proceso de escritura y revisión definido en estos prompts fuerza a que el plan de acción esté lógicamente conectado con el diagnóstico. Esto es vital para la credibilidad del informe.
-   **Priorización Inteligente:** Guía a la IA para que no solo liste acciones, sino que también aplique un nivel de juicio estratégico al asignarles una prioridad.
-   **Foco en el "Qué", no en el "Cuándo":** La prohibición de crear roadmaps detallados en esta fase es una decisión de diseño importante. Mantiene esta sección enfocada en definir las iniciativas, dejando la planificación temporal detallada para el `Blueprint` o el `Informe Global`.
