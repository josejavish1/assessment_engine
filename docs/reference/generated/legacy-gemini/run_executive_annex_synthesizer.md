# Documentación: `run_executive_annex_synthesizer.py`

## Resumen

Este script es un orquestador que implementa el principio arquitectónico "Top-Down" del sistema. Su función principal es leer un `BlueprintPayload` (el documento técnico detallado) y utilizar un agente de IA para sintetizar y generar un `AnnexPayload`, que es un resumen ejecutivo conciso y orientado a negocio.

## Componentes Principales

### `synthesize_annex(client_name, tower_id)`

Esta es la función principal que orquesta todo el flujo de trabajo de I/O (entrada/salida).

**Pasos:**
1.  **Resolución de Rutas:** Construye las rutas a los ficheros necesarios: el `BlueprintPayload` de entrada, la inteligencia de cliente, el gráfico de radar y el `AnnexPayload` de salida.
2.  **Carga de Datos:** Lee el `BlueprintPayload` de forma robusta utilizando `robust_load_payload`. También carga la configuración del agente desde un fichero YAML y los datos de inteligencia del cliente.
3.  **Llamada a la Lógica Principal:** Invoca a la función `generate_synthesis` para realizar el trabajo de síntesis con la IA.
4.  **Guardado de Resultados:** Si la síntesis es exitosa, guarda el `AnnexPayload` resultante en un fichero JSON, que servirá de entrada para el renderizador final del anexo.

### `generate_synthesis(...)`

Contiene la lógica de negocio principal y la interacción con el agente de IA.

**Responsabilidades:**
1.  **Construcción del Prompt:** Prepara un prompt detallado para el agente de IA, combinando las instrucciones definidas en el fichero de configuración YAML con datos específicos extraídos del `Blueprint` y de la inteligencia de cliente.
2.  **Invocación del Agente:** Utiliza `ai_client.run_agent` para ejecutar el agente de IA. Es un paso crucial, ya que le pasa el esquema `AnnexPayload` como el "contrato" de salida que la IA debe cumplir.
3.  **Enriquecimiento del Payload:** Una vez que la IA devuelve una respuesta válida, la función no se limita a guardarla. La enriquece con datos adicionales calculados a partir del `Blueprint`:
    *   Añade metadatos de versionado y linaje.
    *   Calcula la puntuación media de madurez y la convierte en una banda cualitativa (ej: "Gestionado", "Optimizado").
    *   Puebla el perfil de madurez por pilar.
    *   Añade la ruta al gráfico de radar si existe.

## Rol en el Proyecto

Este script juega un doble papel fundamental: **Orquestador y Sintetizador**.

-   **Como Orquestador:** Gestiona el flujo de datos, leyendo el artefacto de una etapa anterior (`Blueprint`) y generando el artefacto para la siguiente (`Annex`), asegurando así el cumplimiento del flujo "Top-Down" y la consistencia entre documentos.
-   **Como Sintetizador:** Actúa como el "cerebro" que traduce la información. Orquesta un agente de IA especializado para transformar un análisis técnico y exhaustivo en un resumen estratégico y de alto nivel, adaptado para una audiencia ejecutiva.

Este script es un excelente ejemplo de la arquitectura del proyecto: un orquestador Python que dirige a un agente de IA, el cual opera dentro de los límites de un contrato de datos estricto definido por esquemas de Pydantic.
