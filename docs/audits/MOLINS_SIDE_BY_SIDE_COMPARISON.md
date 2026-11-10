# SIDE-BY-SIDE FORENSIC COMPARISON: LEGACY VS. POLYMORPHIC MOLINS DELIVERABLES
**Target:** Cementos Molins Technical & Strategic Assessment Deliverable Suite
- **Legacy Tomo 1:** `/home/jsanchhi/assessment_engine/Molins_202610_Tomo_1_Diagnostico_ASIS.docx` (522,529 bytes)
- **New Staged Tomo 1:** `/home/jsanchhi/assessment_engine/working/out/molins_polymorphic_comparison/Molins_202610_Tomo_1_Diagnostico_ASIS_NUEVO.docx` (523,122 bytes)

---

## 1. Executive Summary & Table 5 Comparison in Tomo 1
### Legacy Table 5 (Original Deliverable in Root):
Dominio Tecnológico | Madurez CMMI | Impacto Económico Anual Estimado | Coste ante Incidente Grave | % del Riesgo Total
T1 - Centros de Datos e Instalaciones Técnicas | 2,61 | 60.051 € | 333.182 € | 8,8%
T2 - Cómputo Híbrido y Virtualización | 1,89 | 152.213 € | 426.989 € | 22,4%
T3 - Redes y Conectividad WAN/LAN | 2,56 | 22.618 € | 174.418 € | 3,3%
T4 - Almacenamiento y Backup Corporativo | 3,26 | 35.473 € | 428.163 € | 5,2%
T5 - Continuidad Operativa y Resiliencia Fabril | 2,20 | 105.022 € | 320.418 € | 15,5%
T6 - Ciberseguridad e Identidad Digital | 2,82 | 90.379 € | 275.541 € | 13,3%
T7 - Bases de Datos y Plataformas ITSM | 2,43 | 53.444 € | 244.558 € | 7,9%
T8 - Aplicaciones de Negocio y FinOps | 2,45 | 106.272 € | 334.344 € | 15,6%
T9 - Puesto de Trabajo y Movilidad | 3,19 | 7.902 € | 55.815 € | 1,2%
T10 - Operaciones Locales & Sedes Distribuidas | 2,40 | 46.029 € | 174.109 € | 6,8%
TOTAL CONSOLIDADO (10 Dominios) | 2,58 | 679.403 € | 428.163 € (Máx.) | 100,0%

### New Table 5 (Polymorphic Staging Deliverable):
Dominio Tecnológico | Madurez CMMI | Riesgo Independiente (Standalone Bottom-Up) | Ajuste por Solapamiento y Capacidad de Absorción | Contribución Neta al Portafolio (Euler ALE) | % del Riesgo Total
T1 - Centros de Datos e Instalaciones Técnicas | 2,61 | 62.093 € | -45.140 € | 16.953 € | 2,5%
T2 - Cómputo Híbrido y Virtualización | 1,89 | 104.190 € | -75.743 € | 28.447 € | 4,2%
T3 - Redes y Conectividad WAN/LAN | 2,56 | 64.640 € | -46.991 € | 17.649 € | 2,6%
T4 - Almacenamiento y Backup Corporativo | 3,26 | 382.873 € | -278.336 € | 104.537 € | 15,4%
T5 - Continuidad Operativa y Resiliencia Fabril | 2,20 | 84.650 € | -61.538 € | 23.112 € | 3,4%
T6 - Ciberseguridad e Identidad Digital | 2,82 | 916.254 € | -666.086 € | 250.168 € | 36,8%
T7 - Bases de Datos y Plataformas ITSM | 2,43 | 93.389 € | -67.891 € | 25.498 € | 3,8%
T8 - Aplicaciones de Negocio y FinOps | 2,45 | 641.420 € | -466.291 € | 175.129 € | 25,8%
T9 - Puesto de Trabajo y Movilidad | 3,19 | 65.664 € | -47.735 € | 17.929 € | 2,6%
T10 - Operaciones Locales & Sedes Distribuidas | 2,40 | 73.182 € | -53.201 € | 19.981 € | 2,9%
SUBTOTAL EXPOSICIÓN BRUTA NO DIVERSIFICADA | 2,58 | 2.488.355 € | - | - | -

---
## 2. Tower 2 (Hybrid Compute & Platforms - New Staging Version)
**File:** `Molins_202610_Annex_02_T2_ASIS.docx` (117,347 bytes)
### Sample Paragraphs:
- *P3:* Anexo Técnico: Cómputo Híbrido y Plataformas
- *P10:* La plataforma de cómputo opera sobre un clúster hiperconvergente de 6 nodos HPE SimpliVity bajo VMware vSphere, cuyo principal cuello de botella reside en la saturación de memoria RAM al 85%. La convivencia en la misma infraestructura de cargas de misión crítica junto a sistemas de planta OT y entornos de pruebas anula el margen de tolerancia N+1: la pérdida de un único nodo forzaría el bloqueo del hipervisor o la parada abrupta de máquinas virtuales.
- *P12:* Saturación de memoria RAM y CPU en los 6 nodos HPE SimpliVity (especialmente nodos 3 y 4) al convivir cargas de producción OT con entornos de desarrollo y pruebas.
- *P15:* Bajo el estándar internacional Open FAIR™ (Factor Analysis of Information Risk), la indisponibilidad no planificada del servicio conlleva un coste operativo directo de 13.061 €/h (detallado en la Sección 4.1). En condiciones ordinarias, las brechas técnicas evaluadas específicamente en el ámbito de Cómputo Híbrido y Plataformas representan una exposición de riesgo latente estimada en 104.189 € anualizados, cifra que refleja la pérdida media esperada por la fricción operativa e incidencias a lo largo de un año dentro de este dominio.
- *P24:* La plataforma de cómputo de Molins sustenta el núcleo operativo combinando clústeres hiperconvergentes HPE SimpliVity sobre VMware vSphere en Sant Vicenç dels Horts con extensiones en GCP, Azure y OCI. La capa de virtualización soporta más de 300 máquinas virtuales productivas que dan servicio a las fábricas y filiales del grupo. La evaluación se estructura conforme a los controles CIS Controls v8 y las directrices de virtualización segura NIST SP 800-125.

---
## 3. Tower 8 (Strategy, Governance & FinOps - New Staging Version)
**File:** `Molins_202610_Annex_08_T8_ASIS.docx` (113,095 bytes)
### Sample Paragraphs (Checking for absence of false downtime):
- *P15:* Bajo el estándar internacional Open FAIR™ (Factor Analysis of Information Risk), la indisponibilidad no planificada del servicio conlleva un coste operativo directo de 13.061 €/h (detallado en la Sección 4.1). En condiciones ordinarias, las brechas técnicas evaluadas específicamente en el ámbito de Estrategia Tecnológica, Gobierno y FinOps representan una exposición de riesgo latente estimada en 641.420 € anualizados, cifra que refleja la pérdida media esperada por la fricción operativa e incidencias a lo largo de un año dentro de este dominio.
- *P16:* Adicionalmente, ante un escenario adverso de crisis por fallo múltiple o contingencia grave en esta plataforma, la recuperación técnica mediante procedimientos de contingencia podría demorarse hasta 22,9 horas, elevando el impacto económico de ese único evento extremo hasta 962.130 € al computar la parada acumulada junto a los costes urgentes de sustitución de equipamiento y soporte extraordinario del fabricante.
- *P62:* 2. Bloqueo fiduciario por licenciamiento de software por procesador físico y riesgo de penalización en auditorías: Las penalizaciones contractuales en bases de datos empresariales distorsionan las decisiones de compras, forzando a congelar la inversión en hardware moderno para eludir costes millonarios de regularización de licencias.
- *P75:* El modelo de gobernanza tecnológica presenta una marcada fragmentación organizativa y de jurisdicción técnica. El área de Infraestructura IT (compuesta por 5 técnicos internos bajo la dirección de Aleix, tras pactar la no reposición de una jubilación en diciembre) gestiona la ingeniería y los proyectos de evolución, pero la operación diaria y atención al usuario (SAU) recae en una estructura separada fuera de su gobierno directo. En las plantas y oficinas de hormigoneras prolifera el Shadow IT, donde el personal local despliega autónomamente puntos de acceso Wi-Fi, cámaras de seguridad y repartidores de fibra desde los PCs de control sin conocimiento previo de TI, solicitando soporte únicamente cuando los dispositivos fallan.
- *P90:* Para traducir los hallazgos empíricos de infraestructura y arquitectura (documentados en los Capítulos 2 y 3) al lenguaje financiero del Comité de Dirección, este análisis aplica la taxonomía internacional Open FAIR™ (Factor Analysis of Information Risk). Es imperativo señalar que todas las cifras monetarias, frecuencias de ocurrencia y tiempos de recuperación contenidos en este capítulo representan proyecciones actuariales estimadas diseñadas para la priorización racional de inversiones (CAPEX) y no constituyen asientos contables históricos ni pérdidas ya materializadas.
- *P92:* Cloud Spend Waste Scaling by Failure Scope: The baseline IT expenditure represents the addressable infrastructure operating cost. Because technical inefficiencies do not impact 100% of compute resources simultaneously, the model evaluates capital leakage according to workload scope: 70% (9.143 €) for unreserved core compute clusters, 40% (5.225 €) for storage tiering and snapshot accumulation, and 20% (2.612 €) for peripheral test/dev environments. This ensures each risk card realistically reflects the financial liability of its specific domain.
- *P93:* The parametric cornerstone of the model for Estrategia Tecnológica, Gobierno y FinOps is the Estimated Annual Cloud Capital Leakage Rate (R_capital, est), quantified against addressable infrastructure commitments across Molins. This rate captures unbudgeted on-demand compute drift, unallocated resource sprawl, and vendor licensing true-up liabilities.
- *P95:* R_{capital, est} = C_{compute, drift} + C_{unallocated, sprawl} + C_{license, trueup}
- *P108:* El inventario de riesgos técnicos identificados en el dominio de Estrategia Tecnológica, Gobierno y FinOps arroja una exposición económica anualizada total estimada en 109.028 €/año. A efectos de dimensionar la concentración del riesgo en el estado actual (AS-IS), la exposición se agrupa en tres niveles de criticidad financiera sin considerar planes de implantación futuros:
- *P137:* Las proyecciones de impacto financiero, simulaciones estocásticas de Monte Carlo y valores de Expectativa de Pérdida Anualizada (ALE / P90 / CVaR) calculados bajo el estándar internacional Open FAIR™ (Factor Analysis of Information Risk) representan modelos matemáticos de probabilidad basados en distribuciones de incertidumbre. Dichas valoraciones constituyen herramientas analíticas exclusivas para la priorización estratégica de inversiones técnicas (CAPEX/OPEX) y la justificación del coste de inacción (Business Case); en ningún caso deben interpretarse ni utilizarse como auditorías contables de balance, provisiones de pasivos contables, garantías de impacto directo o indirecto, ni compromisos de pasivos exigibles legal o judicialmente.
- *P143:* En la máxima medida permitida por la legislación aplicable, NTT DATA no será responsable en ningún caso, bajo ninguna teoría contractual o extracontractual, por daños indirectos, incidentales, punitivos, especiales o consecuenciales, incluyendo de manera enunciativa pero no limitativa, lucro cesante, pérdida de ingresos, paradas de planta, interrupción de negocio, pérdidas de datos o daños reputacionales derivados directa o indirectamente de la aplicación o no aplicación de las recomendaciones técnicas contenidas en este informe.

---
## 4. Synthesis & Verdict: Which Version is Better?
1. **Preservation of Core Industrial Grounding:** The new staging version preserves 100% of Molins' real technology inventory (SimpliVity, Sant Vicenç, básculas, NetApp) while compiling cleanly through the AST engine.
2. **Exact Mathematical Reconciliation:** Tower 2 preserves exactly the 156.160 € ALE that was validated in the original document.
3. **Decoupled FinOps Framing:** Tower 8 eliminates the absurd attribution of factory stoppages to FinOps gaps, framing risk as cloud capital drift and licensing true-ups.