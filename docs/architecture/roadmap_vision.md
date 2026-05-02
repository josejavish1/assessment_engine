# Visión Arquitectónica: Hacia el Sistema Operativo Agentic

Este documento establece la hoja de ruta estratégica para evolucionar el Assessment Engine desde un orquestador CLI avanzado hacia una plataforma de ingeniería agentic "Top Mundial" (estándar 2026).

## Roadmap de Evolución de la Plataforma

### Fase 1: Golden Paths & Architectural Fitness Functions (Completado)
**Objetivo:** Eliminar la improvisación de los agentes y asegurar consistencia estructural.
*   Implementación de plantillas estándar (`templates/golden_paths/`) para APIs, workers y tests.
*   Gobernanza mediante `AGENTS.md`.
*   Verificación automática (Policy-as-Code) en CI/CD mediante `run_golden_path_check.py` para evitar que se creen archivos fuera del estándar.

### Fase 2: Observabilidad Zero-Code en VMs (En curso)
**Objetivo:** Visibilidad 100% 360 del código de negocio y del orquestador, sin acoplamiento.
*   Adopción de *Structured JSON Logging* en todo el código base (Assessment + Orquestador).
*   Eliminación de decoradores intrusivos en favor de auto-instrumentación (`opentelemetry-instrument`).
*   Correlación nativa con el Ops Agent de Google Cloud (`logging.googleapis.com/trace`).
*   Refactorización masiva de deuda técnica heredada (conversión de `print` a `logger.info`).

### Fase 3: Agent Evals & Behavior CI/CD (Próximo paso)
**Objetivo:** Verificar el comportamiento del orquestador y los agentes de forma automatizada (Red Teaming local).
*   Creación de `tests/agent_evals/` con peticiones trampa (destructivas, out-of-scope, fuga de secretos).
*   Pipelines en GitHub Actions que validan que el agente planificador (Product Owner Planner) rechaza acciones peligrosas o exige aprobación humana antes de modificar código crítico.
*   Garantizar que el agente respeta las *Invariantes* del proyecto de manera consistente.

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
