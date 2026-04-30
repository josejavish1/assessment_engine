# Documentación: `lib/editorial_autofix.py`

## Resumen

Este módulo es un **corrector editorial automático no supervisado**. Su propósito es identificar y corregir pequeños defectos de estilo y ortografía (principalmente tildes en español) en los textos generados por la IA. Funciona como una herramienta de "autocorrección" que se aplica cuando el agente Revisor detecta únicamente problemas menores de tipo editorial, evitando así una nueva y costosa ronda de revisión por parte de la IA.

## Componentes Principales

### `EDITORIAL_REPLACEMENTS`

-   **Propósito:** Es un diccionario que actúa como la **base de conocimiento** del corrector.
-   **Contenido:** Mapea palabras comunes en español sin tilde a su versión correctamente acentuada (ej: `"tecnico": "técnico"`).
-   **Función:** Es la lista de "buscar y reemplazar" que se aplicará sobre el texto.

### `should_autofix_editorial(defects: list[dict]) -> bool`

-   **Propósito:** Es la función de **decisión**. Determina si es seguro y apropiado aplicar la autocorrección.
-   **Lógica:**
    1.  Recibe la lista de `defects` generada por el agente Revisor.
    2.  Itera sobre cada defecto y comprueba dos condiciones:
        a.  Que la `severity` del defecto sea `"minor"`.
        b.  Que el `type` o `message` del defecto contenga palabras clave como "ortografía", "editorial" o "estilo".
    3.  Devuelve `True` **solo si todos los defectos** cumplen ambas condiciones. Si hay un solo defecto que sea `major` o que no sea de tipo editorial, devuelve `False`.
-   **Rol:** Actúa como un guardián de seguridad, asegurando que la autocorrección solo se aplique a problemas de bajo riesgo y para los que está diseñada, evitando modificar textos por razones de contenido o estructura.

### `apply_editorial_autofix(draft: dict) -> tuple[dict, int]`

-   **Propósito:** Es la función de **ejecución**. Aplica las correcciones al borrador.
-   **Lógica:**
    1.  Recibe el objeto `draft` (el borrador de la sección).
    2.  Llama a una función interna `_walk` que recorre **recursivamente** toda la estructura del JSON (diccionarios, listas y cadenas).
    3.  Cuando encuentra una cadena de texto, aplica todas las reglas de reemplazo definidas en `EDITORIAL_REPLACEMENTS`.
    4.  Devuelve el `draft` completamente corregido y un contador con el número total de reemplazos realizados.

## Rol en el Proyecto

Este módulo es una **Herramienta de Eficiencia y Calidad Automatizada**.

-   **Aumento de la Eficiencia:** Su principal rol es evitar una costosa llamada adicional a la IA (una nueva ronda de corrección del Escritor) para solucionar problemas triviales como las tildes. Esto acelera el pipeline y reduce costes.
-   **Mejora de la Calidad del Texto:** Asegura un nivel básico de calidad ortográfica y de estilo en los textos, corrigiendo los errores más comunes de los LLMs al escribir en español.
-   **Parte del Ciclo de Calidad "Legacy":** Es una pieza clave en la lógica de `normalize_review` dentro del `run_section_pipeline.py`. Cuando un `review` se normaliza de `revise` a `approve` porque solo contiene defectos menores, este módulo es el que se encarga de que esos defectos menores se solucionen de todas formas.
-   **Enfoque Pragmático:** Representa un enfoque pragmático para el control de calidad: en lugar de aspirar a la perfección a través de la IA, se identifican problemas simples y se solucionan con reglas deterministas, reservando la IA para las tareas más complejas.
