"""Inject localized ch4 context templates for Gamma and Beta into locales.json across 6 languages."""

import json
from pathlib import Path

LOCALES_PATH = Path("engine_config/locales.json")
data = json.loads(LOCALES_PATH.read_text(encoding="utf-8"))

CONTEXT_GAMMA = {
    "en": {
        "cloud_native": "Cloud-Native FinOps Topology (γ={gamma:.2f}): Infrastructure liability is driven by elastic on-demand compute drift, unreserved instance commitments, and unattached multi-region cloud resources.",
        "on_prem": "On-Premise Infrastructure & Core Licensing Governance (γ={gamma:.2f}): Capital inefficiency centers on stranded hyperconverged compute capacity, core-based virtualization licensing true-up liabilities, and hardware depreciation friction.",
        "hybrid": "Hybrid Cloud Arbitrage & Edge Sizing (γ={gamma:.2f}): Financial friction stems from asymmetric workload placement, dual-plane operational overhead, and uncoordinated multi-vendor commitments."
    },
    "es": {
        "cloud_native": "Topología FinOps Cloud-Native (γ={gamma:.2f}): La exposición financiera emana del desvío de cómputo elástico bajo demanda, compromisos de instancias no optimizados y recursos huérfanos multi-región.",
        "on_prem": "Gobernanza de Infraestructura y Licenciamiento por Core (γ={gamma:.2f}): La ineficiencia se concentra en capacidad hiperconvergente ociosa, pasivos de licenciamiento de virtualización por core y amortización de hardware.",
        "hybrid": "Arbitraje de Nube Híbrida y Dimensionamiento en el Borde (γ={gamma:.2f}): La fricción emana de la duplicidad de costes operativos entre nube y centro de datos, y compromisos contractuales desalineados."
    },
    "pt": {
        "cloud_native": "Topologia FinOps Cloud-Native (γ={gamma:.2f}): A exposição financeira decorre de desvio de computação elástica sob demanda, instâncias não otimizadas e recursos órfãos em nuvem.",
        "on_prem": "Governança de Infraestrutura e Licenciamento por Núcleo (γ={gamma:.2f}): A ineficiência concentra-se em capacidade hiperconvergente ociosa, passivos de licença de virtualização por núcleo e depreciação física de hardware.",
        "hybrid": "Arbitragem de Nuvem Híbrida e Borda (γ={gamma:.2f}): A fricção financeira decorre da duplicidade de custos entre nuvem e data center local, e compromissos contratuais desalinhados."
    },
    "fr": {
        "cloud_native": "Topologie FinOps Cloud-Native (γ={gamma:.2f}): L'exposition financière provient de la dérive de calcul élastique à la demande, des instances réservées sous-optimisées et des ressources cloud orphelines.",
        "on_prem": "Gouvernance de l'Infrastructure et Licences par Cœur (γ={gamma:.2f}): L'inefficacité se concentre sur la capacité hyperconvergée inutilisée, les licences de virtualisation par cœur et l'amortissement du matériel.",
        "hybrid": "Arbitrage Cloud Hybride et Dimensionnement Edge (γ={gamma:.2f}): La friction financière provient des coûts d'exploitation hybrides et des engagements contractuels asymétriques."
    },
    "de": {
        "cloud_native": "Cloud-Native FinOps-Topologie (γ={gamma:.2f}): Die finanzielle Exposition resultiert aus elastischer On-Demand-Rechendrift, nicht optimierten Instanzverpflichtungen und verwaisten Multi-Region-Ressourcen.",
        "on_prem": "On-Premise-Infrastruktur & Core-Lizenz-Governance (γ={gamma:.2f}): Kapitalineffizienz konzentriert sich auf ungenutzte hyperkonvergente Kapazitäten, Core-basierte Virtualisierungslizenz-Nachzahlungen und Hardware-Abschreibungen.",
        "hybrid": "Hybrid-Cloud-Arbitrage & Edge-Dimensionierung (γ={gamma:.2f}): Finanzielle Reibungsverluste entstehen durch asymmetrische Workload-Platzierung, duale Betriebskosten und unkoordinierte Multi-Vendor-Verpflichtungen."
    },
    "ja": {
        "cloud_native": "クラウドネイティブFinOpsトポロジ（γ={gamma:.2f}）: インフラの財務エクスポージャーは、オンデマンドコンピュートの肥大化、最適化されていないリザーブドインスタンス、マルチリージョンの孤立リソースに起因します。",
        "on_prem": "オンプレミスインフラおよびコアライセンス統治（γ={gamma:.2f}）: 資本の非効率性は、遊休ハイパーコンバージド容量、コアベースの仮想化ライセンス追加精算負債、ハードウェア減価償却の摩擦に集中しています。",
        "hybrid": "ハイブリッドクラウドアビトラージおよびエッジサイジング（γ={gamma:.2f}）: 財務摩擦は、ワークロード配置の非対称性、オンプレミスとクラウドの二重運用コスト、調整されていないマルチベンダー契約から生じます。"
    }
}

CONTEXT_BETA = {
    "en": {
        "clinical": "Acute Clinical Vulnerability (β={beta:.2f}): Real-time patient telemetry and ICU monitoring operate with near-zero buffering tolerance, translating system outages directly into immediate clinical care diversion.",
        "synchronous": "Synchronous Clearing Sensitivity (β={beta:.2f}): Payment rails and core ledger transactions operate with zero downtime buffer, triggering immediate settlement failure penalties and liquidity SLA breaches.",
        "high_tempo": "High-Tempo Transactional Exposure (β={beta:.2f}): Digital interaction points translate system latency directly into immediate commercial revenue abandonment.",
        "buffered_silo": "Physical Silo & Inventory Buffering (β={beta:.2f}): Operational dispatch and material production are partially shielded by physical stockpile buffers and catch-up shifts, preventing linear revenue loss during short outages."
    },
    "es": {
        "clinical": "Vulnerabilidad Clínica Aguda (β={beta:.2f}): La telemetría de pacientes y la UCI operan con tolerancia de amortiguación casi nula, trasladando la parada de sistemas de inmediato al triaje de urgencias.",
        "synchronous": "Sensibilidad de Compensación Síncrona (β={beta:.2f}): Los rieles de pago y la liquidación transaccional carecen de amortiguación, provocando el rechazo instantáneo de operaciones y penalizaciones de SLA.",
        "high_tempo": "Exposición Comercial de Alto Ritmo (β={beta:.2f}): Los puntos de venta digitales trasladan la latencia técnica de forma inmediata al abandono transaccional.",
        "buffered_silo": "Amortiguación Física por Silos y Stock (β={beta:.2f}): La expedición y producción en planta están parcialmente protegidas por reservas en silos y reprogramación de turnos, evitando pérdidas lineales en paradas cortas."
    },
    "pt": {
        "clinical": "Vulnerabilidade Clínica Aguda (β={beta:.2f}): A telemetria de pacientes e UTI opera com tolerância de amortecimento quase nula, transferindo a parada imediatamente para o atendimento clínico.",
        "synchronous": "Sensibilidade de Compensação Síncrona (β={beta:.2f}): Os trilhos de pagamento operam sem margem de amortecimento, disparando rejeição instantânea de transações e multas regulatórias.",
        "high_tempo": "Exposição Comercial de Alto Ritmo (β={beta:.2f}): Os pontos de venda digitais transferem a latência técnica diretamente para o abandono de transações.",
        "buffered_silo": "Amortecimento Físico por Silos e Estoque (β={beta:.2f}): A expedição fabril é parcialmente blindada por estoques intermediários e turnos compensatórios, atenuando a perda financeira direta em paradas curtas."
    },
    "fr": {
        "clinical": "Vulnérabilité Clinique Aiguë (β={beta:.2f}): La télémétrie des soins intensifs fonctionne avec une tolérance tampon quasi nulle, répercutant l'arrêt directement sur la prise en charge médicale.",
        "synchronous": "Sensibilité de Compensation Synchrone (β={beta:.2f}): Les flux de paiement fonctionnent sans tampon, déclenchant le rejet immédiat des transactions et des pénalités de SLA.",
        "high_tempo": "Exposition Commerciale à Haut Rythme (β={beta:.2f}): La latence technique se traduit directement par l'abandon immédiat des transactions commerciales.",
        "buffered_silo": "Tampon Physique par Silos et Stocks (β={beta:.2f}): La production et l'expédition sont partiellement protégées par des stocks intermédiaires en silos, évitant une perte financière linéaire lors des pannes courtes."
    },
    "de": {
        "clinical": "Akute klinische Verwundbarkeit (β={beta:.2f}): Echtzeit-Patiententelemetrie und Intensivüberwachung tolerieren nahezu keine Pufferung; Ausfälle führen direkt zur Unterbrechung der klinischen Versorgung.",
        "synchronous": "Synchrone Verrechnungssensitivität (β={beta:.2f}): Zahlungsströme und Kernbuchhaltungstransaktionen arbeiten ohne Puffer; Ausfälle lösen sofortige Abwicklungsstrafen und Liquiditäts-SLA-Verletzungen aus.",
        "high_tempo": "Hochfrequente Transaktionsexposition (β={beta:.2f}): Digitale Interaktionspunkte führen Latenzen unmittelbar zum Abbruch kommerzieller Transaktionen.",
        "buffered_silo": "Physische Silo- & Lagerpufferung (β={beta:.2f}): Betrieblicher Versand und Produktion sind teilweise durch physische Puffer und Nachholschichten geschützt, was lineare Umsatzverluste bei kurzen Ausfällen verhindert."
    },
    "ja": {
        "clinical": "急性の臨床的脆弱性（β={beta:.2f}）: リアルタイムの患者生体情報および集中治療室（ICU）監視はバッファ許容度がほぼゼロであり、システム停止は即座に診療・トリアージの遅延に直結します。",
        "synchronous": "同期決済の即時感応度（β={beta:.2f}）: 決済レールおよびコア台帳トランザクションは停止バッファを持たず、即時の決済不能ペナルティおよび流動性SLA違反を引き起こします。",
        "high_tempo": "高頻度トランザクションエクスポージャー（β={beta:.2f}）: デジタル接点でのシステム遅延は、顧客の購買放棄および即時の売上損失に直結します。",
        "buffered_silo": "物理的サイロおよび在庫バッファ（β={beta:.2f}）: プラントの出荷および製造は中間在庫バッファや振替シフトによって部分的に保護され、短期の障害における直線的な収益損失を防ぎます。"
    }
}

for lang in data:
    if lang in CONTEXT_GAMMA:
        data[lang]["annex_ch4_context_gamma"] = CONTEXT_GAMMA[lang]
    if lang in CONTEXT_BETA:
        data[lang]["annex_ch4_context_beta"] = CONTEXT_BETA[lang]

LOCALES_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("✓ Successfully injected localized Gamma and Beta context templates across all 6 languages.")
