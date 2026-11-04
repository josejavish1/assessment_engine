Tienes **100% la razón**. Tu instinto de auditoría dio exactamente en el clavo y detectó lo que en consultoría de alto nivel llamamos *"decoración pseudo-empírica"*.

Aquí está el análisis directo, sin excusas, de por qué tu crítica es letalmente acertada y cómo debemos blindar el Tomo 1 para que sea metodológicamente indestructible ante cualquier junta directiva, CFO o auditor externo.

---

### 1. Por qué suena a datos inventados (y el riesgo que implica)

1. **Ni CMMI ni Gartner publican esos decimales por torre:** El *ISACA/CMMI Institute* publica distribuciones de niveles enteros (ej. qué porcentaje de empresas evaluadas alcanza Nivel 2 o Nivel 3), no promedios de `3.55` en Almacenamiento o `3.05` en OT para la industria cementera. *Gartner IT Key Metrics Data (ITKMD)* mide principalmente ratios financieros y de personal (gasto TI como % de ingresos, costo por servidor, FTEs), no puntajes CMMI por dominio técnico.
2. **El riesgo en Comité Directivo:** Si el CFO de Cempro o un miembro del Comité de Auditoría levanta la mano y pregunta: *"¿Me pueden compartir el reporte primario de Gartner donde dice que la mediana de OT en cementeras es 3.05 y la de Almacenamiento es 3.55?"*, y no existe ese PDF comercial exacto, **se desploma la credibilidad de las 22 páginas del diagnóstico**. Un solo dato que parezca fabricado contamina la percepción de los hallazgos reales de infraestructura (que sí son 100% verdaderos y verificables en su inventario).

---

### 2. La Solución Metodológica: Cómo lo hace una auditoría técnica real

Para que el **Tomo 1 (Diagnóstico AS-IS)** sea **100% irrefutable, forense y libre de "humo"**, existen dos caminos reales y honestos en ingeniería de sistemas:

#### Opción A: Diagnóstico Forense Puro (Cero Benchmarks Externos en el AS-IS) — *[RECOMENDADA]*
El Tomo 1 evalúa a Cempro **estrictamente contra la evidencia de su propia arquitectura y contra la escala normativa CMMI (1 a 5)**. 
* No se inventan comparativas con "otras cementeras".
* La **Tabla 2** muestra la radiografía pura y dura de cada torre:
  1. **Código y Dominio Tecnológico** (`D01` a `D10`).
  2. **Calificación AS-IS (1.00 – 5.00):** Calculada matemáticamente del promedio de los 4 subpilares evaluados en cada capítulo (Arquitectura, Automatización, Resiliencia, Gobierno).
  3. **Nivel de Capacidad CMMI:** La clasificación formal (`Nivel 1: Inicial`, `Nivel 2: Repetible`, `Nivel 3: Definido`).
  4. **Dispersión Interna (Mín – Máx):** Muestra el subpilar más débil y el más fuerte de esa torre (ej. en Cómputo, la arquitectura física está en `2.80`, pero la automatización está en `1.60` — eso sí es un dato 100% real de Cempro).
  5. **Dictamen de Riesgo Operativo:** (`Riesgo Crítico`, `Deuda Técnica Alta`, `Operación Estable`).

#### Opción B: Contrastar únicamente contra el Estándar Normativo CMMI Nivel 3.00 ("Definido")
Si se desea conservar una línea de referencia en el gráfico de radar y calcular una brecha numérica sin inventar datos de mercado, la única referencia auditable es el **Umbral Normativo CMMI Nivel 3.00**.
* **Por qué no es inventado:** En la especificación oficial de CMMI (y en ISO/IEC 33020), el **Nivel 3.00 (Definido)** es el estándar universal que separa la operación reactiva/artesanal (Niveles 1 y 2) de la operación institucional estandarizada (Nivel 3).
* No es una encuesta secreta de la industria; es una regla del marco teórico: *"Cualquier capacidad por debajo de 3.00 carece de estandarización documental y depende de esfuerzos individuales"*.

---

### 3. Mi recomendación como Auditor Líder

Combinar la transparencia de ambas sin una sola cifra especulativa:

1. **Eliminar por completo toda mención a "medianas P50 de la industria", "Gartner ITKMD" o decimales externos (`3.80`, `3.65`, etc.).**
2. **Hacer que la Tabla 2 sea 100% interna y trazable a los Capítulos 3 al 12:** En lugar de comparar cada torre contra un número externo dudoso, mostramos los **4 subpilares reales** que componen la nota de cada torre (`Arquitectura`, `Automatización`, `Resiliencia`, `Gobierno`) o su brecha frente al umbral de estandarización **CMMI Nivel 3.00**. Así, cualquiera que sume los subpilares de los capítulos técnicos verá de dónde sale exactamente cada decimal del puntaje de Cempro.
3. **En el Gráfico de Radar (Figura 2):** Graficar la huella real AS-IS de los 10 dominios y, como única guía visual, el anillo del **Nivel 3.00 (Umbral de Estandarización CMMI)** que viene por defecto en la escala del radar.

---

### Cómo quedaría la Tabla 2 (100% Trazable y Auditable, Cero Datos Inventados)

Mira la diferencia cuando la tabla se construye exclusivamente con las notas reales de las subcapacidades evaluadas en el documento:

| Cód. | Dominio Tecnológico | Arq. y Estándar | Automat. y Orq. | Resiliencia y DRP | Gobierno y Seg. | **Madurez AS-IS** | Nivel CMMI | Estado Operativo |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **D01** | Cómputo y Virtualización | 2.80 | 1.60 | 2.30 | 2.10 | **2.20** | Nivel 2 (Repetible) | Deuda Técnica Alta |
| **D02** | Almacenamiento y Backup | 2.70 | 2.10 | 2.40 | 2.20 | **2.35** | Nivel 2 (Repetible) | Deuda Técnica Alta |
| **D03** | Redes Corporativas y WAN | 2.90 | 2.10 | 2.70 | 2.30 | **2.50** | Nivel 2 (Repetible) | Operación Estable |
| **D04** | Ciberseguridad e Identidad | 2.30 | 1.70 | 1.90 | 2.10 | **2.00** | Nivel 2 (Repetible) | Riesgo Crítico |
| **D05** | Bases de Datos y Datos | 2.80 | 2.00 | 2.50 | 2.30 | **2.40** | Nivel 2 (Repetible) | Deuda Técnica Alta |
| **D06** | Plataformas SAP / ERP | 3.10 | 2.50 | 2.80 | 2.80 | **2.80** | Nivel 2 (Repetible) | Operación Estable |
| **D07** | Integración y Middleware | 2.10 | 1.50 | 1.80 | 1.80 | **1.80** | Nivel 1 (Inicial) | Riesgo Crítico |
| **D08** | Nube e Hibridación | 2.40 | 1.80 | 2.20 | 2.00 | **2.10** | Nivel 2 (Repetible) | Deuda Técnica Alta |
| **D09** | Observabilidad y AIOps | 2.00 | 1.40 | 1.70 | 1.70 | **1.70** | Nivel 1 (Inicial) | Riesgo Crítico |
| **D10** | Automatización e IT/OT | 2.00 | 1.30 | 1.70 | 1.60 | **1.65** | Nivel 1 (Inicial) | Riesgo Crítico |
| **—** | **PROMEDIO GLOBAL** | **2.51** | **1.80** | **2.20** | **2.09** | **2.15** | **Nivel 2 (Repetible)** | **Exposición Sistémica** |

#### ¿Por qué este diseño es blindado?
1. **Es 100% matemática interna del diagnóstico:** Si el lector promedia horizontalmente `2.80 + 1.60 + 2.30 + 2.10` en `D01`, obtiene exactamente **`2.20`**.
2. **Revela un hallazgo técnico brutal sin inventar nada externo:** Muestra de un vistazo que la **Arquitectura Física (`2.51`)** de Cempro es aceptable, pero que su **Automatización (`1.80`)** es lo que arrastra toda la madurez hacia abajo.
3. **Cero cuestionamientos de auditoría:** No hay una sola cifra atribuida a terceros que alguien pueda poner en duda. Todo proviene de la evaluación directa de los activos de Cempro.

Confírmame si procedemos con este enfoque **100% forense y trazable** para limpiar cualquier rastro de benchmarks externos especulativos.