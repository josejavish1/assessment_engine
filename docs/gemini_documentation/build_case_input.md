# Documentación: `build_case_input.py`

## Resumen

Este script es el punto de partida del pipeline de `assessment-engine`. Su responsabilidad es recoger múltiples ficheros de entrada en crudo (respuestas del cliente en formatos como `.docx` o `.rtf`, documentos de contexto, definiciones de la torre) y consolidarlos en un único fichero JSON estructurado: `case_input.json`. Este fichero sirve como la entrada principal para las siguientes fases del proceso de assessment.

## Componentes Principales

### `main()`

Es la función de entrada que se ejecuta desde la línea de comandos. Utiliza `argparse` para procesar los argumentos necesarios:
-   `--client`: Nombre del cliente.
-   `--tower`: El ID de la torre tecnológica a evaluar (ej: "T5").
-   `--context-file`: Ruta al documento de contexto del cliente.
-   `--responses-file`: Ruta al fichero con las respuestas del cliente a las preguntas del assessment.

### `build_case_input(args)`

Es la función central que orquesta la construcción del objeto `case_input`.

**Flujo de trabajo:**
1.  **Carga la Definición de la Torre:** Lee el fichero `tower_definition_{TOWER}.json` que contiene toda la estructura de la torre: pilares, KPIs y preguntas.
2.  **Extrae las Respuestas:** Lee el fichero de respuestas del cliente. Utiliza funciones auxiliares para extraer texto plano de distintos formatos (`.docx`, `.rtf`, `.txt`).
3.  **Parsea las Puntuaciones:** Utiliza una expresión regular para encontrar y extraer las puntuaciones de cada pregunta (ej: "T5.P1.K1.PR1: 4.5") del texto extraído.
4.  **Consolida y Enriquece:** Cruza las puntuaciones parseadas con la definición de la torre para crear una lista estructurada de "respuestas", añadiendo el texto completo de la pregunta, el nombre del pilar, etc.
5.  **Recopila Metadatos:** Agrega una gran cantidad de metadatos al fichero, como un `case_id` único, el nombre del cliente, la fecha, la lista de documentos fuente y las "reglas de trabajo" (criterios de puntuación) de la torre.
6.  **Integra Inteligencia de Cliente:** Intenta leer un fichero `client_intelligence.json` para obtener una puntuación de madurez objetivo específica para esa torre y cliente.
7.  **Genera el JSON:** Devuelve un único diccionario con toda la información consolidada, listo para ser guardado como `case_input.json`.

### Funciones de Extracción de Texto

-   **`read_docx_text`, `read_rtf_text`, `read_text`:** Un conjunto de utilidades que permiten al script manejar diferentes formatos de fichero para las respuestas del cliente, haciendo el proceso de ingesta más flexible.

## Rol en el Proyecto

Este script cumple la función de **Ingesta y Consolidación de Datos**. Es el primer eslabón de la cadena de procesamiento.

-   **Punto de Entrada:** "Arranca" el proceso de assessment al crear el `case_input.json` inicial.
-   **Normalización:** Abstrae la complejidad de los diferentes formatos de fichero de entrada. El resto del pipeline no necesita saber cómo leer un `.docx`; solo necesita consumir el `case_input.json` normalizado.
-   **Enriquecimiento:** No se limita a copiar los datos, sino que enriquece las puntuaciones en crudo con el contexto completo de la torre, preparando los datos para que sean más fáciles de procesar por los agentes de IA.
-   **Desacoplamiento:** Separa limpiamente la lógica de "parseo" de la lógica de "análisis". Esto hace que el núcleo del motor de assessment sea más limpio y se enfoque únicamente en su tarea principal, sin preocuparse por los detalles de la ingesta de datos.
