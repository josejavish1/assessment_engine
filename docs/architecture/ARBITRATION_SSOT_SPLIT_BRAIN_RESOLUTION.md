# BRIEFING DE ARQUITECTURA DE SISTEMAS: Erradicación de Split-Brain en Motores de Evaluación y Cálculo Actuarial

**De:** `gemini-4-argon` (Principal Enterprise Architect & Staff Infrastructure Engineer)  
**Para:** Comité de Ingeniería Principal / Arquitectura de Dominio  
**Asunto:** Resolución Definitiva de Divergencia Semántica y Numérica en Escalas de Madurez y Severidad Financiera  
**Estado:** CRÍTICO / BLOQUEANTE DE AUDITORÍA  

---

## 1. DIAGNÓSTICO EJECUTIVO: La Patología del "Split-Brain" Semántico

El sistema actual exhibe una vulnerabilidad arquitectónica clásica de sistemas legados en crecimiento: **Primitive Obsession** combinada con **Leakage de Lógica de Dominio hacia Capas de Infraestructura y Presentación**. 

Tener múltiples definiciones de umbrales (`1.5` vs `1.59`, `< 2.6`) y severidades financieras estáticas (`150,000 EUR` vs `25,000 EUR` vs escalas dinámicas Open FAIR) no es simplemente deuda técnica; es un **defecto de integridad referencial del modelo matemático**. En entornos regulados o de misión crítica (como Stripe Core o Palantir Foundry), que un mismo *Annualized Loss Expectancy (ALE)* de `30,000 EUR` sea clasificado simultáneamente como `CRITICAL` en el motor actuarial, `MEDIUM` en el hidratador de payloads, y `LM 2 (Bajo)` en la escala Open FAIR de un cliente Enterprise, invalida la trazabilidad determinista del motor.

Para erradicar este problema de raíz, evaluamos las tres estrategias propuestas bajo el prisma de ingeniería Tier-1.

---

## 2. ANÁLISIS DE OPCIONES ARQUITECTÓNICAS

### Opción A: Pure Declarative Configuration (Zero-Code SSOT)
Externalizar todos los intervalos, etiquetas, colores y curvas actuariales a un archivo declarativo (`engine_config/governance_scales.json`), compilado en un registro inmutable en tiempo de arranque.

*   **Pros:**
    *   **Auditabilidad Externa:** Permite que equipos de Riesgo/Actuaría auditen las reglas sin leer código Python.
    *   **Versionado de Políticas:** Facilita atar una evaluación histórica a un hash SHA-256 específico del archivo de configuración (crucial para reproducibilidad temporal).
    *   **Interoperabilidad:** El mismo JSON puede ser consumido por el Backend (Python) y el Frontend (TypeScript/React) para renderizar leyendas sin duplicar lógica.
*   **Contras:**
    *   **Pérdida de Seguridad de Tipos Estática (Static Type Safety):** Si el código hace referencias por `string` (ej. `config.get_band("HIGH")`), se pierde la validación en tiempo de compilación/linting (Mypy/Pyright).
    *   **Riesgo de "Configuration Drift":** Sin un esquema de validación estricto en el arranque, un error de sintaxis o un hueco en los intervalos (`[1.0, 2.5]` y `[2.6, 3.5]`) rompe el sistema en *runtime*.
*   **Blast Radius de Migración:** **Medio-Alto.** Requiere introducir un componente de carga de infraestructura (Bootloader) y refactorizar funciones puras para que reciban el contexto de configuración (Inyección de Dependencias).
*   **Modos de Fallo y Edge Cases:** Huecos matemáticos en intervalos declarados por humanos (ej. ¿qué pasa con `2.55` si un rango termina en `2.5` y el otro empieza en `2.6`?), errores de redondeo de punto flotante (IEEE 754) al parsear JSON.

---

### Opción B: Domain-Driven Core Primitive (Code-as-SSOT)
Consolidar toda la lógica en un único módulo de dominio (`domain/governance/primitives.py`) usando `Pydantic` / `dataclasses(frozen=True)`, tipos estrictos (`NewType`, `Enum`) y eliminando físicamente los módulos competidores.

*   **Pros:**
    *   **Garantía de Compilación (Zero-Runtime Surprise):** El uso de `Enum` y `TypeGuards` garantiza que ningún desarrollador pueda instanciar un puntaje de madurez o severidad fuera de los invariantes del dominio.
    *   **Encapsulamiento Total:** El valor numérico viaja *junto* con su semántica resuelta (Value Object). El hidratador de payloads ya no evalúa `if ale > 150000`; simplemente pide `ale_evaluation.severity_label`.
    *   **Simplicidad Operacional:** No hay dependencias de archivos externos ni latencia de I/O en la inicialización de tests unitarios.
*   **Contras:**
    *   **Rigidez de Despliegue:** Cualquier ajuste fino en un umbral o etiqueta requiere un ciclo completo de CI/CD y despliegue de código.
    *   **Insuficiente por sí sola para el Problema Financiero:** Consolidar `150,000` y `25,000` en un solo archivo de código no resuelve el hecho de que usar constantes estáticas de moneda para empresas de distinto tamaño es financieramente incorrecto.
*   **Blast Radius de Migración:** **Alto en el corto plazo (Refactorización masiva de imports), Cero en el largo plazo.** Al borrar `domain/actuarial/maturity_band.py` y `global_maturity_policy.py`, los tests rotos guiarán exactamente dónde actualizar las llamadas.
*   **Modos de Fallo y Edge Cases:** Acoplamiento excesivo si las capas de presentación necesitan metadatos visuales (colores hexadecimales) y estos se incrustan directamente en el modelo de dominio puro (violación de Clean Architecture).

---

### Opción C: Context-Aware Dynamic Calibration Engine (Firmographic Actuarial Engine)
Erradicar las constantes monetarias absolutas. Toda severidad financiera se calcula dinámicamente en función de puntos básicos (bps) de la facturación del cliente, capital operativo o límites de tolerancia al riesgo (VaR), alineado nativamente con Open FAIR.

*   **Pros:**
    *   **Coherencia Matemática y Actuarial:** Es la única solución que resuelve el defecto de negocio real. `150k EUR` es catastrófico para una PYME (facturación 2M EUR) e irrelevante (ruido estadístico) para una corporación IBEX-35 / Fortune 500 (facturación 1.144B EUR).
    *   **Unificación con Open FAIR:** Conecta directamente la salida de simulación de Monte Carlo / ALE con las bandas de *Loss Magnitude (LM 1 - LM 5)* sin dicotomías.
*   **Contras:**
    *   **Dependencia de Datos de Contexto:** Ningún cálculo de severidad puede ejecutarse en el vacío; requiere obligatoriamente el objeto `FirmographicContext` (ingresos anuales, industria, apetito de riesgo).
    *   **Complejidad de Interfaz:** Funciones que antes eran simples (`get_severity(ale: float)`) ahora requieren firma extendida (`evaluate_severity(ale: MonetaryAmount, context: FirmographicContext)`).
*   **Blast Radius de Migración:** **Muy Alto.** Cambia las firmas de los métodos en `actuarial_calculator.py` y `tower_payload_hydrator.py`, obligando a propagar el contexto firmográfico a través de todo el pipeline de ejecución.
*   **Modos de Fallo y Edge Cases:** 
    *   ¿Qué ocurre si un cliente no tiene `revenue` informado (`None` o `0`)? (División por cero o fallo de calibración).
    *   Empresas sin ánimo de lucro, entidades gubernamentales o startups pre-revenue (donde la facturación no refleja el valor en riesgo; se requiere fallback a *Operating Budget* o *Total Assets*).

---

## 3. MATRIZ DE COMPARACIÓN ARQUITECTÓNICA

| Dimensión / Criterio | Opción A: Declarative Config | Opción B: DDD Core Primitive | Opción C: Dynamic Actuarial Engine |
| :--- | :---: | :---: | :---: |
| **Seguridad de Tipos (Mypy/IDE)** | Baja | **Extrema** | Alta |
| **Precisión Actuarial / Negocio** | Media (si es estática) | Baja (si mantiene estáticos) | **Extrema** |
| **Auditabilidad / Versionado** | **Extrema** | Media (vía Git history) | Alta |
| **Esfuerzo de Refactorización** | Medio | Medio | **Alto** |
| **Prevención de Regresiones** | Media (requiere tests de schema) | **Extrema (por compilación)** | Alta |

---

## 4. RECOMENDACIÓN TIER-1: La Síntesis Arquitectónica (B + C + A Compilado)

Un equipo de ingeniería de élite (Google/Stripe/Palantir) **no elegiría una sola opción de forma aislada**, porque atacan capas distintas del problema:
*   La **Opción B** resuelve la *estructura del software* (cómo el código previene el Split-Brain).
*   La **Opción C** resuelve el *modelo matemático* (cómo se calcula la severidad financiera).
*   La **Opción A** resuelve la *gobernanza y auditoría* (dónde viven los parámetros).

### La Solución Definitiva: **Motor de Primitivas de Gobernanza Basado en Contexto con Esquema Compilado**

1.  **Para la Escala de Madurez (Estática e Invariante):** Aplicar **Opción B + A**. Definir un *Value Object* inmutable en el dominio (`MaturityScore`) cuyos intervalos contiguos se cargan desde un manifiesto YAML/JSON versionado, validado al inicio mediante Pydantic para garantizar que no existan huecos matemáticos (invariante de partición continua del espacio `[0.0, 5.0]`).
2.  **Para la Severidad Financiera (Dinámica y Relativa):** Aplicar **Opción C + B**. Prohibir y eliminar cualquier constante en Euros en el código. Crear un motor de calibración firmográfica donde la severidad se exprese internamente en **Puntos Básicos (bps) de Capacidad Financiera**, proyectando dinámicamente los umbrales monetarios en tiempo de ejecución y garantizando un *Fallback* seguro para entidades sin datos firmográficos.

---

## 5. DISEÑO DE IMPLEMENTACIÓN EXACTO (BLUEPRINT)

### Paso 1: El Manifiesto Declarativo (SSOT de Parámetros)
Archivo: `engine_config/governance_scales_v1.json`

```json
{
  "version": "1.0.0",
  "maturity_scale": {
    "precision_epsilon": 1e-9,
    "bands": [
      {"level": 1, "code": "INITIAL", "upper_bound_exclusive": 1.5, "ui_semantic_token": "status-critical", "label_es": "Inicial / Ad-Hoc (D)"},
      {"level": 2, "code": "REPEATABLE", "upper_bound_exclusive": 2.5, "ui_semantic_token": "status-warning", "label_es": "Repetible / Intuitivo (C-)"},
      {"level": 3, "code": "DEFINED", "upper_bound_exclusive": 3.5, "ui_semantic_token": "status-neutral", "label_es": "Definido (C)"},
      {"level": 4, "code": "MANAGED", "upper_bound_exclusive": 4.5, "ui_semantic_token": "status-good", "label_es": "Gestionado Cuantitativamente (B)"},
      {"level": 5, "code": "OPTIMIZED", "upper_bound_exclusive": 5.0001, "ui_semantic_token": "status-excellent", "label_es": "Optimizado (A)"}
    ]
  },
  "financial_severity_bps": {
    "default_fallback_revenue_eur": 50000000.0,
    "open_fair_loss_magnitude_bps": {
      "LM1_MAX_BPS": 0.1136,
      "LM2_MAX_BPS": 0.4545,
      "LM3_MAX_BPS": 1.8181,
      "LM4_MAX_BPS": 7.2727
    }
  }
}
```
*(Nota: En el ejemplo de 1.144B EUR, `0.1136 bps` equivale exactamente a `~13,000 EUR`, `7.2727 bps` equivale a `~832,000 EUR`. La escala Open FAIR queda 100% unificada matemáticamente con los umbrales de severidad).*

### Paso 2: Primitivas de Dominio con Invariantes (Python / Pydantic)
Archivo: `domain/governance/scales.py` (Único punto de acceso autorizado).

```python
from enum import Enum
from typing import Final, List, Optional
from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel, Field, model_validator

# 1. Enums Estrictos (Eliminan Magic Strings en todo el código)
class MaturityBandCode(str, Enum):
    INITIAL = "INITIAL"
    REPEATABLE = "REPEATABLE"
    DEFINED = "DEFINED"
    MANAGED = "MANAGED"
    OPTIMIZED = "OPTIMIZED"

class FinancialSeverity(str, Enum):
    LOW = "LOW"           # Equivalente a Open FAIR LM 1
    MODERATE = "MODERATE" # Equivalente a Open FAIR LM 2
    ELEVATED = "ELEVATED" # Equivalente a Open FAIR LM 3
    HIGH = "HIGH"         # Equivalente a Open FAIR LM 4
    CRITICAL = "CRITICAL" # Equivalente a Open FAIR LM 5

# 2. Value Object Inmutable para Madurez
class ResolvedMaturity(BaseModel, frozen=True):
    raw_score: float
    normalized_score: Decimal
    band_code: MaturityBandCode
    level: int
    label_es: str
    ui_semantic_token: str # La UI traduce este token a Hex, el dominio NO sabe de colores

# 3. Contexto Firmográfico Obligatorio para Finanzas
class FirmographicContext(BaseModel, frozen=True):
    annual_revenue_eur: Optional[Decimal] = Field(default=None, gt=0)
    operating_budget_eur: Optional[Decimal] = Field(default=None, gt=0)

    def get_financial_basis(self, fallback_eur: Decimal) -> Decimal:
        """Resuelve la base de cálculo con fallback determinista (Startup/Gov/SME)."""
        return self.annual_revenue_eur or self.operating_budget_eur or fallback_eur

# 4. Value Object Inmutable para Severidad Financiera
class ResolvedFinancialRisk(BaseModel, frozen=True):
    ale_eur: Decimal
    basis_eur: Decimal
    impact_bps: Decimal
    severity: FinancialSeverity
    open_fair_lm: str # "LM1" .. "LM5"
```

### Paso 3: El Motor de Resolución (Single Source of Truth)
Archivo: `domain/governance/engine.py`

```python
from decimal import Decimal, ROUND_HALF_UP
from domain.governance.scales import (
    MaturityBandCode, FinancialSeverity, ResolvedMaturity, 
    ResolvedFinancialRisk, FirmographicContext
)

class GovernanceScaleEngine:
    """
    Motor Singleton inmutable cargado al inicio de la aplicación.
    Reemplaza a:
    - domain/maturity_band.py
    - domain/actuarial/maturity_band.py
    - infrastructure/global_maturity_policy.py
    """
    
    @staticmethod
    def resolve_maturity(score: float) -> ResolvedMaturity:
        if not (0.0 <= score <= 5.0):
            raise ValueError(f"Invariant violation: Maturity score {score} out of bounds [0.0, 5.0]")
        
        # Normalización estricta a 2 decimales para evitar el bug 1.5 vs 1.59
        # Todo corte es ESTRICTAMENTE MENOR QUE (<) el límite superior.
        norm = Decimal(str(score)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        if norm < Decimal("1.50"):
            return ResolvedMaturity(raw_score=score, normalized_score=norm, band_code=MaturityBandCode.INITIAL, level=1, label_es="Inicial / Ad-Hoc (D)", ui_semantic_token="status-critical")
        elif norm < Decimal("2.50"):
            return ResolvedMaturity(raw_score=score, normalized_score=norm, band_code=MaturityBandCode.REPEATABLE, level=2, label_es="Repetible / Intuitivo (C-)", ui_semantic_token="status-warning")
        elif norm < Decimal("3.50"):
            return ResolvedMaturity(raw_score=score, normalized_score=norm, band_code=MaturityBandCode.DEFINED, level=3, label_es="Definido (C)", ui_semantic_token="status-neutral")
        elif norm < Decimal("4.50"):
            return ResolvedMaturity(raw_score=score, normalized_score=norm, band_code=MaturityBandCode.MANAGED, level=4, label_es="Gestionado Cuantitativamente (B)", ui_semantic_token="status-good")
        else:
            return ResolvedMaturity(raw_score=score, normalized_score=norm, band_code=MaturityBandCode.OPTIMIZED, level=5, label_es="Optimizado (A)", ui_semantic_token="status-excellent")

    @staticmethod
    def resolve_financial_severity(ale_eur: float | Decimal, context: FirmographicContext) -> ResolvedFinancialRisk:
        ale = Decimal(str(ale_eur))
        if ale < 0:
            raise ValueError("ALE cannot be negative.")
            
        # Base por defecto: 50M EUR (Mid-Market baseline) si no hay dato firmográfico
        basis = context.get_financial_basis(fallback_eur=Decimal("50000000.0"))
        
        # Cálculo en Puntos Básicos: 1 bps = 0.01% = 0.0001 de la base
        impact_bps = (ale / basis) * Decimal("10000")
        
        # Escala unificada: Severidad Interna === Open FAIR Loss Magnitude
        if impact_bps < Decimal("0.1136"):
            sev, lm = FinancialSeverity.LOW, "LM1"
        elif impact_bps < Decimal("0.4545"):
            sev, lm = FinancialSeverity.MODERATE, "LM2"
        elif impact_bps < Decimal("1.8181"):
            sev, lm = FinancialSeverity.ELEVATED, "LM3"
        elif impact_bps < Decimal("7.2727"):
            sev, lm = FinancialSeverity.HIGH, "LM4"
        else:
            sev, lm = FinancialSeverity.CRITICAL, "LM5"
            
        return ResolvedFinancialRisk(
            ale_eur=ale,
            basis_eur=basis,
            impact_bps=impact_bps.quantize(Decimal("0.0001")),
            severity=sev,
            open_fair_lm=lm
        )
```

---

## 6. PLAN DE EJECUCIÓN Y GOBERNANZA (ANTI-REGRESIÓN)

Para asegurar que este defecto nunca vuelva a ocurrir en el repositorio, se debe ejecutar el siguiente protocolo de despliegue en 4 fases:

### Fase 1: Resolución de la Discrepancia `1.5` vs `1.59` (Decisión de Producto/Actuaría)
El origen del `1.59` en `domain/actuarial/maturity_band.py` suele ser un intento erróneo de manejar el redondeo a un decimal (ej. querer que `1.54` redondeado a `1.5` caiga en la banda inferior). 
*   **Regla Arquitectónica:** Los cortes continuos se definen como intervalos semiabiertos $[a, b)$. El límite es `< 1.50`, `< 2.50`, `< 3.50`, `< 4.50`. La cuantización (`Decimal.quantize`) ocurre **antes** de la comparación.

### Fase 2: "Scorched Earth" (Eliminación de Archivos Competidores)
No deprecar; **eliminar físicamente** en un único Pull Request atómico:
1.  Eliminar `domain/maturity_band.py`.
2.  Eliminar `domain/actuarial/maturity_band.py`.
3.  Eliminar las reglas numéricas de `infrastructure/global_maturity_policy.py` (convertirlo en un simple mapeador de `ui_semantic_token` $\rightarrow$ `Hex Color`).
4.  En `tower_payload_hydrator.py` y `actuarial_calculator.py`, eliminar los `if ale > ...` y reemplazarlos por llamadas a `GovernanceScaleEngine.resolve_financial_severity(ale, context)`.

### Fase 3: Linter Arquitectónico en CI/CD (Fitness Function)
En equipos Tier-1, la arquitectura se protege con tests automatizados de estructura (usando `pytest-archon` o reglas AST en `ruff`/`flake8`):
*   **Regla 1:** Ningún archivo fuera de `domain/governance/` puede definir constantes flotantes asociadas a umbrales de madurez o riesgo.
*   **Regla 2:** Prohibido serializar hacia la capa de presentación (API/UI) un `float` de madurez o un `float` de ALE sin que vaya encapsulado en el DTO de `ResolvedMaturity` o `ResolvedFinancialRisk`. La UI tiene prohibido calcular colores o etiquetas por su cuenta; solo debe pintar lo que el objeto resuelto le dicta.

### Fase 4: Backtesting y Shadow Evaluation (Mitigación de Blast Radius)
Dado que cambiar de umbrales estáticos (`25k` / `150k`) a umbrales dinámicos (bps) alterará la clasificación de riesgo de los clientes actuales:
1.  Ejecutar un script de *Shadow Comparison* sobre la base de datos de evaluaciones actuales.
2.  Generar un reporte de impacto (ej. *"El 34% de los riesgos antes marcados como CRITICAL en clientes Enterprise pasarán a MODERATE/LM2 al ajustar por su facturación de >1B EUR"*).
3.  Entregar este reporte al equipo de Negocio/Riesgo como prueba de la corrección del bug actuarial antes de promover a producción.