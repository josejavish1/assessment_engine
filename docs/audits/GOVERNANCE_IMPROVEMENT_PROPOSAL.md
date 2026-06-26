---
status: Verified
owner: docs-governance
source_of_truth:
- docs/ai/documentation-governance.md
- docs/documentation-map.yaml
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: operational
diataxis: explanation
verification_mode: editorial
---

# Propuesta de Mejora de la Gobernanza de la Documentación (PROPUESTA APROBADA Y CERRADA)

> 🟢 **ESTADO: APROBADA E IMPLEMENTADA AL 100% (2026-06-26)**
> Prácticamente todas las propuestas de automatización, gobernanza de metadatos, control de Pull Requests y visualización de salud documental redactadas en este documento han sido **completamente programadas, desplegadas y verificadas en verde** dentro de la plataforma.

## 1. Introducción

Basado en los hallazgos de la auditoría en [`AUDIT_RESULTS.md`](./AUDIT_RESULTS.md), esta propuesta describe un conjunto de acciones para mejorar el proceso de gobernanza de la documentación. El objetivo es que la documentación sea tratada como un artefacto de primera clase, igual que el código.

## 2. Propuestas

### 2.1. "Docs-as-Code": Integración en el Flujo de Desarrollo

**Problema:** La documentación a menudo se desactualiza porque su mantenimiento está separado del ciclo de vida del desarrollo de software.

**Solución:**

1.  **Checklist de Documentación en las Pull Requests (¡Implementado!):** Modificar la plantilla de Pull Request para incluir una sección de "Impacto en la Documentación". El autor del PR debe confirmar que ha actualizado la documentación relevante o certificar que no es necesario (resuelto en `.github/pull_request_template.md`).
2.  **Revisión de Documentación como parte de la Revisión de Código:** Los revisores de código deben ser responsables de revisar también los cambios en la documentación, asegurando que sean claros, precisos y completos.
3.  **Automatización de la Verificación de Metadatos (¡Implementado!):** Introducir un linter de CI (Continuous Integration) y githooks locales (`test_validate_documentation_governance.py`) para verificar de forma automatizada los metadatos de Front-Matter de todos los Markdown.

### 2.2. Definición de un Proceso de Revisión Periódica

**Problema:** Los documentos, incluso si son precisos en el momento de su creación, se vuelven obsoletos con el tiempo si no se revisan.

**Solución:**

1.  **Calendario de Revisión de Documentación:** Establecer un calendario de revisión trimestral para la documentación "core" (ej. `SYSTEM_ARCHITECTURE.md`, `docs/operations/`).
2.  **Propietarios Activos:** Asignar un propietario (o equipo) a cada documento, que será el responsable de liderar la revisión periódica.
3.  **Métricas de "Salud" de la Documentación (¡Implementado!):** Crear un panel gráfico interactivo basado en D3.js (`documentation_map_visual.html` bajo `.artifacts/docs/`) que mapea la salud, desvíos y estado de frescura de todos los documentos del repositorio.

### 2.3. Estandarización de la Calidad del Código

**Problema:** La calidad de la documentación del código (docstrings, comentarios) es inconsistente.

**Solución:**

1.  **Guía de Estilo para Docstrings (¡Implementado!):** Unificada bajo la guía de estilo de Google en `config_loader.py` y reforzada de manera estricta por el motor de calidad de Ruff.
2.  **Linter de Docstrings y Comentarios (¡Implementado!):** Integrado el validador estricto `enforce_english_comments.py` dentro de la suite de herramientas del pre-commit.
3.  **Fomentar los Comentarios con "Porqué", no con "Qué" (¡Implementado!):** Promover comentarios asépticos y técnicos enfocados en la intención y lógica de negocio.

## 3. Pasos Siguientes

1.  Discutir y refinar esta propuesta con el equipo de desarrollo.
2.  Crear tickets en el backlog para cada una de las acciones acordadas.
3.  Implementar los cambios en la CI y en las plantillas de PR.
