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

### Fase 4: Arquitectura Dual de Control (Visión Futura)
**Objetivo:** Desacoplar la experiencia de usuario (UX) resolviendo el debate "Build vs Buy", separando la plataforma de Ingeniería de la plataforma de Negocio.

#### 4A: Developer Control Plane (El Motor para Ingeniería)
*   **Usuarios:** Tech Leads y AI Engineers.
*   **Propósito:** Desarrollar nuevas funcionalidades, afinar los agentes y mantener el orquestador (`po-run`).
*   **Enfoque (IDE-First):** Integración nativa del servidor MCP (`mcp_server.py`) directamente en IDEs avanzados (Cursor / VS Code). Cero mantenimiento de frontend. El ingeniero interactúa con los agentes de código directamente sobre los archivos, aprovechando las interfaces *Multi-file Diff* nativas del editor.

#### 4B: Business Command Center (La Interfaz para Clientes/Consultores)
*   **Usuarios:** Consultores, Product Owners y Clientes finales.
*   **Propósito:** Ejecutar los Assessments, visualizar resultados, GAPs y Blueprints.
*   **Enfoque (Custom Web Platform):** 
    *   **Frontend:** Aplicación web dedicada (Next.js + Vercel AI SDK / React Flow) construida de forma acelerada *por* el equipo de agentes de IA usando componentes base (Shadcn/v0).
    *   **UX (Generative UI):** Interfaz limpia y espacial. El consultor no ve código ni JSONs. Ve los "Towers" y "Pillars" del Assessment renderizados dinámicamente como gráficas interactivas, alimentados por el mismo servidor MCP en background.

---
*Nota: Este documento sirve como "North Star" para guiar el desarrollo de los agentes internos del equipo. La construcción de la Fase 4B debe delegarse como una serie de Epics a los agentes del Developer Control Plane.*
