# Documentación: `lib/review_resilience.py`

## Resumen

Este módulo es una librería de utilidades que proporciona las **herramientas de resiliencia** para el ciclo de revisión de la arquitectura "legacy" (orquestado por `run_section_pipeline.py`). Su propósito es gestionar los resultados del agente Revisor de IA y manejar los casos en los que el ciclo de calidad no converge, asegurando que el pipeline pueda continuar sin quedarse bloqueado.

## Componentes Principales

### `build_corrective_feedback(review: dict) -> list[str]`

-   **Propósito:** Traducir el objeto JSON de revisión, que es estructurado y complejo, en una lista simple de instrucciones en lenguaje natural para el agente Escritor.
-   **Lógica:**
    1.  Toma el objeto `review` como entrada.
    2.  Extrae los mensajes de la lista de `defects` y de la lista de `approval_conditions`.
    3.  Concatena la información relevante de cada defecto (tipo, mensaje, sugerencia) en una única frase.
    4.  Devuelve una lista de cadenas de texto, donde cada cadena es una instrucción clara y accionable.
-   **Rol:** Actúa como el **traductor** entre el lenguaje estructurado del Revisor y el lenguaje de instrucción que necesita el Escritor para la siguiente ronda de corrección.

### `force_approve_review(review: dict, reason: str) -> dict`

-   **Propósito:** Forzar el estado de una revisión a "aprobado" cuando el ciclo de calidad no converge.
-   **Lógica:**
    1.  Toma un objeto de revisión.
    2.  Cambia el valor del campo `status` a `"approve"`.
    3.  Añade una cadena de texto (`reason`) a la lista de `review_notes` para dejar constancia de por qué se forzó la aprobación.
-   **Rol:** Es el **mecanismo de escape** del bucle de revisión. Garantiza que el pipeline no se detenga indefinidamente si los agentes de IA no se ponen de acuerdo.

### `inject_manual_revision_note(draft: dict, review: dict, note_field: str) -> dict`

-   **Propósito:** Inyectar una nota de advertencia directamente en el contenido de un borrador cuando se ha forzado su aprobación.
-   **Lógica:**
    1.  Toma el último `draft` y la `review` que causó el atasco.
    2.  Usa `build_corrective_feedback` para obtener un resumen del problema principal.
    3.  Construye una frase de advertencia, como "Nota de revisión pendiente: este contenido... requiere ajuste manual posterior. [Resumen del problema]".
    4.  Añade esta frase al final del campo de texto especificado por `note_field` (ej: "executive_narrative").
-   **Rol:** Es el **mecanismo de señalización**. Asegura que, aunque el pipeline continúe, los problemas de calidad no resueltos no se pierdan, sino que queden marcados en el propio contenido para que un humano los pueda identificar y corregir fácilmente en la etapa final.

## Rol en el Proyecto

Este módulo es el **Kit de Herramientas de Resiliencia para el Ciclo de Calidad Heredado**.

-   **Habilitador de la Iteración:** La función `build_corrective_feedback` es lo que hace posible el ciclo de revisión-corrección, al permitir que la salida de un agente se convierta en la entrada del otro.
-   **Prevención de Bloqueos:** Las funciones `force_approve_review` e `inject_manual_revision_note` son cruciales para la robustez del pipeline "legacy". Garantizan que el proceso siempre termine, incluso si no se alcanza la calidad perfecta de forma automática.
-   **Trazabilidad de Problemas:** La inyección de notas asegura que los problemas de convergencia de la IA no se "pierdan por el camino", sino que se transmitan de forma visible hasta el producto final, facilitando la intervención humana.
-   **Componente de la Arquitectura Legacy:** Estas herramientas son intrínsecas al funcionamiento del `run_section_pipeline.py` y son una de las razones por las que ese orquestador, aunque heredado, es tan sofisticado.
