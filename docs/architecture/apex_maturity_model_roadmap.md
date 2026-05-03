# Apex Enterprise Roadmap: Hacia la Madurez Nivel 4 (CNCF)

Este documento define la estrategia de evolución de **The Apex** desde un orquestador de IA funcional hacia una **Plataforma de IA Autónoma de Grado Enterprise**. El objetivo es alcanzar el "100% perfecto" en seguridad, observabilidad, eficiencia financiera (FinOps) y gobernanza.

---

## FASE 1: Blindaje Táctico y FinOps (El Cortafuegos)
*Objetivo: Detener el derroche de recursos y cerrar brechas de seguridad críticas.*

- **[F-ARQ] Sandboxing Estricto de Ejecución:** Migrar el agente ejecutor a contenedores Docker efímeros sin red para neutralizar ataques RCE.
- **[F-MOT] Context Caching Nativo (Vertex AI):** Implementar caché de contexto para el ADN estratégico y contexto de negocio, reduciendo el coste de tokens de entrada hasta un 70%.
- **[F-MOT] Token Throttling por Rol:** Configurar límites estrictos de `max_output_tokens` en `model_profiles.json` según la responsabilidad del agente.

## FASE 2: Observabilidad Viva y Calidad del Dato (El Sistema Nervioso)
*Objetivo: Trazabilidad total y validación semántica automatizada.*

- **[F-MOT] Telemetría y Structured Logging:** Sustituir `print()` por JSON Logging y propagar `trace_id` (OpenTelemetry) en todos los procesos.
- **[F-CAB] Command Center Real-time:** Migrar de Polling a Server-Sent Events (SSE) o WebSockets para feedback instantáneo en la UI.
- **[F-INT] Golden Dataset & LLM-as-a-Judge:** Crear una suite de evaluación continua que compare las salidas de la IA contra un dataset de referencia ("Golden Set").

## FASE 3: Gobernanza Activa y Auto-Curación (El Sistema Inmunitario)
*Objetivo: Prevención de errores y reparación autónoma del código.*

- **[F-ARQ] Pipeline DevSecOps:** Integrar TruffleHog (secretos) y Bandit/Ruff (SAST) en el flujo de validación.
- **[F-INT] Auto-healing (Agente Doctor):** Conectar el Agente Doctor a las alertas de seguridad para que genere parches (`patch_file`) de forma autónoma.
- **[F-GOB] Doc-to-Code Drift Blocker:** Bloqueo de commits si el código y la documentación (`documentation-map.yaml`) pierden sincronía.

## FASE 4: Apex Structural Health Index (ASHI) (La Excelencia Operativa)
*Objetivo: Transparencia total a través de un panel de control de salud de plataforma.*

- **[F-CAB] Dashboard ASHI:** Interfaz visual en Next.js con métricas en tiempo real:
    - **DORA:** Lead Time, Deployment Frequency.
    - **Security:** Attack Success Rate (ASR), Blast Radius Index.
    - **FinOps:** Coste real por Torre, Context Waste Ratio.
    - **Agentic Health:** Agent Loop Efficiency (ALE), Ratio Probabilístico/Determinístico.
    - **Code Health:** Complejidad cognitiva, Type Hinting (Pydantic), Cobertura de Tests.

---

## Métricas de Éxito (Nivel 4)
- **Seguridad:** ASR < 0.01% ante ataques de inyección de prompt.
- **FinOps:** > 80% Cache Hit Rate en Vertex AI.
- **Gobernanza:** 100% de cumplimiento del "Golden Path".
- **Calidad:** > 95% de Faithfulness respecto al Golden Dataset.
