---
status: "Draft"
owner: "architecture-board"
reviewers:
  - "principal-architect"
  - "compliance-lead"
last_updated: "2026-05-02"
doc_type: "architectural-decision-record"
---

# Gobernanza de Élite 2026: Arquitectura "The Apex"

## 1. Resumen Ejecutivo

Este documento define la arquitectura "The Apex", una capa de gobernanza y supervisión diseñada para garantizar la máxima calidad, fiabilidad y cumplimiento normativo de los artefactos generados por el `assessment-engine`. The Apex se compone de tres agentes especializados que operan en concierto para formar un sistema inmunitario digital que protege la integridad del pipeline.

Esta arquitectura es la implementación de referencia para la operación en **Modo de Gobernanza**, como se describe en el [documento de arquitectura del sistema](./SYSTEM_ARCHITECTURE.md).

## 2. Principios de Diseño

La arquitectura The Apex se fundamenta en tres pilares:

1.  **Separación de Responsabilidades:** Cada agente tiene un mandato único y no solapado, previniendo conflictos de interés y asegurando una evaluación multifacética.
2.  **Defensa en Profundidad:** Los agentes actúan en secuencia, formando múltiples barreras de calidad. Un artefacto debe superar las tres revisiones para ser considerado "aprobado para producción".
3.  **Trazabilidad y Responsabilidad:** Cada decisión tomada por un agente queda registrada, creando un rastro de auditoría inmutable que culmina en una firma de responsabilidad.

## 3. Componentes de la Arquitectura

### 3.1. Agente "Doctor": Gobernanza Inmunitaria y Coherencia Estructural

El agente **Doctor** es la primera línea de defensa. Su función es análoga al sistema inmunitario del cuerpo humano: busca y neutraliza patógenos dentro de los artefactos generados antes de que puedan causar daño.

**Responsabilidades:**

-   **Análisis de Coherencia Interna:** Verifica que un artefacto (ej. un `blueprint_payload.json`) es lógicamente consistente. Por ejemplo, asegura que las conclusiones se derivan directamente de la evidencia presentada y que no hay contradicciones.
-   **Detección de "Alucinaciones":** Identifica y marca contenido generado por la IA que no se sustenta en los datos de entrada (`case_input.json`, `findings.json`).
-   **Validación de Contratos de Datos:** Asegura que el artefacto cumple estrictamente con su esquema Pydantic definido y con los contratos de interoperabilidad descritos en [`docs/contracts/`](../contracts/).
-   **Triaje y Cuarentena:** Si un artefacto presenta anomalías, el Doctor lo mueve a un estado de "cuarentena" y emite un diagnóstico detallado para su revisión por un operador humano o para su re-generación automática.

### 3.2. Agente "Verification": Pragmatismo de Élite y Alineamiento de Negocio

El agente **Verification** actúa como un consultor de élite o un "Principal" en una firma de consultoría. Su perspectiva no es la corrección técnica, sino el valor y la adecuación estratégica.

**Responsabilidades:**

-   **Alineamiento con el Contexto de Negocio:** Evalúa si el artefacto responde a las necesidades y al contexto del cliente. ¿El tono es el adecuado? ¿El nivel de detalle es útil para un CIO?
-   **Evaluación de "Reasonableness":** Aplica un juicio experto para determinar si las conclusiones y recomendaciones son pragmáticas, accionables y creíbles desde una perspectiva de negocio.
-   **Control de Calidad del "Producto Final":** A diferencia del Doctor, que se enfoca en la estructura, Verification se enfoca en la calidad percibida del entregable. Revisa la redacción, el estilo y la claridad de la comunicación.
-   **Identificación de "Valor Atípico":** Detecta recomendaciones que, aunque técnicamente correctas, son inviables o contraproducentes en el mundo real (ej. proponer una migración a la nube en 48 horas).

### 3.3. Agente "Liability Signer": zk-Governance y Cumplimiento Normativo

El **Liability Signer** es el componente final y más crítico del pipeline. Su función es actuar como un oficial de cumplimiento normativo, proporcionando una firma final que certifica que el artefacto es seguro, fiable y cumple con la regulación vigente.

**Responsabilidades:**

-   **Certificación de Cumplimiento (EU AI Act):** Verifica que el proceso de generación del artefacto ha seguido las directrices de la **Ley de Inteligencia Artificial de la Unión Europea**, especialmente en lo relativo a la explicabilidad (XAI), la trazabilidad y la robustez.
-   **Auditoría del Linaje de Datos:** Confirma que todos los datos utilizados en la generación del artefacto provienen de fuentes autorizadas (`source_of_truth`) y que el rastro de transformaciones está completo y es verificable.
-   **Firma Criptográfica (zk-Governance):** Utilizando un mecanismo de "conocimiento cero" (Zero-Knowledge), el agente genera una firma digital que atestigua el cumplimiento sin exponer los detalles internos del proceso. Esta firma vincula el artefacte a una versión específica del motor, de la configuración y de los datos de entrada.
-   **Registro de Responsabilidad:** La firma se inscribe en un registro inmutable (ledger), asumiendo formalmente la "responsabilidad" por el contenido del artefacto en nombre de la organización. Un artefacto sin esta firma no puede ser liberado al cliente.

## 4. Flujo de Orquestación

El flujo de gobernanza es estrictamente secuencial:

1.  Un artefacto es generado por el pipeline principal.
2.  Es enviado al agente **Doctor**.
    -   Si es rechazado, entra en un ciclo de remediación.
    -   Si es aprobado, pasa al siguiente agente.
3.  El artefacto es evaluado por el agente **Verification**.
    -   Si es rechazado, se devuelve al pipeline para un refinamiento estratégico.
    -   Si es aprobado, pasa a la fase final.
4.  El artefacto es procesado por el agente **Liability Signer**.
    -   Si la firma falla, se dispara una alerta de alta prioridad por posible violación de cumplimiento.
    -   Si la firma es exitosa, el artefacto se marca como `production-ready` y se libera.
