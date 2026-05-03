# Backlog de Mejoras de Documentación y Código

## 1. Introducción

Este documento contiene un backlog priorizado de tareas de mejora, derivado de los hallazgos de la auditoría en [`AUDIT_RESULTS.md`](./AUDIT_RESULTS.md). Cada elemento de esta lista debería convertirse en un ticket en el sistema de seguimiento de incidencias del proyecto (ej. GitHub Issues).

## 2. Prioridades

La priorización se basa en el impacto y el esfuerzo estimado:

*   **P1 (Crítico):** Arreglos que desbloquean la velocidad de desarrollo, corrigen información peligrosamente incorrecta o mejoran significativamente la incorporación de nuevos miembros.
*   **P2 (Importante):** Mejoras que aumentan la claridad y completitud de la documentación core.
*   **P3 (Recomendado):** Tareas de pulido y completitud que mejoran la calidad de vida del desarrollador.

## 3. Backlog

| Prioridad | Área | Título de la Tarea | Descripción | Hallazgo Relacionado |
|---|---|---|---|---|
| **P1** | Clean Architecture | Migrar Orquestador a Validación Estricta con Pydantic | Refactorizar `run_product_owner_orchestrator.py` para reemplazar la deserialización genérica de `plan.json` (`json.loads`) por la rehidratación tipada estricta (`ProductOwnerAlternatives.model_validate_json`). Esto previene bugs de "ruptura de contrato" y cuelgues por lectura de claves inexistentes. | Diseño de APEX X-Ray |
| **P1** | Clean Architecture | Resiliencia de Pipeline y Remediación Determinista (Zero-AI para Infraestructura) | Implementar Quality Gates que impidan que el orquestador pida a la IA resolver fallos de infraestructura local (ej. `git clean`). Migrar a playbooks de recuperación 100% deterministas en Python. Añadir un `Prompt Adherence Evaluator` y un `Action Gate` humano para operaciones destructivas. | Resiliencia de Día 2 |
| **P1** | FinOps | Context Caching Nativo (Vertex AI) | Implementar caché de contexto para el ADN estratégico y contexto de negocio en `run_tower_pipeline.py`, reduciendo el coste de tokens de entrada hasta un 70%. | Roadmap Fase 1 |
| **P1** | FinOps | Token Throttling por Rol | Configurar límites estrictos de `max_output_tokens` en `model_profiles.json` según la responsabilidad del agente para evitar desperdicio y alucinaciones costosas. | Roadmap Fase 1 |
| **P1** | Seguridad | Sandboxing Estricto de Ejecución | Migrar el agente ejecutor para que las herramientas que modifican archivos o corren comandos (`run_command`) se ejecuten dentro de contenedores efímeros (Docker/gVisor) sin acceso a red, neutralizando ataques de ejecución remota de código (RCE) vía Prompt Injection. | Estrategia DevSecOps 2026 |
| **P1** | Documentación | Actualizar las instrucciones de instalación en `docs/operations/installation.md` | El documento debe reflejar el proceso de instalación moderno con `pyproject.toml` y `pip install -e .`, y eliminar las referencias a `PYTHONPATH`. | `AUDIT_RESULTS.md` |
| **P1** | Código | Añadir Docstrings a los Pipelines Principales | Añadir docstrings a nivel de módulo y función a `run_tower_pipeline.py`, `run_global_pipeline.py`, y `run_commercial_pipeline.py` para explicar su propósito, argumentos y artefactos. | `AUDIT_RESULTS.md` |
| **P2** | Clean Architecture | Meta-Remediación y Autonomía Nivel 5 (El Meta-Sentinel) | Implementar la Fase 5 del Roadmap: crear un `Detector de Bucles por Telemetría` y un `Meta-Sentinel Agent` con ejecución `Out-Of-Band` para rescatar al orquestador de fallos sistémicos (ej. bloqueos de Git o alucinaciones en bucle). | Roadmap Fase 5 |
| **P2** | Operaciones | Resiliencia de Arranque (Boot Persistence) | Configurar `loginctl enable-linger` para el usuario de ejecución, asegurando que los servicios `systemctl --user` (BCC y MCP) arranquen automáticamente en el boot sin requerir login interactivo. | Fiabilidad de Infraestructura |
| **P2** | Robustez SOTA | Resiliencia de Pipeline y Contratos Estrictos | 1) Implementar Checkpointing (Idempotencia) en orquestadores. 2) Añadir Exponential Backoff y Control de Concurrencia para errores 429. 3) Migrar a Contratos Estrictos con Pydantic para el output de IA. | Escalabilidad de Día 2 |
| **P2** | Clean Architecture | Erradicación de Entropía y Convenciones Estrictas | 1) Eliminar backups manuales (`.tar.gz`, `_archive`, `_legacy`). 2) Renombrar plantillas DOCX para eliminar versiones manuales (`v2_6`). 3) Enforzar que el output generado se aísle en `working/out/[client_id]/`. | Análisis de Entropía |
| **P2** | Clean Code | Refactorización Sistémica Incremental (The Great Refactor) | Refactorizar `src/` aplicando la "Boy Scout Rule" (por flujos, usando Golden Datasets como red de seguridad): 1) Desacoplar "God Scripts" (>500 líneas). 2) Sustituir acceso a diccionarios crudos por Pydantic. 3) Mover lógica de negocio hardcodeada a `engine_config/`. 4) Eliminar código zombie. | Análisis de Deuda Técnica |
| **P2** | Clean Code | Erradicación de "Swallowed Exceptions" | Escanear el código base y reemplazar todos los bloques `except Exception` por manejo de excepciones tipado e integrado con un sistema de `Structured Logging (JSON)`, garantizando que ningún error crítico se silencie. | Análisis de Deuda Técnica |
| **P2** | DevSecOps | Auto-Curación de Vulnerabilidades SAST | Integrar Bandit (o reglas de seguridad de Ruff) en el `VerificationAgent`. Conectar las alertas de vulnerabilidad al `Agente Doctor` para que repare el código automáticamente en el `Shadow Workspace`. | Estrategia DevSecOps 2026 |
| **P2** | DevSecOps | Bloqueo Estricto de Secretos | Integrar TruffleHog en la fase de validación del orquestador. Cualquier commit (humano o agente) que intente filtrar credenciales será bloqueado y enviado al ciclo de corrección antes de tocar Git. | Estrategia DevSecOps 2026 |
| **P2** | Documentación | Completar el README en `docs/architecture/README.md` | Añadir una descripción general de la sección de arquitectura, explicando el propósito de cada documento y cómo se relacionan. | `AUDIT_RESULTS.md` |
| **P2** | Documentación | Validar y anotar el diagrama en `docs/SYSTEM_ARCHITECTURE.md` | Añadir una fecha de "última validación" al diagrama de flujo y enriquecerlo con más anotaciones para que sea más claro. | `AUDIT_RESULTS.md` |
| **P2** | Código | Mejorar el Manejo de Errores en los Pipelines | Implementar un manejo de errores más robusto en los scripts de los pipelines para proporcionar feedback claro cuando faltan artefactos o fallan los pasos. | `AUDIT_RESULTS.md` |
| **P3** | DevSecOps | Escudo Anti-Inyección (Prompt Shield) | Añadir un middleware (ej. NeMo Guardrails ligero) que sanitize los documentos subidos por los clientes antes de enviarlos a los prompts de síntesis para prevenir Jailbreaks. | Estrategia DevSecOps 2026 |
| **P3** | Documentación | Renderizado de Documentación | Configurar MkDocs Material (generador de sitios estáticos) para la carpeta `docs/` para mejorar la legibilidad y búsqueda por perfiles no técnicos o en fases de adopción masiva. | Deuda Estética |
| **P3** | Documentación | Añadir metadatos de propiedad a los documentos | Revisar los documentos en `docs/` para asegurar que todos tengan un propietario, fecha de última revisión y estado. | `AUDIT_RESULTS.md` |
| **P3** | Código | Añadir Docstrings a `config_loader.py` | Añadir docstrings a las funciones en `src/assessment_engine/scripts/lib/config_loader.py` para mejorar la claridad. | `AUDIT_RESULTS.md` |
