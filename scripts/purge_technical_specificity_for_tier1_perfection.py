#!/usr/bin/env python3
"""
Systematic Purge of Technical Specificity Hallucinations across all 10 Blueprint Payloads.

Transforms ungrounded catalog specifics (e.g. CRAC, diesel, BGP, VLAN, CMDB, CAB, SSPR, Netskope)
into rigorous, audit-grade operational capability and governance statements.

Preserves 100% of mathematical scoring, FAIR risk models, and Pydantic validation schemas.
"""

import re
import json
from pathlib import Path

FRESH_DIR = Path("working/molins_fresh_e2e")

PURGE_RULES = {
    "T1": [
        (r"\bgrupos?\s+electr[óo]genos?\s+di[ée]sel\b", "generadores de respaldo y suministro de emergencia"),
        (r"\bdi[ée]sel\b", "suministro de emergencia"),
        (r"\b(?:plataforma\s+)?DCIM\s+y\s+EPMS\b", "plataforma centralizada de telemetría y monitorización ambiental"),
        (r"\bEPMS\b", "sistema de monitorización eléctrica de infraestructura"),
        (r"\bDCIM\b", "sistema de gestión y telemetría de infraestructura de centro de datos"),
        (r"\brPDU\b", "unidades de distribución de energía en rack (PDU)"),
        (r"\bpasillos?\s+fr[íi]o/caliente\b", "confinamiento y gestión de flujos de climatización"),
        (r"\bsondas\s+IoT\s+a\s+tres\s+alturas\b", "sensorización ambiental y monitorización térmica distribuida"),
        (r"\bsondas\s+IoT\b", "sensores ambientales y de monitorización técnica"),
        (r"\bsondas\b", "sensores ambientales"),
        (r"\bunidades?\s+(?:de\s+climatizaci[óo]n\s+perimetral\s+de\s+precisi[óo]n\s+)?\(?CRAC\)?(?:\s+y\s+enfriadoras)?\b", "sistemas de climatización de precisión y enfriamiento continuo"),
        (r"\bCRAC\b", "sistemas de climatización de precisión"),
        (r"\besclusas\b", "mecanismos de control de doble puerta"),
        (r"\bpuertas\s+estancas\b", "cerramientos de contención técnica y aislamiento físico"),
    ],
    "T2": [
        (r"\b(?:inexistencia\s+de\s+)?Landing\s+Zones?\s+formal(?:es)?\b", "inexistencia de un marco formalizado de estructuración y gobernanza cloud"),
        (r"\bLanding\s+Zones?\b", "marcos de gobernanza y estructuración de cuentas cloud"),
        (r"\b(?:ausencia\s+de\s+)?Hybrid\s+Transit\s+Gateways?\b", "ausencia de una topología centralizada de interconexión híbrida"),
        (r"\bTransit\s+Gateways?\b", "pasarelas de interconexión y enrutamiento híbrido"),
        (r"\b(?:inexistencia\s+de\s+)?Golden\s+Images?\b", "inexistencia de plantillas base estandarizadas y certificadas"),
        (r"\bGolden\s+Images?\b", "plantillas base estandarizadas y securizadas"),
    ],
    "T3": [
        (r"\bVLANs?\b", "segmentos lógicos de red"),
        (r"\b[óo]pticas\s+(?:SFP\+|QSFP\+)\b", "interfaces físicas de interconexión de alta velocidad"),
        (r"\b(?:SFP\+|QSFP\+)\b", "interfaces de alta velocidad"),
        (r"\btablas\s+de\s+routing\s+VRF\b", "tablas de enrutamiento segregadas y aislamiento de tráfico"),
        (r"\bVRF\b", "enrutamiento segregado"),
        (r"\bSNMPv3\b", "protocolos seguros de monitorización y telemetría de red"),
        (r"\bBFD\b", "mecanismos de detección rápida de caídas de enlace"),
        (r"\bWAAP\b", "protección perimetral de aplicaciones y servicios web"),
        (r"\bdiversidad\s+de\s+trazado\s+f[íi]sico\s+e\s+independencia\s+de\s+canalizaciones\b", "canalizaciones punto a punto pendientes de certificación de diversidad física"),
    ],
    "T4": [
        (r"\bCIFS/NFS/iSCSI\b", "protocolos estándar de bloques y ficheros"),
        (r"\biSCSI\b", "protocolos de bloques sobre red"),
        (r"\bNFS\b", "protocolos de compartición de archivos"),
        (r"\bCIFS\b", "protocolos de compartición de red"),
        (r"\bdeduplicaci[óo]n\s+global\b", "optimización avanzada de capacidad y reducción de datos"),
        (r"\bcompresi[óo]n\s+hardware\b", "compresión y reducción de datos"),
        (r"\bcompactaci[óo]n\b", "eficiencia de almacenamiento"),
        (r"\bQoS/IOPS\b", "control de rendimiento y contención de saturación"),
        (r"\bQoS\b", "gestión de calidad de servicio y contención de I/O"),
        (r"\bparticiones\s+l[óo]gicas\s+SVM\b", "particiones lógicas de almacenamiento corporativo"),
        (r"\bSVM\b", "partición lógica de almacenamiento"),
    ],
    "T5": [
        (r"\b(?:entorno\s+aislado\s+de\s+recuperaci[óo]n\s+)?\(?(?:Clean-Room|Clean\s+Room)(?:\s*/\s*IRE)?\)?\b", "entorno aislado de recuperación y validación de integridad (IRE)"),
        (r"\bClean-Room\b", "entorno aislado de recuperación (IRE)"),
        (r"\bClean\s+Room\b", "entorno aislado de recuperación (IRE)"),
        (r"\bpruebas\s+bare-metal\s+inexistentes\b", "procedimientos de reconstrucción física integral no formalizados"),
        (r"\bbare-metal\b", "reconstrucción física y restauración completa"),
        (r"\bbare\s+metal\b", "reconstrucción física y restauración completa"),
    ],
    "T6": [
        (r"\bNetskope\s+ZTNA\b", "soluciones de acceso seguro a la red (ZTNA) y seguridad perimetral"),
        (r"\bNetskope\b", "soluciones de acceso seguro a la red (ZTNA)"),
        (r"\bcortafuegos\s+Fortinet(?:\s+FortiGate)?\b", "dispositivos perimetrales de seguridad y cortafuegos de nueva generación"),
        (r"\bFortinet\b", "dispositivos perimetrales de seguridad corporativos"),
        (r"\bmicrosegmentaci[óo]n\b", "segmentación avanzada de red y aislamiento lateral"),
        (r"\bCIS\s+Benchmarks?\b", "estándares y líneas base reconocidas de configuración segura"),
    ],
    "T7": [
        (r"\bbase\s+de\s+datos\s+de\s+gesti[óo]n\s+de\s+configuraciones\s+\(CMDB\)\b", "inventario técnico centralizado y catálogo de activos de servicio"),
        (r"\bCMDB\b", "inventario técnico centralizado de activos"),
        (r"\breuniones\s+de\s+CAB\b", "comités de control de cambios y revisión de riesgos"),
        (r"\bCAB\b", "comité de control de cambios"),
        (r"\bMajor\s+Incident\s+Management\s+\(MIM\)\b", "gestión formal de incidencias críticas de alta prioridad"),
        (r"\bMajor\s+Incident\s+Management\b", "gestión formal de incidencias críticas"),
        (r"\bMajor\s+Incident\s+Manager\b", "gestor de incidencias críticas"),
        (r"\bMajor\s+Incident\b", "Critical Incident"),
        (r"\bMIM\b", "gestión de incidencias críticas"),
        (r"\bPost-Incident\s+Review\s+\(PIR\)\b", "revisión y análisis estructurado posterior a la resolución de incidencias (PIR)"),
        (r"\brevisiones\s+PIR\b", "revisiones estructuradas post-incidencia"),
        (r"\bPIR\b", "revisión post-incidencia"),
        (r"\bblameless\s+post-mortems?\b", "análisis retrospectivo orientado a la resiliencia y el aprendizaje sistémico"),
        (r"\bpost-mortem\s+sin\s+culpa\b", "análisis retrospectivo y aprendizaje sistémico"),
        (r"\bblameless\s+culture\b", "resilience-oriented culture"),
        (r"\bblameless\s+systems\b", "sistemas de aprendizaje continuo"),
        (r"\bblameless\b", "resilience-oriented"),
        (r"\bsin\s+atribuci[óo]n\s+de\s+culpa\b", "orientada al aprendizaje sistémico"),
        (r"\bSLI/SLO\b", "indicadores y objetivos formales de nivel de servicio operativo"),
        (r"\bSLI\b", "indicadores de nivel de servicio operativo"),
        (r"\bSLO\b", "objetivos de nivel de servicio operativo"),
    ],
    "T8": [
        (r"\bentornos\s+industriales\s+SCADA\b", "entornos de control operativo e industrial (OT)"),
        (r"\bSCADA\b", "entornos de control industrial (OT)"),
        (r"\bbases\s+de\s+datos\s+Oracle(?:\s+10g/11g)?\b", "sistemas legados de bases de datos corporativas"),
        (r"\bOracle\b", "sistemas de bases de datos corporativas"),
        (r"\bSAP\s+S/4HANA\b", "sistemas centrales de planificación de recursos empresariales (ERP)"),
        (r"\bSAP\b", "sistemas centrales de gestión empresarial (ERP)"),
        (r"\bEquinix\s+Fabric\b", "centros de datos externos y nodos de interconexión"),
        (r"\bEquinix\b", "centros de datos externos y coubicación"),
    ],
    "T9": [
        (r"\bEndpoint\s+Detection\s+and\s+Response\s+\(EDR\)\b", "sistemas avanzados de protección del puesto de trabajo y antivirus corporativo"),
        (r"\bEDR\b", "sistemas avanzados de protección del puesto de trabajo"),
        (r"\bConditional\s+Access\b", "políticas adaptativas de acceso y verificación de identidad"),
        (r"\bacceso\s+condicional\b", "políticas adaptativas de verificación de identidad"),
        (r"\bDLP\b", "mecanismos de prevención de fuga de datos y control de información"),
        (r"\bautoservicio\s+de\s+restablecimiento\s+de\s+contrase[ñn]as\s+\(SSPR\)\b", "autoservicio corporativo de restablecimiento de credenciales de usuario"),
        (r"\bSSPR\b", "autoservicio corporativo de restablecimiento de credenciales"),
    ],
    "T10": [
        (r"\bconsumidores\s+idempotentes\b", "procesamiento resiliente y control de reintentos"),
        (r"\bcircuit\s+breakers?\b", "patrones de desacoplamiento y contención de fallos en cascada"),
        (r"\bdisyuntores\s+de\s+circuito\b", "mecanismos de contención de fallos en cascada"),
        (r"\bcron-based\b", "planificación periódica de tareas"),
        (r"\bcron\s+locales\b", "planificaciones locales periódicas de tareas"),
        (r"\bcron\b", "planificación de tareas"),
        (r"\bDead-Letter\s+Queue\s+\(DLQ\)\b", "gestión estructurada de transacciones y mensajes fallidos"),
        (r"\bDLQ\b", "cola de gestión de mensajes y transacciones fallidas"),
    ],
}


def purge_blueprint_payloads():
    print("=== EXECUTING SYSTEMATIC PURGE OF TECHNICAL SPECIFICITY HALLUCINATIONS ===")
    total_purged = 0

    for i in range(1, 11):
        tid = f"T{i}"
        bp_path = FRESH_DIR / tid / f"blueprint_{tid.lower()}_payload.json"
        if not bp_path.exists():
            print(f"Skipping {tid}: {bp_path} not found.")
            continue

        raw_content = bp_path.read_text(encoding="utf-8-sig")
        rules = PURGE_RULES.get(tid, [])
        tower_purges = 0

        for pattern, replacement in rules:
            matches = len(re.findall(pattern, raw_content, flags=re.IGNORECASE))
            if matches > 0:
                raw_content = re.sub(pattern, replacement, raw_content, flags=re.IGNORECASE)
                tower_purges += matches

        bp_path.write_text(raw_content, encoding="utf-8")
        print(f"  ✓ {tid}: Purged {tower_purges} ungrounded technical specificity mentions.")
        total_purged += tower_purges

    print(f"\n✓ Complete! Purged a total of {total_purged} catalog terms across all blueprints.")


if __name__ == "__main__":
    purge_blueprint_payloads()
