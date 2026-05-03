---
status: Verified
owner: docs-governance
source_of_truth:
  - src/business_command_center/README.md
last_verified_against: '2026-05-03'
applies_to:
  - humans
doc_type: canonical
---
# Assessment Engine Command Center: SOTA Orchestrator (Edición 2026)

## Objetivo
Convertir el "Command Center" en la **Interfaz Gráfica Definitiva (GUI) para el `Product Owner Orchestrator`** de Python. 
El sistema fusiona el flujo local de desarrollo con las tecnologías de vanguardia de 2026 (Model Context Protocol avanzado, Human-in-the-Loop determinista y grafos de razonamiento) para garantizar un código perfecto, auditable y alineado con la arquitectura ("Golden Paths").

---

## Resumen Ejecutivo de Prioridades (ROI Framework)
Basado en una auditoría técnica estricta, las siguientes mejoras pendientes se han reordenado según su Retorno de Inversión (ROI: máximo impacto con el menor riesgo):

| Prioridad | Tarea Pendiente | Impacto (Retorno) | Riesgo / Esfuerzo | Justificación |
|---|---|---|---|---|
| **1** | **Cierre End-to-End (Secretos GH)** | Alto | Muy Bajo | Configurar credenciales de IA en GitHub Actions. Desbloquea la auto-reparación 100% autónoma en la nube. |
| **2** | **Reviewers Automáticos** | Alto | Bajo | Orquestar `gh pr edit --add-reviewer` leyendo el archivo `CODEOWNERS`. Garantiza que todo cambio sea auditado por el humano correcto. |
| **3** | **Micro-Checkpoints (Idempotencia)** | Medio-Alto | Medio | Retomar PRs interrumpidas sin repetir tareas ya completadas, ahorrando tokens y tiempo (Fase 4). |
| **4** | **GUI / Conexión MCP** | Medio | Alto | Desarrollar el frontend React. Es valioso para adopción, pero no debe priorizarse hasta que la capa de terminal exprima todo el valor de la automatización pura (Fases 1 y 2). |

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

## Fase 3.5: The Apex Orchestrator MVP (Completada)
Implementar el núcleo de la arquitectura "The Apex" en el backend del orquestador (`run_product_owner_orchestrator.py`) para garantizar robustez y aislamiento antes de escalar la GUI.
- **Aislamiento Total (Shadow Workspaces) 🚀 [SOTA]**: El orquestador ejecuta las mutaciones de código en un `git worktree` efímero oculto. Esto garantiza un **Blast Radius Cero**: el directorio de trabajo real del Product Owner jamás se corrompe por alucinaciones o comandos destructivos del agente.
- **El Bucle del Doctor (Auto-Curación) 🚀 [SOTA]**: Separación de responsabilidades en la validación. Cuando un Quality Gate falla en el Shadow Workspace, el log de error no se envía al agente codificador, sino al agente **Doctor** (Diagnosticador Puro). El Doctor analiza el fallo, emite un veredicto de seguridad (`is_safe_to_proceed`) y proporciona un plan de remediación exacto, evitando la "ceguera de taller" del codificador.

---

## Fase 4: Eficiencia Operativa, Checkpointing e Idempotencia ("Close the Loop")
Llevar la arquitectura al siguiente nivel de resiliencia y eficiencia mediante un enfoque de "Pragmatismo de Élite", abandonando el reintento desde cero sin caer en la sobreingeniería de DAGs asíncronos.
- **Idempotencia y Micro-Checkpoints basados en Git 🚀 [SOTA]**: El orquestador aprovecha el `Git Worktree` como fuente de verdad. Si ocurre un fallo o un Action Gate requiere intervención, al reanudar, el sistema lee el estado real del disco para saltarse las tareas ya completadas, reanudando la ejecución exactamente en la tarea y el intento donde se detuvo. Esto reduce drásticamente los tiempos de espera y el consumo de tokens sin añadir complejidad de bases de datos.
- **Smart Resume (Reanudación Quirúrgica)**: Inyección del feedback autorizado por el Product Owner como contexto inicial en los reintentos tras un Action Gate, asegurando que el Worker sepa exactamente qué corrección aplicar.
- **Estado de GitHub en Vivo**: Tarjeta resumen con el PR number y el estado de los checks de GitHub Actions.
- **Monitor de Reconciliación Automática**: Visualizar el bucle del watcher (`orchestrator-pr-reconcile.yml`). Si GitHub falla, la UI muestra cómo el agente descarga el feedback y aplica el parche.

---

## Fase 5: Dual-Brain Action Gate (Gobernanza por Intención) 🚀 [SOTA] (Completada)
Implementar un "Action Gate" determinista e infranqueable que prevenga matemáticamente que los sub-agentes realicen modificaciones fuera de alcance (Out-of-Scope).

- **Intercepción de Intención (`MutationIntent`)**: Obligar a los agentes Worker (Brain 1) a declarar explícitamente qué archivos van a tocar y por qué, en un formato JSON estructurado, ANTES de realizar cambios físicos.
- **Juez Determinista (Brain 2)**: El orquestador actúa como un juez que valida el `MutationIntent` contra el `in_scope` definido en el Plan. Si hay una discrepancia (ej. el agente intenta tocar código Python cuando solo tiene permiso para Markdown), el Gate se cierra (`ScopeBreachError`) y la ejecución se aborta inmediatamente.
- **Prevención de Alucinaciones**: Esta capa de gobernanza desacopla la *propuesta* de cambio de la *autorización*, eliminando el riesgo de que el agente `Doctor` intente arreglar errores técnicos derivados de cambios de negocio no autorizados.
- **Esquema Pydantic Estricto**: Integración en `product_owner_models.py` para garantizar que la intención sea siempre procesable por código determinista.
