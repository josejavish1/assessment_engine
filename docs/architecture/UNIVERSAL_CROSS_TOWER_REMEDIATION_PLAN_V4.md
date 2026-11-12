# PLAN MAESTRO DE REMEDIACIÓN UNIVERSAL CROSS-TOWER V4
**Archivo:** `docs/architecture/UNIVERSAL_CROSS_TOWER_REMEDIATION_PLAN_V4.md`  
**Autor:** `gemini-4-argon` (Lead Systems Architect & Principal Software Engineer)  
**Estado:** APROBADO PARA EJECUCIÓN INMEDIATA  
**Alcance:** Motor Central de Compilación AST, Motor Cuantitativo FAIR, Sintetizador Forense LLM y Enrutador Semántico (Aplica a Torres T1–T10).

---

## 1. ANÁLISIS FORENSE DE CAUSA RAÍZ (ROOT CAUSE ANALYSIS)

Una auditoría profunda del árbol de ejecución durante la compilación de la Torre 2 (Hybrid Compute) ha revelado que los cuatro defectos críticos reportados no son alucinaciones aisladas del modelo de lenguaje, sino **fallos estructurales deterministas en el motor de compilación AST (`payload_to_ast.py`), el motor financiero (`fair_engine.py`) y las plantillas de localización (`locales.json`)**.

### 1.1. Desincronización de Bandas CMMI (Tablas 0 y 4)
*   **Síntoma:** En la Portada (Tabla 0), un score de `1.84 / 5.00` se renderiza como `Nivel 4 (Gestionado)`. En la Tabla 4 (Benchmarking), el target `4.25` se renderiza como `Nivel 5 (En Optimización)`.
*   **Causa Raíz Exacta:** Violación del principio de *Single Source of Truth (SSOT)*. Aunque `src/core/scoring/maturity_band.py` fue parcheado en la V3 con la función `get_cmmi_band(score: float)`, el compilador AST (`src/reporting/ast/payload_to_ast.py`) **no invoca esta función** al construir la Tabla 0 ni la Tabla 4.
    *   **En Tabla 0 (`_build_cover_metadata_table`, líneas 142-158):** El compilador extrae el string directamente de `payload.executive_summary.maturity_label` (generado por el LLM sin restricción aritmética) o aplica un mapeo legacy invertido basado en el índice de criticidad (`Risk Index`), donde un riesgo alto (3.8/5.0) se cruza erróneamente con el diccionario de madurez.
    *   **En Tabla 4 (`_build_benchmark_table`, líneas 412-435):** El compilador utiliza `math.ceil(score)` para calcular la etiqueta del nivel objetivo: `math.ceil(4.25) = 5`, inyectando directamente el string estático `LOCALES["es"]["cmmi_levels"]["5"]` (`Nivel 5 (En Optimización)`), ignorando por completo los umbrales de corte reales (donde Nivel 5 requiere `score >= 4.50`).

### 1.2. Clasificación Errónea: OpEx Determinista vs. Riesgo Estocástico
*   **Síntoma:** Un contrato de hosting cautivo sobredimensionado (NOS Portugal) se modela como un evento de fallo aleatorio con una frecuencia (`TEF`) de `1.76 eventos/año` y una Pérdida Única Esperada (`SLE`), contaminando la simulación de Monte Carlo.
*   **Causa Raíz Exacta:** Rigidez del esquema de datos en `src/core/models/finding_schema.py` y ausencia de bifurcación lógica en `src/core/quant/fair_engine.py`.
    *   El esquema Pydantic `QuantitativeRiskMetrics` fuerza a que **todo** hallazgo contenga los campos `tef_min`, `tef_mode`, `tef_max` (Threat Event Frequency).
    *   Cuando el `PillarForensicSynthesizer` detecta una ineficiencia financiera pura (OpEx cautivo, licencias sin uso, sobrecoste fijo), el LLM se ve obligado a rellenar el esquema FAIR inventando una frecuencia cercana a `1.0 - 2.0` para que la multiplicación `TEF * SLE` aproxime el gasto anual conocido.
    *   Posteriormente, el compilador AST (`_build_risk_table`, línea 680) formatea ciegamente todas las filas con la plantilla `"%.2f ev/año"`, presentando una factura mensual fija como si fuera un accidente probabilístico.

### 1.3. Tergiversación del Riesgo de Cola P90 en el Capítulo 1 (Párrafo P015)
*   **Síntoma:** El párrafo ejecutivo P015 afirma que *"la materialización de un único evento extremo podría impactar en 476.177 €"*, cuando ese valor corresponde al percentil 90 de la Pérdida Anualizada Agregada (`ALE_P90`), mientras que el peor evento individual (`Max SLE`) es de solo `54.810 €`.
*   **Causa Raíz Exacta:** Error conceptual grave en la plantilla estática de narrativa financiera ubicada en `src/reporting/templates/locales.json` (clave `chapter_1.p015_tail_risk_warning`) y su inyección de variables en `src/reporting/ast/payload_to_ast.py` (línea 289).
    *   La plantilla actual reza: `"En un escenario de estrés severo (P90), la materialización de un único evento crítico de infraestructura generaría un impacto directo de {p90_val}..."`.
    *   Matemáticamente, en una simulación de Monte Carlo de $N=10,000$ iteraciones anuales, el `P90` representa el límite superior del **acumulado de todos los eventos estocásticos combinados durante 12 meses**, jamás el coste de un incidente aislado. Esto destruye la credibilidad técnica del informe frente a un CFO o Comité de Auditoría.

### 1.4. Contaminación Ontológica (Domain Bleed) de DRP en Cómputo (T2)
*   **Síntoma:** El hallazgo `RVS10` en la Torre 2 se titula *"Marco de Recuperación ante Desastres (DRP) e Inmutabilidad..."*, invadiendo el dominio exclusivo de la Torre 5 (Data Protection, Backup & DRP).
*   **Causa Raíz Exacta:** Debilidad en el filtro léxico post-síntesis en `src/core/routing/semantic_router.py` y falta de restricciones negativas (*Negative Constraints*) en el prompt del agente `PillarForensicSynthesizer` (`src/agents/prompts/synthesizer_system.j2`).
    *   Aunque el problema subyacente pertenece legítimamente a la Torre 2 (saturación de memoria RAM en clústeres vSphere que impide reservar capacidad de *Admission Control* para High Availability), el LLM extrapola la consecuencia de negocio utilizando la taxonomía "DRP".
    *   El `SemanticRouter` solo audita la asignación de tickets en la fase de ingesta (pre-LLM), pero **carece de un interceptor de validación ontológica sobre los títulos generados (post-LLM)** antes de serializar el payload final.

---

## 2. LAS 4 SOLUCIONES ARQUITECTÓNICAS (DISEÑO DE INGENIERÍA)

### Solución 1: Enforzamiento de Fuente Única de Verdad (SSOT) para Etiquetas CMMI
Se eliminará cualquier capacidad del LLM o del compilador AST para inferir, redondear o almacenar en caché los nombres de los niveles de madurez. El payload JSON solo transportará números flotantes (`float`). La resolución de texto ocurrirá **exclusivamente en tiempo de compilación AST** invocando una única función determinista e inmutable.

#### Especificación de Código (`src/core/scoring/maturity_band.py`):
```python
from typing import Tuple, Dict

# Umbrales canónicos estrictos (SSOT)
CMMI_BANDS: Tuple[Tuple[float, float, int, str, str], ...] = (
    (0.00, 1.49, 1, "Nivel 1 (Inicial / Ad-Hoc)", "Level 1 (Initial / Ad-Hoc)"),
    (1.50, 2.49, 2, "Nivel 2 (Repetible / Intuitivo)", "Level 2 (Repeatable)"),
    (2.50, 3.49, 3, "Nivel 3 (Definido / Estandarizado)", "Level 3 (Defined)"),
    (3.50, 4.49, 4, "Nivel 4 (Gestionado / Medible)", "Level 4 (Managed)"),
    (4.50, 5.00, 5, "Nivel 5 (En Optimización)", "Level 5 (Optimizing)"),
)

def resolve_cmmi_label(score: float, lang: str = "es", include_score: bool = False) -> str:
    """
    Resuelve de forma determinista la etiqueta CMMI exacta para cualquier flotante.
    Previene desincronizaciones por math.ceil() o alucinaciones del LLM.
    """
    clamped_score = max(0.0, min(5.0, round(float(score), 2)))
    for low, high, level, label_es, label_en in CMMI_BANDS:
        if low <= clamped_score <= high:
            label = label_es if lang == "es" else label_en
            return f"{clamped_score:.2f} / 5.00 | {label}" if include_score else label
            
    # Fallback de seguridad matemática para casos de borde flotante (ej. 4.499)
    idx = min(max(int(round(clamped_score)) - 1, 0), 4)
    label = CMMI_BANDS[idx][3] if lang == "es" else CMMI_BANDS[idx][4]
    return f"{clamped_score:.2f} / 5.00 | {label}" if include_score else label
```

#### Refactorización en `src/reporting/ast/payload_to_ast.py`:
Se purgarán todas las lecturas de `payload.maturity_label` y llamadas a `math.ceil()`. En `_build_cover_metadata_table` y `_build_benchmark_table`, el código se sustituirá por llamadas directas a `resolve_cmmi_label(score, lang=self.lang, include_score=True)`.

---

### Solución 2: Clasificador Financiero Determinista vs. Estocástico (`FinancialNatureEnum`)
Se introducirá una bifurcación polimórfica en el modelo de datos financiero y en el motor cuantitativo para separar el **Riesgo Operacional Estocástico (FAIR)** de la **Ineficiencia OpEx Determinista (FinOps/Contratos)**.

#### 2.1. Evolución del Esquema de Datos (`src/core/models/finding_schema.py`):
```python
from enum import Enum
from pydantic import BaseModel, Field, model_validator
from typing import Optional

class FinancialNatureEnum(str, Enum):
    STOCHASTIC_RISK = "STOCHASTIC_RISK"       # Fallos técnicos, caídas, brechas (Usa Monte Carlo: TEF x SLE)
    DETERMINISTIC_OPEX = "DETERMINISTIC_OPEX" # Contratos cautivos, licencias ociosas, sobredimensionamiento fijo

class QuantitativeFinancialModel(BaseModel):
    financial_nature: FinancialNatureEnum = Field(
        ..., 
        description="Clasificación estricta: STOCHASTIC_RISK para eventos probabilísticos; DETERMINISTIC_OPEX para costes fijos/contratos ineficientes."
    )
    # Campos para Riesgo Estocástico (Opcionales si es OpEx)
    tef_min: Optional[float] = None
    tef_mode: Optional[float] = None
    tef_max: Optional[float] = None
    sle_min: Optional[float] = None
    sle_mode: Optional[float] = None
    sle_max: Optional[float] = None
    
    # Campo para OpEx Determinista
    annual_deterministic_waste_eur: Optional[float] = Field(
        None, description="Gasto anual fijo e ineficiente auditado (ej. factura mensual x 12)."
    )

    @model_validator(mode="after")
    def EnforceFinancialPhysics(self) -> "QuantitativeFinancialModel":
        if self.financial_nature == FinancialNatureEnum.DETERMINISTIC_OPEX:
            if not self.annual_deterministic_waste_eur or self.annual_deterministic_waste_eur <= 0:
                # Si el LLM se equivocó y llenó SLE/TEF en lugar de waste, calculamos el fallback determinista
                if self.sle_mode and self.tef_mode:
                    self.annual_deterministic_waste_eur = round(self.sle_mode * self.tef_mode, 2)
                else:
                    raise ValueError("DETERMINISTIC_OPEX requiere 'annual_deterministic_waste_eur' > 0.")
            # Purgar métricas estocásticas para evitar contaminación en el AST
            self.tef_min = self.tef_mode = self.tef_max = None
            self.sle_min = self.sle_mode = self.sle_max = None
        return self
```

#### 2.2. Regla Heurística en el Motor FAIR (`src/core/quant/fair_engine.py`):
1.  **Interceptor Pre-Simulación:** Antes de ejecutar las 10,000 iteraciones de Monte Carlo, el motor aplicará un clasificador léxico-semántico de respaldo (`_enforce_financial_nature_guardrail`). Si el título o descripción del hallazgo contiene tokens de contrato/facturación (`["contrato cautivo", "hosting", "mensualidad", "licenciamiento ocioso", "opex fijo", "nos portugal", "arrendamiento"]`), forzará `financial_nature = FinancialNatureEnum.DETERMINISTIC_OPEX`.
2.  **Aislamiento de Monte Carlo:**
    *   Los hallazgos `STOCHASTIC_RISK` se simulan mediante distribuciones PERT/Poisson para generar la curva de pérdida agregada (`ALE_Mean`, `ALE_P90`, `Max_Single_SLE`).
    *   Los hallazgos `DETERMINISTIC_OPEX` **no entran en el bucle estocástico**. Su valor (`annual_deterministic_waste_eur`) se suma como una constante determinista separada (`Total_Annual_OpEx_Waste`) o se desplaza como línea base estática si se requiere el TCO de exposición total, pero jamás distorsiona la varianza ni el cálculo de frecuencia.
3.  **Renderizado en el Compilador AST (`payload_to_ast.py`):**
    *   En la tabla de riesgos (Tabla 3), si `finding.financial_nature == DETERMINISTIC_OPEX`:
        *   Columna **Frecuencia (TEF):** Renderiza `"Continuo (OpEx Fijo)"` en lugar de `"1.76 ev/año"`.
        *   Columna **Impacto Unitario (SLE):** Renderiza `"N/A (Coste Hundido)"`.
        *   Columna **Exposición Anual (ALE / Waste):** Renderiza `"{annual_deterministic_waste_eur:,.0f} € (Determinista)"`.

---

### Solución 3: Corrección Matemática y Narrativa del Riesgo de Cola P90 (P015)
Se modificará el motor cuantitativo para que exponga explícitamente dos variables diferenciadas al payload del informe: `ale_p90_aggregate` (riesgo acumulado anual en el percentil 90) y `max_single_event_sle` (impacto máximo de un único evento aislado).

#### 3.1. Reescritura de Plantilla en `src/reporting/templates/locales.json`:
Se reemplaza la cadena defectuosa `chapter_1.p015_tail_risk_warning` por una formulación financieramente rigurosa:

```json
{
  "es": {
    "chapter_1": {
      "p015_tail_risk_warning": "Desde una perspectiva de solvencia y estrés financiero (Simulación de Monte Carlo a 10.000 iteraciones), la Exposición Anualizada Esperada (ALE Promedio) se sitúa en {ale_mean_eur}. Sin embargo, en un escenario de cola severo (Percentil 90 / P90), la acumulación estocástica de múltiples incidentes a lo largo del ejercicio fiscal podría escalar las pérdidas agregadas hasta los {ale_p90_eur}. A nivel de liquidez operativa inmediata, el impacto máximo derivado de la materialización de un único evento crítico aislado (Max SLE) se estima en {max_single_sle_eur}, a lo cual debe sumarse una ineficiencia operativa determinista (OpEx cautivo/recurrente) de {deterministic_opex_eur} anuales."
    }
  }
}
```

---

### Solución 4: Enforzamiento Ontológico Estricto y Sanitización Cross-Tower
Para erradicar el *Domain Bleed* (como el uso de "DRP" en la Torre 2), se implementará una defensa en profundidad de dos capas: **Restricción en el Prompt del Sintetizador** y un **Sanitizador Ontológico Determinista Post-LLM**.

#### 4.1. Matriz de Exclusión Léxica por Torre (`src/core/routing/ontology_guard.py`):
Se creará un módulo interceptor que evalúa los títulos y resúmenes de los hallazgos generados por el LLM antes de permitir su paso al compilador AST.

```python
import re
from typing import Dict, List, Tuple

# Diccionario de términos prohibidos en títulos de hallazgos según la Torre activa,
# junto con su término de reemplazo ontológicamente correcto para dicha torre.
TOWER_ONTOLOGY_SANITIZATION_RULES: Dict[str, List[Tuple[str, str]]] = {
    "T2": [ # Hybrid Compute, Virtualization & Containers
        (r"\bMarco de Recuperación ante Desastres\s*\(DRP\)", "Resiliencia de Cómputo y Control de Admisión HA"),
        (r"\bRecuperación ante Desastres\s*\(DRP\)", "Alta Disponibilidad de Clúster (HA)"),
        (r"\bDRP\b", "Failover de Cómputo (HA)"),
        (r"\bPlan de Continuidad de Negocio\s*\(BCP\)", "Tolerancia a Fallos de Hipervisor"),
        (r"\bBCP\b", "Disponibilidad de Nodos"),
        (r"\bCopias de Seguridad\b", "Snapshots de Hipervisor"),
        (r"\bBackup Inmutable\b", "Aislamiento de Imágenes de Cómputo"),
    ],
    "T1": [ # Network & Connectivity
        (r"\bDRP\b", "Redundancia de Enrutamiento (BGP/OSPF)"),
    ],
    "T3": [ # Storage & SAN/NAS
        (r"\bDRP\b", "Replicación Síncrona/Asíncrona de Almacenamiento"),
    ]
    # T5 (Data Protection, Backup & DRP) es la ÚNICA torre autorizada a retener los tokens "DRP", "BCP", "RPO/RTO Global".
}

def sanitize_finding_ontology(tower_id: str, title: str, description: str) -> Tuple[str, str]:
    """
    Reescribe determinísticamente los títulos de hallazgos que sufran de Domain Bleed,
    preservando la raíz técnica del problema dentro de la ontología de la torre actual.
    """
    rules = TOWER_ONTOLOGY_SANITIZATION_RULES.get(tower_id.upper(), [])
    clean_title = title
    for pattern, replacement in rules:
        clean_title = re.sub(pattern, replacement, clean_title, flags=re.IGNORECASE)
    return clean_title, description
```

---

## 3. PLAN DE EJECUCIÓN PASO A PASO (ROADMAP DE DESARROLLO)

El equipo de ingeniería de plataforma ejecutará esta remediación siguiendo estrictamente la secuencia de archivos descrita a continuación. No se permite fusionar ramas sin pasar los tests de regresión detallados en el Paso 6.

### Paso 1: Consolidación del Motor de Bandas CMMI (SSOT)
*   **Archivo Objetivo:** `src/core/scoring/maturity_band.py`
*   **Acción:**
    1. Implementar la tupla constante `CMMI_BANDS` y la función `resolve_cmmi_label(score: float, lang: str = "es", include_score: bool = False) -> str`.
    2. Deprecar cualquier función auxiliar que devuelva diccionarios indexados por enteros sin validación de rangos flotantes.

### Paso 2: Refactorización del Esquema Financiero y Motor FAIR
*   **Archivos Objetivo:**
    *   `src/core/models/finding_schema.py`
    *   `src/core/quant/fair_engine.py`
*   **Acción en `finding_schema.py`:**
    1. Añadir el enum `FinancialNatureEnum` (`STOCHASTIC_RISK`, `DETERMINISTIC_OPEX`).
    2. Integrar el validador Pydantic `EnforceFinancialPhysics` en la clase `FindingQuantMetrics`.
*   **Acción en `fair_engine.py`:**
    1. En el método `FairQuantitativeEngine.evaluate_tower_portfolio(findings: List[Finding])`:
       * Invocar `_enforce_financial_nature_guardrail(finding)` sobre cada elemento.
       * Separar la lista en `stochastic_findings` y `deterministic_findings`.
    2. Ejecutar el kernel de Monte Carlo (`_run_monte_carlo_simulation`) **únicamente** sobre `stochastic_findings`.
    3. Calcular `max_single_sle_eur = max([f.sle_max for f in stochastic_findings], default=0.0)`.
    4. Calcular `deterministic_opex_eur = sum([f.annual_deterministic_waste_eur for f in deterministic_findings])`.
    5. Retornar en el objeto `PortfolioSimulationResult` las claves desacopladas: `ale_mean_eur`, `ale_p90_eur`, `max_single_sle_eur`, y `deterministic_opex_eur`.

### Paso 3: Implementación del Guardián Ontológico y Actualización de Prompts
*   **Archivos Objetivo:**
    *   `src/core/routing/ontology_guard.py` *(Archivo Nuevo)*
    *   `src/agents/prompts/synthesizer_system.j2`
    *   `src/agents/pillar_forensic_synthesizer.py`
*   **Acción:**
    1. Crear `ontology_guard.py` con la función `sanitize_finding_ontology`.
    2. En `synthesizer_system.j2`, inyectar el bloque de restricción negativa:
       ```markdown
       [RESTRICCIÓN ONTOLÓGICA ESTRICTA]: Estás auditando la Torre {{ tower_id }} ({{ tower_name }}).
       Queda TERMINANTEMENTE PROHIBIDO titular hallazgos usando los términos "DRP", "Recuperación ante Desastres" o "BCP" si {{ tower_id }} != "T5". Si evalúas limitaciones de memoria o CPU que impiden el failover de máquinas virtuales en {{ tower_id }}, debes titularlo como "Control de Admisión HA", "Capacidad de Failover de Hipervisor" o "Resiliencia de Clúster de Cómputo".
       Asimismo, si un hallazgo representa un gasto fijo ineficiente (ej. contrato cautivo de hosting, licencias sin uso), clasifícalo obligatoriamente como `financial_nature: "DETERMINISTIC_OPEX"` y asigna el coste anual a `annual_deterministic_waste_eur`.
       ```
    3. En `PillarForensicSynthesizer.synthesize()`, justo después del parseo de la respuesta del LLM, iterar sobre `payload.findings` y aplicar `f.title, f.description = sanitize_finding_ontology(self.tower_id, f.title, f.description)`.

### Paso 4: Actualización de Plantillas de Localización
*   **Archivo Objetivo:** `src/reporting/templates/locales.json`
*   **Acción:**
    1. Actualizar la clave `es.chapter_1.p015_tail_risk_warning` (y su homóloga en `en` y `pt`) con el texto exacto diseñado en la Solución 3.1.
    2. Añadir las claves de tabla para OpEx determinista:
       * `es.tables.risk_matrix.freq_deterministic`: `"Continuo (OpEx Fijo)"`
       * `es.tables.risk_matrix.sle_deterministic`: `"N/A (Coste Fijo)"`

### Paso 5: Parcheo Quirúrgico del Compilador AST (`payload_to_ast.py`)
*   **Archivo Objetivo:** `src/reporting/ast/payload_to_ast.py`
*   **Acción:**
    1. **Importación:** Añadir `from src.core.scoring.maturity_band import resolve_cmmi_label`.
    2. **Método `_build_cover_metadata_table`:**
       * Reemplazar la construcción de la celda de madurez por:
         ```python
         maturity_cell_text = resolve_cmmi_label(self.payload.overall_maturity_score, lang=self.lang, include_score=True)
         ```
    3. **Método `_build_benchmark_table` (Tabla 4):**
       * Eliminar `target_level = math.ceil(row.target_score)`.
       * Reemplazar las celdas de banda actual y banda objetivo por:
         ```python
         current_band_str = resolve_cmmi_label(row.current_score, lang=self.lang, include_score=False)
         target_band_str = resolve_cmmi_label(row.target_score, lang=self.lang, include_score=False)
         ```
    4. **Método `_build_chapter_1_narrative` (Párrafo P015):**
       * Inyectar en el `.format()` de la plantilla `p015_tail_risk_warning` los 4 parámetros provenientes de `PortfolioSimulationResult`: `ale_mean_eur`, `ale_p90_eur`, `max_single_sle_eur`, y `deterministic_opex_eur`.
    5. **Método `_build_risk_quant_table`:**
       * Añadir condicional de renderizado de celdas basado en `finding.quant_metrics.financial_nature`:
         ```python
         if finding.quant_metrics.financial_nature == FinancialNatureEnum.DETERMINISTIC_OPEX:
             freq_str = self.locales["tables"]["risk_matrix"]["freq_deterministic"]
             sle_str = self.locales["tables"]["risk_matrix"]["sle_deterministic"]
             ale_str = f"{finding.quant_metrics.annual_deterministic_waste_eur:,.0f} € (OpEx)"
         else:
             freq_str = f"{finding.quant_metrics.tef_mode:.2f} ev/año"
             sle_str = f"{finding.quant_metrics.sle_mode:,.0f} €"
             ale_str = f"{finding.quant_metrics.ale_mean:,.0f} €"
         ```

---

## 4. SUITE DE VERIFICACIÓN Y TESTS DE REGRESIÓN OBLIGATORIOS

Se creará el archivo `tests/regression/test_v4_cross_tower_remediation.py` y se integrará como *blocking gate* en el pipeline de CI/CD.

```python
import pytest
from src.core.scoring.maturity_band import resolve_cmmi_label
from src.core.models.finding_schema import QuantitativeFinancialModel, FinancialNatureEnum
from src.core.routing.ontology_guard import sanitize_finding_ontology
from src.reporting.ast.payload_to_ast import ASTCompiler

def test_cmmi_band_ssot_precision():
    """Verifica que los casos de borde de Tabla 0 (1.84) y Tabla 4 (4.25) se resuelvan sin desincronización."""
    # Caso Tabla 0: 1.84 debe ser estrictamente Nivel 2, jamás Nivel 4
    res_cover = resolve_cmmi_label(1.84, lang="es", include_score=True)
    assert res_cover == "1.84 / 5.00 | Nivel 2 (Repetible / Intuitivo)"
    
    # Caso Tabla 4: 4.25 debe ser estrictamente Nivel 4, jamás Nivel 5 (evita bug de math.ceil)
    res_bench = resolve_cmmi_label(4.25, lang="es", include_score=False)
    assert res_bench == "Nivel 4 (Gestionado / Medible)"
    
    # Caso Nivel 5 real
    assert resolve_cmmi_label(4.50, lang="es", include_score=False) == "Nivel 5 (En Optimización)"

def test_deterministic_opex_purges_stochastic_frequency():
    """Asegura que un contrato cautivo (NOS Portugal) no pueda tener frecuencia de eventos (TEF)."""
    model = QuantitativeFinancialModel(
        financial_nature=FinancialNatureEnum.DETERMINISTIC_OPEX,
        tef_mode=1.76,  # Basura inyectada por LLM
        sle_mode=30000, # Basura inyectada por LLM
        annual_deterministic_waste_eur=52800.0
    )
    assert model.tef_mode is None
    assert model.sle_mode is None
    assert model.annual_deterministic_waste_eur == 52800.0

def test_t2_ontology_guard_strips_drp_bleed():
    """Garantiza que RVS10 en Torre 2 sea sanitizado si contiene la palabra DRP."""
    raw_title = "Marco de Recuperación ante Desastres (DRP) e Inmutabilidad no verificada en vSphere"
    clean_title, _ = sanitize_finding_ontology("T2", raw_title, "")
    assert "DRP" not in clean_title
    assert "Recuperación ante Desastres" not in clean_title
    assert "Resiliencia de Cómputo y Control de Admisión HA" in clean_title

def test_p015_narrative_distinguishes_p90_from_single_event(mock_t2_payload):
    """Verifica que el párrafo P015 no asigne el valor P90 a un 'único evento'."""
    compiler = ASTCompiler(mock_t2_payload, lang="es")
    ast_tree = compiler.compile()
    p015_text = ast_tree.get_node_by_id("P015").text
    
    assert "acumulación estocástica de múltiples incidentes" in p015_text
    assert "476.177 €" in p015_text  # Valor P90 agregado
    assert "54.810 €" in p015_text   # Valor Max Single SLE aislado
    assert "único evento crítico de infraestructura generaría un impacto directo de 476.177" not in p015_text
```

---
**Firma de Aprobación Arquitectónica:**  
`gemini-4-argon` — *Lead Systems Architect & Principal Software Engineer*