---
status: Verified
owner: docs-governance
source_of_truth:
- ../../pyproject.toml
- ../../tests/integration/test_validate_contracts_schemas.py
- ../../src/assessment_engine/application/run_tower_pipeline.py
- ../../src/assessment_engine/application/run_global_pipeline.py
- ../../src/assessment_engine/application/run_commercial_pipeline.py
- ../../src/assessment_engine/application/tools/regenerate_smoke_artifacts.py
- ../architecture/working-artifacts.md
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: workflow
---
# Troubleshooting `working/` and Smoke Artifacts Playbook

Este manual de operaciones unifica el diagnóstico, la resolución de fallos y el **playbook de regeneración reproducible de artefactos de humo (`smoke_ivirma`)** para restaurar el entorno cuando se presentan inconsistencias lógicas o fallas de validación en el directorio temporal `working/`.

---

## 1. El Estado de Conformidad (*Baseline State*)

La suite de pruebas unitarias de contratos y entregables (`test_validate_contracts_schemas.py` y `test_payload_validation.py`) consume artefactos de datos reales de prueba previamente compilados en lugar de instanciar mocks puramente desacoplados.

Para el verde absoluto de la suite, se exige la presencia física de los siguientes artefactos en tu disco local:

*   `working/smoke_ivirma/T5/blueprint_t5_payload.json`
*   `working/smoke_ivirma/T5/approved_annex_t5.template_payload.json`
*   `working/smoke_ivirma/T5/Blueprint_Transformacion_T5_smoke_ivirma.docx`
*   `working/smoke_ivirma/T5/annex_t5_smoke_ivirma_final.docx`
*   `working/smoke_ivirma/global_report_payload.json`
*   `working/smoke_ivirma/commercial_report_payload.json`
*   `working/smoke_ivirma/presentation/index.html`

Si estos archivos son eliminados, alterados o sufren derivas contractuales, los tests del sistema fallarán o se ignorarán.

---

## 2. Protocolo de Diagnóstico Rápido

Si registras un fallo en pytest, ejecuta estas aserciones de diagnóstico físico:

### A. Inspección de Estructura de Trabajo General
```bash
find working -maxdepth 3 -type f | sort
```

### B. Inspección del Perfil de Cliente
```bash
find working/smoke_ivirma -maxdepth 2 -type f | sort
```

---

## 3. Playbook de Regeneración de Artefactos de Humo

Si constatas la ausencia, alteración o desactualización del baseline, utiliza el runner dedicado de la plataforma para regenerarlo de forma idéntica y trazable.

### Comando Base (Aprovisionamiento Estándar):
```bash
python -m assessment_engine.application.tools.regenerate_smoke_artifacts
```
*Por defecto, este comando regenera el cliente `smoke_ivirma`, torre `T5` y escenario `baseline` usando la semilla determinista `42`.*

---

### Variantes Operativas y Casos de Uso Avanzados:

#### A. Simulación Rápida en Seco (*Dry-run*):
Para validar la orquestación y regeneración de artefactos sin realizar llamadas costosas ni consumir tokens de la API de Vertex AI:
```bash
python -m assessment_engine.application.tools.regenerate_smoke_artifacts --dry-run
```
*Este modo sustituye las salidas de la IA por estructuras sintácticamente perfectas vacías para validar que el pipeline de compilación no tenga roturas lógicas.*

#### B. Ejecución Fuera de Línea (*Air-gapped / Local-only*):
Si no dispones de conexión a internet o el proveedor de Cloud sufre una interrupción temporal del servicio, puedes regenerar el baseline local desactivando por completo las llamadas a LLMs:
```bash
python -m assessment_engine.application.tools.regenerate_smoke_artifacts --local-only
```
*Este modo utiliza un caché de respuestas y plantillas almacenado de forma segura en `templates/` para simular la ejecución de forma 100% offline.*

#### C. Regeneración con Consolidación Global, Comercial y Web:
Para ejecutar una prueba de humo de integración de extremo a extremo que valide la cascada de compilación completa:
```bash
python -m assessment_engine.application.tools.regenerate_smoke_artifacts --with-global --with-commercial --with-web
```

#### D. Pruebas Multi-Torre en Escenarios Personalizados:
Para validar el comportamiento del motor bajo una topología compleja con múltiples especialidades tecnológicas:
```bash
python -m assessment_engine.application.tools.regenerate_smoke_artifacts \
  --client vodafone_demo \
  --scenario vodafone-public \
  --towers T2 T3 T5 \
  --with-global --with-commercial --with-web
```

---

## 4. Validación de Acceso a Google Cloud / Vertex AI

Si deseas validar las cuotas, credenciales y conexión con Vertex AI antes de lanzar una regeneración con IA:

```bash
python -m assessment_engine.application.tools.check_vertex_ai_access
```

### Resolución de Errores Comunes de Acceso Cloud:
*   **Error:** `GoogleDefaultCredentialsError` / `PermissionDenied` en la llamada generativa.
*   **Solución:**
    1.  Verificar que las credenciales locales estén inicializadas de forma activa en la sub-shell actual:
        ```bash
        gcloud auth application-default login
        ```
    2.  Si tu red local restringe la conexión con los servidores de Google, conmutar la ejecución utilizando el flag `--local-only`.

---

## 5. Directrices de Mantenimiento ante Cambios en Código

Cuando realices modificaciones en el motor (como alterar la lógica de scoring o expandir Pydantic schemas) que rompan de forma legítima el baseline antiguo:
1.  **Regenera el Baseline:** Lanza `python -m assessment_engine.application.tools.regenerate_smoke_artifacts --with-global --with-commercial --with-web` para compilar los nuevos payloads conformes.
2.  **Verifica en Verde:** Corre la suite de tests (`pytest tests/`) para asegurar que el rastro de aserciones transicione con éxito al estado verde brillante.
3.  **Garantiza la Coherencia Transversal:** Verifica que no se hayan introducido divergencias métricas entre el scoring de Python y el storytelling de los Word compilados en la carpeta temporal.
