---
status: Needs Review
owner: docs-governance
source_of_truth:
- docs/SYSTEM_ARCHITECTURE.md
- src/assessment_engine/
last_verified_against: 2026-06-25
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
---

# Apex Enterprise Roadmap: Hacia la Madurez Nivel 4

Este documento define la estrategia de evolución de **The Apex** desde un orquestador funcional hacia una **plataforma integrada de procesamiento determinista y agentic**. El objetivo es consolidar la robustez en seguridad, observabilidad, eficiencia financiera (FinOps) y gobernanza técnica.

---

## FASE 1: Blindaje Táctico y FinOps (El Cortafuegos)
*Objetivo: Optimizar el consumo de recursos y restringir las fronteras de seguridad críticas.*

- **[F-ARQ] Sandboxing Estricto de Ejecución:** Migrar el agente ejecutor a contenedores Docker efímeros sin red externa para neutralizar riesgos de ejecución de código remoto (RCE).
- **[F-MOT] Context Caching Nativo (Vertex AI):** Implementar caché de contexto para el ADN de la torre y contexto de negocio, disminuyendo el volumen de tokens de entrada hasta un 70%.
- **[F-MOT] Token Throttling por Rol (¡Implementado!):** Configurar límites estrictos de `max_output_tokens` en `model_profiles.json` según la responsabilidad funcional del agente.

## FASE 2: Observabilidad Viva y Calidad del Dato (El Sistema Nervioso)
*Objetivo: Trazabilidad completa de procesos y validación semántica automatizada.*

- **[F-MOT] Telemetría y Structured Logging:** Reemplazar llamadas a `print()` por logging estructurado JSON y propagar `trace_id` basados en OpenTelemetry en todo el flujo asíncrono.
- **[F-CAB] Command Center Real-time:** Migrar del método de Polling actual a Server-Sent Events (SSE) o WebSockets para retroalimentación instantánea en la interfaz web.
- **[F-INT] Golden Dataset & LLM-as-a-Judge:** Crear una suite de evaluación continua que compare las salidas de la IA contra un dataset de referencia ("Golden Set") para medir calidad semántica.

## FASE 3: Gobernanza Activa y Auto-Curación (El Sistema Inmunitario)
*Objetivo: Prevención sistemática de errores y reparación autónoma asistida.*

- **[F-ARQ] Pipeline DevSecOps:** Integrar herramientas de escaneo de secretos (TruffleHog) y análisis estático de seguridad (SAST/Bandit) en el flujo de integración continua.
- **[F-INT] Auto-healing (Agente Doctor):** Habilitar la ejecución automatizada del Agente Doctor ante excepciones de seguridad para generar parches de código (`patch_file`) de forma autónoma.
- **[F-GOB] Doc-to-Code Compliance Gate (¡Implementado!):** Sincronización automática de esquemas pre-commit y Sentinel Diario a medianoche para prevenir desviaciones documentales.

## FASE 4: El Motor RAGE de Tercera Generación (RAGE Grounding)
- **Active Framework Rubrics (Grounded Baseline):** Implementar la búsqueda en internet en caliente de evidencias regulatorias asociadas a la torre actual (DORA, ENS Alta, DAMA-DMBOK) para calcular benchmarks de forma puramente matemática en Python, eliminando el "vibe-scoring" y la alucinación del LLM.

---

## 🏛️ Catálogo de Rúbricas y Estándares de Élite (Trazabilidad)

| Estándar Regulatorio / De Facto | Ámbito y Torre Tecnológica | Indicadores de Evaluación |
| :--- | :--- | :--- |
| **ENS (Esquema Nacional de Seguridad) Alta** | T6 (Seguridad) / T5 (Continuidad) | Porcentaje de implantación oficial y segregación de perímetros. |
| **Google DORA** | T1 (DevOps / Agilidad) | Frecuencia de despliegue en prod y estabilidad de entrega. |
| **DAMA-DMBOK v2** | T4 (Data Governance) | Porcentaje de formalización de catálogo y gobierno de datos. |

---

## 📊 Matriz de Referencias y Glosario de Direcciones

| Sigla | Término Técnico | Explicación dentro de la Plataforma |
| :--- | :--- | :--- |
| **TEF** | Threat Event Frequency | Frecuencia anual estimada de ocurrencia de eventos de amenaza (FAIR). |
| **LM** | Loss Magnitude | Impacto financiero de pérdidas estimado por evento de amenaza (FAIR). |
| **ALE** | Annual Loss Expectancy | Pérdida financiera estimada anual calculada deterministamente (TEF x LM). |
| **RAGE** | Runtime Agentic Grounding & Evaluation | Motor asíncrono y adversarial de evaluación factual en caliente con descarga de evidencias. |

---

## Métricas de Éxito (Nivel 4)
- **Seguridad:** ASR < 0.01% ante vectores de ataque de inyección de prompt.
- **FinOps:** > 80% Cache Hit Rate en Vertex AI.
- **Gobernanza:** 100% de cumplimiento del "Golden Path".
- **Calidad:** > 95% de Faithfulness respecto al Golden Dataset de referencia.
