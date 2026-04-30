# Documentación: `lib/config_loader.py`

## Resumen

Este módulo funciona como un **cargador de configuración centralizado** para todo el `assessment-engine`. Su única responsabilidad es proporcionar una interfaz limpia y consistente para que el resto de la aplicación acceda a los diversos ficheros de configuración `.json` que se encuentran en el directorio `engine_config/`. Abstrae los detalles de las rutas de los ficheros y el parseo, haciendo que el resto del código sea más limpio y esté menos acoplado a la estructura física de los ficheros.

## Componentes Principales

El módulo consiste en una serie de funciones simples y bien nombradas, cada una responsable de cargar una pieza específica de configuración. Se dividen en dos categorías:

### 1. Cargadores Directos (`load_*`)

Estas funciones cargan un fichero de configuración específico directamente.
-   **`load_runtime_manifest()`:** Carga el `runtime_manifest.json`, que contiene la configuración de alto nivel para una ejecución específica del motor.
-   **`load_model_profiles()`:** Carga `model_profiles.json`, que define las características de los diferentes perfiles de modelos de IA (ej: un modelo rápido para tareas simples, uno potente para análisis complejos).
-   **`load_model_profile(profile_name)`:** Carga la configuración para un perfil de modelo específico.
-   **`load_document_profile(profile_name)`:** Carga un perfil de documento, que puede contener ajustes sobre el estilo o la estructura de los entregables.
-   **`load_policy_file(file_name)`:** Una función genérica para cargar ficheros de la subcarpeta `policies/`.

### 2. Resolutores (`resolve_*`)

Estas funciones son más inteligentes. Primero leen el `runtime_manifest.json` para determinar qué perfil o política está activa en la ejecución actual, y luego cargan esa configuración específica.
-   **`resolve_model_profile_for_role(role_name)`:** Una función clave. Busca un "rol" (ej: `writer_fast`) en el manifiesto para encontrar el nombre del perfil de modelo que debe usar (ej: `gemini-1.5-pro-tuned`) y entonces carga los detalles de ese perfil. Esto permite cambiar el modelo de IA para una tarea simplemente modificando el manifiesto, sin tocar el código.
-   **`resolve_document_profile()`:** Lee el nombre del perfil de documento activo del manifiesto y lo carga.
-   **`resolve_target_maturity_defaults(...)`:** Obtiene las puntuaciones de madurez objetivo por defecto según la política de madurez.
-   **`resolve_review_rules()`:** Obtiene las reglas de revisión de la política de revisiones.

## Rol en el Proyecto

Este módulo actúa como un **Hub de Configuración** o un **Servicio de Configuración**.

-   **Centralización:** Es el único punto de acceso a la configuración. Si la ubicación o el formato de un fichero de configuración cambia, solo hay que actualizar este módulo, no todos los scripts que lo usan.
-   **Abstracción:** Oculta los detalles de implementación (rutas de ficheros, parseo de JSON) al resto de la aplicación. Un script simplemente pide la configuración que necesita por su nombre lógico.
-   **Desacoplamiento:** Desacopla la lógica de la aplicación de los datos de configuración. Esto hace que el sistema sea extremadamente flexible; cambiar un modelo de IA o una política de negocio es tan simple como editar un fichero JSON.
-   **Claridad:** Las funciones bien nombradas hacen que el código que las utiliza sea más legible y auto-explicativo.
