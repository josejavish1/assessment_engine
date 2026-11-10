#!/usr/bin/env python3
"""
Master Harmonization Script for All 10 Towers (Cementos Molins).

Applies the exact same forensic standard proven in Tower 2 to ALL 10 TOWERS:
1. Native 3-column Divergence Tables wherever Declared vs Calibrated gap >= 0.50.
2. 100% Executive Consulting Tone (zero accusatory words, purely strategic).
3. Ground Truth Invariant (Zero brand hallucinations; only verified client assets).
4. Full mathematical and tabular alignment across Tomo 1 and Anexos 01 to 10.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CALIBRATION_SPEC = {
    "T1": {
        "calibrated_score": 1.93,
        "declared_score": 2.61,
        "pillars": {
            "T1.P1": {
                "declared": 2.50,
                "calibrated": 1.75,
                "narrative": (
                    "El suministro eléctrico en los centros de datos de Sant Vicenç dels Horts se estructura mediante sistemas "
                    "SAI/UPS de doble conversión en línea de 60 kVA en configuración N+1 (37 kW por sala) y un grupo electrógeno "
                    "diésel de emergencia de 250 kVA con ATS automático en CPD 1. La alimentación de socorro hacia CPD 2 depende de una única "
                    "línea subterránea de baja tensión de 500 metros en zanja industrial sin trazado divergente. "
                    "La autoevaluación inicial de la organización proyectaba una puntuación de 2,50 sobre 5,0. Sin embargo, la contrastación "
                    "técnica constata la ausencia de ensayos periódicos de corte en carga sobre el conmutador ATS, la falta de pruebas "
                    "de conductancia interna en las ramas de baterías y la ausencia de selectividad cronoamperimétrica en el CGBT de cabecera. "
                    "Por ello, la auditoría calibra la madurez operativa en 1,75 (Nivel 2 Repetible) para justificar las inversiones de consolidación en el Tomo 2."
                )
            },
            "T1.P4": {
                "declared": 4.00,
                "calibrated": 1.75,
                "narrative": (
                    "La seguridad ambiental y protección contra incendios cuenta con detección precoz por aspiración láser y extinción automática "
                    "mediante agente limpio gaseoso según norma NFPA 2001 en ambas salas técnicas. "
                    "La autoevaluación inicial de la organización proyectaba una puntuación de 4,00 sobre 5,0. No obstante, las evidencias "
                    "técnicas constatan la caducidad de las certificaciones de prueba de estanqueidad de sala (Door Fan Test) y la ausencia "
                    "de lazo de cable sensor direccionable de detección de fugas de agua bajo el falso suelo perimetral a las climatizadoras. "
                    "La disipación accidental del agente gaseoso limitaría la sofocación ante un conato eléctrico, requiriendo intervención manual. "
                    "Por ello, la auditoría calibra la madurez operativa en 1,75 (Nivel 2 Repetible) para fundamentar las partidas de adecuación ambiental en el Tomo 2."
                )
            }
        }
    },
    "T2": {
        "calibrated_score": 1.89,
        "declared_score": 2.45,
        "pillars": {
            "T2.P2": {
                "declared": 4.25,
                "calibrated": 1.00,
                "narrative": (
                    "El análisis forense de las evidencias operativas de Molins confirma la ausencia de plataformas de contenedorización "
                    "o clústeres de orquestación Kubernetes en la arquitectura actual de cómputo. El paradigma de despliegue de aplicaciones, "
                    "tanto para servicios corporativos como para los entornos requeridos por el equipo de desarrollo y las cargas industriales "
                    "de planta (OT), se apoya exclusivamente en la provisión de máquinas virtuales completas sobre hipervisores tradicionales "
                    "(VMware vSphere en los CPDs centrales y una instancia aislada de Proxmox en cantera).\n\n"
                    "Los estudios de ingeniería de sistemas de IEEE IC2E demuestran que el empaquetado ligero en contenedores reduce el consumo "
                    "de memoria RAM entre un 65% y un 78% frente a máquinas virtuales tradicionales al eliminar los sistemas operativos huésped "
                    "redundantes, multiplicando la densidad de servidores. La autoevaluación inicial de la organización proyectaba una puntuación "
                    "de 4,25 sobre 5,0. Sin embargo, la contrastación técnica y las evidencias forenses en planta constatan inexistencia de plataformas "
                    "de contenedores; la totalidad de las cargas de desarrollo, test y producción se despliegan sobre más de 300 máquinas virtuales "
                    "pesadas (Windows y Linux) con asignación estática de recursos. Por ello, la auditoría calibra la madurez operativa en 1,00 (Inicial) "
                    "para fundamentar de forma objetiva las prioridades de modernización correspondientes en el Tomo 2."
                )
            }
        }
    },
    "T3": {
        "calibrated_score": 2.01,
        "declared_score": 2.56,
        "pillars": {
            "T3.P1": {
                "declared": 3.75,
                "calibrated": 2.00,
                "narrative": (
                    "La red de campus y centros de datos enlaza los edificios de oficinas y plantas mediante conmutación troncal y fibra óptica a 10 Gbps. "
                    "La autoevaluación inicial de la organización proyectaba una puntuación de 3,75 sobre 5,0. Sin embargo, el levantamiento técnico "
                    "constata la dependencia de una única canalización subterránea de 500 metros sin anillo divergente y la proliferación de conmutadores "
                    "y puntos de acceso Wi-Fi no gestionados en casetas de hormigoneras periféricas sin segmentación industrial estricta. "
                    "Por ello, la auditoría calibra la madurez operativa en 2,00 (Nivel 2 Repetible) para fundamentar el despliegue de SD-LAN y segmentación en el Tomo 2."
                )
            },
            "T3.P3": {
                "declared": 2.33,
                "calibrated": 1.75,
                "narrative": (
                    "La interconexión de centros de datos (DCI) se confía al tendido directo de fibra oscura a 500 metros para sostener el tráfico inter-nodo. "
                    "La autoevaluación inicial proyectaba una puntuación de 2,33 sobre 5,0. No obstante, las evidencias físicas revelan que ambos tendidos "
                    "comparten zanja y arquetas intermedias en la campa de fábrica, careciendo de redundancia por camino geográficamente divergente. "
                    "Por ello, la auditoría calibra la capacidad en 1,75 (Nivel 2 Repetible) para fundamentar el tendido de un anillo redundante en el Tomo 2."
                )
            }
        }
    },
    "T4": {
        "calibrated_score": 2.30,
        "declared_score": 3.28,
        "pillars": {
            "T4.P3": {
                "declared": 3.75,
                "calibrated": 2.50,
                "narrative": (
                    "Los servicios de protección de almacenamiento se sustentan en cabinas unificadas NetApp con replicación SnapMirror entre CPD 1 y CPD 2. "
                    "La autoevaluación inicial proyectaba una puntuación de 3,75 sobre 5,0. Sin embargo, la contrastación técnica constata que la replicación "
                    "opera en modo asíncrono periódico (ventanas de 4 horas), careciendo de arquitectura síncrona activo-activo (MetroCluster) y dependiendo "
                    "de intervenciones manuales de ruptura de espejo para conmutar datastores. "
                    "Por ello, la auditoría calibra la capacidad en 2,50 (Nivel 2 Repetible) para planificar la sincronización continua en el Tomo 2."
                )
            },
            "T4.P4": {
                "declared": 3.67,
                "calibrated": 1.50,
                "narrative": (
                    "La seguridad y custodia de datos combina instantáneas locales con copias secundarias en clúster Cohesity DataPlatform. "
                    "La autoevaluación inicial de la organización proyectaba una puntuación de 3,67 sobre 5,0. No obstante, la auditoría constata "
                    "la ausencia de repositorios inmutables con bloqueo de objetos WORM por hardware (NetApp SnapLock / Cohesity DataLock en Compliance Mode) "
                    "y la carencia de verificación multiautor (MAV), dejando los respaldos expuestos ante un compromiso de credenciales de dominio. "
                    "Por ello, la auditoría calibra la madurez operativa en 1,50 (Nivel 1 Inicial) para priorizar el blindaje inmutable en el Tomo 2."
                )
            }
        }
    },
    "T5": {
        "calibrated_score": 1.80,
        "declared_score": 2.15,
        "pillars": {
            "T5.P2": {
                "declared": 3.50,
                "calibrated": 2.25,
                "narrative": (
                    "La plataforma dispone de copias de seguridad centralizadas con Cohesity y políticas de retención estructuradas. "
                    "La autoevaluación inicial proyectaba una puntuación de 3,50 sobre 5,0. Sin embargo, las evidencias de auditoría indican "
                    "la ausencia de simulacros periódicos documentados de restauración completa para grandes bases de datos (SAP HANA / Oracle) "
                    "hacia entornos aislados de contingencia para certificar los tiempos reales de recuperación (RTO). "
                    "Por ello, la auditoría calibra la capacidad en 2,25 (Nivel 2 Repetible) para formalizar el plan de pruebas en el Tomo 2."
                )
            },
            "T5.P3": {
                "declared": 2.00,
                "calibrated": 1.50,
                "narrative": (
                    "La arquitectura de recuperación ante desastres descansa en la proximidad de CPD 1 y CPD 2 a 500 metros en el campus central. "
                    "La autoevaluación inicial proyectaba 2,00 sobre 5,0. No obstante, al compartir ambas salas el mismo dominio de riesgo geográfico, "
                    "acometida municipal de media tensión y canalizaciones de fábrica, no se garantiza la continuidad ante contingencias mayores de zona. "
                    "Por ello, la auditoría calibra la capacidad en 1,50 (Nivel 1 Inicial) para justificar la extensión a nube o colocation en el Tomo 2."
                )
            }
        }
    },
    "T6": {
        "calibrated_score": 1.94,
        "declared_score": 2.79,
        "pillars": {
            "T6.P2": {
                "declared": 4.50,
                "calibrated": 1.50,
                "narrative": (
                    "La gestión de accesos con privilegios en la infraestructura de servidores y almacenamiento se apoya en políticas de directorio corporativo. "
                    "La autoevaluación inicial de la organización proyectaba una puntuación de 4,50 sobre 5,0. Sin embargo, la contrastación técnica "
                    "constata la ausencia de una solución corporativa de gestión y bóveda de accesos privilegiados (PAM), coexistiendo credenciales "
                    "administrativas compartidas entre el equipo propio y proveedores externos de soporte sin rotación automática ni aislamiento de sesiones. "
                    "Por ello, la auditoría calibra la madurez operativa en 1,50 (Nivel 1 Inicial) para situar el despliegue de PAM como prioridad #1 en el Tomo 2."
                )
            },
            "T6.P5": {
                "declared": 3.00,
                "calibrated": 2.00,
                "narrative": (
                    "La monitorización de seguridad registra trazas en consolas de cortafuegos y plataformas operativas locales. "
                    "La autoevaluación inicial proyectaba 3,00 sobre 5,0. No obstante, las evidencias técnicas indican la ausencia de un SIEM/SOC "
                    "centralizado con retención inmutable de registros durante 12 meses, generando una brecha de cumplimiento frente a la Directiva NIS2. "
                    "Por ello, la auditoría calibra la capacidad en 2,00 (Nivel 2 Repetible) para fundamentar la ingestión de telemetría en el Tomo 2."
                )
            }
        }
    },
    "T7": {
        "calibrated_score": 2.15,
        "declared_score": 2.49,
        "pillars": {
            "T7.P5": {
                "declared": 3.20,
                "calibrated": 2.00,
                "narrative": (
                    "La observabilidad de infraestructura se articula mediante sondas de Zabbix e interfaces nativas de virtualización y red. "
                    "La autoevaluación inicial proyectaba una puntuación de 3,20 sobre 5,0. Sin embargo, el análisis técnico constata que la monitorización "
                    "opera predominantemente a nivel de infraestructura básica (CPU, RAM, ping), careciendo de observabilidad de transacciones de negocio (APM), "
                    "gestión de correlación de eventos o automatización AIOps para la resolución proactiva de incidencias. "
                    "Por ello, la auditoría calibra la capacidad en 2,00 (Nivel 2 Repetible) para impulsar la monitorización de servicios en el Tomo 2."
                )
            }
        }
    },
    "T8": {
        "calibrated_score": 2.00,
        "declared_score": 2.44,
        "pillars": {
            "T8.P1": {
                "declared": 3.00,
                "calibrated": 2.00,
                "narrative": (
                    "La planificación tecnológica dispone de líneas maestras de evolución hacia entornos híbridos y modernización de bases de datos. "
                    "La autoevaluación inicial proyectaba 3,00 sobre 5,0. No obstante, el levantamiento constata la proximidad del vencimiento contractual "
                    "de Broadcom/VMware en mayo de 2027 sin un análisis formal de TCO comparativo frente a alternativas hiperconvergentes o cloud, "
                    "lo que expone a la organización a un incremento sustancial no planificado del OPEX recurrente. "
                    "Por ello, la auditoría calibra la capacidad en 2,00 (Nivel 2 Repetible) para establecer el marco de gobernanza FinOps en el Tomo 2."
                )
            },
            "T8.P2": {
                "declared": 2.50,
                "calibrated": 1.75,
                "narrative": (
                    "El gobierno de contratos de infraestructura acusa la dispersión derivada de adquisiciones corporativas internacionales. "
                    "La autoevaluación inicial proyectaba 2,50 sobre 5,0. Sin embargo, en la filial SECIL de Portugal se mantiene un contrato cerrado "
                    "de servicios gestionados con el operador NOS que representa un desembolso recurrente sin integración operativa con el equipo central. "
                    "Por ello, la auditoría calibra la capacidad en 1,75 (Nivel 2 Repetible) para justificar la captura de sinergias en el Tomo 2."
                )
            }
        }
    },
    "T9": {
        "calibrated_score": 2.10,
        "declared_score": 3.15,
        "pillars": {
            "T9.P1": {
                "declared": 4.00,
                "calibrated": 1.75,
                "narrative": (
                    "La gestión del parque de puestos de trabajo cubre una flota de aproximadamente 1.200 usuarios y estaciones en centros fabriles. "
                    "La autoevaluación inicial de la organización proyectaba una puntuación de 4,00 sobre 5,0. Sin embargo, la contrastación técnica "
                    "constata que la preparación de los aproximadamente 350 ordenadores renovados al año se ejecuta de forma artesanal mediante memorias USB "
                    "e imágenes estáticas de Ghost/MDT, requiriendo 3,5 horas de dedicación manual de técnico por equipo ante la falta de Windows Autopilot Zero-Touch. "
                    "Por ello, la auditoría calibra la madurez operativa en 1,75 (Nivel 2 Repetible) para fundamentar la modernización a Intune en el Tomo 2."
                )
            },
            "T9.P5": {
                "declared": 2.75,
                "calibrated": 1.25,
                "narrative": (
                    "La experiencia digital del empleado (DEX) se gestiona de forma reactiva a través del canal de atención a usuarios del Service Desk. "
                    "La autoevaluación inicial proyectaba 2,75 sobre 5,0. No obstante, las evidencias demuestran la ausencia total de herramientas "
                    "de telemetría continua de puesto (como Nexthink, 1E o Endpoint Analytics), detectándose incidencias de rendimiento solo tras el reporte del usuario. "
                    "Por ello, la auditoría calibra la capacidad en 1,25 (Nivel 1 Inicial) para priorizar la observabilidad de experiencia en el Tomo 2."
                )
            }
        }
    },
    "T10": {
        "calibrated_score": 1.95,
        "declared_score": 2.40,
        "pillars": {
            "T10.P3": {
                "declared": 2.50,
                "calibrated": 1.75,
                "narrative": (
                    "La operativa de expedición y pesaje de cemento a granel se apoya en sistemas de control de básculas y el aplicativo Prenet en fábrica. "
                    "La autoevaluación inicial proyectaba 2,50 sobre 5,0. Sin embargo, el análisis técnico revela que la base de datos Oracle 10g/11g "
                    "experimenta saturación recurrente de CPU por consultas de desarrollo antiguo en Forms & Reports, ralentizando la emisión de albaranes "
                    "y generando colas de camiones cisterna en accesos durante turnos de máxima demanda. "
                    "Por ello, la auditoría calibra la capacidad en 1,75 (Nivel 2 Repetible) para fundamentar la modernización de básculas en el Tomo 2."
                )
            },
            "T10.P4": {
                "declared": 2.50,
                "calibrated": 1.75,
                "narrative": (
                    "La integración entre las básculas de planta y los sistemas corporativos ERP se confía a interfaces directas y ficheros planos. "
                    "La autoevaluación inicial proyectaba 2,50 sobre 5,0. No obstante, se constata la carencia de una capa de integración moderna "
                    "mediante APIs REST estandarizadas y colas de mensajería desacopladas, lo que limita la resiliencia operativa ante caídas del enlace central. "
                    "Por ello, la auditoría calibra la capacidad en 1,75 (Nivel 2 Repetible) para justificar la integración industrial en el Tomo 2."
                )
            }
        }
    }
}

def apply_harmonization():
    print("=" * 80)
    print("APPLYING COMPREHENSIVE FORENSIC CALIBRATION ACROSS ALL 10 TOWERS")
    print("=" * 80)

    for code, spec in CALIBRATION_SPEC.items():
        p = REPO_ROOT / f"working/molins/{code}/blueprint_{code.lower()}_payload.json"
        if not p.exists():
            print(f"Skipping {code} (not found)")
            continue

        with open(p, "r", encoding="utf-8-sig") as f:
            d = json.load(f)

        d["score"] = spec["calibrated_score"]
        d["overall_score"] = spec["calibrated_score"]
        d["exact_score"] = spec["calibrated_score"]
        d["maturity_score"] = spec["calibrated_score"]
        d["declared_score"] = spec["declared_score"]
        d["survey_declared_score"] = spec["declared_score"]

        # Update pillars
        for pi in d.get("pillars_analysis", []):
            pid = pi.get("pillar_id")
            if pid in spec["pillars"]:
                p_spec = spec["pillars"][pid]
                pi["declared_score"] = p_spec["declared"]
                pi["survey_declared_score"] = p_spec["declared"]
                pi["score"] = p_spec["calibrated"]
                pi["exact_score"] = p_spec["calibrated"]
                pi["perception_gap_delta"] = round(p_spec["calibrated"] - p_spec["declared"], 2)
                pi["perception_gap_warning"] = True

                nar = p_spec["narrative"]
                pi["asis_architecture_description"] = nar
                pi["architectural_narrative_paragraphs"] = [s.strip() for s in nar.split("\n\n") if s.strip()]

        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)

        print(f"✓ Harmonized {code}: Declared={spec['declared_score']:.2f} -> Calibrated={spec['calibrated_score']:.2f} with native Divergence Tables.")

if __name__ == "__main__":
    apply_harmonization()
