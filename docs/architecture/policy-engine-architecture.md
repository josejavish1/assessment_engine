---
status: Verified
owner: docs-governance
source_of_truth:
- ../../src/assessment_engine/infrastructure/policy_engine.py
- ../../engine_config/policies/
- ../../tests/integration/test_policy_engine.py
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: code
---
# Sovereign Policy Engine Architecture

Este documento detalla la especificación técnica de la arquitectura del **Sovereign Policy Engine (Motor de Políticas Soberano)** de la plataforma.

Su objetivo es actuar como el **guardarraíl determinista y de conformidad final** del sistema, interceptando los payloads semánticos generados por la Inteligencia Artificial y aplicando reglas lógicas rígidas de seguridad, de-duplicación y alineación estratégica de riesgos antes de la compilación de entregables.

---

## 1. Patrón Arquitectónico: Compilador de Políticas de Paso Único

El Motor de Políticas no realiza sugerencias; es un **compilador determinista** que se ejecuta como un interceptor en la fase final de síntesis del blueprint (`run_tower_blueprint_engine.py`).

Toma como entrada el payload JSON de la torre generado por el modelo de lenguaje, ejecuta de forma secuencial una suite de clases de políticas registradas, y devuelve el payload saneado, reestructurado e inyectado con controles obligatorios:

```
===================================================================================================
| AI BLUEPRINT PAYLOAD ➔ [ POLICY ENGINE COMPILER ] ➔ SANITIZED SECURE PAYLOAD ➔ DOCX RENDERER    |
===================================================================================================
|                                                                                                 |
|   Políticas Registradas y Ejecutadas en Cascada:                                                |
|                                                                                                 |
|   1. Policy 1: Proyecto De-duplicación y Consolidación (DeduplicationPolicy):                  |
|      - Escanea proyectos duplicados o con propósitos similares (ej: Platform Engineering)        |
|        y los consolida en un único proyecto maestro bajo la torre correspondiente.               |
|                                                                                                 |
|   2. Policy 2: Re-secuenciación de Dependencias (SequencingPolicy):                             |
|      - Modifica dinámicamente las duraciones y horizontes temporales (ej: fuerza que el plan     |
|        de adopción vaya en H1 (Mes 1-2) y retrasa el piloto de Kubernetes a H2).                 |
|                                                                                                 |
|   3. Policy 3: Salvaguarda OT/SCADA (OtPerimeterPolicy):                                         |
|      - Si se detecta un proyecto de SCADA o entornos industriales OT críticos, inyecta           |
|        obligatoriamente el entregable y objetivo de "Diodo de Datos de Hardware".                |
|                                                                                                 |
`-------------------------------------------------------------------------------------------------'
```

---

## 2. Implementación de Políticas Clave

### A. Política de De-duplicación y Fusión de Esfuerzos
*   **Problema de la IA:** Los LLMs tienden a proponer el mismo proyecto genérico en múltiples pilares tecnológicos distintos (por ejemplo, "Migración a AWS" tanto en Cómputo como en Redes), fragmentando el presupuesto del cliente.
*   **La Solución:** La regla busca similitudes conceptuales y semánticas. Borra los duplicados redundantes de los pilares satélites e inyecta un único proyecto maestro consolidado en el pilar de gobierno general (ej. Automatización y Autoservicio).

### B. Política de Secuenciación Lógica de Cronogramas
*   **Problema de la IA:** La IA carece de noción temporal de construcción real, sugiriendo habitualmente arrancar "Pilotos de Kubernetes" en el Mes 1 sin haber diseñado la "Política de Contenedores" previa.
*   **La Solución:** Re-ordena las tareas de forma cronológica estricta:
    *   Fase de Arranque (Mes 1-2): Planes estratégicos y gobernanza.
    *   Horizonte 1 (Mes 1-6): Diseños de bases y pilotos.
    *   Horizonte 2 (Mes 6-12): Implantaciones de producción masivas.

### C. Salvaguarda Perimetral de Infraestructuras Críticas (OT)
*   **Problema de la IA:** Los modelos de lenguaje desconocen la criticidad de seguridad de una red de transporte de energía SCADA, proponiendo de forma insegura "extraer telemetría de OT directa a la nube de AWS".
*   **La Solución:** Si el motor de políticas detecta un proyecto asociado a SCADA u OT, inyecta de forma obligatoria el requerimiento técnico no funcional de **Diodos de Datos de Hardware unidireccionales**. Esto garantiza el aislamiento físico total de la red eléctrica frente a internet, cumpliendo con las normativas NIS2 y PIC oficiales.

---

## 3. Integración con el Análisis FAIR (Factor Analysis of Information Risk)

El Motor de Políticas se alimenta de los perfiles de riesgo FAIR declarados de forma estructurada en `engine_config/policies/fair_risk_profiles.json`.

Cruza las variables deterministas de **Frecuencia de Eventos de Amenaza (TEF)** y **Magnitud de Pérdida (LM)** para calcular la **Pérdida Anual Estimada (ALE)** de cada pilar técnico. Si el ALE supera el umbral de tolerancia financiera configurado, el motor de políticas eleva la prioridad de mitigación de la iniciativa y restringe las libertades del agente generador.
