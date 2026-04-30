# Documentación: `lib/runtime_env.py`

## Resumen

Este módulo es una utilidad de configuración de entorno muy específica pero crucial. Su única responsabilidad es asegurar que las variables de entorno necesarias para conectarse a **Google Cloud (y, por lo tanto, a Vertex AI)** estén siempre presentes durante la ejecución del pipeline.

## Componentes Principales

### Constantes Globales

-   **`DEFAULT_GOOGLE_CLOUD_PROJECT`:** Define el ID del proyecto de Google Cloud que se usará por defecto si no se especifica otro.
-   **`DEFAULT_GOOGLE_CLOUD_LOCATION`:** Define la región de Google Cloud (ej: "europe-west1") que se usará por defecto.

### `ensure_google_cloud_env_defaults(env: dict | None) -> dict | None`

-   **Propósito:** Esta es la única función del módulo. Su trabajo es verificar y establecer las variables de entorno de Google Cloud.
-   **Lógica:**
    1.  Toma un diccionario que representa las variables de entorno (o usa las del sistema operativo si no se proporciona uno).
    2.  Utiliza el método `setdefault` para establecer `GOOGLE_CLOUD_PROJECT` y `GOOGLE_CLOUD_LOCATION` **solo si no existen previamente**.
-   **Importancia:** Esta lógica de "establecer si no existe" es clave. Permite que un desarrollador o un sistema de CI/CD sobreescriban el proyecto o la región simplemente estableciendo las variables de entorno antes de ejecutar el pipeline, pero también asegura que el sistema funcione "de fábrica" con una configuración por defecto si no se proporciona ninguna.

## Rol en el Proyecto

Este módulo desempeCHA el rol de **Configurador del Entorno de Cloud**.

-   **Garantía de Conectividad:** Es el mecanismo que garantiza que cualquier script que necesite llamar a los servicios de Vertex AI (como `ai_client.py`) tendrá el contexto (`project` y `location`) necesario para establecer la conexión.
-   **Centralización de la Configuración:** Al igual que `runtime_paths.py`, centraliza una pieza crítica de la configuración. Si el proyecto de Google Cloud por defecto cambiara, solo habría que modificar la constante en este fichero.
-   **Flexibilidad vs. Robustez:** Proporciona un equilibrio perfecto. Es lo suficientemente **flexible** como para permitir que el entorno se configure desde fuera (mediante variables de entorno), y lo suficientemente **robusto** como para asegurar que siempre haya una configuración válida por defecto, evitando fallos por un entorno mal configurado.
-   **Colaborador de los Orquestadores:** Los scripts orquestadores (`run_tower_pipeline.py`, etc.) llaman a esta función al principio de su ejecución para preparar el diccionario de entorno que luego pasarán a cada uno de los subprocesos que ejecutan.
