"""Inject localized FinOps P90 callout strings across all 6 languages in locales.json."""

import json
from pathlib import Path

p = Path("engine_config/locales.json")
data = json.loads(p.read_text(encoding="utf-8"))

FINOPS_P90_LOCALES = {
    "es": {
        "p90_callout_finops_p1": "Para evaluar el límite de resistencia fiscal y operativa de este dominio, el modelo simula un escenario de contingencia grave en el que coinciden múltiples desalineaciones contractuales y arquitectónicas: {trigger_text}.",
        "p90_callout_finops_p2": "Ante un desvío presupuestario de esta magnitud, la regularización exige renegociar compromisos de volumen multianuales, implantar compuertas de detección de anomalías FinOps y auditar la dispersión de recursos no asignados. Bajo las prácticas de gobierno actuales, estabilizar el gasto requeriría una ventana de remediación de hasta {p90_rec_hours_str} meses.",
        "p90_callout_finops_p3": "La exposición financiera total de este escenario alcanza {p90_contingency_str}. Este impacto se desglosa en: {direct_stoppage_str} por desvío directo de consumo bajo demanda no optimizado, y {secondary_spend_str} en ajustes extraordinarios de regularización de licencias y consultoría especializada de FinOps."
    },
    "en": {
        "p90_callout_finops_p1": "To evaluate the practical fiscal resilience limit of this capability tower, the model simulates a severe, plausible scenario in which multiple contractual and architectural commitment lapses occur simultaneously: {trigger_text}.",
        "p90_callout_finops_p2": "In a compounding budgetary drift of this magnitude, recovery requires renegotiating multi-year volume commitments, establishing automated FinOps anomaly gates, and auditing unallocated cloud resource sprawl across teams. Under current governance baselines, fully stabilizing expenditure and enforcing tag compliance would require a remediation window of up to {p90_rec_hours_str} months.",
        "p90_callout_finops_p3": "The total financial exposure of this scenario reaches {p90_contingency_str}. This impact breaks down clearly into two categories: {direct_stoppage_str} in direct unhedged on-demand compute drift and cloud budget overruns, and {secondary_spend_str} in extraordinary vendor licensing true-up adjustments and specialized FinOps consultancy intervention."
    },
    "pt": {
        "p90_callout_finops_p1": "Para avaliar o limite de resiliência fiscal e operacional deste domínio, o modelo simula um cenário adverso no qual coincidem múltiplos desvios contratuais e arquiteturais: {trigger_text}.",
        "p90_callout_finops_p2": "Diante de um desvio orçamentário dessa magnitude, a regularização exige renegociação de compromissos contratuais de volume e auditoria de recursos dispersos. Sob a governança atual, estabilizar os custos exigiria uma janela de até {p90_rec_hours_str} meses.",
        "p90_callout_finops_p3": "A exposição financeira total deste cenário atinge {p90_contingency_str}, dividida em: {direct_stoppage_str} em desvio de consumo sob demanda e {secondary_spend_str} em ajustes extraordinários de licenciamento e consultoria FinOps."
    },
    "fr": {
        "p90_callout_finops_p1": "Pour évaluer la limite de résilience budgétaire de ce domaine, le modèle simule un scénario sévère où coïncident de multiples écarts contractuels et architecturaux: {trigger_text}.",
        "p90_callout_finops_p2": "Face à une dérive budgétaire d'une telle ampleur, la régularisation nécessite de renégocier les engagements pluriannuels et d'auditer les ressources orphelines. Stabiliser les dépenses nécessiterait jusqu'à {p90_rec_hours_str} mois.",
        "p90_callout_finops_p3": "L'exposition financière totale de ce scénario atteint {p90_contingency_str}, ventilée en: {direct_stoppage_str} en surcoûts directs de calcul à la demande et {secondary_spend_str} en régularisations de licences et conseil FinOps spécialisé."
    },
    "de": {
        "p90_callout_finops_p1": "Um die steuerliche und betriebliche Widerstandsfähigkeit zu bewerten, simuliert das Modell ein schweres Szenario mit vertraglichen und architektonischen Abweichungen: {trigger_text}.",
        "p90_callout_finops_p2": "Bei einer Budgetabweichung dieser Größenordnung erfordert die Konsolidierung Neuverhandlungen von Volumenverträgen und Audits. Die Bereinigung würde bis zu {p90_rec_hours_str} Monate erfordern.",
        "p90_callout_finops_p3": "Die finanzielle Gesamtexposition beträgt {p90_contingency_str}, aufgeteilt in: {direct_stoppage_str} für direkte On-Demand-Kostenüberschreitungen und {secondary_spend_str} für Lizenznachzahlungen und FinOps-Beratung."
    },
    "ja": {
        "p90_callout_finops_p1": "本ドメインの財務的レジリエンス限界を評価するため、複数の契約上およびアーキテクチャ上の逸脱が同時に発生する重大シナリオをシミュレートします: {trigger_text}。",
        "p90_callout_finops_p2": "この規模の予算超過が発生した場合、長期契約の再交渉および遊休クラウドリソースの監査が必要です。支出の完全な安定化には最大 {p90_rec_hours_str} ヶ月の是正期間を要します。",
        "p90_callout_finops_p3": "このシナリオの総財務エクスポージャーは {p90_contingency_str} に達し、{direct_stoppage_str} のオンデマンド費用超過と、{secondary_spend_str} の追加ライセンス清算およびFinOps専門支援費用に分類されます。"
    }
}

for lang, strings in FINOPS_P90_LOCALES.items():
    if lang in data:
        data[lang].update(strings)

p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("✓ Successfully injected localized FinOps P90 strings across all 6 languages.")
