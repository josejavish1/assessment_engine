---
status: Needs Review
owner: docs-governance
source_of_truth:
- docs/operations/engineering-quality-gates.md
- src/assessment_engine/mcp_server.py
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
---
# Product & Infrastructure Roadmap: The Sovereign Engine

Este documento define la hoja de ruta de desarrollo de producto e infraestructura de la plataforma, organizada bajo el estándar de ingeniería **"Now, Next, Later"** (Thematic Horizons) para garantizar la agilidad y predictibilidad del software.

---

## 1. El Paradigma de Aislamiento: "Platform vs Application"

Para garantizar que el motor sea universal y reutilizable por cualquier cuenta, se establece una frontera de diseño estricta:

*   **Sovereign Engine (La Plataforma):** Infraestructura agnóstica de bajo nivel. Carece de contexto de negocio. Gestiona el aislamiento, la orquestación asíncrona, el checkpointing y la telemetría.
*   **Business Applications (La Aplicación):** Lógicas de negocio construidas *sobre* la plataforma. Define las metodologías, los esquemas de datos Pydantic, las políticas de scoring de las torres y los renderizadores de entregables OpenXML (.docx).

---

## 2. Horizontes de Desarrollo Semántico (Thematic Horizons)

```
===================================================================================================
|  NOW (Fase 0 y 1 - En Desarrollo) ➔  NEXT (Fase 2 y 3 - Planificado) ➔  LATER (Fase 4 - Futuro) |
===================================================================================================
```

### 🟢 NOW: Robustez local, FinOps y RAGE Basales
*Objetivo de Negocio: Consolidar la fiabilidad local de los agentes, blindar la seguridad de datos del cliente y optimizar el consumo de APIs.*

-   **[F-GOB] Quality Gate Compliance (¡Implementado!):** Compuertas locales e internacionales que bloquean el commit o merge si el sitemap global o las firmas de tipado se desvían de los "Golden Paths".
-   **[F-MOT] Token Throttling & Caching (¡Implementado!):** Configuración de `max_output_tokens` en `model_profiles.json` por rol de agente y caché de Vertex AI para disminuir costes un 70%.
-   **[F-MOT] El Motor Factual RAGE v3 (¡Implementado!):** Compilación asíncrona de benchmarks y rastro de evidencias físicas mediante búsquedas Google Search y bóveda de PDFs locales para erradicar el *vibe-scoring*.
-   **[F-ARQ] Aislamiento de Ejecución (Shadow Workspaces):** Implementación de la primitiva de mutación de código aislada en un `git worktree` oculto y efímero. **Blast Radius Cero**: las alucinaciones de la IA jamás corrompen el espacio de trabajo local del desarrollador.

---

### 🟡 NEXT: Automatización y Interfaces (MCP / HITL)
*Objetivo de Negocio: Exponer la potencia de los orquestadores locales hacia IDEs y mallas de colaboración interactiva.*

-   **[F-CAB] Developer Control Plane (FastMCP):** Exposición de la totalidad de las herramientas de la fábrica (`cli.py` y orquestadores) a través del protocolo MCP para inyección directa en editores (Cursor / VS Code), eliminando el costo de mantener frontends para ingeniería.
-   **[F-INT] El Bucle del Agente Doctor:** Desacoplamiento del manejo de errores en el Shadow Workspace. Si un test de pytest falla, el log de error no se inyecta al agente programador (evitando su ceguera de taller), sino al agente **Doctor** (Diagnosticador Puro), el cual emite un veredicto de seguridad y le proporciona el plano de reparación exacto al programador.
-   **[F-CAB] Human-in-the-Loop (HITL) Dinámico:** Integración de la directiva `elicitInput()` de MCP. Ante ambigüedades arquitectónicas críticas, la ejecución se detiene, enviando una alerta al canal corporativo (Teams/WhatsApp) para que un arquitecto humano tome la decisión antes de continuar.
-   **[F-INT] Memoria Vectorial y Smart Ingest:** Integración de `pgvector` sobre la base de datos de checkpoints para habilitar RAG semántico y almacenamiento del historial de aserciones.

---

### 🔵 LATER: Autonomía y Gobernanza Avanzada B2B (The Stigmergic Fabric)
*Objetivo de Negocio: Escalar el motor a un sistema descentralizado, neuro-simbólico y legalmente inexpugnable para multinacionales.*

-   **[F-GOB] Firmas Criptográficas de Consentimiento (EU AI Act):** Integración de agentes especializados de cumplimiento y responsabilidad civil (`Liability Signer` y `VerificationAgent`). El sistema genera hashes SHA-256 inmutables de aprobación por cada nodo de decisión de la IA, garantizando que el software cumple con el Artículo 14 de la Ley de Inteligencia Artificial de la Unión Europea.
-   **[F-GOB] Estigmergia Digital (Shared Knowledge Graph):** Eliminación del paso de mensajes jerárquicos tradicionales (que colapsan el orquestador). Los agentes se coordinan dejando marcas semánticas en un Grafo de Conocimiento compartido, permitiendo la colaboración simultánea de miles de agentes con costo lineal de concurrencia.
-   **[F-GOB] Memoria Episódica Temporal:** Sustitución de la base de datos vectorial por Grafos Temporales (Zep/Graphiti) para recordar la causalidad del tiempo ("Quién/Cuándo/Qué") en las cuentas.
