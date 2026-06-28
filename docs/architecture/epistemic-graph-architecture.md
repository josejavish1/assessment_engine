---
status: Verified
owner: docs-governance
source_of_truth:
- ../../src/assessment_engine/infrastructure/epistemic_graph_service.py
- ../../engine_config/policies/epistemic_dependencies.json
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

Su objetivo de diseño es actuar como el **cerebro de propagación de riesgos y dependencia causal** de la plataforma, modelando el holding tecnológico del cliente como un sistema vivo interconectado.

---

## 1. Patrón Arquitectónico: Loopy Causal Belief Network (LCBN)

El motor de grafos no utiliza topologías rígidas o simples DAGs (Directed Acyclic Graphs). Implementa una arquitectura **LCBN (Loopy Causal Belief Network)** sobre `NetworkX` para modelar la realidad física compleja de infraestructuras Tier 1 (donde existen bucles de realimentación continuos, ej. Redes T3 protege a SOC T5, y SOC T5 securiza a Redes T3).

*   **Topología Declarativa Dinámica:** Las aristas y los pesos del grafo (dependencias causales de riesgo) no están acopladas en código. Se cargan de forma dinámica en tiempo de ejecución desde perfiles JSON (`engine_config/policies/epistemic_dependencies.json`) según el sector del cliente (ej. `critical_infrastructure`, `retail`).
*   **Convergencia de Punto Fijo (Banach):** La propagación probabilística del riesgo a través de los ciclos cerrados de la red se resuelve matemáticamente mediante un algoritmo de contracción iterativa de punto fijo. El sistema absorbe los impactos en bucle y converge de forma segura a un equilibrio estable.

---

## 2. Unificación Matemática: PageRank de Centralidad de Riesgo (ERC)

El Grafo Epistémico logra la unificación sistémica del análisis estocástico de la **Fase 1 (MCDA Monte Carlo Fuzzer)** con la topología estructural de la **Fase 2 (BBN)**.

*   **La Ecuación Unificada:** El motor calcula el **Eigenvector Risk Centrality (ERC)**. Esto se logra ponderando la Matriz de Adyacencia ($W$) por las desviaciones estándar ($\sigma$) de Monte Carlo de cada torre técnica.
*   **PageRank Adaptado (Katz Centrality):** Para evitar el colapso nilpotente de las redes dirigidas, se emplea una iteración de potencia asíncrona con un factor de amortiguación (Damping Factor $d = 0.85$). El resultado aísla de forma determinista la **Torre más frágil (SPOF)** de la organización, basándose conjuntamente en su inestabilidad estadística interna y en su carga de responsabilidad estructural.

---

## 3. Auto-Calibración Evolutiva (Causal Backpropagation)

El sistema de grafos epistémicos es un sistema que aprende de sus errores de estimación.
*   **Descenso de Gradiente Analítico:** Al contrastar las recomendaciones de madurez intrínseca generadas *A Priori* por el LLM con las madureces reales empíricas obtenidas *A Posteriori* en las auditorías de las torres técnicas, el sistema calcula el Error Cuadrático Medio (MSE) predictivo.
*   **Actualización de Pesos:** El motor de backpropagation recalcula y optimiza las aristas del grafo para minimizar dicho error.
*   **Guardado Atómico POSIX:** Los nuevos pesos asimilados se persisten físicamente de vuelta al archivo JSON declarativo (`epistemic_dependencies.json`) mediante reemplazos atómicos de sistema de archivos (`os.replace`). El Grafo se autoadapta y evoluciona de forma segura para cada sector corporativo.

---

## 4. Visualización de Caminos Críticos de Fallo
El analizador interno de NetworkX cuenta con algoritmos adaptativos para extraer los **Caminos de Propagación de Riesgo**. Incluso en arquitecturas totalmente cíclicas (sin un nodo origen explícito), el motor extrae dinámicamente las cascadas de fallo más severas (ej. `T6 -> T5 -> T2`) y su multiplicador de transferencia de riesgo acumulado, empaquetándolas en el dossier del cliente (`client_intelligence.json`).
