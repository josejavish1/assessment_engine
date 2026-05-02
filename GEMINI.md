---
status: Needs Review
owner: docs-governance
source_of_truth:
  - docs/ai/documentation-governance.md
  - docs/README.md
  - docs/SYSTEM_ARCHITECTURE.md
  - src/assessment_engine/
last_verified_against: 2026-05-01
applies_to:
  - gemini
doc_type: operational
---

# Directiva de Agente: Memoria Operativa del Proyecto

> **Estado documental:** `Needs Review`
>
> **Rol actual:** este fichero pasa a ser un **adaptador operativo para Gemini** y una memoria útil en transición. La política documental central vive en [`docs/ai/documentation-governance.md`](docs/ai/documentation-governance.md) y el mapa maestro en [`docs/README.md`](docs/README.md).
>
> Este archivo **ya no debe tratarse como fuente única de verdad**. Si hay conflicto entre esta narrativa y el código, tests, workflows, schemas o documentación canónica, manda el repo ejecutable y la documentación central.

Este documento recoge contexto operativo y arquitectónico útil para Gemini, pero debe mantenerse alineado con la base documental común del proyecto.

---

## 1. Visión y Propósito del Sistema

El `assessment-engine` es una **fábrica de generación de documentos** diseñada para producir entregables de assessment tecnológico de nivel B2B. Utiliza un pipeline orquestado por Python y asistido por agentes de IA para transformar datos brutos de evaluaciones en una serie de informes coherentes y de alto valor.

---

## 2. Arquitectura y Flujo de Datos (Modelo "Top-Down")

La arquitectura actual se basa en el principio "Top-Down" para garantizar la consistencia. El sistema se compone de dos fases principales que procesan los datos desde el nivel más detallado hasta el más estratégico.

> **Lectura canónica recomendada:** usa esta sección como resumen rápido, pero apóyate en `docs/architecture/` para la versión más mantenible y precisa del flujo actual.

### 2.1. Diagrama de Flujo de Datos

```
========================================================================================================================
| INPUTS                                                                                                               |
========================================================================================================================
|                                                                                                                      |
|   [ Customer Files: .docx, .txt ]  (desde /ficheros o /source_docs)                                                  |
|   (Respuestas, Contexto de Negocio, etc.)                                                                            |
|                                                                                                                      |
|   [ Methodological Config: .json ] (desde /engine_config)                                                            |
|                                                                                                                      |
`----------------------------------------------------------------------------------------------------------------------'
                                                     |
                                                     V
========================================================================================================================
| FASE 1: PIPELINE DE ANÁLISIS POR TORRE (Orquestador: run_tower_pipeline.py)                                           |
========================================================================================================================
|                                                                                                                      |
|   1. Preparación de Datos (Determinista):                                                                            |
|      - build_case_input.py         --> [ case_input.json ]                                                           |
|      - build_evidence_ledger.py    --> [ evidence_ledger.json ]                                                      |
|      - run_scoring.py              --> [ scoring_output.json ]                                                       |
|      - run_evidence_analyst.py     --> [ findings.json ]                                                             |
|                                                                                                                      |
|   2. Análisis Nuclear por IA (Creación de la Fuente de Verdad):                                                      |
|      - run_tower_blueprint_engine.py --> [ blueprint_Txx_payload.json ]  <--- (LA ÚNICA FUENTE DE VERDAD)             |
|                                                                                                                      |
|   3. Síntesis y Renderizado (Derivación desde la Fuente de Verdad):                                                  |
|      - run_executive_annex_synthesizer.py --> [ approved_annex_txx.template_payload.json ]                           |
|      - render_tower_blueprint.py          --> [ Blueprint_Txx.docx ]                                                 |
|      - render_tower_annex_from_template.py --> [ Annex_Txx.docx ]                                                    |
|      - generate_tower_radar_chart.py      --> [ radar_chart.png ]                                                    |
|                                                                                                                      |
`----------------------------------------------------------------------------------------------------------------------'
                                                     |
                                                     V (Agrega los `blueprint_payload.json` de varias torres)
========================================================================================================================
| FASE 2: PIPELINES GLOBALES Y COMERCIALES (Orquestadores: run_global_pipeline.py, run_commercial_pipeline.py)          |
========================================================================================================================
|                                                                                                                      |
|   1. Agregación Global:                                                                                              |
|      - build_global_report_payload.py --> [ global_report_payload.json ]                                             |
|                                                                                                                      |
|   2. Refinamiento Estratégico y Comercial por IA:                                                                    |
|      - run_executive_refiner.py    --> [ global_report_payload.json refinado ]                                       |
|      - run_commercial_refiner.py   --> [ commercial_report_payload.json ]                                            |
|                                                                                                                      |
|   3. Renderizado de Entregables Finales:                                                                             |
|      - render_global_report_from_template.py --> [ CIO_Ready_Report.docx ]                                           |
|      - render_commercial_report.py --> [ Internal_Commercial_Plan.docx ]                                           |
|      - render_web_presentation.py  --> [ Interactive_Dashboard.html ]                                                |
|                                                                                                                      |
`----------------------------------------------------------------------------------------------------------------------'

```

### 2.2. Modos de Operación
-   **1. Modo Pipeline:** Ejecución por línea de comandos de los orquestadores para generar informes de forma completa y desatendida.
-   **2. Modo Servidor de Herramientas:** El script `mcp_server.py` expone las capacidades del motor como un servicio, permitiendo que un agente de IA supervisor externo orqueste el proceso de forma dinámica.

### 2.3. Arquitectura "Legacy" (Archivada)
En `src/assessment_engine/scripts/_legacy` se encuentra la arquitectura anterior, que generaba cada sección del informe en paralelo. Fue abandonada por el problema de "split-brain" (inconsistencia entre secciones).

---

## 3. Análisis de Calidad de Código (Memoria de evaluación)

### 3.1. Resumen Ejecutivo
El `assessment-engine` es un prototipo avanzado con una base arquitectónica muy sólida y sofisticada. Sin embargo, su rápida evolución ha generado una deuda técnica notable. El concepto es de nivel "enterprise", pero el código necesita una fase de consolidación para ser verdaderamente robusto y mantenible.

### 3.2. Evaluación por Áreas
-   **Arquitectura y Diseño (4/5):**
    -   **Fortalezas:** Principios de diseño (Top-Down, Contract-First) excelentes. Arquitectura dual (pipeline/servidor) muy avanzada.
    -   **Debilidades:** Scripts monolíticos que mezclan responsabilidades (especialmente los `render_*.py`).
-   **Calidad de Código y Mantenibilidad (3/5):**
    -   **Fortalezas:** Buena nomenclatura, uso excelente de Pydantic y centralización de utilidades en `lib/`.
    -   **Debilidades:** Persisten scripts monolíticos y partes del sistema con alto acoplamiento. El problema estructural de `PYTHONPATH` ha quedado resuelto, pero todavía queda deuda de modularización en varios renderizadores.
-   **Robustez y Fiabilidad (4/5):**
    -   **Fortalezas:** Gestión de la interacción con IA (`ai_client.py`) y manejo de datos (`robust_load_payload`) de nivel de producción.
    -   **Debilidades:** Gestión de errores inconsistente fuera de la capa de IA.
-   **Pruebas y Verificación (3.5/5):**
    -   **Fortalezas:** Uso de patrones de testing maduros (Tests de Contrato, Golden File Tests).
    -   **Debilidades:** Cobertura de tests unitarios baja para la lógica determinista.

---

## 4. Roadmap Estratégico de Endurecimiento (Memoria histórica de trabajo)

Este es el plan de acción para elevar la calidad del proyecto. La priorización busca maximizar el retorno de la inversión en cada fase, donde el "retorno" es una combinación de **reducción de riesgo** y **aumento de la velocidad de desarrollo futura**.

### **Prioridad 1: "Dejar de Sangrar" - Habilitación de la Velocidad y Reducción de Riesgo**
*(ROI: Muy Alto)*
Esta fase tiene el ROI más inmediato. No añade funcionalidades, pero arregla los problemas fundamentales que hacen que cualquier cambio sea lento y peligroso.

1.  **Empaquetar el Proyecto:**
    *   **Acción:** Crear un `setup.py` o configurar `pyproject.toml` para que el proyecto sea instalable con `pip install -e .`.
    *   **Retorno:** Resuelve todos los problemas de `PYTHONPATH` de forma definitiva. Reduce la fricción de desarrollo y elimina errores de entorno. Es la base de todo lo demás.

2.  **Ampliar Cobertura de Tests Unitarios:**
    *   **Acción:** Añadir tests (`pytest`) para la lógica determinista: `lib/text_utils.py`, `run_scoring.py`, `bootstrap_tower_from_matrix.py`.
    *   **Retorno:** Es la **póliza de seguros** del proyecto. Permite refactorizar con la confianza de que no se está rompiendo la lógica fundamental. Habilita directamente la siguiente fase de forma segura.

**Estado actual (2026-04-30):** Prioridad 1 completada a nivel operativo.
-   El proyecto ya se instala en modo editable desde `pyproject.toml` usando `setuptools`, sin depender de `hatchling`.
-   La suite de tests ya no necesita `PYTHONPATH=src` ni inyección manual de `sys.path` desde `tests/conftest.py`.
-   Existen tests específicos para `text_utils`, `run_scoring`, `bootstrap_tower_from_matrix` y `render_web_presentation`, que actúan como red de seguridad mínima para refactors.
-   Se ha validado la instalación editable y la ejecución de tests clave directamente con `./.venv/bin/python -m pytest ...`.

### **Prioridad 2: "Pagar la Deuda Principal" - Aumento de Velocidad a Largo Plazo**
*(ROI: Alto)*
Una vez que tenemos la red de seguridad de los tests, podemos atacar la deuda técnica que más ralentiza la evolución del proyecto.

1.  **Externalizar el Contenido Web:**
    *   **Acción:** Mover el HTML/CSS/JS de `render_web_presentation.py` a sus propios ficheros. Usar un motor de plantillas (ej. Jinja2) para inyectar los datos.
    *   **Retorno:** Desbloquea la capacidad de mejorar el entregable más vistoso del proyecto de forma rápida y segura. Permite que un desarrollador frontend pueda trabajar en el dashboard sin tocar el motor de Python.

2.  **Refactorizar los Renderizadores Monolíticos:**
    *   **Acción:** Dividir los scripts `render_*.py` en módulos con responsabilidades claras: una capa para la lógica de negocio/mapeo de datos y otra puramente para el renderizado.
    *   **Retorno:** Reduce drásticamente la complejidad. Un cambio en una tabla de un Word ya no requerirá entender toda la lógica de negocio, haciendo las modificaciones más rápidas y menos arriesgadas.

### **Prioridad 3: "Pulir y Optimizar" - Mejora de la Calidad de Vida y Operatividad**
*(ROI: Medio)*
Estas acciones tienen un retorno tangible en la calidad y la experiencia de uso y mantenimiento del sistema.

1.  **Introducir Observabilidad (`run_id` y Telemetría):**
    *   **Acción:** Implementar un identificador de ejecución único (`run_id`) que se propague a todos los artefactos y logs. Ampliar `ai_client.py` para que registre el coste estimado por llamada.
    *   **Retorno:** Capacidad de depurar problemas de producción y controlar costes ("FinOps"). Inversión en la estabilidad y control futuros.

2.  **Unificar la Configuración:**
    *   **Acción:** Mover todos los ficheros de configuración, incluyendo los YAML de los prompts, a subdirectorios dentro de `engine_config/`.
    *   **Retorno:** Mejora la "calidad de vida" del desarrollador. Un único punto de verdad para toda la configuración hace el sistema más fácil de entender y modificar.

---

## 5. Base de Conocimiento y Documentación

La base documental canónica del proyecto ya no vive aquí. La ruta recomendada es:

1. `README.md`
2. `docs/README.md`
3. `docs/ai/documentation-governance.md`
4. `docs/architecture/`, `docs/operations/` y `docs/contracts/`

`docs/reference/generated/legacy-gemini/` conserva la referencia heredada útil, pero no como contenedor estratégico principal. Este `GEMINI.md` debe mantenerse breve, operativo y alineado con la documentación canónica.

---

## 6. Diario de Refactorización

-   **2026-05-02 - Endurecimiento del workflow de DevOps**
    -   Se ha refactorizado el workflow `orchestrator-pr-reconcile.yml` para mejorar su mantenibilidad y robustez.
    -   La lógica de actualización de PRs, que antes era un script inline, se ha externalizado a `.github/scripts/reconcile_prs.sh`.
    -   El nuevo script es ejecutable e incluye una gestión de errores más estricta (`set -euo pipefail`) y asegura un estado de git limpio en cada iteración.
-   **2026-04-30 - Cierre de Prioridad 1 / estabilización del entorno y tests**
    -   Se eliminó la dependencia artificial de `PYTHONPATH=src` en la suite de tests.
    -   Se retiró la manipulación manual de `sys.path` en `tests/conftest.py` y se actualizó `tests/test_environment.py` para verificar el paquete instalado en editable.
    -   Se migró el backend de build de `hatchling` a `setuptools` en `pyproject.toml`, dejando también empaquetada la plantilla HTML del dashboard.
    -   Se corrigió `pytest.ini` para eliminar configuración inválida y se actualizó la checklist operativa (`A5_CHECKLIST.md`) para reflejar el nuevo flujo de validación.
    -   Se robustecieron tests de integridad documental para que no fallen por ausencia de artefactos concretos del workspace o por variaciones razonables en headings de plantillas DOCX.
    -   Validación ejecutada: `pip install -e . --no-build-isolation`, tests clave de entorno/lógica/render y generación real del dashboard web para `ivirma`.

---

## 7. Integración y DevOps (GitHub)

Para garantizar una integración nativa, estable y segura con el repositorio de GitHub, este proyecto utiliza **GitHub CLI (`gh`)** como herramienta central de autenticación y "credential helper" para Git.

**Políticas operativas:**
-   **Nunca se deben usar tokens en texto plano** en comandos de git ni embebidos en las URLs de los remotos (ej. evitar `https://<token>@github.com/...`).
-   Las operaciones de control de versiones (`push`, `pull`, `fetch`) se ejecutan a través de HTTPS utilizando la sesión viva gestionada por `gh`.
-   El sistema está configurado mediante `gh auth setup-git`.
-   Para verificar el estado de la conexión en cualquier momento, usar: `gh auth status`.
