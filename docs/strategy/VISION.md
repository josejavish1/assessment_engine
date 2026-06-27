---
status: Needs Review
owner: docs-governance
source_of_truth:
- src/assessment_engine/infrastructure/epistemic_graph.py
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
---
# Architectural Vision: The Sovereign Agentic OS

Este documento establece la "Estrella del Norte" conceptual y estratégica a largo plazo (3-5 años) del motor. Define el porqué de la evolución hacia un sistema operativo de agentes y los principios cognitivos que neutralizan los riesgos de alucinación e inconsistencia en entornos corporativos B2B.

---

## 1. El Problema Base: Silos de Datos y Amnesia de Cliente

El modelo tradicional de consultoría y de herramientas de diagnóstico opera en silos temporales y de datos:

1.  **Fricción en Nuevos Productos:** La especialización por "Torres" (Cómputo, Redes, Datos) obliga a duplicar preguntas de gobernanza o resiliencia en múltiples cuestionarios, aumentando la fricción en el cliente.
2.  **Amnesia de Cuenta:** Si un cliente realiza un diagnóstico de Nube en Enero y uno de Ciberseguridad en Octubre, el sistema vuelve a interrogarle sobre variables que ya conoce, ignorando la memoria institucional de la cuenta.
3.  **Rigidez en la Agregación:** La correlación entre torres y su alineación con los objetivos ejecutivos depende en su totalidad del razonamiento probabilístico de la IA en tiempo de inferencia, exponiendo al informe a alucinaciones de aserción.

---

## 2. La Resolución: El Grafo Epistémico y GitOps SOTA

Para resolver estas deudas de forma definitiva, la plataforma evoluciona hacia una **Arquitectura de Inferencia Activa** sustentada en el control GitOps y la persistencia de aserciones del Grafo Epistémico:

### 2.1. GitOps como el CMS Headless
En el desarrollo de software SOTA, duplicar el estado entre un portal externo de administración de datos y el repositorio es un anti-patrón (*State Drift*).
*   **La Regla:** El control permanece en Git. Los consultores y arquitectos editan de forma directa los archivos declarativos JSON/YAML bajo `engine_config/`. Esto garantiza trazabilidad criptográfica total, rollback instantáneo de cambios (Ctrl+Z) y disciplina mediante Pull Requests.
*   **El Compilador de Conocimiento:** El grafo epistémico (`epistemic_graph.py`) no es una base de datos aislada que los humanos modifican manualmente de forma insegura; es un **artefacto compilado**. Lee el repositorio GitOps plano en caliente y proyecta el Grafo de tripletas semánticas resultante de forma determinista.

### 2.2. Memoria Episódica con Decaimiento Temporal (TTL)
La plataforma no olvida; trata el diagnóstico del cliente como un **Gemelo Digital vivo**.
*   **El Grafo de Tripletas:** Almacena hechos inmutables mediante el rastro secuencial (`Sujeto -> Predicado -> Objeto -> Timestamp -> Confianza`).
*   **Decaimiento (Time-To-Live):** No todos los datos caducan al mismo tiempo. El proveedor de Cloud seleccionado por el cliente (ej. AWS) tiene un TTL de 3 años; el estado de automatización de sus pipelines de CI tiene un TTL de 6 meses.
*   **Evaluación Incremental:** Al iniciar un nuevo assessment, el sistema sólo pregunta el delta faltante o re-valida datos próximos a caducar de forma asistida, reduciendo la fricción a cero y habilitando un modelo de *Continuous Readiness*.

---

## 3. Principios de Inferencia de Élite

La plataforma implementa tres disciplinas cognitivas para neutralizar los riesgos de la IA generativa:

1.  **Minimización de la Entropía (Active Inference):** Los agentes operan bajo una capa de control matemática que busca minimizar la "Sorpresa" (Free Energy Principle). Ante inconsistencias de datos o falta de telemetría (alta entropía), el agente está programado para suspender la generación e iniciar búsquedas de ganancia de información (OSINT/RAGE) en lugar de intentar predecir una respuesta falsa.
2.  **Precedencia Epistémica Determinista:** Si la IA extrae por OSINT de forma probabilística que el cliente usa Azure (nivel de confianza 0.4), pero el cliente declara formalmente en su cuestionario que usa AWS (nivel de confianza 1.0), el compilador de Python destruye de forma matemática la aserción de Azure antes de enviar el contexto a la ventana de inferencia del LLM, garantizando un 0% de alucinación cruzada.
3.  **Economía Cognitiva Interna:** El orquestador opera como un mercado de tareas. Las subtareas de un PR o plan de trabajo se subastan internamente, garantizando que siempre interviene la combinación de agentes y LLMs más eficiente (enrutamiento de coste/razonamiento) para optimizar el FinOps de la operación.
