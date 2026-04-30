# Documentación: `ai_client.py`

## Resumen

Este módulo proporciona un cliente centralizado, robusto y observable para interactuar con los agentes de Vertex AI. Su propósito es abstraer las complejidades de la comunicación con los modelos de IA, gestionando la concurrencia, los reintentos y la validación de los datos recibidos.

## Componentes Principales

### `run_agent(...)`

Es la función principal y el punto de entrada para todas las interacciones con la IA. Orquesta el proceso de enviar un mensaje a un agente y procesar su respuesta.

**Responsabilidades:**
1.  **Gestión de Concurrencia:** Utiliza un semáforo (`_vertex_semaphore`) para limitar el número de peticiones simultáneas a Vertex AI (actualmente 5), evitando así exceder los límites de la API.
2.  **Ejecución con Reintentos:** Delega la llamada a la API a la función `_execute_query_with_retry`, que gestiona automáticamente los reintentos en caso de fallos transitorios.
3.  **Captura de Salida:** Opcionalmente, puede guardar la respuesta completa y sin procesar del modelo en un fichero de texto.
4.  **Parseo y Validación:** Extrae el JSON de la respuesta del modelo y, si se proporciona un esquema de Pydantic, valida que la estructura de los datos sea la correcta.
5.  **Telemetría:** Al finalizar cada llamada, imprime en consola un resumen con métricas clave: duración, número de reintentos, nombre del agente, modelo utilizado y el esquema de salida esperado.

### `_execute_query_with_retry(...)`

Función interna que envuelve la llamada a la API del agente con la librería `tenacity`. Está configurada para reintentar la operación hasta 5 veces con un tiempo de espera exponencial entre intentos. Esto aporta una gran resiliencia al sistema frente a errores de red o fallos puntuales del modelo.

### `_robust_unwrap_and_validate(...)`

Utilidad que valida el JSON recibido contra un esquema Pydantic. Su diseño "robusto" le permite buscar los datos correctos dentro de posibles anidamientos innecesarios que el modelo de IA a veces añade en sus respuestas.

### `call_agent(...)`

Una función de conveniencia que simplifica las llamadas "ad-hoc" a un agente. Crea un agente temporal, ejecuta la consulta a través de `run_agent` y devuelve el resultado. Es útil para interacciones simples que no requieren gestionar el ciclo de vida de un objeto `AdkApp`.

## Rol en el Proyecto

Este módulo es fundamental en la arquitectura del `assessment-engine`. Actúa como la **puerta de enlace única y controlada para todas las operaciones de IA**. Centraliza funcionalidades críticas que son indispensables para un sistema de nivel empresarial:

-   **Fiabilidad:** La lógica de reintentos asegura que los fallos transitorios no interrumpan los pipelines de generación de documentos.
-   **Control de Concurrencia:** El semáforo protege el sistema contra sobrecargas y errores de "rate limiting" de la API.
-   **Observabilidad:** La telemetría que genera es vital para monitorizar la salud, el rendimiento y los costes de las operaciones de IA.
-   **Cumplimiento de Contratos:** La validación con esquemas Pydantic garantiza que los datos generados por la IA son estructuralmente correctos antes de ser consumidos por otras partes del sistema, previniendo errores en cascada.
