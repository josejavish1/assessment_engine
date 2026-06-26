---
path: docs/architecture/data-provenance-ontology.md
kind: document
title: Data Provenance Ontology & Extraction Heuristics
doc_type: canonical
status: Verified
owner: docs-governance
applies_to:
- humans
- ai-agents
source_of_truth:
- ../../src/assessment_engine/infrastructure/epistemic_graph.py
- ../../src/assessment_engine/infrastructure/evidence_engine.py
last_verified_against: 2026-06-26
notes: Ontología de extracción y linaje de evidencias documentales a partir de PDFs de origen.
diataxis: explanation
verification_mode: editorial
---

# Data Provenance Ontology & Extraction Heuristics

Este documento define de manera formal la ontología de extracción de datos, linaje de procedencia (*data provenance*) y modelado de incertidumbre que utiliza el motor para estructurar evidencias a partir de fuentes documentales no estructuradas (como informes técnicos, inventarios de sistemas y auditorías en formato PDF).

---

## 1. El Grafo Epistémico como Modelo de Verdad

El motor de evaluación fundamenta su capacidad de auditoría en un **Grafo Epistémico** (`epistemic_graph.py`). A diferencia de una base de datos documental plana, un grafo epistémico representa los hallazgos técnicos como relaciones semánticas interconectadas que conectan la observación con la norma.

```
       [ Fuente PDF ]  <--- (Linaje / Provenance)
             │
             ▼
      [ Evidencia (Nodo) ]
             │
             ├──────────────────────────┐
             ▼                          ▼
   [ Componente Técnico ]  <───>  [ Control Regulador ]
                                   (ENS, ISO, DORA)
```

Cada hecho afirmado por el motor debe tener un nodo de evidencia asociado que actúe como ancla de validez legal e histórica.

---

## 2. Ontología del Grafo de Evidencias

Definimos formalmente las entidades (*nodes*) y relaciones (*edges*) que estructuran la ontología de evidencias en el sistema:

### 2.1 Clases de Nodos Epistémicos

| Clase de Nodo | Atributos Críticos | Propósito en el Dominio |
|---|---|---|
| `EvidenceNode` | `id`, `source_document`, `page_number`, `raw_quote`, `confidence_score` | Representa la cita exacta extraída del PDF origen que actúa como prueba de un hecho técnico o brecha. |
| `SystemNode` | `id`, `name`, `network_segment`, `technology_stack` | Representa un componente de infraestructura o sistema físico auditado (ej. "Core DB", "CPD Principal"). |
| `GapNode` | `id`, `title`, `severity`, `business_risk` | Identifica una brecha de seguridad o desalineación técnica observada en la infraestructura. |
| `ControlNode` | `id`, `framework_code`, `domain`, `description` | Representa el estándar regulatorio o control objetivo (ej. "ENS-re.3.1", "ISO-27001-A.12.1"). |

### 2.2 Relaciones de Trazabilidad (*Edges*)

*   `SUPPORTED_BY` (`EvidenceNode` $\rightarrow$ `SystemNode` o `GapNode`): Certifica que una observación de infraestructura o vulnerabilidad está estrictamente respaldada por una cita textual en un PDF origen.
*   `VIOLATES` (`GapNode` $\rightarrow$ `ControlNode`): Mapea una brecha de seguridad detectada directamente con el control de cumplimiento que se está incumpliendo.
*   `COVERS` (`SystemNode` $\rightarrow$ `ControlNode`): Indica qué controles regulatorios están siendo implementados con éxito por un componente técnico.

---

## 3. Heurísticas de Linaje de Datos No Estructurados

La transformación de un reporte de PDF crudo a nodos epistémicos fuertemente tipados sigue un pipeline determinista en la capa de infraestructura:

```
[ PDF de Origen ] ──(PyPDF/OCR)──> [ Bloques de Texto ] ──(Regex & AST Parsing)──> [Evidencias] ──(Pydantic)──> [Grafo Epistémico]
```

### Reglas de Extracción de Procedencia:
1.  **Mapeo de Coordenadas Físicas:** Cada nodo de evidencia (`EvidenceNode`) extraído debe almacenar la referencia exacta del origen:
    *   `source_file`: Nombre del archivo PDF original (ej. `ANEXO_A_CPD_v1.2.pdf`).
    *   `page_number`: Número de página física indexada.
    *   `anchor_context`: Las 3 líneas de texto anteriores y posteriores al hallazgo para dar contexto al revisor humano.
2.  **Identificación de Entidades Transversales:** Se aplica un resolutor de entidades (`entity_resolution.py`) para evitar la duplicidad de conceptos idénticos que se nombran de forma diferente en varios anexos (ej. "CPD Principal" vs. "Centro de Datos de Madrid").

---

## 4. Cuantificación de la Confianza y Prevención del Drift

Para evitar falsos positivos o "alucinaciones" por parte de los agentes de recolección dinámicos, cada pieza de evidencia recibe un índice de confianza basado en su modo de verificación:

$$\text{Confidence Score (CS)} = w_{\text{mode}} \times \left(1.0 - \frac{\text{churn\_rate}}{100}\right)$$

Donde:
*   `verification_mode: code` $\rightarrow$ Confianza $100\%$ ($1.0$). Verificado contra el código fuente ejecutable del proyecto.
*   `verification_mode: workflow` $\rightarrow$ Confianza $90\%$ ($0.9$). Verificado por la ejecución exitosa de un pipeline de CI.
*   **Freshness Gate:** Si un documento `Verified` supera la edad máxima permitida de 120 días sin reverificación manual, su nivel de confianza se degrada automáticamente a `0` y su estado baja a `Needs Review`.

Este modelo de metadatos asegura que la salud documental sea medible matemáticamente mediante cuadros de mando automáticos.
