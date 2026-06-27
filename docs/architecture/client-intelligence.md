---
status: Verified
owner: docs-governance
source_of_truth:
- ../../src/assessment_engine/domain/schemas/intelligence.py
- ../../src/assessment_engine/infrastructure/client_intelligence.py
- ../../src/assessment_engine/application/run_intelligence_harvesting.py
- ../../src/assessment_engine/application/build_case_input.py
- ../../src/assessment_engine/application/run_tower_blueprint_engine.py
- ../../src/assessment_engine/application/build_global_report_payload.py
- ../../src/assessment_engine/application/run_executive_refiner.py
- ../../src/assessment_engine/application/run_commercial_refiner.py
- ../../src/assessment_engine/domain/prompts/intelligence_prompts.py
- ../../src/assessment_engine/domain/prompts/global_prompts.py
- ../../src/assessment_engine/domain/prompts/commercial_prompts.py
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
---
# Client intelligence architecture

El archivo `client_intelligence.json` constituye el dossier de inteligencia estratégica de la organización del cliente. Su propósito principal es proveer un contexto semántico e histórico consistente y auditable, consumible y trazable de manera transversal por los siguientes módulos de la plataforma:

-   Preparación y delimitación de contexto por torre tecnológica;
-   Generación y síntesis del blueprint canónico;
-   Consolidación del reporte estratégico global;
-   Activación comercial del plan de cuenta.

## Rol en la Arquitectura de Datos

El dossier reside en la ruta física determinista `working/<client>/client_intelligence.json`, comportándose como un input de enriquecimiento estratégico transversal para todo el pipeline de ejecución.

El cargador de configuración e infraestructura soporta la compatibilidad retroactiva a través de tres capas evolutivas de datos:
-   **Esquema Plano Histórico:** Soporte para estructuras iniciales basadas en `industry`, `ceo_agenda` y `target_maturity_matrix`.
-   **Esquema de Transición 2.0:** Enfocado en la estructuración básica del perfil de la organización y sobreescrituras por torre tecnológica (`tower_overrides`).
-   **Esquema de Madurez 3.0:** Orientado a la declaración precisa del contexto operacional, aserciones cualitativas (*claims*) certificadas y consumo contextual estructurado en prompts.

La lógica de normalización, compatibilidad de esquemas históricos y derivación de parámetros operativos reside en `src/assessment_engine/infrastructure/client_intelligence.py`.

## Estructura Contractual v3

La especificación técnica del esquema `3.0` añade cinco bloques de propiedades estructurales en el modelo Pydantic:

1.  **`metadata`:**
    -   Identidad digital y firma del dossier.
    -   Marcas temporales de creación y última mutación.
    -   Idioma de referencia del diagnóstico.
    -   Metadatos de trazabilidad y rastro de generación.
2.  **`profile`:**
    -   Industria o sector de actividad.
    -   Clasificación y perfil financiero (*tier*).
    -   Modelo operativo de TI (p. ej., centralizado, federado).
    -   Distribución geográfica y mercados prioritarios.
    -   Líneas de negocio críticas.
3.  **`business_context` & `technology_context`:**
    -   Agenda ejecutiva y prioridades de dirección.
    -   Programas de transformación activos en la organización.
    -   Proveedores y fabricantes tecnológicos dominantes (*vendors*).
    -   Restricciones presupuestarias u operativas de cumplimiento.
    -   Señales de incidentes recientes e interrupciones operativas.
    -   Horizonte temporal de planificación de la transformación.
4.  **`tower_overrides`:**
    -   Umbrales de madurez objetivo por torre.
    -   Criticidad de negocio del dominio tecnológico.
    -   Presión regulatoria y de cumplimiento asociada.
    -   Urgencia de cambio operacional.
    -   Restricciones físicas y lógicas específicas del dominio.
5.  **`claims` & `review`:**
    -   Clasificación epistémica de la información: Hechos objetivos, Inferencias deducidas y Supuestos teóricos.
    -   Índice cuantitativo de confianza de la aserción.
    -   Fuentes y traza de origen de la evidencia.
    -   Estado de revisión e intervención humana en el dossier.

## Ingesta y Flujos de Consumo en los Pipelines

### 1. Fase de Análisis de Torre
El módulo de preparación de telemetría de torre (`build_case_input.py`) incorpora dinámicamente:
-   La meta de madurez global predeterminada (`target_maturity_default`) derivada de los overrides del dossier.
-   Un resumen ejecutivo sintetizado del contexto del cliente.
-   El paquete de datos de inteligencia filtrado para el dominio específico.

Posteriormente, el motor de síntesis de la torre (`run_tower_blueprint_engine.py`) consume este paquete contextual para enriquecer las instrucciones y límites de aserción de los prompts del blueprint, consolidando esta información estratégica dentro del payload resultante de la torre.

### 2. Fase de Consolidación Global
Por su parte, el agregador global (`build_global_report_payload.py`) valida la existencia del dossier en la ruta física determinista, incorporando una representación estructurada en el payload global consolidado.

Esta información es consumida por el refinador ejecutivo (`run_executive_refiner.py`), permitiendo que el análisis directivo herede de forma íntegra las restricciones regulatorias, la agenda de transformación del cliente y las aserciones certificadas.

### 3. Fase de Refinamiento Comercial
Finalmente, el refinador comercial (`run_commercial_refiner.py`) unifica de manera determinista tres capas contextuales:
-   El payload global estratégico consolidado.
-   El catálogo de iniciativas tácticas y proyectos derivados directamente de los blueprints de torre.
-   El dossier resumido `client_intelligence` de la organización.

Esta correlación multidimensional faculta al plan de cuenta comercial para mapear las oportunidades y propuestas técnicas de manera explícita contra la agenda directiva del cliente, la presión regulatoria del sector, los vendors dominantes y las restricciones físicas del entorno operativo.

## Plan de Evolución de la Capa de Inteligencia

La modernización del ciclo de vida de la inteligencia estratégica sigue los siguientes hitos técnicos:
1.  **Ampliación Contractual:** Soportar de forma robusta la definición v3 manteniendo compatibilidad completa hacia atrás.
2.  **Optimización de Cosecha (*Harvesting*):** Refinar la recolección automática en el script de smoke-test integrando esquemas ricos de datos.
3.  **Trazabilidad Extensiva:** Asegurar el paso íntegro del dossier a través de `case_input`, blueprints, global y comercial.
4.  **Inyección Contextual Directa:** Estructurar las señales operacionales y de negocio explícitamente en el andamiaje de prompts de la plataforma.
5.  **Garantía de Cohesión:** Blindar la ingesta y transformación mediante tests unitarios de coerción de tipos y validación de payloads.

## Fortalezas y Límites Operacionales

La arquitectura del dossier estratégico optimiza directamente:
-   La trazabilidad de origen de las aserciones del assessment.
-   La homogeneidad terminológica y de objetivos entre entregables de distinta naturaleza.
-   La capacidad de inyectar contexto corporativo real en motores generativos de manera estructurada.
-   El rigor en la priorización de iniciativas en los reportes comercial y global.

*Nota de Límitación Técnica: La existencia del contrato no sustituye la calidad de las fuentes primarias de entrada; un dossier con telemetría deficiente producirá downstream resúmenes de contexto de baja especificidad.* El roadmap tecnológico proyecta la ampliación de las capacidades de harvesting mediante la ingesta automática de memorias financieras, reportes de M&A y registros operacionales directos.
