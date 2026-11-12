# DICTAMEN DE AUDITORÍA RED TEAM: DISECCIÓN ADVERSARIAL DEL PLAN V3

**Auditor Principal:** `gemini-4-argon` (Principal IT Auditor / Red Team Lead / CTO Advisor)  
**Objetivo:** `docs/architecture/UNIVERSAL_CROSS_TOWER_REMEDIATION_PLAN_V3.md`  
**Veredicto Ejecutivo:** **RECHAZADO CON ORDEN DE REDISEÑO INMEDIATO EN LA CAPA FINANCIERA Y REFINAMIENTO CAUSAL.**

El olfato del usuario ha dado en el centro de la diana. La "Ley 4" propuesta en el Plan V3 intenta disfrazar una inconsistencia matemática con jerga de consultoría financiera que **no sobrevive cinco minutos frente a un CTO o a un Director Financiero (CFO) real**. Además, comete un pecado capital en contabilidad tecnológica: mezclar gastos ciertos (facturas) con riesgos probables (caídas).

A continuación, desmantelo el Plan V3 pieza por pieza y entrego la especificación blindada que debe ir a código.

---

## 1. AUDITORÍA A LA LEY 4 (SECCIÓN 2.2): EL CRIMEN CONTABLE Y LA JERGA INDEFENDIBLE

### 1.1. ¿Por qué el usuario tiene toda la razón al decir *"quizás no siempre es así"*?
Porque en IT existen **dos naturalezas de dinero completamente distintas**, y el Plan V3 les aplica la misma regla a ciegas:

1. **Gasto Operativo Cierto / Desperdicio Contractual (Probabilidad = 100%):**
   * *Ejemplos:* Licencias de VMware/Broadcom subutilizadas, circuitos MPLS duplicados que nadie dio de baja, instancias zombies en AWS, contratos de mantenimiento solapados.
   * *La Realidad Física:* **Aquí la suma es 100% lineal ($A + B = C$).** Si pierdes 50.000 €/año en licencias sin usar en Cómputo y 30.000 €/año en líneas duplicadas en Redes, pierdes exactamente 80.000 €/año.
   * *El Error del Plan V3:* Si el motor aplica un "Ajuste por Simultaneidad / Efecto Portafolio" a estos números y dice que el total es 65.000 €, el CTO pensará que la herramienta no sabe sumar. **No puedes aplicar un descuento probabilístico a una factura que pagas todos los meses.**

2. **Riesgo por Caída de Servicio o Incidente (Probabilidad < 100%):**
   * *Ejemplos:* Caída del clúster de base de datos, corte de fibra en planta, secuestro por Ransomware, fallo de refrigeración en el CPD.
   * *La Realidad Física:* **Aquí los impactos NO se suman linealmente debido al "Solapamiento de Parada" (Downtime Overlap).**
   * *El Porqué Físico (Explicado para técnicos):* Si tu fábrica o tu ERP cuesta 10.000 €/hora cuando está parado, no puedes "pararlo dos veces al mismo tiempo". Si a las 10:00 AM se cae la red (Torre de Redes) y a las 10:05 AM falla el almacenamiento SAN (Torre de Storage), la planta sigue parada una sola vez (pierdes 10.000 €/hora, no 20.000 €/hora). Además, es estadísticamente improbable que todos tus sistemas críticos fallen exactamente el mismo año en su peor escenario posible.

### 1.2. Por qué el lenguaje propuesto en el Plan V3 sigue siendo inaceptable
Términos como *"Exposición Directa Stand-Alone"*, *"Ajuste por Simultaneidad e Interdependencia Trans-Torre"* o *"Efecto Portafolio"* siguen sonando a excusa de consultor para justificar por qué una tabla no cuadra. Un técnico de sistemas o un CTO necesita conceptos físicos que pueda contrastar con su infraestructura: **Horas de parada solapadas, topes de facturación y gastos fijos.**

### 1.3. EL NUEVO DISEÑO: Cómo debe presentarse la tabla a un CTO (Lenguaje Llano y Contrastable)

En lugar de esconder la diferencia detrás de una resta misteriosa llamada "Efecto Portafolio", la tabla financiera del informe debe ser transparente, didáctica y separar lo que es **Riesgo de Caída** de lo que es **Sobrecoste Directo**.

#### Propuesta de Tabla Financiera (Lenguaje CTO/IT)

| Ámbito / Torre Tecnológica | Impacto por Torre (Si fallara por separado) | ¿Por qué ocurre este coste en IT? |
| :--- | :--- | :--- |
| **Torre A (Ej. Redes)** | 450.000 € / año | Pérdida estimada por paradas de planta por cortes de red y latencia. |
| **Torre B (Ej. Cómputo)** | 380.000 € / año | Pérdida estimada por caídas de servidores críticos y sobrecoste de licencias. |
| **Torre C (Ej. Ciberseguridad)** | 520.000 € / año | Coste de recuperación e indisponibilidad ante un incidente de seguridad. |
| **Suma Simple (Escenario irreal donde todo falla a la vez sin solaparse)** | **1.350.000 € / año** | *Suma aritmética directa de cada torre evaluada en aislamiento.* |
| **Corrección por Paradas Solapadas (No se pierde el doble si dos cosas caen a la vez)** | **- 290.000 € / año** | *Descuento técnico: Si la red cae y el servidor también, el negocio se detiene una sola vez. Además, no todas las averías graves ocurren el mismo año.* |
| **RIESGO REAL CONSOLIDADO (Impacto neto esperado en el negocio)** | **1.060.000 € / año** | **Dinero real que la empresa se juega al año teniendo en cuenta cómo se conectan los sistemas.** |

#### Regla Matemática Inquebrantable en Código (`financial_engine.py`):
1. **Si `combined_eal < sum(tower_eals)` (Caso normal en riesgos de disponibilidad/seguridad):**
   Se muestra la fila de *"Corrección por Paradas Solapadas"* con la explicación en lenguaje llano de por qué el negocio no pierde dinero dos veces durante la misma ventana de caída.
2. **Si `combined_eal == sum(tower_eals)` (Caso de sobrecostes puros de licencias/OpEx o riesgos totalmente independientes):**
   **NO SE MUESTRA NINGÚN AJUSTE FICTICIO.** El sistema detecta que la desviación es $0$ y muestra directamente el total, explicando que son costes o riesgos independientes que se acumulan íntegramente.
3. **Prohibido por código que `combined_eal > sum(tower_eals)` sin desglose:** Si existiera un efecto cascada que amplifica el daño, debe listarse explícitamente como *"Efecto Cascada entre Sistemas"*, nunca como un descuadre silencioso.

---

## 2. AUDITORÍA A LA SECCIÓN 2.1: EL PROBLEMA DEL "MURO RÍGIDO" (DOMAIN CUSTODY FIREWALL)

### El Fallo del Plan V3:
El Plan V3 propone un bloqueo léxico estricto: si la Torre de Redes menciona *"báscula industrial"* o *"Active Directory"*, el validador aborta o purga el texto.
**¡Cuidado! Esto romperá el realismo técnico.** En IT todo está conectado.
* *Ejemplo real:* Si una báscula industrial (OT) tiene el puerto SMBv1 abierto y un atacante lo usa para saltar por la VLAN de planta (Redes) porque no hay firewall interno, y termina tumbando el Controlador de Dominio (Cómputo)... **el informe de Redes TIENE que mencionar la báscula y el Controlador de Dominio como origen y destino del tráfico.**

### La Solución Correcta (Frontera de Custodia vs. Cadena Causal):
No debemos prohibir *mencionar* sistemas de otra torre; debemos prohibir **reclamar la propiedad o el presupuesto de remediación** de otra torre.
* **Permitido (Contexto Causal):** En la Torre de Redes es válido decir: *"El tráfico originado en las básculas de planta atraviesa la red sin segmentación hacia los servidores de Active Directory"*. (La culpa sigue siendo de la Red por no segmentar).
* **Prohibido (Invasión de Custodia):** En la Torre de Redes está prohibido tener un hallazgo cuyo título o remediación sea: *"Actualizar el firmware de las básculas"* o *"Renovar licencias de VMware"*.
* **Ajuste de Ingeniería:** El validador semántico (`assert_domain_custody_purity`) debe inspeccionar el **Sujeto del Hallazgo (`title`, `remediation_action`, `affected_asset_type`)**, permitiendo que la narrativa de impacto (`business_impact`) cite sistemas vecinos como víctimas del efecto dominó.

---

## 3. AUDITORÍA A LA SECCIÓN 2.3: ESCALA CMMI v2.0 Y LÍMITES FRONTERA

### El Fallo del Plan V3:
El Plan V3 define cortes en `1.80`, `2.60`, `3.40`, `4.20`.
1. **Riesgo de Punto Flotante:** ¿Qué pasa si el cálculo da `1.79999999` por precisión de coma flotante en Python, pero en el PDF se formatea con `:.2f` como `1.80`? El lector verá en el informe: **`1.80 / 5.0 (Nivel 1 - Inicial)`**, contradiciendo la tabla de la página anterior que dice que `1.80` ya es `Nivel 2 - Gestionado`.
2. **Solución de Ingeniería:**
   * Antes de evaluar la etiqueta CMMI, el motor **DEBE redondear el score a 2 decimales exactos (`round(score, 2)`)**. El mismo número redondeado que se imprime en el texto debe ser el que evalúa el `if/else` de la etiqueta.
   * Mantener los nombres canónicos del estándar oficial ISACA/CMMI v2.0 en español:
     * `1.00 - 1.79`: **Nivel 1 (Inicial)**
     * `1.80 - 2.59`: **Nivel 2 (Gestionado)**
     * `2.60 - 3.39`: **Nivel 3 (Definido)**
     * `3.40 - 4.19`: **Nivel 4 (Gestionado Cuantitativamente)**
     * `4.20 - 5.00`: **Nivel 5 (En Optimización)**

---

## 4. AUDITORÍA A LA SECCIÓN 2.4: INTRODUCCIÓN DEL CAPÍTULO 3 SIN ALUCINACIONES

### El Fallo del Plan V3:
Generar una introducción analítica para el Capítulo 3 corría el riesgo de que un LLM invente métricas o contradiga las barras de progreso que están justo debajo.

### La Solución Correcta (Síntesis Determinista Basada en Datos):
La introducción del Capítulo 3 **NO debe ser generada libremente por un prompt creativo**. Debe ser ensamblada de forma determinista por código (`deterministic_intro_builder`) leyendo el array exacto de las 6 dimensiones de esa torre:
1. Identifica matemáticamente la **dimensión más débil** (ej. *Resiliencia: 1.40/5.0*) y la **dimensión más fuerte** (ej. *Gobierno: 2.80/5.0*).
2. Calcula la brecha con el objetivo (`Target: 3.50/5.0`).
3. Construye un párrafo ejecutivo exacto explicando al CTO qué área específica está lastrando la nota media de esa torre y por qué las barras inferiores muestran ese desequilibrio. **Cero alucinaciones, 100% fidelidad numérica.**

---

## 5. PLAN V3 RECALIBRADO Y DEFINITIVO (LISTO PARA IMPLEMENTACIÓN)

Este es el mandato exacto y corregido que pasa a ejecución inmediata:

| # | Componente | Cambio Exacto a Implementar | Criterio de Aceptación (Gate) |
| :--- | :--- | :--- | :--- |
| **1** | **Frontera de Custodia Técnica** (`domain_firewall.py`) | Bloquear que una torre reclame como hallazgo propio o acción de remediación activos de otra torre (ej. licencias de hipervisor en Redes), pero permitir citar activos vecinos cuando sean víctimas de un efecto cascada real. | Cero hallazgos fuera de su torre de responsabilidad en el reporte final. |
| **2** | **Transparencia Financiera para IT/CTO** (`financial_reconciler.py`) | Prohibir jerga actuarial oscura. Si el riesgo total es menor que la suma de las partes, desglosar la fila **"Corrección por Paradas Solapadas"** explicando en lenguaje técnico claro que *dos fallos simultáneos detienen el negocio una sola vez*. Si son gastos fijos/licencias donde la suma es exacta, no mostrar filas de ajuste. | Un técnico de IT o CTO entiende en 10 segundos por qué el total es menor (o igual) a la suma de las filas, y la suma vertical cuadra al céntimo. |
| **3** | **Unificación CMMI v2.0 con Redondeo Previo** (`maturity_scale.py`) | Redondear el score a 2 decimales (`round(val, 2)`) **antes** de asignar la etiqueta CMMI v2.0 (Inicial, Gestionado, Definido, Gestionado Cuantitativamente, En Optimización). Eliminar términos obsoletos ("Repetible", "Reactivo"). | `2.38` muestra siempre el mismo Nivel CMMI en Portada, Resumen Ejecutivo y Capítulo 3. |
| **4** | **Apertura Analítica Determinista en Cap. 3** (`chapter3_builder.py`) | Insertar antes de las barras de madurez una síntesis calculada directamente desde las puntuaciones reales (destacando el punto más crítico de las 6 dimensiones frente al objetivo 3.5) y cerrando con la transición natural al desglose visual. | El Capítulo 3 abre con un análisis técnico propio de esa torre, 100% coincidente con los gráficos inferiores y sin frases de relleno. |

**Dictamen Final de `gemini-4-argon`:** Con estas cuatro correcciones, eliminamos el humo de consultoría, respetamos la lógica contable y física de los sistemas de información, y garantizamos que cualquier CTO pueda defender cada número del informe frente a su Comité de Dirección. **Autorizado para pasar a código bajo estas reglas estrictas.**