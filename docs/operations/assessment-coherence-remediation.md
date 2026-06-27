---
status: Verified
owner: product-engineering
source_of_truth:
- ../../src/assessment_engine/application/run_tower_blueprint_engine.py
- ../../src/assessment_engine/domain/schemas/blueprint.py
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: operational
diataxis: how_to
verification_mode: workflow
---
# Proceso de Remediación de Coherencia en Assessments

Este documento describe la política, el protocolo y los procedimientos operativos requeridos para identificar, aislar y subsanar inconsistencias lógicas o semánticas transversales en los artefactos del assessment generados por el motor.

## 1. Política de Coherencia Semántica

**La coherencia semántica y consistencia lógica transversal entre todos los artefactos generados en un ciclo de evaluación constituye un requerimiento estructural no negociable del motor.**

Cualquier discrepancia, divergencia métrica o fragmentación narrativa (*split-brain*) entre los entregables de distinta audiencia (p. ej., `Annex_Txx.docx`, `Blueprint_Txx.docx`, `Account_Action_Plan_<client>.docx`) se clasifica de forma inmediata como un **defecto de criticidad máxima (`P0`)**, dado que compromete de manera directa la integridad del diagnóstico estratégico y la defendibilidad del sistema.

La arquitectura del sistema, gobernada por principios de flujo determinista *Top-Down*, está diseñada para anular la aparición de estas derivas. La interfaz `blueprint_<tower>_payload.json` constituye la única fuente de verdad canónica del sistema. Los artefactos ulteriores representan proyecciones o derivaciones directas y estrictamente acopladas a este payload de origen.

## 2. Protocolo de Detección, Aislamiento y Remediación

### Paso 1: Detección e Identificación
La presencia de derivas lógicas o inconsistencias semánticas puede ser identificada a través de:
-   Los controles automatizados de las compuertas de calidad (*Quality Gates* o CI).
-   El proceso de validación técnica del Product Owner.
-   La revisión y control de calidad editorial de los entregables de cuenta.

**Desviaciones Típicas Catalogadas:**
-   **Incoherencia Cualitativa-Cuantitativa:** Puntuaciones numéricas calculadas en las tablas de scoring que no se corresponden con el rango cualitativo o la banda de madurez expresada en la narrativa directiva.
-   **Deriva Visual:** Gráficos radar u otros recursos visuales generados automáticamente que contradicen la volumetría o aserciones técnicas del reporte consolidado.
-   **Fragmentación de Iniciativas:** Iniciativas prioritarias detalladas en el anexo que omiten su correspondencia lógica o difieren en alcance dentro del plan de transformación global o comercial.

### Paso 2: Análisis de Causa Raíz
Una vez detectada una desviación, se debe ejecutar un análisis determinista sobre la tubería de datos (*data pipeline*) para identificar la capa de origen del defecto:

1.  **Auditoría de la Fuente de Verdad:** Inspeccionar el payload canónico `blueprint_<tower>_payload.json` de la torre correspondiente:
    -   **Causa Estética (Presentación):** Si el payload es correcto, el defecto reside exclusivamente en el script compilador o renderizador (p. ej., `render_tower_annex_from_template.py`, `render_global_report_from_template.py`), el cual está proyectando incorrectamente el modelo de datos.
    -   **Causa de Dominio (Cómputo/Lógica):** Si el payload es incorrecto, el defecto se origina en el motor de análisis y síntesis (`run_tower_blueprint_engine.py`) o en sus módulos preparatorios deterministas (`run_scoring.py`, `build_case_input.py`, etc.).

### Paso 3: Remediación en Caliente

**Queda terminantemente prohibida la manipulación manual directa sobre los documentos y entregables físicos de salida (`.docx`, `.html` u otros).**

La subsanación debe aplicarse de forma permanente sobre las abstracciones de código o de datos del motor:

1.  **Codificación de Caso de Prueba de Regresión:** Antes de corregir el defecto, se debe codificar un caso de prueba unitaria o aserción en `tests/` que replique la inconsistencia exacta. El test debe fallar inicialmente (*Red State*).
2.  **Modificación Quirúrgica del Código:** Refactorizar el componente del motor o renderer responsable de la desviación, de modo que se resuelva la causa raíz de forma tipada y determinista.
3.  **Certificación y Cierre:** Ejecutar la suite de pruebas unitarias para certificar la transición exitosa del test de regresión a verde (*Green State*). Regenerar el andamiaje completo de los artefactos del assessment y verificar la homogeneidad de los datos.

## 3. Justificación Operativa de la Inmutabilidad del Flujo

Este proceso formal de remediación no representa una carga administrativa; constituye el mecanismo de protección estructural de la calidad, valor y reproducibilidad de los diagnósticos tecnológicos de la plataforma.

### Mitigación de Riesgos Críticos

1.  **Vulneración de la Credibilidad Estratégica:** Informes contradictorios (p. ej., un gráfico radar indicando un estado crítico "Inicial" junto a un bloque de texto que describe un estado "Alineado") destruyen la confiabilidad del assessment, inhabilitándolo como herramienta sólida para la toma de decisiones del cliente.
2.  **Inducción a Inversiones Erróneas:** El cliente podría guiar sus planes de inversión técnica o adquisiciones sobre datos inconsistentes, exponiendo a la organización a derivas financieras o responsabilidades de cumplimiento regulatorio indeseadas.
3.  **Entropía de Parcheo (*Hot-Fixing Drift*):** Subsanar manualmente un error sobre un documento OpenXML compilado constituye un parche transitorio. En la siguiente ejecución del motor, la inconsistencia resurgirá, arrastrando ciclos infinitos de correcciones manuales no reproducibles.

### Atribuciones de Valor de Ingeniería

*   **Calidad de Escala Industrial:** Un flujo estricto de remediación garantiza que el motor mantenga un estándar de calidad homogéneo, permitiendo automatizar de manera confiable la generación masiva de assessment deliverables.
*   **Blindaje del Principio "Single Source of Truth":** La observancia del flujo *Top-Down* asegura que el sistema permanezca robusto y libre de entropías. Al forzar que cada corrección ocurra en la fuente canónica o en la lógica estricta de renderizado, se protege la cohesión semántica global del repositorio.
*   **Eficiencia en el Retorno de Inversión:** Depurar la causa raíz e incorporar el caso de prueba de regresión representa una inversión en estabilidad. Mitiga costos futuros de mantenimiento y dota al equipo de un entorno seguro para evolucionar las capacidades del motor.
