"""Refactor T3 to 100% canonical Technical English and expand taxonomy_multilingual.json with all T3 KPIs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T3_DEF_PATH = ROOT / "engine_config" / "towers" / "T3" / "tower_definition_T3.json"
TAX_PATH = ROOT / "engine_config" / "taxonomy_multilingual.json"


def refactor_t3() -> None:
    # 1. Update tower_definition_T3.json to canonical Technical English
    data = json.loads(T3_DEF_PATH.read_text(encoding="utf-8"))

    data["tower_name"] = "Network & Connectivity"
    data["maturity_scale"] = [
        {"level": 1, "label": "Initial", "operational_reading": "Network architecture is ad-hoc, unsegmented, or lacks documented topology."},
        {"level": 2, "label": "Managed", "operational_reading": "Baseline routing and switching exist but failover and observability lack automation."},
        {"level": 3, "label": "Defined", "operational_reading": "Network topology, routing policies, and segmentation standards are standardized enterprise-wide."},
        {"level": 4, "label": "Quantitatively Managed", "operational_reading": "Network is automated via NetDevOps, continuous telemetry flows, and automated failover."},
        {"level": 5, "label": "Optimizing", "operational_reading": "Software-defined network mesh with autonomous self-healing, predictive capacity scaling, and zero-trust microsegmentation."}
    ]

    data["score_bands"] = [
        {"min": 1.00, "max": 1.59, "label": "Level 1 - Initial"},
        {"min": 1.60, "max": 2.59, "label": "Level 2 - Managed"},
        {"min": 2.60, "max": 3.59, "label": "Level 3 - Defined"},
        {"min": 3.60, "max": 4.59, "label": "Level 4 - Quantitatively Managed"},
        {"min": 4.60, "max": 5.00, "label": "Level 5 - Optimized"}
    ]

    pillars_english = [
        {
            "pillar_id": "T3.P1",
            "pillar_name": "Data Center & Campus Network Foundation (LAN / Core Routing & Switching)",
            "weight_pct": 22,
            "kpis": [
                {
                    "kpi_id": "T3.P1.K1",
                    "kpi_name": "Core Network Resiliency & Single Point of Failure Elimination",
                    "questions": [{
                        "question_id": "T3.P1.K1.PR1",
                        "question_text": "How are core switching fabrics and distribution layers designed to eliminate single points of failure across primary facilities?"
                    }]
                },
                {
                    "kpi_id": "T3.P1.K2",
                    "kpi_name": "Internal Segmentation Maturity: VLANs, VRFs & Security Zones",
                    "questions": [{
                        "question_id": "T3.P1.K2.PR1",
                        "question_text": "What level of macro and micro-segmentation isolates workloads and traffic zones across local switching fabrics?"
                    }]
                },
                {
                    "kpi_id": "T3.P1.K3",
                    "kpi_name": "Architecture & Configuration Standardization (Templates & Drift Control)",
                    "questions": [{
                        "question_id": "T3.P1.K3.PR1",
                        "question_text": "How are switch configurations, firmware baselines, and configuration drift managed across network hardware?"
                    }]
                },
                {
                    "kpi_id": "T3.P1.K4",
                    "kpi_name": "LAN Capacity & Performance Management (Oversubscription & Latency)",
                    "questions": [{
                        "question_id": "T3.P1.K4.PR1",
                        "question_text": "How are port capacity, oversubscription ratios, and packet buffer latency monitored across core switches?"
                    }]
                }
            ]
        },
        {
            "pillar_id": "T3.P2",
            "pillar_name": "WAN / SD-WAN & Branch Connectivity",
            "weight_pct": 20,
            "kpis": [
                {
                    "kpi_id": "T3.P2.K1",
                    "kpi_name": "Site Connectivity Resiliency (Redundancy, Carrier Diversity & Failover)",
                    "questions": [{
                        "question_id": "T3.P2.K1.PR1",
                        "question_text": "What carrier diversity, dual-homing, and automated failover mechanisms protect regional branch and facility connections?"
                    }]
                },
                {
                    "kpi_id": "T3.P2.K2",
                    "kpi_name": "WAN Performance Governance: Latency, Loss & Per-Application Jitter",
                    "questions": [{
                        "question_id": "T3.P2.K2.PR1",
                        "question_text": "How is network latency, packet loss, and jitter measured and enforced for critical application transport?"
                    }]
                },
                {
                    "kpi_id": "T3.P2.K3",
                    "kpi_name": "Traffic Steering Policies & Quality of Service (QoS) Prioritization",
                    "questions": [{
                        "question_id": "T3.P2.K3.PR1",
                        "question_text": "How does SD-WAN dynamic path selection prioritize mission-critical business transactions over bulk traffic?"
                    }]
                },
                {
                    "kpi_id": "T3.P2.K4",
                    "kpi_name": "Carrier Vendor Governance & Contractual SLA Compliance",
                    "questions": [{
                        "question_id": "T3.P2.K4.PR1",
                        "question_text": "How are telecommunication provider SLAs, MTTR commitments, and credit penalties monitored and audited?"
                    }]
                }
            ]
        },
        {
            "pillar_id": "T3.P3",
            "pillar_name": "DCI (Data Center Interconnect) & Resilient Transport",
            "weight_pct": 18,
            "kpis": [
                {
                    "kpi_id": "T3.P3.K1",
                    "kpi_name": "Physical Route Diversity & DCI Conduit Redundancy",
                    "questions": [{
                        "question_id": "T3.P3.K1.PR1",
                        "question_text": "What physical conduit separation, fiber path diversity, and right-of-way independence protect critical DCI circuits?"
                    }]
                },
                {
                    "kpi_id": "T3.P3.K2",
                    "kpi_name": "DCI Throughput SLA, Latency Telemetry & Optical Monitoring",
                    "questions": [{
                        "question_id": "T3.P3.K2.PR1",
                        "question_text": "How are sub-millisecond round-trip times and optical signal levels monitored across high-speed interconnect links?"
                    }]
                },
                {
                    "kpi_id": "T3.P3.K3",
                    "kpi_name": "Transport Switching Cadence & Live Failover Drill Evidence",
                    "questions": [{
                        "question_id": "T3.P3.K3.PR1",
                        "question_text": "How frequently are unannounced optical link cuts and BGP route convergence drills executed under production load?"
                    }]
                }
            ]
        },
        {
            "pillar_id": "T3.P4",
            "pillar_name": "Hybrid Cloud Connectivity & Edge Services",
            "weight_pct": 20,
            "kpis": [
                {
                    "kpi_id": "T3.P4.K1",
                    "kpi_name": "Hybrid Cloud Transit Architecture: BGP Routing, Segmentation & Peering",
                    "questions": [{
                        "question_id": "T3.P4.K1.PR1",
                        "question_text": "How are AWS Direct Connect, Azure ExpressRoute, or Transit Gateways segmented between production and non-production?"
                    }]
                },
                {
                    "kpi_id": "T3.P4.K2",
                    "kpi_name": "Cloud Interconnect Resiliency: Multi-Region Redundancy & Automated Fallback",
                    "questions": [{
                        "question_id": "T3.P4.K2.PR1",
                        "question_text": "What automated BFD-backed route failover protects dedicated cloud interconnects from cross-region outages?"
                    }]
                },
                {
                    "kpi_id": "T3.P4.K3",
                    "kpi_name": "Edge Service Ingress: L4/L7 Load Balancing, WAF & Public API Protection",
                    "questions": [{
                        "question_id": "T3.P4.K3.PR1",
                        "question_text": "How do perimeter ingress load balancers, DDoS mitigation, and API gateways protect public endpoints?"
                    }]
                }
            ]
        },
        {
            "pillar_id": "T3.P5",
            "pillar_name": "Network Operations, Observability & Automation (NetOps/NetDevOps)",
            "weight_pct": 20,
            "kpis": [
                {
                    "kpi_id": "T3.P5.K1",
                    "kpi_name": "Full-Stack Network Observability: SNMP Telemetry, NetFlow & Streaming Analytics",
                    "questions": [{
                        "question_id": "T3.P5.K1.PR1",
                        "question_text": "What unified observability platform aggregates flow telemetry, interface drops, and synthetic network latency probes 24/7?"
                    }]
                },
                {
                    "kpi_id": "T3.P5.K2",
                    "kpi_name": "Infrastructure as Code (IaC) Network Change Governance & Versioned Rollbacks",
                    "questions": [{
                        "question_id": "T3.P5.K2.PR1",
                        "question_text": "How are network configuration changes governed through version control, CI/CD pipelines, and automated rollback triggers?"
                    }]
                },
                {
                    "kpi_id": "T3.P5.K3",
                    "kpi_name": "Source-of-Truth Network Automation (NetDevOps & Reproducible Fleet Baselines)",
                    "questions": [{
                        "question_id": "T3.P5.K3.PR1",
                        "question_text": "How does a single source of truth (e.g. NetBox) drive automated configuration generation and device provisioning?"
                    }]
                },
                {
                    "kpi_id": "T3.P5.K4",
                    "kpi_name": "Network Incident Response Lifecycle, Automated Runbooks & MTTR Governance",
                    "questions": [{
                        "question_id": "T3.P5.K4.PR1",
                        "question_text": "What automated triage runbooks, root-cause post-mortems, and mean-time-to-repair (MTTR) metrics govern network incidents?"
                    }]
                }
            ]
        }
    ]

    data["pillars"] = pillars_english

    all_questions = []
    for pil in pillars_english:
        for k in pil["kpis"]:
            for q in k["questions"]:
                all_questions.append({
                    "question_id": q["question_id"],
                    "question_text": q["question_text"],
                    "pillar_id": pil["pillar_id"],
                    "kpi_id": k["kpi_id"],
                    "kpi_name": k["kpi_name"]
                })
    data["questions"] = all_questions

    T3_DEF_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Refactored {T3_DEF_PATH.name} to 100% canonical Technical English.")

    # 2. Update taxonomy_multilingual.json for all T3 KPIs
    tax_data = json.loads(TAX_PATH.read_text(encoding="utf-8"))
    t3_pillars = tax_data.get("T3", {}).get("pillars", {})

    t3_kpis = {
        "T3.P1": {
            "T3.P1.K1": {
                "canonical_name": "Core Network Resiliency & Single Point of Failure Elimination",
                "locales": {
                    "en": "Core Network Resiliency & Single Point of Failure Elimination",
                    "es": "Resiliencia de Red Core y Eliminación de SPOF",
                    "pt": "Resiliência de Rede Core e Eliminação de SPOF",
                    "fr": "Résilience du Cœur de Réseau et Élimination des SPOF",
                    "de": "Core-Netzwerk-Resilienz & Beseitigung von SPOFs",
                    "ja": "コアネットワークレジリエンスおよび単一障害点（SPOF）の排除"
                }
            },
            "T3.P1.K2": {
                "canonical_name": "Internal Segmentation Maturity: VLANs, VRFs & Security Zones",
                "locales": {
                    "en": "Internal Segmentation Maturity: VLANs, VRFs & Security Zones",
                    "es": "Madurez de Segmentación Interna: VLANs, VRFs y Zonas de Seguridad",
                    "pt": "Maturidade de Segmentação Interna: VLANs, VRFs e Zonas de Segurança",
                    "fr": "Maturité de Segmentation Interne: VLANs, VRFs et Zones de Sécurité",
                    "de": "Interne Segmentierungsreife: VLANs, VRFs & Sicherheitszonen",
                    "ja": "内部セグメンテーション成熟度：VLAN、VRFおよびセキュリティゾーン"
                }
            },
            "T3.P1.K3": {
                "canonical_name": "Architecture & Configuration Standardization (Templates & Drift Control)",
                "locales": {
                    "en": "Architecture & Configuration Standardization (Templates & Drift Control)",
                    "es": "Estandarización de Arquitectura y Configuración (Plantillas y Control de Deriva)",
                    "pt": "Padronização de Arquitetura e Configuração (Modelos e Controle de Desvio)",
                    "fr": "Standardisation d'Architecture et Configuration (Modèles et Dérive)",
                    "de": "Architektur- & Konfigurationsstandardisierung (Templates & Drift-Kontrolle)",
                    "ja": "アーキテクチャおよび構成の標準化（テンプレートとドリフト制御）"
                }
            },
            "T3.P1.K4": {
                "canonical_name": "LAN Capacity & Performance Management (Oversubscription & Latency)",
                "locales": {
                    "en": "LAN Capacity & Performance Management (Oversubscription & Latency)",
                    "es": "Gestión de Capacidad y Rendimiento LAN (Sobresuscripción y Latencia)",
                    "pt": "Gestão de Capacidade e Desempenho LAN (Sobresubscrição e Latência)",
                    "fr": "Gestion de Capacité et Performance LAN (Sur-souscription et Latence)",
                    "de": "LAN-Kapazitäts- & Leistungsmanagement (Oversubscription & Latenz)",
                    "ja": "LAN容量およびパフォーマンス管理（オーバーサブスクリプションとレイテンシ）"
                }
            }
        },
        "T3.P2": {
            "T3.P2.K1": {
                "canonical_name": "Site Connectivity Resiliency (Redundancy, Carrier Diversity & Failover)",
                "locales": {
                    "en": "Site Connectivity Resiliency (Redundancy, Carrier Diversity & Failover)",
                    "es": "Resiliencia de Conectividad en Sedes (Diversidad de Operador y Failover)",
                    "pt": "Resiliência de Conectividade em Sedes (Diversidade de Operadora e Failover)",
                    "fr": "Résilience de Connectivité de Site (Diversité d'Opérateurs et Basculement)",
                    "de": "Standortkonnektivitäts-Resilienz (Redundanz, Carrier-Diversität & Failover)",
                    "ja": "拠点接続レジリエンス（冗長性、キャリア多様性およびフェイルオーバー）"
                }
            },
            "T3.P2.K2": {
                "canonical_name": "WAN Performance Governance: Latency, Loss & Per-Application Jitter",
                "locales": {
                    "en": "WAN Performance Governance: Latency, Loss & Per-Application Jitter",
                    "es": "Gobernanza de Rendimiento WAN: Latencia, Pérdida y Jitter por Aplicación",
                    "pt": "Governança de Desempenho WAN: Latência, Perda e Jitter por Aplicação",
                    "fr": "Gouvernance de Performance WAN: Latence, Perte et Gigue par Application",
                    "de": "WAN-Leistungsüberwachung: Latenz, Paketverlust & Jitter pro Anwendung",
                    "ja": "WANパフォーマンスガバナンス：アプリケーション別のレイテンシ、パケット損失、ジッター"
                }
            },
            "T3.P2.K3": {
                "canonical_name": "Traffic Steering Policies & Quality of Service (QoS) Prioritization",
                "locales": {
                    "en": "Traffic Steering Policies & Quality of Service (QoS) Prioritization",
                    "es": "Políticas de Enrutamiento Dinámico y Priorización de Calidad de Servicio (QoS)",
                    "pt": "Políticas de Roteamento Dinâmico e Priorização de Qualidade de Serviço (QoS)",
                    "fr": "Politiques de Routage Dynamique et Priorisation QoS",
                    "de": "Traffic-Steering-Richtlinien & Quality of Service (QoS)-Priorisierung",
                    "ja": "トラフィックステアリングポリシーおよびQoS優先順位付け"
                }
            },
            "T3.P2.K4": {
                "canonical_name": "Carrier Vendor Governance & Contractual SLA Compliance",
                "locales": {
                    "en": "Carrier Vendor Governance & Contractual SLA Compliance",
                    "es": "Gobernanza de Proveedores de Telecomunicaciones y Cumplimiento de SLAs",
                    "pt": "Governança de Fornecedores de Telecomunicações e Cumprimento de SLAs",
                    "fr": "Gouvernance des Opérateurs Télécoms et Respect des Niveaux de Service (SLA)",
                    "de": "Carrier-Vendor-Governance & vertragliche SLA-Einhaltung",
                    "ja": "通信キャリアベンダーガバナンスおよび契約SLA遵守"
                }
            }
        },
        "T3.P3": {
            "T3.P3.K1": {
                "canonical_name": "Physical Route Diversity & DCI Conduit Redundancy",
                "locales": {
                    "en": "Physical Route Diversity & DCI Conduit Redundancy",
                    "es": "Diversidad de Trazado Físico y Redundancia de Canalizaciones DCI",
                    "pt": "Diversidade de Rota Física e Redundância de Duto DCI",
                    "fr": "Diversité des Itinéraires Physiques et Redondance DCI",
                    "de": "Physische Trassendiversität & DCI-Kanalredundanz",
                    "ja": "物理ルート多様性およびDCI管路冗長性"
                }
            },
            "T3.P3.K2": {
                "canonical_name": "DCI Throughput SLA, Latency Telemetry & Optical Monitoring",
                "locales": {
                    "en": "DCI Throughput SLA, Latency Telemetry & Optical Monitoring",
                    "es": "SLAs de Ancho de Banda DCI, Telemetría de Latencia y Monitorización Óptica",
                    "pt": "SLAs de Vazão DCI, Telemetria de Latência e Monitoramento Óptico",
                    "fr": "SLA de Débit DCI, Télémétrie de Latence et Surveillance Optique",
                    "de": "DCI-Durchsatz-SLA, Latenz-Telemetrie & optisches Monitoring",
                    "ja": "DCIスループットSLA、レイテンシテレメトリおよび光監視"
                }
            },
            "T3.P3.K3": {
                "canonical_name": "Transport Switching Cadence & Live Failover Drill Evidence",
                "locales": {
                    "en": "Transport Switching Cadence & Live Failover Drill Evidence",
                    "es": "Cadencia de Conmutación de Transporte y Evidencia de Simulacros de Failover",
                    "pt": "Cadência de Comutação de Transporte e Evidência de Simulacros de Failover",
                    "fr": "Cadence de Basculement du Transport et Preuves d'Exercices de Repli",
                    "de": "Transport-Schaltkadenz & operative Failover-Bohrnachweise",
                    "ja": "トランスポート切り替え頻度および実フェイルオーバー訓練エビデンス"
                }
            }
        },
        "T3.P4": {
            "T3.P4.K1": {
                "canonical_name": "Hybrid Cloud Transit Architecture: BGP Routing, Segmentation & Peering",
                "locales": {
                    "en": "Hybrid Cloud Transit Architecture: BGP Routing, Segmentation & Peering",
                    "es": "Arquitectura de Tránsito Cloud Híbrido: Enrutamiento BGP, Segmentación y Peering",
                    "pt": "Arquitetura de Trânsito em Nuvem Híbrida: Roteamento BGP, Segmentação e Peering",
                    "fr": "Architecture de Transit Cloud Hybride: Routage BGP, Segmentation et Peering",
                    "de": "Hybrid-Cloud-Transit-Architektur: BGP-Routing, Segmentierung & Peering",
                    "ja": "ハイブリッドクラウドトランジットアーキテクチャ：BGPルーティング、セグメンテーションおよびピアリング"
                }
            },
            "T3.P4.K2": {
                "canonical_name": "Cloud Interconnect Resiliency: Multi-Region Redundancy & Automated Fallback",
                "locales": {
                    "en": "Cloud Interconnect Resiliency: Multi-Region Redundancy & Automated Fallback",
                    "es": "Resiliencia de Interconexión Cloud: Redundancia Multirregional y Fallback Automatizado",
                    "pt": "Resiliência de Interconexão em Nuvem: Redundância Multirregional e Fallback",
                    "fr": "Résilience d'Interconnexion Cloud: Redondance Multirégionale et Repli Automatisé",
                    "de": "Cloud-Interconnect-Resilienz: Multiregionale Redundanz & automatisierter Fallback",
                    "ja": "クラウド相互接続レジリエンス：マルチリージョン冗長性および自動フォールバック"
                }
            },
            "T3.P4.K3": {
                "canonical_name": "Edge Service Ingress: L4/L7 Load Balancing, WAF & Public API Protection",
                "locales": {
                    "en": "Edge Service Ingress: L4/L7 Load Balancing, WAF & Public API Protection",
                    "es": "Ingreso de Servicios Edge: Balanceo L4/L7, WAF y Protección de APIs Públicas",
                    "pt": "Ingresso de Serviços Edge: Balanceamento L4/L7, WAF e Proteção de APIs Públicas",
                    "fr": "Ingress de Services Edge: Équilibrage L4/L7, WAF et Protection d'APIs Publiques",
                    "de": "Edge-Service-Ingress: L4/L7-Lastverteilung, WAF & Schutz öffentlicher APIs",
                    "ja": "エッジサービス入力：L4/L7ロードバランシング、WAFおよび公開API保護"
                }
            }
        },
        "T3.P5": {
            "T3.P5.K1": {
                "canonical_name": "Full-Stack Network Observability: SNMP Telemetry, NetFlow & Streaming Analytics",
                "locales": {
                    "en": "Full-Stack Network Observability: SNMP Telemetry, NetFlow & Streaming Analytics",
                    "es": "Observabilidad de Red Full-Stack: Telemetría SNMP, NetFlow y Flujos de Analítica",
                    "pt": "Observabilidade de Rede Completa: Telemetria SNMP, NetFlow e Fluxos de Análise",
                    "fr": "Observabilité Réseau Complète: Télémétrie SNMP, NetFlow et Analyse de Flux",
                    "de": "Full-Stack-Netzwerk-Observability: SNMP-Telemetrie, NetFlow & Streaming-Analytik",
                    "ja": "フルスタックネットワーク可観測性：SNMPテレメトリ、NetFlowおよびストリーミング分析"
                }
            },
            "T3.P5.K2": {
                "canonical_name": "Infrastructure as Code (IaC) Network Change Governance & Versioned Rollbacks",
                "locales": {
                    "en": "Infrastructure as Code (IaC) Network Change Governance & Versioned Rollbacks",
                    "es": "Gobernanza de Cambios de Red mediante IaC y Rollbacks Versionados",
                    "pt": "Governança de Mudanças de Rede via IaC e Rollbacks Versionados",
                    "fr": "Gouvernance des Modifications Réseau via IaC et Retours Arrière Versionnés",
                    "de": "Infrastructure as Code (IaC)-Netzwerk-Change-Governance & versionierte Rollbacks",
                    "ja": "Infrastructure as Code（IaC）ネットワーク変更ガバナンスおよびバージョン管理ロールバック"
                }
            },
            "T3.P5.K3": {
                "canonical_name": "Source-of-Truth Network Automation (NetDevOps & Reproducible Fleet Baselines)",
                "locales": {
                    "en": "Source-of-Truth Network Automation (NetDevOps & Reproducible Fleet Baselines)",
                    "es": "Automatización de Red basada en Single Source of Truth y Modelos NetDevOps",
                    "pt": "Automação de Rede baseada em Fonte Única da Verdade e Modelos NetDevOps",
                    "fr": "Automatisation Réseau basée sur Source Unique de Vérité et NetDevOps",
                    "de": "Source-of-Truth-Netzwerkautomatisierung (NetDevOps & reproduzierbare Flottenbaselines)",
                    "ja": "信頼できる唯一の情報源（SSOT）ネットワーク自動化（NetDevOpsと再現可能なフリートベースライン）"
                }
            },
            "T3.P5.K4": {
                "canonical_name": "Network Incident Response Lifecycle, Automated Runbooks & MTTR Governance",
                "locales": {
                    "en": "Network Incident Response Lifecycle, Automated Runbooks & MTTR Governance",
                    "es": "Ciclo de Respuesta a Incidentes de Red, Runbooks Automatizados y Gobernanza de MTTR",
                    "pt": "Ciclo de Resposta a Incidentes de Rede, Runbooks Automatizados e Governança de MTTR",
                    "fr": "Cycle de Réponse aux Incidents Réseau, Runbooks Automatisés et MTTR",
                    "de": "Netzwerk-Vorfallreaktionszyklus, automatisierte Runbooks & MTTR-Governance",
                    "ja": "ネットワークインシデント対応ライフサイクル、自動化ランブックおよびMTTRガバナンス"
                }
            }
        }
    }

    for p_id, kpis_dict in t3_kpis.items():
        if p_id in t3_pillars:
            t3_pillars[p_id]["kpis"] = kpis_dict

    TAX_PATH.write_text(json.dumps(tax_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Expanded {TAX_PATH.name} with complete T3 KPI multilingual hierarchy across all 6 locales.")


if __name__ == "__main__":
    refactor_t3()
