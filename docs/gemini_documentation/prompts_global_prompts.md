# Documentación: `prompts/global_prompts.py`

## Resumen

Este módulo define las "personalidades" (instrucciones) y las plantillas de prompts para los agentes de IA que realizan tareas de revisión y refinamiento a nivel **global y ejecutivo**. Estos agentes no trabajan sobre los datos de una única torre, sino sobre el informe consolidado que las agrupa, y su principal objetivo es asegurar la calidad, coherencia y el tono estratégico del entregable final.

## Componentes Principales

El fichero define un par de funciones (`get_*_instruction` y `get_*_prompt`) para cada uno de los roles de IA. La **instrucción** establece la "personalidad" o el rol del agente, mientras que el **prompt** construye la tarea específica que debe realizar, combinando la instrucción con los datos de entrada.

### Agente "Global Reviewer"

-   **`get_global_reviewer_instruction()`:**
    -   **Personalidad:** "Eres un editor senior especializado en QA y revisión de calidad de informes ejecutivos...".
    -   **Objetivo:** Actuar como un agente de control de calidad. No corrige, solo detecta.
-   **`get_global_reviewer_prompt(...)`:**
    -   **Tarea:** Le pide al agente que revise el documento completo en busca de problemas transversales como incoherencias, duplicidades, contradicciones, problemas de tono y repeticiones.
    -   **Reglas Clave:** Le prohíbe explícitamente reescribir el documento o inventar defectos. Su única salida debe ser un JSON que indique si el documento se aprueba (`approve`) o necesita revisión (`revise`), junto con una lista de los problemas encontrados.

### Agente "Global Refiner"

-   **`get_global_refiner_instruction()`:**
    -   **Personalidad:** "Eres un editor senior especializado en refinamiento...".
    -   **Objetivo:** Mejorar el documento basándose en los hallazgos del Reviewer.
-   **`get_global_refiner_prompt(...)`:**
    -   **Tarea:** Le pide al agente que, si el estado de la revisión es "revise", proponga ediciones para solucionar los problemas.
    -   **Reglas Clave:** Le exige que las ediciones sean "quirúrgicas" y se devuelvan en un formato similar a JSONPatch (`path`, `action`, `value`). Le prohíbe cambiar datos objetivos (como puntuaciones) y le instruye a centrarse en mejorar la redacción y la coherencia.

### Agente "Executive Refiner"

-   **`get_executive_refiner_instruction()`:**
    -   **Personalidad:** "Eres un Senior Partner de consultoría estratégica de TI redactando un informe para el Board."
    -   **Objetivo:** Elevar el nivel del contenido a una calidad apta para la más alta dirección.
-   **`get_executive_section_prompt(...)`:**
    -   **Tarea:** Generar una nueva sección estratégica del informe (por ejemplo, el resumen ejecutivo).
    -   **Reglas Clave (Muy Estrictas):** Este prompt contiene las reglas de estilo más importantes del proyecto:
        -   **Prohibido usar la primera persona del plural** ("nuestro", "hemos detectado") para mantener un tono objetivo y externo.
        -   **Prohibido usar códigos internos** (T1, T2, etc.), exigiendo que se hable de los dominios por su nombre ("Ciberseguridad", "Redes").
        -   **Foco absoluto en el impacto de negocio** (Riesgo, P&L, Time-to-Market).

## Rol en el Proyecto

Este fichero es el **Manual de Estilo y Comportamiento para los Agentes de Calidad y Estrategia**.

-   **Codificación de la Calidad:** En lugar de escribir código Python para revisar la calidad, se "programa" a los agentes de IA a través de estas instrucciones para que realicen esa tarea.
-   **División de Responsabilidades:** Implementa un patrón de IA de "Separación de Tareas" (Reviewer vs. Refiner) que es análogo a los procesos de revisión por pares en humanos, buscando mejorar la objetividad y la calidad.
-   **Control del Tono:** Es el mecanismo principal para controlar el tono, el lenguaje y el estilo de los entregables de más alto nivel, asegurando que se alineen con los estándares de una consultora estratégica.
-   **Flexibilidad:** Permite cambiar drásticamente el comportamiento de la revisión o el estilo de redacción simplemente modificando estas instrucciones en lenguaje natural, sin necesidad de alterar la lógica del orquestador de Python.
