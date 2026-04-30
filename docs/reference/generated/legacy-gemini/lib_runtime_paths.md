# Documentación: `lib/runtime_paths.py`

## Resumen

Este módulo actúa como el **"GPS" o el servicio de resolución de rutas** para todo el proyecto. Su única responsabilidad es proporcionar una manera centralizada y consistente de obtener las rutas (`Path`) a los directorios y ficheros clave en tiempo de ejecución. Esto evita que las rutas estén "hardcodeadas" (escritas directamente) en múltiples scripts, lo que hace que el sistema sea mucho más robusto y fácil de mantener.

## Componentes Principales

La estrategia principal del módulo es buscar rutas o identificadores en las **variables de entorno** y, si no las encuentra, recurrir a valores por defecto o calcular las rutas de forma relativa al directorio raíz del proyecto.

### `ROOT`

-   **Propósito:** Una constante global que almacena la ruta absoluta al directorio raíz del proyecto.
-   **Implementación:** `Path(__file__).resolve().parents[4]`
-   **Rol:** Es el "ancla" a partir de la cual se calculan todas las demás rutas relativas, asegurando que el sistema funcione independientemente de desde dónde se ejecute.

### `resolve_tower_id(default: str) -> str`

-   **Propósito:** Obtener el identificador de la torre que se está procesando (ej: "T5").
-   **Lógica:** Busca la variable de entorno `ASSESSMENT_TOWER_ID`. Si no existe, devuelve el valor por defecto.

### `resolve_client_id(default: str) -> str`

-   **Propósito:** Obtener el identificador del cliente que se está procesando (ej: "smoke_ivirma").
-   **Lógica:** Busca la variable de entorno `ASSESSMENT_CLIENT_ID`. Si no existe, devuelve el valor por defecto.

### `resolve_case_dir(...) -> Path`

-   **Propósito:** Obtener la ruta al directorio de trabajo para la ejecución actual, que es donde se guardan todos los ficheros generados para un cliente y una torre específicos.
-   **Lógica:**
    1.  Primero, busca la variable de entorno `ASSESSMENT_CASE_DIR`. Si existe, la devuelve directamente. Esto permite sobreescribir la ubicación por completo.
    2.  Si no existe, construye la ruta dinámicamente usando las otras funciones: `ROOT / "working" / resolve_client_id() / resolve_tower_id()`.
-   **Ejemplo de Ruta:** `/path/to/assessment_engine/working/smoke_ivirma/T5`

### `resolve_tower_definition_file(...) -> Path`

-   **Propósito:** Obtener la ruta al fichero de definición de una torre, que contiene su metodología.
-   **Lógica:** Construye la ruta dinámicamente: `ROOT / "engine_config" / "towers" / resolve_tower_id() / f"tower_definition_{tower_id}.json"`.

## Rol en el Proyecto

Este módulo es un componente fundamental para la **configuración y la robustez del entorno de ejecución**.

-   **Centralización:** Es el único punto de verdad para la resolución de rutas. Si la estructura de directorios del proyecto cambia (por ejemplo, si la carpeta `working` se renombra a `output`), solo es necesario actualizar este fichero, en lugar de modificar docenas de scripts.
-   **Flexibilidad:** El uso de variables de entorno hace que los scripts sean muy flexibles y controlables desde el exterior. Los orquestadores (`run_tower_pipeline.py`, etc.) utilizan este mecanismo para pasar el contexto de ejecución a cada uno de los subprocesos que lanzan.
-   **Código Limpio (DRY - Don't Repeat Yourself):** Evita la repetición constante de la lógica para construir rutas en cada script, haciendo que el resto del código sea más limpio, más legible y menos propenso a errores.
-   **Independencia de la Ubicación:** Al basar todas las rutas en la constante `ROOT`, los scripts pueden ser ejecutados desde cualquier directorio sin que las rutas relativas se rompan.
