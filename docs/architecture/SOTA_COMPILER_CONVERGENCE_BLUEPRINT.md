# BRIEFING DE ARQUITECTURA: ERRADICACIÓN DEL ANTI-PATRÓN "COMPILER SPLIT-BRAIN" Y REDISEÑO DE LA CAPA DE PRESENTACIÓN DOCUMENTAL

**DE:** `gemini-4-argon`, Principal Enterprise Architect & Fellow in Systems Design  
**FECHA:** Noviembre 2026  
**ASUNTO:** Consolidación de Compiladores DOCX, Aislamiento de Dominio Hexagonal y Pipeline AST Declarativo SOTA  
**CLASIFICACIÓN:** Estándar de Ingeniería Tier-1 (Nivel Stripe / Palantir Foundry)

---

## 0. RESUMEN EJECUTIVO Y DIAGNÓSTICO

El motor de evaluación sufre actualmente de una severa degradación arquitectónica en su capa de salida: el anti-patrón **"Compiler Split-Brain"** (Cerebro Dividido de Compilación), agravado por **Domain Bleed** (fuga de lógica de dominio hacia los adaptadores de presentación). 

Tener 7 artefactos de compilación compitiendo por generar archivos OpenXML (DOCX), sumado al hecho de que un adaptador de presentación (`payload_to_ast.py`, 5.3k LOC) importe funciones de cálculo de negocio (`derive_in_memory_fair_risks`) desde un compilador hermano (`in_memory_asis_compiler.py`, 2.3k LOC), viola de manera flagrante los principios de **Clean/Hexagonal Architecture**, **Single Responsibility Principle (SRP)** y el **Paradigma de Compiladores Modernos (LLVM-style Pipeline)**.

A continuación, se define la solución definitiva de Grado Empresarial (SOTA Noviembre 2026) para reducir la deuda técnica a cero, unificar la emisión documental y garantizar la universalidad multi-vertical.

---

## 1. THE TARGET ARCHITECTURE (Aislamiento Hexagonal y Pipeline de 3 Etapas)

Para erradicar el *Domain Bleed*, adoptamos una **Arquitectura Hexagonal Estricta (Ports & Adapters)** combinada con un **Pipeline de Compilación Desacoplado (Frontend -> IR -> Backend)** inspirado en la arquitectura de compiladores modernos (como LLVM o Pandoc) y sistemas de generación de reportes financieros de misión crítica (Stripe Reporting Engine).

```
[ CAPA DE APLICACIÓN / DOMINIO (Pura, Determinista, Sin Estado) ]
  Raw Telemetry / Inputs
       │
       ▼
  ┌──────────────────────────────────────────────────────────┐
  │ Domain Valuation & Analytics Engine                      │
  │ - ActuarialEngine (FAIR Risk, ALE, Montecarlo)           │
  │ - FinancialEngine (Euler Discounting, NPV, ROI)          │
  │ - MaturityEngine (CMMI Resolution, Benchmarking)         │
  └──────────────────────────────────────────────────────────┘
       │ Emite: ValidatedAssessmentReadModel (100% Pre-computado)
       ▼
═══════════════════ PUERTO DE SALIDA (OUTPUT PORT) ═══════════════════
       │
       ▼
[ CAPA DE PRESENTACIÓN / ADAPTADOR DE INFRAESTRUCTURA (Dumb Renderer) ]
  ┌──────────────────────────────────────────────────────────┐
  │ 1. AST Lowering Engine (Frontend Declarativo)            │
  │    - Transforma el ReadModel en un DocumentAST agnóstico │
  │    - Usa Composición Funcional (Nodes, Blocks, Inlines)  │
  └──────────────────────────────────────────────────────────┘
       │ Emite: DocumentAST (Intermediate Representation - IR)
       ▼
  ┌──────────────────────────────────────────────────────────┐
  │ 2. OpenXML Emitter Engine (Backend Determinista)         │
  │    - Recorre el DocumentAST (Visitor Pattern)            │
  │    - Aplica ThemeContract (Estilos, Tipografía, Colores) │
  │    - Serializa a binario .docx                           │
  └──────────────────────────────────────────────────────────┘
```

### Reglas de Oro de la Nueva Arquitectura:
1. **Cero Matemáticas en la Presentación:** La capa de presentación tiene **prohibido** importar librerías estadísticas, financieras o de resolución de matrices. Si un dato no viene calculado en el *Read Model*, el compilador falla en tiempo de validación (*Fail-Fast*), jamás intenta calcularlo.
2. **Representación Intermedia (IR) Universal:** El `DocumentAST` no sabe qué es "riesgo FAIR" ni qué es una "Torre Tecnológica". Solo conoce primitivas semánticas de documento: `Section`, `Heading`, `Paragraph`, `DataTable`, `CalloutBox`, `MetricCard`, `ChartVector`.
3. **100% Technical English:** Todo el código, nombres de nodos AST, variables, contratos de datos y comentarios internos se escriben estrictamente en inglés técnico. El idioma del entregable final (ej. Español, Inglés, Alemán) se inyecta como un diccionario de localización (`LocaleBundle`) en el *Read Model*.

---

## 2. THE UNIFIED COMPILER STRATEGY (Estrategia de Consolidación y Purga)

Un reporte global (Tomo 1) y un anexo de torre individual no son arquitecturas distintas; **son exactamente el mismo árbol sintáctico (AST) instanciado con diferente topología de composición**. Un reporte global es simplemente un nodo raíz (`DocumentRoot`) que itera sobre múltiples sub-árboles de dominio, mientras que un anexo proyecta un único sub-árbol.

### A. Matriz de Disposición de Artefactos (Tombstoning)

| Artefacto Actual | Estado SOTA | Justificación Arquitectónica |
| :--- | :--- | :--- |
| `render_tower_annex_from_template.py` | **TOMBSTONED (Eliminar)** | La interpolación de plantillas binarias es frágil, imposible de versionar en Git con claridad y propensa a corromper el XML subyacente. |
| `render_global_report_from_template.py` | **TOMBSTONED (Eliminar)** | Mismo motivo anterior. Tecnología obsoleta. |
| `in_memory_asis_compiler.py` (2.3k LOC) | **DECONSTRUCT & TOMBSTONE** | Extraer toda la lógica de negocio (`derive_in_memory_*`) hacia el `Domain Analytics Engine`. Eliminar el resto del archivo. |
| `compile_asis_docx_from_modules.py` | **TOMBSTONED (Eliminar)** | Redundante frente a un motor composicional basado en AST. |
| `tomo_asis_ast_compiler.py` | **TOMBSTONED (Eliminar)** | Caso especial acoplado. Se reemplaza por un *Blueprint* declarativo en el nuevo motor AST. |
| `payload_to_ast.py` (5.3k LOC) | **REFACTOR & SLIM DOWN** | Es un monolito procedimental. Debe dividirse en constructores de componentes AST puros y declarativos (< 800 LOC en total). |
| `docx_compiler.py` | **RETAIN & UPGRADE** | Se mantiene como el **único Backend Emisor OpenXML**. Se limpia para que solo acepte el `DocumentAST` validado y un `ThemeContract`. |

### B. El Nuevo Diseño Unificado: Compositional AST Blueprints

En lugar de tener un compilador por tipo de documento, creamos un único motor gobernado por **Document Blueprints** (inspirado en *React Server Components* o *SwiftUI* pero aplicado a generación estática de documentos).

```python
# presentation/blueprints/assessment_blueprints.py (100% Technical English)

class DocumentBlueprint(Protocol):
    def build_ast(self, model: AssessmentReadModel, i18n: LocaleBundle) -> DocumentNode:
        ...

class TowerAnnexBlueprint(DocumentBlueprint):
    """Composes an individual domain/tower technical annex."""
    def build_ast(self, model: TowerReadModel, i18n: LocaleBundle) -> DocumentNode:
        return DocumentNode(
            metadata=model.metadata,
            children=[
                 CoverPageComponent.render(model.header, i18n),
                ExecutiveSummaryComponent.render(model.summary, i18n),
                MaturityMatrixComponent.render(model.cmmi_matrix, i18n),
                FairRiskTableComponent.render(model.actuarial_risks, i18n),
                TechnicalFindingsComponent.render(model.findings, i18n),
            ]
        )

class GlobalExecutiveReportBlueprint(DocumentBlueprint):
    """Composes the consolidated multi-tower global report (formerly Tomo 1)."""
    def build_ast(self, model: GlobalAssessmentReadModel, i18n: LocaleBundle) -> DocumentNode:
        return DocumentNode(
            metadata=model.metadata,
            children=[
                CoverPageComponent.render(model.header, i18n),
                GlobalFinancialRollupComponent.render(model.consolidated_financials, i18n),
                CrossDomainMaturityComponent.render(model.global_cmmi, i18n),
                # Composición iterativa reutilizando exactamente los mismos componentes:
                *[TowerSummarySectionComponent.render(tower, i18n) for tower in model.towers]
            ]
        )
```

---

## 3. THE DATA CONTRACT (El Contrato de Datos Inmutable)

Para garantizar que el compilador sea un **"Dumb Renderer"** (Renderizador Tonto) y cumpla con los estándares de sistemas distribuidos modernos (Palantir Foundry Ontology / Stripe API Contracts), establecemos una frontera infranqueable mediante **Pydantic v2** (con núcleo en Rust) o `msgspec` para validación ultrarrápida y estricta inmutabilidad.

### Propiedades del Contrato (`AssessmentReadModel`):
1. **Inmutabilidad Criptográfica (`frozen=True`):** El compilador no puede mutar el estado de los datos durante el renderizado.
2. **Valores Pre-computados y Formateados Semánticamente:** El dominio entrega estructuras de valor tipadas (`MonetaryValue`, `PercentageValue`, `RiskDistribution`), nunca números flotantes crudos ambiguos ni diccionarios sin esquema (`dict[str, Any]` está estrictamente prohibido).
3. **Agnosticismo Vertical:** No existen campos llamados `cement_plant_risk` o `molins_specific_metric`. Todo se modela mediante ontologías universales (`AssetNode`, `RiskScenario`, `CapabilityDimension`).

```python
# domain/contracts/read_models.py (100% Technical English)
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from typing import Tuple

class StrictImmutableModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

class MonetaryValuation(StrictImmutableModel):
    amount: Decimal
    currency_iso: str = Field(min_length=3, max_length=3)
     formatted_display: str  # Pre-formateado según locale, ej. "€1,250,000.00"

class ActuarialRiskRecord(StrictImmutableModel):
    scenario_id: str
    asset_name: str
    threat_community: str
    annualized_loss_expectancy: MonetaryValuation
    present_value_euler_discounted: MonetaryValuation
    loss_exceedance_p90: MonetaryValuation
    risk_severity_tier: str  # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"

class MaturityDimensionRecord(StrictImmutableModel):
    capability_id: str
    capability_name: str
    current_cmmi_level: int = Field(ge=1, le=5)
    target_cmmi_level: int = Field(ge=1, le=5)
    gap_delta: int
    benchmark_percentile: float

class TowerReadModel(StrictImmutableModel):
    domain_id: str
    domain_name: str
    actuarial_risks: Tuple[ActuarialRiskRecord, ...]
    cmmi_matrix: Tuple[MaturityDimensionRecord, ...]
    # ... otros tensores de datos 100% resueltos por el dominio
```

---

## 4. EXECUTION PLAN (Plan de Migración Sin Tiempo de Inactividad)

Para migrar hacia esta arquitectura sin romper la generación actual en producción (ej. entregables críticos como Molins), ejecutaremos el patrón **Strangler Fig (Higuera Estranguladora)** combinado con **Shadow Verification & Golden Master Testing (Pruebas de Snapshot de AST)**.

### Fase 1: Extracción de Dominio y Congelamiento de Golden Masters (Días 1-3)
1. **Snapshot Baseline:** Ejecutar el pipeline actual con el dataset de producción (Molins) y capturar el `DocumentAST` generado por `payload_to_ast.py` serializado en JSON, así como las métricas financieras exactas. Este JSON será nuestro **Golden Master**.
2. **Desacoplamiento Quirúrgico:** Mover `derive_in_memory_fair_risks`, `derive_in_memory_maturity_matrix`, cálculos de Euler y ALE desde `in_memory_asis_compiler.py` hacia un nuevo módulo puro: `src/domain/analytics_engine/`.
3. **Inyección Inversa Temporal:** Hacer que tanto `in_memory_asis_compiler.py` como `payload_to_ast.py` importen estas funciones desde el nuevo módulo de dominio. *(En este punto, el acoplamiento cruzado entre compiladores desaparece sin cambiar una sola línea del output).*

### Fase 2: Implementación del Contrato de Datos (`ReadModel`) (Días 4-6)
1. Construir los esquemas estrictos de Pydantic v2 (`GlobalAssessmentReadModel` y `TowerReadModel`).
2. Crear el servicio orquestador de aplicación (`AssessmentProjectionService`) que toma los datos crudos, invoca al `analytics_engine`, y construye el `ReadModel` inmutable.
3. Escribir tests unitarios deterministas que validen que los cálculos del `ReadModel` coinciden al 100% (precisión decimal exacta) con los resultados del Golden Master.

### Fase 3: Refactorización del Frontend AST a Componentes Declarativos (Días 7-10)
1. Dividir el monolito `payload_to_ast.py` (5.3k LOC) en componentes modulares puros dentro de `src/presentation/ast_components/` (Tablas, Matrices, Portadas, Secciones).
2. Erradicar todo el texto hardcodeado en español dentro del código; mover las cadenas estáticas a un archivo de recursos `locales/es_ES.json` y `locales/en_US.json`.
3. Implementar `TowerAnnexBlueprint` y `GlobalExecutiveReportBlueprint` consumiendo únicamente el `ReadModel`.
4. **Shadow Testing (Verificación de Paridad):** Ejecutar el nuevo motor de Blueprints con el dataset de Molins y comparar el AST resultante contra el **Golden Master AST** de la Fase 1. Deben ser estructural y semánticamente idénticos.

### Fase 4: Consolidación del Backend OpenXML y Purga Final (Días 11-12)
1. Conectar la salida de los nuevos Blueprints directamente a `docx_compiler.py`.
2. Verificar visual y estructuralmente el binario `.docx` generado para Molins.
3. **Ejecución del Tombstoning:** Eliminar permanentemente del repositorio los 5 compiladores obsoletos (`render_tower_annex_from_template.py`, `render_global_report_from_template.py`, `in_memory_asis_compiler.py`, `compile_asis_docx_from_modules.py`, `tomo_asis_ast_compiler.py`) y el antiguo `payload_to_ast.py`.
4. Configurar reglas de Linter estático (`ruff` + `import-linter`) en el pipeline de CI/CD que **bloqueen cualquier Pull Request** si el paquete `src/presentation/` intenta importar cualquier módulo de `src/domain/analytics_engine/` (solo se le permite importar `src/domain/contracts/`).

---

### CONCLUSIÓN ARQUITECTÓNICA
Con esta intervención, pasamos de 7 scripts acoplados y frágiles (~10,000+ LOC combinadas con lógica duplicada) a **1 Único Pipeline Compilador Determinista (~1,500 LOC modulares)** gobernado por tipos estrictos. El motor de evaluación queda blindado contra regresiones, preparado para escalar a cualquier vertical industrial sin tocar el código del compilador, y alineado con el estado del arte de la ingeniería de software a nivel mundial.