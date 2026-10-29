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

Este documento contiene exclusivamente el backlog activo de tareas de ingeniería pendientes del motor `assessment_engine`, derivado de la evaluación formal en [`AUDIT_RESULTS.md`](./AUDIT_RESULTS.md). Todas las tareas cerradas han sido verificadas en el histórico de commits.

---

## 2. Backlog Activo de Tareas Pendientes

| Prioridad | Área | Título de la Tarea | Alcance Técnico Requerido | Impacto en la Plataforma |
| :---: | :--- | :--- | :--- | :--- |
| **P1** | Seguridad | **Sandboxing Estricto de Ejecución de Herramientas** | Encapsular la ejecución de subprocesos y herramientas CLI (`run_command`) dentro de micro-contenedores efímeros sin acceso a red (Docker/gVisor). | Aislamiento estricto y mitigación de escape de entorno en ejecuciones multi-tenant. |
| **P2** | Operaciones | **Resiliencia de Arranque (Boot Persistence)** | Configurar `loginctl enable-linger` en el host Linux para que los daemons supervisores en segundo plano persistan automáticamente tras reinicios del sistema sin requerir sesión interactiva. | Continuidad operativa 24/7 y SLA en entornos de producción. |
| **P2** | DevSecOps | **Auto-Curación SAST (Bandit)** | Integrar el escáner de seguridad estática `bandit` en la compuerta de CI y acoplarlo al agente de verificación para auto-reparación asistida. | Prevención proactiva de patrones de código vulnerables en Python. |
| **P2** | DevSecOps | **Bloqueo Estricto de Secretos (TruffleHog)** | Integrar TruffleHog en el hook de pre-commit y en el pipeline de CI para bloquear de forma determinista la inserción accidental de credenciales o tokens. | Blindaje criptográfico de la cadena de suministro. |
| **P2** | Clean Code | **Erradicación de "Swallowed Exceptions"** | Sustituir bloques residuales `except Exception: pass` por excepciones fuertemente tipadas y trazabilidad con structured logging JSON. | Observabilidad forense y eliminación de fallos silenciosos. |
| **P2** | Robustez | **Manejo de Errores de Entrada en Pipelines** | Añadir validación temprana y mensajes de diagnóstico específicos ante la ausencia de archivos de entrada (`case_input.json`, `findings.json`). | Experiencia de operador y diagnóstico inmediato de fallos de entrada. |
| **P3** | DevSecOps | **Escudo Anti-Inyección (Prompt Shield)** | Implementar un middleware de sanitización semántica ligero en la ingesta de documentos para bloquear intentos de inyección de prompts (*Jailbreaks*). | Protección perimetral de modelos cognitivos frente a documentos no confiables. |
| **P3** | Documentación | **Renderizado Web Corporativo (MkDocs Material)** | Configurar el generador estático MkDocs Material para compilar el árbol `/docs` en un portal HTML interactivo y navegable. | Mejora de lectura ejecutiva y experiencia de auditoría externa. |

---

## 3. Iniciativas Desestimadas por Arquitectura Soberana

| Prioridad | Área | Título de la Iniciativa | Razón Técnica de Desestimación |
| :---: | :--- | :--- | :--- |
| **P1** | FinOps | **Context Caching Nativo (Google Vertex AI)** | **[DECLINED BY ARCHITECTURE]** Descartado formalmente para preservar la **Soberanía y Portabilidad Tecnológica (Zero Lock-in)**. Acoplar el pipeline a la API propietaria `cachedContent` violaría la neutralidad del motor frente a otros proveedores (OpenAI, Anthropic, vLLM local). |
