---
status: Verified
owner: docs-governance
source_of_truth:
  - src/business_command_center/README.md
last_verified_against: '2026-05-02'
applies_to:
  - humans
doc_type: canonical
---
# Assessment Engine Command Center: SOTA Orchestrator (Edición 2026)

## Objetivo
Convertir el "Command Center" en la **Interfaz Gráfica Definitiva (GUI) para el `Product Owner Orchestrator`** de Python. 
El sistema fusiona el flujo local de desarrollo con las tecnologías de vanguardia de 2026 (Model Context Protocol avanzado, Human-in-the-Loop determinista y grafos de razonamiento) para garantizar un código perfecto, auditable y alineado con la arquitectura ("Golden Paths").

---

## Fase 1: La Interfaz de Petición (El "Prompt" de Negocio)
Reemplazar la CLI (`bin/po-run`) por un Command Center conversacional e hiper-conectado.
- **Chat/Command Input Integrado**: La Paleta de Comandos (`Ctrl+Shift+P`) es el "cerebro". El Product Owner escribe su necesidad (ej: "Endurecer la reconciliación de PRs").
- **Conexión MCP (Capa Base)**: Establecer una conexión real-time (WebSockets/SSE) con el servidor MCP de Python, exponiendo el tool `run_product_owner_orchestrator.py` a la interfaz React.

---

## Fase 2: Planificación, "Blast Radius", Alternativas y Aprobación (Pre-Flight)
Visualizar el output del `product_owner_planner` con telemetría predictiva antes de tocar el código.
- **Generación de Alternativas (The 3-Way Pattern) 🚀 [SOTA]**: El orquestador no devuelve un único plan, sino 3 alternativas distintas (ej: Rápido, Refactor Profundo, Seguro). La UI permite comparar los enfoques.
- **Multi-Agent Debate & Critic 🚀 [SOTA]**: Antes de presentar las alternativas, un agente 'Critic' evalúa los planes buscando fallos de seguridad o invariantes rotos, asegurando un consenso multi-agente de alta calidad.
- **Renderizado del Plan Global**: Mostrar en el Lienzo Dinámico (ArtifactCanvas) la Spec Mínima, rama, título de PR y riesgo asociado del plan seleccionado.
- **Análisis de Impacto ("Blast Radius") 🚀 [SOTA]**: Un agente evaluador invisible analiza el plan y muestra un minimapa visual de los archivos y sistemas críticos que serán alterados, alertando si el alcance cruza dominios no previstos.
- **Desglose en Kanban**: Inyectar automáticamente las "tareas pequeñas" (con su `source_of_truth` e `invariants`) en la columna "Backlog".
- **Aprobación de Arquitecto (Gate 1)**: Un botón maestro "Approve & Execute" que requiere confirmación humana para iniciar la mutación del código.

---

## Fase 3: The Apex - Ejecución Gobernanza por Agentes (Completada)
Monitorizar la ejecución automática del agente (`gemini-2.5-pro`) con capacidad de interrupción y bajo la supervisión de un sistema de agentes especializados que garantizan la calidad y el cumplimiento normativo.
- **Streaming de Estados en Vivo**: Las tarjetas se mueven solas a "In Progress". Se visualiza la fase real ("Pensando", "Codificando", "Ejecutando Pytest").
- **Terminal Incrustada (Live Logs)**: Consola dentro de la tarjeta de tarea mostrando el `stdout/stderr` de los Quality Gates locales.
- **Human-in-the-Loop (HITL) Dinámico 🚀 [SOTA]**: Implementación de la directiva `elicitInput()` de MCP. Si el agente encuentra una ambigüedad arquitectónica crítica que no puede resolver con certeza, la ejecución se pausa y la UI muestra un modal solicitando al Arquitecto una micro-decisión (ej. elegir entre dos patrones de diseño). Al responder, el agente continúa.
- **Nota sobre Implementación**: El concepto de "Shadow Routing" (ejecutar un segundo modelo en paralelo para comparación) fue descartado en favor de un sistema de validación y firma más robusto y determinista, liderado por los agentes `Doctor`, `Verification` y `Liability Signer`, que operan sobre los artefactos generados por el agente primario.

---

## Fase 4: Eficiencia Operativa, Checkpointing y Reconciliación ("Close the Loop")
Llevar la arquitectura al siguiente nivel de resiliencia y eficiencia, abandonando el reintento desde cero en favor de una máquina de estados determinista.
- **State Checkpointing y DAG Orchestration 🚀 [SOTA]**: El orquestador guarda su estado interno tras cada micro-paso (Worker Done, Verification Done, Commit Done). Si ocurre un fallo de red, de infraestructura o un Action Gate requiere intervención, al reanudar, el sistema salta directamente al punto de fallo en lugar de reiniciar todo el pipeline, reduciendo drásticamente los tiempos de espera y el consumo de tokens.
- **Estado de GitHub en Vivo**: Tarjeta resumen con el PR number y el estado de los checks de GitHub Actions.
- **Monitor de Reconciliación Automática**: Visualizar el bucle del watcher (`orchestrator-pr-reconcile.yml`). Si GitHub falla, la UI muestra cómo el agente descarga el feedback y aplica el parche.
- **Trazabilidad "Time-Travel"**: Si una tarea fracasa repetidamente (ej. falla typing 3 veces), la UI permite desplegar un "Árbol de Razonamiento". El usuario puede ver visualmente qué estrategia intentó el agente en el Intento 1, el error que obtuvo, y por qué decidió pivotar en el Intento 2.
