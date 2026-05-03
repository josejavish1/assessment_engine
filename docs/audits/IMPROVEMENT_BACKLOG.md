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
| **P1** | Documentación | Actualizar las instrucciones de instalación en `docs/operations/installation.md` | El documento debe reflejar el proceso de instalación moderno con `pyproject.toml` y `pip install -e .`, y eliminar las referencias a `PYTHONPATH`. | `AUDIT_RESULTS.md` |
| **P1** | Código | Añadir Docstrings a los Pipelines Principales | Añadir docstrings a nivel de módulo y función a `run_tower_pipeline.py`, `run_global_pipeline.py`, y `run_commercial_pipeline.py` para explicar su propósito, argumentos y artefactos. | `AUDIT_RESULTS.md` |
| **P2** | Documentación | Completar el README en `docs/architecture/README.md` | Añadir una descripción general de la sección de arquitectura, explicando el propósito de cada documento y cómo se relacionan. | `AUDIT_RESULTS.md` |
| **P2** | Documentación | Validar y anotar el diagrama en `docs/SYSTEM_ARCHITECTURE.md` | Añadir una fecha de "última validación" al diagrama de flujo y enriquecerlo con más anotaciones para que sea más claro. | `AUDIT_RESULTS.md` |
| **P2** | Código | Mejorar el Manejo de Errores en los Pipelines | Implementar un manejo de errores más robusto en los scripts de los pipelines para proporcionar feedback claro cuando faltan artefactos o fallan los pasos. | `AUDIT_RESULTS.md` |
| **P3** | Documentación | Añadir metadatos de propiedad a los documentos | Revisar los documentos en `docs/` para asegurar que todos tengan un propietario, fecha de última revisión y estado. | `AUDIT_RESULTS.md` |
| **P3** | Código | Añadir Docstrings a `config_loader.py` | Añadir docstrings a las funciones en `src/assessment_engine/scripts/lib/config_loader.py` para mejorar la claridad. | `AUDIT_RESULTS.md` |
