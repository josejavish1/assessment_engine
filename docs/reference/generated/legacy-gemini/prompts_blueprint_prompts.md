# Documentación: `prompts/blueprint_prompts.py`

## Resumen

Este módulo define las plantillas de prompts para el **equipo de agentes de IA** responsable de generar el `BlueprintPayload`, el artefacto de análisis técnico más detallado y fundamental del proyecto. Este fichero es el núcleo del motor `run_tower_blueprint_engine.py` y codifica las instrucciones para los tres roles de IA que colaboran en el proceso: el Arquitecto, el Crítico y el Orquestador de Cierre.

Una característica de diseño clave de este módulo es que **carga el contenido de los prompts desde ficheros de configuración YAML externos** (ubicados en `prompts/registry/`) mediante la función `load_prompt_config`. Esto permite modificar las instrucciones de la IA sin necesidad de cambiar el código Python, facilitando enormemente el mantenimiento y la experimentación.

## Componentes Principales

### Agente "Blueprint Architect" (Arquitecto de Pilar)

-   **`get_blueprint_architect_instruction()`:** Define la personalidad general del agente: un "Arquitecto de Soluciones Enterprise" experto en una materia, cuya misión es traducir datos en un plan de transformación accionable.
-   **`get_pilar_architect_prompt(...)`:** Construye la tarea para el análisis de un pilar individual.
    -   **Contexto:** Se le proporciona un contexto muy rico que incluye el ADN estratégico del cliente, el contexto de negocio, y lo más importante, las respuestas detalladas del cliente para ese pilar.
    -   **Tarea:** Debe generar un borrador completo del análisis para ese pilar, incluyendo el estado actual (`health_check_asis`), la visión futura (`target_architecture_tobe`) y las iniciativas concretas para cerrar la brecha (`projects_todo`).
    -   **Reglas:** Se le exige que cada iniciativa esté justificada por los hallazgos y que no invente información.

### Agente "Critic" (Crítico Revisor)

-   **`get_critic_prompt(...)`:**
    -   **Rol:** Actúa como el revisor de calidad del borrador generado por el Arquitecto.
    -   **Tarea:** Recibe el JSON del Arquitecto y se le instruye para que lo "depure" y refine.
    -   **Objetivos de Revisión Clave:**
        1.  Eliminar afirmaciones vagas o redundantes.
        2.  Asegurar la coherencia entre el AS-IS, el TO-BE y el TO-DO.
        3.  Verificar que cada iniciativa (`project_todo`) responde a un problema real identificado en el AS-IS.
    -   **Salida:** Debe devolver el JSON final corregido, manteniendo la misma estructura.

### Agente "Closing Orchestrator" (Orquestador de Cierre)

-   **`get_closing_orchestrator_prompt(...)`:**
    -   **Rol:** Actúa como el "Arquitecto Jefe" que tiene la visión de conjunto.
    -   **Contexto:** A diferencia de los otros agentes, este recibe el análisis ya completado y revisado de **todos los pilares**.
    -   **Tarea:** Su misión es realizar un análisis transversal. Debe leer los análisis de todos los pilares y, a partir de ellos, sintetizar las secciones globales del Blueprint:
        -   El Resumen Ejecutivo (`executive_snapshot`).
        -   El Análisis de Capacidades Transversales.
        -   El Roadmap de Ejecución.
        -   Las Decisiones Ejecutivas requeridas.
    -   **Reglas:** Se le dan instrucciones claras sobre la estructura y el tono que deben tener estas secciones de alto nivel.

## Rol en el Proyecto

Este fichero es el **Cerebro del Motor de Análisis Técnico**.

-   **Generador de Contenido Primario:** Es el responsable de definir cómo se crea el contenido más detallado y valioso de todo el pipeline: el `BlueprintPayload`.
-   **Implementación del "Equipo de IAs":** Codifica el patrón de IA colaborativa (Arquitecto -> Crítico -> Orquestador) que busca asegurar la coherencia y calidad del análisis.
-   **Desacoplamiento de Prompts y Código:** El uso de ficheros YAML externos es una práctica de ingeniería de prompts avanzada que hace que el sistema sea más modular y fácil de mantener.
-   **"Prompt Chaining" Implícito:** El flujo de trabajo que define (el resultado de un agente es la entrada del siguiente) es una forma de "prompt chaining", donde se construyen análisis complejos a través de una secuencia de pasos más simples y especializados.
