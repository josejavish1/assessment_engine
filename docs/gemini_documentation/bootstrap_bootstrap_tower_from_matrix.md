# Documentación: `bootstrap/bootstrap_tower_from_matrix.py`

## Resumen

Este script es una herramienta de **"bootstrapping" o inicialización de torres tecnológicas**. Su única función es leer y analizar un documento de Word (`.docx`), conocido como la "Matriz de Madurez", y extraer de él toda la información necesaria para generar automáticamente el fichero de configuración `tower_definition_Txx.json`. Este fichero JSON es la "fuente de verdad" metodológica que el `assessment-engine` utiliza para evaluar una torre específica.

Este script es, en esencia, un **analizador sintáctico ("parser") de documentos de Word no asistido por IA**, que utiliza una combinación de extracción de XML, expresiones regulares y lógica de normalización de texto para convertir un documento legible por humanos en un artefacto de datos estructurado y legible por máquinas.

## Componentes Principales

El script es un pipeline de extracción de datos complejo y secuencial.

### 1. Extracción de Texto (`extract_docx_paragraphs`)

-   **Acción:** Descomprime el fichero `.docx`, accede al `word/document.xml` interno y extrae el contenido de todos los párrafos, convirtiéndolos en una lista de cadenas de texto limpias. Esta es la materia prima para todo el proceso.

### 2. Funciones de Extracción (`extract_*`)

El núcleo del script es un conjunto de funciones, cada una especializada en encontrar y extraer una pieza específica de información del texto, utilizando expresiones regulares (`regex`) para buscar patrones.
-   `extract_tower_name`: Busca el nombre de la torre.
-   `extract_purpose`: Encuentra la descripción del propósito de la torre.
-   `build_pillar_name_map`: Localiza las definiciones de los pilares y sus IDs (ej: "T5.P1").
-   `extract_weights`: Busca la sección "Factores de Importancia" para extraer el peso porcentual de cada pilar.
-   `extract_kpis`: Encuentra los KPIs (Key Performance Indicators) y sus nombres.
-   `extract_questions`: Localiza las preguntas de evaluación asociadas a cada KPI.

### 3. Ensamblaje y Validación

-   **`build_tower_definition`:** Una vez que todas las piezas de información han sido extraídas, esta función las ensambla en la estructura jerárquica final del `tower_definition.json` (Preguntas dentro de KPIs, KPIs dentro de Pilares, etc.).
-   **`validate_tower_definition`:** Antes de guardar el resultado, esta función realiza una serie de comprobaciones de sanidad críticas para asegurar la integridad del fichero generado. Por ejemplo:
    -   Verifica que no haya IDs duplicados.
    -   Comprueba que la suma de los pesos de los pilares sea exactamente 100.
    -   Asegura que cada KPI y cada pregunta estén asociados a un pilar válido.

### 4. Generación de Manifiesto (`build_manifest`)

-   Junto con el fichero de definición, el script genera un `bootstrap_manifest.json`. Este fichero contiene metadatos sobre el proceso de extracción, como el nombre del fichero de origen, la fecha, un resumen de los datos extraídos (nº de pilares, KPIs, etc.) y una lista de **advertencias (`warnings`)** sobre cualquier anomalía detectada durante el proceso (ej: "No se pudo encontrar el nombre para el KPI T5.P1.K3").

## Rol en el Proyecto

Este script es una **Herramienta de Productividad y Habilitación Metodológica**.

-   **Automatización de la Configuración:** Su rol principal es automatizar la creación de la configuración de una nueva torre. Permite a los expertos en la materia (que no son necesariamente programadores) definir la metodología de una torre en un formato familiar como es un documento de Word.
-   **Puente entre Humanos y Máquinas:** Actúa como un traductor, convirtiendo un documento semi-estructurado legible por humanos en el formato JSON estrictamente estructurado que el software necesita.
-   **Reducción de Errores:** Al automatizar este proceso, se reduce drásticamente la posibilidad de errores manuales de copiar y pegar al crear el fichero JSON, y la función de validación asegura la calidad del resultado.
-   **Mantenimiento de la Metodología:** Facilita la actualización y el mantenimiento de las metodologías de las torres, ya que los cambios se pueden hacer en el documento maestro de Word y luego "re-compilar" el fichero de configuración con este script.
