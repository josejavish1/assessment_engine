# Documentación: `build_global_report_payload.py`

## Resumen

Este script funciona como un **agregador global**. Su misión es escanear el directorio de un cliente, encontrar todos los `BlueprintPayload` de las diferentes torres tecnológicas, y consolidar la información más relevante de cada uno en un único fichero de alto nivel: `global_report_payload.json`. Este payload global es la base para generar el informe final destinado al CIO, que ofrece una visión panorámica de todo el estado tecnológico del cliente.

## Componentes Principales

### `main()`

Es la función de entrada que se ejecuta desde la línea de comandos, aceptando tres argumentos:
1.  La ruta al directorio de trabajo del cliente.
2.  El nombre del cliente.
3.  La ruta del fichero de salida donde se guardará el `global_report_payload.json`.

### `build_global_payload(client_dir, client_name)`

Es la función principal que contiene toda la lógica de agregación y consolidación.

**Flujo de trabajo:**
1.  **Descubrimiento de Ficheros:** Busca en los subdirectorios de cada torre (ej: `T1/`, `T5/`) los ficheros `blueprint_*_payload.json`. De forma crucial, también busca ficheros más antiguos (`approved_annex_*.refined.json`) para usarlos como *fallback*, garantizando la retrocompatibilidad.
2.  **Procesamiento Priorizado:** Itera sobre los ficheros encontrados, dando siempre prioridad a los `BlueprintPayload` más nuevos. Si para una torre solo existe un fichero antiguo, lo procesa en su lugar.
3.  **Extracción de Datos Clave:** De cada fichero de torre, extrae la información más estratégica:
    *   La puntuación media de madurez y su banda cualitativa.
    *   El mensaje principal del resumen ejecutivo (`bottom_line`).
    *   Los riesgos estratégicos más importantes.
    *   Las iniciativas de transformación clave (`projects_todo`).
    *   Principios de arquitectura y otras implicaciones.
4.  **Agregación y Síntesis:** Una vez procesadas todas las torres, consolida los datos:
    *   Calcula una puntuación media de madurez global.
    *   Crea una lista maestra con los riesgos estratégicos más críticos de todo el ecosistema.
    *   Compila una lista unificada con las iniciativas más importantes.
    *   Elimina duplicados y limita el número de elementos en ciertas listas para que el informe global sea conciso y enfocado.
5.  **Construcción del Payload Final:** Ensambla toda esta información agregada en la estructura del `global_report_payload`, con secciones para el resumen ejecutivo, un mapa de calor (`heatmap`) del estado de las torres, los riesgos, las iniciativas, etc.

## Rol en el Proyecto

Este script es el **Agregador Global** del sistema. Se sitúa en un nivel alto del flujo "Top-Down", justo por encima de los análisis de las torres individuales.

-   **Visión Holística:** Su función principal es romper los silos de información de cada torre para crear una vista unificada y estratégica del panorama tecnológico del cliente.
-   **Elevación de la Información:** Transforma datos tácticos y detallados (extraídos de los blueprints) en un resumen estratégico de alto nivel, adecuado para la toma de decisiones por parte de la alta dirección (CIO).
-   **Retrocompatibilidad:** La capacidad de procesar tanto los nuevos blueprints como los antiguos anexos refinados hace que el sistema sea robusto y permite una migración gradual de las torres al nuevo formato sin interrumpir la generación de informes globales.
-   **Alimentador de Informes Finales:** El `global_report_payload.json` que produce es la entrada directa para el script que renderiza el documento final `.docx` del informe para el CIO.
