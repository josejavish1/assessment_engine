"""Add canonical Table 5 Open FAIR localization keys across all 6 supported locales in engine_config/locales.json."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = ROOT / "engine_config" / "locales.json"

TABLE5_KEYS = {
    "en": {
        "tomo_table5_col_domain": "Technology Domain",
        "tomo_table5_col_cmmi": "CMMI Maturity",
        "tomo_table5_col_standalone": "Standalone Bottom-Up ALE",
        "tomo_table5_col_adjustment": "Overlap & Absorption Adjustment",
        "tomo_table5_col_euler_net": "Net Portfolio Contribution (Euler ALE)",
        "tomo_table5_col_share_pct": "% of Total Risk",
        "tomo_table5_row_subtotal_gross": "SUBTOTAL GROSS UNDIVERSIFIED",
        "tomo_table5_row_copula_adjustment": "ACTUARIAL ADJUSTMENT (COPULA)",
        "tomo_table5_badge_copula_overlap": "[-{overlap_pct}% Copula Overlap]",
        "tomo_table5_row_total_net": "TOTAL NET CONSOLIDATED RISK",
        "tomo_table5_symbol_na": "—",
        "tomo_table5_bridge_explanation": "Actuarial Portfolio Bridge: Standalone domain exposures evaluate each area in isolation. The Copula Overlap & Absorption Adjustment captures multi-risk correlation and entity-level loss limits, deriving the true Net Portfolio Contribution (Euler allocation) where relative weights sum strictly to 100.0%."
    },
    "es": {
        "tomo_table5_col_domain": "Dominio Tecnológico",
        "tomo_table5_col_cmmi": "Madurez CMMI",
        "tomo_table5_col_standalone": "Riesgo Independiente (Standalone Bottom-Up)",
        "tomo_table5_col_adjustment": "Ajuste por Solapamiento y Capacidad de Absorción",
        "tomo_table5_col_euler_net": "Contribución Neta al Portafolio (Euler ALE)",
        "tomo_table5_col_share_pct": "% del Riesgo Total",
        "tomo_table5_row_subtotal_gross": "SUBTOTAL EXPOSICIÓN BRUTA NO DIVERSIFICADA",
        "tomo_table5_row_copula_adjustment": "AJUSTE ACTUARIAL (DIVERSIFICACIÓN CÓPULA)",
        "tomo_table5_badge_copula_overlap": "[-{overlap_pct}% Correlación Cópula]",
        "tomo_table5_row_total_net": "TOTAL CONSOLIDADO DEL GRUPO",
        "tomo_table5_symbol_na": "—",
        "tomo_table5_bridge_explanation": "Conciliación Actuarial de Portafolio: Las exposiciones independientes evalúan cada dominio de forma aislada. El Ajuste por Solapamiento y Capacidad de Absorción (Cópula) modela la correlación multirriesgo y los límites de absorción corporativos, derivando la Contribución Neta al Portafolio (asignación de Euler) donde la suma de pesos relativos totaliza exactamente el 100,0%."
    },
    "pt": {
        "tomo_table5_col_domain": "Domínio Tecnológico",
        "tomo_table5_col_cmmi": "Maturidade CMMI",
        "tomo_table5_col_standalone": "Risco Independente (Standalone Bottom-Up)",
        "tomo_table5_col_adjustment": "Ajuste por Sobreposição e Capacidade de Absorção",
        "tomo_table5_col_euler_net": "Contribuição Líquida ao Portfólio (Euler ALE)",
        "tomo_table5_col_share_pct": "% do Risco Total",
        "tomo_table5_row_subtotal_gross": "SUBTOTAL EXPOSIÇÃO BRUTA NÃO DIVERSIFICADA",
        "tomo_table5_row_copula_adjustment": "AJUSTE ATUARIAL (DIVERSIFICAÇÃO CÓPULA)",
        "tomo_table5_badge_copula_overlap": "[-{overlap_pct}% Correlação Cópula]",
        "tomo_table5_row_total_net": "TOTAL CONSOLIDADO DO GRUPO",
        "tomo_table5_symbol_na": "—",
        "tomo_table5_bridge_explanation": "Conciliação Atuarial de Portfólio: As exposições independentes avaliam cada domínio de forma isolada. O Ajuste por Sobreposição e Absorção (Cópula) modela a correlação multirrisco e os limites de solvência corporativos, derivando a Contribuição Líquida ao Portfólio (alocação de Euler) com pesos que somam estritamente 100,0%."
    },
    "fr": {
        "tomo_table5_col_domain": "Domaine Technologique",
        "tomo_table5_col_cmmi": "Maturité CMMI",
        "tomo_table5_col_standalone": "Risque Indépendant (Standalone Bottom-Up)",
        "tomo_table5_col_adjustment": "Ajustement de Chevauchement et d'Absorption",
        "tomo_table5_col_euler_net": "Contribution Nette au Portefeuille (Euler ALE)",
        "tomo_table5_col_share_pct": "% du Risque Total",
        "tomo_table5_row_subtotal_gross": "SOUS-TOTAL EXPOSITION BRUTE NON DIVERSIFIÉE",
        "tomo_table5_row_copula_adjustment": "AJUSTEMENT ACTUARIEL (DIVERSIFICATION COPULE)",
        "tomo_table5_badge_copula_overlap": "[-{overlap_pct}% Corrélation Copule]",
        "tomo_table5_row_total_net": "TOTAL CONSOLIDÉ DU GROUPE",
        "tomo_table5_symbol_na": "—",
        "tomo_table5_bridge_explanation": "Réconciliation Actuarielle de Portefeuille: Les expositions indépendantes évaluent chaque domaine isolément. L'Ajustement de Chevauchement et d'Absorption modélise la corrélation multirisque et les plafonds d'absorption, dérivant la Contribution Nette au Portefeuille (allocation d'Euler) dont la somme des poids totalise strictement 100,0%."
    },
    "de": {
        "tomo_table5_col_domain": "Technologiedomäne",
        "tomo_table5_col_cmmi": "CMMI-Reifegrad",
        "tomo_table5_col_standalone": "Unabhängiges Bottom-Up-ALE",
        "tomo_table5_col_adjustment": "Überlappungs- & Absorptionsanpassung",
        "tomo_table5_col_euler_net": "Netto-Portfoliometrik (Euler-ALE)",
        "tomo_table5_col_share_pct": "% des Gesamtrisikos",
        "tomo_table5_row_subtotal_gross": "ZWISCHENSUMME BRUTTO UNVERSICHERT",
        "tomo_table5_row_copula_adjustment": "AKTUARIELLE ANPASSUNG (COPULA-DIVERSIFIKATION)",
        "tomo_table5_badge_copula_overlap": "[-{overlap_pct}% Copula-Korrelation]",
        "tomo_table5_row_total_net": "KONSOLIDIERTES GESAMTRISIKO",
        "tomo_table5_symbol_na": "—",
        "tomo_table5_bridge_explanation": "Aktuarielle Portfolioüberleitung: Die Standalone-Expositionen bewerten jede Domäne isoliert. Die Überlappungs- und Absorptionsanpassung modelliert die Multirisikokorrelation und Absorptionsgrenzen, woraus der Netto-Portfoliobeitrag (Euler-Allokation) abgeleitet wird, dessen Gewichte exakt 100,0% ergeben."
    },
    "ja": {
        "tomo_table5_col_domain": "技術ドメイン",
        "tomo_table5_col_cmmi": "CMMI成熟度",
        "tomo_table5_col_standalone": "独立ボトムアップALE",
        "tomo_table5_col_adjustment": "重複・吸収調整",
        "tomo_table5_col_euler_net": "純ポートフォリオ寄与（オイラーALE）",
        "tomo_table5_col_share_pct": "総リスク比率",
        "tomo_table5_row_subtotal_gross": "未分散総エクスポージャー小計",
        "tomo_table5_row_copula_adjustment": "数理調整（コピュラ分散効果）",
        "tomo_table5_badge_copula_overlap": "[-{overlap_pct}% コピュラ相関]",
        "tomo_table5_row_total_net": "グループ連結総リスク",
        "tomo_table5_symbol_na": "—",
        "tomo_table5_bridge_explanation": "ポートフォリオ数理調整ブリッジ：独立ドメインエクスポージャーは各領域を個別に評価します。重複および吸収調整（コピュラ）は、マルチリスクの相関関係と組織の損失吸収限界をモデル化し、純ポートフォリオ寄与（オイラー配分）を導出します。相対比率の合計は厳密に100.0%になります。"
    }
}


def add_keys() -> None:
    data = json.loads(LOCALES_PATH.read_text(encoding="utf-8"))
    for lang, keys_dict in TABLE5_KEYS.items():
        if lang in data:
            data[lang].update(keys_dict)

    LOCALES_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("✓ Added canonical Table 5 Open FAIR localization keys across all 6 locales.")


if __name__ == "__main__":
    add_keys()
