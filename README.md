---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
- docs/ai/documentation-governance.md
- pyproject.toml
- src/assessment_engine/
- .github/workflows/daily-auto-heal.yml
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: editorial
notes: Project entry point and onboarding index.
---
# Assessment Engine

`assessment-engine` es un motor de procesamiento de datos y compilación de informes técnicos de evaluación. Su pipeline asíncrono transforma el contexto de un cliente, las evidencias documentales y las respuestas de auditoría en un grafo de relaciones semánticas (Grafo Epistémico), resolviendo niveles de madurez técnica y compilando entregables ejecutivos en formato OpenXML (.docx) y HTML.

---

## 1. Estructura de Paquetes (Arquitectura Hexagonal)

La base de código está encapsulada bajo el espacio de nombres unificado de Python `src/assessment_engine/` y sigue un patrón de diseño hexagonal desacoplado:

*   **`src/assessment_engine/domain/`:** Contiene las clases de negocio, las invariantes lógicas y los esquemas de datos estructurados de Pydantic (`schemas/ast.py`, `schemas/blueprint.py`, etc.) y las plantillas declarativas de prompts (`domain/prompts/`).
*   **`src/assessment_engine/ports/`:** Define las interfaces de puerto abstractas (ej., `document_compiler.py`) que desacoplan el dominio de la tecnología física de renderizado.
*   **`src/assessment_engine/adapters/`:** Implementa los adaptadores de entrada/salida físicos, compiladores OpenXML y renderizadores (`adapters/compilers/docx_compiler.py` para Word, y maquetadores de HTML).
*   **`src/assessment_engine/application/`:** Contiene los entrypoints lógicos de los pipelines de procesamiento de torre, consolidación global y comercial (`run_tower_pipeline.py`).
*   **`src/assessment_engine/application/tools/`:** Aloja las utilidades operativas y la suite de validación continua de calidad documental.
*   **`src/assessment_engine/infrastructure/`:** Implementa la persistencia del grafo, clientes de APIs efímeros de Vertex AI/Gemini (`ai_client.py`) y utilidades comunes.
*   **`src/assessment_engine/prompts/`:** Almacena el registro de prompts de soporte de los agentes.

---

## 2. Onboarding e Instalación Local

### Requisitos Previos:
*   Python 3.11 instalado en el sistema operativo.
*   Acceso a la línea de comandos (Terminal/Bash).

### Configuración del Entorno:
1.  **Crear el entorno virtual de Python:**
    ```bash
    python -m venv .venv
    ```
2.  **Activar el entorno virtual:**
    ```bash
    source .venv/bin/activate
    ```
3.  **Instalar dependencias y paquete local en modo editable:**
    ```bash
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e .
    ```
4.  **Instalar la suite de ganchos Git (Pre-commit hooks):**
    ```bash
    pip install pre-commit
    pre-commit install
    ```

---

## 3. Validación y Ejecución de Pruebas

Para garantizar la estabilidad del motor tras realizar cualquier modificación, ejecuta la batería completa de pruebas unitarias e integrales locales:

```bash
PYTHONPATH=src .venv/bin/pytest
```

La suite de pruebas contiene 105 tests y está configurada en `pyproject.toml` para ignorar advertencias cruzadas y evitar el descubrimiento de directorios de trabajo efímeros (`working/`).

---

## 4. Gobernanza y Calidad Documental

El repositorio cuenta con un sistema de verificación estricta de la documentación para evitar la obsolescencia y la deriva de información (*documentation drift*):

*   **Sincronización de Esquemas:** El linter automático verifica que las propiedades y tipos de las tablas en `docs/contracts/` coincidan bit a bit con los esquemas Pydantic del código de Python.
*   **Bucle de Auto-Curación Pre-Commit:** Al ejecutar `git commit`, un gancho local de pre-commit corrige de forma desatendida y actualiza las tablas Markdown con cualquier cambio que hayas introducido en el código.
*   **Nightly Reconciliador:** GitHub Actions ejecuta un flujo diario de auto-curación (`daily-auto-heal.yml`) a medianoche para formatear, linterizar, compilar sitemaps de IA (`llms-full.txt`) y reconciliar el repositorio.

---

## 5. Orden de Lectura Recomendado

Para asimilar el funcionamiento de la plataforma en profundidad:

1.  **Gobernanza:** [docs/ai/documentation-governance.md](docs/ai/documentation-governance.md) (Reglas de calidad documental).
2.  **Arquitectura:** [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md) (Diagrama de capas y flujos de datos).
3.  **Contratos:** [docs/contracts/payload-render-boundaries.md](docs/contracts/payload-render-boundaries.md) (Límites de payloads).
4.  **Operaciones:** [docs/operations/troubleshooting-working.md](docs/operations/troubleshooting-working.md) (Manual de resolución de incidencias y regeneración de humo).
