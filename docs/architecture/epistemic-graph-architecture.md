---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/infrastructure/epistemic_graph.py
- src/assessment_engine/infrastructure/policy_engine.py
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: code
---

# Epistemic Knowledge Graph Architecture

Este documento detalla la especificación técnica de la infraestructura del **Epistemic Knowledge Graph (Grafo de Conocimiento Epistémico)** del sistema.

Su objetivo de diseño es actuar como el **cerebro relacional y semántico de la plataforma**, organizando la información del diagnóstico como un gemelo digital relacional inmutable que separa estrictamente la captura de eventos de la consulta rápida de datos.

---

## 1. Patrón Arquitectónico: Event Sourcing & CQRS

El motor de grafos no utiliza bases de datos relacionales tradicionales modificables en caliente. En su lugar, implementa dos de los patrones de diseño más avanzados e industriales del software de alta fidelidad:

### A. Event Sourcing (Lado de Escritura / Write-Side)
Cada hecho, aserción o cambio de diagnóstico no se "sobrescribe" en una celda. Se captura como un objeto de evento inmutable y ordenado secuencialmente en el tiempo (`GraphEvent`).
*   **Ledger Append-Only:** Estos eventos se añaden en cascada en un diario de transacciones de texto plano (un archivo JSONL duradero):
    `working/{client_id}/epistemic_ledger.jsonl`
*   **Beneficio:** Este ledger constituye el historial definitivo e indestructible del diagnóstico del cliente. Nunca hay pérdida de datos ni colisiones accidentales de sobrescritura.

### B. CQRS (Lado de Lectura / Read-Side)
Para permitir que el motor de políticas y el pipeline lancen consultas semánticas complejas en microsegundos (lo cual es inviable si hay que analizar un largo archivo JSONL de texto plano cada vez), el sistema separa el modelo de lectura.
*   **Proyección SQLite en Memoria:** Al arrancar la clase, el método `_replay_ledger()` lee secuencialmente el ledger JSONL del disco, "reproduce" toda la historia de eventos y proyecta el estado resultante de las aserciones válidas en una **base de datos SQLite temporal en memoria (`self.conn`)**.
*   **Consultas Rápidas:** El sistema puede lanzar consultas SQL directas contra este "gemelo digital" en memoria para extraer dependencias cruzadas entre pilares técnicos al instante.

```
===================================================================================================
| WRITE-SIDE (Event Sourcing)                     ➔   READ-SIDE (CQRS / Proyección)               |
===================================================================================================
|                                                                                                 |
|   1. add_event(S, P, O, conf)                                                                   |
|      ➔ Escribe GraphEvent en `epistemic_ledger.jsonl` (Append-Only)                            |
|                                                                                                 |
|   2. _replay_ledger() de arranque:                                                              |
|      ➔ Re-lee `epistemic_ledger.jsonl` del disco ➔ Proyecta estado en SQLite en memoria         |
|                                                                                                 |
|   3. Consultas de consulta rápidas (Query):                                                     |
|      ➔ SQL Query a la base de datos SQLite en memoria ➔ Devuelve aserciones en microsegundos.   |
|                                                                                                 |
`-------------------------------------------------------------------------------------------------'
```

---

## 2. El Modelo de Datos: Tripletas Semánticas de Confianza

Los hechos del diagnóstico se modelan como aserciones lógicas basadas en **Sujeto-Predicado-Objeto (Tripletas RDF)** enriquecidas con metadatos de certidumbre:

*   **Sujeto (Subject):** El nodo o entidad a evaluar (ej. `Cloud_Adoption`).
*   **Predicado (Predicate):** La relación o atributo (ej. `has_status` o `requires_remediation`).
*   **Objeto (Object):** El valor o destino de la relación (ej. `In_Progress` o `Active_Directory_MFA`).
*   **Confianza (Confidence Score):** Un índice numérico (de 0.0 a 1.0) que indica la fiabilidad de la fuente.

### Resolución de Contradicciones (Epistemic Precedence)
Si dos fuentes de información contradictorias (ej. un cuestionario preliminar de un consultor junior vs. un reporte del BOE oficial descargado por RAGE) intentan asertar sobre el mismo sujeto y predicado:
*   **Regla de Precedencia:** El lector del grafo consulta el SQLite en memoria y selecciona **el objeto que posea el mayor Confidence Score en la marca de tiempo más reciente**. El dato de baja confianza es "sombreado" de la vista actual de forma matemática, garantizando la consistencia factual frente a ruido de entrada.
