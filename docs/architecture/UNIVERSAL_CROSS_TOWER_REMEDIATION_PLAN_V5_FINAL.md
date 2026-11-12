# PLAN MAESTRO DE REMEDIACIÓN ARQUITECTÓNICA V5 (DEFINITIVO)
**Documento:** `docs/architecture/UNIVERSAL_CROSS_TOWER_REMEDIATION_PLAN_V5_FINAL.md`  
**Autor:** Dirección de Arquitectura de Sistemas & Engineering Lead  
**Estado:** PENDIENTE DE CERTIFICACIÓN DE RED TEAM  
**Alcance:** Motor de Compilación AST, Modelado Financiero Cuantitativo, Síntesis Forense LLM y Gobernanza CMMI v2.0 (Torres T1 a T10).

---

## 1. OBJETIVO DEL PLAN V5

Erradicar de raíz los cuatro defectos sistémicos identificados en la Torre 2 y transversales a toda la plataforma:
1. **Desincronización de Niveles y Bandas CMMI:** Portada de T2 rotulando `1,84 / 5,00` como `Nivel 4 (Gestionado)`, y Tabla 4 rotulando `4,25` como `Nivel 5 (En Optimización)`.
2. **Tratamiento Erróneo de Gastos Fijos (OpEx):** Contratos cautivos de hosting (NOS Portugal en T2) modelados como averías probabilísticas con frecuencia de 1,76 eventos/año.
3. **Antipatrón "Mad-Libs" en Narrativa Financiera:** Dependencia de cadenas de texto gigantescas con `{p90_val}` en `locales.json` que tergiversan el P90 anual acumulado como si fuera un "único evento".
4. **Parches Cosméticos de Regex:** Intentos de usar `re.sub()` para cambiar "DRP" por "Resiliencia" en lugar de gobernar el alcance semántico en memoria.

---

## 2. LOS 4 PILARES ARQUITECTÓNICOS INVARIANTES

### PILAR 1: Resolución Determinista CMMI v2.0 (SSOT en Compiladores)
* **Principio:** Ni el LLM ni las plantillas de localización deciden los niveles o etiquetas de madurez. Solo se transporta el número decimal flotante.
* **Intervalos Oficiales CMMI v2.0 en `maturity_band.py`:**
  * Nivel 1 (0,00 - 1,49): `Inicial (Ad-Hoc / Reactivo)`
  * Nivel 2 (1,50 - 2,49): `Gestionado (Repetible)`
  * Nivel 3 (2,50 - 3,49): `Definido (Estandarizado)`
  * Nivel 4 (3,50 - 4,49): `Gestionado Cuantitativamente (Medible)`
  * Nivel 5 (4,50 - 5,00): `En Optimización (Mejora Continua)`
* **Erradicación en `payload_to_ast.py`:**
  * Se elimina el diccionario desincronizado `band_key_level_map` (que asignaba `"band_managed": 4`).
  * La celda de la Portada (Tabla 0) extrae el nivel directamente de `band_info["level"]` y su etiqueta oficial. Un score de `1,84` resolverá SIEMPRE como `Nivel 2 (Gestionado)`.
  * La Tabla 4 erradica `math.ceil(target_score)` y resuelve la banda mediante `resolve_maturity_band()`, asegurando que `4,25` resuelva como `Nivel 4 (Gestionado Cuantitativamente)`.

### PILAR 2: Clasificador Polimórfico Financiero (`FinancialNatureEnum`)
* **Esquema Pydantic (`finding_schema.py`):**
  * `STOCHASTIC_RISK`: Averías, cortes y fallos técnicos. Se modelan con frecuencia anual (`TEF`) y coste por evento (`SLE`). En la ficha técnica, $\text{ALE} = \text{SLE} \times \text{Frecuencia}$.
  * `DETERMINISTIC_OPEX`: Ineficiencias contractuales, licencias ociosas y sobrecostes fijos (ej. Broadcom en RVS02 y NOS Portugal en RVS06).
* **Renderizado AST en Fichas de Riesgo:**
  * Si `is_deterministic`:
    * Frecuencia: `N/A (Coste Fijo Recurrente)`
    * Coste por Evento: `N/A (Gasto Mensual / Anual)`
    * Impacto Anual: `{annual_deterministic_waste_eur:,.0f} € / año`
    * Impacto en Planta: `Sin parada de planta`
    * Ajuste por simultaneidad de parada fabril: **0% (Suma directa al céntimo)**.

### PILAR 3: Presentador de Telemetría Financiera (Fin de Mad-Libs en `locales.json`)
* **Principio:** `locales.json` se restringe exclusivamente a etiquetas de interfaz y nombres de columnas (UI Chrome). Prohibido almacenar párrafos narrativos complejos con variables interpoladas.
* **Módulo `financial_presenter.py`:**
  * Recibe el contrato de telemetría:
    * `corporate_ale`: Exposición anual promedio.
    * `p90_tail_risk`: Riesgo acumulado anual en ejercicio extremo (Monte Carlo P90).
    * `max_single_incident`: Peor evento individual aislado (Max SLE).
    * `deterministic_opex`: Desperdicio fijo anual.
  * Ensambla en código Python la narrativa ejecutiva de solvencia financiera (Párrafo P015), explicando con rigor que el P90 es la acumulación de múltiples contingencias a lo largo de 12 meses, frente a los costes contenidos de un incidente aislado.

### PILAR 4: Compuerta Semántica CEGAR (Rechazo en Memoria sin Regex Cosmético)
* **Principio:** Prohibido usar `re.sub(r"DRP", "Resiliencia")` en tiempo de compilación.
* **Validación en `PillarForensicSynthesizer`:**
  * Cada torre tiene una lista de responsabilidades permitidas y prohibidas.
  * Si el LLM titula un hallazgo en la Torre 2 como *"Marco de Recuperación ante Desastres (DRP)"*, el `SemanticGatekeeper` intercepta el objeto en memoria y lanza un `SemanticQualityError`:
    *«Rechazado: La gobernanza de DRP pertenece a la Torre 5. En la Torre 2 la limitación es técnica de hipervisores; retitule como 'Resiliencia de Hipervisores y Disponibilidad vSphere HA ante Caída de Nodos'».*
  * El LLM reescribe el hallazgo desde la raíz. Cero parches cosméticos en caliente.

---

## 3. PLAN DE IMPLEMENTACIÓN SECUENCIAL

1. **Paso 1:** Refactorizar `src/assessment_engine/domain/maturity_band.py` y actualizar `payload_to_ast.py:1625` (Pilar 1).
2. **Paso 2:** Introducir `FinancialNatureEnum` en el generador de riesgos y compilar RVS06 (NOS Portugal) como OpEx determinista sin frecuencia falsa (Pilar 2).
3. **Paso 3:** Implementar `financial_presenter.py` y purgar la plantilla Mad-Libs de `locales.json` (Pilar 3).
4. **Paso 4:** Actualizar `gatekeeper.py` para rechazar DRP en T2 forzando el título legítimo de vSphere HA (Pilar 4).
5. **Paso 5:** Recompilar los 11 documentos y ejecutar la suite de tests unitarios y de arquitectura.
