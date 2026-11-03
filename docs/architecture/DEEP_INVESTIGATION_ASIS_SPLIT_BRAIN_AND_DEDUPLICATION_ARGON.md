# Informe de Investigación Forense: Auditoría Intra-Documento y Arquitectura de Deduplicación Cross-Tower

**Rol:** Chief Systems Architect & Principal Actuary  
**Alcance:** Inspección profunda del motor determinista (`ActuarialCalculator`), transpilador AST (`payload_to_ast.py`) y payloads de datos (`working/molins/T1..T10`).

---

## 1. Auditoría de Deduplicación Cross-Tower: ¿Estamos duplicando riesgos hoy?

Tu intuición es quirúrgica y ha destapado exactamente la brecha entre la **capacidad del motor** y la **realidad actual de los datos (fixtures)**.

### A. El Estado del Código (El Motor está preparado)
El compilador matemático y el transpilador AST ya tienen implementada la lógica de deduplicación contable:
1. **Esquema de Datos (`ConditionalLossEvent`):** Soporta los campos `ownership_type` (`PRIMARY_CUSTODIAN` vs `TANGENTIAL_CONTRIBUTOR`) y `primary_risk_ref`.
2. **Motor Actuarial (`ActuarialCalculator`):** Si detecta `ownership_type == "TANGENTIAL_CONTRIBUTOR"`, marca `is_deduplicated = True` y fuerza **`effective_sle = 0.0` y `ale = 0.0`**, evitando que sume al total de la torre o del programa.
3. **Renderizado AST (`payload_to_ast.py`):** Cuando un riesgo es tangencial, omite las filas financieras de SLE/ALE en la tarjeta del riesgo e inyecta la nota legal:  
   *«Exposición Financiera (ALE) contabilizada en el Riesgo Primario: {primary_risk_ref}»*.

### B. La Realidad en los Datos (Por qué hoy se están sumando todos)
Al auditar los payloads JSON en `working/molins/T1/` y `T2/`, comprobamos que **todos los riesgos tienen actualmente `"ownership_type": null`**.
* Cuando el campo es `null`, el motor aplica el fallback por defecto: `PRIMARY_CUSTODIAN`.
* **Consecuencia:** Hoy el mecanismo está programado pero **inactivo en los datos**. Por ejemplo, el riesgo de corte o degradación por acceso a red/perímetro o caída de infraestructura compartida se está cuantificando íntegramente en T1 y volviendo a cuantificar en T2/T4 sin deduplicar.

---

## 2. El Problema de las Torres Parciales: "Ceguera Actuarial" vs. Doble Contabilidad

Planteas el escenario más crítico en consultoría modular: **¿Qué ocurre si un riesgo de T2 (Compute) apunta como primario a T6 (Ciberseguridad), pero el cliente solo contrata T1 y T2?**

* **El peligro del hardcoding estático:** Si marcamos estáticamente un riesgo en T2 como `TANGENTIAL_CONTRIBUTOR` apuntando a `T6.R01`, y el cliente **no contrata T6**, el motor pondría el riesgo a `0 €` en T2 asumiendo que ya se cuenta en T6. Como T6 no forma parte del alcance contratado, **el riesgo desaparece financieramente del entregable**. El cliente tendría un *Blind Spot* (punto ciego actuarial) gravísimo.
* **La regla de negocio necesaria:** Un riesgo tangencial **solo debe deduplicarse (ponerse a 0 €) si y solo si la Torre Custodia Primaria forma parte del alcance activo (`active_towers_scope`) del contrato del cliente**. Si la torre primaria no se evalúa, el riesgo en la torre evaluada debe **promocionarse dinámicamente a `PRIMARY_CUSTODIAN`** (o asumir una cuota de custodia local) para que la exposición financiera jamás quede oculta.

---

## 3. Arquitectura de Solución: `DynamicCustodyResolver` (100% Technical English Specification)

To eliminate both **Double Counting** (when all towers are contracted) and **Actuarial Blind Spots** (when a subset of towers is contracted), we introduce the **`DynamicCustodyResolver`** middleware in the pre-calculation pipeline before invoking `ActuarialCalculator`.

### Architectural Pattern: Contextual Custody Promotion

```python
from enum import Enum
from typing import List, Set, Optional
from pydantic import BaseModel, Field


class OwnershipType(str, Enum):
    PRIMARY_CUSTODIAN = "PRIMARY_CUSTODIAN"
    TANGENTIAL_CONTRIBUTOR = "TANGENTIAL_CONTRIBUTOR"


class CustodyResolutionAudit(BaseModel):
    risk_id: str
    declared_ownership: OwnershipType
    effective_ownership: OwnershipType
    primary_risk_ref: Optional[str] = None
    primary_tower_id: Optional[str] = None
    was_promoted: bool = False
    resolution_reason: str


class DynamicCustodyResolver:
    """
    Context-aware actuarial deduplication resolver.
    Prevents double-counting across evaluated towers while guaranteeing zero blind spots
    when a client contracts a partial subset of capability towers.
    """

    @staticmethod
    def extract_tower_id(primary_risk_ref: Optional[str]) -> Optional[str]:
        """Extracts canonical tower ID (e.g., 'T6' from 'T6.R01' or 'T6-R02')."""
        if not primary_risk_ref:
            return None
        normalized = primary_risk_ref.replace("-", ".").strip().upper()
        parts = normalized.split(".")
        return parts[0] if parts and parts[0].startswith("T") else None

    @classmethod
    def resolve_event_custody(
        cls,
        risk_id: str,
        declared_ownership: Optional[OwnershipType],
        primary_risk_ref: Optional[str],
        active_towers_scope: Set[str],
    ) -> CustodyResolutionAudit:
        """
        Determines effective financial custody based on the contracted assessment scope.
        """
        # Default fallback if untagged in JSON payload
        ownership = declared_ownership or OwnershipType.PRIMARY_CUSTODIAN

        if ownership == OwnershipType.PRIMARY_CUSTODIAN:
            return CustodyResolutionAudit(
                risk_id=risk_id,
                declared_ownership=ownership,
                effective_ownership=OwnershipType.PRIMARY_CUSTODIAN,
                primary_risk_ref=primary_risk_ref,
                was_promoted=False,
                resolution_reason="Explicit or default PRIMARY_CUSTODIAN.",
            )

        # Case: TANGENTIAL_CONTRIBUTOR
        target_tower = cls.extract_tower_id(primary_risk_ref)
        normalized_scope = {t.strip().upper() for t in active_towers_scope}

        if target_tower and target_tower in normalized_scope:
            # Target primary tower IS evaluated in this engagement -> Deduplicate (ALE = 0)
            return CustodyResolutionAudit(
                risk_id=risk_id,
                declared_ownership=ownership,
                effective_ownership=OwnershipType.TANGENTIAL_CONTRIBUTOR,
                primary_risk_ref=primary_risk_ref,
                primary_tower_id=target_tower,
                was_promoted=False,
                resolution_reason=(
                    f"Target primary tower '{target_tower}' is in active scope "
                    f"{sorted(normalized_scope)}. Financial exposure deduplicated."
                ),
            )
        else:
            # Target primary tower is NOT evaluated -> Promote to PRIMARY_CUSTODIAN
            return CustodyResolutionAudit(
                risk_id=risk_id,
                declared_ownership=ownership,
                effective_ownership=OwnershipType.PRIMARY_CUSTODIAN,
                primary_risk_ref=primary_risk_ref,
                primary_tower_id=target_tower,
                was_promoted=True,
                resolution_reason=(
                    f"Target primary tower '{target_tower}' is OUTSIDE active scope "
                    f"{sorted(normalized_scope)}. Dynamically promoted to PRIMARY_CUSTODIAN "
                    f"to prevent an actuarial blind spot."
                ),
            )
```

### How It Works in the Pipeline:
1. **Full 10-Tower Engagement (`active_towers_scope = {"T1", ..., "T10"}`):**  
   A tangential risk in `T2` pointing to `T6.R01` sees `"T6" in active_towers_scope`. It remains `TANGENTIAL_CONTRIBUTOR`, its local `ALE` is set to `0.00 €`, and the document explicitly cross-references `T6.R01`.
2. **Partial Engagement (`active_towers_scope = {"T1", "T2"}`):**  
   The resolver detects `"T6" not in {"T1", "T2"}`. It sets `was_promoted = True` and promotes the risk to `PRIMARY_CUSTODIAN` for this client delivery. The risk is fully quantified in `T2`, and the AST renders a transparent footnote:  
   *«Nota de Alcance: Riesgo cuantificado localmente en T2 dado que la torre custodia primaria (T6) no forma parte del alcance evaluado.»*

---

## 4. Auditoría Forense de "Split-Brain" Intra-Documento (Capítulos 1 al 4)

Hemos ejecutado una inspección cruzada de extremo a extremo sobre el generador (`payload_to_ast.py`), el calculador (`ActuarialCalculator`) y los documentos compilados de las torres para verificar si quedan discrepancias internas (*split-brains*) dentro de un mismo documento AS-IS.

| Punto de Control Intra-Documento | Secciones Cruzadas | Estado Actual | Veredicto Forense |
| :--- | :--- | :---: | :--- |
| **1. Coste Horario de Parada (Burn Rate)** | Cap. 1 (1.1 Cockpit) vs. Cap. 4 (4.1 Base Actuarial y Tarjetas 4.3) | **100% Sincronizado** | **SIN SPLIT-BRAIN.** Ambos leen de la fuente única `ActuarialCalculationResult.hourly_downtime_rate_eur` (`13.061,29 €/h` en Molins). |
| **2. Exposición Anual Esperada (ALE P50)** | Cap. 1 (1.1 Cockpit / 1.2 Hallazgos) vs. Cap. 4 (Suma de Riesgos 4.3) | **100% Sincronizado** | **SIN SPLIT-BRAIN.** El total de la torre (`total_tower_ale_eur`) es la suma exacta de los riesgos primarios de la sección 4.3 (`43.559,39 €` en T1; `44.996,15 €` en T2). |
| **3. Exposición Extremo (VaR P90)** | Cap. 1 (1.1 Cockpit) vs. Cap. 4 (4.1 / 4.2 Agregación de Cola) | **100% Sincronizado** | **SIN SPLIT-BRAIN.** Calculado mediante el mismo motor de agregación lognormal / condicional y referenciado idénticamente en ambas secciones. |
| **4. Pesos y Madurez CMMI (1.00 - 5.00)** | Cap. 2 (2.2 Modelo de Pesos) vs. Cap. 3 (3.1 Tabla de Diagnóstico y 3.2 Pilares) | **100% Sincronizado** | **SIN SPLIT-BRAIN.** La media ponderada de las capacidades en Cap. 3 coincide al céntimo con el índice global del Cockpit en Cap. 1 (`2,65 / 5,00` en T1; `2,30 / 5,00` en T2). |
| **5. Trazabilidad Diagnóstico -> Riesgos** | Cap. 3 (3.2 Análisis por Pilar) vs. Cap. 4 (4.3 Eventos de Pérdida) | **100% Sincronizado** | **SIN SPLIT-BRAIN.** Los riesgos de la sección 4.3 referencian las capacidades con menor madurez del Cap. 3 y utilizan su score CMMI para modular la vulnerabilidad. |
| **6. Coordenadas del Heatmap vs. Escalas** | Cap. 4 (4.2 Mapa de Calor) vs. Cap. 4 (4.2.1 Escala TEF y 4.2.2 Escala LM) | **100% Sincronizado** | **SIN SPLIT-BRAIN.** Tras la remediación previa, ningún riesgo cae en coordenadas huérfanas: cada celda `[Pn, Im]` del Heatmap corresponde matemáticamente a los umbrales de `TEF` y `SLE` de las tablas 4.2.1 y 4.2.2. |
| **7. Aritmética Interna de Tarjetas SLE** | Cap. 4 (4.3 Horas de Parada × Coste/h = SLE Efectivo) | **100% Sincronizado** | **SIN SPLIT-BRAIN.** El motor calcula `SLE = Horas × 13.061,29 €/h` sin redondeos intermedios prematuros que descuadren la multiplicación visual en la tabla. |

---

## 5. Conclusión Ejecutiva y Plan de Acción Inmediato

1. **Intra-Documento (Dentro de cada Torre):** **No existe ningún *split-brain* residual** entre los Capítulos 1, 2, 3 y 4. Todas las cifras financieras (`13.061,29 €/h`, `SLE`, `ALE P50`, `VaR P90`), escalas (`TEF`/`LM`) y puntuaciones de madurez (`CMMI`) emanan de una única ejecución determinista de `ActuarialCalculator` antes de renderizar el AST.
2. **Inter-Documento (Entre las 10 Torres):** El código ya soporta deduplicación, pero **los ficheros JSON de las torres tienen `ownership_type: null`**, y además falta el resolvedor dinámico para clientes que contratan torres sueltas.
3. **Siguientes pasos recomendados para cerrar el ciclo al 100%:**
   * **Paso 1:** Integrar `DynamicCustodyResolver` dentro de `ActuarialCalculator.calculate_from_payload()` recibiendo `active_towers_scope`.
   * **Paso 2:** Auditar el catálogo completo de riesgos de `T1` a `T10` para etiquetar qué riesgos son `TANGENTIAL_CONTRIBUTOR` y a qué `primary_risk_ref` apuntan (ej. riesgos de red en T2 que apuntan a T4, o riesgos de ransomware en T2/T3 que apuntan a T6).