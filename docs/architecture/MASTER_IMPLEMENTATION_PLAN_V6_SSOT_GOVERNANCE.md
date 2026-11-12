# PLAN MAESTRO DE IMPLEMENTACIÓN V6: GOBERNANZA ACTUARIAL Y RESOLUCIÓN DEFINITIVA DE SPLIT-BRAIN (SSOT)

**Documento:** `docs/architecture/MASTER_IMPLEMENTATION_PLAN_V6_SSOT_GOVERNANCE.md`  
**Autor:** Dirección de Arquitectura de Sistemas & Engineering Lead  
**Estado:** LISTO PARA EJECUCIÓN SECUENCIAL  
**Aprobado por:** Dictamen Adversario Red Team SOTA (`RT-AUDIT-SOTA-V5`)  
**Alcance:** Unificación absoluta de CMMI v2.0, Escala de Severidad Alométrica Open FAIR ($R^{0.75}$) y erradicación de umbrales hardcodeados en todo el repositorio.

---

## 1. OBJETIVO TÉCNICO

Eliminar de forma irreversible el "Split-Brain" semántico, numérico y financiero del motor de evaluación:
1. **SSOT de Madurez:** Sustituir los 3 archivos en conflicto (`domain/maturity_band.py`, `domain/actuarial/maturity_band.py` y `global_maturity_policy.py`) por un único motor de tipos estricto en `domain/governance/` con partición continua semiabierta $[a_k, a_{k+1})$.
2. **SSOT de Severidad Financiera:** Erradicar las constantes estáticas de `150.000 €` (hydrator) y `25.000 €` (actuarial calculator). Implementar el **Escalado Alométrico Sub-lineal** validado por el Red Team:
   $$\text{Umbral}_k(R) = F_k + \alpha_k \cdot R^{0.75}$$
   garantizando que la severidad de un riesgo sea matemáticamente idéntica a su nivel Open FAIR (*LM 1 a LM 5*).
3. **Inmunidad Numérica:** Sanitizar toda entrada de punto flotante a `Decimal(str(val))` cuantizado para evitar *boundary jitter* por imprecisión binaria IEEE 754.

---

## 2. MAPA DE ARCHIVOS Y SECUENCIA DE EJECUCIÓN

```
[FASE 1: MOTOR CANÓNICO]
  ├── engine_config/governance_scales.json                 (NUEVO: Parámetros declarativos versionados)
  ├── src/assessment_engine/domain/governance/
  │     ├── __init__.py                                   (NUEVO: Exportación pública restringida)
  │     ├── primitives.py                                 (NUEVO: Value Objects inmutables y sanitizador Decimal)
  │     └── scale_engine.py                               (NUEVO: Motor singleton determinista CMMI + Alometría)
  └── tests/unit/test_governance_scale_engine.py          (NUEVO: Batería de 15 pruebas de invariantes matemáticas)

[FASE 2: REFUGIO DE COMPATIBILIDAD Y TIERRA QUEMADA]
  ├── src/assessment_engine/domain/maturity_band.py       (REFACTOR: Reenrutado al motor canónico)
  ├── src/assessment_engine/domain/actuarial/maturity_band.py (DEPRECADO / REDIRIGIDO al canónico)
  └── src/assessment_engine/infrastructure/global_maturity_policy.py (REFACTOR: Solo tokens visuales, 0 fórmulas)

[FASE 3: ERRADICACIÓN DE UMBRALES FINANCIEROS HARDCODEADOS]
  ├── src/assessment_engine/domain/actuarial_calculator.py (REFACTOR: Conexión al motor alométrico)
  └── src/assessment_engine/application/services/tower_payload_hydrator.py (REFACTOR: Eliminado if ale > 150000)

[FASE 4: CAPA DE PRESENTACIÓN Y COMPILADORES AST]
  ├── src/assessment_engine/adapters/compilers/payload_to_ast.py (VERIFICACIÓN: Consumo exclusivo de Value Objects)
  └── src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py (VERIFICACIÓN: Coherencia de cartera)

[FASE 5: CERTIFICACIÓN INTEGRAL]
  ├── Ejecución de pytest completo (unit + architecture)
  └── Recompilación completa de la suite de 11 entregables de Molins (validación en DOCX)
```

---

## 3. ESPECIFICACIÓN DETALLADA PASO A PASO

### FASE 1: Creación del Núcleo de Gobernanza Canónico (`domain/governance/`)

#### Paso 1.1: Archivo de Configuración Declarativo
* **Ruta:** `engine_config/governance_scales.json`
* **Contenido:**
  * Escala de madurez CMMI con intervalos exactos:
    * `INITIAL`: $[0.00, 1.50)$
    * `REPEATABLE`: $[1.50, 2.50)$
    * `DEFINED`: $[2.50, 3.50)$
    * `MANAGED`: $[3.50, 4.50)$
    * `OPTIMIZED`: $[4.50, 5.00]$
  * Coeficientes alométricos de Open FAIR ($\beta = 0.75$) calibrados para que a $1.144\text{ B€}$ (Molins) los cortes coincidan exactamente con la Tabla 8:
    * LM 1: $< 13.000\text{ €}$
    * LM 2: $13.000\text{ €} - 52.000\text{ €}$
    * LM 3: $52.000\text{ €} - 208.000\text{ €}$
    * LM 4: $208.000\text{ €} - 832.000\text{ €}$
    * LM 5: $\ge 832.000\text{ €}$

#### Paso 1.2: Primitivas de Dominio y Value Objects
* **Ruta:** `src/assessment_engine/domain/governance/primitives.py`
* **Clases:**
  * `MaturityBandCode(StrEnum)`: `INITIAL`, `REPEATABLE`, `DEFINED`, `MANAGED`, `OPTIMIZED`.
  * `FinancialSeverityCode(StrEnum)`: `LOW`, `MODERATE`, `ELEVATED`, `HIGH`, `CRITICAL`.
  * `ResolvedMaturity(BaseModel, frozen=True)`:
    * `raw_score: float`
    * `normalized_score: Decimal`
    * `level: int`
    * `band_code: MaturityBandCode`
    * `label_es: str`
    * `ui_semantic_token: str`
  * `ResolvedFinancialRisk(BaseModel, frozen=True)`:
    * `ale_eur: Decimal`
    * `reference_basis_eur: Decimal`
    * `severity: FinancialSeverityCode`
    * `open_fair_lm: str` ("LM1" .. "LM5")
    * `model_provenance: str` (Trazabilidad SR 11-7)
  * `sanitize_to_decimal(val) -> Decimal`: Sanitizador anti-IEEE 754 via `Decimal(str(val))`.

#### Paso 1.3: Motor de Resolución Singleton
* **Ruta:** `src/assessment_engine/domain/governance/scale_engine.py`
* **Métodos Principales:**
  * `GovernanceScaleEngine.resolve_maturity(score: float | Decimal) -> ResolvedMaturity`
  * `GovernanceScaleEngine.resolve_financial_risk(ale_eur: float | Decimal, annual_revenue_eur: float | Decimal | None) -> ResolvedFinancialRisk`
  * Verificación en `__init__` de la invariante formal: $0 = a_0 < a_1 < a_2 < a_3 < a_4 < a_5$.

---

### FASE 2: Pruebas Unitarias Invariantes y de Propiedad

* **Ruta:** `tests/unit/test_governance_scale_engine.py`
* **Cobertura Requerida:**
  1. *Partición Completa:* Probar frontera crítica `1.499`, `1.500`, `2.499`, `2.500`, `3.499`, `3.500`, `4.499`, `4.500`. Cero colisiones, cero limbos.
  2. *Sanitización Float:* `sanitize_to_decimal(1.95)` debe dar exactamente `Decimal('1.9500')`, jamás `1.9499999999999999`.
  3. *Alometría de Escala:* Validar que para Molins ($1.144\text{ B€}$), una pérdida de $35.000\text{ €}$ resuelve a `MODERATE / LM2`, mientras que para una PYME ($2\text{ M€}$) resuelve a `CRITICAL / LM5`.
  4. *Invariante Formal:* Assert de que los umbrales son estrictamente crecientes $\forall R > 0$.

---

### FASE 3: Refactorización y Supresión de Split-Brain ("Tierra Quemada")

#### Paso 3.1: Unificación de `domain/maturity_band.py`
* Redirigir `resolve_maturity_band` para que delegue internamente en `GovernanceScaleEngine.resolve_maturity()`, garantizando compatibilidad retroactiva a los módulos consumidores sin duplicar la lógica.

#### Paso 3.2: Reemplazo en `actuarial_calculator.py`
* En `_resolve_severity(ale: Decimal, ...)`:
  * Eliminar el diccionario estático `{"CRITICAL": 25000, "HIGH": 10000, "ELEVATED": 3000}`.
  * Delegar en `GovernanceScaleEngine.resolve_financial_risk(ale, client_revenue)`.

#### Paso 3.3: Reemplazo en `tower_payload_hydrator.py`
* En la línea 224:
  * Eliminar: `severity = "HIGH" if latent.annual_loss_expectancy > 150000.0 else "MEDIUM"`.
  * Sustituir por la llamada canónica a `GovernanceScaleEngine`.

#### Paso 3.4: Limpieza de `global_maturity_policy.py`
* Purgar las funciones con `score < 2.6` y `score < 3.4`. Convertir el módulo en un consumidor limpio de los tokens de `ResolvedMaturity.ui_semantic_token`.

---

### FASE 4: Verificación en Compiladores y Generación Documental

* Verificar que `payload_to_ast.py` y `in_memory_asis_compiler.py` operan sobre los nuevos Value Objects.
* Recompilar la suite completa de entregables:
  `.venv/bin/python3 scripts/build_full_client_delivery_suite.py --only all`
* Auditar en DOCX que:
  * Portadas muestran el nivel CMMI unificado correcto.
  * Tablas de benchmarking no presentan discrepancias de bandas.
  * Todas las fichas de riesgo y tablas FAIR coinciden en la calificación de severidad (*LM 1 a LM 5*).

---

### FASE 5: Cierre y Certificación Git
* Ejecución de `pytest` sobre toda la suite (deben pasar el 100% de los tests).
* Empaquetado del ZIP final consolidado.
* Commit y push atómico a `origin/main` en GitHub.
