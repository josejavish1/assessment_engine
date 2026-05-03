---
status: "Verified"
owner: "product-engineering"
last_verified_against: "2026-05-03"
applies_to:
  - humans
  - ai-agents
source_of_truth:
  - src/assessment_engine/scripts/run_tower_blueprint_engine.py
  - src/assessment_engine/schemas/blueprint.py
doc_type: "operational"
---

# Proceso de Remediación de Coherencia en Assessments

Este documento describe la política y el proceso para identificar y corregir las incoherencias en los documentos generados por el motor de assessment.

## 1. Política de Coherencia

**La coherencia entre todos los artefactos de un assessment es un requisito no negociable.**

Cualquier discrepancia, contradicción o falta de alineamiento entre los distintos documentos generados (ej. `Annex`, `Blueprint`, `CIO Report`) se considera un **defecto de alta prioridad (`P0`)**, ya que impacta directamente en la credibilidad y el valor del producto.

La arquitectura del sistema, basada en el principio "Top-Down", está diseñada para prevenir este tipo de errores. La única fuente de verdad es el `blueprint_Txx_payload.json`. Todos los demás artefactos se derivan de él.

## 2. Proceso de Detección y Remediación

### Paso 1: Detección

La incoherencia puede ser detectada durante:
-   Las revisiones de calidad internas (Quality Gates).
-   La validación por parte del Product Owner.
-   El feedback del cliente final.

**Ejemplos de incoherencia:**
-   Una puntuación numérica en una tabla no se corresponde con la descripción cualitativa en el texto.
-   Un gráfico (`radar_chart.png`) muestra un resultado que contradice el análisis del `CIO_Ready_Report.docx`.
-   Un `finding` clave mencionado en el anexo no aparece en el informe global.

### Paso 2: Análisis de Causa Raíz

Una vez detectada una incoherencia, el objetivo es encontrar su origen en el pipeline de generación.

1.  **Verificar la Fuente de Verdad:** Inspeccionar el `blueprint_Txx_payload.json` relevante.
    -   **Si el payload es correcto:** El error reside en uno de los scripts de *renderizado* (ej. `render_tower_annex.py`, `render_global_report.py`). El script está interpretando o proyectando mal los datos del payload.
    -   **Si el payload es incorrecto:** El error reside en el núcleo del motor de análisis (`run_tower_blueprint_engine.py`) o en un script *preparatorio* (`run_scoring.py`, `build_case_input.py`, etc.).

### Paso 3: Corrección

**La corrección NUNCA debe realizarse manualmente sobre los documentos de salida (`.docx`, `.html`).**

La solución debe aplicarse en el código fuente del script que ha originado el error.

1.  **Crear un Test de Regresión:** Antes de corregir, se debe crear un test que replique la incoherencia. Este test debe fallar inicialmente.
2.  **Corregir el Código:** Modificar el script erróneo para que la lógica de generación sea la correcta.
3.  **Verificar la Solución:** Ejecutar el test de regresión, que ahora debe pasar. Regenerar el assessment completo y verificar que la incoherencia ha desaparecido en todos los artefactos.

## 3. Racional: ¿Por qué este proceso es innegociable?

Este riguroso proceso de remediación no es burocrático; es el sistema inmunitario que protege el valor y la credibilidad de nuestro producto. Un assessment es una herramienta para la toma de decisiones estratégicas, y la coherencia interna de los datos es la base de su fiabilidad.

### Riesgos que Mitiga

1.  **Pérdida de Confianza del Cliente:** Un informe con datos contradictorios (ej. un gráfico que dice "riesgo alto" y un texto que dice "riesgo bajo") destruye la credibilidad del assessment y de nuestra marca. El cliente no puede confiar en los resultados para tomar decisiones.

2.  **Toma de Decisiones Erróneas:** El cliente podría basar decisiones de negocio o de inversión en una pieza de información incorrecta, creyendo que es la correcta. Esto puede tener consecuencias financieras o estratégicas negativas, generando un riesgo de responsabilidad para nosotros.

3.  **Deuda Técnica por "Hot-Fixing":** Corregir manualmente un error en un documento `.docx` es un parche de corto plazo que genera una deuda técnica masiva. En la siguiente ejecución del motor, el error volverá a aparecer, creando un ciclo de revisiones manuales insostenible y propenso a errores.

### Valor Estratégico

*   **Producto de Calidad Industrial:** Un proceso formal y automatizado para garantizar la coherencia nos permite escalar la producción de assessments manteniendo un nivel de calidad constante y predecible.

*   **Defensa del Diseño "Single Source of Truth":** Este proceso refuerza la arquitectura "Top-Down", que es nuestra ventaja competitiva. Al forzar que las correcciones se hagan en la fuente (`blueprint`) o en la lógica de renderizado, protegemos el núcleo del sistema contra la entropía y la inconsistencia.

*   **Eficiencia y Escalabilidad:** Arreglar la causa raíz es una inversión. Aunque el coste inicial es mayor que un parche manual, el retorno es un sistema más robusto que no requiere intervención manual en cada ejecución, liberando al equipo para trabajar en mejoras de mayor valor.
