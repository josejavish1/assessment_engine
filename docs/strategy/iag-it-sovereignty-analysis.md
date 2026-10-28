---
status: Needs Review
owner: docs-governance
source_of_truth:
- docs/strategy/VISION.md
- docs/strategy/ROADMAP.md
last_verified_against: '2026-07-08'
applies_to:
- src/assessment_engine/infrastructure
- src/assessment_engine/domain
doc_type: canonical
diataxis: explanation
verification_mode: editorial
last_updated: '2026-07-08'
---
# Análisis Estratégico de Soberanía Tecnológica (IAG IT Sovereignty)

Este documento detalla el análisis de alineamiento y reutilización del motor `assessment-engine` para el proyecto de **Soberanía Tecnológica de IAG (International Airlines Group)**.

---

## 1. Análisis Técnico de la Propuesta Ganada (IAG IT Sovereignty)

El proyecto tiene como objetivo establecer un **Sovereignty Baseline (Línea Base de Soberanía)** en un plazo de 3 meses, evaluando **10 Sociedades Operativas (OpCos)** (ej. Iberia, British Airways, Vueling, etc.) y priorizando un perímetro de **140 sistemas críticos e ICFR** (91 ICFR y 66 Mission-Critical).

### El Marco Metodológico Compuesto:
1.  **Objetivos de Soberanía (Sovereignty Objectives - SOV-1 a SOV-8):**
    *   **SOV-1: Strategic** (Anclaje estratégico, control de cambio).
    *   **SOV-2: Legal & Jurisdictional** (Protección frente a leyes extraterritoriales como FISA 702 y CLOUD Act).
    *   **SOV-3: Data & AI** (Control de datos, hosting de modelos, propiedad de prompts y cumplimiento del EU AI Act e ISO/IEC 42001).
    *   **SOV-4: Operational** (Autonomía operativa, equipos locales, runbooks).
    *   **SOV-5: Supply Chain** (Procedencia de hardware/firmware, SBOMs, canales de actualización).
    *   **SOV-6: Technology** (Independencia del stack de cómputo, aceleradores y estándares abiertos).
    *   **SOV-7: Security & Compliance** (Control de SOC, SIEM, identidades privilegiadas y continuidad segura).
    *   **SOV-8: Environmental Sustainability** (Eficiencia, PUE, consumos y transparencia de emisiones).
2.  **Modelo de Aseguramiento SEAL (SEAL-0 a SEAL-4):**
    *   **SEAL-0: Sin soberanía** (Control absoluto por actores no-UE).
    *   **SEAL-1: Soberanía Jurisdiccional** (Aplica ley de la UE, pero el control operativo efectivo es de proveedores no-UE).
    *   **SEAL-2: Soberanía de Datos** (Protección legal UE, con dependencias no-UE significativas).
    *   **SEAL-3: Resiliencia Digital** (Control efectivo retenido localmente, dependencias no-UE muy limitadas).
    *   **SEAL-4: Soberanía Digital Completa** (Operación en la UE bajo control total, sin dependencias materiales externas).

---

## 2. Estrategia de Reutilización de la Infraestructura de assessment-engine

La arquitectura hexagonal, el motor de políticas y el pipeline asíncronos del `assessment-engine` son 100% reutilizables y permiten industrializar este análisis de 3 meses, reduciendo los tiempos de ejecución mediante aceleración por IA controlada (Human-in-the-loop).

```text
===================================================================================================
| EVIDENCIAS RAW (IAG) ➔ [ INGEST / RAPTOR ] ➔ EVIDENCE VAULT ➔ [ INTEL HARVEST ] ➔ CLIENT INTEL |
===================================================================================================
                                                                             │
                                                                             ▼ (Pipelines SOV-1 a SOV-8)
===================================================================================================
| SOV BLUEPRINTS (SEAL) ➔ [ SOVEREIGN POLICY ENGINE ] ➔ MATURITY REPORT & HEATMAPS (D3.1 / D3.2)  |
===================================================================================================
```

### A. Ingestión y RAG de Evidencias (Fase 2 - Discovery)
*   **Reutilización:** El componente de ingesta de evidencias (`evidence_engine.py` y `raptor_engine.py`) puede procesar masivamente los documentos que entregará IAG (contratos, SLAs, DPAs, diagramas de arquitectura y configuraciones de nube).
*   **Impacto:** Automatiza la generación del **D2.1 Evidence Collection Tracker** y el pre-llenado de los **D2.2 Completed Assessment Questionnaires**, extrayendo cláusulas de jurisdicción y patrones de acceso mediante búsquedas semánticas y RAG local.

### B. Mapeo de la Jerarquía Holding-Filial (OpCos)
*   **Reutilización:** El esquema de datos de `src/assessment_engine/domain/schemas/intelligence.py` ya define nativamente la jerarquía Holding -> Filial con campos avanzados para `technical_stack` y `field_metrics`.
*   **Impacto:** Permite modelar a IAG como Holding y a las 10 OpCos (Iberia, Vueling, BA, etc.) como filiales bajo el mismo archivo `client_intelligence.json`, automatizando el mapeo de dependencias para el **D1.3 Prioritized Assessment Inventory**.

### C. Remapeo de Torres Técnicas a Dimensiones de Soberanía (Towers ➔ SOV-x)
*   **Reutilización:** El motor está diseñado para ejecutar pipelines por torres tecnológicas (T1, T2, etc.). Podemos re-mapear las torres para representar los Sovereignty Objectives (SOV-1 a SOV-8).
*   **Impacto:** Al ejecutar `run_tower_pipeline.py --tower SOV3...`, el sistema procesará la evidencia específica de esa dimensión de soberanía, validará contra los esquemas Pydantic de `blueprint.py` y generará un "Sovereignty Objective Blueprint" robusto y estructurado para cada una.

### D. Motor de Puntuación SEAL Automatizado
*   **Reutilización:** Adaptar `src/assessment_engine/domain/maturity_band.py` y `run_scoring.py` para mapear los rangos de cumplimiento de los criterios directamente a los niveles **SEAL-0 a SEAL-4**.
*   **Impacto:** Cálculo matemático preciso y determinista de las notas SEAL ponderadas por aplicación, OpCo y a nivel consolidado de Grupo IAG, generando de forma automática los datos para la matriz **D3.1 Sovereignty Maturity Report**.

### E. Sovereign Policy Engine y Análisis de Riesgos FAIR
*   **Reutilización:** El motor de políticas (`policy_engine.py`) y la política `FairRiskPolicy` (alimentada por `fair_risk_profiles.json`) pueden cruzarse con las variables de exposición extraterritorial (FISA 702 / CLOUD Act).
*   **Impacto:** Si una aplicación crítica almacena datos sensibles en regiones fuera de la UE o utiliza un proveedor con administración privileged no controlada, el motor de políticas puede calcular el riesgo de pérdida financiera anual estimada (ALE) por sanciones o fugas, inyectando de forma automática medidas paliativas obligatorias y re-secuenciando los proyectos de remediación.

### F. Compilación de Entregables e Interactive Web Presentation
*   **Reutilización:** Los componentes `docx_compiler.py` y `render_web_presentation.py` pueden configurarse con plantillas específicas de soberanía.
*   **Impacto:** Generación automatizada bit a bit del informe consolidado **D3.1 Sovereignty Maturity Report** y **D3.2 Main Findings Executive Summary** en Word, además de un cuadro de mando HTML interactivo en `presentation/index.html` con gráficos de radar y mapas de calor por OpCo.

---

## 3. Foco de Profundización para el Dominio de Infraestructura (Su Responsabilidad)

Para ir más allá de la propuesta y aportar un valor técnico diferencial al comité de dirección de IAG, su análisis de infraestructura debe estructurarse e incrementar los siguientes puntos de control:

### A. Soberanía Jurisdiccional y Cifrado con Claves Externas (Hold Your Own Key - HYOK)
*   **El Riesgo:** Las multinacionales creen que por hospedar datos en regiones europeas (ej. AWS `eu-west-1` en Dublín o `eu-south-2` en Aragón) están exentas del CLOUD Act de EE. UU. Sin embargo, si la matriz proveedora es estadounidense, las autoridades de EE. UU. pueden obligar legalmente a la empresa a desencriptar los datos si las claves son gestionadas por el propio hyperscaler.
*   **La Remediación en Infraestructura:** Debe auditar si existen esquemas de **HYOK** u **External Key Store (EKS)**. El control de las claves de cifrado debe residir físicamente en módulos HSM locales gestionados por un custodio europeo independiente. Esto garantiza de forma física la soberanía, haciendo que los datos sean técnicamente ilegibles ante requerimientos de agencias externas.

### B. Rutas de Privilegios y Soporte Transfronterizo (Follow-the-Sun Operational Escapes)
*   **El Riesgo:** Los hyperscalers operan redes de soporte globales con ingenieros de guardia en todo el mundo. Si un ingeniero en EE. UU., India o Filipinas se conecta para resolver un problema de infraestructura de un sistema crítico de IAG, se ha producido un acceso transfronterizo fuera de la jurisdicción europea, violando la soberanía de control y exponiendo datos sensibles.
*   **La Remediación en Infraestructura:** Evaluar la implementación de perímetros de soporte restringidos exclusivamente a personal en territorio europeo de la UE/UK (*EU-only administrative paths*) y la adopción de esquemas de accesos just-in-time restringidos por software (como AWS Sovereign Shield o Google Sovereign Cloud partners).

### C. Soberanía en la Evolución de la IA (Cómputo, Pesos y Datos)
*   **El Riesgo:** IAG busca definir "quién debe tener la soberanía y propiedad de la IA". Si IAG depende únicamente de APIs de modelos comerciales cerrados basados en EE. UU. (como OpenAI o Anthropic):
    1.  Se exponen a fugas de propiedad intelectual (los prompts de negocio y datos del cliente entran en el flujo de los proveedores externos).
    2.  Carecen de control operativo sobre el ciclo de vida del modelo (depreciación de versiones, cambios en el alineamiento).
    3.  Existe un lock-in absoluto con el hardware del proveedor.
*   **La Remediación en Infraestructura:** Proponer un modelo de **Soberanía Híbrida de IA** en infraestructura:
    *   **Cómputo:** Evaluar dónde residen físicamente las unidades de procesamiento (GPUs). ¿Se ejecutan inferencias en clústeres locales, en nubes privadas virtuales soberanas o mediante hyperscalers con aislamiento garantizado?
    *   **Modelos de Pesos Abiertos (Open-Weight Models):** Proponer el despliegue de modelos abiertos de alto rendimiento (ej. Llama 3 o Mistral Large) alojados y ejecutados en infraestructura local o nubes soberanas europeas controladas por IAG. Esto retiene el 100% de la propiedad intelectual de los prompts, los pesos ajustados (fine-tuning) y los datos de entrenamiento.

### D. Portabilidad de Plataforma y Salida Segura (Exit Complexity & DORA)
*   **El Riesgo:** Concentración severa en un hyperscaler específico que imposibilita una migración en plazos razonables, violando las directivas NIS2 y DORA sobre resiliencia e inmunidad operativa.
*   **La Remediación en Infraestructura:** Evaluar la independencia de la arquitectura mediante capas de abstracción abiertas (como Red Hat OpenShift o Kubernetes agnóstico) y el almacenamiento distribuido compatible con S3 independiente del proveedor. Esto permite portar cargas críticas on-premise de forma rápida en escenarios de rescisión contractual o disputas jurisdiccionales.

---

## Recomendación de Siguientes Pasos

Este análisis demuestra que el 90% del motor de `assessment-engine` es directamente reutilizable. El trabajo principal consistirá en:
1.  **Adaptar los esquemas de datos** para sustituir los campos genéricos por dimensiones de objetivos de soberanía (SOV-1 a SOV-8).
2.  **Configurar el motor de políticas** para inyectar de forma determinista mitigaciones de soberanía e HYOK.
3.  **Diseñar las plantillas de prompts** orientadas específicamente al análisis de contratos (SLA/DPA) e infraestructura soberana.
