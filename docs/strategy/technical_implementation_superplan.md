---
status: Needs Review
owner: docs-governance
applies_to:
- humans
doc_type: canonical
last_verified_against: 2026-06-27
source_of_truth:
- README.md
diataxis: explanation
verification_mode: editorial
---
# Plan de Implementación Técnica: Sovereign AI Engine

Este documento detalla la hoja de ruta técnica exhaustiva para construir el **NTT Sovereign AI Engine**, el Meta-Framework de grado empresarial diseñado para orquestar agentes de IA bajo estrictas normativas B2B.

---

## 1. Delimitación de Fronteras: El Paradigma "Platform vs Application"

Para garantizar que el motor sea universal y reutilizable por cualquier área de NTT DATA, se establece una frontera arquitectónica infranqueable:

### ⚙️ El "Sovereign Engine" (La Plataforma)
Es la infraestructura subyacente. Carece de contexto de negocio. No sabe qué es una auditoría de código, ni un contrato legal. Sus únicas responsabilidades son:
*   **Orquestación y Estado (Durable Execution):** Wrapper sobre LangGraph para manejar grafos de estado, reintentos y Checkpointing automático en base de datos.
*   **Gobernanza y Sandboxing:** Implementación nativa de ejecución aislada en Docker Fortificado (Rootless, no-net).
*   **Observabilidad Forense (Trazabilidad):** Generación de la "Burbuja Causal" mediante OpenTelemetry y LangSmith para auditorías legales.
*   **Smart Parsing / Ingesta:** Módulo de pre-procesamiento inteligente para transformar documentos complejos a Markdown canónico antes del análisis LLM.
*   **FinOps:** Token Throttling y enrutamiento por capacidades (Gateway LLM).

### 🏢 Las "Aplicaciones Cliente" (Ej. Fast Assessment Tool)
Son las herramientas de negocio que se construyen *encima* del motor.
*   **Lógica de Dominio:** Criterios de puntuación, metodologías específicas, diccionarios de evaluación.
*   **Modelos de Datos Pydantic:** Definen los contratos exactos que el motor debe obligar a cumplir a los agentes.
*   **Renderizadores de Entregables:** Scripts que transforman el JSON final aprobado por el motor en documentos corporativos finales.

---

## 2. Asimilación de las Dimensiones de Élite (Arquitectura Core)

El **Sovereign Engine** integrará las siguientes primitivas técnicas:

### Dimensión 1: Control y Flujo (Orquestación Contractual)
*   **Durable Execution (Wrapper LangGraph):** Todo flujo se compila en un Grafo de Estados con *Checkpointing* persistente (Postgres). Si el proceso falla, se reanuda desde el último nodo exitoso.
*   **Contract-Driven Execution:** El motor inyecta validación Pydantic estricta entre nodos. El grafo no avanza si la salida de un agente no cumple matemáticamente el contrato, disparando un bucle de auto-reparación.
*   **Asynchronous HITL (Human-in-the-Loop):** Capacidad de pausar grafos de larga duración para requerir aprobación humana vía canales corporativos (Teams, WhatsApp) antes de acciones críticas.

### Dimensión 2: Estado y Memoria
*   **State Schemas Estrictos:** La memoria a corto plazo compartida es fuertemente tipada.
*   **Memoria Episódica Iterativa:** Fase 1 mediante Vector RAG (`pgvector`) para historial básico. Fase 2 mediante Grafos Temporales (Zep/Graphiti) para retener el contexto relacional "Quién/Cuándo/Qué" sin *State Drift*.

### Dimensión 3: Aislamiento (Sandbox Epistémico)
*   **Shadow Workspace (Docker Fortificado):** Primitiva de ejecución aislada integrada en el SDK. Los agentes ejecutan tests o validaciones en contenedores efímeros (`--read-only`, `--network=none`) garantizando riesgo cero para el host de NTT DATA o del cliente.
*   **Integración MCP Segura:** Uso del Model Context Protocol para enchufar herramientas pre-aprobadas, manteniendo el control de acceso corporativo.

### Dimensión 4: Observabilidad y Debugging Forense
*   **Nested Tracing B2B (OpenTelemetry):** Árboles causales de ejecución. Permite auditar qué prompt, qué herramienta y qué contexto exacto generaron cada decisión del agente, vital para Compliance y justificación ante clientes.

### Dimensión 5: Economía y Tuning (FinOps)
*   **Gateway LLM:** Router interno que desvía tareas deterministas a modelos rápidos y tareas de alto razonamiento a modelos frontera.
*   **Smart Ingestion Pipeline:** Conversión de documentos no estructurados (PDFs, Web) a formatos digeribles antes del procesamiento, reduciendo la ventana de contexto y los costes.

---

## 3. Hoja de Ruta Táctica (Fases de Implementación del Framework)

### Fase 0: Andamiaje del Framework y FinOps Inmediato
*   **Acción:** Construir el SDK base y la infraestructura mínima.
*   **Backlog Integrado:**
    *   Definición de Clases Abstractas (`NttAgent`, `NttState`).
    *   Integración de LangGraph como motor subyacente.
    *   Gateway LLM y Caching Semántico (Vertex AI).
*   **Entregable:** Paquete `ntt_sovereign_engine` básico que abstrae el orquestador, maneja estado fuertemente tipado y expone la API de desarrollo.

### Fase 1: Sandbox Epistémico y Trazabilidad Forense
*   **Acción:** Blindar la ejecución y encender la telemetría.
*   **Backlog Integrado:**
    *   Implementar `SandboxAdapter` con Docker Fortificado.
    *   Integrar OpenTelemetry para trazas causales.
    *   Mecanismo *Contract-Driven* de auto-reparación de Pydantic.
*   **Entregable:** Un motor capaz de orquestar código aislado y trazar matemáticamente cada decisión de los agentes en LangSmith/OpenTelemetry.

### Fase 2: Ingesta Inteligente y Memoria Vectorial
*   **Acción:** Resolver el problema del "ruido" y recordar el pasado.
*   **Backlog Integrado:**
    *   Módulo de *Smart Parsing* (pre-procesamiento de documentos complejos).
    *   Implementar RAG Vectorial con `pgvector` sobre la base de datos de Checkpointing.
*   **Entregable:** Los agentes reciben Markdown semántico limpio y pueden consultar resoluciones pasadas guardadas en la base de datos relacional/vectorial.

### Fase 3: Omnicanalidad Asíncrona (HITL Avanzado)
*   **Acción:** Integración del flujo de aprobación B2B.
*   **Backlog Integrado:**
    *   Mecanismos de pausa/rehidratación de grafos (Durable HITL).
    *   Conectores de notificación para aprobación ejecutiva (WhatsApp/Teams/Email).
*   **Entregable:** El framework orquesta pausas de meses, esperando eventos externos corporativos para reanudar operaciones seguras.

### Fase 4: Autonomía y Grafo Temporal (Investigación Futura)
*   **Acción:** Evolución hacia Nivel 5 de autonomía.
*   **Backlog Integrado:**
    *   Sustitución de Memoria Vectorial por Grafos Temporales (Zep/Graphiti).
    *   Auto-Optimización de Prompts (DSPy).
*   **Entregable:** El motor auto-afina la inteligencia de sus aplicaciones y retiene la causalidad del tiempo en su memoria a largo plazo.
