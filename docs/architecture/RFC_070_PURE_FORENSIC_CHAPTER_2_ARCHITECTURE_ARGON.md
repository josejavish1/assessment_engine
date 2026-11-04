### 1. Forensic Redesign of Table 2 (Capability Maturity Matrix)

To ensure audit-proof integrity, all synthetic external sector benchmarks (`Mediana P50`, `Gap vs. Sector`) are purged. Table 2 is restructured into a 6-column forensic matrix that maps each technology tower's empirical score (`1.00–5.00`) directly to its **CMMI Maturity Tier**, **Operational Posture**, and **Primary Diagnostic Driver**.

#### Deterministic Tier Classification Logic (Engine Rule)
*   **Score $\ge 3.00$:**
    *   `cmmi_tier`: **Level 3 — Defined** (`tomo_cmmi_lvl3`)
    *   `operational_status`: **Standardized Operation** (`tomo_status_standardized`)
*   **$2.45 \le$ Score $< 3.00$:**
    *   `cmmi_tier`: **Level 2 — Repeatable** (`tomo_cmmi_lvl2`)
    *   `operational_status`: **Moderate Technical Debt** (`tomo_status_moderate_debt`)
*   **Score $< 2.45$:**
    *   `cmmi_tier`: **Level 2 — Repeatable (Fragile)** (`tomo_cmmi_lvl2_fragile`)
    *   `operational_status`: **High Operational Risk** (`tomo_status_high_risk`)

#### Table 2 Structure & Empirical Mapping (`es` Reference)

| Código | Área Tecnológica Evaluada | Madurez AS-IS | Nivel CMMI | Estado Operativo | Factor Focal de Diagnóstico |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **T1** | Comunicaciones y Red | **2.50** | Nivel 2 — Repetible | Deuda Técnica Moderada | Topología WAN estable, pero segmentación IT/OT incompleta y enlaces críticos sin redundancia física de doble operador en plantas. |
| **T2** | Cómputo y Virtualización | **2.60** | Nivel 2 — Repetible | Deuda Técnica Moderada | Clústeres hiperconvergentes consolidados a nivel central, penalizados por infraestructura local envejecida en plantas industriales. |
| **T3** | Almacenamiento y Backup | **3.30** | Nivel 3 — Definido | Operación Estandarizada | Arquitectura de respaldo centralizada con políticas definidas, pendiente de extender copias inmutables verificadas a sedes remotas. |
| **T4** | Puesto de Trabajo Digital | **3.10** | Nivel 3 — Definido | Operación Estandarizada | Ecosistema colaborativo estandarizado y gestión de identidades madura, con brechas de control en terminales operativos de planta. |
| **T5** | Aplicaciones Core | **2.40** | Nivel 2 — Repetible (Frágil) | Riesgo Operativo Alto | Ecosistema ERP fragmentado con integraciones punto a punto no documentadas y alta dependencia de soporte correctivo manual. |
| **T6** | Ciberseguridad | **2.40** | Nivel 2 — Repetible (Frágil) | Riesgo Operativo Alto | Controles perimetrales activos en capa corporativa, pero visibilidad limitada en redes OT y ausencia de respuesta automatizada (SOAR). |
| **T7** | Gobierno y Gestión IT | **2.40** | Nivel 2 — Repetible (Frágil) | Riesgo Operativo Alto | Procesos ITSM reactivos, ausencia de CMDB federada y catálogo de servicios sin acuerdos de nivel de servicio (SLA) auditables. |
| **T8** | Continuidad en Planta | **2.10** | Nivel 2 — Repetible (Frágil) | Riesgo Operativo Alto | Ausencia de planes DRP probados en entornos industriales, puntos únicos de fallo en servidores locales y alta dependencia de personal clave. |
| **T9** | Integración de Datos | **2.30** | Nivel 2 — Repetible (Frágil) | Riesgo Operativo Alto | Extracción de datos mediante procesos batch frágiles, sin capa intermedia de gobierno ni linaje de datos entre sistemas de planta y ERP. |
| **T10** | Básculas y Expedición | **2.40** | Nivel 2 — Repetible (Frágil) | Riesgo Operativo Alto | Sistemas de pesaje y despacho acoplados a hardware local sin contingencia automatizada, generando riesgo directo de bloqueo logístico. |
| **—** | ** Media Consolidada** | **2.55** | **Nivel 2 — Repetible** | **Deuda Técnica Moderada** | **Asimetría estructural entre servicios corporativos estandarizados (Nivel 3) y operaciones críticas de planta expuestas (Nivel 2).** |

---

### 2. Multi-Locale Dictionary Specification (`locales.json`)

The following dictionary keys replace all external benchmark strings and provide enriched executive prose across all 6 supported locales (`es`, `en`, `pt`, `fr`, `de`, `ja`).

```json
{
  "tomo_ch2_intro": {
    "es": "La evaluación de madurez tecnológica determina la capacidad real de la arquitectura actual para sostener la continuidad operativa, escalar procesos industriales y mitigar riesgos de interrupción. El modelo analítico audita las 10 torres tecnológicas bajo la escala estándar CMMI (Capability Maturity Model Integration) de 1.00 a 5.00, basándose exclusivamente en evidencias empíricas recolectadas sobre la infraestructura, aplicaciones y procesos operativos de la organización.",
    "en": "The technology maturity assessment determines the actual capacity of the current architecture to sustain operational continuity, scale industrial processes, and mitigate disruption risks. The analytical model audits the 10 technology towers under the standard CMMI (Capability Maturity Model Integration) scale from 1.00 to 5.00, based exclusively on empirical evidence collected across the organization's infrastructure, applications, and operational processes.",
    "pt": "A avaliação de maturidade tecnológica determina a capacidade real da arquitetura atual para sustentar a continuidade operacional, escalar processos industriais e mitigar riscos de interrupção. O modelo analítico audita as 10 torres tecnológicas sob a escala padrão CMMI (Capability Maturity Model Integration) de 1.00 a 5.00, baseando-se exclusivamente em evidências empíricas coletadas na infraestrutura, aplicações e processos operacionais da organização.",
    "fr": "L'évaluation de la maturité technologique détermine la capacité réelle de l'architecture actuelle à maintenir la continuité opérationnelle, à faire évoluer les processus industriels et à atténuer les risques d'interruption. Le modèle analytique audite les 10 tours technologiques selon l'échelle standard CMMI (Capability Maturity Model Integration) de 1,00 à 5,00, en se basant exclusivement sur des preuves empiriques collectées sur l'infrastructure, les applications et les processus opérationnels de l'organisation.",
    "de": "Die Bewertung des technologischen Reifegrads bestimmt die tatsächliche Fähigkeit der aktuellen Architektur, die Betriebskontinuität aufrechtzuerhalten, industrielle Prozesse zu skalieren und Unterbrechungsrisiken zu mindern. Das Analysemodell prüft die 10 Technologietürme nach der CMMI-Standardskala (Capability Maturity Model Integration) von 1,00 bis 5,00 und stützt sich dabei ausschließlich auf empirische Nachweise aus der Infrastruktur, den Anwendungen und den Betriebsprozessen der Organisation.",
    "ja": "技術成熟度評価は、現在のアーキテクチャが業務継続性を維持し、産業プロセスを拡張し、中断リスクを軽減するための実際の能力を判定します。分析モデルは、組織のインフラストラクチャ、アプリケーション、および運用プロセス全体で収集された実証的証拠のみに基づき、1.00から5.00までの標準CMMI（能力成熟度モデル統合）スケールで10の技術タワーを監査します。"
  },
  "tomo_ch2_summary_p1": {
    "es": "El índice de madurez global consolidado se sitúa en {overall_maturity} sobre 5.00, posicionando la plataforma tecnológica en el Nivel 2 (Repetible). Este resultado refleja una arquitectura de dos velocidades claramente diferenciadas. Por un lado, las capacidades de base corporativa —Almacenamiento y Backup (3.30) y Puesto de Trabajo Digital (3.10)— han alcanzado el Nivel 3 (Definido), operando bajo estándares documentados, arquitecturas centralizadas y niveles de servicio predecibles.",
    "en": "The consolidated global maturity index stands at {overall_maturity} out of 5.00, positioning the technology platform at Level 2 (Repeatable). This result reflects a clearly differentiated two-speed architecture. On one hand, foundational corporate capabilities—Storage & Backup (3.30) and Digital Workplace (3.10)—have reached Level 3 (Defined), operating under documented standards, centralized architectures, and predictable service levels.",
    "pt": "O índice global consolidado de maturidade situa-se em {overall_maturity} sobre 5.00, posicionando a plataforma tecnológica no Nível 2 (Repetível). Este resultado reflete uma arquitetura de duas velocidades claramente diferenciadas. Por um lado, as capacidades de base corporativa — Armazenamento e Backup (3.30) e Posto de Trabalho Digital (3.10) — atingiram o Nível 3 (Definido), operando sob padrões documentados, arquiteturas centralizadas e níveis de serviço previsíveis.",
    "fr": "L'indice global consolidé de maturité s'établit à {overall_maturity} sur 5,00, positionnant la plateforme technologique au Niveau 2 (Répétable). Ce résultat reflète une architecture à deux vitesses clairement différenciées. D'une part, les capacités de base de l'entreprise — Stockage et Sauvegarde (3,30) et Poste de Travail Numérique (3,10) — ont atteint le Niveau 3 (Défini), fonctionnant selon des normes documentées, des architectures centralisées et des niveaux de service prévisibles.",
    "de": "Der konsolidierte globale Reifegradindex liegt bei {overall_maturity} von 5,00 und positioniert die Technologieplattform auf Stufe 2 (Wiederholbar). Dieses Ergebnis spiegelt eine klar differenzierte Architektur der zwei Geschwindigkeiten wider. Einerseits haben grundlegende Unternehmensfähigkeiten – Speicher & Backup (3,30) und Digitaler Arbeitsplatz (3,10) – Stufe 3 (Definiert) erreicht und arbeiten nach dokumentierten Standards, zentralisierten Architekturen und vorhersagbaren Service-Levels.",
    "ja": "統合されたグローバル成熟度指数は5.00満点中{overall_maturity}であり、技術プラットフォームはレベル2（反復可能）に位置しています。この結果は、明確に分化した2つの速度を持つアーキテクチャを反映しています。一方では、企業の基盤機能であるストレージとバックアップ（3.30）およびデジタルワークプレイス（3.10）がレベル3（定義済み）に到達しており、文書化された標準、集中型アーキテクチャ、および予測可能なサービスレベルの下で運用されています。"
  },
  "tomo_ch2_summary_p2": {
    "es": "Por otro lado, los dominios que sustentan la ejecución industrial y transaccional —Continuidad en Planta (2.10), Integración de Datos (2.30), Aplicaciones Core (2.40) y Básculas y Expedición (2.40)— permanecen anclados en la franja frágil del Nivel 2. En estas áreas, la estabilidad operativa depende del esfuerzo reactivo del personal técnico, configuraciones locales sin redundancia automatizada e integraciones punto a punto. Esta asimetría estructural entre el entorno corporativo y la planta industrial constituye el vector principal de exposición operativa y financiera analizado en el Capítulo 3.",
    "en": "On the other hand, the domains sustaining industrial and transactional execution—Plant Continuity (2.10), Data Integration (2.30), Core Applications (2.40), and Weighbridge & Dispatch (2.40)—remain anchored in the fragile tier of Level 2. In these areas, operational stability relies on reactive technical staff heroics, local configurations lacking automated redundancy, and point-to-point integrations. This structural asymmetry between the corporate environment and the industrial plant constitutes the primary vector of operational and financial exposure analyzed in Chapter 3.",
    "pt": "Por outro lado, os domínios que sustentam a execução industrial e transacional — Continuidade em Planta (2.10), Integração de Dados (2.30), Aplicações Core (2.40) e Balanças e Expedição (2.40) — permanecem ancorados na faixa frágil do Nível 2. Nestas áreas, a estabilidade operacional depende do esforço reativo da equipe técnica, configurações locais sem redundância automatizada e integrações ponto a ponto. Esta assimetria estrutural entre o ambiente corporativo e a planta industrial constitui o vetor principal de exposição operacional e financeira analisado no Capítulo 3.",
    "fr": "D'autre part, les domaines soutenant l'exécution industrielle et transactionnelle — Continuité en Usine (2,10), Intégration des Données (2,30), Applications Core (2,40) et Ponts-Bascules et Expédition (2,40) — restent ancrés dans la tranche fragile du Niveau 2. Dans ces domaines, la stabilité opérationnelle repose sur l'effort réactif des équipes techniques, des configurations locales sans redondance automatisée et des intégrations point à point. Cette asymétrie structurelle entre l'environnement corporatif et l'usine industrielle constitue le vecteur principal d'exposition opérationnelle et financière analysé au Chapitre 3.",
    "de": "Andererseits bleiben die Domänen, die die industrielle und transaktionale Ausführung tragen – Werkskontinuität (2,10), Datenintegration (2,30), Kernanwendungen (2,40) sowie Waagen und Versand (2,40) – im fragilen Bereich der Stufe 2 verankert. In diesen Bereichen beruht die Betriebsstabilität auf dem reaktiven Einsatz des technischen Personals, lokalen Konfigurationen ohne automatisierte Redundanz und Punkt-zu-Punkt-Integrationen. Diese strukturelle Asymmetrie zwischen der Unternehmensumgebung und dem Industriewerk bildet den Hauptvektor des betrieblichen und finanziellen Risikos, das in Kapitel 3 analysiert wird.",
    "ja": "他方、産業およびトランザクションの実行を支える領域—工場事業継続性（2.10）、データ統合（2.30）、コアアプリケーション（2.40）、および計量台・出荷システム（2.40）—は、レベル2の脆弱な領域に留まっています。これらの領域では、運用の安定性は技術スタッフの事後対応的な尽力、自動冗長性を欠いたローカル構成、およびポイントツーポイントの統合に依存しています。コーポレート環境と産業プラント間のこの構造的な非対称性は、第3章で分析される運用上および財務上のリスクエクスポージャーの主要因となっています。"
  },
  "tomo_ch2_tbl_col_code": {
    "es": "Código",
    "en": "Code",
    "pt": "Código",
    "fr": "Code",
    "de": "Code",
    "ja": "コード"
  },
  "tomo_ch2_tbl_col_tower": {
    "es": "Área Tecnológica Evaluada",
    "en": "Evaluated Technology Domain",
    "pt": "Área Tecnológica Avaliada",
    "fr": "Domaine Technologique Évalué",
    "de": "Bewerteter Technologiebereich",
    "ja": "評価対象技術領域"
  },
  "tomo_ch2_tbl_col_asis": {
    "es": "Madurez AS-IS",
    "en": "AS-IS Maturity",
    "pt": "Maturidade AS-IS",
    "fr": "Maturité AS-IS",
    "de": "AS-IS-Reifegrad",
    "ja": "AS-IS成熟度"
  },
  "tomo_ch2_tbl_col_cmmi": {
    "es": "Nivel CMMI",
    "en": "CMMI Tier",
    "pt": "Nível CMMI",
    "fr": "Niveau CMMI",
    "de": "CMMI-Stufe",
    "ja": "CMMIレベル"
  },
  "tomo_ch2_tbl_col_status": {
    "es": "Estado Operativo",
    "en": "Operational Posture",
    "pt": "Estado Operacional",
    "fr": "Posture Opérationnelle",
    "de": "Betriebszustand",
    "ja": "運用状態"
  },
  "tomo_ch2_tbl_col_driver": {
    "es": "Factor Focal de Diagnóstico",
    "en": "Primary Diagnostic Driver",
    "pt": "Fator Focal de Diagnóstico",
    "fr": "Facteur Clé de Diagnostic",
    "de": "Primärer Diagnosefaktor",
    "ja": "主要診断要因"
  },
  "tomo_cmmi_lvl3": {
    "es": "Nivel 3 — Definido",
    "en": "Level 3 — Defined",
    "pt": "Nível 3 — Definido",
    "fr": "Niveau 3 — Défini",
    "de": "Stufe 3 — Definiert",
    "ja": "レベル3 — 定義済み"
  },
  "tomo_cmmi_lvl2": {
    "es": "Nivel 2 — Repetible",
    "en": "Level 2 — Repeatable",
    "pt": "Nível 2 — Repetível",
    "fr": "Niveau 2 — Répétable",
    "de": "Stufe 2 — Wiederholbar",
    "ja": "レベル2 — 反復可能"
  },
  "tomo_cmmi_lvl2_fragile": {
    "es": "Nivel 2 — Repetible (Frágil)",
    "en": "Level 2 — Repeatable (Fragile)",
    "pt": "Nível 2 — Repetível (Frágil)",
    "fr": "Niveau 2 — Répétable (Fragile)",
    "de": "Stufe 2 — Wiederholbar (Fragil)",
    "ja": "レベル2 — 反復可能（脆弱）"
  },
  "tomo_status_standardized": {
    "es": "Operación Estandarizada",
    "en": "Standardized Operation",
    "pt": "Operação Padronizada",
    "fr": "Opération Standardisée",
    "de": "Standardisierter Betrieb",
    "ja": "標準化運用"
  },
  "tomo_status_moderate_debt": {
    "es": "Deuda Técnica Moderada",
    "en": "Moderate Technical Debt",
    "pt": "Dívida Técnica Moderada",
    "fr": "Dette Technique Modérée",
    "de": "Moderate Technische Schuld",
    "ja": "中程度の技術的負債"
  },
  "tomo_status_high_risk": {
    "es": "Riesgo Operativo Alto",
    "en": "High Operational Risk",
    "pt": "Risco Operacional Alto",
    "fr": "Risque Opérationnel Élevé",
    "de": "Hohes Betriebsrisiko",
    "ja": "高運用リスク"
  },
  "tomo_ch2_driver_T1": {
    "es": "Topología WAN estable, pero segmentación IT/OT incompleta y enlaces críticos sin redundancia física de doble operador en plantas.",
    "en": "Stable WAN topology, but incomplete IT/OT segmentation and critical plant links lacking dual-carrier physical redundancy.",
    "pt": "Topologia WAN estável, mas segmentação IT/OT incompleta e links críticos sem redundância física de dupla operadora nas plantas.",
    "fr": "Topologie WAN stable, mais segmentation IT/OT incomplète et liaisons critiques sans redondance physique double opérateur en usine.",
    "de": "Stabile WAN-Topologie, aber unvollständige IT/OT-Segmentierung und kritische Werksverbindungen ohne physische Dual-Carrier-Redundanz.",
    "ja": "安定したWANトポロジだが、IT/OTセグメンテーションが不完全であり、工場の重要回線にデュアルキャリアの物理的冗長性が欠如。"
  },
  "tomo_ch2_driver_T2": {
    "es": "Clústeres hiperconvergentes consolidados a nivel central, penalizados por infraestructura local envejecida en plantas industriales.",
    "en": "Consolidated central hyperconverged clusters, offset by aging local server infrastructure across industrial plants.",
    "pt": "Clusters hiperconvergentes consolidados a nível central, penalizados por infraestrutura local envelhecida nas plantas industriais.",
    "fr": "Clusters hyperconvergés consolidés au niveau central, pénalisés par une infrastructure locale vieillissante dans les usines.",
    "de": "Konsolidierte zentrale hyperkonvergente Cluster, beeinträchtigt durch veraltete lokale Serverinfrastruktur in den Industriewerken.",
    "ja": "中央で統合されたハイパーコンバージドクラスタだが、産業プラント全体の老朽化したローカルサーバーインフラが足かせ。"
  },
  "tomo_ch2_driver_T3": {
    "es": "Arquitectura de respaldo centralizada con políticas definidas, pendiente de extender copias inmutables verificadas a sedes remotas.",
    "en": "Centralized backup architecture with defined policies, pending extension of verified immutable copies to remote sites.",
    "pt": "Arquitetura de backup centralizada com políticas definidas, pendente de estender cópias imutáveis verificadas a sedes remotas.",
    "fr": "Architecture de sauvegarde centralisée avec politiques définies, en attente d'extension des copies immuables aux sites distants.",
    "de": "Zentralisierte Backup-Architektur mit definierten Richtlinien, ausstehende Ausweitung verifizierter unveränderlicher Kopien auf Remote-Standorte.",
    "ja": "定義されたポリシーを持つ集中バックアップアーキテクチャだが、リモート拠点への検証済み不変コピーの拡張が未完了。"
  },
  "tomo_ch2_driver_T4": {
    "es": "Ecosistema colaborativo estandarizado y gestión de identidades madura, con brechas de control en terminales operativos de planta.",
    "en": "Standardized collaboration ecosystem and mature identity management, with control gaps in shop-floor operational endpoints.",
    "pt": "Ecossistema colaborativo padronizado e gestão de identidades madura, com lacunas de controle em terminais operacionais de planta.",
    "fr": "Écosystème collaboratif standardisé et gestion des identités mature, avec des lacunes de contrôle sur les terminaux d'usine.",
    "de": "Standardisiertes Kollaborations-Ökosystem und reifes Identitätsmanagement, mit Kontrolllücken bei operativen Endgeräten im Werk.",
    "ja": "標準化されたコラボレーション環境と成熟したID管理だが、工場現場の運用端末における管理ギャップが存在。"
  },
  "tomo_ch2_driver_T5": {
    "es": "Ecosistema ERP fragmentado con integraciones punto a punto no documentadas y alta dependencia de soporte correctivo manual.",
    "en": "Fragmented ERP ecosystem with undocumented point-to-point integrations and high reliance on manual corrective support.",
    "pt": "Ecossistema ERP fragmentado com integrações ponto a ponto não documentadas e alta dependência de suporte corretivo manual.",
    "fr": "Écosystème ERP fragmenté avec intégrations point à point non documentées et forte dépendance au support correctif manuel.",
    "de": "Fragmentiertes ERP-Ökosystem mit undokumentierten Punkt-zu-Punkt-Integrationen und hoher Abhängigkeit von manuellem Support.",
    "ja": "文書化されていないポイントツーポイント統合と手動の是正サポートへの高い依存を伴う断片化されたERPエコシステム。"
  },
  "tomo_ch2_driver_T6": {
    "es": "Controles perimetrales activos en capa corporativa, pero visibilidad limitada en redes OT y ausencia de respuesta automatizada (SOAR).",
    "en": "Active perimeter controls at corporate layer, but limited visibility across OT networks and absence of automated response (SOAR).",
    "pt": "Controles perimetrais ativos na camada corporativa, mas visibilidade limitada em redes OT e ausência de resposta automatizada (SOAR).",
    "fr": "Contrôles périmétriques actifs au niveau corporatif, mais visibilité limitée sur les réseaux OT et absence de réponse automatisée (SOAR).",
    "de": "Aktive Perimeterkontrollen auf Unternehmensebene, aber begrenzte Sichtbarkeit in OT-Netzwerken und fehlende automatisierte Reaktion (SOAR).",
    "ja": "コーポレート層での境界制御は有効だが、OTネットワークの可視性が限定的であり、自動応答（SOAR）が欠如。"
  },
  "tomo_ch2_driver_T7": {
    "es": "Procesos ITSM reactivos, ausencia de CMDB federada y catálogo de servicios sin acuerdos de nivel de servicio (SLA) auditables.",
    "en": "Reactive ITSM processes, absence of federated CMDB, and service catalog lacking auditable Service Level Agreements (SLAs).",
    "pt": "Processos ITSM reativos, ausência de CMDB federada e catálogo de serviços sem acordos de nível de serviço (SLA) auditáveis.",
    "fr": "Processus ITSM réactifs, absence de CMDB fédérée et catalogue de services sans accords de niveau de service (SLA) auditables.",
    "de": "Reaktive ITSM-Prozesse, fehlende föderierte CMDB und Servicekatalog ohne prüfbare Service Level Agreements (SLAs).",
    "ja": "事後対応型のITSMプロセス、統合CMDBの欠如、および監査可能なサービスレベル契約（SLA）のないサービスカタログ。"
  },
  "tomo_ch2_driver_T8": {
    "es": "Ausencia de planes DRP probados en entornos industriales, puntos únicos de fallo en servidores locales y alta dependencia de personal clave.",
    "en": "Absence of tested DRP plans in industrial environments, single points of failure in local servers, and high key-person dependency.",
    "pt": "Ausência de planos DRP testados em ambientes industriais, pontos únicos de falha em servidores locais e alta dependência de pessoal-chave.",
    "fr": "Absence de plans PRA testés en environnement industriel, points de défaillance uniques sur serveurs locaux et dépendance aux personnes clés.",
    "de": "Fehlende getestete DRP-Pläne in Industrieumgebungen, Single Points of Failure bei lokalen Servern und hohe Abhängigkeit von Schlüsselpersonal.",
    "ja": "産業環境におけるテスト済みDRP計画の欠如、ローカルサーバーの単一障害点、および特定技術者への高い依存。"
  },
  "tomo_ch2_driver_T9": {
    "es": "Extracción de datos mediante procesos batch frágiles, sin capa intermedia de gobierno ni linaje de datos entre sistemas de planta y ERP.",
    "en": "Data extraction via fragile batch processes, lacking an intermediate governance layer or data lineage between plant systems and ERP.",
    "pt": "Extração de dados mediante processos batch frágeis, sem camada intermediária de governança nem linhagem de dados entre planta e ERP.",
    "fr": "Extraction de données via des processus batch fragiles, sans couche de gouvernance intermédiaire ni lignage entre usine et ERP.",
    "de": "Datenextraktion über fragile Batch-Prozesse, ohne zwischengeschaltete Governance-Ebene oder Datenherkunft zwischen Werkssystemen und ERP.",
    "ja": "脆弱なバッチ処理によるデータ抽出であり、工場システムとERP間の中間ガバナンス層やデータリネージが欠如。"
  },
  "tomo_ch2_driver_T10": {
    "es": "Sistemas de pesaje y despacho acoplados a hardware local sin contingencia automatizada, generando riesgo directo de bloqueo logístico.",
    "en": "Weighbridge and dispatch systems coupled to local hardware without automated contingency, creating direct risk of logistics gridlock.",
    "pt": "Sistemas de pesagem e expedição acoplados a hardware local sem contingência automatizada, gerando risco direto de bloqueio logístico.",
    "fr": "Systèmes de pesage et d'expédition couplés au matériel local sans contingence automatisée, créant un risque direct de blocage logistique.",
    "de": "Waagen- und Versandsysteme ohne automatisierte Ausfallsicherung an lokale Hardware gekoppelt, was direktes Risiko von Logistikblockaden birgt.",
    "ja": "自動緊急代替手段なしでローカルハードウェアに結合された計量・出荷システムにより、物流停滞の直接的リスクが発生。"
  },
  "tomo_ch2_driver_summary": {
    "es": "Asimetría estructural entre servicios corporativos estandarizados (Nivel 3) y operaciones críticas de planta expuestas (Nivel 2).",
    "en": "Structural asymmetry between standardized corporate services (Level 3) and exposed critical plant operations (Level 2).",
    "pt": "Assimetria estrutural entre serviços corporativos padronizados (Nível 3) e operações críticas de planta expostas (Nível 2).",
    "fr": "Asymétrie structurelle entre les services corporatifs standardisés (Niveau 3) et les opérations critiques d'usine exposées (Niveau 2).",
    "de": "Strukturelle Asymmetrie zwischen standardisierten Unternehmensdiensten (Stufe 3) und exponierten kritischen Werksabläufen (Stufe 2).",
    "ja": "標準化されたコーポレートサービス（レベル3）とリスクに晒された重要工場運用（レベル2）間の構造的な非対称性。"
  },
  "tomo_radar_caption": {
    "es": "Figura 2.1. Radiografía Polar de Madurez Tecnológica AS-IS (Escala CMMI 1.00 - 5.00).",
    "en": "Figure 2.1. Polar Radiography of AS-IS Technology Maturity (CMMI Scale 1.00 - 5.00).",
    "pt": "Figura 2.1. Radiografia Polar de Maturidade Tecnológica AS-IS (Escala CMMI 1.00 - 5.00).",
    "fr": "Figure 2.1. Radiographie Polaire de Maturité Technologique AS-IS (Échelle CMMI 1,00 - 5,00).",
    "de": "Abbildung 2.1. Polare Radiographie des technologischen AS-IS-Reifegrads (CMMI-Skala 1,00 - 5,00).",
    "ja": "図 2.1. AS-IS技術成熟度の極座標ラジオグラフィー（CMMIスケール 1.00 - 5.00）。"
  },
  "tomo_radar_legend_asis": {
    "es": "Huella de Madurez AS-IS ({client_name})",
    "en": "AS-IS Maturity Footprint ({client_name})",
    "pt": "Pegada de Maturidade AS-IS ({client_name})",
    "fr": "Empreinte de Maturité AS-IS ({client_name})",
    "de": "AS-IS-Reifegradprofil ({client_name})",
    "ja": "AS-IS成熟度フットプリント ({client_name})"
  }
}
```

---

### 3. Implementation Blueprint: `tomo_asis_ast_compiler.py`

The compiler method `_build_chapter_2_maturity_overview` is refactored to remove the external benchmark callout box, inject the two-paragraph executive narrative, and construct the 6-column forensic Table 2.

```python
    def _classify_maturity_tier(self, score: float) -> tuple[str, str]:
        """Classify empirical maturity score into CMMI Tier and Operational Posture keys."""
        if score >= 3.00:
            return (
                self._t("tomo_cmmi_lvl3", "Level 3 — Defined"),
                self._t("tomo_status_standardized", "Standardized Operation"),
            )
        if score >= 2.45:
            return (
                self._t("tomo_cmmi_lvl2", "Level 2 — Repeatable"),
                self._t("tomo_status_moderate_debt", "Moderate Technical Debt"),
            )
        return (
            self._t("tomo_cmmi_lvl2_fragile", "Level 2 — Repeatable (Fragile)"),
            self._t("tomo_status_high_risk", "High Operational Risk"),
        )

    def _build_chapter_2_maturity_overview(self) -> Section:
        """Compile Chapter 2: Empirical Maturity Radiography (Zero External Benchmarks)."""
        sec = Section(
            id="sec-ch2-maturity",
            title=self._t("tomo_ch2_title", "2. Radiografía de Madurez (10 Torres)"),
            level=1,
        )

        # 1. Methodological Introduction
        sec.blocks.append(
            Paragraph(
                text=self._t("tomo_ch2_intro", ""),
                style_hint="body",
            )
        )

        # 2. Compute Empirical Maturity Scores Across All 10 Towers
        rows: list[TableRow] = []
        total_asis = 0.0
        count = 0

        for idx in range(1, 11):
            t_id = f"T{idx}"
            t_data = self.towers_data.get(t_id, {})
            t_name = self._get_tower_display_name(t_id, t_data)
            asis_val = float(t_data.get("maturity_asis", 2.5))

            total_asis += asis_val
            count += 1

            cmmi_label, status_label = self._classify_maturity_tier(asis_val)
            driver_text = self._t(f"tomo_ch2_driver_{t_id}", "")

            rows.append(
                TableRow(
                    cells=[
                        TableCell(content=[Paragraph(text=t_id)], align="center", bold=True),
                        TableCell(content=[Paragraph(text=t_name)], align="left", bold=True),
                        TableCell(content=[Paragraph(text=f"{asis_val:.2f}")], align="center", bold=True),
                        TableCell(content=[Paragraph(text=cmmi_label)], align="center"),
                        TableCell(content=[Paragraph(text=status_label)], align="center", bold=(asis_val < 2.45)),
                        TableCell(content=[Paragraph(text=driver_text)], align="left"),
                    ]
                )
            )

        avg_asis = total_asis / count if count > 0 else 0.0
        avg_cmmi_label, avg_status_label = self._classify_maturity_tier(avg_asis)

        # 3. Consolidated Summary Row
        rows.append(
            TableRow(
                cells=[
                    TableCell(content=[Paragraph(text="—")], align="center", bold=True),
                    TableCell(
                        content=[Paragraph(text=self._t("tomo_ch2_tbl_avg", "Media Consolidada"))],
                        align="left",
                        bold=True,
                    ),
                    TableCell(content=[Paragraph(text=f"{avg_asis:.2f}")], align="center", bold=True),
                    TableCell(content=[Paragraph(text=avg_cmmi_label)], align="center", bold=True),
                    TableCell(content=[Paragraph(text=avg_status_label)], align="center", bold=True),
                    TableCell(
                        content=[Paragraph(text=self._t("tomo_ch2_driver_summary", ""))],
                        align="left",
                        bold=True,
                    ),
                ]
            )
        )

        # 4. Enriched Dual-Speed Executive Narrative
        summary_p1 = self._t("tomo_ch2_summary_p1", "").format(
            overall_maturity=f"{avg_asis:.2f}"
        )
        summary_p2 = self._t("tomo_ch2_summary_p2", "")

        sec.blocks.append(Paragraph(text=summary_p1, style_hint="body"))
        sec.blocks.append(Paragraph(text=summary_p2, style_hint="body"))

        # 5. Forensic Table 2 (6-Column Empirical Capability Matrix)
        headers = [
            TableCell(content=[Paragraph(text=self._t("tomo_ch2_tbl_col_code", "Código"))], align="center", bold=True),
            TableCell(content=[Paragraph(text=self._t("tomo_ch2_tbl_col_tower", "Área Tecnológica Evaluada"))], align="left", bold=True),
            TableCell(content=[Paragraph(text=self._t("tomo_ch2_tbl_col_asis", "Madurez AS-IS"))], align="center", bold=True),
            TableCell(content=[Paragraph(text=self._t("tomo_ch2_tbl_col_cmmi", "Nivel CMMI"))], align="center", bold=True),
            TableCell(content=[Paragraph(text=self._t("tomo_ch2_tbl_col_status", "Estado Operativo"))], align="center", bold=True),
            TableCell(content=[Paragraph(text=self._t("tomo_ch2_tbl_col_driver", "Factor Focal de Diagnóstico"))], align="left", bold=True),
        ]

        sec.blocks.append(
            Table(
                id="tbl-ch2-maturity",
                caption=self._t(
                    "tomo_ch2_tbl_caption",
                    "Tabla 2. Matriz de Madurez Tecnológica AS-IS por Dominio de Capacidad.",
                ),
                headers=headers,
                rows=rows,
                col_widths=[0.07, 0.20, 0.10, 0.16, 0.16, 0.31],
            )
        )

        # 6. Single-Series Authentic Polar Radar Chart
        if self.radar_chart_path and Path(self.radar_chart_path).exists():
            sec.blocks.append(
                Figure(
                    id="fig-ch2-radar",
                    path=str(self.radar_chart_path),
                    caption=self._t(
                        "tomo_radar_caption",
                        "Figura 2.1. Radiografía Polar de Madurez Tecnológica AS-IS (Escala CMMI 1.00 - 5.00).",
                    ),
                    width_pct=0.82,
                )
            )

        return sec
```

---

### 4. Implementation Blueprint: `generate_global_radar_chart.py`

The polar radar generator is stripped of all external benchmark polygons (`benchmark_scores`, dashed gray lines) and renders a high-contrast, single-series corporate blue (`#0072BC`) capability footprint over the CMMI Level 1–5 grid, annotated with empirical data badges at each vertex.

```python
"""Single-Series Empirical Polar Radar Chart Generator for Chapter 2."""

from pathlib import Path
import math
import matplotlib.pyplot as plt
import numpy as np


def generate_global_radar_chart(
    labels: list[str],
    asis_scores: list[float],
    output_path: str | Path,
    title: str = "",
    legend_asis_label: str = "AS-IS Maturity Footprint",
) -> Path:
    """Render a high-resolution single-series CMMI polar radar chart.

    Args:
        labels: Ordered list of 10 technology tower display names.
        asis_scores: Ordered list of 10 empirical AS-IS scores (1.00 - 5.00).
        output_path: Destination PNG file path.
        title: Chart header title.
        legend_asis_label: Localized label for the client AS-IS footprint.

    Returns:
        Path to the generated PNG image.
    """
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

    # Close the polar polygon
    scores_closed = list(asis_scores) + [asis_scores[0]]
    angles_closed = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(8.5, 8.5), subplot_kw={"polar": True}, dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    # Orient T1 at top (12 o'clock) and plot clockwise
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # Configure CMMI radial rings (Levels 1 to 5)
    ax.set_ylim(0, 5.0)
    ax.set_yticks([1.0, 2.0, 3.0, 4.0, 5.0])
    ax.set_yticklabels(
        ["CMMI 1", "CMMI 2", "CMMI 3", "CMMI 4", "CMMI 5"],
        color="#475569",
        fontsize=8.5,
        fontweight="bold",
    )
    ax.set_rlabel_position(18)

    # Style radial and angular gridlines
    ax.yaxis.grid(True, color="#CBD5E1", linestyle="--", linewidth=0.9, alpha=0.85)
    ax.xaxis.grid(True, color="#CBD5E1", linestyle="-", linewidth=0.8, alpha=0.75)
    ax.spines["polar"].set_color("#94A3B8")
    ax.spines["polar"].set_linewidth(1.1)

    # Plot authentic single-series AS-IS footprint in Corporate Solid Blue (#0072BC)
    corporate_blue = "#0072BC"
    ax.plot(
        angles_closed,
        scores_closed,
        color=corporate_blue,
        linewidth=2.6,
        linestyle="solid",
        marker="o",
        markersize=7,
        markerfacecolor=corporate_blue,
        markeredgecolor="#FFFFFF",
        markeredgewidth=1.5,
        label=legend_asis_label,
        zorder=4,
    )
    ax.fill(
        angles_closed,
        scores_closed,
        color=corporate_blue,
        alpha=0.22,
        zorder=3,
    )

    # Annotate exact empirical score at each vertex
    for angle, score in zip(angles, asis_scores):
        radial_offset = min(score + 0.38, 4.85)
        ax.text(
            angle,
            radial_offset,
            f"{score:.2f}",
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=8.5,
            fontweight="bold",
            color="#0F172A",
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": "#FFFFFF",
                "edgecolor": corporate_blue,
                "alpha": 0.92,
                "linewidth": 0.8,
            },
            zorder=5,
        )

    # Configure outer tower labels with intelligent alignment
    ax.set_xticks(angles)
    ax.set_xticklabels([])  # Custom placement for clean padding

    for angle, label in zip(angles, labels):
        deg = math.degrees(angle)
        if deg == 0 or deg == 180:
            ha = "center"
        elif 0 < deg < 180:
            ha = "left"
        else:
            ha = "right"

        ax.text(
            angle,
            5.55,
            label,
            size=9.5,
            fontweight="bold",
            color="#1E293B",
            horizontalalignment=ha,
            verticalalignment="center",
        )

    if title:
        plt.title(
            title,
            size=12,
            fontweight="bold",
            color="#0F172A",
            y=1.12,
        )

    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.18, 1.10),
        frameon=True,
        facecolor="#FFFFFF",
        edgecolor="#CBD5E1",
        fontsize=9.5,
    )

    plt.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="#FFFFFF")
    plt.close(fig)

    return out_path
```