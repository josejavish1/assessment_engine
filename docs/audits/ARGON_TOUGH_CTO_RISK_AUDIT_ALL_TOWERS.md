---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-08
applies_to:
- gemini
- audits
- risks
doc_type: operational
diataxis: reference
verification_mode: editorial
---

### AUDITORÍA FORENSE DEL REGISTRO DE RIESGOS (T1 – T10)
**De:** Group CTO & Chief Risk Officer (CRO)  
**Para:** Comité de Dirección / Directores de Dominio Tecnológico  
**Asunto:** Revisión implacable de los Dossiers de Riesgo previos al Consejo de Administración (Ingresos: €1.144M | Operativa continua 24/7: Hornos de clínker, molienda, básculas de expedición, canteras y filiales internacionales).

He revisado línea por línea el registro completo de riesgos de las 10 torres. Como responsable último de que nuestros hornos no se enfríen, de que los camiones no colapsen las carreteras comarcales en Sant Vicenç dels Horts y de que el CFO no nos humille en el Consejo por presentar matemáticas rotas, mi tolerancia hacia el "humo consultor", los errores de cálculo y la duplicidad de competencias es exactamente **cero**.

A continuación, presento mi dictamen forense torre por torre.

---

### TORRE 1: Physical Data Center & Critical Facilities (T1)
* **Puntuación CTO:** **5.2 / 10.0**
  * *Realismo Actuarial y Credibilidad Financiera:* 1.0 / 2.5
  * *Profundidad Operativa y Arraigo Industrial:* 1.8 / 2.5
  * *Pureza de Custodia y No-Duplicación:* 1.4 / 2.5
  * *Accionabilidad a Nivel de Consejo:* 1.0 / 2.5

* **El Veredicto del CTO:**
  * **Lo que es sólido e irrefutable:** **RVS01** (cortes eléctricos recurrentes en Sant Vicenç que superan las UPS), **RVS03** (fibra única de 10 Gbps sin anillo redundante a 500m) y **RVS04** (servidores físicos OT en canteras y salas técnicas sin control de acceso) reflejan exactamente nuestra realidad física en fábrica.
  * **Lo que es endeble, defectuoso o peligrosamente mal calibrado:** **¡Matemáticas rotas y relleno de plantilla!** Los riesgos **RVS02, RVS05 y RVS06** son textos genéricos ("Déficit en gestión de hotspots...", "necesidad de automatización de controles técnicos") con un `SLE` de €15.000, un `LEF` de 0.27, pero un **`ALE` de €0.0 y `P90` de €0.0**. Si llevo una tabla al Comité de Auditoría donde multiplicamos 0.27 por €15.000 y el resultado da cero, nos echan de la sala antes de abrir el segundo café. Además, en **RVS01**, un apagón total de ambos CPDs de fábrica tiene un `SLE` de €141k; si paramos expedición y control OT durante un turno completo, entre pérdida de despacho, enfriamiento térmico y horas extra, el golpe supera fácilmente los €250k–€350k.
  * **Lo que cuestionaría en un interrogatorio:** En **RVS01** y **RVS03** estáis mezclando el fallo físico (corte de luz / rotura de zanja de fibra) con la falta de RAM en HPE SimpliVity y el *split-brain* de NetApp MetroCluster. T1 es dueño del edificio, los cuadros eléctricos, las UPS, los grupos electrógenos y el conducto físico; no de la memoria RAM de VMware.

* **Directivas Exactas de Remediación:**
  1. **Eliminar o reescribir RVS02, RVS05 y RVS06:** Prohibido usar frases hechas de plantilla. O se cuantifica el fallo real de climatización/incendios en las salas técnicas de Sant Vicenç y canteras corrigiendo el motor matemático (`ALE = LEF × SLE`), o se consolidan en un único riesgo de *Degradación Ambiental en Salas Técnicas de Planta* con un `SLE` de €65.000 y `ALE` de ~€17.550.
  2. **Limpiar la custodia en RVS01 y RVS03:** Ceñir RVS01 al fallo de conmutación de grupos electrógenos/UPS y la proximidad física (500m) en el mismo recinto industrial. Ceñir RVS03 a la obra civil (trazado físico único en bandeja/zanja expuesta a maquinaria pesada en fábrica).
  3. **Recalibrar RVS01:** Elevar el `SLE` a **€280.000** (coste real de parada de planta y recuperación física de equipos quemados por picos de tensión).

---

### TORRE 2: Hybrid Cloud, Compute & Virtualization (T2)
* **Puntuación CTO:** **6.8 / 10.0**
  * *Realismo Actuarial y Credibilidad Financiera:* 1.7 / 2.5
  * *Profundidad Operativa y Arraigo Industrial:* 2.3 / 2.5
  * *Pureza de Custodia y No-Duplicación:* 1.0 / 2.5
  * *Accionabilidad a Nivel de Consejo:* 1.8 / 2.5

* **El Veredicto del CTO:**
  * **Lo que es sólido e irrefutable:** El diagnóstico técnico es excelente. Habéis capturado la bomba de relojería de los 6 nodos HPE SimpliVity (especialmente los nodos 3 y 4 con cargas OT al límite de RAM), la revisión manual "cada mañana" por miedo a que explote (**RVS08**), las >300 VMs perpetuas sin ciclo de decomiso (**RVS06**) y el estrangulamiento de recursos en producción coexistiendo con Test (**RVS07**).
  * **Lo que es endeble, defectuoso o peligrosamente mal calibrado:** Tenéis una **duplicación masiva interna y externa**. **RVS01** (agotamiento de RAM que impide failover entre CPD A y B) y **RVS09** (invalidez práctica del failover automatizado de SimpliVity por falta de RAM física) son **exactamente el mismo riesgo técnico y financiero** contado dos veces para inflar el ALE de la torre. Además, **RVS02** (CPDs a 500m expuestos a cortes eléctricos) invade directamente las competencias de T1 y T5. Por último, un `SLE` de €47k en RVS01/RVS09 por dejar caer las VMs de OT de la fábrica principal equivale a apenas 1.5 horas de parada de planta; está subestimado.
  * **Lo que cuestionaría en un interrogatorio:** "¿Por qué me pedís CapEx para 2 nodos SimpliVity nuevos en RVS01, RVS05 y RVS09 si en RVS06 admitís que tenéis más de 300 máquinas virtuales encendidas a perpetuidad sin purgar?" El CFO os dirá que apaguéis la basura de desarrollo antes de firmar un solo euro en hierro nuevo.

* **Directivas Exactas de Remediación:**
  1. **Fusionar RVS01 y RVS09:** Consolidar en un único riesgo maestro: *Incapacidad de Failover HA en Clústeres HPE SimpliVity (Nodos 3 y 4 OT) por Saturación Crítica de RAM*. Asignar `TEF` 4.0, `SLE` **€145.000** (parada de expedición y sistemas de control durante 4-6 horas de triaje manual) y `ALE` **€52.200**.
  2. **Transferir/Suprimir RVS02:** La ubicación física de los CPDs a 500m y los cortes eléctricos pertenecen a **T1 (Custodio Primario)** y **T5 (DRP)**. Eliminarlo de T2.
  3. **Ajustar RVS04 (Contenedores):** Un `ALE` de €2.112 es ruido estadístico para una empresa de €1.144M. Integrar la falta de contenerización como causa raíz dentro del riesgo de *VM Sprawl y Densidad de Cómputo* (**RVS06**).

---

### TORRE 3: Enterprise Networks & WAN Connectivity (T3)
* **Puntuación CTO:** **4.5 / 10.0**
  * *Realismo Actuarial y Credibilidad Financiera:* 1.0 / 2.5
  * *Profundidad Operativa y Arraigo Industrial:* 1.5 / 2.5
  * *Pureza de Custodia y No-Duplicación:* 0.8 / 2.5
  * *Accionabilidad a Nivel de Consejo:* 1.2 / 2.5

* **El Veredicto del CTO:**
  * **Lo que es sólido e irrefutable:** La visibilidad sobre la asimetría operativa entre el modelo on-premise de Sant Vicenç y la externalización total en la telco NOS en SECIL Portugal (**RVS02**), así como el riesgo de *split-brain* entre los Core Switches Huawei, NetApp y SimpliVity por el enlace DCI de 10 Gbps sin anillo (**RVS04**).
  * **Lo que es endeble, defectuoso o peligrosamente mal calibrado:** **Invasión absurda de competencias y errores de cálculo.** ¿Qué hace **RVS07** (servidores Linux dimensionados "muy justitos" de disco para que fallen cuando una consulta SQL llena 1 GB de log) en la torre de **Redes Corporativas y WAN**? ¡Eso es almacenamiento/operaciones de sistemas (T4/T7/T8), no tiene nada que ver con switches Huawei ni enlaces WAN! ¿Qué hace **RVS03** (acumulación de ERPs congelados SAP, FICOS, Primavera consumiendo recursos de CPD) en Redes? Además, **RVS05** vuelve a presentar el fallo del motor financiero: `SLE` €15.000 y **`ALE` €0.0**.
  * **Lo que cuestionaría en un interrogatorio:** En **RVS04**, decís que un corte de fibra paraliza "la operativa de planta y básculas" provocando un *split-brain* generalizado, ¿y valoráis el `SLE` en unos ridículos **€15.924**? Si se paran las básculas y la planta de Sant Vicenç por un corte de fibra y tardamos 8 horas en fusionar y levantar el MetroCluster de NetApp y SimpliVity, perdemos más de €120.000 solo en logística y facturación diferida. Y en **RVS01**, el *finding* dice que los switches Huawei funcionan perfectamente en activo-activo... ¡eso es un control validado, no un hallazgo de vulnerabilidad!

* **Directivas Exactas de Remediación:**
  1. **Expulsar RVS03 y RVS07 de T3:** RVS03 pertenece exclusivamente a **T10** (Plataformas Core/ERPs M&A) y RVS07 a **T7/T8** (Observabilidad y Dimensionamiento).
  2. **Eliminar RVS01:** Si la conmutación Core Huawei está probada y funciona, no es un riesgo de red. El riesgo de desastre físico de planta completa a 500m ya está en T1 y T5.
  3. **Recalibrar RVS04 (Enlace DCI 10 Gbps):** T1 cubre la zanja física; T3 debe cubrir la *Arquitectura Lógica de Red DCI y Convergencia ante Split-Brain*. Subir el `SLE` de €15.924 a **€95.000** (`ALE` ~€25.650).
  4. **Corregir RVS05:** Eliminar el texto de plantilla con `ALE = 0.0` y sustituirlo por el riesgo real de *Falta de Visibilidad y Segmentación de Red en Planta (Frontera IT/OT y Canteras)*.

---

### TORRE 4: Storage Platforms & Corporate Backup (T4)
* **Puntuación CTO:** **5.5 / 10.0**
  * *Realismo Actuarial y Credibilidad Financiera:* 1.3 / 2.5
  * *Profundidad Operativa y Arraigo Industrial:* 1.8 / 2.5
  * *Pureza de Custodia y No-Duplicación:* 1.0 / 2.5
  * *Accionabilidad a Nivel de Consejo:* 1.4 / 2.5

* **El Veredicto del CTO:**
  * **Lo que es sólido e irrefutable:** La identificación de la dispersión de almacenamiento en canteras con soluciones domésticas/PYME como Synology y Proxmox frente a NetApp/Cohesity (**RVS01**), y la falta de procedimientos validados para recuperar desde la segunda copia (Cohesity) o tercera copia (Guacamole) (**RVS03**).
  * **Lo que es endeble, defectuoso o peligrosamente mal calibrado:** **Canibalización severa de otras torres.** **RVS04** (uso de cuentas `root` y `full admin` compartidas) pertenece a **T6 (Ciberseguridad/PAM)**. **RVS05** (dependencia del único DBA en Croacia) se repite aquí, en T5, en T8 y en T9; su custodio natural es **T8 (Gobierno/Talento)** o **T10 (Bases de Datos)**, no la torre de cabinas de almacenamiento y backup. Además, en **RVS03**, valorar el `SLE` de un fallo o retraso crítico en la orquestación de Cohesity/Guacamole durante un desastre mayor en **€6.392** (`ALE` €1.150) es un insulto a la inteligencia: €6.000 no paga ni dos días de consultoría de emergencia de NetApp/Cohesity, mucho menos el impacto de tener la fábrica sin datos.
  * **Lo que cuestionaría en un interrogatorio:** "¿Dónde está el riesgo del Stretch MetroCluster de NetApp operando sobre un enlace único de 10 Gbps a 500m sin árbitro externo resiliente?" Lo habéis mencionado de pasada en T1 y T3, pero en T4 —que es la dueña de NetApp— ¡ni siquiera aparece!

* **Directivas Exactas de Remediación:**
  1. **Eliminar RVS04 y RVS05 de T4:** Consolidar PAM (`root`) en **T6** y el riesgo de hombre clave (DBA en Croacia) en **T8**.
  2. **Incorporar el Riesgo Core de NetApp MetroCluster:** Crear un nuevo riesgo en T4 para la *Corrupción o Indisponibilidad de Volúmenes en NetApp MetroCluster ante Apagados Eléctricos Abruptos o Caída de Enlace Inter-CPD*, con `SLE` de **€110.000** y `ALE` de **€29.700**.
  3. **Recalibrar RVS03 (Recuperación Cohesity/Guacamole):** Subir el `SLE` de €6.392 a **€85.000** (coste de extensión de parada de planta por incapacidad de restaurar backups inmutables a tiempo).

---

### TORRE 5: Operational Continuity & Disaster Recovery (T5)
* **Puntuación CTO:** **7.9 / 10.0**
  * *Realismo Actuarial y Credibilidad Financiera:* 2.0 / 2.5
  * *Profundidad Operativa y Arraigo Industrial:* 2.4 / 2.5
  * *Pureza de Custodia y No-Duplicación:* 1.5 / 2.5
  * *Accionabilidad a Nivel de Consejo:* 2.0 / 2.5

* **El Veredicto del CTO:**
  * **Lo que es sólido e irrefutable:** Esta torre habla el idioma de la industria cementera. **RVS01** clava el problema real: el negocio asume disponibilidad infinita sin RTO/RPO firmados, y una caída bloquea la expedición de camiones generando colas y sanciones por bloqueo de vías públicas. **RVS04** (scripts reactivos en Zabbix que reinician servicios enmascarando fallos crónicos de código) y **RVS07** (contaminación cruzada IT/OT en vCenter y aplicaciones puente de básculas) son hallazgos de primer nivel.
  * **Lo que es endeble, defectuoso o peligrosamente mal calibrado:** Sigue habiendo **solapamiento directo** con T1 y T2. **RVS06** (sobresuscripción de CPU/RAM en clústeres 3 y 4) es idéntico a T2.RVS01/RVS09. **RVS08** (cortes eléctricos crónicos en CPDs de Sant Vicenç, `ALE` €58.729) es idéntico a T1.RVS01 (`ALE` €50.922). Si sumamos ambos en el presupuesto global del Grupo, estamos contabilizando dos veces el mismo apagón. Asimismo, en **RVS05** (ausencia de DR georreferenciado fuera de la planta de Sant Vicenç), un `SLE` de **€64.849** para una "pérdida total e irrecuperable a corto/medio plazo de la operativa industrial y corporativa ante un desastre físico o incendio" es ridículamente bajo: un desastre que destruya ambos CPDs en Sant Vicenç cuesta millones de euros, no €64k.
  * **Lo que cuestionaría en un interrogatorio:** "Si se incendia o inunda el recinto de Sant Vicenç y perdemos el 85% de nuestra infraestructura on-premise (RVS05), ¿me estáis diciendo que la pérdida única esperada (`SLE`) es de €64.850, pero si hay un simple corte eléctrico (RVS08) la pérdida es de €163.137?" ¡Eso viola cualquier lógica actuarial! Un evento de `LM = 5.0` (catastrófico) no puede tener un `SLE` inferior a un evento de `LM = 4.0`.

* **Directivas Exactas de Remediación:**
  1. **Corregir la inversión actuarial en RVS05 (Ausencia de DR Geográfico):** Reducir la frecuencia (`LEF`) a un evento extremo real (0.02 – 0.05 anual), pero elevar el `SLE` a **€1.850.000** (reconstrucción de infraestructura, pérdida de semanas de facturación/expedición y migración de emergencia a nube), situando el `ALE` en **~€74.000** y el `P90` por encima de **€450.000**.
  2. **Delimitar la frontera con T1 y T2 en RVS06 y RVS08:** Mantener en T1 el daño físico/eléctrico y en T2 la falta de capacidad de cómputo; en T5, refundir ambos en un único riesgo de *Inviabilidad del Plan de Recuperación ante Desastres (DRP) y Tiempos de Triaje Manual Extendidos en Crisis*, eliminando la doble contabilidad.
  3. **Retirar RVS03 (DBA único):** Dejar la custodia primaria en **T8**.

---

### TORRE 6: Cybersecurity & Identity Governance (T6)
* **Puntuación CTO:** **7.4 / 10.0**
  * *Realismo Actuarial y Credibilidad Financiera:* 1.8 / 2.5
  * *Profundidad Operativa y Arraigo Industrial:* 2.2 / 2.5
  * *Pureza de Custodia y No-Duplicación:* 2.0 / 2.5
  * *Accionabilidad a Nivel de Consejo:* 1.4 / 2.5

* **El Veredicto del CTO:**
  * **Lo que es sólido e irrefutable:** **RVS05** es el riesgo mejor articulado de todo el dossier: *Nodos VMware ESXi con más de 613 días de uptime continuo sin parches por imposibilidad de evacuar RAM en clústeres 3 y 4*. Un ransomware de cifrado de datastores ESXi ahí nos apaga la cementera entera. **RVS06** (frontera IT/OT sin gobierno en el canal directo entre silos OT y la BBDD de expedición de camiones) y **RVS03** (uso directo de `root` y `full admin` sin PAM) pertenecen legítimamente a esta torre.
  * **Lo que es endeble, defectuoso o peligrosamente mal calibrado:** **RVS04** vuelve a ser basura de plantilla automatizada ("Déficit en gestión de excepciones de hardening...", `SLE` €15.000, **`ALE` €0.0**). Además, para una corporación industrial sujeta a la directiva **NIS2** con €1.144M de facturación, las cifras de impacto de ciberseguridad ignoran por completo las sanciones regulatorias (que pueden alcanzar hasta €10M o el 2% de la facturación global) y el coste real de respuesta a incidentes forenses. Un `SLE` de €14.316 en **RVS03** por compromiso o borrado destructivo mediante cuenta `root` en los clústeres de producción OT es diez veces inferior a la realidad.
  * **Lo que cuestionaría en un interrogatorio:** "Si un atacante explota una vulnerabilidad de hace 613 días en ESXi (RVS05) o cruza desde la red de silos OT hasta el CPD central (RVS06), ¿por qué no veo reflejado el impacto de cumplimiento NIS2 ni el rescate/reconstrucción de los >300 servidores?"

* **Directivas Exactas de Remediación:**
  1. **Erradicar el texto de plantilla en RVS04:** Reemplazar por *Ausencia de Bastionado (Hardening) y Parcheo en Sistemas Operativos Legacy y Servidores de Ficheros de Delegaciones*, corrigiendo el cálculo para generar un `ALE` real (~€18.000).
  2. **Recalibrar RVS03 (Cuentas Root/Full Admin sin PAM):** Como custodio primario (absorbiendo T4.RVS04 y T10.RVS02), elevar el `SLE` de €14.316 a **€95.000** (`ALE` **€34.200**), reflejando el coste de destrucción de volúmenes productivos sin trazabilidad forense.
  3. **Incorporar exposición NIS2 en RVS05 y RVS06:** Ajustar el `SLE` de **RVS05** a **€450.000** (`P90` > €650.000) y el de **RVS06** a **€220.000**, documentando explícitamente la paralización de básculas y la responsabilidad legal de la Alta Dirección bajo NIS2.

---

### TORRE 7: Gestión de Servicios de TI y Operaciones Digitales (T7)
* **Puntuación CTO:** **3.5 / 10.0** *(La peor torre del registro)*
  * *Realismo Actuarial y Credibilidad Financiera:* 0.5 / 2.5
  * *Profundidad Operativa y Arraigo Industrial:* 1.2 / 2.5
  * *Pureza de Custodia y No-Duplicación:* 1.0 / 2.5
  * *Accionabilidad a Nivel de Consejo:* 0.8 / 2.5

* **El Veredicto del CTO:**
  * **Lo que es sólido e irrefutable:** **RVS01** expone una herida organizativa real: la escisión entre Ingeniería de Infraestructura y el nuevo equipo de Operaciones/ISAU, que opera fuera de nuestro gobierno directo con un traspaso incompleto, retrasando el escalado de incidentes de fábrica.
  * **Lo que es endeble, defectuoso o peligrosamente mal calibrado:** **Tres de los cinco riesgos (RVS02, RVS04 y RVS05 — el 60% de la torre) son relleno de plantilla con `ALE = €0.0` y `P90 = €0.0`.** Leer frases como *"Déficit en madurez sre: slos/slis y reducción de toil (cuando aplica)"* en minúsculas, copiadas directamente de un cuestionario genérico, es inaceptable para presentar a un Consejo de Administración. Por si fuera poco, **RVS03** mezcla tres cosas inconexas en un mismo párrafo: servidores Linux "muy justitos" de disco (que ya salió en T3, T4 y T8), un único técnico para Kubernetes y la renovación de hosts HPE SimpliVity (que es de T2).
  * **Lo que cuestionaría en un interrogatorio:** "Director de T7, usted viene a pedir presupuesto para ITSM y Operaciones Digitales con un dossier donde el 60% de sus riesgos tienen un impacto anual esperado de cero euros y hablan de 'toil (cuando aplica)', mientras sus operadores reciben alertas críticas de producción por chats de Microsoft Teams (como confiesa T9.RVS07). ¿En qué mundo vive?"

* **Directivas Exactas de Remediación:**
  1. **Reescribir íntegramente RVS02, RVS04 y RVS05 con hechos reales de Molins:**
     * **RVS02 (Service Desk / Escalado):** *Ausencia de SLAs formales de resolución y pérdida de trazabilidad en el escalado entre ISAU (N1/N2) e Ingeniería (N3) ante paradas de básculas y despacho en planta.* (`SLE`: €35.000 | `ALE`: €12.600).
     * **RVS04 (Problem Management):** *Gestión reactiva de incidencias crónicas mediante reinicios manuales o scripts en Zabbix sin erradicación de causa raíz en aplicaciones core.* (`SLE`: €40.000 | `ALE`: €10.800).
     * **RVS05 (Observabilidad y Gestión de Eventos):** *Ausencia de correlación de eventos y gestión manual de alarmas críticas mediante avisos en chats de Microsoft Teams hacia desarrollo (absorbiendo T9.RVS07) y llenado deliberado de discos Linux de 1 GB como método de alerta.* (`SLE`: €55.000 | `ALE`: €19.800).
  2. **Depurar RVS03:** Sacar de T7 la renovación de hardware HPE (pertenece a T2) y el riesgo de hombre clave de Kubernetes (pertenece a T8).

---

### TORRE 8: Estrategia Tecnológica, Gobierno y FinOps (T8)
* **Puntuación CTO:** **7.6 / 10.0**
  * *Realismo Actuarial y Credibilidad Financiera:* 1.9 / 2.5
  * *Profundidad Operativa y Arraigo Industrial:* 2.1 / 2.5
  * *Pureza de Custodia y No-Duplicación:* 1.6 / 2.5
  * *Accionabilidad a Nivel de Consejo:* 2.0 / 2.5

* **El Veredicto del CTO:**
  * **Lo que es sólido e irrefutable:** Es un diagnóstico estratégico muy potente para el CEO y el CFO. Captura la fragmentación de poder en tres frentes (**RVS02**: negocio de cemento decide redes de fábrica sin IT, 20-40 desarrolladores externos lanzan código sin gobierno de infraestructura, y opacidad total en SECIL Portugal), el riesgo de "Hombre Clave" en un equipo reducido a 5 personas con una jubilación sin cubrir y el único DBA/experto en red en Croacia (**RVS04**), la parálisis FinOps CapEx vs. OpEx para renovar los SimpliVity de 2018 (**RVS05**), y los contratos con HPE que solo garantizan 4h de respuesta pero no tiempo de reparación (CTR) junto a la filosofía de *"no reemplazar bajas hasta ver si vamos mal"* (**RVS06**).
  * **Lo que es endeble, defectuoso o peligrosamente mal calibrado:** **RVS01** (deuda técnica de Oracle 10g/11g y Forms/Reports) se pisa directamente con **T10.RVS04 y T10.RVS06**. Y **RVS07** vuelve a repetir por cuarta vez la historia de los servidores dimensionados con 1 GB de margen de disco para detectar logs descontrolados (ya visto en T3, T4 y T7).
  * **Lo que cuestionaría en un interrogatorio:** "En RVS05 valoráis en €11.546 anuales (`ALE`) la fricción financiera entre CapEx y OpEx, y en RVS01 valoráis en €17.635 anuales tener toda la empresa anclada en Oracle 10g/11g desde la crisis de 2008. Si migrar Oracle Forms y las bases de datos cuesta cientos de miles de euros, el CFO verá un `ALE` de €17k y dirá: *'Sale más barato asumir el riesgo que pagar la migración'*."

* **Directivas Exactas de Remediación:**
  1. **Designar a T8 como Custodio Primario Único del Riesgo de Talento/Hombre Clave (RVS04):** Absorber las duplicidades de T4.RVS05, T5.RVS03 y T9.RVS05. Elevar el `SLE` a **€125.000** (`ALE` **€45.000**) reflejando el coste de contratación de emergencia y caída prolongada de fábrica si el especialista en Croacia causa baja.
  2. **Diferenciar RVS01 de T10:** En T8, enfocar RVS01 exclusivamente en el *Riesgo Estratégico, Bloqueo Evolutivo y Sobrecoste de Licenciamiento/Soporte Extendido por Deuda Técnica Heredada (Post-2008)*, dejando el fallo operativo diario de las consultas SQL en T10.
  3. **Eliminar RVS07 de T8:** Ya está cubierto operativamente en T7 (Observabilidad/Logs).

---

### TORRE 9: Digital Workplace & Unified Communications (T9)
* **Puntuación CTO:** **3.8 / 10.0**
  * *Realismo Actuarial y Credibilidad Financiera:* 0.8 / 2.5
  * *Profundidad Operativa y Arraigo Industrial:* 1.0 / 2.5
  * *Pureza de Custodia y No-Duplicación:* 0.8 / 2.5
  * *Accionabilidad a Nivel de Consejo:* 1.2 / 2.5

* **El Veredicto del CTO:**
  * **Lo que es sólido e irrefutable:** **RVS08** aporta un dato valioso que no estaba en otras torres: la pérdida de conocimiento funcional de los frontales de usuario (solo 2 de los 4 Product Owners conocen Forms/Reports) y la indecisión sobre migrar solo el frontal a PHP/Node o hacer un Big Bang.
  * **Lo que es endeble, defectuoso o peligrosamente mal calibrado:** **Esta torre es un cajón de sastre que ha robado hallazgos de todo el registro porque no tenía suficientes datos propios de Digital Workplace.**
    * ¿Qué hace el DBA en Croacia y el experto en Kubernetes (**RVS05**) en la torre de *Puesto de Trabajo Digital y Comunicaciones Unificadas*?
    * ¿Qué hace el aprovisionamiento de más de 300 servidores virtuales (**RVS07**) en Workplace?
    * ¿Qué hacen las redes de fábrica y las básculas (**RVS02**) con un ridículo `SLE` de **€777,85** y un **`ALE` de €210,02**? ¡Por €210 al año no dedico ni 30 segundos de lectura ejecutiva!
    * Y, de nuevo, **RVS03** tiene el fallo de plantilla con `SLE` €15.000 y **`ALE` €0.0**.
  * **Lo que cuestionaría en un interrogatorio:** "Me traéis un riesgo de €210 al año (RVS02) y otro de €379 al año (RVS01), me habláis de Kubernetes y de bases de datos en Croacia, y no me decís ni una palabra real sobre la seguridad de los endpoints en fábrica, la telefonía IP en canteras o la resiliencia de Microsoft Teams cuando lo estáis usando como sistema de alertas de producción."

* **Directivas Exactas de Remediación:**
  1. **Purgar la torre de intrusiones ajenas:** Eliminar **RVS05** (DBA/K8s -> va a T8), **RVS06** (ISAU/Operaciones -> ya está en T7.RVS01) y depurar **RVS07** (pasar la gestión de alarmas por Teams y plantillas de servidores a T7/T2).
  2. **Consolidar y recalibrar los riesgos reales de Workplace:**
     * Refundir **RVS01 y RVS02** en *Desestandarización y Fragilidad de Terminales Operativos en Planta, Básculas, Canteras y Filiales (Molins vs. SECIL)*, con un `SLE` creíble de **€28.000** (parada de puestos de expedición/báscula en fábrica por fallo de terminal/conectividad local) y `ALE` de **€7.560**.
     * Corregir **RVS03** eliminando el `ALE = 0.0` y enfocándolo en la *Fricción de Identidad, Gestión de Puestos y Soporte N1 (ISAU) por Falta de Base de Conocimiento (MoinMoin)* (uniéndolo con **RVS04**), con `SLE` de **€25.000** y `ALE` de **€9.000**.

---

### TORRE 10: Plataformas Core, Sistemas de Planta y Operaciones Locales (T10)
* **Puntuación CTO:** **7.8 / 10.0**
  * *Realismo Actuarial y Credibilidad Financiera:* 1.8 / 2.5
  * *Profundidad Operativa y Arraigo Industrial:* 2.5 / 2.5
  * *Pureza de Custodia y No-Duplicación:* 1.5 / 2.5
  * *Accionabilidad a Nivel de Consejo:* 2.0 / 2.5

* **El Veredicto del CTO:**
  * **Lo que es sólido e irrefutable:** Operativamente es impecable. Describe la migración ad-hoc del IBM iSeries a PostgreSQL/Excel y el cementerio de ERPs congelados (FICOS, Primavera, SAP legacy) (**RVS01**), los bloqueos constantes en planta por `SELECTs` ineficientes de Oracle Forms sobre Oracle 10g/11g (**RVS04**), y el cuello de botella crítico entre los silos OT y la base de datos IT para emitir el albarán de báscula (**RVS05**).
  * **Lo que es endeble, defectuoso o peligrosamente mal calibrado:** **Infracuantificación severa en procesos críticos de fábrica y duplicidad con T2/T6.** En **RVS05**, si se cae la integración IT/OT de pesaje y los camiones quedan bloqueados en la báscula sin albarán de expedición, el `SLE` que habéis puesto es de solo **€17.464** (`ALE` €4.715). En una cementera que factura €1.144M, bloquear la salida de cisternas y bañeras en hora punta paraliza la logística de obras enteras, genera penalizaciones inmediatas y atasca la planta; un incidente serio ahí supera los €80.000. Además, **RVS02** (cuentas `root` y runbooks) duplica T6.RVS03 y T3.RVS06, y **RVS03** (VM Sprawl de >300 VMs) es exactamente el mismo riesgo que **T2.RVS06** (donde tenía un `ALE` de €39.590 y aquí le ponéis €6.187 con un `TEF` de 5.0).
  * **Lo que cuestionaría en un interrogatorio:** "¿Por qué el mismo problema de las >300 máquinas virtuales de desarrollo cuesta €39.590 al año en la Torre 2 y €6.187 al año en la Torre 10? ¿Y por qué habéis separado RVS04 (rendimiento de Oracle 10g/11g con Forms) y RVS06 (deuda técnica de Oracle 10g/11g con Forms) en dos riesgos distintos dentro de la misma torre?"

* **Directivas Exactas de Remediación:**
  1. **Eliminar RVS02 y RVS03 de T10:** El control de cuentas `root` reside en **T6**; el *VM Sprawl* (>300 VMs) reside en **T2**.
  2. **Fusionar RVS04 y RVS06:** Unificar en un gran riesgo de *Degradación Operativa, Bloqueos Transaccionales y Obsolescencia Crítica (EoL) en Aplicaciones Core (Oracle Forms/Reports sobre Oracle 10g/11g)*, con `TEF` 4.0, `SLE` **€85.000** y `ALE` **€30.600**.
  3. **Recalibrar RVS05 (Integración IT/OT en Básculas y Expedición):** Elevar el `SLE` de €17.464 a **€90.000** (`ALE` **€24.300**), reflejando el coste industrial real de detener la expedición física de cemento en planta.
  4. **Ajustar RVS01 (IBM iSeries y ERPs Congelados M&A):** Como custodio primario (absorbiendo T3.RVS03), elevar el `SLE` a **€35.000** por el riesgo de sanción fiscal/auditoría si un ERP congelado (FICOS/Primavera) no levanta o pierde integridad referencial durante una inspección.

---

### TABLA CONSOLIDADA DE PUNTUACIÓN (SCORECARD T1 – T10)

| Torre | Dominio Tecnológico | Realismo Actuarial (2.5) | Arraigo Industrial (2.5) | Pureza de Custodia (2.5) | Accionabilidad Consejo (2.5) | **Nota CTO (10.0)** | Estado para el Consejo |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **T1** | Physical Data Center & Facilities | 1.0 | 1.8 | 1.4 | 1.0 | **5.2** | **RECHAZADO** (3 riesgos con ALE = €0) |
| **T2** | Hybrid Cloud, Compute & Virt. | 1.7 | 2.3 | 1.0 | 1.8 | **6.8** | **CONDICIONADO** (Duplicidad interna RVS01/09) |
| **T3** | Enterprise Networks & WAN | 1.0 | 1.5 | 0.8 | 1.2 | **4.5** | **RECHAZADO** (Riesgos de Linux/ERP en Redes) |
| **T4** | Storage Platforms & Backup | 1.3 | 1.8 | 1.0 | 1.4 | **5.5** | **RECHAZADO** (Falta MetroCluster; duplica PAM/DBA) |
| **T5** | Operational Continuity & DR | 2.0 | 2.4 | 1.5 | 2.0 | **7.9** | **APROBADO CON AJUSTES** (Subir SLE Geo-DR) |
| **T6** | Cybersecurity & Identity Gov. | 1.8 | 2.2 | 2.0 | 1.4 | **7.4** | **CONDICIONADO** (Borrar RVS04 ALE=€0; añadir NIS2) |
| **T7** | IT Service Management & Ops | 0.5 | 1.2 | 1.0 | 0.8 | **3.5** | **RECHAZADO CRÍTICO** (60% relleno con ALE = €0) |
| **T8** | Tech Strategy, Gov & FinOps | 1.9 | 2.1 | 1.6 | 2.0 | **7.6** | **APROBADO CON AJUSTES** (Limpiar solape T7/T10) |
| **T9** | Digital Workplace & UC | 0.8 | 1.0 | 0.8 | 1.2 | **3.8** | **RECHAZADO CRÍTICO** (Riesgos de €210 y robo de temas) |
| **T10**| Core Platforms & Plant Systems | 1.8 | 2.5 | 1.5 | 2.0 | **7.8** | **APROBADO CON AJUSTES** (Subir SLE básculas; limpiar T2) |
| **MEDIA** | **GLOBAL PORTFOLIO** | **1.38** | **1.88** | **1.26** | **1.48** | **6.00 / 10** | **NO APTO PARA PRESENTACIÓN SIN SANEAMIENTO** |

---

### VEREDICTO EJECUTIVO FINAL DEL CTO & CRO

El trabajo de campo subyacente es extraordinario: habéis destapado las verdades incómodas de nuestra infraestructura (los 613 días sin parchear en ESXi, los clústeres 3 y 4 de OT al borde del colapso de RAM en SimpliVity, los dos CPDs a 500 metros sufriendo apagones en Sant Vicenç, las básculas dependiendo de un hilo entre OT e IT, el DBA único en Croacia, los discos Linux con 1 GB de margen libre y la ceguera operativa sobre NOS en SECIL Portugal).

Sin embargo, **el empaquetado actuarial y la arquitectura de custodia del registro actual no pueden entrar al Consejo de Administración en este estado** por tres razones letales:

1. **El Escándalo de los "Ceros" (Fallo de Motor / Plantillas Vacías):** Hay exactamente **9 riesgos** repartidos en T1 (RVS02, RVS05, RVS06), T3 (RVS05), T6 (RVS04), T7 (RVS02, RVS04, RVS05) y T9 (RVS03) que tienen texto genérico de consultoría, un `SLE` fijo de €15.000 y un **`ALE` de €0.00**. Si el CFO ve un solo `ALE = 0.0` con textos como *"reducción de toil (cuando aplica)"*, desacreditará la metodología FAIR de las 10 torres en el acto.
2. **Contabilidad Múltiple del Mismo Siniestro (Inflación por Duplicidad):**
   * El **DBA único en Croacia** se cobra 4 veces (T4, T5, T8, T9).
   * Los **discos Linux dimensionados al límite (1 GB)** para detectar logs de SQL se cobran 4 veces (T3, T4, T7, T8).
   * Los **cortes eléctricos y los 500 metros de distancia en Sant Vicenç** se cobran 4 veces (T1, T2, T3, T5).
   * La **falta de RAM en HPE SimpliVity para hacer failover** se cobra 3 veces (dos veces dentro de T2 y una en T5).
   * El uso de **cuentas `root` compartidas** se cobra 3 veces (T4, T6, T10).
   * Los **ERPs congelados (FICOS, Primavera, SAP)** se cobran 3 veces (T3, T8, T10).
3. **Descalibración Financiera en Planta:** Mientras infláis el registro repitiendo riesgos administrativos, estáis subestimando brutalmente el coste de parada industrial. Nuestro **ALE total agregado suma €870.896** (apenas un **0.076%** de nuestros €1.144M de facturación). Valorar el bloqueo de las básculas de expedición en €17k (T10) o la destrucción total de ambos CPDs sin DR geográfico en €64k (T5) transmite una falsa sensación de seguridad.

**Mi Orden Ejecutiva:**  
Tenéis **48 horas** para ejecutar las directivas de remediación: erradicar los 9 riesgos con `ALE = €0.0`, asignar un único **Custodio Primario (`PRIMARY_CUSTODIAN`)** por cada hallazgo técnico eliminando las 18 duplicidades cruzadas, y recalibrar los `SLE` de parada de fábrica, básculas y ciberataque ESXi/NIS2 a costes industriales reales. Cuando el registro esté limpio, blindado y sin fisuras, iremos juntos al Consejo a conseguir el presupuesto.