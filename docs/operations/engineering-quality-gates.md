---
status: Verified
owner: docs-governance
source_of_truth:
- ../../docs/operations/agentic-development-workflow.md
- ../../pyproject.toml
- ../../requirements.txt
- ../../.github/workflows/quality.yml
- ../../.github/workflows/typing.yml
- ../../.github/pull_request_template.md
- ../../AGENTS.md
- ../../.github/copilot-instructions.md
- ../../src/assessment_engine/infrastructure/global_maturity_policy.py
- ../../src/assessment_engine/application/tools/run_incremental_quality_gate.py
- ../../src/assessment_engine/application/tools/run_incremental_typecheck.py
- ../../tests/test_global_coherence.py
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: workflow
---

# Engineering quality gates

Este documento establece y define las compuertas de calidad (*quality gates*) aplicadas de forma automatizada sobre el ciclo de vida del motor. Su propósito es asegurar que cualquier cambio de código se someta a análisis estáticos de calidad y tipado estricto, complementando las pruebas de comportamiento y verificaciones de coherencia documental.

## Alcance de Validación (Superficie Activa)

Las compuertas automáticas restringen sus análisis estrictamente a la superficie de desarrollo activa del repositorio:

-   `src/assessment_engine/domain/`
-   `tests/`

Se excluyen deliberadamente las rutas históricas, obsoletas o generadas pasivamente (como la documentación técnica archivada en `docs/reference/generated/legacy-gemini/`), de modo que la deuda técnica heredada y no operativa no obstruya la agilidad en la integración de la base de código viva.

## Regla central

Las invariantes lógicas y de negocio críticas del sistema no deben residir únicamente en prompts de LLMs, registros de memoria de equipo o listas de control manual. Es un requisito ineludible que cualquier regla transversal se materialice en uno o más de los siguientes mecanismos de validación deterministas:

1.  **Políticas y Utilidades de Dominio Compartidas (Domain Policies):** Centralización de la lógica de negocio en helpers desacoplados.
2.  **Esquemas de Datos Tipados y Validaciones de Restricción:** Modelamiento estricto mediante clases Pydantic.
3.  **Pruebas Unitarias e Integración Automatizadas:** Cobertura de tests para bloquear regresiones.
4.  **Flujos de Verificación Continua (CI/CD Quality Checkpoints):** Validación de integración mediante GitHub Actions.

Cualquier decisión estructural asociada a la resolución cuantitativa, coherencia narrativa, contratos de interfaz o renderizado de deliverables no puede depender de supuestos o disciplina manual de codificación; debe estar respaldada por un guardarraíl ejecutable. El desarrollo de estas soluciones debe basarse en una especificación mínima aprobada, tal como se detalla en [`agentic-development-workflow.md`](agentic-development-workflow.md).

## Gates ejecutables actuales

### 1. Calidad Estática Incremental
El workflow `.github/workflows/quality.yml` orquesta la ejecución del script `src/assessment_engine/application/tools/run_incremental_quality_gate.py`.

El proceso de verificación realiza las siguientes operaciones secuenciales:
1.  **Determinación de Delta de Cambios:** Identificación de archivos modificados empleando diffs de Git entre `base_sha` y `head_sha`.
2.  **Filtrado de Ámbito Activo:** Selección exclusiva de rutas dentro de la superficie viva, descartando archivos eliminados en el árbol de trabajo actual.
3.  **Análisis Estático (Linter):** Ejecución de `ruff check` sobre el delta de archivos modificados.
4.  **Validación de Estilo (Formatter):** Inspección de formato empleando `ruff format --check`.

Este enfoque incremental bloquea de manera proactiva la introducción de nueva deuda técnica sin requerir la refactorización inmediata de los componentes históricos del repositorio.

### 2. Tipado Estático Incremental
El workflow `.github/workflows/typing.yml` orquesta la ejecución del script `src/assessment_engine/application/tools/run_incremental_typecheck.py`.

Este job reutiliza el mismo delta de cambios y ejecuta el análisis estático de tipos (`mypy`) exclusivamente sobre los archivos modificados dentro de `src/assessment_engine/domain/**` y `tests/**`. El objetivo de este checkpoint no es exigir la tipificación completa del código heredado de forma inmediata, sino blindar el crecimiento del sistema garantizando que cada nueva adición o modificación se adhiera al sistema de tipos estáticos.

### 3. Coherencia de Dominio
Para prevenir la duplicidad semántica de políticas y la fragmentación lógica (*split-brain*), los parámetros transversales de puntuación (*score*), bandas de madurez, gradientes cromáticos y metas cualitativas se encuentran consolidados.

El cálculo compartido de madurez reside de forma exclusiva en `src/assessment_engine/infrastructure/maturity_band.py`. Los componentes de ejecución (`run_scoring.py`, `run_executive_annex_synthesizer.py`, `render_tower_blueprint.py`, `build_global_report_payload.py` y el compilador del dashboard web) consumen este servicio de forma centralizada sin implementar deducciones o umbrales locales. A su vez, `src/assessment_engine/infrastructure/global_maturity_policy.py` hereda esta misma política para mantener la equivalencia consolidada. La consistencia lógica transversal se blinda mediante aserciones dedicadas en `tests/test_global_coherence.py`.

## Reglas de implementación del proyecto

-   **Reutilización Imperativa:** Consumir siempre helpers, esquemas de datos y utilidades de dominio compartidas antes de duplicar lógicas de cálculo o formateo.
-   **No Ocultación:** Toda lógica de negocio y de reporting técnico de alta relevancia debe codificarse de forma determinista en Python, prohibiéndose su ocultación exclusiva dentro de prompts de modelos de lenguaje.
-   **Alineamiento Multidimensional:** Ante cambios en contratos o interfaces de payload, actualizar de forma obligatoria las suites de pruebas unitarias y la documentación canónica asociada.
-   **Consistencia Directiva:** Si se modifican parámetros asociados al score, bandas de madurez, targets u otros elementos cliente-facing, es obligatorio sincronizar y certificar los tests en `tests/test_global_coherence.py`.
-   **Aislamiento de Legado:** Prohibido emplear carpetas de compatibilidad heredada, archivos obsoletos o código muerto como fuente de verdad técnica para nuevas implementaciones.

## Relación con la revisión humana

Las compuertas automáticas constituyen condiciones necesarias pero no suficientes para la integración:

-   El checklist de `.github/pull_request_template.md` exige la certificación explícita de impacto de calidad e integridad documental antes de la fusión.
-   Dicho template incluye una sección dedicada de **assessment coherence checks** para Pull Requests que modifiquen componentes de scoring, payloads canónicos, prompts de LLM o el dossier estratégico `client_intelligence`.
-   `AGENTS.md` y `.github/copilot-instructions.md` dirigen a las inteligencias artificiales a someterse a esta disciplina de calidad pre-vuelo antes de generar código.
-   El orquestador de pull requests (`.github/workflows/orchestrator-pr-reconcile.yml`), cuando está operativo, actúa coordinando los reintentos de análisis estáticos y validaciones de estado, garantizando que el pipeline de fusión respete rigurosamente todas las compuertas del repositorio.

## Ejecución local recomendada

Para certificar localmente los archivos modificados en una rama de trabajo, ejecute:

```bash
./.venv/bin/python src/assessment_engine/application/tools/run_incremental_quality_gate.py \
  --repo-root . \
  --path src/assessment_engine/application/tools/run_incremental_quality_gate.py \
  --path tests/test_run_incremental_quality_gate.py

./.venv/bin/python src/assessment_engine/application/tools/run_incremental_typecheck.py \
  --repo-root . \
  --path src/assessment_engine/application/build_global_report_payload.py \
  --path tests/test_global_coherence.py

./.venv/bin/python -m pytest \
  tests/test_global_coherence.py \
  tests/test_build_global_report_payload.py -q
```

*Nota: La ejecución local de compuertas incrementales complementa, pero no sustituye, la obligación de ejecutar la suite de pruebas unitarias (`pytest`) del proyecto antes de confirmar los cambios.*

## Estrategia de Endurecimiento Futuro

Conforme la base de código viva avance en su consolidación, las compuertas de calidad se endurecerán bajo las siguientes directrices:
1.  **Ampliación del Tipado:** Elevar el análisis de MyPy de nivel incremental (*fichero modificado*) a nivel de módulos y paquetes completos en `domain` y `application`.
2.  **Endurecimiento de Coherencia:** Ampliar los tests de coherencia cruzada para englobar aserciones semánticas en la capa comercial, alineamiento térmico y correspondencia directa en payloads web.
3.  **Validación Arquitectónica Estricta:** Incorporar análisis de dependencias de importación para blindar la estructura hexagonal, previniendo acoplamientos prohibidos entre adaptadores e infraestructura.

## Protección de Rama (`main`)

Para garantizar la estabilidad del repositorio y la integridad del proceso de integración, la rama `main` está protegida con las siguientes reglas a nivel de GitHub:

1.  **No se permiten commits directos:** Todo cambio debe integrarse a través de un Pull Request, asegurando que pasa por el proceso de revisión y validación.
2.  **Se requieren verificaciones de estado (Status Checks):** Un Pull Request no puede ser fusionado si alguno de los jobs de CI/CD configurados (como `quality` y `typing`) ha fallado.
3.  **Sincronización obligatoria con `main`:** Un Pull Request no puede ser fusionado si no está actualizado con el último commit de la rama `main`. Esto previene conflictos y asegura que las pruebas se ejecutan sobre la versión más reciente del código.
