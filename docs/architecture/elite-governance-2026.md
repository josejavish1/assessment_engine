---
status: Draft
owner: product-owner-orchestrator
source_of_truth:
  - src/assessment_engine/
last_verified_against: 2026-05-02
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Arquitectura de Gobernanza de Agentes (The Apex)

Este documento describe el modelo de gobernanza de alto nivel, conocido como "The Apex", que supervisa el pipeline de generación de artefactos del `assessment-engine`. Este sistema utiliza un trío de agentes especializados para garantizar la calidad, el cumplimiento y la responsabilidad de cada entregable.

## 1. Visión General

La arquitectura "The Apex" es una capa de supervisión que se sitúa por encima de los pipelines de ejecución (Modo Pipeline y Modo Servidor). Su propósito es automatizar las funciones de revisión, corrección y validación que tradicionalmente realizaría un equipo humano de control de calidad y cumplimiento normativo.

El flujo es el siguiente:
1.  Un pipeline genera un artefacto borrador (ej. `Blueprint_Txx.docx`).
2.  El artefacto es entregado al agente `Doctor` para una primera revisión y corrección.
3.  El artefacto corregido pasa al agente `Verification` para un análisis de cumplimiento.
4.  Finalmente, el agente `Liability Signer` realiza la validación final y asume la responsabilidad formal del contenido.

## 2. Responsabilidades de los Agentes

### 2.1. Agente "Doctor"

**Misión:** Sanar y corregir. El agente `Doctor` es la primera línea de defensa de la calidad del contenido.

**Responsabilidades:**
-   **Análisis Sintáctico y Estilístico:** Detectar y corregir errores gramaticales, de puntuación y de estilo en el texto generado.
-   **Coherencia Interna:** Asegurar que el artefacto no contiene contradicciones lógicas dentro de sí mismo. Por ejemplo, que las conclusiones se derivan lógicamente de la evidencia presentada.
-   **Reparación Estructural:** Corregir problemas de formato o estructura en los documentos generados (ej. tablas rotas, numeración incorrecta).
-   **Feedback Loop:** Si detecta errores recurrentes, puede notificar al sistema de orquestación para ajustar los prompts o la configuración del pipeline subyacente.

### 2.2. Agente "Verification"

**Misión:** Verificar y validar. El agente `Verification` actúa como un auditor de cumplimiento y calidad.

**Responsabilidades:**
-   **Cumplimiento de Contratos:** Verificar que el artefacto cumple con los "contratos" definidos en los `schemas` y las políticas del motor (ej. `orchestrator_policy.json`).
-   **Trazabilidad de la Evidencia:** Asegurar que cada afirmación o conclusión en el informe está respaldada por la evidencia correspondiente en los datos de entrada (`evidence_ledger.json`).
-   **Adherencia a la "Fuente de Verdad":** Validar que el contenido del artefacto es una representación fiel y no contradictoria del `blueprint_payload.json` del que se deriva.
-   **Control de Calidad Normativo:** Comprobar que el entregable cumple con los estándares de calidad y las regulaciones externas aplicables (ej. directrices del EU AI Act).

### 2.3. Agente "Liability Signer"

**Misión:** Asumir la responsabilidad. El `Liability Signer` es el último eslabón de la cadena y representa la firma formal de la organización sobre el documento.

**Responsabilidades:**
-   **Validación Final de Calidad:** Realizar una última revisión holística del artefacto, confirmando que ha pasado satisfactoriamente las fases de `Doctor` y `Verification`.
-   **Firma Criptográfica (Futuro):** En futuras implementaciones, este agente podría aplicar una firma digital o registrar el artefacto en un sistema de control de versiones o blockchain para garantizar su inmutabilidad.
-   **Registro de Responsabilidad:** Crear una entrada auditable que vincule el artefacto final con la versión exacta del código, la configuración y los datos utilizados para generarlo.
-   **Gatekeeper Final:** Es el único agente con la autoridad para aprobar un artefacto para su entrega al cliente. Si detecta un problema crítico no resuelto, puede vetar la publicación del documento.
