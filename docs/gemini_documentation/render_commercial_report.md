# Documentación: `render_commercial_report.py`

## Resumen

Este script es un renderizador de documentos especializado en generar el "Account Action Plan". A diferencia de otros renderizadores, el documento que produce no es para el cliente, sino que es un **artefacto comercial estratégico para uso exclusivamente interno**. Su propósito es traducir los hallazgos técnicos y estratégicos de las fases anteriores en un plan de ventas y Go-To-Market (GTM) concreto y accionable para los equipos comerciales.

## Componentes Principales

### `main()`

Es la función principal que orquesta la creación del documento. Recibe tres argumentos desde la línea de comandos:
1.  La ruta al fichero JSON de entrada, el `CommercialPayload`.
2.  La ruta a una plantilla `.docx`.
3.  La ruta de salida para el "Account Action Plan" final.

### `render_*` Functions

El script se divide en múltiples funciones de renderizado, cada una encargada de construir una sección del plan de acción. El contenido de estas secciones refleja su naturaleza confidencial e interna:
-   **`render_commercial_cover()`:** Crea una portada con una advertencia de confidencialidad muy visible.
-   **`render_commercial_summary()`:** Genera el "Deal Snapshot" o resumen del acuerdo, que incluye el Mercado Total Direccionable (TAM) estimado, los principales impulsores de compra, el "tema ganador" (Win Theme) de NTT DATA y una matriz de valor para los diferentes directivos del cliente.
-   **`render_gtm_strategy()`:** Detalla la estrategia de Go-To-Market, con tácticas de entrada como "El Caballo de Troya" o la "Transformación Autofinanciada".
-   **`render_opportunities_pipeline()`:** Describe oportunidades de venta específicas, incluyendo su Valor Total de Contrato (TCV) estimado, las posibles objeciones del cliente (análisis "Red Team") y las respuestas preparadas para manejarlas ("Objection Handling").
-   **`render_proactive_proposals()`:** Una sección de gran valor que genera borradores de propuestas de varias páginas. Estos anexos están casi listos para ser adaptados y enviados al cliente, e incluyen marcadores de posición para que el equipo comercial inserte detalles finales, como credenciales de proyectos similares.

### Utilidades y Carga

-   **Carga Robusta:** Utiliza `robust_load_payload` para cargar y validar el `CommercialPayload` de entrada, asegurando que los datos cumplen con el contrato definido en `schemas/commercial.py`.
-   **Ayudantes de Docx:** Reutiliza muchas de las funciones auxiliares de otros renderizadores para mantener la consistencia en el formato de los documentos, y añade utilidades específicas como `clean_commercial_text` para este informe.

## Rol en el Proyecto

Este script cumple el rol de **Renderizador de Estrategia Comercial**. Representa el paso final en la cadena de valor interna del `assessment-engine`.

-   **Herramienta de Ventas Accionable:** Su función principal es convertir un análisis técnico en un plan de ventas tangible. No es un simple informe, sino un manual de estrategia para el equipo comercial.
-   **Enfoque Interno:** A diferencia de otros renderizadores, este se centra en producir un documento para consumo interno, lleno de información comercial sensible.
-   **Último Eslabón de la Cadena:** Se sitúa al final del flujo "Top-Down", consumiendo el `CommercialPayload` que, a su vez, es el resultado del refinamiento del informe global y los blueprints.
-   **Generador de Alto Valor:** Produce uno de los artefactos más valiosos de todo el proceso: propuestas proactivas y basadas en datos que pueden acelerar significativamente el ciclo de ventas.
