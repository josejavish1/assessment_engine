#!/usr/bin/env python3
"""Update Chapter 3 strings in locales.json after removing Section 3.2."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = REPO_ROOT / "engine_config" / "locales.json"

UPDATES = {
    "es": {
        "tomo_sec32_heatmap_title": "3.2. Mapa de Riesgos Corporativos (Open FAIR™)",
        "tomo_sec33_risk_cards_title": "3.3. Principales Riesgos Operativos (Top 5)",
        "tomo_ch3_p90_title": "3.4. Riesgo de Cola Anual Corporativo (P90 de Cartera)",
        "tomo_ch3_loss_composition_note": "Nota metodológica sobre la composición del impacto: En consonancia con la metodología Open FAIR™, las pérdidas económicas anualizadas no representan únicamente costes indirectos de productividad. Ante la concurrencia de incidencias graves, aproximadamente el 50% de la exposición se traduce en salidas directas de caja asociadas a costes extraordinarios de recuperación: contratación de soporte de emergencia 24x7 de fabricantes fuera de contrato, adquisición prioritaria de equipamiento en mercado spot y peritaje forense para la restauración de datos.",
        "tomo_ch3_p90_1": "Mientras que las fichas de riesgo detalladas en la Sección 3.3 evalúan el impacto de eventos individuales severos en centros operacionales clave, el modelo estocástico de Monte Carlo simula además la cola anual de pérdidas agregadas de la cartera tecnológica completa.",
    },
    "en": {
        "tomo_sec32_heatmap_title": "3.2. Corporate Risk Heatmap (Open FAIR™)",
        "tomo_sec33_risk_cards_title": "3.3. Top Corporate Systemic Risk Cards (Top 5)",
        "tomo_ch3_p90_title": "3.4. Corporate Annual Portfolio Tail Risk (P90)",
        "tomo_ch3_loss_composition_note": "Methodological Note on Loss Composition: Under Open FAIR™ standards, modeled annualized loss exposure does not merely reflect soft productivity losses. In severe incident scenarios, approximately 50% of financial exposure translates into hard cash outflows for emergency recovery: expedited 24x7 Tier-3 vendor interventions, spot-market hardware replacement, and forensic database restoration.",
        "tomo_ch3_p90_1": "While the individual risk cards detailed in Section 3.3 evaluate severe standalone outage events across primary operational facilities, the Monte Carlo stochastic model also simulates the annual aggregate loss distribution tail across the entire technology portfolio.",
    },
    "pt": {
        "tomo_sec32_heatmap_title": "3.2. Mapa de Riscos Corporativos (Open FAIR™)",
        "tomo_sec33_risk_cards_title": "3.3. Principais Riscos Operacionais (Top 5)",
        "tomo_ch3_p90_title": "3.4. Risco de Cauda Anual Corporativo (P90 da Carteira)",
        "tomo_ch3_loss_composition_note": "Nota metodológica sobre a composição do impacto: De acordo com a metodologia Open FAIR™, as perdas econômicas anualizadas não representam apenas custos indiretos de produtividade. Em incidentes graves, cerca de 50% da exposição se converte em saídas diretas de caixa para recuperação de emergência.",
        "tomo_ch3_p90_1": "Enquanto os cartões de risco detalhados na Seção 3.3 avaliam o impacto de eventos individuais severos, o modelo estocástico de Monte Carlo simula a cauda anual de perdas agregadas de todo o portfólio.",
    },
    "fr": {
        "tomo_sec32_heatmap_title": "3.2. Carte Thermique des Risques (Open FAIR™)",
        "tomo_sec33_risk_cards_title": "3.3. Principaux Risques Opérationnels (Top 5)",
        "tomo_ch3_p90_title": "3.4. Risque de Queue Annuel Corporatif (P90)",
        "tomo_ch3_loss_composition_note": "Note méthodologique sur la composition de l'impact : Selon la méthodologie Open FAIR™, les pertes annualisées modélisées ne représentent pas uniquement des coûts indirects de productivité. Lors d'incidents majeurs, environ 50% de l'exposition se traduit par des décaissements directs d'urgence.",
        "tomo_ch3_p90_1": "Alors que les fiches de risque détaillées à la Section 3.3 évaluent l'impact d'événements majeurs isolés, le modèle stochastique de Monte Carlo simule la queue de distribution annuelle des pertes agrégées du portefeuille.",
    },
    "de": {
        "tomo_sec32_heatmap_title": "3.2. Unternehmensrisiko-Heatmap (Open FAIR™)",
        "tomo_sec33_risk_cards_title": "3.3. Wichtigste operationelle Risiken (Top 5)",
        "tomo_ch3_p90_title": "3.4. Jährliches Portfolio-Tail-Risk (P90)",
        "tomo_ch3_loss_composition_note": "Methodischer Hinweis zur Schadenszusammensetzung: Gemäß Open FAIR™ stellen die jährlichen Verluste nicht nur Produktivitätseinbußen dar. Bei schweren Störungen entsprechen rund 50% direkten Notfallauszahlungen für Wiederherstellung und Hardwarebeschaffung.",
        "tomo_ch3_p90_1": "Während die in Abschnitt 3.3 detaillierten Risikokarten schwere Einzelereignisse bewerten, simuliert das stochastische Monte-Carlo-Modell das jährliche Gesamtschadensrisiko des Technologieportfolios.",
    },
    "ja": {
        "tomo_sec32_heatmap_title": "3.2. 全社リスクヒートマップ（Open FAIR™）",
        "tomo_sec33_risk_cards_title": "3.3. 主要システムリスク（上位5項目）",
        "tomo_ch3_p90_title": "3.4. 年間ポートフォリオ・テールリスク（P90）",
        "tomo_ch3_loss_composition_note": "損失構成に関する方法論的注記：Open FAIR™フレームワークに基づき、年間の想定損失額は単なる生産性損失だけでなく、深刻な障害時における緊急復旧やスポット調達に伴う約50%の直接的な現金支出を含んでいます。",
        "tomo_ch3_p90_1": "セクション3.3で詳述した各リスクカードは個別重大インシデントの影響を評価する一方、モンテカルロ確率モデルはポートフォリオ全体における年間の累積テールリスクをシミュレーションしています。",
    },
}


def main() -> None:
    with open(LOCALES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for loc, items in UPDATES.items():
        if loc in data:
            for k, val in items.items():
                data[loc][k] = val

    with open(LOCALES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Successfully updated Chapter 3 keys across all 6 locales!")


if __name__ == "__main__":
    main()
