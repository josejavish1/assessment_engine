# Documentación: `prompts/gap_prompts.py`

## Resumen

Este módulo contiene las plantillas de prompts para los agentes de IA responsables de generar y revisar la sección de "GAP Analysis". Esta sección es una de las más importantes del informe, ya que articula la brecha entre el estado actual de la tecnología del cliente y el estado objetivo recomendado, explicando las implicaciones de negocio de dicha brecha. El módulo implementa el patrón de IA de "Writer + Reviewer" (Escritor + Revisor) para esta tarea.

## Componentes Principales

### Agente "Writer" (Escritor)

-   **`get_gap_writer_prompt(...)`:**
    -   **Rol:** Actuar como el agente Escritor del motor de assessment.
    -   **Tarea Principal:** Redactar la sección de GAP Analysis para una torre tecnológica específica. La función clave de esta sección es explicar la diferencia entre el "AS-IS" (estado actual) y el "TO-BE" (estado objetivo) para cada pilar tecnológico.
    -   **Entradas:** Recibe un contexto muy rico, incluyendo los hallazgos (`findings`), las puntuaciones (`scoring`), el análisis AS-IS y el análisis TO-BE, y la definición metodológica de la torre.
    -   **Salida Esperada:** Debe producir un JSON que contenga una introducción y una lista de `gap_items`. Cada `gap_item` debe detallar, por pilar:
        1.  Un resumen del estado actual (`as_is_summary`).
        2.  Una descripción del estado objetivo (`target_state`).
        3.  La brecha clave que los separa (`key_gap`).
        4.  La **implicación operativa** de esa brecha (`operational_implication`), que es el dato de mayor valor de esta sección.
    -   **Reglas Cruciales:** Se le ordena explícitamente que no invente información y que base su análisis únicamente en los datos de entrada proporcionados. También se le prohíbe convertir esta sección en un roadmap o plan de proyecto.

### Agente "Reviewer" (Revisor)

-   **`get_gap_reviewer_prompt(...)`:**
    -   **Rol:** Actuar como el agente Revisor del motor de assessment.
    -   **Tarea Principal:** Revisar la calidad y consistencia del borrador de la sección GAP generado por el Writer.
    -   **Criterios de Revisión:** El prompt le da una lista de verificación muy clara:
        -   ¿Es consistente con los hallazgos y el scoring?
        -   ¿Es coherente con los análisis AS-IS y TO-BE?
        -   ¿Se ha inventado alguna brecha o implicación?
        -   ¿La calidad del texto es profesional?
    -   **Salida Esperada:** No debe reescribir el texto. Su salida es un JSON con un veredicto (`status`: "approve", "revise", o "human_validation_required") y una lista estructurada de "defectos" (`defects`), cada uno con su severidad, tipo, mensaje y una sugerencia de corrección.
    -   **Reglas Cruciales:** Debe usar la definición de la torre como la "fuente de verdad metodológica" y no aplicar criterios externos.

## Rol en el Proyecto

Este fichero es el **Cerebro del Análisis de Brechas**.

-   **Generador de Insights:** Define el proceso por el cual el sistema transforma el análisis descriptivo (AS-IS, TO-BE) en un análisis prescriptivo y de valor (la brecha y, sobre todo, su impacto en el negocio).
-   **Aplicación de la Lógica de Negocio:** Las instrucciones en estos prompts "programan" a la IA para que realice un análisis de causa y efecto que es fundamental para el propósito del assessment.
-   **Garantía de Consistencia:** El agente Revisor actúa como una red de seguridad automatizada, asegurando que esta sección tan crítica no se contradiga con los datos objetivos presentados en las secciones anteriores del informe.
-   **Especialización de Tareas de IA:** Es un claro ejemplo de cómo se utilizan agentes de IA muy especializados para tareas concretas (análisis de GAP) dentro de un pipeline más grande, en lugar de usar un único agente monolítico.
