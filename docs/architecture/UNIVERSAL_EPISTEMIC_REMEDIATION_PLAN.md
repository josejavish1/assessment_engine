```markdown
# PLAN MAESTRO DE REMEDIACIÓN ARQUITECTÓNICA Y EPISTÉMICA UNIVERSAL (TIER-1)

**Documento:** `docs/architecture/UNIVERSAL_EPISTEMIC_REMEDIATION_PLAN.md`  
**Autor:** `gemini-4-argon` (Lead AI Systems Architect & Principal Software Engineer)  
**Destinatario:** Agente de Implementación (`Gemini 3.8`)  
**Estado:** APROBADO PARA EJECUCIÓN INMEDIATA  
**Clasificación:** Crítico / Refactorización del Core Engine  

---

## 0. RESUMEN EJECUTIVO DEL MANDATO

Una auditoría forense externa sobre los entregables AS-IS generados por el motor ha expuesto tres fallos sistémicos e inaceptables en sistemas de evaluación empresarial de Nivel 1 (Tier-1):
1. **Manipulación Arbitraria de Puntuaciones y Violación de Dominio (Cross-Domain Contamination).**
2. **Alucinación Forense por Presión de Volumen (Epistemic Over-extension).**
3. **Opacidad Matemática en la Desagregación Actuarial (Euler/Copula Math Opacity).**

Queda terminantemente prohibido aplicar parches tácticos (ej. filtros `if/else` para clientes específicos o listas negras de palabras). Este documento establece las directrices de ingeniería de software para reestructurar el núcleo del motor en Python, garantizando **integridad epistémica, determinismo matemático y aislamiento estricto de dominios** para cualquier cliente global.

---

## 1. ANÁLISIS FORENSE DE CAUSA RAÍZ (ROOT CAUSE ANALYSIS)

### 1.1. Pecado Capital 1: Violación de Dominio y Alteración de Scores (`score_reconciler.py`)
* **Mecánica del Fallo:** El módulo `score_reconciler.py` opera bajo un antipatrón de *Heurística Semántica Post-Hoc*. Tras la generación de narrativa por parte del LLM, un analizador basado en expresiones regulares (Regex) escanea el texto generado buscando tokens de polaridad negativa (ej. `"ausencia"`, `"inexistente"`, `"sin plan"`, `"carece"`). Si los detecta, aplica un multiplicador de penalización severo o establece un *hard-cap* (ej. limitar la nota a `1.75/5.00`), sobrescribiendo la puntuación empírica original declarada por el cliente (`4.00/5.00`).
* **Contaminación Cruzada:** El motor de extracción (`context_builder`) inyecta el contexto global o permite que el LLM correlacione libremente riesgos sistémicos. En el caso auditado, al evaluar `T1.P4` (Protección contra Incendios), el LLM mencionó que un incendio sería catastrófico debido a la *"ausencia de un DRP"* (Disaster Recovery Plan, que pertenece estrictamente al dominio `T5 - Resiliencia`). El `score_reconciler.py` leyó la palabra *"ausencia"* dentro del bloque de texto de `T1.P4` y destruyó la nota de Protección contra Incendios del cliente. Esto viola el principio de ortogonalidad de dominios.

### 1.2. Pecado Capital 2: Alucinación Forense por Presión de Densidad (`UniversalTowerSynthesizer`)
* **Mecánica del Fallo:** Los prompts del sistema en `UniversalTowerSynthesizer` contienen restricciones estáticas de longitud y estilo (ej. *"Escriba un análisis técnico exhaustivo de mínimo 400 palabras por pilar con mentalidad de auditor forense CISA/TIA-942"*).
* **Fallo Epistémico:** Los LLMs son motores probabilísticos de completado de secuencias. Cuando la evidencia empírica inyectada en el contexto para un pilar específico es escasa (ej. una única línea en el cuestionario: *"Contamos con SAI y grupo electrógeno"* y 0 menciones en las transcripciones), la restricción de "mínimo 400 palabras forenses" fuerza al modelo a proyectar su distribución de probabilidad latente sobre estándares de la industria para rellenar el espacio. El resultado es la invención de especificaciones técnicas plausibles pero falsas (`"UPS de 60 kVA"`, `"Generador de 250 kVA"`, `"37 kW por sala"`, `"Door Fan Test caducado"`). El motor confunde *estilo forense* con *invención de pruebas*.

### 1.3. Pecado Capital 3: Inconsistencia Matemática Aparente en Tarjetas de Riesgo (`payload_to_ast.py` / `tomo_asis_ast_compiler.py`)
* **Mecánica del Fallo:** El motor actuarial calcula correctamente el riesgo individual bruto ($\text{ALE}_{\text{raw}} = \text{SLE} \times \text{Freq}$) y posteriormente aplica un modelo de agregación de portafolio mediante Cópulas (Gaussiana/t-Student) y asignación de capital por el Principio de Euler para obtener el riesgo neto diversificado ($\text{ALE}_{\text{net}}$).
* **Fallo de Compilación AST:** Al serializar el objeto de riesgo hacia el Abstract Syntax Tree (AST) del documento Word, el compilador mapea $\text{SLE}_{\text{raw}}$ (`282.500 €`) y $\text{Freq}_{\text{raw}}$ (`0.15`), pero en la celda de resultado final imprime directamente el $\text{ALE}_{\text{net}}$ (`34.246 €`) omitiendo el $\text{ALE}_{\text{raw}}$ (`42.375 €`) y el factor de descuento por diversificación (`-19.18%`). Para cualquier Director Financiero (CFO) o auditor que lea la tabla, $282.500 \times 0.15 \neq 34.246$, destruyendo instantáneamente la credibilidad matemática de todo el informe.

---

## 2. LA FUNDACIÓN EPISTÉMICA UNIVERSAL (REGLAS ARQUITECTÓNICAS)

Para erradicar estos problemas a nivel de raíz, se establecen cuatro Leyes Arquitectónicas Inmutables en el motor:

### 2.1. Ley de Supremacía Empírica Declarada (Rule of Declared Supremacy)
La nota base (Baseline Score) calculada matemáticamente a partir de las respuestas explícitas del cliente en el cuestionario de evaluación es **SAGRADA E INMUTABLE POR EL TEXTO DEL LLM**.
* El código Python (`score_reconciler.py`) tiene **terminantemente prohibido** alterar, degradar o recalibrar un score basándose en el análisis de sentimiento, conteo de palabras clave o inferencias extraídas del texto generado por el LLM.
* **Única Excepción de Recalibración (Evidencia Contradictoria Intra-Dominio):** Una nota declarada solo puede ser modificada si existe una **Evidencia Forense Contradictoria Explícita** en las transcripciones de las entrevistas que pertenezca **al mismo subdominio exacto** ($T_x.P_y$). Esta contradicción no se detecta por Regex sobre el output del LLM, sino mediante un paso previo, determinista y estructurado de validación de evidencias (`EvidenceVerificationEngine`) que requiere citar literalmente (verbatim) el fragmento de la transcripción que contradice el cuestionario. Si no hay cita literal contradictoria en la transcripción para ese pilar, $\text{Score}_{\text{Final}} \equiv \text{Score}_{\text{Cuestionario}}$.

### 2.2. Ley de Densidad Epistémica Proporcional (Rule of Epistemic Density)
El volumen de texto generado por el LLM debe ser una función matemática estricta de la cantidad de información empírica disponible (Entropía de la Evidencia).
* Se introduce el **Índice de Densidad de Evidencia ($\text{EDI}$)** por cada pilar $T_x.P_y$, calculado en Python antes de invocar al LLM:
  $$\text{EDI}(T_x.P_y) = W_{\text{survey}}(T_x.P_y) + W_{\text{transcripts}}(T_x.P_y)$$
  Donde $W$ es el conteo de palabras (tokens informativos limpios) de las respuestas del cuestionario y de los fragmentos de transcripción mapeados exclusivamente a ese pilar.
* El prompt del `UniversalTowerSynthesizer` ajustará dinámicamente su restricción de longitud y su directiva epistémica según tres regímenes:
  * **Régimen 1: Evidencia Escasa ($\text{EDI} < 40$ palabras):** Directiva de *Síntesis Ejecutiva Sobria*. Longitud máxima permitida: **100 - 150 palabras**. Prohibición explícita de asumir arquitecturas subyacentes. El LLM debe declarar explícitamente el límite de observación (ej. *"El alcance documental proporcionado para este pilar se limita a la declaración de control base, sin desglose de capacidades nominales..."*).
  * **Régimen 2: Evidencia Moderada ($40 \le \text{EDI} < 150$ palabras):** Directiva de *Análisis Técnico Estándar*. Longitud permitida: **150 - 250 palabras**.
  * **Régimen 3: Evidencia Densa ($\text{EDI} \ge 150$ palabras):** Directiva de *Auditoría Forense Profunda*. Longitud permitida: **300 - 450 palabras**.

### 2.3. Ley de Segregación Estricta de Dominios (Rule of Strict Domain Segregation)
Cada Torre ($T_1 \dots T_{10}$) y cada Pilar ($P_1 \dots P_n$) constituye un espacio vectorial de evaluación ortogonal.
* El contexto inyectado al LLM al sintetizar $T_x.P_y$ solo contendrá evidencias etiquetadas taxonómica y exclusivamente para $T_x.P_y$.
* Se prohíbe al LLM utilizar la ausencia de un control en la Torre $B$ (ej. DRP en $T_5$) como argumento de degradación arquitectónica en la Torre $A$ (ej. Protección contra Incendios en $T_1$). Si existe una dependencia arquitectónica relevante, el LLM puede añadir una nota de *"Referencia Cruzada Informativa"* al final del párrafo, la cual tendrá **peso cero (0.00)** en el cálculo de madurez de la Torre $A$.

### 2.4. Ley de Transparencia Actuarial Absoluta (Rule of Actuarial Transparency)
Ninguna cifra financiera agregada o ajustada estocásticamente puede imprimirse en un informe sin mostrar la ecuación completa que la origina.
* Toda tarjeta de riesgo y tabla financiera en el AST debe desglosar explícitamente la cascada de valoración en cuatro componentes obligatorios:
  1. **Exposición Singular Bruta ($\text{SLE}$)** y **Frecuencia Anualizada ($\text{ARO / Freq}$)**.
  2. **Pérdida Anual Esperada Intrínseca ($\text{ALE Bruto} = \text{SLE} \times \text{Freq}$)**.
  3. **Ajuste por Diversificación de Cópula / Efecto Cartera ($\Delta_{\text{Copula}}$ en $€$ y $\%$)**.
  4. **Pérdida Anual Esperada Neta Retenida ($\text{ALE Neto} = \text{ALE Bruto} - \Delta_{\text{Copula}}$)**.

---

## 3. PLAN DE EJECUCIÓN DE DESARROLLO PASO A PASO (IMPLEMENTATION BLUEPRINT)

El agente de implementación (`Gemini 3.8`) ejecutará las siguientes modificaciones secuenciales en el repositorio.

---

### PASO 1: Desacoplamiento del Score y Erradicación de Heurísticas Regex
**Archivo Objetivo:** `src/engine/scoring/score_reconciler.py` (y referencias en el pipeline de orquestación).

#### 1.1. Eliminación de Código Táctico/Defectuoso
* **Acción:** Eliminar por completo todas las funciones que utilicen expresiones regulares (`re.search`, `re.findall`) o listas de palabras negativas (`NEGATIVE_KEYWORDS`, `PENALTY_TRIGGERS`) sobre el texto generado por el LLM para modificar scores.
* **Acción:** Eliminar cualquier lógica de *Hard-Capping* automático basada en la narrativa sintetizada.

#### 1.2. Implementación del Nuevo `ImmutableScoreReconciler`
Reemplazar la lógica existente por una arquitectura basada en contratos de datos (Pydantic). El reconciliador ya no se ejecuta *después* de la narrativa del LLM para cambiar la nota, sino *antes* de la narrativa, utilizando exclusivamente datos crudos.

```python
# src/engine/scoring/score_reconciler.py
from pydantic import BaseModel, Field
from typing import Optional, List

class ContradictoryEvidence(BaseModel):
    pillar_id: str
    transcript_source_id: str
    verbatim_quote: str = Field(..., min_length=20)
    contradiction_rationale: str
    suggested_score_override: float = Field(..., ge=1.0, le=5.0)
    domain_match_verified: bool

class PillarScoreResolution(BaseModel):
    pillar_id: str
    declared_score: float
    final_score: float
    is_overridden: bool = False
    override_audit_trail: Optional[str] = None

class ImmutableScoreReconciler:
    """
    Garantiza la Ley de Supremacía Empírica Declarada y Segregación de Dominios.
    """
    @staticmethod
    def resolve_pillar_score(
        pillar_id: str,
        declared_score: float,
        verified_contradictions: List[ContradictoryEvidence]
    ) -> PillarScoreResolution:
        # Filtrar estrictamente por coincidencia exacta de pillar_id (Ej: "T1.P4" == "T1.P4")
        # y verificación de dominio positiva.
        valid_contradictions = [
            c for c in verified_contradictions 
            if c.pillar_id == pillar_id and c.domain_match_verified is True and len(c.verbatim_quote.strip()) > 0
        ]

        if not valid_contradictions:
            # LEY DE SUPREMACÍA: Sin evidencia forense literal contradictoria en el mismo dominio,
            # la nota declarada en el cuestionario es INMUTABLE.
            return PillarScoreResolution(
                pillar_id=pillar_id,
                declared_score=declared_score,
                final_score=round(declared_score, 2),
                is_overridden=False,
                override_audit_trail="Score anclado estrictamente a la declaración empírica del cuestionario."
            )

        # Si existe contradicción empírica verificada en transcripción del mismo dominio:
        primary_conflict = valid_contradictions[0]
        return PillarScoreResolution(
            pillar_id=pillar_id,
            declared_score=declared_score,
            final_score=round(primary_conflict.suggested_score_override, 2),
            is_overridden=True,
            override_audit_trail=(
                f"Ajuste intra-dominio aplicado. Declarado: {declared_score:.2f}. "
                f"Evidencia contradictoria en [{primary_conflict.transcript_source_id}]: "
                f"'{primary_conflict.verbatim_quote}' -> {primary_conflict.contradiction_rationale}"
            )
        )
```

---

### PASO 2: Implementación del Calculador de Densidad Epistémica y Anti-Alucinación
**Archivo Objetivo:** `src/engine/synthesizers/universal_tower_synthesizer.py` (y sus plantillas de prompts asociadas).

#### 2.1. Cálculo Previo del Índice de Densidad de Evidencia (EDI)
Añadir un método determinista en Python dentro de `UniversalTowerSynthesizer` que mida el volumen exacto de evidencia cruda disponible para un pilar antes de construir el prompt.

```python
# Fragmento a inyectar en src/engine/synthesizers/universal_tower_synthesizer.py
import re
from dataclasses import dataclass

@dataclass
class EpistemicConstraint:
    edi_word_count: int
    regime: str  # "SPARSE", "MODERATE", "DENSE"
    target_word_range: str
    max_tokens: int
    epistemic_directive: str

class EpistemicDensityController:
    @staticmethod
    def calculate_constraints(survey_raw_text: str, transcript_chunks: list[str]) -> EpistemicConstraint:
        combined_text = f"{survey_raw_text} {' '.join(transcript_chunks)}".strip()
        words = re.findall(r'\b\w+\b', combined_text)
        word_count = len(words)

        if word_count < 40:
            return EpistemicConstraint(
                edi_word_count=word_count,
                regime="SPARSE",
                target_word_range="100 a 150 palabras",
                max_tokens=300,
                epistemic_directive=(
                    "MODO DE EVIDENCIA ESCASA ACTIVADO: La evidencia empírica proporcionada para este pilar "
                    f"es mínima ({word_count} palabras). Redacte un resumen ejecutivo sobrio y directo de "
                    "ENTRE 100 Y 150 PALABRAS. QUEDA TERMINANTEMENTE PROHIBIDO inventar, inferir o extrapolar "
                    "cifras técnicas, capacidades en kVA/kW, modelos de hardware, fechas de caducidad de pruebas "
                    "(ej. Door Fan Test) o topologías no mencionadas literalmente en el bloque de evidencia. "
                    "Declare explícitamente qué confirma el cliente y señale que no se aportaron especificaciones "
                    "de detalle adicionales en la fase de captura."
                )
            )
        elif word_count < 150:
            return EpistemicConstraint(
                edi_word_count=word_count,
                regime="MODERATE",
                target_word_range="150 a 250 palabras",
                max_tokens=500,
                epistemic_directive=(
                    "MODO DE EVIDENCIA MODERADA ACTIVADO: Redacte un análisis técnico objetivo de "
                    "ENTRE 150 Y 250 PALABRAS ciñéndose estrictamente a los hechos declarados. No invente "
                    "métricas ni especificaciones de equipamiento que no figuren literalmente en la evidencia."
                )
            )
        else:
            return EpistemicConstraint(
                edi_word_count=word_count,
                regime="DENSE",
                target_word_range="300 a 450 palabras",
                max_tokens=900,
                epistemic_directive=(
                    "MODO DE EVIDENCIA DENSA ACTIVADO: Existe abundante evidencia empírica. Desarrolle una "
                    "auditoría técnica detallada de ENTRE 300 Y 450 PALABRAS, citando las métricas y hechos "
                    "exactos presentes en el contexto, manteniendo fidelidad absoluta a los datos de entrada."
                )
            )
```

#### 2.2. Refactorización del Prompt del Sistema en `UniversalTowerSynthesizer`
Modificar la plantilla de prompt del sintetizador de torres para inyectar:
1. El `final_score` ya bloqueado e inmutable (calculado en el Paso 1).
2. La directiva `epistemic_directive` dinámica (calculada en el Paso 2.1).
3. La cláusula de **Aislamiento de Dominio (Firewall Taxonómico)**.

**Nueva Estructura del Prompt de Síntesis (Obligatoria):**
```text
[SISTEMA - REGLAS DE INTEGRIDAD FORENSE INQUEBRANTABLES]
1. INMUTABILIDAD DE PUNTUACIÓN: La puntuación oficial y definitiva para el pilar {pillar_id} ({pillar_name}) es {final_score}/5.00. Su narrativa DEBE justificar y ser coherente con esta nota exacta. No puede sugerir una nota distinta.
2. CERO ALUCINACIÓN DE ESPECIFICACIONES (ZERO-SPEC FABRICATION): Si la evidencia de entrada dice "existe un SAI", usted escribirá "se confirma la existencia de un sistema SAI". Si usted escribe "un SAI de 60 kVA" sin que el número "60" esté en la evidencia de entrada, cometerá una violación grave de auditoría. Prohibido inventar capacidades (kW, kVA, Gbps), marcas, modelos o estados de certificaciones/pruebas no declarados.
3. AISLAMIENTO ESTRICTO DE DOMINIO (DOMAIN FIREWALL): Usted está evaluando EXCLUSIVAMENTE {tower_id} -> {pillar_id} ({pillar_name}). Queda PROHIBIDO criticar o penalizar este pilar por carencias que pertenecen a otras torres tecnológicas (ejemplo: prohibido penalizar Protección contra Incendios T1.P4 por la falta de un DRP de TI, ya que el DRP pertenece a T5 Resiliencia).
4. RESTRICCIÓN DINÁMICA DE VOLUMEN: {epistemic_directive}
```

#### 2.3. Validador Post-Generación de Entidades Numéricas (`NumericHallucinationGuard`)
Crear un filtro determinista ligero en `src/engine/validators/hallucination_guard.py` que se ejecute inmediatamente después de recibir la respuesta del LLM en `UniversalTowerSynthesizer`:
* Extrae todas las secuencias de `Número + Unidad Técnica` del texto generado por el LLM mediante Regex: `\b\d+(?:[.,]\d+)?\s*(?:kVA|kW|MW|Gbps|Mbps|TB|PB|horas|ms|dB|%)\b`.
* Verifica que cada magnitud técnica encontrada en el output del LLM exista en el texto de la evidencia de entrada de ese pilar (o corresponda al score / porcentajes derivados del score).
* Si el LLM genera `"60 kVA"` y `"60"` no está en la evidencia de entrada del pilar, el validador rechaza la generación y re-ejecuta la llamada al LLM con `temperature=0.0` inyectando una alerta de violación: `"ERROR CRÍTICO: Usted ha inventado las siguientes métricas no presentes en la evidencia: {fabricated_metrics}. Elimínelas inmediatamente."`

---

### PASO 3: Transparencia Matemática en el Motor Actuarial y Compilador AST
**Archivos Objetivo:**
* `src/engine/actuarial/risk_engine.py` (o donde se instancie el modelo de datos de las Risk Cards).
* `src/compiler/payload_to_ast.py`
* `src/compiler/tomo_asis_ast_compiler.py`

#### 3.1. Expansión del Contrato de Datos Actuarial
Asegurar que el diccionario o modelo Pydantic que representa cada tarjeta de riesgo exporte explícitamente los valores pre- y post-cópula, verificando la identidad contable antes de serializar.

```python
# En el generador del payload actuarial (ej. risk_engine.py / payload_to_ast.py)
class ActuarialRiskCardPayload(BaseModel):
    risk_id: str
    title: str
    tower_id: str
    sle_eur: float
    aro_freq: float
    ale_gross_eur: float          # DEBE SER EXACTAMENTE round(sle_eur * aro_freq, 2)
    copula_discount_eur: float    # Positivo, representa el ahorro por diversificación (ale_gross - ale_net)
    copula_discount_pct: float    # Porcentaje de diversificación: ((ale_gross - ale_net) / ale_gross) * 100
    ale_net_euler_eur: float      # Valor final asignado por Euler

    def validate_accounting_identity(self) -> None:
        expected_gross = round(self.sle_eur * self.aro_freq, 2)
        if abs(self.ale_gross_eur - expected_gross) > 1.0:
            self.ale_gross_eur = expected_gross
        self.copula_discount_eur = round(self.ale_gross_eur - self.ale_net_euler_eur, 2)
        if self.ale_gross_eur > 0:
            self.copula_discount_pct = round((self.copula_discount_eur / self.ale_gross_eur) * 100, 2)
        else:
            self.copula_discount_pct = 0.0
```

#### 3.2. Refactorización de la Tabla de Riesgo en el Compilador AST (`payload_to_ast.py` y `tomo_asis_ast_compiler.py`)
Localizar la función que construye los nodos de tabla AST para las Tarjetas de Riesgo (Risk Cards) y la Tabla Resumen Financiera. Reemplazar la estructura de 3 columnas (`SLE | Freq | ALE`) por el nuevo estándar de **Desglose Actuarial Transparente de 5 Parámetros**:

**Estructura Obligatoria de Renderizado en la Tarjeta de Riesgo (Word/AST):**

| Parámetro Actuarial | Valor Cuantificado | Nota Metodológica |
| :--- | :---: | :--- |
| **Exposición Singular Bruta (SLE)** | `282.500 €` | Impacto directo estimado por evento materializado |
| **Frecuencia Anualizada (ARO)** | `0,15 eventos/año` | Probabilidad empírica calibrada según madurez del control |
| **Pérdida Anual Esperada Intrínseca (ALE Bruto)** | **`42.375 € / año`** | *Cálculo directo lineal ($\text{SLE} \times \text{ARO}$)* |
| **Ajuste por Diversificación de Cartera (Cópula)** | `-8.129 € (-19,18%)` | *Mitigación por incorrelación estocástica (Asignación de Euler)* |
| **Riesgo Neto Retenido en Cartera (ALE Neto)** | **`34.246 € / año`** | **Contribución marginal real al VaR operativo global** |

* **Nota de Implementación en `payload_to_ast.py`:** Actualizar los diccionarios de filas de la tabla AST de cada riesgo para que incluyan las filas `ALE Bruto (SLE x ARO)`, `Ajuste Diversificación Cópula` y `ALE Neto (Euler)`.
* **Nota de Implementación en `tomo_asis_ast_compiler.py`:** Asegurar que si existe una tabla resumen consolidada de riesgos al inicio o final del documento, esta contenga las columnas: `ID | Riesgo | SLE (€) | ARO | ALE Bruto (€) | Desc. Cópula (%) | ALE Neto (€)`, de modo que la suma de la columna `ALE Neto (€)` coincida exactamente con el ALE Total Diversificado de la compañía reportado en el Resumen Ejecutivo.

---

## 4. PROTOCOLO DE VERIFICACIÓN Y CRITERIOS DE ACEPTACIÓN (QA GATE)

Antes de dar por cerrada la tarea, el agente de implementación (`Gemini 3.8`) deberá ejecutar la suite de pruebas de regresión verificando las siguientes aserciones automatizadas (`tests/test_epistemic_integrity.py`):

1. **Test de Inmutabilidad Declarada (`test_declared_score_supremacy`):**
   * *Input:* Cuestionario con `T1.P4 = 4.00`. Transcripción sin menciones a `T1.P4`, pero con mención a `"No tenemos DRP"` en `T5`.
   * *Resultado Esperado:* El score final de `T1.P4` es exactamente `4.00`. Ninguna función altera este valor.
2. **Test de Control de Densidad y Cero Alucinación (`test_sparse_evidence_no_hallucination`):**
   * *Input:* Pilar con 12 palabras de evidencia (`"Disponen de SAI y grupo electrógeno con mantenimiento anual contratado"`).
   * *Resultado Esperado:* El controlador activa el régimen `SPARSE`. El texto generado tiene entre 100 y 150 palabras y el `NumericHallucinationGuard` certifica `0` unidades técnicas inventadas (ausencia total de `kVA`, `kW`, etc.).
3. **Test de Identidad Contable Actuarial (`test_actuarial_card_transparency`):**
   * *Input:* Riesgo con `SLE = 282500`, `ARO = 0.15`, `ALE_Net = 34246`.
   * *Resultado Esperado:* El nodo AST de la tarjeta contiene literalmente los strings `"42.375 €"` (ALE Bruto), `"-8.129 €"` o `"-19,18%"` (Ajuste Cópula) y `"34.246 €"` (ALE Neto).

---
*Fin de la Especificación Arquitectónica. Proceda con la implementación secuencial.*
```