# 📋 Resoluciones de Diseño Arquitectónico (Sovereign Engine)

*Este documento registra las decisiones finales tomadas en los "Tribunales de Decisión" tras el debate estratégico. Estas directrices dictan la arquitectura base del NTT Sovereign AI Engine.*

### 1. El Tribunal del Motor de Estado (Orquestación Core)
*   **Veredicto:** **LangGraph**
*   **Justificación:** Se utilizará LangGraph como motor subyacente para gestionar el grafo de estados, ciclos de razonamiento y checkpointing. Se construirá una capa contractual (SDK) propia por encima para evitar el vendor lock-in directo, manteniendo la flexibilidad de cambiar el motor a futuro si es necesario, pero aprovechando la agilidad actual de LangGraph.

### 2. El Tribunal del Sandboxing y Seguridad
*   **Veredicto:** **Docker Fortificado (Defense in Depth)**
*   **Justificación:** Se descartan gVisor/Firecracker en la línea base por su alto coste operativo en entornos híbridos/on-premise de clientes. La plataforma utilizará contenedores Docker estándar pero aplicando tres reglas estrictas de fortificación: (1) Ejecución Rootless, (2) Red deshabilitada (`--network=none`), y (3) Sistema de archivos de solo lectura (`--read-only`) excepto un volumen de trabajo. Esto ofrece protección estadística suficiente contra IA errática y exploits casuales sin sacrificar viabilidad comercial. La interfaz de código (`SandboxAdapter`) permitirá conectar microVMs en proyectos de alta clasificación.

### 3. Diseño de la API Contractual (Developer Experience)
*   **Veredicto:** **Sintaxis Híbrida Python/Pydantic**
*   **Justificación:** Los desarrolladores y consultores de NTT DATA definirán agentes, herramientas y flujos heredando de clases base en Python (`class NttAgent(...)`) con fuerte tipado vía Pydantic. Se descarta la rigidez de YAML puro en favor del autocompletado, validación estática, debugging y la flexibilidad de integrar lógicas condicionales complejas de negocio que exige la consultoría.

### 4. El Tribunal de la Memoria Episódica
*   **Veredicto:** **Fase 1: Vector RAG (pgvector) -> Fase 2: Grafos Temporales (Zep / Graphiti)**
*   **Justificación:** Por motivos de pragmatismo y para evitar paralizar el proyecto con alta complejidad inicial (problemas de "State Drift" y extracción de sub-grafos masivos), se adoptará un enfoque iterativo. La Fase 1 utilizará una memoria vectorial clásica basada en PostgreSQL (`pgvector`), aprovechando que LangGraph ya utiliza Postgres para el *Checkpointing*. Una vez el Sovereign Engine esté operativo y generando valor, el departamento de I+D sustituirá esta capa por Memoria Episódica basada en Grafos Temporales para alcanzar la autonomía total, sin bloquear el "Time-to-Market" inicial.
