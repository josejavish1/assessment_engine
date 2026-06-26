---
status: Verified
owner: docs-governance
source_of_truth:
- ../../pyproject.toml
- ../../tests/test_contract_handover.py
- ../../tests/test_t5_golden.py
- ../../src/assessment_engine/application/run_tower_pipeline.py
- ../../src/assessment_engine/application/run_global_pipeline.py
- ../../src/assessment_engine/application/run_commercial_pipeline.py
- ../architecture/working-artifacts.md
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: workflow
---

# Troubleshooting `working/` and artifact-dependent validation

Este manual de operaciones establece los protocolos de diagnóstico, resolución de fallos y recuperación del entorno de ejecución cuando se presentan inconsistencias, ausencias de datos de telemetría o fallas de validación de contratos en el directorio de trabajo `working/`.

## Parámetros de Referencia del Entorno Virtual (*Baseline State*)

Bajo el estado de conformidad certificado del repositorio, el árbol de trabajo debe verificar la presencia física de los siguientes artefactos basales:

-   `working/smoke_ivirma/T5/blueprint_t5_payload.json` (disponible).
-   `working/smoke_ivirma/T5/approved_annex_t5.template_payload.json` (disponible).
-   `working/smoke_ivirma/global_report_payload.json` (disponible).
-   `working/smoke_ivirma/commercial_report_payload.json` (disponible).
-   `working/smoke_ivirma/presentation/index.html` (disponible).

La suite completa de pruebas unitarias (`pytest`) se ejecuta con éxito cuando estos activos de referencia se encuentran estables en el entorno. La alteración, eliminación o inconsistencia en la generación de estos artefactos basales provocará fallas de validación contractual o aserciones ignoradas (*skipped tests*) debido a la desactualización del estado de referencia.

## Naturaleza de las Pruebas de Telemetría

Ciertos componentes de la suite de pruebas unitarias implementan validaciones que consumen artefactos de datos previamente compilados en lugar de instanciar mocks puramente desacoplados. Por consiguiente, la presencia íntegra del baseline es una condición necesaria para el estado verde de la suite; su ausencia o fragmentación inducirá fallas de validación que no necesariamente constituyen un defecto funcional en el motor.

## Protocolo de Diagnóstico Expedito

### 1. Inspección de Estructura de Trabajo General
Para listar de forma recursiva los artefactos de datos activos en el entorno, ejecute:
```bash
find working -maxdepth 3 -type f | sort
```

### 2. Inspección de un Dominio Tecnológico Específico
Para certificar el estado de los payloads de una torre aislada, ejecute:
```bash
find working/<client>/<tower> -maxdepth 1 -type f | sort
```

### 3. Inspección del Perfil Completo del Cliente
Para auditar la totalidad de los entregables y payloads de consolidación de una cuenta, ejecute:
```bash
find working/<client> -maxdepth 2 -type f | sort
```

## Protocolos de Regeneración de Artefactos de Telemetría

### 1. Ausencia de Payloads de Torre Tecnológica
Para regenerar el payload estructural e informes de un dominio tecnológico aislado, invoque el orquestador correspondiente:
```bash
./.venv/bin/python -m assessment_engine.application.run_tower_pipeline \
  --tower T5 \
  --client ivirma \
  --context-file /ruta/al/contexto.docx \
  --responses-file /ruta/a/respuestas.txt
```

En caso de que la inconsistencia resida específicamente en el baseline del cliente de referencia (`smoke_ivirma`), se debe ejecutar el regenerador reproducible de la plataforma:
```bash
./.venv/bin/python -m assessment_engine.application.tools.regenerate_smoke_artifacts
```

Para forzar la compilación incluyendo la fase global determinista, ejecute:
```bash
./.venv/bin/python -m assessment_engine.application.tools.regenerate_smoke_artifacts --with-global
```

Para aislar y descartar si el bloqueo operativo se debe a fallas de autenticación con el proveedor de IA o a restricciones de red, realice una ejecución en seco puramente local:
```bash
./.venv/bin/python -m assessment_engine.application.tools.regenerate_smoke_artifacts --local-only
```

### 2. Ausencia de Payload de Consolidación Global
Para forzar la agregación y refinamiento estratégico global de un cliente, ejecute:
```bash
./.venv/bin/python -m assessment_engine.application.run_global_pipeline <client_name>
```

### 3. Ausencia de Payload de Activación Comercial
Para compilar el plan de cuenta comercial y pipeline de oportunidades del cliente, ejecute:
```bash
./.venv/bin/python -m assessment_engine.application.run_commercial_pipeline <client_name>
```

## Mapeo de Dependencias de Pruebas Unitarias

### Módulos con Dependencia de Telemetría Directa (*Baseline Required*)
-   `tests/test_contract_handover.py`
-   `tests/test_t5_golden.py`
-   Fracciones específicas de `tests/test_payload_validation.py`

### Módulos Desacoplados (*Standalone Execution*)
-   `tests/test_environment.py`
-   Suites de validación sintáctica de esquemas de datos Pydantic.
-   Módulos de formateo y renderización unitaria desacoplados que instancian sus propios mocks de prueba.

## Directrices Operativas de Resolución

Si se registra una falla de validación o interrupción de prueba debido a la ausencia de activos en `working/`:
1.  **Aislamiento:** No asuma de forma inmediata la presencia de una desviación lógica de código.
2.  **Verificación:** Confirme mediante los comandos de diagnóstico si el payload JSON u OpenXML esperado reside físicamente en la ruta correspondiente de `working/`.
3.  **Aprovisionamiento:** Si se constata su ausencia, re-ejecute la fase precedente de la tubería para aprovisionar el activo.
4.  **Certificación:** Proceda a relanzar la validación o prueba para confirmar el estado verde.

Si el smoke global canónico (`--with-global`) falla, la interpretación técnica correcta indica que existe una regresión lógica o una dependencia indeseada de lógicas retrocompatibles fuera del flujo principal, debiendo depurarse de inmediato como desviación del motor.

## Relación con la Configuración de pytest

La directriz en `pyproject.toml` (bajo la clave `[tool.pytest.ini_options]`) excluye el directorio `working/` de los procesos de descubrimiento de pruebas automáticos, previniendo que se interpreten los recursos JSON como scripts de prueba, si bien mantiene plenamente la facultad del entorno para consumir estos recursos físicos como dependencias de aserción.

## Estrategia de Mantenimiento y Documentación de Derivas

Durante ciclos de modificación y evolución del motor que impacten los payloads basales, el equipo de ingeniería debe documentar de forma explícita en su reporte de integración:
-   El identificador del payload o contrato modificado.
-   La fase de la tubería responsable de su compilación.
-   Si la anomalía detectada responde a una inconsistencia de datos del baseline local o a una rotura semántica real del contrato de interfaz de la plataforma.
