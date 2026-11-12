# PLAN MAESTRO DE REMEDIACIÓN ARQUITECTÓNICA Y EPISTÉMICA UNIVERSAL (TIER-1)
**Versión:** 2.0 (Aprobada por Red Team — Orientada a Decisión de CTO / IT)  
**Ruta:** `docs/architecture/UNIVERSAL_EPISTEMIC_REMEDIATION_PLAN.md`  
**Estado:** DEFINITIVO / LISTO PARA IMPLEMENTACIÓN  
**Objetivo:** Erradicar de raíz en todo el motor las alucinaciones de inventario, el tampeo injustificado de notas de madurez y la opacidad matemática en los entregables de cualquier cliente.

---

## 0. RESUMEN EJECUTIVO Y CRITERIO DIRECTIVO

Una evaluación de arquitectura tecnológica debe ser una herramienta de decisión transparente para el Director de TI y el CTO, no un ejercicio de fiscalía hostil ni una caja negra actuarial incomprensible.

Este plan maestro establece la arquitectura definitiva para garantizar:
1. **Fidelidad Absoluta a las Respuestas del Cliente:** Las notas del cuestionario son la verdad canónica inicial; el silencio en las notas de entrevista nunca devalúa una nota.
2. **Cero Alucinaciones de Hardware:** Prohibición absoluta de inventar especificaciones técnicas de placa (kVA, kW, modelos no declarados).
3. **Independencia Estricta de Dominios:** La evaluación de un control (ej. Incendios en T1) jamás puede ser penalizada por deficiencias de otra torre (ej. DRP en T5).
4. **Aritmética Transparente de Servilleta (Cero Jerga Actuarial):** Cada ficha de riesgo debe cuadrar a simple vista con una multiplicación básica:  
   $$\text{Impacto Anualizado Directo} = \text{Frecuencia Anual} \times \text{Coste por Incidente}$$  
   El solapamiento multirriesgo se explica al final en lenguaje llano de ingeniería como *"Ajuste por simultaneidad de caídas"*, desterrando términos ajenos al mundo IT como Cópulas o Asignación de Euler.

---

## 1. CAUSAS RAÍZ Y ERRORES SISTÉMICOS IDENTIFICADOS

### 1.1. Tampeo de Puntuaciones por Regex en `score_reconciler.py`
* **El Problema:** El código escaneaba el texto generado por el LLM buscando palabras como `"absence"` o `"ad-hoc"`. Al encontrar que el LLM mencionaba la falta de un DRP en el texto de Incendios (T1), el motor penalizaba automáticamente la nota de 4,00 a 1,75.
* **La Solución:** Erradicar cualquier modificación de notas basada en expresiones regulares sobre el texto del LLM. Las notas se resuelven de forma determinista antes de la redacción.

### 1.2. Alucinación Forense por Presión de Volumen
* **El Problema:** El prompt exigía un mínimo de 400 palabras técnicas por pilar. Cuando el cliente solo aportó una frase en la entrevista, el LLM se vio obligado a inventar detalles plausibles pero falsos (`"SAI de 60 kVA"`, `"generador de 250 kVA"`, `"37 kW por sala"`, `"Door Fan Test caducado"`).
* **La Solución:** Prohibir la invención de especificaciones físicas. Si no hay datos de placa, la redacción se enfoca en explicar el impacto operativo del nivel de madurez declarado, sin inventar activos que el cliente no tiene.

### 1.3. Discrepancia Aritmética Aparente en Fichas de Riesgo
* **El Problema:** La ficha imprimía el impacto por caída ($SLE = 282.500\text{ €}$) y la frecuencia ($0,15/\text{año}$), pero mostraba un impacto anual ($ALE = 34.246\text{ €}$) en lugar de $42.375\text{ €}$, porque aplicaba internamente un descuento de portafolio sin explicarlo al lector.
* **La Solución:** En cada ficha individual se imprime la multiplicación directa exacta. El ajuste de simultaneidad se aplica y explica de forma agregada en la tabla resumen del informe.

---

## 2. LAS 4 LEYES ARQUITECTÓNICAS RECALIBRADAS

### LEY 1: Jerarquía de Verdad y Protección de la Declaración del Cliente
1. **Línea Base Canónica:** La nota declarada en el cuestionario de evaluación (`261014_Respuestas_Test_Molins.txt`) es la base inicial inmutable.
2. **Neutralidad del Silencio:** Si un aspecto técnico no se menciona en las entrevistas, se mantiene íntegra la nota declarada en la encuesta. El silencio documental jamás se interpreta como fallo operativo.
3. **Protocolo de Contradicción Técnica:** Una nota declarada solo puede recalibrarse si existe una **cita textual explícita en las entrevistas del mismo dominio exacto** que demuestre que el control no opera como se declaró. En tal caso, el informe debe documentar con transparencia el motivo técnico del ajuste.

### LEY 2: Fidelidad Técnica sin Invención de Topología
1. **Modo con Evidencia Directa:** Cuando existan datos verificados en la entrevista (ej. 6 nodos SimpliVity, 2 CPDs a 500m, NetApp activo/activo), el texto detalla con precisión esos componentes reales.
2. **Modo con Evidencia Limitada:** Cuando solo se disponga de la respuesta del cuestionario, el texto:
   * Confirma y valida el control declarado por el cliente.
   * Explica los beneficios operativos de ese nivel de madurez y los riesgos típicos que previene en la industria.
   * **Prohibición Total:** Queda terminantemente prohibido inventar potencias eléctricas, modelos de hardware, marcas de software o resultados de ensayos que no consten en las fuentes.

### LEY 3: Independencia de Controles vs. Conexión de Impacto Operativo
1. **Evaluación Ortogonal de Madurez:** La nota de madurez de cada pilar evalúa exclusivamente la solidez de ese control técnico específico. Que una empresa no tenga DRP (Torre 5) no reduce la nota de sus sistemas de extinción de incendios (Torre 1).
2. **Modelado de Impacto Sistémico:** La interdependencia entre torres solo interviene al estimar la duración del impacto: si las salas físicas (T1) fallan, el tiempo de recuperación del negocio se calcula considerando si los sistemas tienen capacidad de conmutación (T5).

### LEY 4: Aritmética Transparente de Servilleta (Cero Jerga Actuarial)

#### 4.1 Fichas de Riesgo Individuales (Coherencia Visual Inmediata)
Cada ficha técnica muestra únicamente tres métricas financieras primarias que cualquier CTO puede verificar mentalmente:
* **Frecuencia Estimada:** Veces que puede ocurrir al año (ej. `0,15 / año` $\to$ aprox. 1 vez cada 6,5 años).
* **Coste por Incidente:** Impacto económico directo de una (1) caída (horas de parada $\times$ coste de inactividad + costes de recuperación técnica).
* **Impacto Anualizado Directo:** **Exactamente el producto de Frecuencia $\times$ Coste por Incidente.** Sin descuentos ocultos.
* **Escenario Crítico (Peor Caso Plausible):** Estimación de coste ante una parada en momentos de máxima producción (sustituye al término técnico VaR 95%).

#### 4.2 Tabla Resumen de Portafolio (Ajuste por Simultaneidad)
La agregación financiera se presenta en la tabla ejecutiva de cierre mediante tres conceptos comprensibles:
1. **Suma de Riesgos Individuales (Exposición Bruta Directa):** Suma aritmética de las fichas individuales.
2. **Ajuste por Simultaneidad y Dependencia IT:** Descuento transparente con explicación técnica:  
   *«Ajuste aplicado debido a que múltiples incidentes técnicos comparten la misma ventana de parada; ante una caída de la infraestructura base, los aplicativos dependientes ya están detenidos y el coste por hora de inactividad no se contabiliza de forma duplicada».*
3. **Exposición Anual Neta Consolidada:** Presupuesto de riesgo realista del grupo empresarial.

---

## 3. PLAN DE DESARROLLO E IMPLEMENTACIÓN PASO A PASO

### FASE 1: Saneamiento del Motor de Scoring (`score_reconciler.py`)
* **Archivo:** `src/assessment_engine/domain/services/score_reconciler.py`
* **Acción:**
  1. Eliminar la búsqueda por regex de palabras negativas (`_ABSENCE_PATTERNS`) sobre el texto del LLM.
  2. Implementar `ImmutableScoreReconciler`, asegurando que la nota de cada pilar provenga del cuestionario original salvo contradicción textual explícita en las transcripciones del mismo dominio.
  3. Restituir las notas originales de Molins (T1 global en 2,61; T1.P4 Incendios en 4,00).

### FASE 2: Adaptación de Prompts en `PillarForensicSynthesizer`
* **Archivo:** `src/assessment_engine/application/services/synthesis/pillar_synthesizer.py`
* **Acción:**
  1. Inyectar la directiva de *Fidelidad Técnica sin Invención*: prohibir explícitamente generar números de kVA, kW, modelos no declarados o inventar ensayos de estanqueidad.
  2. En pilares con baja evidencia documental, guiar al modelo para describir el impacto operativo estándar sin inventar topologías ficticias.
  3. Mantener el tono consultivo sénior y constructivo (cero términos punitivos o despectivos).

### FASE 3: Aritmética Directa en Fichas del Compilador AST
* **Archivos:** `src/assessment_engine/adapters/compilers/payload_to_ast.py` y `tomo_asis_ast_compiler.py`
* **Acción:**
  1. En las fichas de riesgo de los 10 anexos, imprimir:  
     $$\text{ALE Ficha} = \text{SLE} \times \text{Frecuencia}$$  
     garantizando que la multiplicación cuadre al céntimo.
  2. En la Tabla 5 del Tomo 1 y resúmenes ejecutivos, presentar la conciliación en tres líneas: *Suma de Riesgos Aislados*, *Ajuste por Simultaneidad IT* y *Exposición Anual Neta Consolidada*.

### FASE 4: Re-generación y Re-compilación de los 11 Entregables
* **Acción:**
  1. Actualizar los payloads de las 10 torres con las notas y riesgos reconciliados bajo el nuevo estándar.
  2. Recompilar los 10 Anexos Técnicos y el Tomo 1 Consolidado.
  3. Ejecutar los tests de validación matemática y empaquetar el ZIP final.

---

**Criterio de Éxito Definitivo:**  
Ninguna cifra de ficha técnica descuadra con una calculadora básica, ninguna nota de cliente es degradada por falta de pruebas, ningún hardware es inventado, y el informe transmite un rigor técnico intachable para cualquier cliente en el mundo.
