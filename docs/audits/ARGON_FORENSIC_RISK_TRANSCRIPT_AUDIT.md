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

Aquí tienes la auditoría forense y cualitativa completa del registro de riesgos de **Molins**, contrastando línea por línea el JSON de las 10 torres (`T1` a `T10`, 66 riesgos en total) contra la transcripción bruta de la entrevista y el documento de síntesis de contexto.

---

### 1. EXPLICACIÓN TÉCNICA DEL `ALE = 0.0` (Despejando la duda del usuario)

En el registro actual existen exactamente **9 riesgos con `ALE = 0.0`**, distribuidos de la siguiente manera:
*   **T1:** `RVS02` (Hotspots/densidad), `RVS05` (Fugas de agua/condensación), `RVS06` (Game days de facilities).
*   **T3:** `RVS05` (Publicación de servicios Edge L4/L7).
*   **T6:** `RVS04` (Gestión de excepciones de hardening y drift).
*   **T7:** `RVS02` (Backlog y aging de tickets), `RVS04` (Madurez SRE: SLOs/SLIs y reducción de toil), `RVS05` (Correlación end-to-end y AIOps).
*   **T9:** `RVS03` (Ticket rate por problemas de acceso por 100 usuarios/mes).

#### Diagnóstico Empírico Forense: ¿Por qué valen cero?
**NO se trata de una deduplicación financiera entre torres (`TANGENTIAL_CONTRIBUTOR`).** Si observamos el metadato `"ownership_type"` de estos 9 registros en el JSON, todos están marcados como `"PRIMARY_CUSTODIAN"`, y todos tienen exactamente los mismos valores por defecto de frecuencia y magnitud (`"tef": 3.0, "lm": 3.0`).

La causa real es que **son placeholders automáticos de cuestionario no calibrados (`health_check_asis` boilerplate)**:
1.  **Patrón sintáctico idéntico (Plantilla de motor):** Los 9 riesgos comparten exactamente la misma estructura gramatical generada por máquina:
    *   *Finding:* `"Déficit en [nombre literal del ítem del cuestionario] y necesidad de automatización de controles técnicos."`
    *   *Business Risk:* `"Riesgo de degradación del servicio y pérdida de continuidad operativa ante incidencias no contenidas en [nombre literal del ítem del cuestionario]."`
2.  **Por qué ocurrió:** Como se evidencia al final de la transcripción, el consultor apenas le enseñó la plantilla Excel de preguntas al cliente al terminar la reunión (*"Ahora vendría el tercer punto que era los test... te lo puedo enviar"*). Al no haberse volcado aún respuestas cuantitativas calibradas de todas las pestañas del Excel o al no encontrar la IA evidencia en la transcripción para cubrir esos pilares obligatorios de la taxonomía del modelo, el motor rellenó los huecos vacíos de los pilares con el texto por defecto de la pregunta (`TEF=3, LM=3`) y dejó el cálculo actuarial en **`ALE = 0.0`** para no inventar pérdidas financieras sobre preguntas que nunca se hicieron en la entrevista.

---

### 2. RIESGOS BIEN DIAGNOSTICADOS (Aciertos Factuales de la IA)

De los 66 riesgos del registro, **57 riesgos están anclados en evidencia real de la entrevista**. El procesamiento del lenguaje natural ha capturado con gran precisión quirúrgica la casuística operativa de Molins. A continuación se detallan los mayores aciertos por torre:

*   **T1 (Physical Data Center):**
    *   **`T1-RVS01` (Cortes eléctricos en Sant Vicenç):** Captura fielmente que la fábrica sufre caídas eléctricas reales que ya han tumbado tanto el CPD Principal como el Secundario.
    *   **`T1-RVS03` (Fibra inter-CPD de 10 Gbps sin anillo):** Refleja la declaración exacta del cliente: los dos CPDs a 500m están unidos por un único camino físico de fibra (sin anillo cerrado).
    *   **`T1-RVS04` (Máquinas físicas OT remanentes y salas S/M/Cantera):** Recoge la existencia de equipamiento en cantera y salas técnicas con menor seguridad física que el CPD principal.
*   **T2 (Hybrid Cloud, Compute & Virtualization):**
    *   **`T2-RVS01` y `T2-RVS09` (Agotamiento de RAM en los 6 nodos HPE SimpliVity e invalidez del failover):** Excelente diagnóstico. Conecta el hecho de que los clústeres (especialmente los hosts 3 y 4 con cargas OT) están tan saturados de RAM que, aunque el árbitro de SimpliVity dispare la recuperación automática en 15 minutos, los nodos supervivientes no tienen memoria física para levantar todas las VMs (ni siquiera apagando Test).
    *   **`T2-RVS03` (vCenter antiguo con servidores deprecados para desarrolladores):** Captura el detalle de que reciclan hierro sin soporte fuera del clúster principal para cargas de desarrollo.
    *   **`T2-RVS06` y `T2-RVS07` (VM Sprawl >300 VMs y estrangulamiento de recursos):** Refleja que nunca se apagan las VMs que pide Desarrollo y que Test y Producción conviven apretados al máximo para no pedir CAPEX de nuevos nodos cada año.
    *   **`T2-RVS08` (Revisión manual "cada mañana" de vCenter):** Cita literalmente la costumbre del responsable de entrar cada mañana a mirar la consola *"antes de que explote"*.
*   **T3 (Enterprise Networks):**
    *   **`T3-RVS01` y `T3-RVS04` (Core Switches Huawei probados en caída brusca, pero limitados por los 500m y el cable único):** Refleja exactamente la topología real de red de campus/CPD.
    *   **`T3-RVS02` (Asimetría WAN/IT con SECIL y el proveedor NOS en Portugal):** Identifica el choque de modelos entre la gestión propia en España y el alquiler integral de recursos en NOS (Lisboa + 3 cementeras).
*   **T4 (Storage & Backup):**
    *   **`T4-RVS01` (Excepción de Proxmox + Storage HP + Synology en la cantera):** Captura el laboratorio/piloto real desplegado fuera del estándar NetApp/VMware.
    *   **`T4-RVS03` (Falta de DRP documentado para orquestar Cohesity y la 3ª copia en bloque "Guacamole"):** Recoge la arquitectura real de 3 capas de backup y la ausencia de un plan formal tras pasar de 3 personas históricas al equipo actual.
*   **T5 (Operational Continuity & DR):**
    *   **`T5-RVS01` (Falta de RTO/RPO con negocio e impacto en cola de camiones y Mossos d'Esquadra):** Captura de forma brillante el caso real de negocio: el único "RTO" informal hoy es que la cola de camiones parados en la báscula no llegue hasta la carretera general y provoque una sanción policial.
    *   **`T5-RVS04` (Scripts de autorremediación en Zabbix que enmascaran fallos crónicos):** Refleja cómo usan Zabbix para reiniciar o limpiar servicios que fallan repetitivamente por código legacy defectuoso.
*   **T6 (Cybersecurity & Identity Governance):**
    *   **`T6-RVS01` y `T6-RVS03` (Uso histórico de `root` y `full admin` y freno a la delegación):** Captura el dolor exacto de la transición hacia el nuevo equipo de Operaciones (1 interno + 3 externos), bloqueada porque antes entraban como superusuarios y ahora deben diseñar permisos privilegiados acotados.
    *   **`T6-RVS05` (613 días de uptime sin parcheo en ESXi):** Dato forense exacto visto en pantalla durante la sesión demostrativa de vCenter.
    *   **`T6-RVS06` (Frontera IT/OT en pesaje de silos y expedición de camiones):** Diagnóstico preciso de la interconexión mediante firewall entre la red OT de fábrica (gobernada por la unidad de negocio de Cemento) y la BBDD IT.
*   **T7, T8, T9 y T10 (ITSM, Estrategia, Workplace y Core/Planta):**
    *   **`T7-RVS01` / `T9-RVS06` (Escisión organizativa de Operaciones/ISAU):** Refleja que el equipo de N1/Operaciones quedó fuera del mando directo del área de Infraestructura (Aleix/entrevistado), dependiendo directamente de otra rama bajo Javier.
    *   **`T8-RVS01` / `T10-RVS04` / `T10-RVS06` (Deuda técnica de Oracle 10g/11g y Forms & Reports desde la crisis de 2008):** Captura la raíz histórica de las caídas diarias de bases de datos por consultas `SELECT` deficientes.
    *   **`T8-RVS04` (Hombre clave: DBA/Networking en Croacia y especialista en Kubernetes):** Identifica los dos silos críticos en un equipo de 5 personas (donde el manager pasa el día en reuniones y hubo una jubilación en diciembre no cubierta).
    *   **`T9-RVS04` (Wiki antigua en MoinMoin con madurez 3/5):** Cita la herramienta exacta y la nota que se autoadjudicó el cliente.
    *   **`T9-RVS08` (Fuga de conocimiento funcional en Desarrollo):** Recoge que de los 4 Product Owners actuales, solo 2 eran antiguos desarrolladores de Forms & Reports, apoyados por un pool variable de 20 a 40 externos.
    *   **`T10-RVS01` (Retirada de IBM iSeries a PostgreSQL/Excel y cementerio de ERPs M&A):** Captura tanto el proyecto de apagado del AS/400 (iSeries) de contabilidad este verano como las VMs congeladas de FICOS, Primavera y SAP antiguos por si hay inspección fiscal.

---

### 3. RIESGOS QUE FALTAN (Puntos Ciegos: Lo que Molins dijo y la IA se dejó fuera)

Al contrastar la transcripción completa con el JSON, se detectan **10 riesgos críticos explícitamente verbalizados por el cliente** que el proceso de extracción omitió por completo o diluyó hasta hacerlos invisibles:

1.  **Cuello de botella crítico en la contingencia de red hacia SAP S/4HANA en Google Cloud Ámsterdam (Falta en T3 / T5):**
    *   *Evidencia en entrevista:* SAP S/4HANA (migrado en febrero) es el sistema más crítico de Molins y está alojado en GCP Ámsterdam (por ser más barato en su día que Madrid), conectado vía fibra oscura hasta Equinix Barcelona (BA) y Equinix Fabric. El cliente afirma literalmente: *"Si algún día esa línea que tenemos con Equinix me cae, la VPN secundaria [IPSec] no es capaz de asumir todo el ancho de banda que se necesita"*.
    *   *Fallo del registro:* No hay ni un solo riesgo en `T3` ni en `T5` sobre la insuficiencia de ancho de banda de la VPN de respaldo de SAP ni la dependencia del circuito único hacia Equinix Barcelona.
2.  **Obsolescencia extrema de Sistemas Operativos Linux (`CentOS 5` y `CentOS 6` en producción) y ausencia total de ventanas de mantenimiento pactadas (Falta en T6 / T2):**
    *   *Evidencia en entrevista:* El cliente confiesa: *"Desplegábamos una máquina virtual y se quedaba esa máquina virtual CentOS 5 o CentOS 6 y CentOS tenemos ahora... no tenemos la ventana de mantenimiento con negocio pactadas, no tenemos el plan de migrar a Rocky Linux 9 o 10... con los modelos estos de IA te encuentran vulnerabilidades en cero coma"*.
    *   *Fallo del registro:* `T6-RVS05` habla de los 613 días de ESXi, pero **omite por completo** que tienen servidores en `CentOS 5` (EOL en 2017) y `CentOS 6` (EOL en 2020) sin parches de INCIBE y sin ventanas de mantenimiento acordadas con el negocio.
3.  **"Shadow IT / Shadow OT" en plantas remotas: Despliegue incontrolado de Wi-Fi, cámaras y salas técnicas B (Falta en T3 / T6):**
    *   *Evidencia en entrevista:* En las plantas de hormigón (Proxa) y prefabricados (Precast), el departamento industrial actúa por libre: *"Tienen una Shadow sala técnica, hay otra sala técnica B... hubo una temporada que se pusieron a desplegar cámaras de seguridad por su propia cuenta o puntos de acceso Wi-Fi. Luego cuando falla te dicen 'oye, que no me va la Wi-Fi de aquí'. 'Tú no tienes Wi-Fi'. 'Sí, sí que tengo Wi-Fi'"*.
    *   *Fallo del registro:* No se ha registrado el riesgo de seguridad y soporte derivado de redes inalámbricas y dispositivos IP no autorizados conectados en las plantas remotas.
4.  **Punto único de fallo en el firewall de delegaciones/plantas (Tallas S y M) y bloqueo de hormigoneras (Falta en T3):**
    *   *Evidencia en entrevista:* *"Si a mí se me cae el firewall de la delegación, ellos se quedan sin acceso a nada... no sólo está el cliente de oficina que quiera acceder a SAP, sino que también está la hormigonera y otro tipo de servicios que dependen de tener conectividad"* (mientras Ciberseguridad aún está desplegando Netskope ZTNA y preparando el cambio a Fortinet en agosto).
    *   *Fallo del registro:* No aparece en `T3` la fragilidad de las plantas talla S (Proxa) y M (Construction Solutions / Precast) ante la caída del equipo de borde local.
5.  **Herencia de Controladores de Dominio de solo lectura (RODC) y servidores de ficheros obsoletos en las 9 plantas de Precast (Falta en T4 / T6 / T10):**
    *   *Evidencia en entrevista:* Por problemas históricos de ADSL en polígonos industriales, dejaron desplegados en las 9 delegaciones de Precast servidores locales que hacen de *"controlador de dominio de lectura y servidor de ficheros, y eso se ha quedado allí histórico"*.
    *   *Fallo del registro:* Omitido como vector de superficie de ataque de Active Directory y deuda técnica distribuida.
6.  **Riesgo en la base de datos crítica `Prenet` (mini-ERP de prefabricados de hormigón en OCI) sin réplica activa y RTO no probado (Falta en T5 / T10):**
    *   *Evidencia en entrevista:* La aplicación más crítica fuera de SAP es `Prenet`, cuya base de datos está en Oracle Cloud (OCI) **sin replicación activa (standby)**, dependiendo exclusivamente de levantar una instancia desde cero y volcar el backup nocturno (estimando a ojo *"tres horas"*, sin pruebas formales documentadas).
    *   *Fallo del registro:* `Prenet` y `OCI` ni siquiera se mencionan en todo el JSON de riesgos.
7.  **Exposición financiera y bloqueo por renovación de licencias VMware/Broadcom en Mayo de 2027 (Falta en T2 / T8):**
    *   *Evidencia en entrevista:* El cliente lo llama literalmente *"la dolorosa"* de mayo de 2027 y evalúa alternativas urgentes (Proxmox, Syneto, Nutanix o Private Cloud).
    *   *Fallo del registro:* `T8-RVS05` habla del hardware HPE SimpliVity de 2018, pero **omite la fecha crítica de mayo de 2027 de Broadcom/VMware**, que es el verdadero detonante temporal del roadmap.
8.  **Incumplimiento potencial o falta de preparación ante la Directiva NIS2 (Falta en T6 / T8):**
    *   *Evidencia en entrevista:* Están en pleno análisis de impacto de **NIS2** (inmutabilidad del dato, gestión de vulnerabilidades, continuidad en sector crítico de materiales de construcción).
    *   *Fallo del registro:* La palabra `NIS2` no aparece en ningún riesgo de `T6` ni `T8`.
9.  **Fricción en el proceso de Compras / RFP que retrasa proyectos tecnológicos (Falta en T8):**
    *   *Evidencia en entrevista:* *"Esto es una guerra que tenemos con el departamento de Compras"*: Infraestructura diseña la solución con su partner de confianza (HP, NetApp, Dagram) y cuando va a comprar, Compras bloquea o se enfada exigiendo abrir una RFP a tres proveedores desde cero.
    *   *Fallo del registro:* Ausente en la torre de Gobierno y FinOps (`T8`).
10. **Fragilidad de la capa de integración y API Manager (`WSO2`) hacia SAP S/4HANA y caída recurrente de Atlassian Cloud (Falta en T7 / T10):**
    *   *Evidencia en entrevista:* Todo lo que conecta con SAP S/4HANA pasa por web services mediante el API Manager **WSO2** (*"que ahora estamos migrando a ver si cambiamos"*), y además mencionan que desde que subieron la herramienta de ticketing a **Atlassian Cloud** ya han sufrido **3 caídas del servicio** (algo que no les ocurría on-premise). Ninguno de los dos puntos figura en el registro.

---

### 4. RIESGOS QUE SOBRAN (Ruido, Relleno de Catálogo y Alucinaciones)

Para que el informe tenga credibilidad total ante la dirección de Molins, se deben depurar tres categorías de ruido detectadas en el JSON:

#### A. Los 9 Rellenos de Plantilla de Cuestionario (`ALE = 0.0`) — **ELIMINAR O SUSTITUIR**
Como se demostró en el apartado 1, estos 9 riesgos son frases genéricas de catálogo que **nunca se hablaron en la entrevista**:
*   **`T1-RVS02`** (*"Déficit en gestión de hotspots y densidad por rack"*): Nadie habló de temperatura por rack ni de hotspots térmicos en los 6 nodos SimpliVity.
*   **`T1-RVS05`** (*"Déficit en gestión de riesgos ambientales asociados: fugas de agua, condensación"*): Nunca mencionado.
*   **`T1-RVS06`** (*"Déficit en pruebas operativas periódicas: game days de facilities"*): Irrelevante cuando el cliente ya dijo que sufren cortes eléctricos reales que sirven de prueba forzosa.
*   **`T3-RVS05`** (*"Déficit en publicación de servicios edge L4/L7"*): Relleno puro de plantilla.
*   **`T6-RVS04`** (*"Déficit en gestión de excepciones de hardening y control de drift"*): Relleno de plantilla (debería sustituirse por el riesgo real de `CentOS 5/6` y falta de ventanas de parcheo).
*   **`T7-RVS02`** (*"Déficit en backlog y aging de tickets"*): **Contradice directamente la entrevista.** El cliente dijo textualmente: *"El SLA de cumplimiento de tickets lo cerramos, entregamos a tiempo"* (aunque luego admitió que Atlassian Cloud se les ha caído 3 veces).
*   **`T7-RVS04`** (*"Déficit en madurez SRE: SLOs/SLIs y reducción de toil"*): Jerga de catálogo no aplicable al contexto real discutido.
*   **`T7-RVS05`** (*"Déficit en correlación end-to-end y AIOps"*): Relleno de plantilla.
*   **`T9-RVS03`** (*"Déficit en ticket rate por problemas de acceso por 100 usuarios/mes"*): Relleno de plantilla; además, el propio consultor dijo en la reunión que la pestaña de *Digital Workplace* probablemente ni aplicaba a este interlocutor (*"por ejemplo, oye, mira la parte de digital workplace, pues esta no la vamos a contestar porque no ha lugar"*).

#### B. Pequeñas Alucinaciones o Contradicciones con la Transcripción — **CORREGIR MATIZ**
*   **`T2-RVS04` (*"Inexistencia de plataformas de contenedores; la totalidad de las cargas se despliegan sobre VMs"*):** Es **inexacto**. El cliente declaró explícitamente que ya fichó a un especialista en **Kubernetes** para el cambio de modelo a contenedores y que además compraron la cabina **NetApp** aprovechando para desplegar almacenamiento persistente para contenedores (S3/Kubernetes) en local sin ir al cloud. Lo correcto es diagnosticar una *transición incipiente a contenedores con alta dependencia de un único especialista*, no la "inexistencia" de la plataforma.
*   **`T8-RVS06` (*"Ausencia de métricas formales de SLA en el cumplimiento de tickets internos"*):** El cliente afirmó en la entrevista que sí cumplen sus SLAs de tickets internos a tiempo; donde no tienen acuerdos formales es en los **RTO/RPO con negocio** y en las **ventanas de mantenimiento**, además de que el contrato de HPE es de tiempo de respuesta (4h) y no de resolución (CTR). Conviene ajustar la redacción para no contradecir su afirmación sobre los tickets.

#### C. Redundancia Masiva Inter-Torres (Mismo hallazgo repetido hasta 5 veces con `PRIMARY_CUSTODIAN`) — **CONSOLIDAR CUSTODIA**
La IA ha tomado los 7 grandes dolores de la entrevista y los ha clonado en casi todas las torres adjudicándoles a todas el rol de `PRIMARY_CUSTODIAN` (sumando ALE en todas ellas por el mismo hecho físico):
1.  **El truco de dejar 1 GB de disco en servidores Linux para pillar logs descontrolados de SQL:** Está cobrado cuatro veces como `PRIMARY_CUSTODIAN` en **`T2-RVS07`**, **`T3-RVS07`** (¿qué tiene que ver la red WAN con que se llene el disco local de un Apache/Linux?), **`T4-RVS02`**, **`T7-RVS03`** y **`T8-RVS07`**. En `T3` sobra por completo.
2.  **Los CPDs a 500m y los cortes eléctricos de Sant Vicenç:** Cobrado cinco veces como `PRIMARY_CUSTODIAN` en **`T1-RVS01`**, **`T2-RVS02`**, **`T3-RVS01`**, **`T5-RVS05`** y **`T5-RVS08`**.
3.  **El agotamiento de RAM en SimpliVity (nodos 3 y 4) ante un failover:** Cobrado cuatro veces dentro de `T2` y `T5` (**`T2-RVS01`**, **`T2-RVS09`**, **`T5-RVS06`**).
4.  **El DBA en Croacia y el especialista de Kubernetes (Hombre clave):** Cobrado cuatro veces como `PRIMARY_CUSTODIAN` en **`T4-RVS05`**, **`T5-RVS03`**, **`T8-RVS04`** y **`T9-RVS05`**.
5.  **El modelo externalizado de SECIL con NOS en Portugal:** Repetido cinco veces en **`T3-RVS02`**, **`T4-RVS01`**, **`T5-RVS02`**, **`T6-RVS02`** y **`T9-RVS01`**.
6.  **Los ERPs congelados de compras M&A (FICOS, Primavera, SAP):** Repetido cuatro veces en **`T3-RVS03`**, **`T6-RVS02`**, **`T8-RVS03`** y **`T10-RVS01`**.

---

### 5. CONCLUSIÓN Y PLAN DE ACCIÓN RECOMENDADO

El diagnóstico capturado por la IA tiene una **base factual excelente (86% de los riesgos provienen directamente de la boca del cliente)**, pero presenta tres defectos de ensamblaje típicos de cruzar una entrevista libre con una matriz rígida de 10 torres:
1.  Rellenó con texto genérico y `ALE = 0.0` los 9 pilares donde no había respuestas del cuestionario Excel.
2.  Multiplicó los mismos 6 hallazgos estrella de la entrevista en múltiples torres como `PRIMARY_CUSTODIAN` (inflando o dispersando el riesgo).
3.  Dejó fuera 10 riesgos técnicos muy concretos que el cliente verbalizó de pasada (VPN de SAP insuficiente, CentOS 5/6 EOL, Shadow Wi-Fi/cámaras en plantas, Prenet en OCI sin réplica, renovación Broadcom Mayo 2027, NIS2, WSO2, Compras).

#### Pasos concretos para dejar el Registro de Riesgos 100% blindado:
1.  **Purgar los 9 riesgos con `ALE = 0.0` y sustituirlos por los Puntos Ciegos reales de la entrevista:**
    *   En **`T3`**, eliminar `T3-RVS05` (`ALE=0`) y `T3-RVS07` (logs de Linux en torre de red) e insertar: **(a) Insuficiencia de ancho de banda de la VPN IPSec de contingencia hacia SAP S/4HANA en GCP Ámsterdam ante caída de Equinix Fabric**, y **(b) Punto único de fallo en firewalls de plantas remotas (Proxa/Precast) y despliegue de Shadow Wi-Fi/cámaras por el área industrial**.
    *   En **`T6`**, eliminar `T6-RVS04` (`ALE=0`) e insertar: **Persistencia de sistemas operativos en End-of-Life severo (`CentOS 5` y `CentOS 6`) sin ventanas de mantenimiento pactadas con negocio y brecha de adecuación a la directiva `NIS2`**.
    *   En **`T5` / `T10`**, incorporar el riesgo de **Ausencia de réplica activa en OCI para el sistema crítico `Prenet` (prefabricados) y dependencia de restauración manual desde backup nocturno (RTO estimado de 3h no validado)**, junto con la migración pendiente del API Manager **`WSO2`**.
    *   En **`T8`**, incorporar **Hito crítico de renovación de licenciamiento VMware/Broadcom (Mayo 2027)** y **Fricción operativa en el flujo de adjudicación con el área de Compras (RFP vs. prescripción técnica)**.
    *   En **`T7`**, eliminar los tres placeholders con `ALE=0` (`RVS02, RVS04, RVS05`) y reflejar las **caídas recurrentes de disponibilidad sufridas tras migrar la gestión de tickets a Atlassian Cloud**.
2.  **Aplicar la regla `TANGENTIAL_CONTRIBUTOR` en los riesgos transversales:**
    *   Mantener el coste primario (`PRIMARY_CUSTODIAN`) de la caída eléctrica en `T1`/`T5`, el de saturación de RAM de SimpliVity en `T2`, el de los logs de 1 GB en `T7`/`T10`, y el del DBA de Croacia en `T8`, pasando sus duplicados en las demás torres a `TANGENTIAL_CONTRIBUTOR` para evitar doble contabilidad y demostrar rigor metodológico ante el CIO/CISO de Molins.