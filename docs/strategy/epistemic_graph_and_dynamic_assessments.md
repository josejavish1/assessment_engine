---
status: Needs Review
owner: docs-governance
applies_to:
- humans
doc_type: canonical
last_verified_against: 2026-06-27
source_of_truth:
- README.md
diataxis: explanation
verification_mode: editorial
---
# Vision Architecture: The Epistemic Knowledge Graph & Dynamic Assessments (Standard 2026)

## 1. El Problema Actual: Arquitectura Basada en "Silos de Torres"

Actualmente, el motor de evaluación (*Assessment Engine*) opera bajo un paradigma estructural de **"Data-as-Code" estático**. Las matrices de madurez están codificadas en archivos JSON separados por Torres Tecnológicas (T1, T2, T3...).

**Limitaciones Comerciales y Operativas:**
1. **Fricción en Nuevos Productos (Late Motives):** Si la dirección comercial (C-Level) requiere vender un "Assessment de Cumplimiento DORA" o un "Assessment de AI-Readiness", la arquitectura actual obliga a crear "Torres Falsas" o a duplicar preguntas (ej. la gestión de copias de seguridad de la Torre 5 debe copiarse en el Assessment de Ransomware).
2. **Amnesia de Cliente:** Si un cliente realiza un Assessment de Cloud en Enero y un Assessment de Ciberseguridad en Octubre, el sistema le volverá a formular preguntas transversales que ya respondió, generando fricción.
3. **Rigidez de la Agregación:** El cruce de datos entre Torres (ej. cómo una deficiencia en T2 bloquea un objetivo de negocio en T5) depende de la inteligencia de la IA en tiempo de inferencia, no de una resolución matemática determinista previa.

---

## 2. Transición Arquitectónica: "Epistemic Knowledge Graph Retrieval"

Para alinearse con las mejores prácticas de la industria y los estándares empresariales consolidados, la arquitectura debe evolucionar de "Cuestionarios Aislados" a un **Gemelo Digital Arquitectónico**.

El corazón de este sistema ya no son archivos JSON planos, sino una **Ontología en un Grafo de Conocimiento (Knowledge Graph)**.

### 2.1. El Pool Universal de Preguntas (Atomic Knowledge)
En lugar de organizar el conocimiento por "Torres", el sistema se basará en un lago de "Preguntas Atómicas". Cada pregunta es un nodo multidimensional etiquetado matemáticamente.

*   *Nodo:* `¿Se utilizan repositorios de código y pipelines CI/CD automatizados para el despliegue de infraestructura?`
*   *Tags (Lentes):* `[T2_Cloud, T4_Cybersecurity, DORA_Compliance, AI_Readiness, FinOps]`

### 2.2. Ingesta Componible (Just-in-Time Questionnaires)
El motor de orquestación ya no cargará un "JSON de Torre". La generación de assessments se convierte en una **Consulta Matemática (Query)**.

*   **Petición C-Level:** "Generar un Assessment para Resiliencia ante Ransomware".
*   **Ejecución del Motor:** `SELECT questions FROM Universal_Pool WHERE tag CONTAINS Ransomware`.
*   **Resultado:** El sistema ensambla dinámicamente el cuestionario perfecto cruzando preguntas de infraestructuras, datos y seguridad, sin duplicar código ni mantener múltiples excels.

---

## 3. La Memoria Institucional: Decaimiento Temporal (TTL)

El Grafo Epistémico no solo almacena "Verdades", almacena **"Hechos Temporales"** (`Sujeto -> Predicado -> Objeto -> Timestamp -> Confianza`).

### 3.1. Evaluación Incremental (Cross-selling sin Fricción)
Si el cliente contrata un Assessment de "Nube Soberana" seis meses después de su Assessment "Cloud", el sistema consultará el Grafo:
1. El motor identifica qué preguntas requiere la lente "Nube Soberana".
2. El motor detecta que el 60% de esas respuestas ya están en la memoria del Grafo (desde hace 6 meses).
3. **Comprobación de Vigencia (Time-To-Live - TTL):** No todos los datos caducan igual. El proveedor de Cloud (AWS/Azure) tiene un TTL de 3 años. El estado de automatización de un pipeline tiene un TTL de 6 meses.
4. **Validación (Trust, but Verify):** El sistema **solo le pregunta al cliente el 40% restante**. Para el 60% que ya conoce pero que está cerca de caducar, pre-rellena la respuesta: *"En Enero indicaste que tus despliegues eran manuales. ¿Ha evolucionado esta capacidad? [Sí/No/Sigue Igual]"*.

---

## 4. Resolución de Conflictos (Epistemic Precedence)

El Grafo actúa como un Firewall contra alucinaciones de IA y datos obsoletos (OSINT).

1.  **Datos de OSINT (Minuto Cero):** Un agente de IA lee una nota de prensa de 2023 que dice que el cliente usa Azure. Se inyecta en el Grafo: `(Cliente, Usa_Nube, Azure) [Confianza: 0.4] [Origen: OSINT]`.
2.  **Datos del Assessment / Contexto Interno:** El cliente responde en el cuestionario oficial (o en un DOCX de contexto) que usa AWS. Se inyecta: `(Cliente, Usa_Nube, AWS) [Confianza: 1.0] [Origen: VERDAD_ABSOLUTA]`.
3.  **Compilación Pre-Inferencia:** Antes de enviar el contexto a Gemini/OpenAI para redactar el Blueprint, el código Python ejecuta la resolución de la verdad. Como 1.0 > 0.4, **la palabra "Azure" es aniquilada matemáticamente de la base de datos**. El LLM redacta un documento 100% puro sobre AWS.

---

## 5. Roadmap de Implementación Práctica

Para no romper el modelo operativo actual, la transición debe ser "Strangler Fig" (Evolución sin destrucción):

1.  **Fase 1 (Completada hoy):** Implementación del `EpistemicGraph` en memoria (SQLite) para resolver colisiones de Contexto vs OSINT. El código base Hexagonal ya está preparado.
2.  **Fase 2 (Knowledge-as-Code):** Migrar los archivos `tower_definition_*.json` a un único formato de ontología donde las preguntas tienen arrays de `tags`.
3.  **Fase 3 (Persistencia):** Conectar el `EpistemicGraph` a una base de datos persistente (SQLite local o Neo4j/SurrealDB) por cada cliente (`working/CLIENTE/epistemic_ledger.db`).
4.  **Fase 4 (Lentes Dinámicas):** Re-escribir la lógica de orquestación para que, en lugar de pedir `--tower T2`, acepte `--lens DORA` o `--lens RANSOMWARE`.

Esta arquitectura transforma a la consultora de un "Generador de PDFs" a un **"Proveedor de Continuous Readiness"**. El assessment deja de ser un documento muerto para convertirse en un Gemelo Digital vivo del cliente.
