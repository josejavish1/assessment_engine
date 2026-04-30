# Documentación: `prompts/intelligence_prompts.py`

## Resumen

Este módulo define las plantillas de prompts para un **equipo de agentes de IA de investigación (OSINT - Open Source Intelligence)**. El propósito de este equipo es realizar una investigación de fuentes abiertas sobre el cliente para construir el "dossier de inteligencia" (`client_intelligence.json`). Este dossier, también conocido como el "ADN del cliente", proporciona el contexto de negocio, regulatorio y tecnológico esencial que informa y guía todo el proceso de assessment desde el principio.

## Componentes Principales

El flujo de trabajo se divide en dos fases: recolección de información por agentes especializados y una auditoría y enriquecimiento final por un agente auditor.

### 1. Agentes Recolectores (Harvesters)

Estos tres agentes trabajan en paralelo para recopilar información desde diferentes dominios. Se espera que el sistema que los invoca utilice herramientas de búsqueda web para responder a estas preguntas.

-   **`get_regulatory_harvester_prompt(...)`:**
    -   **Rol:** Investigador Regulatorio.
    -   **Tarea:** Identificar el sector del cliente y determinar qué marcos normativos de ciberseguridad o resiliencia le aplican por ley en su región (ej: DORA para finanzas, NIS2 para operadores críticos).

-   **`get_business_harvester_prompt(...)`:**
    -   **Rol:** Analista de Negocio.
    -   **Tarea:** Investigar noticias y resultados financieros para determinar los objetivos estratégicos del CEO (`ceo_agenda`) y estimar el tamaño de la empresa en uno de tres niveles (`financial_tier`).

-   **`get_tech_harvester_prompt(...)`:**
    -   **Rol:** Analista Tecnológico.
    -   **Tarea:** Deducir el "footprint" tecnológico del cliente analizando fuentes como ofertas de empleo o anuncios de alianzas, para entender qué tecnologías usan (ej: Azure, SAP) y hacia dónde se dirigen.

### 2. Agente Auditor (Auditor)

-   **`get_auditor_harvester_prompt(...)`:**
    -   **Rol:** Auditor de Calidad Estratégica.
    -   **Tarea:** Este agente es el "cerebro" del proceso. Recibe un borrador del dossier con la información recopilada por los tres agentes anteriores y realiza dos funciones críticas:
        1.  **Auditoría y Validación:** Comprueba la coherencia de la información (ej: DORA no aplica a un hospital, una empresa del IBEX 35 no puede ser "Tier 3").
        2.  **Enriquecimiento y Síntesis Estratégica:** Genera dos de las piezas de información más valiosas de todo el proyecto:
            -   **`transformation_horizon`:** Basándose en los retos del cliente, determina el nivel de ambición realista para la transformación (ej: "Horizonte 1: Brilliant Basics" si necesitan estandarizar antes de innovar).
            -   **`target_maturity_matrix`:** Establece las **puntuaciones de madurez objetivo** para cada una de las 10 torres tecnológicas. Este es un acto de juicio estratégico, donde el agente ajusta la ambición según la criticidad del sector (ej: un cliente del sector energético o financiero necesita una puntuación máxima en Resiliencia (T5) y Ciberseguridad (T6)).

## Rol en el Proyecto

Este fichero es el **Motor de Contextualización Estratégica**.

-   **Punto de Partida del Contexto:** Genera el `client_intelligence.json`, que es el primer y más fundamental artefacto de contexto. Este fichero se inyecta en casi todos los demás agentes del pipeline (como el `Blueprint Architect`) para asegurar que sus análisis no se hagan en un vacío, sino que estén alineados con la realidad del cliente.
-   **Anclaje en el Mundo Real:** Es el principal mecanismo que conecta el assessment con el entorno de negocio y regulatorio real del cliente.
-   **Definición de la Ambición:** A través de la `target_maturity_matrix`, este módulo establece los objetivos para todo el plan de transformación. Define el "éxito" antes de que comience el análisis detallado.
-   **Simulación de un Equipo de Investigación:** Implementa un flujo de trabajo realista de investigación: primero se recopilan datos en bruto desde diferentes especialidades y luego un experto senior los audita, corrige y sintetiza para extraer insights estratégicos.
