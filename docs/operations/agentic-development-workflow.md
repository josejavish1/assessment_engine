---
status: Verified
owner: docs-governance
source_of_truth:
- ../../AGENTS.md
- ../../.github/copilot-instructions.md
- ../../.github/pull_request_template.md
- ../../docs/operations/engineering-quality-gates.md
- ../../src/assessment_engine/domain/
- ../../tests/
- ../../.github/workflows/ci.yml
- ../../.github/workflows/quality.yml
- ../../.github/workflows/typing.yml
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: workflow
---
# Agentic development workflow

Esta guía establece el protocolo operativo para el ciclo de desarrollo de software asistido por agentes de inteligencia artificial en `assessment-engine`. Su propósito es estructurar la interacción con los agentes autónomos para mitigar la deriva arquitectónica, prevenir la duplicidad lógica o semántica, y erradicar mutaciones de código deficientemente especificadas.

## Regla principal

El agente autónomo tiene estrictamente prohibido operar sobre especificaciones ambiguas o imprecisas. Su intervención requiere una **Especificación Mínima Verificable (*Minimum Verifiable Specification*)**, un alcance rigurosamente delimitado, reglas de validación ejecutables y un proceso de revisión humana enfocado prioritariamente en la semántica del dominio y la cohesión de la arquitectura.

## Flujo de Trabajo Recomendado

### 1. Especificación Previa a la Implementación
Antes de iniciar cualquier modificación en la base de código, se debe declarar de forma determinista la siguiente información:

-   **Definición del Problema:** Diagnóstico exacto de la desviación o capacidad ausente.
-   **Alcance (*In-Scope*):** Delimitación quirúrgica de las modificaciones permitidas.
-   **Exclusiones (*Out-of-Scope*):** Frontera explícita de componentes o archivos no modificables en esta iteración.
-   **Impacto en Contratos:** Identificación de esquemas Pydantic o especificaciones canónicas afectadas.
-   **Invariantes del Sistema:** Reglas de negocio y lógica estructural que deben permanecer inmutables tras el cambio.
-   **Protocolo de Validación:** Criterios empíricos y suites de pruebas exigidas para certificar el cambio.

Cualquier propuesta de Pull Request o sesión de desarrollo interactiva debe responder con exactitud a estas dimensiones para considerarse elegible para su ejecución.

## Plantilla Mínima de Especificación

```text
Problema:
- Definición de la desviación observable o capacidad requerida.

In scope:
- Mutaciones permitidas y archivos objetivo.

Out of scope:
- Límites de exclusión explícitos para esta iteración.

Source of truth:
- Código fuente, esquemas, flujos de CI o especificaciones canónicas que gobiernan la verdad.

Invariantes:
- Comportamientos lógicos y estructurales que deben permanecer estables.

Validación:
- Pruebas y aserciones de conformidad obligatorias.
```

## Reglas de Acotamiento de Alcance

-   **Atomicidad:** Priorizar integraciones incrementales de cambios pequeños, totalmente reversibles y con interfaces claramente delimitadas.
-   **No Mezcla de Tareas:** Evitar la coexistencia de refactorizaciones estructurales, adición de nuevas funcionalidades y rediseños semánticos en un único ciclo de integración.
-   **Identificación de Abstracción:** Si las modificaciones impactan múltiples capas del sistema, definir o extender primero el helper o la política compartida correspondiente en el dominio.
-   **Trazabilidad Multi-fase:** En desarrollos secuenciales complejos, mantener la especificación mínima y el registro de cambios actualizados durante todo el ciclo de vida del refinamiento.

## Buenas Prácticas de Ingeniería en el Repositorio

-   **Uso Estricto de Golden Paths:** Los agentes de IA tienen estrictamente prohibido crear nuevos componentes o servicios (p. ej., endpoints, workers, scripts) desde cero. Deben utilizar obligatoriamente los andamiajes de andamiaje definidos en `templates/golden_paths/` para garantizar la homogeneidad de la telemetría, el registro estructurado de eventos y el control de accesos.
-   **Centralización Semántica:** Mantener una única fuente de verdad lógica para cada regla de negocio.
-   **Determinismo en Código:** Codificar toda lógica de negocio y de reporting en Python, absteniéndose de confinar reglas funcionales en prompts de LLMs.
-   **Uso de Abstracciones de Dominio:** Apoyarse siempre en utilidades de infraestructura y políticas de dominio compartidas para reglas transversales.
-   **Manejo de Errores Riguroso:** Implementar excepciones e interrupciones explícitas en rutas críticas en lugar de degradaciones silenciosas del estado.
-   **Tests de Coherencia Transversal:** Certificar la consistencia conceptual mediante aserciones cruzadas cuando una regla afecte a múltiples capas de datos.

## Prácticas Prohibidas (Anti-patrones)

-   Confinar lógica funcional o reglas de negocio dentro de prompts de modelos de lenguaje.
-   Duplicar constantes o lógicas de asignación de scores, bandas de madurez, gradientes o severidades.
-   Implementar defaults silenciosos en compuertas lógicas críticas.
-   Capturar excepciones globales (`except Exception`) sin registrar una señal estructurada y auditable de error.
-   Modificar archivos o componentes que excedan el alcance mínimo declarado.
-   Introducir fuentes de verdad temporales o parches transitorios.

## Criterios de Revisión Humana (*Code Review*)

Durante el proceso de revisión de pull requests, la evaluación técnica debe priorizar las siguientes aserciones antes que el estilo superficial:

1.  ¿La integración parte de una Especificación Mínima Verificable?
2.  ¿El alcance es atómico y respeta los límites de exclusión declarados?
3.  ¿Se reutilizan las abstracciones y helpers del dominio en lugar de duplicar lógica?
4.  ¿Se previene rigurosamente la introducción de fuentes de verdad lógicas alternativas?
5.  ¿Se han blindado las invariantes del sistema mediante aserciones en la suite de pruebas?
6.  ¿La especificación en `docs/documentation-map.yaml` y la documentación canónica permanecen alineadas?
7.  ¿Se ha verificado que la sintaxis generada por el agente no introduce alucinaciones semánticas en el dominio?

Cualquier PR que modifique la semántica orientada al cliente o la coherencia entre fases debe certificar de manera obligatoria la sección **Assessment coherence checks** en `.github/pull_request_template.md`.

## Interacción con Compuertas Automáticas

Los validadores automatizados del repositorio representan compuertas necesarias pero no suficientes para la integración del cambio.

El ciclo de desarrollo recomendado sigue esta secuencia determinista:
1.  **Declaración:** Confeccionar la Especificación Mínima Verificable.
2.  **Acotamiento:** Limitar el entorno de trabajo al delta de cambios mínimo.
3.  **Implementación:** Codificar la solución apoyándose en esquemas Pydantic y políticas de dominio.
4.  **Certificación Local:** Ejecutar localmente la suite de pruebas unitarias y los validadores de calidad.
5.  **Revisión:** Someter el PR a revisión humana orientada a arquitectura y semántica.
6.  **Ciclo de Feedback:** Subsanar observaciones iterativamente sin evadir las compuertas automáticas.
7.  **Fusión:** Completar el merge una vez que todos los checks automáticos de GitHub estén en verde.

Si se utiliza un agente autónomo para la reconciliación automatizada pos-PR, sus operaciones se rigen estrictamente bajo el siguiente mandato operativo:
-   Analizar de forma exhaustiva los logs de error de las compuertas de GitHub y los comentarios de revisión.
-   Sincronizar y re-integrar la rama de trabajo con la base `main` cuando GitHub indique desactualización.
-   Resolver y depurar de forma quirúrgica las desviaciones en la rama.
-   Verificar localmente la conformidad del cambio empleando las herramientas de calidad del repositorio.
-   Realizar el push del delta correctivo.
-   Monitorear pasivamente los checks oficiales de integración, deteniéndose inmediatamente ante bloqueos de gobernanza o restricciones de protección de rama que escapen a sus atribuciones de contexto.

## Regla de Bloqueo Operativo

Si un ciclo de desarrollo interactivo asistido por agente no dispone de una definición inequívoca del problema, delimitación del alcance de cambio, identificación de la fuente de verdad gobernante y especificación de las invariantes a proteger, **la sesión carece de elegibilidad técnica para realizar modificaciones físicas sobre el repositorio.**

## Interacción con Requerimientos de Negocio

Cuando una iniciativa provenga directamente de requerimientos funcionales o comerciales de negocio (*Product Owner*) en lugar de especificaciones técnicas directas, se debe invocar el orquestador descrito en [`product-owner-orchestrator.md`](product-owner-orchestrator.md) para traducir y estructurar la intención comercial en especificaciones atómicas, tareas lógicas acotadas y aserciones de conformidad automáticas antes de intervenir la base de código.
