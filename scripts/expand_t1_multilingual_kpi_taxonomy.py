"""Expand engine_config/taxonomy_multilingual.json to include full KPI hierarchy under T1 across all 6 locales."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAX_PATH = ROOT / "engine_config" / "taxonomy_multilingual.json"


def expand_taxonomy() -> None:
    data = json.loads(TAX_PATH.read_text(encoding="utf-8"))

    t1_pillars = data.get("T1", {}).get("pillars", {})

    t1_kpis = {
        "T1.P1": {
            "T1.P1.K1": {
                "canonical_name": "Guaranteed Electrical Autonomy (UPS & Backup Generators)",
                "locales": {
                    "en": "Guaranteed Electrical Autonomy (UPS & Backup Generators)",
                    "es": "Autonomía Eléctrica Garantizada (UPS y Generadores)",
                    "pt": "Autonomia Elétrica Garantida (UPS e Geradores)",
                    "fr": "Autonomie Électrique Garantie (UPS et Générateurs)",
                    "de": "Garantierte elektrische Autonomie (USV & Notstromaggregate)",
                    "ja": "保証された電気的自律性（UPSおよびバックアップ発電機）"
                }
            },
            "T1.P1.K2": {
                "canonical_name": "Switching Test Cadence & Controlled Failover Verification",
                "locales": {
                    "en": "Switching Test Cadence & Controlled Failover Verification",
                    "es": "Cadencia de Pruebas de Conmutación y Fallos Controlados",
                    "pt": "Cadência de Testes de Comutação e Failover Controlado",
                    "fr": "Cadence des Tests de Commutation et Basculement Contrôlé",
                    "de": "Schalttest-Kadenz & kontrollierte Failover-Verifizierung",
                    "ja": "切り替えテストの頻度および制御されたフェイルオーバー検証"
                }
            },
            "T1.P1.K3": {
                "canonical_name": "Power Distribution Redundancy & Single Points of Failure Elimination",
                "locales": {
                    "en": "Power Distribution Redundancy & Single Points of Failure Elimination",
                    "es": "Redundancia de Distribución Eléctrica y Eliminación de SPOF",
                    "pt": "Redundância de Distribuição Elétrica e Eliminação de SPOF",
                    "fr": "Redondance de Distribution Électrique et Élimination des SPOF",
                    "de": "Redundanz der Stromverteilung & Beseitigung von SPOFs",
                    "ja": "配電冗長性および単一障害点（SPOF）の排除"
                }
            },
            "T1.P1.K4": {
                "canonical_name": "Electrical Capacity Utilization & Planned Headroom Management",
                "locales": {
                    "en": "Electrical Capacity Utilization & Planned Headroom Management",
                    "es": "Utilización de Capacidad Eléctrica y Gestión de Holgura",
                    "pt": "Utilização de Capacidade Elétrica e Gestão de Margem",
                    "fr": "Utilisation de la Capacité Électrique et Gestion des Marges",
                    "de": "Auslastung der elektrischen Kapazität & Headroom-Management",
                    "ja": "電力容量の使用率および計画されたヘッドルーム管理"
                }
            }
        },
        "T1.P2": {
            "T1.P2.K1": {
                "canonical_name": "Environmental Threshold Compliance & Continuous Thermal Telemetry",
                "locales": {
                    "en": "Environmental Threshold Compliance & Continuous Thermal Telemetry",
                    "es": "Cumplimiento de Rangos Ambientales y Telemetría Térmica Continua",
                    "pt": "Conformidade de Limites Ambientais e Telemetria Térmica Contínua",
                    "fr": "Conformité des Seuils Environnementaux et Télémétrie Thermique",
                    "de": "Einhaltung von Umgebungsschwellenwerten & kontinuierliche thermische Telemetrie",
                    "ja": "環境閾値の準拠および継続的な温度テレメトリ"
                }
            },
            "T1.P2.K2": {
                "canonical_name": "Thermal Hotspot Mitigation & Per-Rack Power Density Governance",
                "locales": {
                    "en": "Thermal Hotspot Mitigation & Per-Rack Power Density Governance",
                    "es": "Mitigación de Hotspots Térmicos y Densidad por Rack",
                    "pt": "Mitigação de Hotspots Térmicos e Densidade por Rack",
                    "fr": "Atténuation des Points Chauds et Densité Électrique par Baie",
                    "de": "Reduzierung thermischer Hotspots & Dichtesteuerung pro Rack",
                    "ja": "熱的ホットスポットの緩和およびラック単位の電力密度管理"
                }
            },
            "T1.P2.K3": {
                "canonical_name": "HVAC Cooling Resiliency (N+1 / 2N) & Concurrent Maintainability",
                "locales": {
                    "en": "HVAC Cooling Resiliency (N+1 / 2N) & Concurrent Maintainability",
                    "es": "Resiliencia de Climatización (N+1 / 2N) y Mantenibilidad Concurrente",
                    "pt": "Resiliência de Climatização (N+1 / 2N) e Manutenibilidade Concorrente",
                    "fr": "Résilience CVC (N+1 / 2N) et Maintenabilité Simultanée",
                    "de": "Klima-Resilienz (N+1 / 2N) & gleichzeitige Wartbarkeit",
                    "ja": "空調レジリエンス（N+1 / 2N）および同時保守性"
                }
            }
        },
        "T1.P3": {
            "T1.P3.K1": {
                "canonical_name": "Zoned Physical Access Control & Biometric Multi-Factor Authentication",
                "locales": {
                    "en": "Zoned Physical Access Control & Biometric Multi-Factor Authentication",
                    "es": "Control de Acceso Físico Zonificado y Autenticación Biométrica",
                    "pt": "Controle de Acesso Físico Zonificado e Autenticação Biométrica",
                    "fr": "Contrôle d'Accès Physique Zoné et Authentification Biométrique",
                    "de": "Zonierte physische Zutrittskontrolle & biometrische MFA",
                    "ja": "ゾーン別物理アクセス制御および生体マルチファクタ認証"
                }
            },
            "T1.P3.K2": {
                "canonical_name": "Vendor Escort Protocols, Room Access Logging & Permits to Work",
                "locales": {
                    "en": "Vendor Escort Protocols, Room Access Logging & Permits to Work",
                    "es": "Protocolos de Acompañamiento, Registro de Accesos y Permisos de Trabajo",
                    "pt": "Protocolos de Acompanhamento, Registro de Acessos e Permissões de Trabalho",
                    "fr": "Protocoles d'Escorte Fournisseurs, Journaux d'Accès et Permis de Travail",
                    "de": "Dienstleister-Eskortenprotokolle, Zutrittsprotokollierung & Arbeitserlaubnisse",
                    "ja": "ベンダーエスコート手順、入室ログ記録および作業許可証"
                }
            },
            "T1.P3.K3": {
                "canonical_name": "CCTV Surveillance Coverage, Access Logs & Tamper-Proof Audit Retention",
                "locales": {
                    "en": "CCTV Surveillance Coverage, Access Logs & Tamper-Proof Audit Retention",
                    "es": "Cobertura CCTV, Registro de Accesos y Retención Inmutable de Evidencias",
                    "pt": "Cobertura de CFTV, Registro de Acessos e Retenção Imutável de Auditoria",
                    "fr": "Couverture Vidéosurveillance, Journaux d'Accès et Rétention Immuable",
                    "de": "CCTV-Überwachungsabdeckung, Zutrittsprotokolle & revisionssichere Aufbewahrung",
                    "ja": "CCTV監視カバレッジ、アクセスログおよび改ざん防止監査ログ保持"
                }
            }
        },
        "T1.P4": {
            "T1.P4.K1": {
                "canonical_name": "Early Fire Detection (VESDA/Aspirating Smoke) & Room Compartmentalization",
                "locales": {
                    "en": "Early Fire Detection (VESDA/Aspirating Smoke) & Room Compartmentalization",
                    "es": "Detección Temprana de Incendios (VESDA) y Sectorización de Salas",
                    "pt": "Detecção Precoce de Incêndio (VESDA) e Compartimentação de Salas",
                    "fr": "Détection Incendie Précoce (VESDA) et Compartimentation des Salles",
                    "de": "Frühe Brandfrüherkennung (VESDA) & Raumkompartimentierung",
                    "ja": "超高感度煙検知（VESDA）および防火区画化"
                }
            },
            "T1.P4.K2": {
                "canonical_name": "Clean Agent Gaseous Fire Suppression & Discharge System Certification",
                "locales": {
                    "en": "Clean Agent Gaseous Fire Suppression & Discharge System Certification",
                    "es": "Extinción Automática por Gas Limpio y Certificación de Descarga",
                    "pt": "Supressão Automática por Gás Limpo e Certificação de Descarga",
                    "fr": "Extinction Automatique par Gaz Propre et Certification de Décharge",
                    "de": "Automatische Gaslöschung & Entladungssystem-Zertifizierung",
                    "ja": "クリーンガス自動消火設備および放出システム認証"
                }
            },
            "T1.P4.K3": {
                "canonical_name": "Environmental Perimeter Hazards: Water Ingress, Flood & Contaminant Mitigation",
                "locales": {
                    "en": "Environmental Perimeter Hazards: Water Ingress, Flood & Contaminant Mitigation",
                    "es": "Mitigación de Inundación, Detección de Fugas de Agua y Contaminantes",
                    "pt": "Mitigação de Inundação, Detecção de Fugas de Água e Contaminantes",
                    "fr": "Mitigation des Infiltrations d'Eau, Inondations et Contaminants",
                    "de": "Umweltrisiken am Perimeter: Wassereinbruch, Hochwasser & Schadstoffminderung",
                    "ja": "環境周辺リスク：漏水検知、洪水対策および汚染物質低減"
                }
            }
        },
        "T1.P5": {
            "T1.P5.K1": {
                "canonical_name": "Continuous Infrastructure Telemetry (DCIM/BMS) & Unified Alarm Triage",
                "locales": {
                    "en": "Continuous Infrastructure Telemetry (DCIM/BMS) & Unified Alarm Triage",
                    "es": "Telemetría Continua de Infraestructura (DCIM/BMS) y Gestión de Alarmas",
                    "pt": "Telemetria Contínua de Infraestrutura (DCIM/BMS) e Triagem de Alarmes",
                    "fr": "Télémétrie Continue d'Infrastructure (DCIM/BMS) et Triage d'Alarmes",
                    "de": "Kontinuierliche Infrastruktur-Telemetrie (DCIM/BMS) & Alarmmanagement",
                    "ja": "継続的インフラテレメトリ（DCIM/BMS）および統合アラームトリアージ"
                }
            },
            "T1.P5.K2": {
                "canonical_name": "Preventive Maintenance Schedules, Vendor SLAs & Spares Inventory",
                "locales": {
                    "en": "Preventive Maintenance Schedules, Vendor SLAs & Spares Inventory",
                    "es": "Mantenimiento Preventivo, Acuerdos de Nivel de Servicio (SLA) y Repuestos",
                    "pt": "Manutenção Preventiva, Acordos de Nível de Serviço (SLA) e Peças Sobressalentes",
                    "fr": "Maintenance Préventive, Niveaux de Service (SLA) et Pièces de Rechange",
                    "de": "Präventive Wartungspläne, Hersteller-SLAs & Ersatzteilbevorratung",
                    "ja": "予防保守スケジュール、ベンダーSLAおよび重要スペアパーツ在庫"
                }
            },
            "T1.P5.K3": {
                "canonical_name": "Facility Capacity Planning & Lifecycle Refresh (Space, Power, Cooling)",
                "locales": {
                    "en": "Facility Capacity Planning & Lifecycle Refresh (Space, Power, Cooling)",
                    "es": "Planificación de Capacidad Física y Ciclo de Vida (Espacio, Energía, Clima)",
                    "pt": "Planejamento de Capacidade Física e Ciclo de Vida (Espaço, Energia, Clima)",
                    "fr": "Planification de la Capacité des Installations et Renouvellement",
                    "de": "Facility-Kapazitätsplanung & Lifecycle-Refresh (Fläche, Strom, Kühlung)",
                    "ja": "ファシリティ容量計画およびライフサイクル更新（スペース、電力、空調）"
                }
            }
        }
    }

    for p_id, kpis_dict in t1_kpis.items():
        if p_id in t1_pillars:
            t1_pillars[p_id]["kpis"] = kpis_dict

    TAX_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Expanded {TAX_PATH.name} with complete T1 KPI multilingual hierarchy across all 6 locales.")


if __name__ == "__main__":
    expand_taxonomy()
