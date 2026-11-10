import json
from pathlib import Path

path = Path("engine_config/locales.json")
data = json.loads(path.read_text(encoding="utf-8"))

CH4_RECEPTORS = {
  "en": {
    "AVAILABILITY_OUTAGE": {
      "methodology_intro": "Actuarial exposure for {domain_name} is modeled via the Open FAIR™ Availability & Service Disruption receptor, capturing the financial impact of unplanned service halting and recovery friction.",
      "formula_expression": "ALE = LEF × (Downtime_Duration × Hourly_Burn_Rate + Recovery_Toil + SLA_Penalties)",
      "vector_alpha_label": "Direct Transactional & SLA Downtime Loss",
      "vector_alpha_desc": "Financial impact of service unavailability across critical assets.",
      "vector_beta_label": "Emergency War-Room & Recovery Labor",
      "vector_beta_desc": "Unplanned engineering toil required to restore state and resolve root causes.",
      "vector_gamma_label": "Downstream Churn & Reputational Attrition",
      "vector_gamma_desc": "Secondary commercial erosion resulting from prolonged systemic instability.",
      "prioritization_rationale": "Remediation sequence is strictly ordered by MTTR reduction and Blast Radius containment."
    },
    "CAPITAL_INEFFICIENCY": {
      "methodology_intro": "Actuarial exposure for {domain_name} is modeled via the Open FAIR™ Capital Inefficiency & Structural Waste receptor, capturing value leakage from unoptimized resources.",
      "formula_expression": "ALE = LEF × (Cloud_Drift_Waste + Software_Licensing_Overhead + FinOps_Rework)",
      "vector_alpha_label": "Unutilized Compute & Zombie Infrastructure Waste",
      "vector_alpha_desc": "Financial drain from over-provisioned architecture and idle cloud instances.",
      "vector_beta_label": "Sub-optimal Licensing & Commitment Discounts",
      "vector_beta_desc": "Loss of capital from software shelfware and failure to leverage reserved pricing.",
      "vector_gamma_label": "Architectural Re-work & Governance Remediation",
      "vector_gamma_desc": "Friction costs stemming from deferred architectural modernization.",
      "prioritization_rationale": "Remediation sequence is ordered by immediate OpEx reclamation and licensing compliance."
    },
    "PRODUCTIVITY_TOIL": {
      "methodology_intro": "Actuarial exposure for {domain_name} is modeled via the Open FAIR™ Productivity Toil & Human Friction receptor, quantifying the loss of engineering and operational bandwidth.",
      "formula_expression": "ALE = LEF × (Engineering_Idle_Time + Time_to_Market_Delay + Manual_Support_Toil)",
      "vector_alpha_label": "Aggregate Engineering & Employee Idle Time",
      "vector_alpha_desc": "Context-switching friction and wait-states induced by poor developer experience or slow tooling.",
      "vector_beta_label": "Delayed Time-to-Market (Opportunity Cost)",
      "vector_beta_desc": "Commercial opportunity cost of reduced feature velocity and deployment bottlenecks.",
      "vector_gamma_label": "Manual Remediation Toil & Escalation Overhead",
      "vector_gamma_desc": "Human capital burned in manual support tickets and repetitive operational triage.",
      "prioritization_rationale": "Remediation sequence prioritizes automation workflows and friction elimination."
    },
    "REGULATORY_AND_BREACH": {
      "methodology_intro": "Actuarial exposure for {domain_name} is modeled via the Open FAIR™ Regulatory & Breach Liability receptor, assessing statutory penalties and forensic crisis scenarios.",
      "formula_expression": "ALE = LEF × (Statutory_Fines + Forensic_Response_Extortion + Reputational_Churn)",
      "vector_alpha_label": "Statutory Regulatory Fines & Legal Liability",
      "vector_alpha_desc": "Empirical projection of supervisory sanctions (NIS2, GDPR, DORA) modeled with enforcement discretion.",
      "vector_beta_label": "Incident Response, Forensics & Extortion",
      "vector_beta_desc": "Direct capital flight from ransom containment and specialized DFIR retainer mobilization.",
      "vector_gamma_label": "Mandatory Notification & Reputational Churn",
      "vector_gamma_desc": "Commercial loss driven by compromised stakeholder trust and mandatory credit monitoring.",
      "prioritization_rationale": "Remediation sequence focuses on lateral movement containment, Zero Trust segmentation, and PAM."
    }
  },
  "es": {
    "AVAILABILITY_OUTAGE": {
      "methodology_intro": "La exposición actuarial para {domain_name} se modela mediante el receptor Open FAIR™ de Indisponibilidad y Parada Operativa, capturando el impacto financiero de la interrupción del servicio.",
      "formula_expression": "ALE = LEF × (Duración_Parada × Tasa_Erosión_Horaria + Esfuerzo_Recuperación + Penalizaciones_SLA)",
      "vector_alpha_label": "Pérdida Transaccional Directa y Penalizaciones SLA",
      "vector_alpha_desc": "Impacto financiero por la inactividad del servicio en activos críticos.",
      "vector_beta_label": "Gabinete de Crisis y Esfuerzo de Recuperación",
      "vector_beta_desc": "Toil de ingeniería no planificado requerido para restaurar el estado y resolver causas raíz.",
      "vector_gamma_label": "Fricción Comercial y Erosión Reputacional",
      "vector_gamma_desc": "Erosión secundaria derivada de la inestabilidad sistémica prolongada.",
      "prioritization_rationale": "La secuencia de remediación se ordena estrictamente por la reducción del MTTR y contención del radio de explosión."
    },
    "CAPITAL_INEFFICIENCY": {
      "methodology_intro": "La exposición actuarial para {domain_name} se modela mediante el receptor Open FAIR™ de Ineficiencia de Capital y Desvío Presupuestario, capturando fugas de valor en recursos no optimizados.",
      "formula_expression": "ALE = LEF × (Desvío_Cloud + Sobrecoste_Licenciamiento + Retrabajo_FinOps)",
      "vector_alpha_label": "Cómputo Ocioso e Infraestructura Zombi",
      "vector_alpha_desc": "Fuga financiera por sobre-aprovisionamiento y capacidad de cómputo inactiva.",
      "vector_beta_label": "Licenciamiento Subóptimo y Falta de Descuentos",
      "vector_beta_desc": "Pérdida de capital en licencias sin uso y fallos en la optimización de instancias reservadas.",
      "vector_gamma_label": "Deuda Arquitectónica y Gobernanza FinOps",
      "vector_gamma_desc": "Costes de fricción derivados del retraso en la modernización de la arquitectura.",
      "prioritization_rationale": "La remediación prioriza la recuperación inmediata de OpEx y el cumplimiento de licencias."
    },
    "PRODUCTIVITY_TOIL": {
      "methodology_intro": "La exposición actuarial para {domain_name} se modela mediante el receptor Open FAIR™ de Fricción de Productividad y Toil, cuantificando la pérdida de ancho de banda operativo e ingeniería.",
      "formula_expression": "ALE = LEF × (Tiempo_Inactivo_Ingeniería + Retraso_Time_to_Market + Toil_Soporte_Manual)",
      "vector_alpha_label": "Fricción Acumulada de Empleados e Ingeniería",
      "vector_alpha_desc": "Tiempos de espera por cambios de contexto e ineficiencias en herramientas lentas.",
      "vector_beta_label": "Retraso en Time-to-Market (Coste de Oportunidad)",
      "vector_beta_desc": "Coste de oportunidad comercial por cuellos de botella en el despliegue de nuevas funcionalidades.",
      "vector_gamma_label": "Toil en Soporte Manual y Gestión de Tickets",
      "vector_gamma_desc": "Capital humano consumido en tareas manuales y soporte repetitivo.",
      "prioritization_rationale": "La remediación prioriza la automatización de flujos y eliminación de cuellos de botella."
    },
    "REGULATORY_AND_BREACH": {
      "methodology_intro": "La exposición actuarial para {domain_name} se modela mediante el receptor Open FAIR™ de Responsabilidad Normativa y Brechas, evaluando sanciones estatutarias y escenarios de crisis forense.",
      "formula_expression": "ALE = LEF × (Multas_Regulatorias + Respuesta_Forense_Extorsión + Impacto_Reputacional)",
      "vector_alpha_label": "Sanciones Regulatorias y Pasivos de Cumplimiento",
      "vector_alpha_desc": "Proyección empírica de multas (NIS2, GDPR, DORA) ajustada por discrecionalidad supervisora.",
      "vector_beta_label": "Respuesta a Incidentes, Forense y Extorsión",
      "vector_beta_desc": "Fuga directa de capital en rescates y movilización especializada de DFIR.",
      "vector_gamma_label": "Notificación Obligatoria y Fuga de Clientes",
      "vector_gamma_desc": "Pérdida comercial por quiebra de confianza y servicios obligatorios de protección de identidad.",
      "prioritization_rationale": "La estrategia de remediación prioriza el bastionado perimetral, Zero Trust y PAM."
    }
  },
  "pt": {
    "AVAILABILITY_OUTAGE": {
      "methodology_intro": "A exposição atuarial para {domain_name} é modelada via receptor Open FAIR™ de Indisponibilidade Operacional, capturando o impacto financeiro de paradas não planejadas.",
      "formula_expression": "ALE = LEF × (Duracao_Parada × Custo_Horario + Esforco_Recuperacao + Multas_SLA)",
      "vector_alpha_label": "Perda Transacional Direta e Multas de SLA",
      "vector_alpha_desc": "Impacto financeiro por indisponibilidade de serviços em ativos críticos.",
      "vector_beta_label": "Esforço de Engenharia de Emergência",
      "vector_beta_desc": "Trabalho não planejado necessário para restaurar e resolver causas raízes.",
      "vector_gamma_label": "Fricção Comercial e Erosão de Reputação",
      "vector_gamma_desc": "Erosão secundária decorrente de instabilidade sistêmica prolongada.",
      "prioritization_rationale": "A remediação é ordenada pela redução do MTTR e contenção do raio de explosão."
    },
    "CAPITAL_INEFFICIENCY": {
      "methodology_intro": "A exposição atuarial para {domain_name} é modelada via receptor Open FAIR™ de Ineficiência de Capital, capturando vazamentos de valor em infraestrutura e licenciamento.",
      "formula_expression": "ALE = LEF × (Desperdicio_Cloud + Licenciamento_Excessivo + Retrabalho_FinOps)",
      "vector_alpha_label": "Computação Ociosa e Infraestrutura Zumbi",
      "vector_alpha_desc": "Dreno financeiro por arquitetura superprovisionada e instâncias de nuvem ociosas.",
      "vector_beta_label": "Licenciamento Subótimo e Sem Descontos",
      "vector_beta_desc": "Perda de capital de software sem uso e falha em alavancar reservas de nuvem.",
      "vector_gamma_label": "Retrabalho de Arquitetura e Governança",
      "vector_gamma_desc": "Custos de fricção oriundos do atraso na modernização da arquitetura.",
      "prioritization_rationale": "A remediação foca na recuperação imediata de OpEx e conformidade de software."
    },
    "PRODUCTIVITY_TOIL": {
      "methodology_intro": "A exposição atuarial para {domain_name} é modelada via receptor Open FAIR™ de Fricção de Produtividade (Toil), quantificando a perda de largura de banda de engenharia.",
      "formula_expression": "ALE = LEF × (Tempo_Ocioso_Engenharia + Atraso_Time_to_Market + Toil_Suporte_Manual)",
      "vector_alpha_label": "Tempo Ocioso Acumulado de Engenheiros",
      "vector_alpha_desc": "Fricção por mudanças de contexto e esperas induzidas por ferramentas lentas.",
      "vector_beta_label": "Atraso no Time-to-Market (Custo de Oportunidade)",
      "vector_beta_desc": "Custo de oportunidade de menor velocidade de entrega e gargalos de deploy.",
      "vector_gamma_label": "Toil em Suporte Manual e Tickets",
      "vector_gamma_desc": "Capital humano queimado em tickets de suporte manuais e processos repetitivos.",
      "prioritization_rationale": "A sequência de priorização visa automação de fluxos e eliminação de atrasos."
    },
    "REGULATORY_AND_BREACH": {
      "methodology_intro": "A exposição atuarial para {domain_name} é modelada via receptor Open FAIR™ de Risco Regulatório e Violações, avaliando penalidades estatutárias e crises cibernéticas.",
      "formula_expression": "ALE = LEF × (Multas_Regulatorias + Resposta_Forense_Extorsao + Perda_Reputacional)",
      "vector_alpha_label": "Multas Regulatórias e Passivo Legal",
      "vector_alpha_desc": "Projeção empírica de sanções (NIS2, GDPR, DORA) ajustada por discrição supervisora.",
      "vector_beta_label": "Resposta a Incidentes, Forense e Extorsão",
      "vector_beta_desc": "Fuga de capital em contenção de resgate e mobilização especializada de DFIR.",
      "vector_gamma_label": "Notificação Obrigatória e Atrito de Clientes",
      "vector_gamma_desc": "Perda comercial por confiança abalada e monitoramento de crédito obrigatório.",
      "prioritization_rationale": "Foco imediato na contenção de movimento lateral, segmentação Zero Trust e PAM."
    }
  },
  "fr": {
    "AVAILABILITY_OUTAGE": {
      "methodology_intro": "L'exposition actuarielle pour {domain_name} est modélisée via le récepteur Open FAIR™ d'Indisponibilité, capturant l'impact financier de l'interruption des services.",
      "formula_expression": "ALE = LEF × (Duree_Indisponibilite × Taux_Horaire + Effort_Recuperation + Penalites_SLA)",
      "vector_alpha_label": "Perte Transactionnelle Directe et Pénalités SLA",
      "vector_alpha_desc": "Impact financier dû à l'indisponibilité des services critiques.",
      "vector_beta_label": "Cellule de Crise et Effort Ingénierie",
      "vector_beta_desc": "Travail imprévu nécessaire pour restaurer l'état et résoudre les causes.",
      "vector_gamma_label": "Attrition Commerciale et Réputation",
      "vector_gamma_desc": "Érosion secondaire résultant d'une instabilité systémique prolongée.",
      "prioritization_rationale": "La remédiation est ordonnée par la réduction du MTTR et le contrôle du rayon d'explosion."
    },
    "CAPITAL_INEFFICIENCY": {
      "methodology_intro": "L'exposition actuarielle pour {domain_name} est modélisée via le récepteur Open FAIR™ d'Inefficacité du Capital, mesurant le gaspillage financier des ressources.",
      "formula_expression": "ALE = LEF × (Gaspillage_Cloud + Licences_Inutilisees + Refonte_FinOps)",
      "vector_alpha_label": "Ressources Inutilisées et Infrastructures Zombies",
      "vector_alpha_desc": "Fuite financière liée au surdimensionnement de l'architecture.",
      "vector_beta_label": "Gestion Sous-optimale des Licences",
      "vector_beta_desc": "Perte de capital en licences logicielles et gestion des remises cloud.",
      "vector_gamma_label": "Dette Architecturale et Remédiation FinOps",
      "vector_gamma_desc": "Coûts de friction liés au report de la modernisation architecturale.",
      "prioritization_rationale": "Priorité à la récupération d'OpEx immédiate et la conformité des licences."
    },
    "PRODUCTIVITY_TOIL": {
      "methodology_intro": "L'exposition actuarielle pour {domain_name} est modélisée via le récepteur Open FAIR™ de Friction de Productivité (Toil), quantifiant la perte de bande passante opérationnelle.",
      "formula_expression": "ALE = LEF × (Temps_Inactif_Ingenierie + Retard_Time_to_Market + Support_Manuel)",
      "vector_alpha_label": "Temps Mort Cumulé des Employés",
      "vector_alpha_desc": "Friction de changement de contexte induite par des outils lents.",
      "vector_beta_label": "Retard de Mise sur le Marché (Coût d'Opportunité)",
      "vector_beta_desc": "Coût d'opportunité dû aux goulots d'étranglement de déploiement.",
      "vector_gamma_label": "Assistance Manuelle et Surcharge d'Escalade",
      "vector_gamma_desc": "Capital humain consommé par les tickets manuels et le support.",
      "prioritization_rationale": "La remédiation cible l'automatisation et l'élimination des frictions."
    },
    "REGULATORY_AND_BREACH": {
      "methodology_intro": "L'exposition actuarielle pour {domain_name} est modélisée via le récepteur Open FAIR™ de Risque Réglementaire et Cyber, évaluant les amendes légales et extorsions.",
      "formula_expression": "ALE = LEF × (Amendes_Reglementaires + Reponse_Forense_Extorsion + Churn_Reputationnel)",
      "vector_alpha_label": "Amendes Réglementaires et Passif Légal",
      "vector_alpha_desc": "Projection empirique des sanctions (NIS2, RGPD, DORA) ajustée par la discrétion.",
      "vector_beta_label": "Réponse aux Incidents, Forensique et Extorsion",
      "vector_beta_desc": "Fuite directe due à l'endiguement de crise et aux experts DFIR.",
      "vector_gamma_label": "Notification Obligatoire et Attrition",
      "vector_gamma_desc": "Perte commerciale due à la méfiance des clients et à la notification légale.",
      "prioritization_rationale": "L'accent est mis sur le Zero Trust, le confinement latéral et le PAM."
    }
  },
  "de": {
    "AVAILABILITY_OUTAGE": {
      "methodology_intro": "Die versicherungsmathematische Exposition für {domain_name} wird über den Open FAIR™ Availability Rezeptor modelliert, der ungeplante Ausfallzeiten misst.",
      "formula_expression": "ALE = LEF × (Ausfallzeit × Stundensatz + Notfallwiederherstellung + SLA_Strafen)",
      "vector_alpha_label": "Direkter Umsatz- und SLA-Ausfallverlust",
      "vector_alpha_desc": "Finanzielle Auswirkungen von Nichtverfügbarkeit auf kritische Assets.",
      "vector_beta_label": "Notfall-Krisenstab und Wiederherstellungsaufwand",
      "vector_beta_desc": "Ungeplanter Aufwand der Ingenieure zur Wiederherstellung und Fehlerbehebung.",
      "vector_gamma_label": "Reputationsverlust und Kundenabwanderung",
      "vector_gamma_desc": "Sekundäre wirtschaftliche Erosion durch anhaltende Instabilität.",
      "prioritization_rationale": "Die Behebung richtet sich strikt nach MTTR-Reduzierung und Eindämmung."
    },
    "CAPITAL_INEFFICIENCY": {
      "methodology_intro": "Die versicherungsmathematische Exposition für {domain_name} wird über den Open FAIR™ Capital Inefficiency Rezeptor modelliert, der Kapitalverluste erfasst.",
      "formula_expression": "ALE = LEF × (Cloud_Verschwendung + Lizenzueberhang + FinOps_Nacharbeit)",
      "vector_alpha_label": "Ungenutzte Ressourcen und Zombie-Infrastruktur",
      "vector_alpha_desc": "Finanzieller Abfluss durch überdimensionierte Cloud-Architektur.",
      "vector_beta_label": "Suboptimale Lizenzen und Rabattverluste",
      "vector_beta_desc": "Kapitalverlust durch ungenutzte Softwarelizenzen und Cloud-Konditionen.",
      "vector_gamma_label": "Architektur-Nacharbeit und FinOps-Governance",
      "vector_gamma_desc": "Reibungskosten, die durch verschobene Modernisierung entstehen.",
      "prioritization_rationale": "Priorisierung liegt auf sofortiger OpEx-Rückgewinnung und Lizenz-Compliance."
    },
    "PRODUCTIVITY_TOIL": {
      "methodology_intro": "Die versicherungsmathematische Exposition für {domain_name} wird über den Open FAIR™ Productivity Toil Rezeptor modelliert, der die menschliche Arbeitsreibung quantifiziert.",
      "formula_expression": "ALE = LEF × (Ingenieur_Leerlauf + Time_to_Market_Verzoegerung + Manueller_Support)",
      "vector_alpha_label": "Kumulierte Leerlaufzeiten von Mitarbeitern",
      "vector_alpha_desc": "Reibungsverluste durch Kontextwechsel und langsame Werkzeuge.",
      "vector_beta_label": "Verzögerung der Markteinführung (Opportunitätskosten)",
      "vector_beta_desc": "Kommerzielle Kosten reduzierter Funktionsgeschwindigkeit und Bereitstellung.",
      "vector_gamma_label": "Manueller Support und Ticket-Overhead",
      "vector_gamma_desc": "Humankapitalverbrauch durch manuelle Tickets und operative Triage.",
      "prioritization_rationale": "Die Priorisierung zielt auf Workflow-Automatisierung und Reibungsminderung ab."
    },
    "REGULATORY_AND_BREACH": {
      "methodology_intro": "Die versicherungsmathematische Exposition für {domain_name} wird über den Open FAIR™ Regulatory & Breach Rezeptor modelliert, der gesetzliche Strafen bewertet.",
      "formula_expression": "ALE = LEF × (Strafgelder + Forensik_Erpressung + Reputationsverlust)",
      "vector_alpha_label": "Gesetzliche Strafen und rechtliche Haftung",
      "vector_alpha_desc": "Empirische Projektion von Sanktionen (NIS2, DSGVO, DORA).",
      "vector_beta_label": "Vorfallreaktion, Forensik und Erpressung",
      "vector_beta_desc": "Direkter Kapitalabfluss durch Krisenmanagement und DFIR-Experten.",
      "vector_gamma_label": "Meldepflichten und Kundenabwanderung",
      "vector_gamma_desc": "Wirtschaftlicher Verlust durch Vertrauensbruch und Identitätsschutzpflichten.",
      "prioritization_rationale": "Fokus auf Zero Trust, Eindämmung lateraler Bewegungen und PAM."
    }
  },
  "ja": {
    "AVAILABILITY_OUTAGE": {
      "methodology_intro": "{domain_name} の数理的露出は Open FAIR™ 可用性・サービス停止レセプターを介してモデル化され、計画外のサービス停止による財務的影響を捉えます。",
      "formula_expression": "ALE = LEF × (ダウンタイム期間 × 1時間あたり損失率 + 復旧労力 + SLAペナルティ)",
      "vector_alpha_label": "直接的な取引損失およびSLA違反損失",
      "vector_alpha_desc": "重要資産におけるサービス利用不可による財務的影響。",
      "vector_beta_label": "緊急対策室および復旧エンジニアリング労力",
      "vector_beta_desc": "状態復元および根本原因解決に必要な計画外のエンジニアリング労力。",
      "vector_gamma_label": "二次的な顧客離れとブランド価値の低下",
      "vector_gamma_desc": "長期化するシステム不安定性に起因する二次的な商業的損失。",
      "prioritization_rationale": "改善順序は、MTTRの削減と影響範囲の封じ込めに厳密に従います。"
    },
    "CAPITAL_INEFFICIENCY": {
      "methodology_intro": "{domain_name} の数理的露出は Open FAIR™ 資本非効率性レセプターを介してモデル化され、未最適化リソースによる価値の漏出を捕捉します。",
      "formula_expression": "ALE = LEF × (クラウド無駄遣い + ソフトウェアライセンス過剰 + FinOps手戻り)",
      "vector_alpha_label": "未稼働コンピュートおよびゾンビインフラの浪費",
      "vector_alpha_desc": "過剰なアーキテクチャおよびアイドル状態のクラウドインスタンスによる資金流出。",
      "vector_beta_label": "非最適なライセンス管理および割引の逸失",
      "vector_beta_desc": "未使用のソフトウェアライセンスや予約済みインスタンスの活用失敗による資本損失。",
      "vector_gamma_label": "アーキテクチャの手戻りおよびFinOps修正",
      "vector_gamma_desc": "近代化の遅れに起因する摩擦コストとガバナンス対応費。",
      "prioritization_rationale": "即時のOpEx回収とライセンスコンプライアンスの遵守を優先します。"
    },
    "PRODUCTIVITY_TOIL": {
      "methodology_intro": "{domain_name} の数理的露出は Open FAIR™ 生産性低下・トイル レセプターを介してモデル化され、従業員の摩擦を定量化します。",
      "formula_expression": "ALE = LEF × (エンジニア待機時間 + タイムトゥマーケット遅延 + 手動サポートトイル)",
      "vector_alpha_label": "従業員およびエンジニアの累積アイドル時間",
      "vector_alpha_desc": "貧弱なツール環境によるコンテキストスイッチや待機状態の摩擦。",
      "vector_beta_label": "タイムトゥマーケットの遅延（機会費用）",
      "vector_beta_desc": "機能リリース速度の低下やデプロイのボトルネックによる商業的機会費用。",
      "vector_gamma_label": "手動対応トイルおよびチケット管理のオーバーヘッド",
      "vector_gamma_desc": "手動でのサポート対応や繰り返しの運用作業で消費される人的資本。",
      "prioritization_rationale": "改善順序は、ワークフロー自動化と摩擦の排除を最優先します。"
    },
    "REGULATORY_AND_BREACH": {
      "methodology_intro": "{domain_name} の数理的露出は Open FAIR™ 規制違反レセプターを介してモデル化され、法定罰金やフォレンジック危機シナリオを評価します。",
      "formula_expression": "ALE = LEF × (法定罰金 + フォレンジック対応・恐喝 + 評判の低下)",
      "vector_alpha_label": "法定罰金および法的責任",
      "vector_alpha_desc": "執行裁量を加味した規制当局の制裁（NIS2、GDPR、DORA）の経験的予測。",
      "vector_beta_label": "インシデント対応、フォレンジック、および恐喝",
      "vector_beta_desc": "ランサムウェア対応および専門DFIR動員による直接的な資本流出。",
      "vector_gamma_label": "義務的通知および顧客離れ",
      "vector_gamma_desc": "ステークホルダーの信頼失墜や義務的な信用監視に起因する商業的損失。",
      "prioritization_rationale": "ラテラルムーブメントの封じ込め、ゼロトラストセグメンテーション、およびPAMに焦点を当てます。"
    }
  }
}

# The engine uses "executive_summary_narrative" as a pseudo-locale for internal generation
# But we only need to inject annex_ch4_receptors into en, es, pt, fr, de, ja.

for lang, receptors in CH4_RECEPTORS.items():
    if lang in data:
        data[lang]["annex_ch4_receptors"] = receptors

path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
