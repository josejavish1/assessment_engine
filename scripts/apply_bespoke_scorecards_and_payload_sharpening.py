#!/usr/bin/env python3
"""Inject 10 completely unique, bespoke scorecard commentaries and sharpen T4, T7, T8, T9 payloads."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
loc_path = REPO_ROOT / "engine_config/locales.json"

with open(loc_path, "r", encoding="utf-8") as f:
    locales = json.load(f)

# ----------------------------------------------------------------------
# 1. 10 COMPLETELY UNIQUE SCORECARD COMMENTARIES (ZERO MAD-LIBS CLONES)
# ----------------------------------------------------------------------
ch3_scorecard_by_tower_es = {
    "T1": "Con una puntuación técnica de {score_val} sobre 5,0 ({maturity_tier_label}), las instalaciones de {client_name} se sitúan en el límite inferior del Nivel 3. La solvencia de los sistemas de extinción de incendios ({strongest_pillar_score}/5,0) contrasta con la fragilidad térmica en salas de proceso ({weakest_pillar_score}/5,0), donde la falta de telemetría de potencia por rack y la exposición a partículas fabriles amenazan la continuidad de los servidores de planta.",
    "T2": "Evaluada en {score_val} sobre 5,0 ({maturity_tier_label}), la plataforma de cómputo opera al límite de su capacidad física en {client_name}. La estabilidad demostrada por los hipervisores en la operativa cotidiana ({strongest_pillar_score}/5,0) contrasta con el agotamiento crítico de memoria RAM y la carencia de entornos de contenedores ({weakest_pillar_score}/5,0), eliminando el margen de seguridad para absorber caídas sin degradar el servicio.",
    "T3": "La infraestructura de red alcanza una calificación de {score_val} sobre 5,0 ({maturity_tier_label}). La robustez del switching en sedes centrales ({strongest_pillar_score}/5,0) contrasta con los puntos únicos de fallo en la red extendida ({weakest_pillar_score}/5,0), donde la dependencia de enlaces WAN monoproveedor hacia canteras y fábricas remotas expone a {client_name} a cortes logísticos inmediatos.",
    "T4": "Con una valoración técnica de {score_val} sobre 5,0 ({maturity_tier_label}), el almacenamiento corporativo cuenta con una base sólida de instantáneas y replicación ({strongest_pillar_score}/5,0). El reto crítico radica en la arquitectura de persistencia ({weakest_pillar_score}/5,0), donde la falta de almacenamiento inmutable contra ransomware y el dimensionamiento restrictivo de disco obligan al equipo de {client_name} a una continua contención manual de cuotas.",
    "T5": "Calificada en {score_val} sobre 5,0 ({maturity_tier_label}), la resiliencia operativa presenta un desfase crítico frente a los ritmos de producción de {client_name}. La fiabilidad del backup local ({strongest_pillar_score}/5,0) contrasta con la vulnerabilidad de la alta disponibilidad ({weakest_pillar_score}/5,0), donde la proximidad física de 500 metros entre centros de datos compartiendo suministro eléctrico convierte cualquier contingencia grave en una amenaza de parada fabril.",
    "T6": "Evaluada en {score_val} sobre 5,0 ({maturity_tier_label}), la postura de ciberseguridad se sitúa en un nivel de exposición severa en {client_name}. Si bien la federación de identidades muestra avances ({strongest_pillar_score}/5,0), el uso generalizado de credenciales root y admin compartidas sin bóveda ({weakest_pillar_score}/5,0) anula la trazabilidad de cambios y genera una exposición sancionadora directa ante la Directiva NIS2.",
    "T7": "Con una puntuación técnica de {score_val} sobre 5,0 ({maturity_tier_label}), la gestión de servicios opera bajo una tensión reactiva permanente en {client_name}. La visibilidad alcanzada con la monitorización de sistemas ({strongest_pillar_score}/5,0) contrasta con la carencia de procesos formales de gestión de problemas ({weakest_pillar_score}/5,0), consumiendo más del 40% de la capacidad del equipo nuclear de cinco ingenieros en apagar fuegos recurrentes.",
    "T8": "La gobernanza tecnológica alcanza una puntuación de {score_val} sobre 5,0 ({maturity_tier_label}). El control riguroso de compras en {client_name} ({strongest_pillar_score}/5,0) convive con una notable opacidad fiduciaria ({weakest_pillar_score}/5,0), donde la dispersión del gasto en tres nubes públicas y las restricciones de licenciamiento de software por procesador condicionan las decisiones de arquitectura de toda la compañía.",
    "T9": "Con una valoración consolidada de {score_val} sobre 5,0 ({maturity_tier_label}), el puesto de trabajo digital presenta una disciplina ejemplar en la renovación de portátiles ({strongest_pillar_score}/5,0). La principal área de fricción recae en el soporte y operaciones ({weakest_pillar_score}/5,0), donde la coexistencia de equipos no estandarizados en fábricas y terminales compartidos en básculas ralentiza los turnos de trabajo en {client_name}.",
    "T10": "Evaluados en {score_val} sobre 5,0 ({maturity_tier_label}), los sistemas de planta y expedición representan el eslabón más sensible para la facturación de {client_name}. La estabilidad de las integraciones transaccionales ({strongest_pillar_score}/5,0) contrasta con la fragilidad del equipamiento de borde y básculas ({weakest_pillar_score}/5,0), donde la sensibilidad a caídas de telecomunicaciones traslada cualquier incidencia técnica a un bloqueo físico de camiones en planta."
}

ch3_scorecard_by_tower_en = {
    "T1": "Scoring a technical maturity of {score_val} out of 5.0 ({maturity_tier_label}), datacenter facilities across {client_name} sit at the lower boundary of Level 3. Solid fire suppression defenses ({strongest_pillar_score}/5.0) contrast with critical thermal fragility in process rooms ({weakest_pillar_score}/5.0), where absent per-rack power telemetry and airborne industrial dust threaten edge plant server continuity.",
    "T2": "Evaluated at {score_val} out of 5.0 ({maturity_tier_label}), compute infrastructure operates at its physical limits across {client_name}. Baseline hypervisor stability ({strongest_pillar_score}/5.0) contrasts with acute memory exhaustion and absent container platforms ({weakest_pillar_score}/5.0), eliminating the resilience buffer required to absorb host failure without disrupting core business transactions.",
    "T3": "Network infrastructure achieves a technical score of {score_val} out of 5.0 ({maturity_tier_label}). Campus switching resilience across headquarters ({strongest_pillar_score}/5.0) contrasts with critical single points of failure across wide-area links ({weakest_pillar_score}/5.0), where single-carrier WAN lines to remote quarries and plants expose {client_name} to logistics isolation during fiber cuts.",
    "T4": "Rated at {score_val} out of 5.0 ({maturity_tier_label}), corporate storage demonstrates dependable snapshot replication ({strongest_pillar_score}/5.0). The critical challenge lies within storage tiering architecture ({weakest_pillar_score}/5.0), where the absence of immutable ransomware vaults and restrictive disk provisioning force technical staff at {client_name} into continuous manual quota containment.",
    "T5": "Scoring {score_val} out of 5.0 ({maturity_tier_label}), operational resilience exhibits an acute gap against manufacturing tolerances across {client_name}. Local operational backup reliability ({strongest_pillar_score}/5.0) contrasts with high availability fragility ({weakest_pillar_score}/5.0), where a 500-meter proximity between datacenters sharing electrical feeds turns localized power cuts into total plant halts.",
    "T6": "Evaluated at {score_val} out of 5.0 ({maturity_tier_label}), cybersecurity operates under severe operational exposure across {client_name}. While identity federation shows progress ({strongest_pillar_score}/5.0), unvaulted shared root/admin credentials ({weakest_pillar_score}/5.0) destroy change auditability and generate direct executive compliance liabilities under the NIS2 Directive.",
    "T7": "Scoring a technical maturity of {score_val} out of 5.0 ({maturity_tier_label}), IT service management operates reactively across {client_name}. System monitoring visibility ({strongest_pillar_score}/5.0) contrasts with the absence of formal problem management ({weakest_pillar_score}/5.0), consuming over 40% of the core five-engineer team's capacity in recurring firefighting.",
    "T8": "Technology governance achieves a score of {score_val} out of 5.0 ({maturity_tier_label}). Disciplined procurement control across {client_name} ({strongest_pillar_score}/5.0) coexists with fiduciary opacity ({weakest_pillar_score}/5.0), where uncoordinated multi-cloud spend across three hyperscalers and core-based software licensing constraints artificially cap compute sizing.",
    "T9": "With a consolidated maturity of {score_val} out of 5.0 ({maturity_tier_label}), the digital workplace exhibits structured laptop fleet renewal ({strongest_pillar_score}/5.0). The primary friction lies within workplace operations and support ({weakest_pillar_score}/5.0), where unstandardized plant PCs and shared weighbridge kiosks introduce shift-change delays across {client_name}.",
    "T10": "Evaluated at {score_val} out of 5.0 ({maturity_tier_label}), plant edge dispatch systems represent the single most sensitive operational bottleneck across {client_name}. Stable transactional interfaces ({strongest_pillar_score}/5.0) contrast with weighbridge edge equipment fragility ({weakest_pillar_score}/5.0), where sensitivity to WAN disconnects directly triggers physical truck gridlock at factory gates."
}

locales["es"]["ch3_scorecard_by_tower"] = ch3_scorecard_by_tower_es
locales["en"]["ch3_scorecard_by_tower"] = ch3_scorecard_by_tower_en

base_keys = set(locales["en"].keys())
for lang in ["pt", "fr", "de", "ja"]:
    if lang in locales:
        for k in base_keys:
            if k not in locales[lang] or isinstance(locales[lang][k], dict):
                locales[lang][k] = locales["en"][k]

with open(loc_path, "w", encoding="utf-8") as f:
    json.dump(locales, f, indent=2, ensure_ascii=False)

print("Injected 10 bespoke, non-cloned scorecard commentaries into locales.json!")

# ----------------------------------------------------------------------
# 2. SHARPEN MOLINS PAYLOADS FOR T4, T7, T8, T9
# ----------------------------------------------------------------------

# T4 (Storage & Backup)
with open(REPO_ROOT / "working/molins/T4/blueprint_t4_payload.json", "r", encoding="utf-8") as f:
    t4 = json.load(f)
t4["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Ausencia de repositorios inmutables con bloqueo de objetos (WORM) y aislamiento air-gap frente a ransomware: La protección de datos descansa en replicación síncrona ordinaria entre cabinas NetApp, permitiendo que una infección por cifrado malicioso corrompa instantáneamente las copias secundarias de las bases de datos transaccionales.",
    "Aprovisionamiento deliberadamente restrictivo de capacidad local (<1GB libre por máquina virtual) para mitigar el gasto CapEx: La política de limitar márgenes de disco para forzar alertas tempranas traslada una carga continua de contención manual al equipo técnico para evitar la congelación de servidores de negocio.",
    "Silos técnicos de almacenamiento y fragmentación en la gestión de copias de seguridad: Coexistencia de cabinas NetApp corporativas en Sant Vicenç dels Horts con soluciones aisladas de backup en plantas remotas y filiales, dificultando la correlación de telemetría de I/O y la verificación periódica de restaurabilidad completa."
]
with open(REPO_ROOT / "working/molins/T4/blueprint_t4_payload.json", "w", encoding="utf-8") as f:
    json.dump(t4, f, indent=2, ensure_ascii=False)

# T7 (ITSM & Operations)
with open(REPO_ROOT / "working/molins/T7/blueprint_t7_payload.json", "r", encoding="utf-8") as f:
    t7 = json.load(f)
t7["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Cuello de botella operativo en el equipo nuclear de cinco ingenieros de infraestructura: La concentración de conocimiento tácito y la ausencia de una CMDB federada viva obligan a los especialistas sénior a destinar más del 40% de su jornada a tareas reactivas de soporte e intervenciones manuales de primer nivel.",
    "Carencia de acuerdos de nivel operacional (OLAs) y gestión estructurada de problemas: Las alertas recurrentes de sistemas se resuelven como incidencias aisladas sin análisis de causa raíz, perpetuando fallos crónicos que impactan en la continuidad operativa de las fábricas.",
    "Atención fragmentada y canales informales de soporte en plantas industriales: La dispersión territorial favorece que las peticiones técnicas se gestionen mediante llamadas directas o correos sin ticket, desalineando las ventanas de mantenimiento de TI respecto a los calendarios de producción de planta."
]
with open(REPO_ROOT / "working/molins/T7/blueprint_t7_payload.json", "w", encoding="utf-8") as f:
    json.dump(t7, f, indent=2, ensure_ascii=False)

# T8 (FinOps & Governance)
with open(REPO_ROOT / "working/molins/T8/blueprint_t8_payload.json", "r", encoding="utf-8") as f:
    t8 = json.load(f)
t8["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Dispersión del gasto tecnológico en tres nubes públicas (GCP, Azure, OCI) sin etiquetado unificado ni telemetría FinOps: Ausencia de modelos de showback o chargeback por planta o unidad de negocio que permitan visibilizar el coste unitario de infraestructura y optimizar recursos ociosos.",
    "Bloqueo fiduciario por licenciamiento de software por procesador físico: Las penalizaciones contractuales en bases de datos empresariales condicionan la arquitectura técnica, forzando a congelar la capacidad de memoria y CPU en clústeres de cómputo para evitar costes imprevistos.",
    "Aislamiento operativo entre ingeniería interna, compras corporativas y proveedores externalizados (NOS, servicios gestionados): Falta de seguimiento centralizado de SLAs contractuales y compras puntuales descentralizadas que duplican costes de mantenimiento entre filiales."
]
with open(REPO_ROOT / "working/molins/T8/blueprint_t8_payload.json", "w", encoding="utf-8") as f:
    json.dump(t8, f, indent=2, ensure_ascii=False)

# T9 (Digital Workplace)
with open(REPO_ROOT / "working/molins/T9/blueprint_t9_payload.json", "r", encoding="utf-8") as f:
    t9 = json.load(f)
t9["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Elevada carga de soporte manual en el ciclo de vida del puesto de trabajo: La preparación artesanal de portátiles sin flujos automatizados de despliegue zero-touch (Intune/Autopilot) consume horas de técnicos y genera heterogeneidad en las configuraciones de usuario.",
    "Brecha tecnológica y fricción en terminales compartidos y quioscos de planta: Los puestos de expedición en básculas y terminales de fábrica operan con hardware dispar y sesiones genéricas, ralentizando los relevos de turno y debilitando la autenticación corporativa.",
    "Desalineación en la distribución de parches y gobierno del puesto entre sedes y filiales integradas: Coexistencia de políticas dispares de actualización de sistema operativo y aplicaciones entre oficinas centrales y filiales adquiridas, elevando la superficie de exposición ante ataques de phishing."
]
with open(REPO_ROOT / "working/molins/T9/blueprint_t9_payload.json", "w", encoding="utf-8") as f:
    json.dump(t9, f, indent=2, ensure_ascii=False)

print("Sharpened Molins payloads for T4, T7, T8, T9 with hard facts and board consequences!")
