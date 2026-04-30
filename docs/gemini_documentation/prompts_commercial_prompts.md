# Documentación: `prompts/commercial_prompts.py`

## Resumen

Este módulo define las instrucciones y las plantillas de prompts para el **ecosistema de agentes de IA comerciales**. Este fichero es, en esencia, un "manual de ventas" codificado en lenguaje natural. Su propósito es guiar a los agentes de IA para que no solo analicen la información técnica, sino que razonen y actúen como un equipo de ventas y consultoría estratégica de alto nivel de NTT DATA, produciendo un "Account Action Plan" que sea realista, accionable y alineado con las prácticas comerciales de la empresa.

## Componentes Principales

### Bases de Conocimiento (Knowledge Bases)

El fichero empieza definiendo dos bloques de texto que actúan como una base de conocimiento para los agentes. Esto asegura que la IA no "alucine" información comercial crítica.

-   **`REFERENCE_CATALOG`:**
    -   **Propósito:** Es un catálogo de precios y tiempos de entrega (`TCV - Total Contract Value`).
    -   **Contenido:** Proporciona rangos de costes y duraciones estándar para diferentes tipos de proyectos (ej: "Migración Cloud Landing Zone: 2-4 meses, 80k€ - 150k€").
    -   **Función:** Obliga a los agentes a basar sus estimaciones financieras en datos realistas y predefinidos, aportando consistencia y credibilidad a las propuestas.

-   **`NTTDATA_WIN_THEMES`:**
    -   **Propósito:** Es un listado de los diferenciadores y fortalezas de NTT DATA.
    -   **Contenido:** Resume los "temas ganadores" o los argumentos de venta clave para diferentes áreas (ej: "Ciberseguridad: Red Global de SOCs, inteligencia de amenazas propia").
    -   **Función:** Proporciona a la IA el material para construir la sección "Por qué NTT DATA" de las propuestas, asegurando que el mensaje esté alineado con la estrategia corporativa.

### Instrucciones y Prompts

-   **`get_commercial_orchestrator_instruction()`:**
    -   **Personalidad:** Establece el marco mental para todo el equipo de IAs: "Eres un ecosistema de agentes de Ventas, Arquitectura y Riesgos...".
    -   **Reglas de Oro Estratégicas:** Codifica la sabiduría de un consultor senior:
        1.  **Priorización Estratégica:** Ordena a la IA que priorice las iniciativas regulatorias (DORA, NIS2) por encima de todo, reflejando las presiones del mundo real en los clientes.
        2.  **Lenguaje de Impacto:** Exige que la IA se comunique en términos de impacto de negocio, no de mejoras técnicas.
        3.  **Estrategia Pragmática:** Instruye a la IA para que adapte la solución a la madurez del cliente ("Brilliant Basics" para los inmaduros, no venderles "AIOps" de inmediato).

-   **`get_commercial_agent_prompt(...)`:**
    -   **Tarea:** Es la plantilla genérica que se usa para dar una instrucción específica a cada agente del equipo (ej: `GLOBAL ACCOUNT DIRECTOR`).
    -   **Refuerzo de Reglas:** Vuelve a inyectar las bases de conocimiento (`REFERENCE_CATALOG`, `NTTDATA_WIN_THEMES`) en cada llamada para que la IA no las olvide.
    -   **Reglas de Redacción Estrictas:** Impone un estilo de escritura muy específico (prohibido el uso de guiones largos o punto y coma) para forzar un tono directo, conciso y profesional.

## Rol en el Proyecto

Este fichero es el **Playbook Estratégico de Ventas para la IA**.

-   **Codificación del "Saber Hacer" Comercial:** Transforma el conocimiento tácito de un equipo de ventas (precios, tácticas, argumentos) en instrucciones explícitas que una IA puede ejecutar.
-   **Anclaje en la Realidad (Grounding):** El uso de catálogos y temas predefinidos es una técnica de "grounding" muy potente, que limita la capacidad de la IA para inventar información y la ancla a los datos de negocio reales.
-   **Alineamiento Estratégico:** Garantiza que la estrategia comercial generada por la IA no sea solo técnicamente sólida, sino que también esté alineada con las prioridades de negocio (regulación, madurez del cliente) y con el posicionamiento de mercado de NTT DATA.
-   **Motor de la Estrategia Accionable:** Es el componente que convierte el análisis en un plan de acción comercial tangible, el paso final y de mayor valor en el pipeline.
