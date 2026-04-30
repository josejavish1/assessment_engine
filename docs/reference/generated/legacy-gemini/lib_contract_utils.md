# Documentación: `lib/contract_utils.py`

## Resumen

Este módulo proporciona utilidades esenciales para manejar los "contratos de datos" (esquemas de Pydantic) de manera robusta y resiliente. Su foco es la carga y guardado de los *payloads* (ficheros JSON) que se intercambian entre las diferentes etapas del pipeline, asegurando que el sistema pueda tolerar pequeñas desviaciones en los datos generados por la IA.

## Componentes Principales

### `robust_load_payload(path, schema, artifact_name)`

Esta es la función más importante del módulo. Implementa la "Degradación Elegante" o carga resiliente de datos, un principio clave del proyecto.

**Flujo de trabajo:**
1.  **Carga el JSON:** Lee el fichero JSON de la ruta especificada.
2.  **Intento de Validación Estricta:** Primero, intenta validar los datos contra el esquema Pydantic proporcionado usando `model_validate`. Si los datos son 100% correctos y cumplen el contrato, la función devuelve el objeto validado y todo continúa con normalidad.
3.  **Gestión de Errores de Validación:** Si la validación estricta falla (porque la IA generó un campo extra, usó un tipo de dato incorrecto, etc.), la función **no detiene el programa**. En su lugar:
    *   **Registra una Advertencia Detallada:** Escribe en el log un aviso (`WARNING`) por cada error de validación, especificando qué campo falló y por qué. Esto es crucial para la observabilidad y la depuración.
    *   **Modo de Recuperación:** Utiliza `model_construct` de Pydantic para crear una instancia del modelo **sin ejecutar las validaciones**. Es un intento de "mejor esfuerzo" para construir el objeto y permitir que el pipeline continúe, asumiendo que los errores no son catastróficos.

### `save_versioned_payload(path, payload, artifact_type)`

Esta función se encarga de guardar un objeto Pydantic en un fichero JSON, asegurando consistencia.
-   **Asegura los Metadatos:** Comprueba si el payload tiene el campo `generation_metadata`. Si no lo tiene o está vacío, lo inyecta con información de versión básica. Esto garantiza que todos los artefactos guardados tengan trazabilidad.
-   **Usa Alias:** Al guardar, utiliza `model_dump(by_alias=True)`. Esto es muy importante porque asegura que los nombres de los campos en el fichero JSON coincidan con sus alias definidos en el esquema (ej: `_generation_metadata` en lugar de `generation_metadata`), cumpliendo así con el contrato de datos.

## Rol en el Proyecto

Este módulo es la columna vertebral del principio de **"Contratos de Intercambio Resilientes"** (Handover contracts resilientes).

-   **Tolerancia a Fallos:** Su rol principal es hacer que el intercambio de datos entre las etapas del pipeline sea robusto. Asume que un LLM puede no ser siempre perfecto y proporciona un mecanismo para gestionar estas imperfecciones sin abortar todo el proceso.
-   **Observabilidad:** El registro detallado de los errores de validación es una pieza clave de la observabilidad del sistema, permitiendo a los desarrolladores identificar y corregir problemas en los prompts o en los modelos de IA.
-   **Cumplimiento Pragmático de Contratos:** Aunque su objetivo es hacer cumplir los contratos de datos, lo hace de una manera pragmática. Prioriza la continuidad del negocio (generar el informe) sobre la perfección absoluta de los datos, que es un requisito fundamental en un sistema de producción.
