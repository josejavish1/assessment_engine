# Documentación: `prompts/conclusion_prompts.py`

## Resumen

Este módulo define las plantillas de prompts para los agentes de IA responsables de generar y revisar la **sección de Conclusión** de un informe de torre. Esta es la sección de cierre que debe sintetizar todo el análisis previo y entregar un mensaje final claro y ejecutivo. El módulo sigue el patrón de IA de "Writer + Reviewer" (Escritor + Revisor).

## Componentes Principales

### Agente "Writer" (Escritor)

-   **`get_conclusion_writer_prompt(...)`:**
    -   **Rol:** Actuar como el agente Escritor, especializado en la síntesis final del informe.
    -   **Tarea Principal:** Redactar la sección de Conclusión. Es una de las tareas más exigentes en cuanto a contexto, ya que el prompt le proporciona **todas las secciones anteriores del informe** como entrada: `SCORING`, `ASIS`, `RISKS`, `TOBE`, `GAP` y `TODO`.
    -   **Salida Esperada:** El prompt le exige un JSON que estructura la conclusión en varias partes clave:
        1.  **`final_assessment`:** Un párrafo con la valoración final sobre el estado de la torre.
        2.  **`executive_message`:** El mensaje clave o "bottom line" destinado a la dirección.
        3.  **`priority_focus_areas`:** Una lista de las áreas que requieren atención prioritaria.
        4.  **`closing_statement`:** Un párrafo de cierre que refuerce el mensaje principal.
    -   **Reglas Cruciales:** La regla más importante es que **"la conclusión debe sintetizar el mensaje ejecutivo final"**. Se le prohíbe simplemente repetir información ya vista; su trabajo es elevar el análisis a una conclusión estratégica, dejando claro "el punto de partida, la brecha dominante y la dirección de evolución".

### Agente "Reviewer" (Revisor)

-   **`get_conclusion_reviewer_prompt(...)`:**
    -   **Rol:** Actuar como el agente Revisor, especializado en validar la calidad de la síntesis final.
    -   **Tarea Principal:** Revisar el borrador de la Conclusión para asegurar que es un cierre coherente y de alto impacto para el informe.
    -   **Criterios de Revisión:** La revisión se centra en la síntesis y la utilidad:
        -   ¿Es la conclusión consistente con todas las secciones anteriores?
        -   ¿Aporta una **utilidad ejecutiva real** o es un simple resumen?
        -   ¿El mensaje final es claro y está bien argumentado?
        -   ¿Evita introducir afirmaciones nuevas o no respaldadas por el análisis previo?
    -   **Salida Esperada:** Un JSON con el veredicto (`status`: "approve", "revise") y una lista de defectos con sugerencias de corrección.

## Rol en el Proyecto

Este fichero es el **Motor de Síntesis Ejecutiva**.

-   **Cierre de la Narrativa:** Su función es asegurar que el informe de cada torre termine con una conclusión potente y coherente, en lugar de simplemente terminar después de la última sección de análisis.
-   **Garantía de Valor:** El agente Revisor, con su foco en la "utilidad ejecutiva real", actúa como un guardián para evitar conclusiones genéricas o poco impactantes, forzando a que el resultado final aporte valor tangible.
-   **Visión Holística (a Nivel de Torre):** El agente Escritor, al recibir todas las secciones como contexto, está programado para realizar una síntesis holística, conectando los puntos entre los riesgos, las brechas y las iniciativas propuestas.
-   **Punto Final del Análisis de Torre:** La generación de esta sección representa la culminación del proceso de análisis para una torre individual, antes de que los datos pasen a los pipelines de agregación global o comercial.
