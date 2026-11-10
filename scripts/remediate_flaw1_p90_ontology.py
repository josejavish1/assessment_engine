"""Remediate Flaw 1: Deploy canonical, cross-domain P90 crisis ontology across all languages."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = ROOT / "engine_config" / "locales.json"

CANONICAL_P90_TRIGGERS = {
    "es": {
        "T1": "pérdida simultánea de acometidas eléctricas redundantes y degradación térmica por colapso de climatización",
        "T2": "caída crítica simultánea de nodos hiperconvergentes y bloqueo del hipervisor de virtualización",
        "T3": "partición del plano de control en el núcleo de conmutación y caída simultánea de enlaces WAN redundantes",
        "T4": "saturación masiva de I/O en cabinas de almacenamiento y corrupción de catálogos de réplica y backup",
        "T5": "fallo en la orquestación de conmutación automatizada entre sedes y desincronización de RTOs críticos",
        "T6": "compromiso de cuentas privilegiadas administrativas con movimiento lateral y despliegue de ransomware",
        "T7": "corrupción de transacciones en bases de datos centrales y saturación del flujo de resolución de incidencias",
        "T8": "pasivo imprevisto por penalización en auditoría de licenciamiento y desvío acumulado en gasto cloud",
        "T9": "bloqueo masivo en el aprovisionamiento de identidades de puesto y fallo en la distribución de parches",
        "T10": "desincronización en la telemetría SCADA/PLC y paralización física en los sistemas de pesaje y expedición",
        "DEFAULT": "fallo concurrente de componentes troncales y pérdida de redundancia operativa en el dominio"
    },
    "en": {
        "T1": "concurrent loss of redundant utility feeds and thermal degradation from cooling system failure",
        "T2": "critical concurrent failure of hyperconverged compute nodes and hypervisor management plane lockup",
        "T3": "core routing plane partition and concurrent failure of redundant enterprise WAN uplinks",
        "T4": "SAN storage fabric I/O contention and concurrent loss of immutable backup catalog metadata",
        "T5": "automated disaster recovery orchestration failure and cross-site replication desynchronization",
        "T6": "privileged credential compromise, uncontained lateral movement, and systemic ransomware execution",
        "T7": "mission-critical database transaction corruption and severe operational ticketing incident backlog",
        "T8": "contractual licensing audit penalties, vendor subscription true-up liability, and runaway cloud spend",
        "T9": "mass endpoint configuration drift, provisioning profile lockouts, and enterprise patch distribution collapse",
        "T10": "cyber-physical SCADA/PLC telemetry desynchronization and halt of automated weighbridge dispatch systems",
        "DEFAULT": "concurrent failure of core components and loss of operational redundancy across the domain"
    },
    "pt": {
        "T1": "perda simultânea de alimentação elétrica redundante e degradação térmica por falha de climatização",
        "T2": "falha crítica simultânea de nós hiperconvergentes e bloqueio do hipervisor de virtualização",
        "T3": "partição do plano de controle no núcleo de comutação e queda simultânea de enlaces WAN redundantes",
        "T4": "saturação massiva de I/O em storage arrays e corrupção de catálogos de backup imutável",
        "T5": "falha na orquestração de failover automatizado e dessincronização de RTOs críticos entre sites",
        "T6": "comprometimento de contas privilegiadas com movimentação lateral e execução de ransomware",
        "T7": "corrupção transacional em bancos de dados críticos e saturação da fila de incidentes operacionais",
        "T8": "passivo imprevisto por auditoria de licenciamento e desvio acumulado em faturamento de nuvem",
        "T9": "bloqueio massivo no provisionamento de estações de trabalho e falha na distribuição de patches",
        "T10": "dessincronização na telemetria SCADA/PLC e paralisação física dos sistemas de pesagem e expedição",
        "DEFAULT": "falha simultânea de componentes centrais e perda de redundância operacional no domínio"
    },
    "fr": {
        "T1": "perte simultanée des arrivées électriques redondantes et dégradation thermique par défaillance de climatisation",
        "T2": "défaillance critique simultanée des nœuds hyperconvergés et blocage de l'hyperviseur de virtualisation",
        "T3": "partition du plan de contrôle au cœur de réseau et panne concurrente des liaisons WAN redondantes",
        "T4": "saturation massive des E/S sur baies de stockage et corruption des catalogues de sauvegarde immuable",
        "T5": "échec de l'orchestration de basculement automatisé et désynchronisation des RTO critiques entre sites",
        "T6": "compromission des comptes à privilèges avec mouvement latéral et déploiement de ransomware",
        "T7": "corruption transactionnelle des bases de données critiques et engorgement du traitement des incidents",
        "T8": "pénalités d'audit de licences logicielles, régularisation contractuelle et dérive budgétaire cloud",
        "T9": "blocage massif du provisionnement des postes de travail et échec du déploiement des correctifs",
        "T10": "désynchronisation de la télémétrie SCADA/PLC et arrêt physique des systèmes de pesage et d'expédition",
        "DEFAULT": "défaillance simultanée des composants clés et perte de redondance opérationnelle dans le domaine"
    },
    "de": {
        "T1": "Gleichzeitiger Ausfall redundanter Stromeinspeisungen und thermische Überlastung durch Kühlungsausfall",
        "T2": "Kritischer gleichzeitiger Ausfall hyperkonvergenter Knoten und Hypervisor-Management-Sperre",
        "T3": "Core-Routing-Plane-Partitionierung und gleichzeitiger Ausfall redundanter WAN-Uplinks",
        "T4": "Massive SAN-I/O-Überlastung und Verlust unveränderlicher Backup-Katalogmetadaten",
        "T5": "Fehlschlag der automatisierten Disaster-Recovery-Orchestrierung und Replikationsdesynchronisation",
        "T6": "Kompromittierung privilegierter Konten mit lateraler Bewegung und Ransomware-Ausführung",
        "T7": "Transaktionskorruption in unternehmenskritischen Datenbanken und massiver Incident-Rückstau",
        "T8": "Vertragliche Lizenzaudit-Strafen, Nachzahlungsverbindlichkeiten und unkontrollierte Cloud-Kosten",
        "T9": "Massive Fehlkonfiguration der Endgeräte, Bereitstellungssperren und Patch-Verteilungszusammenbruch",
        "T10": "Desynchronisation der SCADA/SPS-Telemetrie und physischer Stillstand der Verladesteuerung",
        "DEFAULT": "Gleichzeitiger Ausfall von Kernkomponenten und Verlust der betrieblichen Redundanz"
    },
    "ja": {
        "T1": "冗長受電系統の同時喪失および空調障害によるサーマルシャットダウン",
        "T2": "ハイパーコンバージドノードの同時致命的障害および仮想化ハイパーバイザーのフリーズ",
        "T3": "コアルーティングプレーンの分断および冗長WANアップリンクの同時途絶",
        "T4": "SANファブリックのI/O過負荷および不変バックアップカタログメタデータの破損",
        "T5": "自動ディザスタリカバリオーケストレーションの失敗および拠点間同期障害",
        "T6": "特権アカウントの侵害、横展開の拡大および全社的ランサムウェアの実行",
        "T7": "ミッションクリティカルなデータベースのトランザクション破損および対応バックログの崩壊",
        "T8": "ソフトウェアライセンス監査のペナルティ、サブスクリプション清算およびクラウド浪費",
        "T9": "エンドポイントプロビジョニングの一斉停止およびパッチ配布システムの機能不全",
        "T10": "SCADA/PLC遠隔制御の同期不全および自動計量・出荷システムの物理的停止",
        "DEFAULT": "主要コンポーネントの同時障害およびドメイン全体の冗長性喪失"
    }
}


def update_p90_triggers() -> None:
    data = json.loads(LOCALES_PATH.read_text(encoding="utf-8"))
    for lang, triggers in CANONICAL_P90_TRIGGERS.items():
        if lang in data:
            data[lang]["tower_p90_triggers"] = triggers

    LOCALES_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("✓ Successfully updated canonical P90 crisis ontology across all 6 languages.")


if __name__ == "__main__":
    update_p90_triggers()
