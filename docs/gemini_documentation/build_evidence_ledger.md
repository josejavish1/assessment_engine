# Documentación: `build_evidence_ledger.py`

## Resumen

Este script es un **procesador y contextualizador de evidencias**. Su función es tomar las dos fuentes de datos en crudo del assessment (el texto del `context.txt` y las puntuaciones del `case_input.json`) y transformarlas en una lista única, estructurada y enriquecida de "evidencias". El resultado se guarda en el fichero `evidence_ledger.json`, que actúa como un "libro de contabilidad" o "dossier de pruebas" para el análisis posterior.

## Componentes Principales

### `main()`

-   **Propósito:** La función principal que orquesta la creación del "ledger".
-   **Lógica:**
    1.  Recibe las rutas a los ficheros `case_input.json`, `context.txt` y `responses.txt`.
    2.  Carga estos ficheros junto con el `tower_definition.json` correspondiente.
    3.  Llama a la función `build_evidence_entries` para procesar y transformar los datos.
    4.  Ensambla el objeto final del `evidence_ledger` y lo guarda como un fichero JSON.

### `build_evidence_entries(...)`

Esta es la función que contiene la lógica de negocio principal para la transformación de los datos.

1.  **Procesamiento de Evidencias de Contexto:**
    -   Lee el `context.txt` y lo divide en frases.
    -   Para cada pilar de la `tower_definition`, busca frases en el contexto que contengan palabras clave relevantes para ese pilar.
    -   Cada frase coincidente se convierte en una evidencia de tipo `context_summary`, etiquetada con el pilar correspondiente.

2.  **Procesamiento de Evidencias de Cuestionario:**
    -   Recorre las respuestas (puntuaciones) del `case_input.json`.
    -   Cada respuesta se convierte en una evidencia de tipo `questionnaire_response`.

3.  **Enriquecimiento Inteligente de Evidencias:**
    -   A cada evidencia, ya sea de contexto o de cuestionario, se le añade metadatos cruciales:
        -   `evidence_id`: Un identificador único.
        -   `source_type` y `source_name`: Trazabilidad hacia el fichero de origen.
        -   `excerpt`: El texto o la puntuación en sí.
        -   `pillar_ids` y `kpi_ids`: Un etiquetado preciso que asocia la evidencia con las partes de la metodología a las que afecta.
        -   **`supports`:** Este es el campo más importante. La función `support_tags_from_score` implementa una lógica de negocio clave: basándose en la puntuación de una respuesta, determina para qué secciones del informe servirá como justificación.
            -   Una **puntuación baja** (`< 3.0`) genera etiquetas como `[gap, risk, tobe, todo]`, ya que es evidencia de un problema que requiere un análisis completo.
            -   Una **puntuación alta** (`>= 4.0`) solo genera la etiqueta `[asis]`, ya que representa una fortaleza del estado actual.

## Rol en el Proyecto

Este script es un **Paso de Preparación y Pre-Análisis de Datos** fundamental en el pipeline activo.

-   **Estructurador de Información No Estructurada:** Convierte el texto libre del fichero de contexto en piezas de evidencia estructuradas y asociadas a pilares específicos.
-   **Contextualizador de Datos:** No solo copia los datos, sino que los enriquece con un contexto vital (a qué pilar/KPI pertenecen) y un pre-análisis (para qué secciones del informe son relevantes).
-   **Habilitador para la IA:** El `evidence_ledger.json` que produce es una entrada de gran valor para los agentes de IA posteriores (como el `run_evidence_analyst.py`). En lugar de tener que procesar los ficheros en crudo, la IA recibe un "dossier de pruebas" ya organizado y clasificado, lo que le permite generar análisis más consistentes y basados en evidencias.
-   **Trazabilidad:** Al crear un registro de cada pieza de información con un ID único y una referencia a su origen, mejora la trazabilidad y la auditabilidad del análisis final.
