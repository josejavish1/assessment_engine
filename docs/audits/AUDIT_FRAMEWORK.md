# Framework de Auditoría de Documentación

## 1. Introducción

Este documento define el marco y la lista de verificación para realizar una auditoría exhaustiva de la documentación del proyecto. El objetivo es garantizar que toda la documentación, desde los diagramas de arquitectura hasta las docstrings en el código, cumpla con un alto estándar de calidad, facilitando el mantenimiento, la incorporación de nuevos miembros y el intercambio de conocimientos.

## 2. Criterios de Calidad

La auditoría evaluará la documentación en función de cuatro criterios clave:

*   **Exactitud:** La documentación debe reflejar correctamente el estado actual del código, la arquitectura y los procesos. Debe estar libre de información obsoleta o engañosa.
*   **Completitud:** La documentación debe cubrir todos los aspectos necesarios del sistema, sin dejar lagunas significativas. Debe proporcionar suficientes detalles para que su público objetivo alcance sus metas sin necesidad de consultar fuentes externas o conocimiento tribal.
*   **Claridad:** La documentación debe ser fácil de entender, estar bien estructurada y utilizar un lenguaje inequívoco. Debe redactarse pensando en su público objetivo.
*   **Facilidad de Descubrimiento (Discoverability):** La documentación debe ser fácil de encontrar. Esto implica una arquitectura de la información lógica, una nomenclatura clara y referencias cruzadas efectivas.

## 3. Checklist de Auditoría

Esta lista de verificación es aplicable a todas las formas de documentación, incluidos los archivos `README.md`, los documentos de arquitectura, los manuales de operaciones (runbooks) y las docstrings en el código.

### 3.1. Checklist General

-   [ ] **Propiedad (Ownership):** ¿Existe un propietario o equipo claramente responsable de mantener el documento?
-   [ ] **Fecha de Última Revisión:** ¿La fecha de la última revisión del documento está presente y es reciente?
-   [ ] **Estado:** ¿El documento tiene un estado claro (p. ej., `Borrador`, `En Revisión`, `Verificado`, `Obsoleto`)?
-   [ ] **Audiencia:** ¿Está claramente definida la audiencia a la que se dirige?

### 3.2. Checklist de Exactitud

-   [ ] **Sincronización con el Código:** ¿La documentación refleja con precisión el comportamiento del código asociado? (p. ej., firmas de funciones, nombres de clases, responsabilidades de módulos).
-   [ ] **Sincronización con los Procesos:** ¿Los documentos de procedimientos (runbooks, flujos de trabajo) coinciden con los pasos reales requeridos?
-   [ ] **Sin Información Obsoleta:** ¿Se han eliminado todas las referencias a funcionalidades eliminadas, arquitecturas antiguas o procesos obsoletos?
-   [ ] **Enlaces Externos:** ¿Son válidos y correctos todos los hipervínculos a recursos externos (p. ej., otros documentos, tickets, sitios web externos)?

### 3.3. Checklist de Completitud

-   [ ] **Cobertura del Alcance:** ¿El documento cubre completamente el alcance que declara?
-   [ ] **Contexto:** ¿Proporciona suficiente contexto para que el lector entienda el "porqué" detrás del "qué"?
-   [ ] **Ejemplos:** ¿Existen suficientes ejemplos de código, fragmentos de comandos o muestras de configuración donde sea aplicable?
-   [ ] **Casos Límite (Edge Cases):** ¿Aborda casos límite comunes, condiciones de error o "gotchas"?
-   [ ] **Docstrings (para código):** ¿Tienen docstrings todos los módulos, clases, funciones y métodos públicos? ¿Explican el propósito, los parámetros y los valores de retorno?

### 3.4. Checklist de Claridad

-   [ ] **Lenguaje Sencillo:** ¿El lenguaje es claro, conciso y libre de jerga en la medida de lo posible?
-   [ ] **Estructura:** ¿Está el documento bien organizado con un flujo lógico, encabezados y subencabezados?
-   [ ] **Formato:** ¿Se utiliza el formato (p. ej., markdown, bloques de código, tablas) de manera efectiva para mejorar la legibilidad?
-   [ ] **Elementos Visuales:** ¿Se utilizan diagramas, capturas de pantalla u otros elementos visuales donde ayudarían a la comprensión? ¿Son legibles y están bien anotados?
-   [ ] **Gramática y Ortografía:** ¿El documento está libre de errores gramaticales y ortográficos significativos?

### 3.5. Checklist de Facilidad de Descubrimiento

-   [ ] **Ubicación:** ¿Está el documento almacenado en una ubicación lógica e intuitiva dentro del directorio `docs/`?
-   [ ] **Nombre de Archivo:** ¿Es el nombre del archivo claro, descriptivo y coherente con las convenciones del proyecto?
-   [ ] **Referencias Cruzadas (Cross-Linking):** ¿Está el documento debidamente enlazado desde puntos de entrada relevantes (p. ej., `docs/README.md`, otros documentos relacionados)?
-   [ ] **Capacidad de Búsqueda:** ¿El documento contiene palabras clave relevantes que ayudarían a su descubrimiento mediante búsquedas?
