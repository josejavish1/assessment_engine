"""Sanitize e-commerce retail bias and software jargon from locales.json across all 6 languages."""

import json
from pathlib import Path

p = Path("engine_config/locales.json")
data = json.loads(p.read_text(encoding="utf-8"))

HIGH_TEMPO_TEXTS = {
    "es": "Exposición Operativa de Alta Intensidad (β={beta:.2f}): La disponibilidad continua es crítica para evitar la interrupción inmediata de las operaciones de negocio y la pérdida directa de ingresos comerciales.",
    "en": "High-Tempo Operational Exposure (β={beta:.2f}): Continuous service availability is critical to prevent immediate business disruption and direct revenue erosion.",
    "pt": "Exposição Operacional de Alto Ritmo (β={beta:.2f}): A disponibilidade contínua é crítica para evitar a interrupção imediata das operações de negócio e perda direta de receitas comerciais.",
    "fr": "Exposition Opérationnelle à Haut Rythme (β={beta:.2f}): La disponibilité continue est critique pour éviter l'interruption immédiate des opérations et la perte directe de revenus.",
    "de": "Hochfrequente operative Exposition (β={beta:.2f}): Kontinuierliche Serviceverfügbarkeit ist kritisch, um sofortige Betriebsunterbrechungen und direkte Umsatzeinbußen zu verhindern.",
    "ja": "高頻度オペレーショナルエクスポージャー（β={beta:.2f}）: 業務オペレーションの即時中断および直接的な収益損失を防ぐため、継続的なサービス可用性が極めて重要です。"
}

TOIL_FORMULAS = {
    "es": "ALE = LEF × (Tiempo_Inactivo_Operativo + Retraso_Entregas + Toil_Soporte_Manual)",
    "en": "ALE = LEF × (Operational_Idle_Time + Delivery_Bottlenecks + Manual_Support_Toil)",
    "pt": "ALE = LEF × (Tempo_Inativo_Operacional + Gargalos_Entrega + Toil_Suporte_Manual)",
    "fr": "ALE = LEF × (Temps_Inactif_Opérationnel + Goulots_Livraison + Toil_Support_Manuel)",
    "de": "ALE = LEF × (Operative_Ausfallzeit + Lieferengpässe + Manueller_Support_Toil)",
    "ja": "ALE = LEF × (業務待機損失時間 + プロセス遅延 + 手作業サポートトイル)"
}

TOIL_BETA_LABELS = {
    "es": "Retraso en Flujos Operativos y Entrega",
    "en": "Operational Bottlenecks & Delivery Delays",
    "pt": "Gargalos em Fluxos Operacionais e Entrega",
    "fr": "Goulots d'Étranglement et Retards de Livraison",
    "de": "Operative Engpässe & Lieferverzögerungen",
    "ja": "業務ボトルネックおよび納品遅延"
}

TOIL_ALPHA_LABELS = {
    "es": "Fricción Acumulada e Ineficiencias de Espera",
    "en": "Cumulative Workforce Friction & Idle Wait Time",
    "pt": "Fricção Acumulada e Ineficiências de Espera",
    "fr": "Friction Cumulée et Inefficacités d'Attente",
    "de": "Kumulierte Reibungsverluste & Wartezeiten",
    "ja": "累積業務摩擦および待機時間損失"
}

for lang in data:
    if lang in HIGH_TEMPO_TEXTS and "annex_ch4_context_beta" in data[lang]:
        data[lang]["annex_ch4_context_beta"]["high_tempo"] = HIGH_TEMPO_TEXTS[lang]
    
    if lang in TOIL_FORMULAS and "annex_ch4_receptors" in data[lang]:
        rec = data[lang]["annex_ch4_receptors"].get("PRODUCTIVITY_TOIL", {})
        if rec:
            rec["formula_expression"] = TOIL_FORMULAS[lang]
            rec["vector_beta_label"] = TOIL_BETA_LABELS[lang]
            rec["vector_alpha_label"] = TOIL_ALPHA_LABELS[lang]

p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("✓ Successfully sanitized e-commerce phrasing and software jargon across all 6 languages.")
