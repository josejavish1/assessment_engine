# Documentación: `run_evidence_analyst.py`

## Resumen

Este script actúa como un **primer analista automático, no basado en IA**. Su función es tomar todos los datos pre-procesados (`case_input.json`, `evidence_ledger.json`, `scoring_output.json`) y, aplicando un conjunto de reglas de negocio y heurísticas deterministas, generar un borrador estructurado de los "hallazgos" del assessment. El resultado de su ejecución es el fichero `findings.json`.

Este script no escribe narrativa compleja, sino que genera "frases plantilla" y estructuras de datos que sirven como un **andamio o esqueleto** para los agentes de IA "escritores" en las fases posteriores del pipeline.

## Componentes Principales

### `main()`

-   **Propósito:** Orquesta la ejecución del análisis.
-   **Lógica:** Carga todos los ficheros de datos necesarios (`case_input`, `evidence_ledger`, `scoring_output` y `tower_definition`) y los pasa a la función `build_findings` para su procesamiento. Finalmente, guarda el resultado.

### `build_findings(...)`

Esta es la función central que contiene la lógica de negocio para el pre-análisis.

1.  **Análisis por Pilar (Basado en Reglas):**
    -   Itera sobre cada pilar tecnológico definido en la metodología.
    -   **Clasificación de Fortalezas/Debilidades:** Para cada KPI dentro del pilar, mira su puntuación. Si es `>= 3`, lo clasifica como una fortaleza; si es `< 3`, como una debilidad (`gap`). Para cada uno, genera una frase estándar utilizando funciones de plantilla como `strength_statement()` y `gap_statement()`.
    -   **Definición de Capacidades Objetivo:** Utiliza la función `capability_phrase()`, que es un conjunto de reglas `if/elif/else`, para seleccionar una descripción predefinida de la capacidad objetivo basándose en palabras clave en el nombre del KPI.
    -   **Propuesta de Iniciativas:** Si la puntuación general de un pilar es baja, genera automáticamente una "iniciativa candidata" con un título genérico (ej: "Programa de mejora para {nombre del pilar}") y una prioridad calculada a partir de la puntuación.

2.  **Generación de Resumen y "Claims":**
    -   **Mensajes Clave:** Identifica el pilar con la puntuación más alta y el más bajo para generar mensajes clave para el resumen ejecutivo (ej: "La mayor fortaleza está en X", "La mayor brecha se concentra en Y").
    -   **Afirmaciones Aprobadas (`approved_claims_for_writer`):** Para cada pilar, crea una lista de afirmaciones objetivas y basadas en datos (ej: "El pilar de Ciberseguridad se sitúa en Nivel 2 con score 2.5"). Estas son frases que la IA podrá usar directamente en su narrativa con la certeza de que son correctas.

3.  **Ensamblaje del `findings.json`:**
    -   Toda la información generada (análisis por pilar, resumen, etc.) se ensambla en una única estructura JSON, el `findings.json`.

## Rol en el Proyecto

Este script es el **Generador de Andamiaje Analítico**.

-   **Puente entre Datos y Narrativa:** Es el paso intermedio crucial que traduce los datos cuantitativos (`scoring`) y las evidencias (`ledger`) en una primera estructura de análisis cualitativo.
-   **Proveedor de "Material de Construcción" para la IA:** El `findings.json` que produce no es un entregable final, sino una entrada de alto valor para los agentes de IA posteriores (como el `run_tower_blueprint_engine`). En lugar de enfrentarse a los datos en crudo, la IA recibe un borrador pre-analizado, lo que reduce su carga cognitiva y le permite centrarse en tareas de mayor nivel como la redacción de una narrativa coherente.
-   **Codificación de Heurísticas de Negocio:** Es el lugar donde se codifican reglas de negocio y conocimiento de experto de forma determinista (ej: qué constituye una fortaleza, qué frase usar para una capacidad objetivo).
-   **Mejora de la Consistencia:** Al proporcionar un esqueleto común y afirmaciones ya validadas, ayuda a que los resultados generados por la IA sean más consistentes y estén mejor anclados a los datos originales.
