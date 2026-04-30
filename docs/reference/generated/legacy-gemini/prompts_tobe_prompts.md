# Documentación: `prompts/tobe_prompts.py`

## Resumen

Este módulo contiene las plantillas de prompts para los agentes de IA responsables de generar y revisar la sección **"TO-BE"**, que define el **estado futuro objetivo**. Esta sección es la visión estratégica del informe, donde se articula cómo debería ser la arquitectura, las capacidades y la operativa del cliente para alcanzar un nivel de madurez óptimo. Se mantiene el patrón de IA de "Writer + Reviewer" para esta tarea.

## Componentes Principales

### Agente "Writer" (Escritor)

-   **`get_tobe_writer_prompt(...)`:**
    -   **Rol:** Actuar como el agente Escritor del motor de assessment, especializado en la visión de futuro.
    -   **Tarea Principal:** Redactar la sección TO-BE. La IA debe sintetizar la información de los hallazgos, el scoring y la definición metodológica para proponer una visión de futuro coherente y valiosa.
    -   **Salida Esperada:** El prompt le exige un JSON estructurado que contenga:
        1.  **`target_maturity`:** Una definición del nivel de madurez objetivo recomendado (por defecto, "Nivel 4 - Optimizado"), una puntuación de referencia y una justificación de por qué se recomienda ese nivel.
        2.  **`target_capabilities_by_pillar`:** Una lista detallada, pilar por pilar, de las capacidades que el cliente debería desarrollar para alcanzar ese estado futuro.
        3.  **`architecture_principles`:** Los principios de arquitectura que deben guiar la transformación.
        4.  **`operating_model_implications`:** Las consecuencias que este cambio tendrá en la forma de operar del cliente.
    -   **Reglas Cruciales:** Las instrucciones son muy claras en prohibir que esta sección se convierta en un plan de proyecto. Se le ordena que **no hable de roadmaps, quick wins ni horizontes temporales**. El TO-BE es el **"qué"** y el **"porqué"**, no el "cómo" ni el "cuándo". Además, se le exige que la visión sea "creíble, no utópica".

### Agente "Reviewer" (Revisor)

-   **`get_tobe_reviewer_prompt(...)`:**
    -   **Rol:** Actuar como el agente Revisor, especializado en validar la visión estratégica.
    -   **Tarea Principal:** Revisar el borrador de la sección TO-BE generado por el Writer.
    -   **Criterios de Revisión:** La lista de verificación se centra en la credibilidad y la coherencia:
        -   ¿Es la visión TO-BE una respuesta lógica a los hallazgos y al scoring?
        -   ¿Es el estado objetivo propuesto creíble y alcanzable?
        -   ¿Se ha colado algún elemento de planificación (roadmap, quick wins)?
        -   ¿La calidad del texto es profesional y ejecutiva?
    -   **Salida Esperada:** Un JSON con el veredicto (`status`: "approve", "revise") y una lista de defectos con sugerencias de corrección.

## Rol en el Proyecto

Este fichero define el **Motor de Visión Estratégica** de la IA.

-   **Establecimiento de la "Estrella del Norte":** Su función es definir la dirección hacia la que debe apuntar todo el plan de transformación. Es la parte del informe que le dice al cliente "así es como deberías ser".
-   **Separación de Visión y Planificación:** Las reglas estrictas que prohíben hablar de roadmaps son un elemento arquitectónico clave. Forzar a la IA a separar la "visión" (TO-BE) del "plan" (que se detallará en la sección TO-DO) asegura una estructura clara y lógica en el informe final.
-   **Fundamento para el Análisis de Brechas:** La visión TO-BE generada aquí es una de las entradas fundamentales para el análisis de la sección GAP. Sin un TO-BE claro, es imposible medir la brecha.
-   **Alineamiento con la Metodología:** La regla de que el TO-BE debe apuntar por defecto al Nivel 4 asegura el alineamiento con la metodología de madurez subyacente del assessment.
