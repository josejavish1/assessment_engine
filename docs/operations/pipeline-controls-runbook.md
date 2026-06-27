---
status: Verified
owner: docs-governance
source_of_truth:
- ../../src/assessment_engine/application/run_tower_pipeline.py
- ../../src/assessment_engine/application/run_global_pipeline.py
- ../../src/assessment_engine/application/run_commercial_pipeline.py
- ../../src/assessment_engine/adapters/render_web_presentation.py
- ../../src/assessment_engine/application/tools/check_vertex_ai_access.py
- ../../src/assessment_engine/application/tools/regenerate_smoke_artifacts.py
- ./pipeline-execution.md
- ./troubleshooting-working.md
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: how_to
verification_mode: workflow
---
# Pipeline controls runbook

Este manual de operaciones (*runbook*) formaliza el protocolo de control, supervisión e intervenciones correctivas aplicables sobre la tubería de ejecución del motor. Define de manera determinista los checkpoints pre-vuelo, la telemetría de éxito de cada fase y los árboles de decisión ante interrupciones operacionales.

## Dimensiones de Protección y Continuidad

1.  **Continuidad Operacional:** Garantía de transaccionalidad de generación de deliverables.
2.  **Coherencia Semántica:** Prevención de fragmentación lógica (*split-brain*) inter-fases.
3.  **Diagnóstico Expedito:** Aislamiento rápido de cuellos de botella mediante logs estructurados.
4.  **Aislamiento de Causas Raíz:** Discriminación explícita entre anomalías de red/autenticación, desviaciones contractuales de payloads o fallas de renderizado visual.

## Checklist de Verificación de Checkpoints Pre-vuelo

| Checkpoint | Validación Empírica | Propósito en el Dominio |
|---|---|---|
| **Entorno Aislado Certificado** | Ejecución activa bajo `./.venv/` | Asegura el aislamiento de paquetes y consistencia de librerías. |
| **Integridad de Dependencias** | `pip check` | Certifica la disponibilidad completa de las dependencias lógicas. |
| **Gobernanza de Acceso a Vertex AI** | Ejecución de `check_vertex_ai_access.py` | Previene fallas tempranas de autenticación en llamadas generativas. |
| **Aprovisionamiento de Entradas** | Presencia física de context-files y responses | Valida que la tubería disponga de materia prima para operar. |
| **Disponibilidad de Ruta de Trabajo** | `working/<client>` legible y escribible | Garantiza los permisos de E/S necesarios para persistir artefactos. |

## Secuencia de Ejecución Estándar

1.  **Preflight de Infraestructura Cloud:** Certificar el acceso al proveedor de IA antes de consumir créditos.
2.  **Análisis por Dominio Tecnológico:** Ejecutar el flujo por torre para fabricar la verdad base de cada especialidad.
3.  **Consolidación Ejecutiva Global:** Unificar el estado de las torres activas bajo la agenda directiva del cliente.
4.  **Generación de Plan Comercial:** Formular propuestas de inversión y planes de cuenta acoplados a la verdad técnica.
5.  **Compilación de Visualización Web:** Generar la interfaz web interactiva agregada para soporte de presentación.
6.  **Validación y Certificación:** Ejecutar pruebas de regresión y smoke-tests para blindar el repositorio ante derivas.

## Telemetría de Éxito por Fase

| Fase | Artefacto de Certificación | Checkpoint de Salud Mínimo |
|---|---|---|
| **Preflight IA** | Retorno exitoso del script de acceso. | Autenticación y cuotas de Vertex AI certificadas. |
| **Torre** | `blueprint_<tower>_payload.json` | Existencia y consistencia estructural frente al esquema de Pydantic. |
| **Annex** | `approved_annex_<tower>.template_payload.json` | Handover directivo derivado sin contradicciones del blueprint. |
| **Global** | `global_report_payload.json` | Agregación de torres refinada sin lógicas huérfanas de legado. |
| **Comercial** | `commercial_report_payload.json` | Mapeo de oportunidades comerciales justificado técnicamente. |
| **Web** | `working/<client>/presentation/index.html` | Dashboard HTML interactivo compilado sin pérdidas de datos. |
| **Baseline Smoke** | Árbol `smoke_ivirma` completo. | Integridad de todos los artefactos físicos e informe de tests en verde. |

*Nota de Gobernanza:* El smoke-test en su modo consolidado global (`--with-global`) ejecuta la agregación canónica nativa a partir de blueprints. Si el baseline global requiere de lógicas retrocompatibles para compilar, la anomalía debe depurarse prioritariamente como una desviación estructural del motor y no como una variante de ejecución permitida.

## Matriz de Diagnóstico de Incidentes por Síntoma

| Síntoma Observable | Causa Raíz Probable | Acción Operativa Recomendada |
|---|---|---|
| Fallo en la instanciación de cualquier payload IA. | Interrupción de red, vencimiento de tokens o cuotas excedidas en Vertex AI. | Ejecutar la utilidad de diagnóstico `check_vertex_ai_access`. |
| Entradas disponibles pero omisión en la generación de blueprints. | Bloqueo o timeout en el motor de síntesis de la torre. | Inspeccionar logs estructurados de `run_tower_pipeline.py`. |
| Blueprint correcto pero ausencia o inconsistencia del anexo directivo. | Falla de aserción en el sintetizador ejecutivo de handover. | Auditar trazas de error de `run_executive_annex_synthesizer.py`. |
| Blueprints estables pero falla en la consolidación global. | Conflicto de fusión o anomalía en el builder global de payloads. | Depurar lógica de agregación en `build_global_report_payload.py`. |
| Payload global verificado pero error en la activación comercial. | Falla lógica en el refinador de cuenta. | Diagnosticar parámetros de ejecución de `run_commercial_refiner.py`. |
| Payloads estables pero entregable OpenXML `.docx` corrupto o desalineado. | Desviación de diseño en la plantilla física o en el renderer OpenXML. | Corregir de forma desacoplada el script renderer y la plantilla física; prohibido alterar la lógica de negocio del payload. |
| Interrupción de pruebas unitarias asociadas a la ruta de trabajo `working/`. | Desactualización o ausencia física de los artefactos del baseline. | Verificar la existencia de los JSON e inicializar el regenerador de smoke. |

*Gobernanza Semántica de Métricas:* Ante inconsistencias observadas entre las métricas de score y las bandas cualitativas asociadas, la intervención correctiva debe ocurrir de forma obligatoria en la política de madurez compartida de la plataforma (`maturity_band.py`) y en sus consumidores centralizados, prohibiéndose la redefinición lógica local en prompts o renderizadores.

## Protocolo de Intervención Rápida

### 1. Interrupción de Red o Autenticación
Ante sospechas de fallas de conexión o credenciales expiradas en Google Cloud, invoque:
```bash
python -m assessment_engine.application.tools.check_vertex_ai_access
```

### 2. Deriva Contractual entre Capas
Si una fase derivada falla pero la fase precedente completó con éxito:
1.  Verifique la compatibilidad estructural del payload de origen frente a su esquema de Pydantic correspondiente.
2.  Descarte la presencia de normalizaciones excepcionales no documentadas en la capa de renderizado.
3.  Verifique la actualización física de las dependencias de datos del módulo consumidor.

### 3. Degradación en la Capa Estética de Presentación
Si los payloads de datos son correctos pero el deliverable final presenta distorsiones de diseño:
1.  Verifique la alineación de estilos e integridad OpenXML en la plantilla de origen.
2.  Inspeccione el mapeo de variables lógicas en el renderer de destino.
3.  Se prohíbe realizar modificaciones directas en el código de negocio para subsanar desviaciones de formateo visual.

## Matriz de Recuperación ante Desastres

| Incidente Operacional | Ruta de Recuperación Certificada |
|---|---|
| **Eliminación accidental del baseline local** | Ejecutar el aprovisionador: `python -m assessment_engine.application.tools.regenerate_smoke_artifacts` |
| **Interrupción prolongada del proveedor Cloud** | Conmutar de forma segura a ejecución local libre de APIs: `--local-only` |
| **Bloqueos transitorios por latencias de red** | Forzar la expiración transaccional configurando timeouts explícitos de ejecución. |
| **Ausencia de telemetría por torre** | Relanzar el orquestador por torre o reanudar desde el checkpoint estable de origen. |
| **Ausencia de telemetría global o comercial** | Relanzar específicamente la fase consumidora inmediata agregando los flags correspondientes. |

## Prácticas Prohibidas y Anti-patrones Operacionales

1.  **Asunción Errónea de Defectos:** Atribuir fallas de aserción en pytest a bugs lógicos sin certificar previamente la integridad física del baseline en `working/`.
2.  **Validación Basada en Presentación:** Consumir documentos OpenXML compilados de formato estético como prueba de la verdad estructural del diagnóstico.
3.  **Parcheo Lateral:** Corregir inconsistencias de datos de negocio modificando la lógica de formateo del renderizador o alterando manualmente el documento de salida.
4.  **Uso de Lógicas de Compatibilidad Residual:** Confiar en flujos o fallback heredados de forma preferente cuando el sistema ya dispone de payloads canónicos tipados.

## Indicadores de Estabilidad Operativa

El estado operacional del motor se considera bajo gobernanza y control estricto cuando:
-   Los payloads estructurados residen de forma íntegra en sus rutas deterministas.
-   El andamiaje de pruebas `smoke_ivirma` es 100% reproducible y determinista.
-   Las alertas e interrupciones discriminan con exactitud entre anomalías de API generativa, desviaciones contractuales o fallas de renderizado.
-   La base de conocimiento de la plataforma coincide plenamente con el comportamiento ejecutable del repositorio.

## Referencias Cruzadas Autorizadas

-   **Ejecución y Flujos:** [`pipeline-execution.md`](pipeline-execution.md)
-   **Troubleshooting y Regeneración de Smoke-test:** [`troubleshooting-working.md`](troubleshooting-working.md)
-   **Contratos e Interfaces:** [`../contracts/artifact-contracts.md`](../contracts/artifact-contracts.md)
