# Documentación: `tools/generate_smoke_data.py`

## Resumen

Este script es una **herramienta de generación de datos de prueba**. Su único propósito es crear los ficheros de entrada (`responses.txt` y `context.txt`) para un cliente ficticio llamado `smoke_ivirma`. Estos ficheros sirven como la base para ejecutar un **"smoke test"**, que es una prueba de alto nivel diseñada para verificar que el pipeline de generación de informes funciona de principio a fin sin errores graves.

## Componentes Principales

### Generación de Respuestas (`responses.txt`)

-   **Lógica:**
    1.  El script itera sobre una lista predefinida de torres tecnológicas (T2, T3, T4, etc.).
    2.  Para cada torre, lee su fichero de `tower_definition_*.json` para obtener una lista de todos sus KPIs.
    3.  Para cada KPI, genera una **puntuación de madurez aleatoria**.
-   **Inteligencia del Escenario:** La generación no es completamente aleatoria. El script utiliza un diccionario `tower_targets` que define un rango de madurez para cada torre (ej: `T5 - Resiliencia` con una puntuación muy baja, `T8 - Cloud` con una puntuación alta). Esto simula un escenario de cliente más realista, con áreas de fortaleza y debilidad bien definidas, lo que permite probar la capacidad de la IA para detectar y reaccionar a estos patrones.
-   **Salida:** Escribe un fichero de texto plano donde cada línea representa la respuesta a una pregunta, en el formato `Txx.Pxx.Kxx.PR1: 3.5`.

### Generación de Contexto (`context.txt`)

-   **Lógica:** El script define una cadena de texto multilínea que contiene una descripción narrativa de la situación del cliente `smoke_ivirma`.
-   **Contenido:** El contexto está diseñado para ser rico en información estratégica y dar "pistas" a los agentes de IA. Incluye:
    -   **Contexto de Negocio:** Objetivos de expansión, M&A, etc.
    -   **Contexto Tecnológico:** Proveedor cloud estratégico, problemas de red.
    -   **Contexto de Seguridad y Normativa:** Preocupación por el ransomware, mención explícita de la directiva NIS2.
    -   **Contexto de Operaciones:** Problemas con el ITSM, falta de CMDB.
-   **Salida:** Escribe este texto en el fichero `context.txt`.

## Rol en el Proyecto

Este script es una **Herramienta Fundamental de Desarrollo y Testing**.

-   **Habilitador de Pruebas End-to-End:** Proporciona un punto de partida consistente y reproducible para ejecutar el pipeline completo. Esto es indispensable para probar cambios que afectan a múltiples partes del sistema.
-   **Creación de Escenarios Realistas:** Al simular fortalezas y debilidades específicas y proporcionar un contexto de negocio rico, permite realizar pruebas que van más allá de la simple validación de formato, evaluando también la calidad del análisis generado por la IA.
-   **Independencia de Datos de Cliente:** Permite a los desarrolladores probar el sistema sin necesidad de tener acceso a datos reales de clientes, lo cual es importante por razones de confidencialidad y simplicidad.
-   **Base para la Integración Continua (CI):** Este tipo de script es un componente típico en un sistema de CI, donde se puede ejecutar automáticamente para validar cada nuevo cambio en el código, asegurando que no se han introducido regresiones.
