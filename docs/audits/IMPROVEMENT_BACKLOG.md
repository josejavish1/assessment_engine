---
status: Verified
owner: docs-governance
source_of_truth:
- ../../docs/
- ../../src/assessment_engine/
last_verified_against: 2026-06-26
applies_to:
- humans
doc_type: operational
diataxis: explanation
verification_mode: editorial
---
# Backlog de Mejoras de Documentación y Código

## 1. Introducción

Este documento contiene el backlog priorizado de tareas de mejora, derivado de los hallazgos de la auditoría en [`AUDIT_RESULTS.md`](./AUDIT_RESULTS.md). Cada elemento de esta lista ha sido clasificado por prioridad, asociando notas de resolución para aquellos hitos **completamente cerrados y validados** durante nuestra gran campaña de saneamiento masivo.

## 2. Prioridades

La priorización se basa en el impacto y el esfuerzo estimado:

*   **P1 (Crítico):** Arreglos que desbloquean la velocidad de desarrollo, corrigen información peligrosamente incorrecta o mejoran significativamente la incorporación de nuevos miembros.
*   **P2 (Importante):** Mejoras que aumentan la claridad y completitud de la documentación core.
*   **P3 (Recomendado):** Tareas de pulido y completitud que mejoran la calidad de vida del desarrollador.

---

## 3. Backlog de Ingeniería y Resoluciones

| Prioridad | Área | Título de la Tarea | Descripción / Estado de Resolución | Hallazgo Relacionado |
|---|---|---|---|---|
| **P1** | FinOps | Context Caching Nativo (Vertex AI) | Implementar caché de contexto para el ADN estratégico y contexto de negocio en `run_tower_pipeline.py`. | Roadmap Fase 1 |
| **P1** | FinOps | Token Throttling por Rol | **[RESOLVED & CLOSED]** Configurados límites estrictos de `max_output_tokens` en `model_profiles.json` según el rol de agente para evitar alucinaciones. | Roadmap Fase 1 |
| **P1** | Seguridad | Sandboxing Estricto de Ejecución | Migrar el agente ejecutor para que las herramientas (`run_command`) se ejecuten dentro de contenedores efímeros sin red (Docker/gVisor). | Estrategia DevSecOps 2026 |
| **P1** | Documentación | Actualizar las instrucciones de instalación en `docs/operations/installation.md` | **[RESOLVED & CLOSED]** Unificadas de forma aséptica todas las instrucciones de instalación con `.venv` y `pyproject.toml`, eliminando `PYTHONPATH`. | `AUDIT_RESULTS.md` |
| **P1** | Código | Añadir Docstrings a los Pipelines Principales | Añadir docstrings a nivel de módulo y función a `run_tower_pipeline.py`, `run_global_pipeline.py`, y `run_commercial_pipeline.py`. | `AUDIT_RESULTS.md` |
| **P2** | Operaciones | Resiliencia de Arranque (Boot Persistence) | Configurar `loginctl enable-linger` para que los servicios arranquen automáticamente en el boot sin requerir login interactivo. | Fiabilidad de Infraestructura |
| **P2** | Robustez de la Plataforma | Resiliencia de Pipeline y Contratos Estrictos | Implementar Checkpointing, exponential backoff, y contratos estrictos con Pydantic para el output de la IA. | Escalabilidad de Día 2 |
| **P2** | Clean Architecture | Erradicación de Entropía y Convenciones Estrictas | **[RESOLVED & CLOSED]** Purgados backups manuales `.tar.gz`, eliminada carpeta `scripts/`, renombradas plantillas `.docx` sin números de versión e inyección aislada en `working/`. | Análisis de Entropía |
| **P2** | Clean Code | Refactorización Sistémica Incremental | Refactorizar `src/` aplicando "Boy Scout Rule", eliminando "God Scripts" y código zombi. | Análisis de Deuda Técnica |
| **P2** | Clean Code | Erradicación de "Swallowed Exceptions" | Reemplazar bloques `except Exception` vacíos por excepciones tipadas e integradas con Structured Logging JSON. | Análisis de Deuda Técnica |
| **P2** | DevSecOps | Auto-Curación de Vulnerabilidades SAST | Integrar Bandit en `VerificationAgent` y conectar alertas al `Agente Doctor` para auto-reparación en `Shadow Workspace`. | Estrategia DevSecOps 2026 |
| **P2** | DevSecOps | Bloqueo Estricto de Secretos | Integrar TruffleHog en el validador del orquestador para bloquear commits que filtren credenciales. | Estrategia DevSecOps 2026 |
| **P2** | Documentación | Completar el README en `docs/architecture/README.md` | **[RESOLVED & CLOSED]** Rediseñado por completo el README para indexar la arquitectura actual con el formato estructurado Diataxis y mapas de lectura. | `AUDIT_RESULTS.md` |
| **P2** | Documentación | Validar y anotar el diagrama en `docs/SYSTEM_ARCHITECTURE.md` | **[RESOLVED & CLOSED]** Actualizada la cabecera Front-Matter, anotado el diagrama con RAGE e infraestructuras latentes de forma aséptica. | `AUDIT_RESULTS.md` |
| **P2** | Código | Mejorar el Manejo de Errores en los Pipelines | Implementar manejo de errores robusto en los scripts de pipelines ante falta de artefactos de entrada. | `AUDIT_RESULTS.md` |
| **P3** | DevSecOps | Escudo Anti-Inyección (Prompt Shield) | Añadir middleware de sanitización (NeMo Guardrails ligero) en la carga de documentos para prevenir Jailbreaks. | Estrategia DevSecOps 2026 |
| **P3** | Documentación | Renderizado de Documentación | Configurar MkDocs Material para la carpeta `docs/` para mejorar la lectura visual corporativa. | Deuda Estética |
| **P3** | Documentación | Añadir metadatos de propiedad a los documentos | **[RESOLVED & CLOSED]** Auditados todos los Markdown activos de la plataforma para asegurar que cuentan con Front-Matter estricto en estado Verified. | `AUDIT_RESULTS.md` |
| **P3** | Código | Añadir Docstrings a `config_loader.py` | **[RESOLVED & CLOSED]** Agregados docstrings de alto nivel, type annotations y especificaciones completas a todas las funciones de `config_loader.py`. | `AUDIT_RESULTS.md` |
