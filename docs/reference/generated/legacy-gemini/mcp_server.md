# Documentación: `mcp_server.py`

## Resumen

Este script implementa un **servidor de herramientas MCP (Model-Context-Protocol)**. Su propósito es exponer las funcionalidades principales del `assessment-engine` como un conjunto de herramientas (`tools`) que pueden ser llamadas y orquestadas por un sistema externo, como un agente de IA supervisor (mencionado en el código como "LangGraph/CrewAI") u otras aplicaciones compatibles.

La existencia de este servidor revela una faceta clave de la arquitectura: el `assessment-engine` no solo está diseñado para ser ejecutado a través de sus propios pipelines lineales (`run_tower_pipeline.py`, etc.), sino que también puede actuar como un **motor de backend controlado por un orquestador externo**.

## Componentes Principales

### `FastMCP`

-   El script utiliza una librería llamada `FastMCP` para crear un servidor. La decoración `@mcp.tool()` se usa para registrar una función de Python como una herramienta disponible para ser llamada remotamente. Cuando se ejecuta el script (`if __name__ == "__main__": mcp.run()`), `FastMCP` se encarga de iniciar el servidor y gestionar la comunicación.

### `_run_script(module_name, args)`

-   Esta es una función de utilidad interna que actúa como un **envoltorio seguro para ejecutar los scripts del motor**.
-   **Aislamiento:** Utiliza el módulo `subprocess` de Python para ejecutar cada script en un proceso completamente nuevo y aislado. Esto es crucial para la estabilidad de un servidor, ya que asegura que los errores en la ejecución de una herramienta no afecten al servidor principal.
-   **Gestión de Errores:** Captura la salida estándar (`stdout`) y el error estándar (`stderr`) del subproceso. Si el script falla, lanza una excepción con un mensaje de error detallado, que el servidor MCP puede entonces comunicar al cliente que llamó a la herramienta.

### Herramientas Expuestas (`@mcp.tool()`)

El servidor expone las siguientes funcionalidades como herramientas:

-   **`build_tower_payload(...)`:**
    -   **Acción:** Ejecuta el script `build_tower_annex_template_payload.py`.
    -   **Propósito:** Permite a un agente externo convertir un JSON de anexo aprobado en el `payload` final listo para renderizar.

-   **`render_tower_docx(...)`:**
    -   **Acción:** Ejecuta el script `render_tower_annex_from_template.py`.
    -   **Propósito:** Permite renderizar el documento `.docx` de un Anexo de Torre.

-   **`generate_radar_chart(...)`:**
    -   **Acción:** Ejecuta `generate_global_radar_chart.py`.
    -   **Propósito:** Permite generar un gráfico de radar a partir de un payload.

-   **`render_commercial_docx(...)`:**
    -   **Acción:** Ejecuta `render_commercial_report.py`.
    -   **Propósito:** Permite renderizar el "Account Action Plan" comercial.

-   **`get_tower_state(...)`:**
    -   **Acción:** No ejecuta un script, sino que inspecciona directamente el sistema de ficheros.
    -   **Propósito:** Es una herramienta de **monitorización y estado**. Permite a un agente supervisor externo comprobar el progreso de un assessment, verificando qué ficheros de sección (`approved_asis.json`, `approved_risks.json`, etc.) ya se han completado. Esto habilita una orquestación más inteligente, donde el agente supervisor puede decidir qué herramienta llamar a continuación basándose en el estado actual.

## Rol en el Proyecto

Este script transforma el `assessment-engine` de un simple conjunto de scripts de línea de comandos a un **Servicio de Generación de Documentos Controlable por IA**.

-   **Habilitador de la Orquestación Externa:** Es la pieza que permite que un sistema de agentes de IA de nivel superior (un "Supervisor Agent") utilice el `assessment-engine` como su "caja de herramientas" para realizar tareas de análisis y renderizado.
-   **Arquitectura Orientada a Servicios:** Representa un modo de operación alternativo y más flexible que los pipelines predefinidos. En lugar de un flujo fijo, un agente externo puede decidir llamar a estas herramientas en cualquier orden, o repetirlas si es necesario.
-   **Flexibilidad y Reutilización:** Expone las capacidades del motor de una forma modular, permitiendo que otras aplicaciones o agentes reutilicen estas funciones sin necesidad de entender toda la lógica del pipeline interno.
-   **Capacidad de Monitorización:** La herramienta `get_tower_state` es particularmente importante, ya que dota al sistema de "observabilidad", permitiendo una orquestación inteligente y reactiva por parte de un agente supervisor.
