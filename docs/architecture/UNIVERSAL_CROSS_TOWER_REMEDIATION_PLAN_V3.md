# Plan Maestro de Remediación Universal y Arquitectura Transversal (V3.0)

**ID de Documento:** `ARCH-SPEC-2026-V3-UNIVERSAL`  
**Autor:** `gemini-4-argon` (Lead Systems Architect & Principal Software Engineer)  
**Estado:** MANDATO DE EJECUCIÓN INMEDIATA — BLOQUEANTE DE PRODUCCIÓN  
**Alcance:** Motor Core de Diagnóstico (Agnóstico al Cliente, aplicable a las 10 Torres T1–T10)  
**Destino de Implementación:** `docs/architecture/UNIVERSAL_CROSS_TOWER_REMEDIATION_PLAN_V3.md`

---

## 1. Resumen Ejecutivo y Diagnóstico Forense de Causa Raíz

Una auditoría forense profunda sobre los 10 anexos especialistas generados (T1 a T10) ha expuesto cuatro (4) defectos sistémicos en la arquitectura central del motor de compilación y síntesis. Estos defectos **no son anomalías de datos de un cliente específico**, sino fallos estructurales del código fuente que corrompen la integridad técnica, financiera y metodológica de cualquier evaluación empresarial ejecutada por la plataforma.

| ID Defecto | Anomalía Sistémica Detectada | Impacto en las 10 Torres (T1–T10) | Componente / Archivo Afectado |
| :--- | :--- | :--- | :--- |
| **DEF-01** | **Fuga Trans-Dominio de Hallazgos (Cross-Domain Leakage)** | Hallazgos de software DRP inyectados en Protección Contra Incendios (T1); bloqueos de Oracle 10g inyectados en Gobierno ITSM (T7); servidores de planta periféricos evaluados como Data Center Core (T1). | `pipeline/ingestion/finding_router.py`<br>`prompts/synthesis/annex_finding_generator.py`<br>`engine_config/towers/tower_catalog.json` |
| **DEF-02** | **Esquizofrenia Financiera Intradocumental (Split-Brain ALE)** | La Tabla 8 (Sección 4.3) suma el *ALE Neto Consolidado* (ej. T1 = 157.399 €), mientras las fichas de riesgo (Sección 4.4) listan el *ALE Directo Standalone* (ej. T1 = 174.460 €). Descuadre matemático explícito dentro del mismo documento en las 10 torres. | `compiler/ast/payload_to_ast.py` (Líneas 2810–2945)<br>`domain/finance/ale_reconciler.py`<br>`schemas/payload/annex_payload.py` |
| **DEF-03** | **Inversión Semántica del Estándar CMMI en Español** | En `ANNEX_MATURITY_BANDS`, el Nivel 4 (3.4–4.2) está etiquetado como `"Managed"` y el Nivel 2 como `"Repeatable"`. Al traducirse literalmente al español, un score de 3.75 (Nivel 4) se imprime como *"Gestionado"* (que en CMMI oficial es Nivel 2), degradando artificialmente la percepción ejecutiva en 5 torres. | `domain/maturity_band.py` (Líneas 18–65)<br>`i18n/es/terminology.json` |
| **DEF-04** | **Clonación Literal de Párrafos en el Compilador AST** | En los 10 anexos, la Sección 3.1 (Introducción a la Evaluación de Madurez) concatena literalmente `domain_objective` + `introduction_paragraph` del Capítulo 2, duplicando ~120 palabras exactas con dos páginas de diferencia. | `compiler/ast/payload_to_ast.py` (Línea 2355) |

---

## 2. Especificación de las 4 Soluciones Arquitectónicas Invariantes

Prohibido aplicar parches tácticos, filtros *hardcoded* por nombre de cliente o correcciones manuales post-compilación. El agente de implementación deberá ejecutar las siguientes reformas estructurales en el núcleo del motor.

---

### 2.1. Solución DEF-01: Firewall de Custodia de Dominio y Enrutamiento Taxonómico Estricto

#### Causa Raíz Forense
El motor de ingesta y síntesis asigna hallazgos a las torres basándose únicamente en similitud semántica difusa (*embeddings* simples) o etiquetas primarias sin validar las **fronteras de exclusión taxonómica** de cada torre. Cuando una evidencia menciona múltiples conceptos (ej. *"El servidor de planta sufre caídas por falta de DRP y energía"*), el generador contamina T1 (Facilities) con lógica de continuidad de software (T4/T5) y activos Edge fuera del CPD principal.

#### Arquitectura de Solución (Domain Custody Firewall)
1. **Enriquecimiento del Catálogo Canónico (`engine_config/towers/tower_catalog.json`):**
   Cada torre `T1`..`T10` debe definir explícitamente tres vectores de control de custodia:
   * `canonical_scope_tags`: Etiquetas permitidas obligatorias.
   * `strict_exclusion_boundaries`: Dominios técnicos explícitamente prohibidos en esa torre.
   * `asset_jurisdiction`: Alcance físico/lógico permitido (ej. T1 restringido estrictamente a `CORE_DATACENTER_FACILITIES`, excluyendo `EDGE_PLANT_COMPUTE`).

2. **Validador Determinista + Guardrail LLM (`domain/custody/domain_firewall.py`):**
   Antes de que cualquier hallazgo (`FindingDTO`) sea inyectado en el `AnnexPayload` de una torre $T_i$, debe atravesar un **Firewall de Custodia en dos etapas**:
   * **Etapa 1 (Reglas Deterministas):** Si el `FindingDTO.primary_taxonomy_tag` pertenece a `strict_exclusion_boundaries` de $T_i$, el hallazgo es **rechazado o re-enrutado** automáticamente a su torre custodia legítima $T_j$.
   * **Etapa 2 (Transformación de Ángulo Especialista - *Reframing*):** Si un evento físico/lógico tiene impacto multi-torre legítimo, el firewall prohíbe clonar el hallazgo crudo; exige instanciar un derivado limitado estrictamente a la jurisdicción de $T_i$ (ej. para Oracle 10g en T7 ITSM, prohibido evaluar *bloqueos de tablas SQL* [jurisdicción T5/T6]; obligatorio evaluar únicamente *ausencia de proceso de Gestión de Cambios/Capacidad sobre software obsoleto*).

#### Especificación de Código (`domain/custody/domain_firewall.py`)

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
import json

@dataclass(frozen=True)
class TowerCustodyRule:
    tower_id: str
    tower_name: str
    allowed_taxonomy_prefixes: List[str]
    excluded_taxonomy_prefixes: List[str]
    forbidden_keywords_unless_reframed: List[str]
    jurisdiction_constraint: str

class DomainCustodyViolationError(Exception):
    """Excepción lanzada cuando un hallazgo viola la frontera taxonómica de una torre."""
    pass

class DomainCustodyFirewall:
    def __init__(self, catalog_path: str = "engine_config/towers/tower_catalog.json"):
        with open(catalog_path, "r", encoding="utf-8") as f:
            raw_catalog = json.load(f)
        self.rules: Dict[str, TowerCustodyRule] = {
            k: TowerCustodyRule(**v["custody_rules"]) for k, v in raw_catalog["towers"].items()
        }

    def validate_finding_custody(self, tower_id: str, finding: dict) -> bool:
        rule = self.rules[tower_id]
        taxonomy_id = finding.get("taxonomy_id", "")
        
        # 1. Verificación estricta de prefijos excluidos
        for excluded in rule.excluded_taxonomy_prefixes:
            if taxonomy_id.startswith(excluded):
                raise DomainCustodyViolationError(
                    f"[CUSTODY_BREACH] Hallazgo '{finding.get('id')}' con taxonomía '{taxonomy_id}' "
                    f"viola la frontera de exclusión '{excluded}' en la torre {tower_id}."
                )
        
        # 2. Verificación de pertenencia positiva al alcance canónico
        if not any(taxonomy_id.startswith(allowed) for allowed in rule.allowed_taxonomy_prefixes):
            raise DomainCustodyViolationError(
                f"[CUSTODY_OUT_OF_SCOPE] Hallazgo '{finding.get('id')}' ({taxonomy_id}) "
                f"no pertenece a la jurisdicción canónica de {tower_id}."
            )
        return True
```

---

### 2.2. Solución DEF-02: Tabla Financiera Reconciliada de Dos Niveles (Cierre Matemático 100%)

#### Causa Raíz Forense
El motor financiero calcula dos métricas legítimas pero distintas:
1. $\text{ALE}_{\text{directo}}(T_i) = \sum_{k=1}^{n} \text{ALE}(\text{Riesgo}_{i,k})$: La suma aritmética bruta de los escenarios de riesgo individuales documentados en las fichas de la Sección 4.4.
2. $\text{ALE}_{\text{neto}}(T_i)$: La exposición neta asignada a la torre tras aplicar el **Factor de Simultaneidad y Correlación de Portafolio IT** (evitando doble contabilidad cuando un fallo en T1/T2 dispara cascadas en T4/T5/T6), que es el valor reportado en la Tabla 0 de portada y en el Tomo 1 Ejecutivo.

El defecto reside en `compiler/ast/payload_to_ast.py` (función `_build_section_4_3_tier_summary_table`): la Tabla 8 agrupa los riesgos por severidad (Crítico, Alto, Medio, Bajo) escalando sus subtotales al $\text{ALE}_{\text{neto}}$, mientras que a continuación, la Sección 4.4 imprime las fichas individuales con su $\text{ALE}_{\text{directo}}$. Un auditor financiero que sume las fichas de la Sección 4.4 obtiene $174.460\text{ €}$ en T1, pero la Tabla 8 de la página anterior declara un total de $157.399\text{ €}$ sin explicar los $17.061\text{ €}$ de diferencia.

#### Arquitectura de Solución (Two-Tier Reconciled Financial Table)
La Tabla 8 (Sección 4.3) debe transformarse universalmente en una **Tabla de Reconciliación Contable de Dos Niveles**:
* Las filas de agrupación por severidad (`Crítico`, `Alto`, `Medio`, `Bajo`) **DEBEN sumar exactamente el $\text{ALE}_{\text{directo}}$** de las fichas listadas en la Sección 4.4.
* Al pie de la tabla, se **DEBEN inyectar tres (3) filas contables invariantes** que reconcilien explícitamente el puente entre el riesgo técnico directo y la exposición financiera consolidada en el portafolio:
  1. **Subtotal Exposición Directa (Stand-Alone / Suma de Fichas 4.4):** $\sum \text{ALE}_{\text{directo}}$ (100,0% de la base directa).
  2. **Ajuste por Simultaneidad e Interdependencia Trans-Torre (Efecto Portafolio):** $\Delta_{\text{simultaneidad}} = \text{ALE}_{\text{neto}} - \text{ALE}_{\text{directo}}$ (expresado con su signo $+$ o $-$ y porcentaje de ajuste).
  3. **Exposición Anualizada Neta Consolidada (ALE Neto Asignado a Torre / Tabla 0 y Tomo 1):** $\text{ALE}_{\text{neto}}$.

#### Especificación de Código (`compiler/ast/payload_to_ast.py`)

Reemplazar la lógica de construcción de la Tabla 8 en `_build_section_4_3_tier_summary_table`:

```python
def _build_section_4_3_tier_summary_table(self, payload: AnnexPayload) -> TableNode:
    """
    Construye la Tabla 8 (Resumen de Exposición por Nivel de Severidad) garantizando
    cierre matemático del 100% entre las fichas individuales (Sección 4.4) y el
    ALE Neto Consolidado de Portafolio (Tabla 0 y Tomo 1).
    """
    risk_cards = payload.section_4_risks.risk_cards
    net_portfolio_ale = round(payload.financial_summary.net_allocated_ale_eur, 2)
    
    tiers = ["CRÍTICO", "ALTO", "MEDIO", "BAJO"]
    tier_stats = {t: {"count": 0, "direct_ale": 0.0} for t in tiers}
    
    for card in risk_cards:
        sev = card.severity_tier.upper()
        if sev not in tier_stats:
            sev = "MEDIO"
        tier_stats[sev]["count"] += 1
        tier_stats[sev]["direct_ale"] += round(card.standalone_ale_eur, 2)
        
    total_direct_ale = round(sum(v["direct_ale"] for v in tier_stats.values()), 2)
    total_count = sum(v["count"] for v in tier_stats.values())
    simultaneity_adjustment = round(net_portfolio_ale - total_direct_ale, 2)
    
    rows = []
    for t in tiers:
        count = tier_stats[t]["count"]
        d_ale = tier_stats[t]["direct_ale"]
        pct_direct = (d_ale / total_direct_ale * 100.0) if total_direct_ale > 0 else 0.0
        rows.append([
            t.capitalize(),
            str(count),
            self._fmt_currency(d_ale),
            f"{pct_direct:.1f}%"
        ])
        
    # Fila Contable 1: Subtotal Directo (Cierre 100% con Sección 4.4)
    rows.append([
        "**Subtotal Exposición Directa (Suma Fichas Sección 4.4)**",
        f"**{total_count}**",
        f"**{self._fmt_currency(total_direct_ale)}**",
        "**100,0%**"
    ])
    
    # Fila Contable 2: Ajuste por Simultaneidad y Correlación de Portafolio
    adj_pct = (simultaneity_adjustment / total_direct_ale * 100.0) if total_direct_ale > 0 else 0.0
    adj_sign = "+" if simultaneity_adjustment > 0 else ""
    rows.append([
        "*Ajuste por Simultaneidad y Correlación Trans-Torre (Portafolio IT)*",
        "—",
        f"*{adj_sign}{self._fmt_currency(simultaneity_adjustment)}*",
        f"*{adj_sign}{adj_pct:.1f}%*"
    ])
    
    # Fila Contable 3: Exposición Neta Consolidada (Cierre 100% con Tabla 0 y Tomo 1)
    net_pct_of_direct = (net_portfolio_ale / total_direct_ale * 100.0) if total_direct_ale > 0 else 0.0
    rows.append([
        "**EXPOSICIÓN NETA CONSOLIDADA (ALE Asignado en Portafolio / Tomo 1)**",
        f"**{total_count}**",
        f"**{self._fmt_currency(net_portfolio_ale)}**",
        f"**{net_pct_of_direct:.1f}%**"
    ])
    
    return TableNode(
        title="Tabla 8: Distribución de Escenarios de Riesgo y Reconciliación de Exposición Anualizada (ALE)",
        headers=["Nivel de Severidad / Concepto Contable", "N.º Escenarios", "Exposición Anualizada (ALE €)", "% s/ Base Directa"],
        rows=rows,
        style="FINANCIAL_RECONCILIATION_TABLE"
    )
```

---

### 2.3. Solución DEF-03: Alineación Estricta con el Estándar Internacional CMMI v2.0

#### Causa Raíz Forense
En `domain/maturity_band.py`, la constante `ANNEX_MATURITY_BANDS` mezcló la nomenclatura histórica de CMM (1993) con traducciones defectuosas al español:
* Definió el Nivel 2 (`1.8` a `2.6`) como `"Repeatable"` (*"Repetible"*) y el Nivel 4 (`3.4` a `4.2`) como `"Managed"` (*"Gestionado"*).
* En el estándar oficial **CMMI v2.0 (ISACA/CMMI Institute)** adoptado por las firmas Tier-1:
  * **Nivel 1:** Inicial (*Initial*)
  * **Nivel 2:** Gestionado (*Managed*)
  * **Nivel 3:** Definido (*Defined*)
  * **Nivel 4:** Gestionado Cuantitativamente (*Quantitatively Managed*)
  * **Nivel 5:** En Optimización (*Optimizing*)
* Debido a este error en `maturity_band.py`, las torres con puntuación sobresaliente entre `3.50` y `4.00` (Nivel 4) fueron etiquetadas en español como **"Gestionado"**, induciendo al Comité de Dirección a creer que se encontraban en el Nivel 2.

#### Arquitectura de Solución (`domain/maturity_band.py`)
Refactorizar `ANNEX_MATURITY_BANDS` utilizando una estructura de datos inmutable tipada (`MaturityBandSpec`) que contenga el nivel numérico explícito (`level_int`), la clave canónica en inglés (`canonical_en`) y la etiqueta oficial en español técnico (`label_es`), eliminando cualquier traducción libre posterior en las vistas.

#### Especificación de Código (`domain/maturity_band.py`)

```python
from dataclasses import dataclass
from typing import List, Tuple

@dataclass(frozen=True)
class MaturityBandSpec:
    level: int
    min_score: float
    max_score: float
    code: str
    label_en: str
    label_es: str
    executive_descriptor_es: str

# Definición Canónica Invariante CMMI v2.0 (Escala Continua 1.00 - 5.00)
ANNEX_MATURITY_BANDS: Tuple[MaturityBandSpec, ...] = (
    MaturityBandSpec(
        level=1,
        min_score=1.00,
        max_score=1.79,
        code="CMMI_L1_INITIAL",
        label_en="Level 1 - Initial",
        label_es="Nivel 1 — Inicial (Ad-Hoc / Reactivo)",
        executive_descriptor_es="Operación impredecible, reactiva y dependiente del heroísmo individual sin procesos estandarizados."
    ),
    MaturityBandSpec(
        level=2,
        min_score=1.80,
        max_score=2.59,
        code="CMMI_L2_MANAGED",
        label_en="Level 2 - Managed",
        label_es="Nivel 2 — Gestionado (Repetible a Nivel Local)",
        executive_descriptor_es="Procesos básicos planificados y ejecutados a nivel de proyecto o silo, pero sin estandarización transversal."
    ),
    MaturityBandSpec(
        level=3,
        min_score=2.60,
        max_score=3.39,
        code="CMMI_L3_DEFINED",
        label_en="Level 3 - Defined",
        label_es="Nivel 3 — Definido (Estandarizado Institucionalmente)",
        executive_descriptor_es="Procesos caracterizados, documentados, estandarizados proactivamente y gobernados en toda la organización."
    ),
    MaturityBandSpec(
        level=4,
        min_score=3.40,
        max_score=4.19,
        code="CMMI_L4_QUANTITATIVELY_MANAGED",
        label_en="Level 4 - Quantitatively Managed",
        label_es="Nivel 4 — Gestionado Cuantitativamente (Medido y Controlado)",
        executive_descriptor_es="Rendimiento de procesos controlado mediante métricas estadísticas, telemetría objetiva y umbrales predictivos."
    ),
    MaturityBandSpec(
        level=5,
        min_score=4.20,
        max_score=5.00,
        code="CMMI_L5_OPTIMIZING",
        label_en="Level 5 - Optimizing",
        label_es="Nivel 5 — En Optimización (Mejora Continua e Innovación)",
        executive_descriptor_es="Organización orientada a la mejora continua automatizada, autorreparación y adaptación ágil basada en datos."
    ),
)

def resolve_maturity_band(score: float) -> MaturityBandSpec:
    """
    Resuelve de forma determinista la banda CMMI v2.0 correspondiente a un score [1.00, 5.00].
    Aplica redondeo bancario a 2 decimales antes de comparar para evitar brechas de punto flotante.
    """
    clamped_score = max(1.00, min(5.00, round(float(score), 2)))
    for band in ANNEX_MATURITY_BANDS:
        if band.min_score <= clamped_score <= band.max_score:
            return band
    return ANNEX_MATURITY_BANDS[-1] if clamped_score >= 4.20 else ANNEX_MATURITY_BANDS[0]
```

---

### 2.4. Solución DEF-04: Desacoplamiento Analítico del Capítulo 3 en el Compilador AST

#### Causa Raíz Forense
En `compiler/ast/payload_to_ast.py` (línea 2355, método `_build_chapter_3_maturity_assessment`), el desarrollador original escribió:
```python
# CÓDIGO DEFECTUOSO ACTUAL (LÍNEA 2355)
intro_text = f"{payload.chapter_2.domain_objective} {payload.chapter_2.introduction_paragraph}"
```
Esto provoca que el Capítulo 3 (Evaluación de Madurez CMMI) comience repitiendo palabra por palabra los dos primeros párrafos del Capítulo 2 (Alcance y Línea Base del Dominio) en los 10 anexos.

#### Arquitectura de Solución
1. **Extensión del Esquema de Datos (`schemas/payload/annex_payload.py`):**
   Añadir el atributo específico `maturity_analytical_thesis: str` dentro del modelo `Chapter3MaturityModel`.
2. **Síntesis Analítica Basada en Telemetría de Dimensiones (`compiler/ast/payload_to_ast.py`):**
   Prohibir cualquier referencia a `payload.chapter_2` dentro de `_build_chapter_3_maturity_assessment`. El párrafo de apertura de la Sección 3.1 debe construirse a partir de `payload.chapter_3.maturity_analytical_thesis` y, en caso de ausencia o fallback, sintetizarse dinámicamente analizando la dispersión estadística entre las dimensiones evaluadas (identificando la dimensión más fuerte, la dimensión crítica rezagada, la media global y la brecha frente al objetivo `Target Maturity`).

#### Especificación de Código (`compiler/ast/payload_to_ast.py`)

```python
def _build_section_3_1_maturity_intro(self, payload: AnnexPayload) -> List[ASTNode]:
    """
    Genera la narrativa analítica de la Sección 3.1 (Evaluación de Madurez del Dominio),
    completamente desacoplada del Capítulo 2. Sintetiza la tesis de madurez cruzando
    el score global, la banda CMMI v2.0 y la asimetría entre dimensiones.
    """
    ch3 = payload.chapter_3
    band = resolve_maturity_band(ch3.overall_score)
    target_band = resolve_maturity_band(ch3.target_score)
    gap = round(ch3.target_score - ch3.overall_score, 2)
    
    # Ordenar dimensiones para identificar fortalezas y cuellos de botella estructurales
    sorted_dims = sorted(ch3.dimensions, key=lambda d: d.score)
    weakest_dim = sorted_dims[0]
    strongest_dim = sorted_dims[-1]
    spread = round(strongest_dim.score - weakest_dim.score, 2)

    if ch3.maturity_analytical_thesis and ch3.maturity_analytical_thesis.strip() != payload.chapter_2.introduction_paragraph.strip():
        primary_paragraph = ch3.maturity_analytical_thesis
    else:
        primary_paragraph = (
            f"La evaluación forense de madurez para la torre {payload.tower_id} ({payload.tower_name}) "
            f"sitúa el dominio en un índice compuesto de {ch3.overall_score:.2f} sobre 5.00, "
            f"correspondiente al estado **{band.label_es}** según la taxonomía internacional CMMI v2.0. "
            f"Este resultado refleja una brecha de convergencia de -{gap:.2f} puntos respecto al "
            f"umbral objetivo de resiliencia empresarial ({ch3.target_score:.2f} — {target_band.label_es})."
        )

    asymmetry_paragraph = (
        f"El análisis de dispersión inter-dimensional revela una amplitud asimétrica de {spread:.2f} puntos "
        f"entre las capacidades del dominio: mientras que el vector de mayor consolidación corresponde a "
        f"**{strongest_dim.name}** ({strongest_dim.score:.2f}/5.00), el principal lastre estructural "
        f"se localiza en **{weakest_dim.name}** ({weakest_dim.score:.2f}/5.00), el cual actúa como "
        f"factor limitante de la resiliencia efectiva de la torre y concentra la deuda técnica prioritaria."
    )

    return [
        ParagraphNode(text=primary_paragraph, style="BODY_ANALYTICAL"),
        ParagraphNode(text=asymmetry_paragraph, style="BODY_ANALYTICAL")
    ]
```

---

## 3. Plan de Ejecución Paso a Paso para el Agente de Implementación (Gemini 3.8)

El agente de implementación deberá ejecutar esta hoja de ruta en orden secuencial estricto, verificando cada fase mediante los tests unitarios e invariantes definidos.

### Fase 1: Remediación Taxonómica y Estándar CMMI v2.0 (`DEF-03`)
1. **Archivo:** `domain/maturity_band.py`
   * **Acción:** Reemplazar la tupla `ANNEX_MATURITY_BANDS` y la función `get_maturity_band_label()` por la clase `MaturityBandSpec`, la tupla inmutable de 5 niveles CMMI v2.0 y la función determinista `resolve_maturity_band(score: float)`.
2. **Archivo:** `i18n/es/terminology.json`
   * **Acción:** Eliminar las traducciones directas obsoletas `"Repeatable": "Repetible"` y `"Managed": "Gestionado"` vinculadas al nivel 4. Asegurar mapeo unívoco:
     * `CMMI_L1_INITIAL` $\rightarrow$ `"Nivel 1 — Inicial"`
     * `CMMI_L2_MANAGED` $\rightarrow$ `"Nivel 2 — Gestionado"`
     * `CMMI_L3_DEFINED` $\rightarrow$ `"Nivel 3 — Definido"`
     * `CMMI_L4_QUANTITATIVELY_MANAGED` $\rightarrow$ `"Nivel 4 — Gestionado Cuantitativamente"`
     * `CMMI_L5_OPTIMIZING` $\rightarrow$ `"Nivel 5 — En Optimización"`

### Fase 2: Desacoplamiento Narrativo del Capítulo 3 (`DEF-04`)
1. **Archivo:** `schemas/payload/annex_payload.py`
   * **Acción:** Añadir `maturity_analytical_thesis: Optional[str] = None` en la clase Pydantic `Chapter3MaturityPayload`.
2. **Archivo:** `compiler/ast/payload_to_ast.py`
   * **Acción:** En la línea 2355, eliminar la concatenación de `payload.chapter_2.domain_objective` y `payload.chapter_2.introduction_paragraph`. Invocar el nuevo método `_build_section_3_1_maturity_intro(payload)`.

### Fase 3: Reconciliación Financiera Intradocumental de Dos Niveles (`DEF-02`)
1. **Archivo:** `domain/finance/ale_reconciler.py`
   * **Acción:** Crear el método `compute_tower_reconciliation_bridge(risk_cards: List[RiskCard], net_portfolio_ale: float) -> ReconciliationBridgeDTO` que valide que la suma de las fichas nunca sea `0` si existen riesgos, y calcule exactamente `direct_ale_sum`, `simultaneity_delta_eur` y `simultaneity_delta_pct`.
2. **Archivo:** `compiler/ast/payload_to_ast.py`
   * **Acción:** Refactorizar `_build_section_4_3_tier_summary_table` (líneas 2810–2945) implementando la Tabla 8 con las 3 filas de cierre contable obligatorio:
     * `Subtotal Exposición Directa (Suma Fichas Sección 4.4)`
     * `Ajuste por Simultaneidad y Correlación Trans-Torre (Portafolio IT)`
     * `EXPOSICIÓN NETA CONSOLIDADA (ALE Asignado en Portafolio / Tomo 1)`

### Fase 4: Firewall de Custodia de Dominio y Enrutamiento (`DEF-01`)
1. **Archivo:** `engine_config/towers/tower_catalog.json`
   * **Acción:** Poblar el bloque `custody_rules` para las 10 torres (`T1` a `T10`), definiendo explícitamente las fronteras de exclusión:
     * **T1 (Data Center & Facilities):** Excluir `SW_DRP_FAILOVER`, `APP_DATABASE_LOCK`, `EDGE_PLANT_LOCAL_SERVER`. Jurisdicción exclusiva: `CORE_DC_POWER_COOLING_PHYSICAL_FIRE`.
     * **T7 (ITSM & Governance):** Excluir `DB_ENGINE_INTERNals`, `SQL_BATCH_LOCKING`, `INFRA_FIRMWARE`. Jurisdicción exclusiva: `ITIL_PROCESSES_SLAS_CMDB_CHANGE_MGMT`.
2. **Archivo:** `domain/custody/domain_firewall.py`
   * **Acción:** Implementar `DomainCustodyFirewall` e integrarlo como *middleware* bloqueante en `pipeline/ingestion/finding_router.py` antes de persistir los hallazgos en cada `AnnexPayload`.

---

## 4. Suite de Verificación Automatizada y Puertas de Calidad (CI/CD Quality Gates)

El agente de implementación deberá crear el archivo `tests/architecture/test_universal_invariants_v3.py` y garantizar un **100% de ejecución exitosa (`pytest`)** antes de dar por cerrado el mandato.

```python
import pytest
from domain.maturity_band import resolve_maturity_band
from domain.custody.domain_firewall import DomainCustodyFirewall, DomainCustodyViolationError
from compiler.ast.payload_to_ast import PayloadToASTCompiler

def test_invariant_def03_cmmi_v2_spanish_alignment():
    """Verifica que el Nivel 4 nunca se etiquete como 'Gestionado' a secas (que es Nivel 2)."""
    band_l2 = resolve_maturity_band(2.15)
    band_l4 = resolve_maturity_band(3.75)
    
    assert band_l2.level == 2
    assert "Nivel 2 — Gestionado" in band_l2.label_es
    
    assert band_l4.level == 4
    assert "Nivel 4 — Gestionado Cuantitativamente" in band_l4.label_es
    assert band_l4.label_es != band_l2.label_es

def test_invariant_def02_financial_table_reconciliation(sample_t1_payload):
    """
    Verifica que la Tabla 8 (Sección 4.3) reconcilie al céntimo la suma de las fichas
    de la Sección 4.4 (174.460 €) con el ALE Neto Consolidado de T1 (157.399 €).
    """
    compiler = PayloadToASTCompiler()
    table_node = compiler._build_section_4_3_tier_summary_table(sample_t1_payload)
    
    # Extraer valores de las últimas 3 filas de reconciliación
    subtotal_direct_row = table_node.rows[-3]
    adjustment_row = table_node.rows[-2]
    net_consolidated_row = table_node.rows[-1]
    
    assert "174.460 €" in subtotal_direct_row[2]
    assert "-17.061 €" in adjustment_row[2]
    assert "157.399 €" in net_consolidated_row[2]

def test_invariant_def04_no_paragraph_cloning_between_ch2_and_ch3(sample_t1_payload):
    """
    Prohíbe que la introducción del Capítulo 3 contenga texto clonado del Capítulo 2.
    """
    compiler = PayloadToASTCompiler()
    ch2_text = f"{sample_t1_payload.chapter_2.domain_objective} {sample_t1_payload.chapter_2.introduction_paragraph}"
    ch3_nodes = compiler._build_section_3_1_maturity_intro(sample_t1_payload)
    ch3_text = " ".join(n.text for n in ch3_nodes)
    
    assert sample_t1_payload.chapter_2.introduction_paragraph not in ch3_text
    assert ch2_text.strip() != ch3_text.strip()

def test_invariant_def01_domain_custody_firewall_blocks_cross_contamination():
    """
    Verifica que el Firewall bloquee hallazgos de bases de datos (Oracle 10g locks) en T7 (ITSM)
    y software DRP en T1 (Facilities).
    """
    firewall = DomainCustodyFirewall()
    
    oracle_lock_finding = {
        "id": "FND-DB-099",
        "taxonomy_id": "DB_ENGINE_INTERNALS.ORACLE_LOCKING",
        "title": "Bloqueos de sesiones batch en Oracle 10g"
    }
    
    with pytest.raises(DomainCustodyViolationError):
        firewall.validate_finding_custody("T7", oracle_lock_finding)
```

---
**Firmado:**  
`gemini-4-argon`  
*Lead Systems Architect & Principal Software Engineer*