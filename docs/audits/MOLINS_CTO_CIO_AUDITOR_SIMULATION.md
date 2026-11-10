# ACTA DE LA SESIÓN DE REVISIÓN ADVERSARIAL: ANEXOS ESPECIALISTAS (T1 - T10)
**Ubicación:** Sala del Consejo, Complejo Industrial de Sant Vicenç dels Horts (Molins)  
**Asistentes:**  
* **CTO (Chief Technology Officer):** Veterano de ingeniería industrial y planta. Conoce cada rack, cada nodo SimpliVity, las canteras y el sistema de básculas. Alérgico a la literatura de consultoría.  
* **CIO (Chief Information Officer):** Responsable corporativo ante el Comité Ejecutivo y el Consejo. Enfoque en presupuestos, defensa ante el comité de auditoría, el "muro" de Broadcom en 2027, la deuda de SECIL (Portugal) y la supervivencia de su equipo de 5 personas.  
* **Auditor Forense (Tier-1 Nitpicker):** Especialista en aseguramiento de calidad documental, caza de contradicciones cruzadas entre torres, validación de coherencia con el riesgo cuantificado (ALE) y detección de "relleno" o alucinaciones.

---

## T1: Centro de Datos Físico e Instalaciones
*(Score: 2.61 | ALE: 94.829 €)*

* **Reacción del CTO:**  
  > "Por fin alguien escribe la verdad sin edulcorarla. CPD 1 y CPD 2 están a 500 metros dentro de la misma fábrica de Sant Vicenç; si cae la subestación o tenemos un incendio grave en el recinto, nos quedamos a oscuras en los dos sitios a la vez. Y el detalle del polvo de clínker y áridos comiéndose los switches en las casetas de las plantas de hormigón es exactamente lo que vivo cada semana. Físicamente exacto."
* **Reacción del CIO:**  
  > "El *Bottom Line* es demoledor y muy útil para que el Comité Ejecutivo entienda por qué dos salas no significan tener un DRP real. Con casi 95.000 € de ALE, me da el argumento económico exacto para pedir CAPEX de adecuación ambiental en plantas o mover cargas críticas fuera de Sant Vicenç."
* **Crítica del Auditor Forense:**  
  > **Fallo de contradicción interna y repetición:** En *Operational Benefits* se afirma que existe "Doble acometida eléctrica independiente", pero inmediatamente en *Structural Risks* se dice "compartiendo dominio de riesgo ambiental y acometida municipal". ¿Es independiente o comparten acometida municipal? Técnicamente son dos líneas que van a la misma subestación local, pero la redacción se contradice frontalmente. Además, el beneficio del enlace a Equinix Fabric se repite casi palabra por palabra en T3.
* **Puntuación de la Torre:** **8.5 / 10**

---

## T2: Cómputo Híbrido y Plataformas
*(Score: 1.89 | ALE: 162.695 €)*

* **Reacción del CTO:**  
  > "Clavado. Los 6 nodos HPE SimpliVity van al 85% de RAM, y los nodos 3 y 4 están sudando tinta porque hemos mezclado producción de planta (OT) con entornos de pruebas. Si hoy peta una placa base de un nodo, el árbitro externo no hace milagros: el vSphere colapsa por falta de memoria libre y paramos fábrica. Y sí, esas 30 máquinas con CentOS 5 y 6 me quitan el sueño, nadie se atreve a tocarlas."
* **Reacción del CIO:**  
  > "Es nuestra torre con peor nota (1.89) y el mayor riesgo financiero de todo el informe (162.695 € de ALE). El resumen ejecutivo justifica al 100% la urgencia de ampliar hardware o limpiar cargas antes de que tengamos una caída masiva. Muy defendible ante el CFO."
* **Crítica del Auditor Forense:**  
  > **Inconsistencia de encuadre:** El tercer riesgo estructural habla de "Adopción embrionaria de contenedores sin orquestador gestionado". Siendo una torre con un ALE de 162k € dominada por colapso de RAM y sistemas operativos muertos (CentOS 5/6), meter la falta de Kubernetes gestionado como uno de los 3 riesgos estructurales principales diluye la gravedad industrial. Además, el título es "Cómputo Híbrido" pero el texto ignora por completo la pata cloud (GCP Ámsterdam, que sí aparece en T3).
* **Puntuación de la Torre:** **9.0 / 10**

---

## T3: Redes y Conectividad
*(Score: 2.56 | ALE: 24.386 €)*

* **Reacción del CTO:**  
  > "El concepto de topología 'Sant Vicenç-céntrica' haciendo *tromboning* es tal cual. Todo pasa por aquí. Los Huawei de core aguantan bien con LACP, pero en las plantas remotas tenemos switches de acceso que son piezas de museo sin soporte y colgando de una sola fibra. Si una excavadora rompe el cable en una cantera, esa planta queda aislada."
* **Reacción del CIO:**  
  > "El diagnóstico arquitectónico es claro, pero tengo un problema al presentarlo al Consejo: la narrativa suena catastrófica ('aísla la conectividad de las plantas', 'SPOF en delegaciones'), pero el ALE es de solo 24.386 € al año. El director financiero me va a decir que por 24.000 euros de riesgo anual no me aprueba duplicar líneas WAN en todas las plantas."
* **Crítica del Auditor Forense:**  
  > **Redundancia inter-torre y desalineación cuantitativa:** El beneficio 2 ("Conectividad dedicada de fibra oscura entre la sede central y Equinix Fabric...") es un duplicado directo del beneficio 3 de la Torre 1. Asimismo, confirmo la alerta del CIO: hay una disonancia severa entre la severidad léxica del *Bottom Line* (SPOF total de comunicaciones) y un ALE marginal de 24k €.
* **Puntuación de la Torre:** **8.0 / 10**

---

## T4: Servicios de Datos y Almacenamiento
*(Score: 3.26 | ALE: 24.601 €)*

* **Reacción del CTO:**  
  > "NetApp FAS y Cohesity es lo mejor que tenemos montado en la casa, por eso saca un 3.26. Es verdad que no tenemos MetroCluster síncrono entre el CPD 1 y el CPD 2 y que si cae la cabina principal nos toca picar piedra a mano para levantar el almacenamiento secundario. También es cierto que los backups pesados se pisan con el turno de mañana."
* **Reacción del CIO:**  
  > "Un resumen muy equilibrado. Pone en valor la inversión que ya hicimos en NetApp y Cohesity (la regla 3-2-1 y la inmutabilidad contra ransomware tranquilizan mucho al Comité de Auditoría), y señala mejoras operativas que no requieren millones de euros, sino orden."
* **Crítica del Auditor Forense:**  
  > **Solapamiento funcional con T5:** El tercer riesgo estructural ("Ausencia de pruebas programadas y automatizadas de restauración...") invade directamente las competencias de la Torre 5 (Resiliencia y Continuidad). De hecho, es casi idéntico al primer y tercer riesgo de T5. En T4 debería haberse ceñido a rendimiento de I/O, capacidad y arquitectura de cabinas.
* **Puntuación de la Torre:** **8.5 / 10**

---

## T5: Resiliencia y Continuidad Operativa
*(Score: 2.20 | ALE: 115.468 €)*

* **Reacción del CTO:**  
  > "El segundo riesgo estructural da en el clavo del problema cultural de Molins: 'Ausencia de ventanas de mantenimiento pactadas con cemento y hormigón'. Los jefes de planta quieren que los hornos y las expediciones funcionen 24/7, no nos dejan parar ni dos horas un domingo para parchear o probar un failover, y luego se quejan si algo falla. Necesito que el Consejo lea esto."
* **Reacción del CIO:**  
  > "Con 115.468 € de ALE, esta torre me da la palanca política que necesito frente a los Directores de Negocio de Cemento y Hormigón. No es un problema de comprar más máquinas, es un problema de gobierno operativo: sin ventanas pactadas y un DRP formal, estamos vendidos."
* **Crítica del Auditor Forense:**  
  > **Fricción técnica con T10 y vaguedad:** El beneficio 2 menciona "procedimientos de contingencia operativa manual en plantas industriales para mantener la carga física durante cortes breves". Esto se solapa con el modo desconectado de básculas de T10, pero aquí se redacta de forma genérica. Además, el *Bottom Line* y los riesgos 1 y 3 dicen exactamente lo mismo con distintas palabras (no hay DRP formal, no hay orquestación, el RTO depende de pasos manuales). Hay redundancia intra-torre.
* **Puntuación de la Torre:** **8.0 / 10**

---

## T6: Seguridad de Infraestructura e Identidad
*(Score: 2.82 | ALE: 96.384 €)*

* **Reacción del CTO:**  
  > "Me duele admitirlo, pero es así. Todos usamos el mismo usuario `root` en los Linux y cuentas genéricas en los switches y el vCenter sin MFA porque cuando hay una urgencia a las 3 de la mañana con un camión parado en la báscula, nadie quiere pelearse con un token. Y sí, desde la red de oficinas se llega demasiado fácil a las redes de los PLC de planta."
* **Reacción del CIO:**  
  > "Si el Comité de Auditoría lee que compartimos `root` sin MFA ni trazabilidad y que no hay microsegmentación IT/OT, se les van a poner los pelos de punta. Pero es necesario: destaca que ya tenemos Netskope y AD funcionando bien en el perímetro de usuario, y centra el tiro en el bastionado interno (PAM/MFA) y segmentación industrial."
* **Crítica del Auditor Forense:**  
  > **Colisión de gestión de identidad con T9:** En T6 (Beneficio 2) se afirma que la gestión centralizada de identidades se soporta en "Microsoft Active Directory". En T9 (Beneficio 2) se afirma que la gestión unificada de identidades es mediante "Microsoft Entra ID". Aunque en un entorno híbrido coexisten (AD on-prem + Entra ID cloud), presentarlos de forma aislada en dos torres distintas sin explicar la sincronización parece una contradicción de inventario. Por lo demás, la torre es implacable y precisa.
* **Puntuación de la Torre:** **9.0 / 10**

---

## T7: Gestión de Servicios de TI y Operaciones Digitales
*(Score: 2.43 | ALE: 78.962 €)*

* **Reacción del CTO:**  
  > "Zabbix y Grafana nos salvan la vida para ver qué pasa, pero somos 5 gatos para todo el grupo. Y el riesgo 1 es el elefante en la habitación: nuestro especialista en remoto que lleva las bases de datos Oracle y la red avanzada. Si mañana ese hombre coge una baja larga o se va, literalmente no sabemos cómo tocar ciertas configuraciones críticas."
* **Reacción del CIO:**  
  > "¡Gracias! Llevo dos años intentando explicar a Recursos Humanos y al CEO que con 5 personas internas no puedo hacer mantenimiento, apagar fuegos en las básculas y además liderar proyectos de transformación. Nombrar explícitamente el *Key Person Dependency* y la falta de SLAs formales con un coste de riesgo de casi 79.000 € es oro puro para pedir headcount o servicios gestionados de nivel 2/3."
* **Crítica del Auditor Forense:**  
  > **Ejecución impecable:** Esta torre no tiene grasa. Conecta perfectamente la métrica de plantilla (5 especialistas), la herramienta real (Zabbix/Grafana), la vulnerabilidad específica (1 especialista remoto para BBDD y redes) y la deficiencia de procesos ITIL (Service Desk N1 desconectado del N2/N3 y sin catálogo SLA). Cero alucinaciones.
* **Puntuación de la Torre:** **9.5 / 10**

---

## T8: Estrategia Tecnológica, Gobierno y FinOps
*(Score: 2.45 | ALE: 109.028 €)*

* **Reacción del CTO:**  
  > "A mí la parte financiera me queda más lejos, pero la consecuencia técnica la sufro: siempre hemos ido poniendo parches tácticos para no gastar. Y lo de SECIL en Portugal es un mundo aparte que nos ha caído encima sin haber limpiado nuestra propia casa."
* **Reacción del CIO:**  
  > "Esta es MI torre para el Consejo de Administración. Pone encima de la mesa las dos bombas de relojería estratégicas: el sablazo de Broadcom/VMware en la renovación de 2027 y la digestión tecnológica de la compra de SECIL en Portugal. Además, reconoce que hemos llevado un control de costes estricto hasta ahora, lo que evita que parezca que hemos gestionado mal. Muy elegante y político."
* **Crítica del Auditor Forense:**  
  > **Repetición interna:** El *Bottom Line* y los *Structural Risks* 1 y 2 son espejos exactos (Broadcom 2027 y deuda técnica de SECIL). No aporta un matiz adicional en los bullets respecto al párrafo superior. Además, menciona "FinOps" en el título y en el riesgo 3, pero el contenido habla de CAPEX industrial tradicional y licenciamiento on-premise (VMware), no de gobierno de gasto variable en nube pública, que es la definición técnica de FinOps.
* **Puntuación de la Torre:** **8.5 / 10**

---

## T9: Puesto de Trabajo Digital y Servicios de Usuario
*(Score: 3.19 | ALE: 9.453 €)*

* **Reacción del CTO:**  
  > "En las oficinas de Sant Vicenç todo el mundo va con su Teams y su Office 365 impecable, pero bajas a las 9 delegaciones de hormigón y prefabricados y tienes PCs llenos de polvo conectados por puerto serie a las básculas, y unos servidores físicos locales debajo de una mesa que nadie administra. Si uno de esos servidores casca, esa planta de hormigón se para."
* **Reacción del CIO:**  
  > "La nota es alta (3.19) y el ALE es muy bajo (9.453 €) porque el despliegue corporativo de M365 está consolidado. El enfoque en la brecha entre el trabajador de cuello blanco y el operario de planta es muy acertado."
* **Crítica del Auditor Forense:**  
  > **Anomalía de clasificación arquitectónica (Violación de Frontera de Torre):** ¿Qué hacen "servidores físicos locales no gestionados en las 9 delegaciones de hormigón que operan como puntos únicos de fallo" dentro de la Torre 9 (*Puesto de Trabajo Digital / End-User Computing*)? Un servidor local de planta pertenece a la **Torre 2 (Cómputo)** o a la **Torre 1 (Instalaciones remotas)**. Además, si esos 9 servidores son "puntos únicos de fallo para la operativa diaria de la planta", ¿cómo es posible que el ALE de toda la torre sea de apenas 9.453 €? Hay una contradicción matemática entre decir que paran una planta y asignarle un impacto financiero irrelevante.
* **Puntuación de la Torre:** **7.0 / 10**

---

## T10: Sistemas Transaccionales Core y Plataformas Críticas
*(Score: 2.40 | ALE: 50.730 €)*

* **Reacción del CTO:**  
  > "Esto es el corazón de Molins. Oracle Forms & Reports sobre Oracle 10g y 11g gobernando el despacho de cemento y las básculas. Si el Forms se cuelga, no hay albarán; si no hay albarán, la barrera no sube y en 20 minutos tenemos una cola de bañeras de cemento colapsando la rotonda de entrada a la fábrica. Al menos reconoce que las básculas tienen un modo autónomo temporal para caídas breves de red, pero como se bloquee la base de datos central, estamos muertos."
* **Reacción del CIO:**  
  > "Traduce perfectamente un problema informático árido (versiones obsoletas de Oracle) en un riesgo físico que cualquier consejero entiende: camiones parados en la puerta y facturación detenida. Y el tercer riesgo —que ya no quedan programadores en el mercado para mantener Forms & Reports— justifica por sí solo el proyecto de modernización de aplicaciones."
* **Crítica del Auditor Forense:**  
  > **Repetición literal intra-torre y omisión de ERP:** El *Bottom Line* dice: *"cualquier bloqueo en el software de expedición detiene físicamente la salida de cemento y hormigón"*. El Riesgo Estructural 2 dice: *"cualquier bloqueo del software de pesaje detiene la salida de camiones"*. Es un copiar-pegar dentro del mismo bloque de 150 palabras. Además, la torre se titula "Sistemas Transaccionales Core", pero se centra exclusivamente en el sistema MES/Expedición en Oracle Forms, omitiendo por completo qué ocurre con el ERP corporativo financiero/logístico y su integración con este legacy.
* **Puntuación de la Torre:** **8.5 / 10**

---

## CUADRO DE MANDO INTEGRAL DE LA REVISIÓN (SCORECARD)

| Torre | Dominio | Score | ALE (€) | Nota del Comité (0-10) | Estado de Auditoría |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T1** | Centro de Datos Físico e Instalaciones | 2.61 | 94.829 € | **8.5** | Contradicción leve en acometida eléctrica; realidad física exacta. |
| **T2** | Cómputo Híbrido y Plataformas | 1.89 | 162.695 € | **9.0** | Muy sólida. Dato exacto de SimpliVity (85% RAM, nodos 3 y 4) y CentOS 5/6. |
| **T3** | Redes y Conectividad | 2.56 | 24.386 € | **8.0** | Duplica el texto de Equinix con T1; ALE muy bajo para un tono tan grave. |
| **T4** | Servicios de Datos y Almacenamiento | 3.26 | 24.601 € | **8.5** | Bien aterrizada en NetApp/Cohesity; el riesgo 3 invade ligeramente T5. |
| **T5** | Resiliencia y Continuidad Operativa | 2.20 | 115.468 € | **8.0** | Gran acierto con las ventanas de negocio; redundancia interna en el texto. |
| **T6** | Seguridad de Infraestructura e Identidad | 2.82 | 96.384 € | **9.0** | Brutalmente honesta (`root` compartido, sin MFA, IT/OT). |
| **T7** | Gestión de Servicios de TI y Operaciones | 2.43 | 78.962 € | **9.5** | **Mejor Torre.** Clava los 5 técnicos, Zabbix y el especialista único remoto. |
| **T8** | Estrategia Tecnológica, Gobierno y FinOps | 2.45 | 109.028 € | **8.5** | Excelente enfoque ejecutivo (Broadcom 2027 + SECIL); uso laxo de "FinOps". |
| **T9** | Puesto de Trabajo Digital | 3.19 | 9.453 € | **7.0** | **Torre más débil.** Mete servidores de las 9 plantas en EUC con un ALE irrisorio. |
| **T10**| Sistemas Transaccionales Core | 2.40 | 50.730 € | **8.5** | Muy realista (Oracle 10g/11g, Forms, básculas); repetición de frase interna. |
| **MEDIA** | **CONSOLIDADO GLOBAL** | **2.58** | **766.536 €** | **8.45 / 10** | **Aprobado con alto rigor industrial y mínimas fricciones editoriales.** |

---

## VEREDICTO FINAL: ¿FIRMAN EL CTO Y EL CIO PARA EL CONSEJO DE MAÑANA?

### **SÍ, FIRMAN (CON 3 CORRECCIONES DE 15 MINUTOS ANTES DE IMPRIMIR).**

* **Veredicto del CTO:**  
  > *"Firmo. Llevo veinte años viendo pasar consultoras por Sant Vicenç que nos entregan copias pegadas de bancos o aseguradoras. Quien ha escrito esto ha estado aquí o se ha leído hasta la última línea de nuestras actas técnicas: sabe que los nodos 3 y 4 de SimpliVity van ahogados, sabe que las dos salas están a 500 metros, sabe que hay polvo de hormigón en los racks remotos y sabe que si se cuelga el Oracle Forms se lía un atasco de camiones en la báscula. No me avergüenza defender este documento mañana."*

* **Veredicto del CIO:**  
  > *"Firmo. Me da exactamente el relato que necesito para el Consejo de Administración: reconoce lo que hemos hecho bien con pocos recursos (NetApp, Cohesity, Netskope, M365) y pone nombre, apellidos y euros de riesgo (766k € de ALE total) a lo que no podemos seguir aguantando con un equipo de 5 personas. Además, prepara al Consejo para la factura de Broadcom de 2027 y la integración de SECIL. Solo pido al equipo redactor que en los próximos 15 minutos corrija los tres detalles que ha cazado el auditor: aclarar que la doble acometida de T1 va a la misma subestación municipal, quitar la frase repetida de Equinix entre T1 y T3, y explicar que los 9 servidores de las plantas de hormigón en T9 son equipos de borde ligados a los puestos de pesaje. Hecho eso, va directo a la carpeta del CEO."*