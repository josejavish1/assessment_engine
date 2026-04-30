# Documentación: `run_section_pipeline.py` (Arquitectura Legacy)

## Resumen

Este script es el **orquestador del pipeline de generación de secciones de la arquitectura "legacy" (heredada)**. Su propósito es generar una única sección del informe (como "AS-IS" o "Riesgos") de forma aislada, utilizando un sofisticado **ciclo iterativo de Escritura-Revisión-Corrección** entre agentes de IA para asegurar una alta calidad del contenido.

Este script representa cómo funcionaba el sistema antes de la transición a la arquitectura "Top-Down". Aunque ha sido mayormente reemplazado, su lógica de control de IA es una de las más avanzadas del proyecto y es fundamental para entender la evolución del sistema.

## Componentes Principales

### `main()` y `_run_section_logic(...)`

La función `main` es el punto de entrada, que recibe como argumento qué sección generar (`asis` o `risks`). La lógica principal reside en `_run_section_logic`, una función asíncrona que orquesta el ciclo de calidad.

### Ciclo de Calidad Iterativo (Bucle de Escritura-Revisión)

El núcleo del script es un bucle `for` que se ejecuta un número máximo de "rondas de revisión". Dentro de este bucle, ocurre el siguiente proceso:
1.  **Generación del Borrador (Writer):**
    -   Se invoca a un agente "Writer" con el prompt correspondiente (construido desde `section_prompts.py`).
    -   Si la primera versión del borrador no es estructuralmente válida (falla la validación de Pydantic), el sistema reintenta la generación varias veces.
    -   Si hay "feedback correctivo" de una ronda anterior, se inyecta en el prompt para guiar al Writer.

2.  **Revisión del Borrador (Reviewer):**
    -   El borrador válido se pasa a un agente "Reviewer".
    -   El Reviewer evalúa el borrador y devuelve un veredicto (`status`) y una lista de defectos.

3.  **Normalización de la Revisión (`normalize_review`):**
    -   Se aplica un conjunto de reglas de negocio para "normalizar" el veredicto. Por ejemplo, si el `status` es `revise` pero todos los defectos son de severidad `minor`, el estado se cambia automáticamente a `approve` para evitar iteraciones innecesarias por problemas menores.

4.  **Decisión de Flujo:**
    -   Si el estado es `approve`, el ciclo termina. El borrador se considera "aprobado" y se guarda. La función `finalize_approved` puede incluso aplicar autocorrecciones editoriales menores (`editorial_autofix`).
    -   Si el estado es `revise`, se extrae el feedback de la revisión (`build_corrective_feedback`) y el bucle vuelve a empezar, pasando este feedback al Writer.

5.  **Mecanismo de Escape (Convergencia Forzada):**
    -   Si el bucle alcanza el número máximo de rondas sin llegar a un `approve`, el sistema asume que no va a converger.
    -   En este caso, se **fuerza la aprobación** del último borrador. La función `force_approve_review` modifica el veredicto y `inject_manual_revision_note` añade una nota al contenido indicando que "requiere ajuste manual pendiente", para no detener todo el pipeline por una única sección.

## Rol en el Proyecto

Este script es el **Orquestador del Ciclo de Calidad de la Arquitectura Heredada**.

-   **Documentación Histórica:** Es la pieza clave para entender la arquitectura original del `assessment-engine`, que se basaba en generar las piezas del informe en paralelo y de forma aislada.
-   **Motor de Calidad Iterativo:** Implementa el patrón de IA más sofisticado del proyecto para el refinamiento de contenido, simulando un proceso de revisión por pares y corrección.
-   **Causa del Cambio a "Top-Down":** Aunque buscaba una alta calidad por sección, su naturaleza aislada es la razón por la que se migró a la arquitectura "Top-Down". Generar `AS-IS` y `TO-BE` por separado podía llevar a un `GAP` incoherente, un problema de "split-brain" que el flujo centrado en el Blueprint resuelve.
-   **Componente Reutilizable:** Aunque el orquestador principal ya no lo usa, la lógica de este script (especialmente el bucle de revisión y la normalización) es un patrón muy valioso que podría reutilizarse en futuros pipelines.
