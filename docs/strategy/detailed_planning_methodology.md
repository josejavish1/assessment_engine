# 🏗️ Metodología de Planificación Técnica Detallada (Contract-First)

Este documento establece el protocolo estricto que seguiremos para pasar de la Alta Estrategia a la Implementación Técnica del **NTT Sovereign AI Engine**, garantizando que no se escriba código sin un diseño hiper-robusto previo.

Para evitar el "Cowboy Coding" y asegurar predictibilidad absoluta, la Fase 0 se ejecutará siguiendo estos 4 pasos secuenciales:

## Paso 1: El Plano Estructural (Directory Blueprint)
Antes de crear carpetas, diseñaremos el árbol de directorios teórico del paquete `ntt_sovereign_engine`.
*   **Objetivo:** Decidir la separación semántica de responsabilidades. ¿Dónde viven los adaptadores (Interfaces externas)? ¿Dónde las primitivas core (LangGraph wrapper)? ¿Dónde las excepciones custom?
*   **Entregable:** Un mapa visual en texto plano debatiendo el porqué de cada módulo.

## Paso 2: Diseño de Interfaces (API Contract / Typing)
Antes de implementar la lógica interna, definiremos las "Cabeceras" de las clases principales usando Python y Tipado Estricto (`Type Hints` / Pydantic), pero con sus cuerpos vacíos (`...`).
*   **Objetivo:** Diseñar la "Experiencia de Desarrollo" (DX). Acordar qué parámetros recibe una clase (`class NttAgent`, `class SovereignGraph`, `class SandboxAdapter`) y qué devuelve, sin pelear con bugs de ejecución.
*   **Entregable:** Un archivo `contracts_draft.py` (no funcional) que defina las firmas de todos los métodos públicos del framework.

## Paso 3: Test-Driven Architecture (El "Golden Test")
Escribiremos el código del primer test de integración o caso de uso asumiendo que el framework ya está terminado.
*   **Objetivo:** Validar si el diseño del Paso 2 es ergonómico. Si invocar al framework para una tarea sencilla resulta en código espagueti o muy verboso, significa que las interfaces están mal diseñadas y debemos iterar el Paso 2 antes de picar la lógica.
*   **Entregable:** Un script `test_usage_simulation.py` que muestre cómo un desarrollador instanciaría el motor en la vida real.

## Paso 4: Atomic Work Breakdown Structure (WBS)
Una vez el contrato y la estructura están blindados, romperemos la Fase 0 en tareas microscópicas y atómicas (Tickets).
*   **Objetivo:** Eliminar la incertidumbre de "qué hacer a continuación". Cada ticket debe ser ejecutable en una sesión corta de desarrollo y tener criterios de aceptación binarios (Pasa/No Pasa).
*   **Entregable:** Una lista de tareas (ej. "T1. Implementar `SandboxAdapter.execute()`: Levantar contenedor, montar `/tmp`, capturar `stdout`").

---
**Estado Actual:** Pendiente de iniciar el **Paso 1** cuando se retome el trabajo.
