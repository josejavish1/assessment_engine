---
status: Needs Review
owner: docs-governance
source_of_truth:
- ../../src/assessment_engine/business_command_center/README.md
last_verified_against: '2026-06-26'
applies_to:
- humans
doc_type: canonical
diataxis: explanation
verification_mode: mixed
---
# Assessment Engine Command Center: Standard Orchestrator (Edición 2026)

## Objetivo
Establecer el "Command Center" como la **interfaz gráfica de usuario (GUI) para el `Product Owner Orchestrator`** de Python.
El sistema consolida el flujo local de desarrollo con las especificaciones técnicas de 2026 (Model Context Protocol, mecanismos de control Human-in-the-Loop deterministas y grafos de razonamiento) para garantizar un código coherente, verificable y alineado con los estándares del repositorio ("Golden Paths").

---

## Fase 1: La Interfaz de Petición (El "Prompt" de Negocio)
Reemplazar la interfaz de línea de comandos (CLI) por un Command Center interactivo e interconectado.
- **Chat/Command Input Integrado**: La Paleta de Comandos (`Ctrl+Shift+P`) unifica la entrada. El Product Owner escribe su necesidad (ej: "Optimizar la conciliación de Pull Requests").
- **Conexión MCP (Capa Base)**: Establecer una conexión en tiempo real basada en WebSockets/SSE con el servidor MCP de Python, exponiendo las herramientas del `run_product_owner_orchestrator.py` a la interfaz React.

---

## Fase 2: Planificación, "Blast Radius", Alternativas y Aprobación (Pre-Flight)
Visualizar el output del `product_owner_planner` con telemetría analítica antes de realizar mutaciones de código.
- **Generación de Alternativas (The 3-Way Pattern)**: El orquestador propone tres enfoques de planificación estructurados (ej. Optimización Rápida, Refactorización Profunda, o Enfoque Seguro). La interfaz permite evaluar de manera comparativa cada propuesta.
- **Multi-Agent Debate & Critic**: Un agente supervisor ('Critic') evalúa de forma previa los planes propuestos buscando desvíos de seguridad o quiebres de invariantes del sistema, garantizando un consenso técnico riguroso.
- **Lienzo Dinámico de Tareas**: Mostrar en la interfaz visual (ArtifactCanvas) la especificación mínima, rama de trabajo, título de Pull Request y los riesgos operativos calculados.
- **Análisis de Impacto ("Blast Radius")**: Un agente evaluador analiza el plan y dibuja un mapa jerárquico de los archivos y sistemas críticos que serán alterados, alertando si el alcance cruza fronteras no deseadas.
- **Desglose en Tablero Kanban**: Inyectar de manera automatizada las tareas de grano fino (con sus respectivas fuentes de verdad e invariantes de código) en las columnas de control.
- **Aprobación de Arquitectura (Gate 1)**: Control de paso obligatorio que exige validación y aprobación humana manual para iniciar la ejecución del plan.

---

## Fase 3: The Apex - Ejecución de Gobernanza por Agentes (Completada)
Monitorear la ejecución automática del agente codificador bajo la supervisión de un sistema de agentes especializados que garantizan la calidad y el cumplimiento normativo.
- **Streaming de Estados en Tiempo Real**: Visualización de los estados de transición de las tareas ("Pensando", "Codificando", "Ejecutando Pytest").
- **Terminal Incrustada (Live Logs)**: Consola embebida en la UI que muestra la salida estándar (`stdout/stderr`) de los Quality Gates locales en tiempo real.
- **Human-in-the-Loop (HITL) Dinámico**: Implementación de la directiva `elicitInput()` de MCP. Ante ambigüedades arquitectónicas críticas, la ejecución se detiene temporalmente, mostrando un modal para que el arquitecto humano tome la micro-decisión de diseño, tras lo cual el agente continúa.
- **Nota sobre Implementación**: El concepto de "Shadow Routing" (comparación de múltiples modelos en paralelo) fue descartado en favor de un sistema de validación y firma más robusto y determinista, liderado por los agentes especializados `Doctor`, `Verification` y `Liability Signer`.

---

## Fase 3.5: The Apex Orchestrator MVP (Prioridad Inmediata)
Implementar el núcleo de la arquitectura "The Apex" en el backend del orquestador (`run_product_owner_orchestrator.py`) para garantizar robustez y aislamiento antes de escalar la GUI.
- **Aislamiento Total (Shadow Workspaces)**: El orquestador ejecuta las mutaciones de código en un `git worktree` efímero oculto. Esto garantiza un **Blast Radius Cero**: el directorio de trabajo real del Product Owner jamás se corrompe por alucinaciones o comandos destructivos del agente.
- **El Bucle del Doctor (Auto-Curación)**: Separación de responsabilidades en la validación. Cuando un Quality Gate falla en el Shadow Workspace, el log de error no se envía al agente codificador, sino al agente **Doctor** (Diagnosticador Puro). El Doctor analiza el fallo, emite un veredicto de seguridad (`is_safe_to_proceed`) y proporciona un plan de remediación exacto, evitando la "ceguera de taller" del codificador.

---

## Fase 4: Eficiencia Operativa, Checkpointing e Idempotencia ("Close the Loop")
Llevar la arquitectura al siguiente nivel de resiliencia y eficiencia mediante un enfoque de "Pragmatismo de Élite", abandonando el reintento desde cero sin caer en la sobreingeniería de DAGs asíncronos.
- **Idempotencia y Micro-Checkpoints basados en Git**: El orquestador aprovecha el `Git Worktree` como fuente de verdad. Si ocurre un fallo o un Action Gate requiere intervención, al reanudar, el sistema lee el estado real del disco para saltarse las tareas ya completadas, reanudando la ejecución exactamente en la tarea y el intento donde se detuvo. Esto reduce drásticamente los tiempos de espera y el consumo de tokens sin añadir complejidad de bases de datos.
- **Smart Resume (Reanudación Quirúrgica)**: Inyección del feedback autorizado por el Product Owner como contexto inicial en los reintentos tras un Action Gate, asegurando que el Worker sepa exactamente qué corrección aplicar.
- **Estado de GitHub en Vivo**: Tarjeta resumen con el PR number y el estado de los checks de GitHub Actions.
- **Monitor de Reconciliación Automática**: Visualizar el flujo de conciliación automatizado (`orchestrator-pr-reconcile.yml`). Si GitHub falla, la UI muestra cómo el agente descarga el feedback y aplica el parche.
