# Documentación: `run_commercial_refiner.py`

## Resumen

Este script es un **orquestador de un sistema multi-agente de IA**. Su propósito es generar el `commercial_report_payload.json` final. Para ello, toma como entrada el `global_report_payload.json` y lo enriquece coordinando a un equipo de agentes de IA especializados, cada uno desempeñando un rol comercial específico para refinar y expandir la estrategia de ventas. Es la implementación del "Contrato Híbrido", ya que consume tanto la visión estratégica del informe global como los detalles tácticos de todos los Blueprints de torre disponibles.

## Componentes Principales

### `main()`

Es la función de entrada. Carga el `global_report_payload.json` y, de forma crucial, invoca a `aggregate_blueprint_catalogs` para encontrar y consolidar un catálogo de todas las iniciativas técnicas de bajo nivel presentes en los ficheros de `Blueprint`. Con este contexto "híbrido", inicia el proceso de refinamiento.

### `refine_commercial_payload(...)`

El orquestador principal. Su flujo de trabajo se divide en tres fases, cada una delegada a uno o más agentes de IA:
-   **Fase 1: Estrategia de Cuenta:** Invoca a un agente "Global Account Director" para que genere el resumen comercial de alto nivel, la estrategia Go-To-Market y el mapa de directivos (stakeholders).
-   **Fase 2: Calificación del Pipeline:** Llama a un agente "Enterprise Presales Architect". Su instrucción es clave: debe **cruzar la estrategia global con el catálogo táctico de los blueprints** para identificar y calificar oportunidades de venta concretas, incluyendo su valor estimado (TCV) y cómo manejar las posibles objeciones.
-   **Fase 3: Propuestas Proactivas:** Para las oportunidades más importantes identificadas en la fase anterior, delega su creación a un sub-orquestador, `build_proactive_proposal`.

### `build_proactive_proposal(...)`

Este es un **sub-orquestador** que simula un esfuerzo colaborativo para construir una única propuesta detallada. Invoca en secuencia a **cuatro agentes de IA diferentes y especializados**:
1.  **Engagement Manager:** Define el contexto y el valor ("El Porqué").
2.  **Lead Solutions Architect:** Define el alcance técnico y el equipo ("El Cómo").
3.  **Delivery & Risk Director:** Define el gobierno del proyecto y los riesgos.
4.  **Sales Partner:** Crea el discurso de venta final y el cronograma de inversión.
Finalmente, ensambla las salidas de los cuatro agentes en una única propuesta coherente.

### `aggregate_blueprint_catalogs(...)`

Esta función es la que habilita el análisis "híbrido". Escanea el directorio del cliente en busca de todos los `blueprint_*_payload.json`, los lee y extrae un catálogo consolidado de todas las iniciativas técnicas, deudas técnicas y conclusiones ejecutivas de cada torre.

## Rol en el Proyecto

Este script es el **Orquestador de la Estrategia Comercial por IA**. Representa el uso más sofisticado de la inteligencia artificial en todo el proyecto.

-   **Sistema Multi-Agente:** Es una implementación práctica de un sistema donde múltiples agentes de IA, cada uno con su propia "personalidad" (rol), instrucciones y contrato de datos, colaboran para lograr un objetivo complejo.
-   **Motor de Análisis Híbrido:** Su capacidad para combinar la visión estratégica de alto nivel con los detalles tácticos de bajo nivel es su principal innovación, permitiéndole generar insights comerciales que de otro modo se perderían.
-   **Generador de Valor Comercial:** Es aquí donde el análisis técnico se convierte en una estrategia de ventas tangible y de alto valor. Transforma los datos en planes de acción y borradores de propuestas que aceleran el ciclo de ventas.
-   **Creador del Payload Final:** Genera el `commercial_report_payload.json`, el artefacto de datos definitivo que alimenta al `render_commercial_report.py` para producir el documento final.
