# INFORME DE AUDITORÍA RED TEAM: EVALUACIÓN ADVERSARIAL DEL PLAN DE REMEDIACIÓN EPISTÉMICA
**Auditor:** `gemini-4-argon` (Principal IT Auditor & Red Team Lead)  
**Objetivo:** `docs/architecture/UNIVERSAL_EPISTEMIC_REMEDIATION_PLAN.md`  
**Estado del Plan Actual:** **RECHAZADO PARCIALMENTE — RIESGO CRÍTICO DE SOBREINGENIERÍA Y FRICCIÓN COGNITIVA**

---

## 1. ANÁLISIS FORENSE DE LA REGLA 4: LA FALACIA ACTUARIAL Y EL RECHAZO DEL CTO

La intuición del usuario es **100% acertada**. La Regla 4 tal como está redactada en el borrador actual es un **anti-patrón arquitectónico severo**. Intentar justificar discrepancias matemáticas escupiendo jerga de seguros (*"Ajuste por Cópula de Gumbel"*, *"Asignación de Capital de Euler"*, *"Varianza estocástica"*) en un informe dirigido a un CTO, CISO o Director de IT es garantía de que **cierren el informe y desconfíen de la herramienta**.

### 1.1 ¿Por qué falla el enfoque actual?
1. **Alienación de la Audiencia:** Un CTO piensa en **Tiempo de Caída (Downtime), SLA, RPO/RTO, Coste de Recuperación y Presupuesto de IT**. No piensa en reservas de capital de Solvencia II. Si ve una fórmula actuarial incomprensible, asume que el software está usando "caja negra matemática" para inflar o desinflar números arbitrariamente.
2. **La Verdadera Causa Raíz del Descuadre Matemático:** El problema en los informes actuales no es la falta de fórmulas complejas; es una **violación de la aritmética básica en la interfaz**. 
   - Si una tarjeta muestra: `Frecuencia: 0.45/año (1 cada 2.2 años)` y `Impacto por caída (SLE): 100.000 €`.
   - El CTO multiplica mentalmente en 2 segundos: `0.45 × 100.000 € = 45.000 €/año`.
   - Si debajo el sistema imprime: `Exposición Anual (ALE): 63.012 €` (porque internamente sumó colas de distribución o penalizaciones ocultas) o `28.400 €` (porque aplicó un descuento por solapamiento sin avisar), **el CTO concluye que la calculadora está rota**.

### 1.2 La Regla de Oro para IT: "Aritmética Transparente de Servillo"
¿No es siempre `ALE = Frecuencia × Impacto`? **En la vista individual de un activo o riesgo, SÍ DEBE SERLO.** 

Si el motor Monte Carlo simula curvas complejas (Log-Normal, Pareto), el resultado que se imprime en la ficha técnica debe ser **aritméticamente coherente a simple vista**:
*   **En cada ficha de riesgo individual:** Mostramos el **Riesgo Directo Aislado**. Si la frecuencia es `F` y el impacto medio por incidente es `I`, la pérdida anual esperada de ese bloque **tiene que ser exactamente `F × I`**. Sin trucos.
*   **¿Dónde va el solapamiento o efecto cascada (lo que antes llamábamos Cópula/Euler)?** Va **al final del documento**, en el Resumen Financiero Global, explicado en **lenguaje llano de ingeniería**: *"Descuento por simultaneidad de caídas (si la red cae, el ERP ya está inoperativo; no se duplica el coste por hora de parada)"* o *"Recargo por fallo en cascada"*.

---

## 2. ESCRUTINIO RED TEAM DE LAS REGLAS 1, 2 Y 3

Antes de reescribir el estándar, auditamos las otras tres leyes propuestas para detectar vulnerabilidades de diseño que podrían romper el motor en producción.

### Vulnerabilidad en Regla 1 (Supremacía del Dato Declarado)
*   **El Riesgo ("El Síndrome del Cuestionario Optimista"):** Es muy común que un cliente marque en la encuesta previa un `5/5 (Óptimo)` en Backups por desconocimiento, pero en la entrevista con el consultor confiese: *"Bueno, hacemos copia en un NAS local pero nunca hemos probado a restaurarla ni está desconectada de la red"*.
*   **Fallo del Plan Actual:** Si aplicamos "Supremacía Absoluta del Dato Declarado", el motor ignorará la confesión crítica de la entrevista y mantendrá el `5/5`, generando un falso negativo gravísimo en auditoría.
*   **Solución Red Team (Jerarquía de Evidencia Auditada):**
    1. **Prioridad 1 (Máxima):** *Contradicción Explícita en Entrevista* (el texto del consultor demuestra con hechos técnicos que la encuesta era errónea). El LLM debe estar autorizado a rebajar la nota **SOLO SI cita textualmente el hecho técnico contradictorio** (ej. *"Aunque el cuestionario inicial indicaba madurez alta, se constata en entrevista técnica la ausencia de copias inmutables"*).
    2. **Prioridad 2:** *Dato Declarado en Cuestionario (`numeric_value`)*.
    3. **Prioridad 3 (Prohibido usar para degradar):** *Silencio u omisión en las notas*. El silencio NUNCA degrada una nota declarada.

### Vulnerabilidad en Regla 2 (Índice de Densidad Epistémica - EDI)
*   **El Riesgo ("Truncamiento Robótico"):** Imponer un límite estricto de palabras (`Máx 150 palabras` si `EDI < 0.25`) mediante validación dura hará que el LLM corte frases a la mitad, omita explicaciones técnicas necesarias de *por qué* un control es importante, o genere un PDF visualmente roto (páginas casi en blanco que parecen errores de maquetación).
*   **Solución Red Team (Control de Especulación, no de Palabras):**
    *   No limitar el conteo de palabras con una fórmula rígida, sino **restringir la especificidad inventada**.
    *   Si `EDI < 0.25` (solo hay encuesta sin detalles técnicos), el LLM **no puede inventar nombres de tecnologías, topologías ni procedimientos del cliente**, pero **SÍ puede y debe** explicar el impacto técnico estándar en la industria para ese nivel de madurez (ej. explicar por qué un nivel 2/5 en parches expone a vulnerabilidades críticas de día cero, manteniendo un tamaño de párrafo ejecutivo normal y profesional).

### Vulnerabilidad en Regla 3 (Segregación de Dominios vs. Efecto Cascada IT)
*   **El Riesgo ("Ceguera Sistémica"):** Aislar T1 (Instalaciones/Incendios) de T5 (Continuidad/DRP) y T10 (Aplicaciones Core) es correcto para **evaluar la madurez del control**, pero peligroso si impide ver la dependencia operativa. Si T1 se quema y no hay DRP en T5, el ERP en T10 muere.
*   **Solución Red Team (Aislamiento de Calificación, Conexión de Impacto):**
    *   **Calificación de Madurez (Score 1-5):** Estrictamente aislada por dominio. Que no tengas DRP (T5) no significa que tus extintores (T1) sean malos. T1 conserva su nota intacta.
    *   **Cálculo de Impacto Operativo (Downtime/SLE):** Conectado. El fallo físico de T1 utiliza el tiempo de recuperación definido en T5 para calcular cuántas horas estará caído el negocio.

---

## 3. ESPECIFICACIÓN DEFINITIVA APROBADA POR RED TEAM (LISTA PARA IMPLEMENTACIÓN)

A continuación se presenta la arquitectura recalibrada, libre de jerga esotérica y blindada contra alucinaciones, lista para ser inyectada en el código.

---

### LEY 1: Jerarquía de Verdad y Prohibición de Penalización por Silencio
1. **El Silencio es Neutro:** Si un bloque tiene respuestas en el cuestionario (`numeric_value`) pero las notas de la entrevista no mencionan ese bloque, el sistema **asume que el cuestionario es 100% veraz**. Queda terminantemente prohibido usar frases como *"No se aportaron evidencias adicionales"* para rebajar la nota o inflar el riesgo.
2. **Protocolo de Contradicción Técnica:** El motor IA solo puede desviarse de la nota del cuestionario si existe una **evidencia textual explícita en las notas del consultor** que contradiga el control. En ese caso, debe declarar explícitamente el motivo del ajuste en lenguaje técnico claro.

---

### LEY 2: Fidelidad Técnica sin Invención de Topología (Reemplaza al EDI Rígido)
En lugar de cortar la longitud del texto artificialmente, el motor adapta el **enfoque narrativo** según los datos disponibles:
*   **Modo Evidencia Directa (Con notas de entrevista/documentos):** Diagnóstico quirúrgico citando los activos reales mencionados por el cliente (nombres de servidores, marcas de firewalls, tiempos RTO declarados).
*   **Modo Diagnóstico por Madurez (Solo cuestionario, sin notas):** Prohibido inventar detalles de la infraestructura del cliente (prohibido asumir si usan cinta, cloud, MPLS o fibra). La narrativa debe centrarse en:
    1. Confirmar el estado declarado en el cuestionario (ej. *"La organización reporta un nivel de madurez 4/5 en redundancia eléctrica..."*).
    2. Explicar qué implica técnicamente ese nivel para la continuidad del negocio en un entorno IT estándar y qué pasos técnicos consolidan el nivel 5/5.

---

### LEY 3: Independencia de Controles vs. Dependencia de Caídas
1. **Evaluación de Controles (Scores):** Cada dominio (`T1` a `T13`) se evalúa exclusivamente con sus propias preguntas y evidencias. La falta de un Plan de Continuidad (T5) o de Copias de Seguridad (T6) **jamás** puede rebajar la puntuación de Seguridad Física (T1) o Climatización (T2).
2. **Traducción a Impacto de Negocio:** Cuando se calcula el coste de un incidente en infraestructura base (ej. caída eléctrica en T2), el tiempo de parada estimado sí tendrá en cuenta si la empresa dispone de contingencia operativa general, explicándolo como **"Tiempo estimado de indisponibilidad del servicio"**.

---

### LEY 4: Transparencia Financiera en Lenguaje IT/CTO (Cero Jerga Actuarial)

**Queda prohibido el uso de términos actuariales oscuros** en el informe (tales como *Cópula, Euler, VaR Estocástico, Prima Pura, Solvencia, Percentil Log-Normal*). Todo el modelo matemático interno se traduce a **Ingeniería Económica de IT comprensible en 5 segundos por un CTO**.

#### 4.1 Estructura Obligatoria de cada Ficha de Riesgo (Aritmética Directa)
En cada bloque o escenario de riesgo individual, los números mostrados **deben cuadrar mediante una multiplicación simple visible para el lector**:

| Concepto en el Informe (Lenguaje CTO) | Qué es realmente | Regla de Coherencia Visual |
| :--- | :--- | :--- |
| **1. Probabilidad / Frecuencia Estimada** | Veces que puede ocurrir al año (ej. `0.20 / año` → *aprox. 1 vez cada 5 años*). | Basado en la madurez de los controles técnicos del bloque. |
| **2. Coste Estimado por Incidente** | Lo que cuesta **una (1)** caída media de este tipo (horas de parada × coste/hora + recuperación técnica). | Explicado con causas técnicas tangibles (tiempo de indisponibilidad, restauración de sistemas, pérdida operativa). |
| **3. Impacto Anualizado Directo** | **Exactamente `(1) × (2)`**. | **DEBE CUADRAR AL EURO CON LA MULTIPLICACIÓN DE LOS DOS ANTERIORES.** Cero ajustes ocultos en la ficha individual. |
| **4. Escenario Crítico (Peor Caso Plausible)** | Coste si el incidente ocurre en el peor momento operativo (ej. caída prolongada en pico de facturación). | Sustituye al antiguo *"VaR 95% / 99%"*. Un CTO entiende inmediatamente qué es un *"Escenario Crítico de Caída Prolongada"*. |

#### 4.2 Cómo justificar la suma total del informe (El "Ajuste por Simultaneidad")
Si un informe tiene 10 bloques de riesgo y la suma simple de sus impactos anuales directos es `500.000 €/año`, pero el motor de simulación global calcula `380.000 €/año`, **no se oculta ni se llama "Asignación de Euler"**. Se presenta en una tabla clara de 3 líneas en el Resumen Ejecutivo:

1. **Suma de Exposiciones Individuales (Riesgos Aislados):** `500.000 € / año`
2. **Ajuste por Simultaneidad y Dependencias IT:** `-120.000 € / año`  
   *(Explicación clara al pie: "Descuento aplicado porque múltiples fallos técnicos comparten la misma ventana de parada operativa; si la infraestructura base cae, las aplicaciones dependientes ya están detenidas y el coste por hora de inactividad no se contabiliza dos veces").*
3. **Exposición Anual Neta Realista (Presupuesto de Riesgo IT):** **`380.000 € / año`**

---

## 4. VEREDICTO DEL AUDITOR Y PLAN DE ACCIÓN INMEDIATO

El cambio propuesto transforma el sistema de una **"Caja Negra Actuarial Incomprensible"** a una **"Herramienta de Decisión Ejecutiva para CTOs"**:

1. **Verificabilidad Instantánea:** Cualquier técnico o director de IT puede sacar la calculadora de su móvil, multiplicar la *Frecuencia* por el *Coste por Incidente* en cualquier página del informe, y comprobar que el *Impacto Anualizado Directo* da exactamente ese resultado.
2. **Trazabilidad del Coste:** Cada euro de impacto se justifica por factores que un CTO domina: horas de caída de servicio, tiempo de recuperación (RTO), pérdida de datos (RPO) y coste de intervención de soporte.
3. **Eliminación de Contradicciones:** Las notas de los cuestionarios se respetan rigurosamente salvo prueba técnica en contrario documentada en la entrevista.

**Instrucción para Ingeniería:** Proceder a actualizar `UNIVERSAL_EPISTEMIC_REMEDIATION_PLAN.md` y los prompts de generación (`prompts.py` / `report_generator.py`) bajo estas 4 Leyes Recalibradas inmediatamente.