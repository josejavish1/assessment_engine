# INSTRUCCIONES MAESTRAS DE EJECUCIÓN: PURGA DEL SPLIT-BRAIN EN LA CAPA DE PRESENTACIÓN (SR 11-7)

> **Destinatario:** Modelo Ejecutor (`gemini-3.8-flash` o agente orquestador).  
> **Mandato:** Implementar de forma exhaustiva, atómica y quirúrgica la erradicación del split-brain actuarial y las mutaciones en la capa de presentación (`adapters/` y `compilers/`), asegurando que **ningún test falle** y que los entregables DOCX continúen compilando con perfección tipográfica.  
> **Regla de Oro:** 100% Technical English en todo el código fuente, docstrings, comentarios, excepciones, nombres de variables y tests. El español es exclusivo de los archivos de localización declarativa (`locales.json`) y la comunicación en el chat.

---

## 1. Contexto y Diagnóstico Forense

El commit auditado `41d4c2d` centralizó la cuantificación actuarial en `CanonicalRiskOrchestrator`, pero la capa de presentación (`adapters/compilers/`) conserva un **motor actuarial y de negocio paralelo**:
1. `in_memory_asis_compiler.py:532-735` ejecuta `derive_in_memory_fair_risks()`, calculando pseudo-FAIR lineal (`ALE = TEF * LM * 1000`, `P90 = ALE * 2.5`) e instanciando `ActuarialInferenceEngine` con 100 M€ de facturación ficticia cuando una torre no tiene hallazgos empíricos.
2. `payload_to_ast.py` muta diccionarios en vuelo, recalibra notas de CMMI según expresiones regulares de texto (líneas 726–794), imputa notas ausentes a `2.5`, escala ALEs pro-rata (3395–3411) y re-calcula horas e importes de tarjetas de riesgo (3765–3838).
3. `tomo_asis_ast_compiler.py` recalcula ALE corporativo (`annual_revenue * 0.001`), P90 (`ALE * 2.5`), estrés a 3 años y ejecuta de forma redundante `EulerPortfolioAllocator`.
4. `asis_fair_chapter.py` define constantes actuariales (`P90_ALE_MULTIPLIER_FALLBACK = 2.5`, `MAX_LOSS_P90_MULTIPLIER_FALLBACK = 1.5`) y fabrica umbrales en render.
5. `build_global_report_payload.py:394-616` calcula un modelo de ROI/payback asumiendo el 100% de exposición evitada sin modelar riesgo residual ni efectividad de controles.
6. `render_global_report_from_template.py:1751-1757` asigna notas fraudulentas por defecto (`score = 4.0`, `band = "Managed"`, `status_color = "green"`) a torres incompletas.
7. `test_rfc084_zero_ale_prohibition_gate.py` exige que torres sin hallazgos tengan ALE > 100.000 €, forzando la retención de motores sintéticos.

---

## 2. Hoja de Ruta de Implementación (Paso a Paso)

### FASE 1: Contrato Canónico de Lectura (Presentation DTOs)
**Archivo a crear:** `src/assessment_engine/application/dtos/presentation_dtos.py`
Define los siguientes modelos Pydantic inmutables (`ConfigDict(frozen=True, extra="forbid")`):
- `EpistemicState(StrEnum)`: `EMPIRICAL_OBSERVED`, `LATENT_INFERRED`, `UNASSESSED_OUT_OF_SCOPE`, `INSUFFICIENT_TELEMETRY`.
- `OwnershipType(StrEnum)`: `PRIMARY_CUSTODIAN`, `TANGENTIAL_CONTRIBUTOR`.
- `ProvenanceMetadataDTO`: `model_version: str`, `calibration_source: str`, `epistemic_state: EpistemicState`, `assumptions_registry_id: str`.
- `PresentationFindingDTO`: contiene identificadores, títulos, textos de riesgo, madurez (`cmmi_score: Optional[float]`), métricas canónicas (`tef_annual`, `lef_annual`, `sle_mean`, `ale_expected`, `p90_var`, `max_probable_loss`, `rto_hours`, `risk_tier_label`), strings pre-formateados (`ale_display`, `p90_display`) y `provenance: ProvenanceMetadataDTO`.
- `PresentationPillarDTO`: `pillar_id`, `pillar_name`, `cmmi_score: Optional[float]`, `cmmi_band_label: str`, `status_color_token: str` ("red", "amber", "green", "grey"), `findings: tuple[PresentationFindingDTO, ...]`.
- `PresentationTowerDTO`: `tower_id`, `tower_name`, `currency_iso`, `currency_symbol`, `locale`, `overall_cmmi_score: Optional[float]`, `overall_cmmi_band: str`, `status_color_token: str`, `standalone_ale: Optional[float]`, `standalone_p90: Optional[float]`, `euler_net_ale: Optional[float]`, `diversification_adjustment: Optional[float]`, `portfolio_share_pct: Optional[float]`, `pillars: tuple[PresentationPillarDTO, ...]`, `all_findings: tuple[PresentationFindingDTO, ...]`, `provenance: ProvenanceMetadataDTO`.
- `ExecutiveFinancialBridgeDTO`: métricas de TCO/ROI pre-calculadas en dominio (o `None` si falta telemetría).
- `PresentationPortfolioDTO`: `tenant_id`, `currency_iso`, `corporate_ale`, `corporate_p90`, `corporate_max_loss`, `var_3y_expected`, `towers: tuple[PresentationTowerDTO, ...]`, `financial_bridge: ExecutiveFinancialBridgeDTO`.

### FASE 2: Orquestador y Ensamblador de DTOs en la Capa de Aplicación
**Archivo a crear:** `src/assessment_engine/application/services/assessment_valuation_orchestrator.py`
1. Recibe los payloads crudos de las torres y el `GlobalAssessmentContext`.
2. Invoca `CanonicalRiskOrchestrator.quantify_payloads()` para ejecutar la simulación de cópula y generar el manifiesto de reproducción.
3. Para cada torre:
   - Si no tiene hallazgos empíricos: marca la torre con `EpistemicState.INSUFFICIENT_TELEMETRY`, `standalone_ale = None`, y genera un finding informativo marcado como `UNASSESSED` (cero números inventados).
   - Extrae los valores del `actuarial_input_vector` generado canónicamente.
   - Resuelve el estado de custodia (`DynamicCustodyResolver`), asignando `ale_expected = 0.0` a riesgos tangenciales.
4. Ejecuta `EulerPortfolioAllocator.allocate_portfolio()` sobre los standalone ALEs canónicos para poblar `euler_net_ale` y `diversification_adjustment`.
5. Retorna `PresentationPortfolioDTO` completamente ensamblado, validado e inmutable.

### FASE 3: Purga de Motores y Mutaciones en los Compiladores
1. **`src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py`:**
   - Eliminar el bloque de cálculo de `derive_in_memory_fair_risks()` (líneas 591–625) y la instanciación de `ActuarialInferenceEngine` (671–730).
   - Convertir `derive_in_memory_fair_risks()` en una función de proyección pura que lea `actuarial_input_vector` o acepte `PresentationTowerDTO`. Si no hay hallazgos, retornar lista vacía `[]` o un registro con `ale_expected = None` y `ale_str = "UNQUANTIFIED"`.
   - Eliminar todas las mutaciones por regex a `score` (líneas 1258–1272, 1354–1370, 1725–1728, 1874–1897).
2. **`src/assessment_engine/adapters/compilers/payload_to_ast.py`:**
   - Envolver el diccionario de entrada con protección de sólo lectura (o aceptar `PresentationTowerDTO`).
   - Eliminar los imports de calibradores actuariales (`ActuarialDowntimeCalibrator`, etc.).
   - Eliminar la mutación de notas por regex (726–794) y la imputación por defecto a `2.5` (1548–1570).
   - Eliminar la normalización pro-rata de ALE (3395–3411) y la construcción manual de `FairActuarialInput` (3765–3838).
   - Si un riesgo carece de ALE canónico, renderizar etiqueta localizada `"No cuantificado"` / `"UNQUANTIFIED"`.
3. **`src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py`:**
   - Eliminar `EulerPortfolioAllocator`, el fallback de corporate ALE (`revenue * 0.001`) y el multiplicador de cola (`ALE * 2.5`).
   - Renderizar la Tabla 5 directamente desde las asignaciones pre-calculadas en `portfolio_dto` o `global_payload["portfolio_summary"]`.
4. **`src/assessment_engine/adapters/compilers/asis_fair_chapter.py`:**
   - Eliminar `P90_ALE_MULTIPLIER_FALLBACK = 2.5` y `MAX_LOSS_P90_MULTIPLIER_FALLBACK = 1.5`.
   - Leer `p90_var` y `max_probable_loss` exclusivamente de los outputs canónicos.
5. **`src/assessment_engine/adapters/render_global_report_from_template.py`:**
   - Sustituir en líneas 1751–1757 el default fraudulento (`score = 4.0, band = "Managed", status_color = "green"`) por (`score = None, band = "UNASSESSED", status_color = "grey"`).
6. **`src/assessment_engine/application/build_global_report_payload.py`:**
   - Extraer el cálculo de ROI/payback a un calculador de dominio (`domain/actuarial/executive_roi_calculator.py`), exigiendo datos antes/después explícitos. Si faltan datos, emitir `NOT_QUANTIFIED`.

### FASE 4: Blindaje de Gobernanza AST e Inmutabilidad de Tests
1. **Crear `tests/architecture/test_presentation_hermetic_immunity_ast.py`:**
   - Implementar `PresentationHermeticVisitor(ast.NodeVisitor)` que analice todos los archivos en `src/assessment_engine/adapters/` y `src/assessment_engine/compilers/`.
   - Prohibir terminantemente:
     * Imports con subcadenas: `"actuarial"`, `"euler_allocator"`, `"calibrator"`, `"inference_engine"`, `"monte_carlo"`, `"roi_calculator"`.
     * Asignaciones directas a claves de negocio: `d["score"] = ...`, `d["fair_ale_score"] = ...`, `d["total_fair_ale"] = ...`, `d["p90"] = ...`, `d["sle"] = ...`, `d["lef"] = ...`.
     * Aritmética de negocio (`*`, `/`) asignada a variables que contengan `ale`, `p90`, `cvar`, `roi`, `payback`.
2. **Crear `tests/architecture/test_compiler_read_only_contract.py`:**
   - Pasar un payload a los compiladores (`compile_payload_to_ast`, `compile_tomo_asis_ast`) y verificar con `assert copy.deepcopy(payload_before) == payload_after` que los diccionarios de entrada no sufren ninguna mutación in-place.
3. **Derogar `tests/certification/test_rfc084_zero_ale_prohibition_gate.py`:**
   - Sustituirlo por `test_epistemic_integrity_and_prior_governance_gate.py`.
   - Verificar que torres sin evidencia producen `UNASSESSED` / `NOT_QUANTIFIED` y que el compilador no inventa euros de pérdida para satisfacer un umbral arbitrario.

---

## 3. Trampas Críticas y Cómo Evitar que `gemini-3.8-flash` Falle

1. **Trampa de `NoneType` en Formatters:**  
   * *Riesgo:* Al eliminar los defaults numéricos (`2.5`, `5000`, `100000`), campos como `cmmi_score` o `ale_expected` pueden ser `None`. Si un helper hace `f"{score:.2f}"` o `format_currency(ale)`, Python lanzará `TypeError: unsupported format string passed to NoneType`.  
   * *Regla Estricta:* Todos los formatters en presentación deben comprobar explícitamente:
     ```python
     score_display = f"{score:.2f}" if score is not None else t("status_unassessed", locale=meta_lang, default="UNASSESSED")
     ale_display = format_currency(ale, ...) if (ale is not None and ale > 0) else t("status_unquantified", locale=meta_lang, default="NOT_QUANTIFIED")
     ```
2. **Trampa de Tabla Vacía en DOCX:**  
   * *Riesgo:* Si `derive_in_memory_fair_risks` devuelve `[]` para una torre sin hallazgos, `tomo_asis_ast_compiler.py` o `asis_fair_chapter.py` pueden generar una tabla sin filas de datos o fallar al indexar `risks[0]`.  
   * *Regla Estricta:* Cuando la lista de riesgos esté vacía, generar una fila tipográfica única indicando:  
     `"No empirical risk scenarios identified for this domain (Unassessed / Out of Scope)"`.
3. **Trampa de Desacoplamiento Lingüístico:**  
   * *Riesgo:* `gemini-3.8-flash` suele deslizar comentarios o textos de excepción en español (ej. `# Calcular métricas de riesgo`, `raise ValueError("El parámetro es inválido")`).  
   * *Regla Inmutable:* El verificador `test_codebase_hygiene_anti_patterns.py::test_no_spanish_characters_in_python_code` fallará si hay un solo carácter acentuado o palabra en español en `src/`. Todo comentario y mensaje de error debe estar en **100% Technical English**.
4. **Trampa de Linter (Ruff):**  
   * *Riesgo:* Dejar imports no utilizados (`F401`), variables huérfanas (`F841`) o imports desordenados (`I001`).  
   * *Regla Estricta:* Ejecutar `.venv/bin/ruff check --fix` y `.venv/bin/ruff format` después de cada archivo editado.

---

## 4. Comandos de Verificación para el Agente

El agente debe ejecutar y certificar en verde los siguientes oráculos antes de concluir:

```bash
# 1. Verificación de pureza de linter y formato
.venv/bin/ruff check src/assessment_engine tests/
.venv/bin/ruff format --check src/assessment_engine tests/

# 2. Verificación de inmunidad AST en presentación (Hermetic Gate)
PYTHONPATH=src .venv/bin/pytest -v tests/architecture/test_presentation_hermetic_immunity_ast.py

# 3. Verificación de inmutabilidad de payloads en compilación
PYTHONPATH=src .venv/bin/pytest -v tests/architecture/test_compiler_read_only_contract.py

# 4. Verificación de la suite actuarial y de orquestación
PYTHONPATH=src .venv/bin/pytest -v \
  tests/unit/domain \
  tests/unit/application \
  tests/unit/test_synthesis_orchestrator.py \
  tests/unit/test_tower_payload_hydrator_epistemic.py \
  tests/unit/test_bayesian_fair_copula_engine.py

# 5. Verificación de compilación real de documentos DOCX
PYTHONPATH=src .venv/bin/pytest -v tests/unit/test_tomo_asis_ast_compiler_multi_tenant.py

# 6. Crisol estocástico de 100 empresas
.venv/bin/python scripts/run_universal_crucible_fuzzer.py
```
