---
status: Verified
owner: docs-governance
source_of_truth:
- ../docs/documentation-map.yaml
- ../src/assessment_engine/application/tools/validate_documentation_governance.py
- ../.github/workflows/daily-auto-heal.yml
last_verified_against: 2026-06-26
applies_to:
- repository
doc_type: canonical
diataxis: explanation
verification_mode: editorial
notes: Documentation directory index and map overview.
---
# Mapa maestro de documentación

Este directorio es la **entrada principal** para entender, navegar y mantener la documentación técnica de `assessment-engine`.

Su propósito es orientar al lector hacia la sección adecuada de la base de conocimiento y mantener la visibilidad sobre cuáles piezas describen el estado operativo actual, cuáles son guías de mantenimiento operativo y cuáles representan contratos o arquitectura.

---

## 1. Jerarquía de verdad

El repositorio opera bajo una estricta jerarquía de verdad de cuatro niveles para resolver contradicciones:

1.  **Código ejecutable:** Esquemas de Pydantic, suites de pytest, flujos de GitHub Actions y configuración física.
2.  **Documentación canónica:** Contratos y especificaciones conceptuales alojados bajo `docs/` y el directorio raíz.
3.  **Referencia derivada:** Inventarios autogenerados o reportes de análisis intermedios.
4.  **Adaptadores de contexto:** Ficheros específicos de personalización para agentes de IA externos.

Si un documento narrativo contradice el comportamiento del código o de los contratos, **manda el repositorio ejecutable**.

---

## 2. Mapa de navegación del árbol documental

| Necesidad del Lector | Documento de Entrada Recomendado |
|---|---|
| Ubicar las políticas y reglas de calidad documental | [`ai/documentation-governance.md`](ai/documentation-governance.md) |
| Comprender la arquitectura hexagonal a alto nivel | [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) |
| Consultar especificaciones y topologías detalladas | [`architecture/README.md`](architecture/README.md) |
| Consultar runbooks de ejecución y mantenimiento | [`operations/README.md`](operations/README.md) |
| Revisar contratos de payload y de entrada de datos | [`contracts/artifact-contracts.md`](contracts/artifact-contracts.md) |
| Ver la auditoría y traza de cambios de la plataforma | [`documentation_audit.md`](documentation_audit.md) |
| Revisar el inventario de gobernanza máquina-legible | [`documentation-map.yaml`](documentation-map.yaml) |

---

## 3. Tipos documentales declarados

*   **`canonical`:** Describe el comportamiento, la arquitectura, el modelo de datos o las reglas oficiales del sistema.
*   **`operational`:** Guías de trabajo paso a paso, manuales de instalación o runbooks de recuperación ante fallos.
*   **`reference_generated`:** Inventarios derivados, listados autogenerados por el linter o reportes de métricas.

---

## 4. Estado de gobernanza actual

La integridad y alineación del corpus se mantienen mediante un **sistema integrado de conciliación y validación continua**:

*   **Sincronización de Esquemas:** Cada confirmación (commit) verifica que los esquemas de datos del código de Python coincidan de forma idéntica con las especificaciones técnicas en las tablas Markdown de los contratos.
*   **Conciliación Pre-commit:** Al ejecutar `git commit` de forma local, el validador formatea y reescribe de manera automática las tablas Markdown que presenten desviaciones antes de consolidar el cambio.
*   **Validación Diaria Continua:** GitHub Actions ejecuta un flujo automatizado diario a medianoche (`daily-auto-heal.yml`) para verificar la consistencia del código, ejecutar análisis estáticos, compilar el mapa maestro de sitemaps (`llms-full.txt`) y reconciliar el estado del repositorio.

---

## 5. Qué hacer ante dudas o contradicciones

1.  Comprobar la ruta y el estado del documento en `docs/documentation-map.yaml`.
2.  Inspeccionar las fuentes de verdad (`source_of_truth`) declaradas en el front matter del documento.
3.  Contrastar la descripción prosa contra las firmas de código, tests o contratos de Pydantic correspondientes.
4.  Si se detecta un desajuste o falta de claridad conceptual, tratar el documento como `Needs Review`.
