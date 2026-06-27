---
status: Verified
owner: docs-governance
source_of_truth:
- ../../pyproject.toml
- ../../requirements.txt
- ../../tests/test_environment.py
- ../../.github/workflows/ci.yml
- ../../src/assessment_engine/infrastructure/runtime_env.py
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: workflow
---
# Installation and environment setup

Este documento describe y formaliza el protocolo estándar de instalación, configuración y aprovisionamiento del entorno local para el desarrollo y ejecución del motor.

## Parámetros Operacionales de Referencia

-   **Entorno de Ejecución:** Python 3.11 constituido como la versión de referencia para la integración continua (CI).
-   **Empaquetado:** El proyecto define su empaquetado y especificaciones de dependencias primarias a través de `pyproject.toml`.
-   **Entorno Aislado:** El estándar operativo local requiere el aislamiento mediante un entorno virtual ubicado de forma determinista en `.venv/`.
-   **Credenciales de Proveedor Cloud:** El pipeline asistido por inteligencia artificial exige las variables de entorno `GOOGLE_CLOUD_PROJECT` y `GOOGLE_CLOUD_LOCATION` para la conexión y firma de llamadas a Vertex AI.

## Protocolo de Aprovisionamiento

El procedimiento estándar para el aprovisionamiento y despliegue del entorno virtual local se ejecuta de la siguiente manera:

```bash
python3.11 -m venv .venv
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

## Justificación del Modo de Instalación Editable (`-e .`)

La suite de pruebas unitarias implementa un control explícito de importación de paquetes independientes del entorno de ejecución, prohibiéndose terminantemente la manipulación dinámica de rutas mediante `sys.path`. La instalación en modo editable (`-e .`) garantiza que el módulo `assessment_engine` sea plenamente visible bajo el namespace nativo absoluto sin requerir configuraciones locales excepcionales.

## Gobernanza de Variables de Env de Google Cloud

Los pipelines de evaluación por torre validan obligatoriamente la presencia de:
-   `GOOGLE_CLOUD_PROJECT`
-   `GOOGLE_CLOUD_LOCATION`

El cargador de entorno de la plataforma (`runtime_env.py`) declara como valores pasivos por defecto:
-   `GOOGLE_CLOUD_PROJECT=sub403o4u0q5`
-   `GOOGLE_CLOUD_LOCATION=europe-west1`

En caso de que las variables ya se encuentren definidas en el entorno de la sub-shell, el cargador de configuración las respeta y asume como prioritarias; en su defecto, el runtime actual poblará de forma pasiva los valores por defecto especificados.

## Protocolo de Certificación Pre-vuelo

### 1. Pruebas de Entorno
Para verificar que el aislamiento y el mapeo del paquete se completaron con éxito, ejecute:
```bash
python -m pytest tests/test_environment.py -q
```

### 2. Certificación de la Suite de Pruebas Unitarias
Para certificar la integridad técnica de todos los componentes, ejecute:
```bash
python -m pytest tests/ -q
```

### 3. Simulacro en Seco del Smoke-test (*Dry-run*)
Para validar la orquestación y regeneración de artefactos sin realizar llamadas externas a APIs, ejecute:
```bash
python -m assessment_engine.application.tools.regenerate_smoke_artifacts --with-global --dry-run
```
Este simulacro en seco (*dry-run*) forma parte de los controles de gobernanza activa del repositorio y certifica que el entorno es capaz de procesar y compilar el pipeline global canónico de forma íntegra, absteniéndose de requerir lógicas de retrocompatibilidad heredadas.

## Resolución de Dependencias: `pyproject.toml` vs `requirements.txt`

1.  **`pyproject.toml`:** Especifica el metapaquete del motor y declara la firma de dependencias abstractas obligatorias para el empaquetado.
2.  **`requirements.txt`:** Bloquea y congela un entorno de trabajo determinista de desarrollo y testing, alineado de manera idéntica con el entorno de ejecución de la integración continua (CI).

El pipeline de CI se aprovisiona consumiendo `requirements.txt` para asegurar la reproducibilidad absoluta y mitigar la deriva de paquetes.

## Estado Final de Éxito de Aprovisionamiento

Tras completar el aprovisionamiento de manera exitosa, el sistema debe certificar la disponibilidad de las siguientes capacidades:
1.  **Importación Absoluta:** Importación nativa de `assessment_engine` desde cualquier sub-shell del entorno virtual.
2.  **Ejecución de Pruebas:** Ejecución sin errores de la suite de pruebas mediante `python -m pytest`.
3.  **Ejecución de Módulos:** Lanzamiento directo de utilidades y orquestadores a través de `python -m assessment_engine.application.<modulo>`.
4.  **Compilación de Recursos:** Resolución de rutas físicas y compilación exitosa de plantillas OpenXML `.docx` y plantillas de renderizado integradas en el paquete.
