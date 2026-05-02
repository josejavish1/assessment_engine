---
status: Verified
owner: docs-governance
source_of_truth:
  - ../../AGENTS.md
last_verified_against: 2026-05-02
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Visión Arquitectónica: Hacia el Sistema Operativo Agentic

Este documento establece la hoja de ruta estratégica para evolucionar el Assessment Engine desde un orquestador CLI avanzado hacia una plataforma de ingeniería agentic "Top Mundial" (estándar 2026).

## Roadmap de Evolución de la Plataforma

### Fase 1: Golden Paths & Architectural Fitness Functions (Completado)
**Objetivo:** Eliminar la improvisación de los agentes y asegurar consistencia estructural.
*   Implementación de plantillas estándar (`templates/golden_paths/`) para APIs, workers y tests.
*   Gobernanza mediante `AGENTS.md`.
*   Verificación automática (Policy-as-Code) en CI/CD mediante `run_golden_path_check.py` para evitar que se creen archivos fuera del estándar.

### Fase 2: Observabilidad Zero-Code en VMs (Completado)
**Objetivo:** Visibilidad 100% 360 del código de negocio y del orquestador, sin acoplamiento.
*   Adopción de *Structured JSON Logging* en todo el código base (Assessment + Orquestador).
*   Eliminación de decoradores intrusivos en favor de auto-instrumentación (`opentelemetry-instrument`).
*   Correlación nativa con el Ops Agent de Google Cloud (`logging.googleapis.com/trace`).
*   Refactorización masiva de deuda técnica heredada (conversión de `print` a `logger.info`).

### Fase 3: Agent Evals & Evaluation-Led Development (SOTA 2026) (Próximo paso)
**Objetivo:** Medir la confiabilidad, coste y calidad arquitectónica de los agentes antes de enviarlos a producción, sin ralentizar el CI/CD diario.
*   **Golden Dataset:** Creación de un entorno de pruebas con peticiones históricas reales (desde refactors complejos hasta intentos de inyección de código).
*   **Telemetry-Driven Metrics:** Uso de la telemetría (Fase 2) para medir el *Zero-Shot Pass Rate* (¿pasa los Quality Gates a la primera?), el *Code Churn* (reescrituras inútiles) y el coste en dólares por PR.
*   **Shadow PR Review (Maintainer Mergeability):** Uso de un LLM hiper-especializado en un pipeline nocturno para evaluar exclusivamente si el código generado respeta los Golden Paths y las invariantes (Mergeability), evitando el uso de jueces de IA lentos en el flujo diario.

### Fase 4: Agentic Command Center / Dynamic Workspace (Visión Futura)
**Objetivo:** Evolucionar la UX de "Terminal Ciega" y "Git-First asíncrono" a una "Simbiosis Humano-IA" en tiempo real usando MCP.
*   **Paradigma:** Dejar de tratar al agente como un chatbot y tratarlo como un co-procesador dentro de un entorno espacial.
*   **Arquitectura:** 
    *   **Backend:** `mcp_server.py` vitaminado con capacidades de streaming (SSE).
    *   **Frontend:** Aplicación web (Next.js + React Flow / Tldraw) construida *por* el propio equipo de agentes de IA.
*   **Experiencia (UX):**
    *   **Generative UI:** Los planes del orquestador se renderizan como un tablero Kanban o un grafo de dependencias en un lienzo interactivo.
    *   **Co-creación:** El Tech Lead puede arrastrar, modificar, aprobar o eliminar nodos (mini-tareas) visualmente antes de la ejecución.
    *   **Telemetría Viva:** Barras de progreso, *reasoning traces* y visualización de Diffs de código integrados en el frontend durante la fase de *builder*.

---
*Nota: Este documento sirve como "North Star" para guiar el desarrollo de los agentes internos del equipo. Las Fases 3 y 4 deben ser ejecutadas progresivamente delegando el trabajo al orquestador interno.*
