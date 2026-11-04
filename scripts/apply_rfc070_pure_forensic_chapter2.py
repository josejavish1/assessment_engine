#!/usr/bin/env python3
"""Apply RFC 070: Pure Forensic Chapter 2 dictionary keys across all 6 locales."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = REPO_ROOT / "engine_config" / "locales.json"

RFC_070_KEYS = {
    "tomo_ch2_intro": {
        "es": "La evaluación de madurez tecnológica determina la capacidad real de la arquitectura actual para sostener la continuidad operativa, escalar procesos industriales y mitigar riesgos de interrupción. El modelo analítico audita las 10 áreas tecnológicas bajo la escala estándar CMMI (Capability Maturity Model Integration) de 1,00 a 5,00, basándose exclusivamente en evidencias empíricas recolectadas sobre la infraestructura, aplicaciones y procesos operativos de la organización.",
        "en": "The technology maturity assessment determines the actual capacity of the current architecture to sustain operational continuity, scale industrial processes, and mitigate disruption risks. The analytical model audits the 10 technology towers under the standard CMMI (Capability Maturity Model Integration) scale from 1.00 to 5.00, based exclusively on empirical evidence collected across the organization's infrastructure, applications, and operational processes.",
        "pt": "A avaliação de maturidade tecnológica determina a capacidade real da arquitetura atual para sustentar a continuidade operacional, escalar processos industriais e mitigar riscos de interrupção. O modelo analítico audita as 10 torres tecnológicas sob a escala padrão CMMI (Capability Maturity Model Integration) de 1,00 a 5,00, baseando-se exclusivamente em evidências empíricas coletadas na infraestrutura, aplicações e processos operacionais da organização.",
        "fr": "L'évaluation de la maturité technologique détermine la capacité réelle de l'architecture actuelle à maintenir la continuité opérationnelle, à faire évoluer les processus industriels et à atténuer les risques d'interruption. Le modèle analytique audite les 10 tours technologiques selon l'échelle standard CMMI (Capability Maturity Model Integration) de 1,00 à 5,00, en se basant exclusivement sur des preuves empiriques collectées sur l'infrastructure, les applications et les processus opérationnels de l'organisation.",
        "de": "Die Bewertung des technologischen Reifegrads bestimmt die tatsächliche Fähigkeit der aktuellen Architektur, die Betriebskontinuität aufrechtzuerhalten, industrielle Prozesse zu skalieren und Unterbrechungsrisiken zu mindern. Das Analysemodell prüft die 10 Technologietürme nach der CMMI-Standardskala (Capability Maturity Model Integration) von 1,00 bis 5,00 und stützt sich dabei ausschließlich auf empirische Nachweise aus der Infrastruktur, den Anwendungen und den Betriebsprozessen der Organisation.",
        "ja": "技術成熟度評価は、現在のアーキテクチャが業務継続性を維持し、産業プロセスを拡張し、中断リスクを軽減するための実際の能力を判定します。分析モデルは、組織のインフラストラクチャ、アプリケーション、および運用プロセス全体で収集された実証的証拠のみに基づき、1.00から5.00までの標準CMMI（能力成熟度モデル統合）スケールで10の技術タワーを監査します。",
    },
    "tomo_ch2_summary_p1": {
        "es": "El índice de madurez global consolidado se sitúa en {overall_maturity} sobre 5,00, posicionando la plataforma tecnológica en el Nivel 2 (Repetible). Este resultado refleja una arquitectura de dos velocidades claramente diferenciadas. Por un lado, las capacidades de base corporativa —Almacenamiento y Backup (3,30) y Puesto de Trabajo Digital (3,10)— han alcanzado el Nivel 3 (Definido), operando bajo estándares documentados, arquitecturas centralizadas y niveles de servicio predecibles.",
        "en": "The consolidated global maturity index stands at {overall_maturity} out of 5.00, positioning the technology platform at Level 2 (Repeatable). This result reflects a clearly differentiated two-speed architecture. On one hand, foundational corporate capabilities—Storage & Backup (3.30) and Digital Workplace (3.10)—have reached Level 3 (Defined), operating under documented standards, centralized architectures, and predictable service levels.",
        "pt": "O índice global consolidado de maturidade situa-se em {overall_maturity} sobre 5,00, posicionando a plataforma tecnológica no Nível 2 (Repetível). Este resultado reflete uma arquitetura de duas velocidades claramente diferenciadas. Por um lado, as capacidades de base corporativa — Armazenamento e Backup (3,30) e Posto de Trabalho Digital (3,10) — atingiram o Nível 3 (Definido), operando sob padrões documentados, arquiteturas centralizadas e níveis de serviço previsíveis.",
        "fr": "L'indice global consolidé de maturité s'établit à {overall_maturity} sur 5,00, positionnant la plateforme technologique au Niveau 2 (Répétable). Ce résultat reflète une architecture à deux vitesses clairement différenciées. D'une part, les capacités de base de l'entreprise — Stockage et Sauvegarde (3,30) et Poste de Travail Numérique (3,10) — ont atteint le Niveau 3 (Défini), fonctionnant selon des normes documentées, des architectures centralisées et des niveaux de service prévisibles.",
        "de": "Der konsolidierte globale Reifegradindex liegt bei {overall_maturity} von 5,00 und positioniert die Technologieplattform auf Stufe 2 (Wiederholbar). Dieses Ergebnis spiegelt eine klar differenzierte Architektur der zwei Geschwindigkeiten wider. Einerseits haben grundlegende Unternehmensfähigkeiten – Speicher & Backup (3,30) und Digitaler Arbeitsplatz (3,10) – Stufe 3 (Definiert) erreicht und arbeiten nach dokumentierten Standards, zentralisierten Architekturen und vorhersagbaren Service-Levels.",
        "ja": "統合されたグローバル成熟度指数は5.00満点中{overall_maturity}であり、技術プラットフォームはレベル2（反復可能）に位置しています。この結果は、明確に分化した2つの速度を持つアーキテクチャを反映しています。一方では、企業の基盤機能であるストレージとバックアップ（3.30）およびデジタルワークプレイス（3.10）がレベル3（定義済み）に到達しており、文書化された標準、集中型アーキテクチャ、および予測可能なサービスレベルの下で運用されています。",
    },
    "tomo_ch2_summary_p2": {
        "es": "Por otro lado, los dominios que sustentan la ejecución industrial y transaccional —Continuidad Operativa (2,10), Aplicaciones de Negocio (2,40) y Sistemas de Expedición (2,40)— permanecen en la franja reactiva del Nivel 2. En estas áreas, la estabilidad operativa depende del esfuerzo reactivo del personal técnico, configuraciones locales sin redundancia automatizada e integraciones punto a punto. Esta asimetría estructural entre el entorno corporativo centralizado y las plantas industriales constituye el vector principal de exposición operativa y financiera analizado en el Capítulo 3.",
        "en": "On the other hand, the domains sustaining industrial and transactional execution—Operational Continuity (2.10), Business Applications (2.40), and Dispatch Systems (2.40)—remain in the reactive band of Level 2. In these areas, operational stability relies on reactive technical staff heroics, local configurations lacking automated redundancy, and point-to-point integrations. This structural asymmetry between the centralized corporate environment and industrial plants constitutes the primary vector of operational and financial exposure analyzed in Chapter 3.",
        "pt": "Por outro lado, os domínios que sustentam a execução industrial e transacional — Continuidade Operacional (2,10), Aplicações de Negócio (2,40) e Sistemas de Expedição (2,40) — permanecem na faixa reativa do Nível 2. Nestas áreas, a estabilidade operacional depende do esforço reativo da equipe técnica, configurações locais sem redundância automatizada e integrações ponto a ponto. Esta assimetria estrutural entre o ambiente corporativo e a planta industrial constitui o vetor principal de exposição operacional e financeira analisado no Capítulo 3.",
        "fr": "D'autre part, les domaines soutenant l'exécution industrielle et transactionnelle — Continuité Opérationnelle (2,10), Applications Métier (2,40) et Systèmes d'Expédition (2,40) — restent ancrés dans la tranche réactive du Niveau 2. Dans ces domaines, la stabilité opérationnelle repose sur l'effort réactif des équipes techniques, des configurations locales sans redondance automatisée et des intégrations point à point. Cette asymétrie structurelle constitue le vecteur principal d'exposition opérationnelle et financière analysé au Chapitre 3.",
        "de": "Andererseits bleiben die Domänen, die die industrielle und transaktionale Ausführung tragen – Betriebskontinuität (2,10), Geschäftsanwendungen (2,40) sowie Versandsysteme (2,40) – im reaktiven Bereich der Stufe 2 verankert. In diesen Bereichen beruht die Betriebsstabilität auf dem reaktiven Einsatz des Personals, lokalen Konfigurationen ohne automatisierte Redundanz und Punkt-zu-Punkt-Integrationen. Diese strukturelle Asymmetrie bildet den Hauptvektor des operativen Risikos, das in Kapitel 3 analysiert wird.",
        "ja": "他方、産業およびトランザクションの実行を支える領域—事業継続性（2.10）、業務アプリケーション（2.40）、および出荷システム（2.40）—は、レベル2の事後対応的な領域に留まっています。これらの領域では、運用の安定性は技術スタッフの事後対応的な尽力、自動冗長性を欠いたローカル構成、およびポイントツーポイントの統合に依存しています。この構造的な非対称性は、第3章で分析される運用上および財務上の主要なリスク要因となっています。",
    },
    "tomo_ch2_tbl_col_code": {
        "es": "Código",
        "en": "Code",
        "pt": "Código",
        "fr": "Code",
        "de": "Code",
        "ja": "コード",
    },
    "tomo_ch2_tbl_col_tower": {
        "es": "Área Tecnológica Evaluada",
        "en": "Evaluated Technology Domain",
        "pt": "Área Tecnológica Avaliada",
        "fr": "Domaine Technologique Évalué",
        "de": "Bewerteter Technologiebereich",
        "ja": "評価対象技術領域",
    },
    "tomo_ch2_tbl_col_asis": {
        "es": "Madurez AS-IS",
        "en": "AS-IS Maturity",
        "pt": "Maturidade AS-IS",
        "fr": "Maturité AS-IS",
        "de": "AS-IS-Reifegrad",
        "ja": "AS-IS成熟度",
    },
    "tomo_ch2_tbl_col_cmmi": {
        "es": "Nivel CMMI",
        "en": "CMMI Tier",
        "pt": "Nível CMMI",
        "fr": "Niveau CMMI",
        "de": "CMMI-Stufe",
        "ja": "CMMIレベル",
    },
    "tomo_ch2_tbl_col_status": {
        "es": "Estado Operativo",
        "en": "Operational Posture",
        "pt": "Estado Operacional",
        "fr": "Posture Opérationnelle",
        "de": "Betriebszustand",
        "ja": "運用状態",
    },
    "tomo_ch2_tbl_col_driver": {
        "es": "Factor Focal de Diagnóstico",
        "en": "Primary Diagnostic Driver",
        "pt": "Fator Focal de Diagnóstico",
        "fr": "Facteur Clé de Diagnostic",
        "de": "Primärer Diagnosefaktor",
        "ja": "主要診断要因",
    },
    "tomo_status_standardized": {
        "es": "Operación Estandarizada",
        "en": "Standardized Operation",
        "pt": "Operação Padronizada",
        "fr": "Opération Standardisée",
        "de": "Standardisierter Betrieb",
        "ja": "標準化運用",
    },
    "tomo_status_moderate_debt": {
        "es": "Deuda Técnica Moderada",
        "en": "Moderate Technical Debt",
        "pt": "Dívida Técnica Moderada",
        "fr": "Dette Technique Modérée",
        "de": "Moderate Technische Schuld",
        "ja": "中程度の技術的負債",
    },
    "tomo_status_high_risk": {
        "es": "Riesgo Operativo Alto",
        "en": "High Operational Risk",
        "pt": "Risco Operacional Alto",
        "fr": "Risque Opérationnel Élevé",
        "de": "Hohes Betriebsrisiko",
        "ja": "高運用リスク",
    },
    "tomo_cmmi_lvl3": {
        "es": "Nivel 3 (Definido)",
        "en": "Level 3 (Defined)",
        "pt": "Nível 3 (Definido)",
        "fr": "Niveau 3 (Défini)",
        "de": "Stufe 3 (Definiert)",
        "ja": "レベル3（定義済み）",
    },
    "tomo_cmmi_lvl2": {
        "es": "Nivel 2 (Repetible)",
        "en": "Level 2 (Repeatable)",
        "pt": "Nível 2 (Repetível)",
        "fr": "Niveau 2 (Répétable)",
        "de": "Stufe 2 (Wiederholbar)",
        "ja": "レベル2（反復可能）",
    },
    "tomo_cmmi_lvl2_fragile": {
        "es": "Nivel 2 (Repetible)",
        "en": "Level 2 (Repeatable)",
        "pt": "Nível 2 (Repetível)",
        "fr": "Niveau 2 (Répétable)",
        "de": "Stufe 2 (Wiederholbar)",
        "ja": "レベル2（反復可能）",
    },
    "tomo_fig_radar_caption": {
        "es": "Figura 2.1: Radiografía Polar CMMI — Perfil de Madurez de Capacidades AS-IS sobre las 10 Áreas Tecnológicas.",
        "en": "Figure 2.1: CMMI Polar Radiography — AS-IS Capability Maturity Profile across the 10 Technology Domains.",
        "pt": "Figura 2.1: Radiografia Polar CMMI — Perfil de Maturidade de Capacidades AS-IS nas 10 Áreas Tecnológicas.",
        "fr": "Figure 2.1 : Radiographie Polaire CMMI — Profil de Maturité des Capacités AS-IS sur les 10 Domaines Technologiques.",
        "de": "Abbildung 2.1: CMMI-Polardiagramm — AS-IS-Fähigkeitenreifeprofil über die 10 Technologiebereiche.",
        "ja": "図2.1：CMMI極座標レーダーチャート — 10の技術領域における現状能力成熟度（AS-IS）プロファイル。",
    },
    "tomo_ch2_driver_T1": {
        "es": "Centros de datos con robustez mecánica consolidada, penalizados por segmentación aerotérmica y telemetría de potencia básica.",
        "en": "Data centers with solid mechanical robustness, constrained by thermal containment and basic power telemetry.",
        "pt": "Data centers com robustez mecânica consolidada, penalizados por confinamento térmico e telemetria de energia básica.",
        "fr": "Centres de données avec robustesse mécanique solide, limités par le confinement thermique et la télémétrie électrique basique.",
        "de": "Rechenzentren mit solider mechanischer Robustheit, eingeschränkt durch thermische Einhausung und grundlegende Leistungstelemetrie.",
        "ja": "堅牢な設備を備えたデータセンターだが、熱的分離と基本的な電力テレメトリに制約が存在。",
    },
    "tomo_ch2_driver_T2": {
        "es": "Clústeres hiperconvergentes centrales estables, pero con elevada saturación de memoria (>90%) y renovación pendiente en mayo 2027.",
        "en": "Stable core hyperconverged clusters, constrained by high memory pressure (>90%) and upcoming renewal in May 2027.",
        "pt": "Clusters hiperconvergentes estáveis, mas com alta saturação de memória (>90%) e renovação pendente em maio de 2027.",
        "fr": "Clusters hyperconvergés centraux stables, mais forte saturation mémoire (>90%) et renouvellement prévu en mai 2027.",
        "de": "Stabile zentrale hyperkonvergente Cluster, jedoch hohe Speicherauslastung (>90%) und anstehende Erneuerung im Mai 2027.",
        "ja": "安定した中央ハイパーコンバージドクラスタだが、高いメモリ使用率（>90%）と2027年5月の更新期限が課題。",
    },
    "tomo_ch2_driver_T3": {
        "es": "Topología WAN/SD-WAN operativa, con necesidad de blindar la segmentación IT/OT y garantizar doble acometida en canteras clave.",
        "en": "Operational WAN/SD-WAN topology, with a need to reinforce IT/OT segmentation and dual carriers at key quarries.",
        "pt": "Topologia WAN/SD-WAN operacional, necessitando reforçar segmentação IT/OT e dupla conectividade em pedreiras críticas.",
        "fr": "Topologie WAN/SD-WAN opérationnelle, avec nécessité de renforcer la segmentation IT/OT et la double adduction sur carrières clés.",
        "de": "Betriebsbereite WAN/SD-WAN-Topologie, mit Bedarf an verstärkter IT/OT-Segmentierung und redundanten Anbindungen in Schlüsselwerken.",
        "ja": "稼働中のWAN/SD-WANトポロジだが、IT/OTセグメンテーションの強化と主要採石場での二重回線化が必要。",
    },
    "tomo_ch2_driver_T4": {
        "es": "Arquitectura de almacenamiento y backup centralizada y predecible, con políticas formales de retención y replicación local.",
        "en": "Centralized and predictable storage and backup architecture, with formal retention policies and local replication.",
        "pt": "Arquitetura de armazenamento e backup centralizada e previsível, com políticas formais de retenção e replicação local.",
        "fr": "Architecture de stockage et sauvegarde centralisée et prévisible, avec politiques formelles de rétention et réplication.",
        "de": "Zentralisierte und vorhersehbare Speicher- und Backup-Architektur mit formalen Aufbewahrungsrichtlinien und lokaler Replikation.",
        "ja": "正式な保持ポリシーとローカルレプリケーションを備えた、中央集権的で予測可能なストレージおよびバックアップ構成。",
    },
    "tomo_ch2_driver_T5": {
        "es": "Procedimientos DRP no formalizados en entornos fabriles, dependencia de intervenciones manuales y tiempos de recuperación prolongados.",
        "en": "Unformalized DRP procedures in plant environments, high reliance on manual interventions, and prolonged recovery times.",
        "pt": "Procedimentos DRP não formalizados nas plantas, dependência de intervenções manuais e tempos de recuperação prolongados.",
        "fr": "Procédures PRA non formalisées en usine, forte dépendance aux interventions manuelles et délais de reprise prolongés.",
        "de": "Nicht formalisierte DRP-Verfahren in Werksumgebungen, hohe Abhängigkeit von manuellen Eingriffen und lange Wiederanlaufzeiten.",
        "ja": "工場環境における非公式なDRP手順、手動介入への高い依存、および長期化する復旧時間。",
    },
    "tomo_ch2_driver_T6": {
        "es": "Controles de seguridad perimetral activos, con necesidad de elevar la visibilidad en redes OT y desplegar gestión de identidades PAM.",
        "en": "Active perimeter security controls, requiring enhanced visibility across OT networks and PAM identity deployment.",
        "pt": "Controles de segurança perimetral ativos, necessitando ampliar visibilidade em redes OT e implantar PAM.",
        "fr": "Contrôles de sécurité périmétrique actifs, nécessitant une visibilité accrue sur les réseaux OT et le déploiement du PAM.",
        "de": "Aktive Perimetersicherheitskontrollen, mit Bedarf an verbesserter OT-Netzwerksichtbarkeit und PAM-Einführung.",
        "ja": "有効な境界セキュリティ制御だが、OTネットワークの可視性向上と特権アクセス管理（PAM）の導入が必要。",
    },
    "tomo_ch2_driver_T7": {
        "es": "Gestión de bases de datos transaccionales estable, pendiente de estandarizar la automatización de parches y gobierno ITSM.",
        "en": "Stable transactional database operations, pending standardization of automated patching and ITSM governance.",
        "pt": "Gestão de bancos de dados transacionais estável, pendente padronizar automação de patches e governança ITSM.",
        "fr": "Gestion stable des bases de données transactionnelles, en attente de standardisation des correctifs et gouvernance ITSM.",
        "de": "Stabiler Transaktionsdatenbankbetrieb, ausstehende Standardisierung von automatisiertem Patching und ITSM-Governance.",
        "ja": "安定したトランザクションデータベース運用だが、パッチ適用の自動化とITSMガバナンスの標準化が未完了。",
    },
    "tomo_ch2_driver_T8": {
        "es": "Ecosistema SAP/ERP consolidado en finanzas, penalizado por integraciones satélite manuales y contratos de licencias fragmentados.",
        "en": "Consolidated core SAP/ERP in finance, constrained by manual satellite integrations and fragmented licensing agreements.",
        "pt": "Ecossistema SAP/ERP consolidado nas finanças, penalizado por integrações satélite manuais e contratos de licença fragmentados.",
        "fr": "Écosystème SAP/ERP consolidé en finance, pénalisé par des intégrations satellites manuelles et contrats fragmentés.",
        "de": "Konsolidiertes SAP/ERP-Ökosystem im Finanzwesen, beeinträchtigt durch manuelle Integrationen und fragmentierte Verträge.",
        "ja": "財務領域で統合されたSAP/ERPエコシステムだが、手動の連携処理と分断されたライセンス契約が課題。",
    },
    "tomo_ch2_driver_T9": {
        "es": "Entorno de productividad y puesto digital estandarizado bajo Microsoft 365, con gobernanza madura en capa ofimática.",
        "en": "Standardized digital workplace and productivity environment under Microsoft 365, with mature governance across office fleet.",
        "pt": "Ambiente de produtividade e posto digital padronizado no Microsoft 365, com governança madura na camada de escritório.",
        "fr": "Environnement bureautique et poste de travail standardisé sous Microsoft 365, avec une gouvernance mature.",
        "de": "Standardisierte Produktivitäts- und Arbeitsplatzumgebung unter Microsoft 365 mit ausgereifter Governance im Bürobereich.",
        "ja": "Microsoft 365の下で標準化されたデジタルワークプレイス環境であり、オフィス環境全体で成熟したガバナンスを確立。",
    },
    "tomo_ch2_driver_T10": {
        "es": "Sistemas de pesaje y despacho acoplados a infraestructura local de planta, sin conmutación por error automatizada en caso de caída.",
        "en": "Weighbridge and dispatch systems tied to local plant infrastructure, lacking automated failover in outage scenarios.",
        "pt": "Sistemas de pesagem e despacho vinculados à infraestrutura local, sem failover automatizado em cenários de parada.",
        "fr": "Systèmes de pesage et expédition liés à l'infrastructure locale, sans basculement automatique en cas de panne.",
        "de": "Waagen- und Versandsysteme an lokale Werkshardware gebunden, ohne automatisiertes Failover bei Ausfällen.",
        "ja": "工場のローカルインフラに依存した計量・出荷システムであり、障害発生時の自動フェイルオーバーが欠如。",
    },
    "tomo_ch2_driver_summary": {
        "es": "Asimetría estructural entre servicios corporativos estandarizados (Nivel 3) y operaciones críticas de planta expuestas (Nivel 2).",
        "en": "Structural asymmetry between standardized corporate services (Level 3) and exposed plant operations (Level 2).",
        "pt": "Assimetria estrutural entre serviços corporativos padronizados (Nível 3) e operações de planta expostas (Nível 2).",
        "fr": "Asymétrie structurelle entre services corporatifs standardisés (Niveau 3) et opérations d'usine exposées (Niveau 2).",
        "de": "Strukturelle Asymmetrie zwischen standardisierten IT-Diensten (Stufe 3) und exponierten Werksoperationen (Stufe 2).",
        "ja": "標準化されたコーポレートITサービス（レベル3）と脆弱な工場現場運用（レベル2）の間の構造的非対称性。",
    },
}


def main() -> None:
    with open(LOCALES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for key, trans_dict in RFC_070_KEYS.items():
        for loc, val in trans_dict.items():
            if loc in data:
                data[loc][key] = val

    with open(LOCALES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Successfully applied RFC 070 pure forensic keys across all 6 locales!")


if __name__ == "__main__":
    main()
