#!/usr/bin/env python3
"""Eradicate hardcoded numbers from locales.json templates and enforce dynamic placeholders."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = REPO_ROOT / "engine_config" / "locales.json"

DYNAMIC_TEMPLATES = {
    "es": {
        "tomo_ch3_p90_1": "Mientras que el incidente mayor analizado en la Sección 3.2 representa una interrupción severa pero aislada en un centro operacional clave (con un coste estimado de {single_event_cost}), el modelo estocástico de Monte Carlo simula además la cola anual de pérdidas agregadas de la cartera tecnológica completa.",
        "tomo_ch3_p90_4": "A un horizonte acumulado de 3 años sin ejecutar las actuaciones de remediación arquitectónica, la pérdida esperada se eleva a {var_3y_expected}, alcanzando un valor en riesgo acumulado a 3 años (VaR 3Y P90) de {var_3y_tail} en un escenario continuado de estrés operativo e incidentes graves.",
        "hours_unit_short": "h",
    },
    "en": {
        "tomo_ch3_p90_1": "While the major incident examined in Section 3.2 represents a severe isolated outage at a primary operational facility (with an estimated single-event cost of {single_event_cost}), the Monte Carlo stochastic model also simulates the annual aggregate loss distribution tail across the entire technology portfolio.",
        "tomo_ch3_p90_4": "Over a cumulative 3-year horizon without architectural remediation, expected baseline losses accumulate to {var_3y_expected}, climbing to a 3-year value-at-risk (VaR 3Y P90) of {var_3y_tail} under persistent operational stress and severe concurrent incidents.",
        "hours_unit_short": "hrs",
    },
    "pt": {
        "tomo_ch3_p90_1": "Enquanto o incidente grave analisado na Seção 3.2 representa uma interrupção severa, mas isolada em uma instalação operacional crítica (com um custo estimado de {single_event_cost}), o modelo estocástico de Monte Carlo também simula a cauda anual de perdas agregadas de todo o portfólio de tecnologia.",
        "tomo_ch3_p90_4": "Em um horizonte cumulativo de 3 anos sem remediação arquitetônica, as perdas esperadas acumulam {var_3y_expected}, atingindo um valor em risco acumulado em 3 anos (VaR 3Y P90) de {var_3y_tail} sob estresse operacional contínuo.",
        "hours_unit_short": "h",
    },
    "fr": {
        "tomo_ch3_p90_1": "Alors que l'incident majeur examiné à la Section 3.2 représente une panne sévère mais isolée sur un site opérationnel clé (avec un coût estimé de {single_event_cost}), le modèle stochastique de Monte Carlo simule également la queue de distribution annuelle des pertes agrégées de l'ensemble du portefeuille.",
        "tomo_ch3_p90_4": "Sur un horizon cumulé de 3 ans sans remédiation architecturale, la perte attendue s'élève à {var_3y_expected}, atteignant une valeur à risque cumulée à 3 ans (VaR 3Y P90) de {var_3y_tail} sous stress opérationnel continu.",
        "hours_unit_short": "h",
    },
    "de": {
        "tomo_ch3_p90_1": "Während der in Abschnitt 3.2 untersuchte Großvorfall einen schwerwiegenden, aber isolierten Ausfall an einem zentralen Betriebsstandort darstellt (mit geschätzten Einzelkosten von {single_event_cost}), simuliert das stochastische Monte-Carlo-Modell auch das jährliche Gesamtschadensrisiko des gesamten Technologieportfolios.",
        "tomo_ch3_p90_4": "Über einen kumulierten 3-Jahres-Horizont ohne Sanierungsmaßnahmen steigen die erwarteten Basisverluste auf {var_3y_expected} und erreichen unter anhaltendem Betriebsstress einen 3-Jahres-Value-at-Risk (VaR 3Y P90) von {var_3y_tail}.",
        "hours_unit_short": "Std.",
    },
    "ja": {
        "tomo_ch3_p90_1": "セクション3.2で検証した重大インシデントは主要拠点での個別停止（推定損失額: {single_event_cost}）を示していますが、モンテカルロ確率モデルはポートフォリオ全体における年間の累積テールリスクも同時にシミュレーションしています。",
        "tomo_ch3_p90_4": "アーキテクチャの是正を実施しない3年間の累積期間において、期待ベースライン損失は {var_3y_expected} に達し、重大インシデントが連続発生した場合の3年間バリュー・アット・リスク（VaR 3Y P90）は {var_3y_tail} に達します。",
        "hours_unit_short": "時間",
    },
}


def main() -> None:
    with open(LOCALES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for loc, keys_dict in DYNAMIC_TEMPLATES.items():
        if loc in data:
            for k, val in keys_dict.items():
                data[loc][k] = val

    with open(LOCALES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Successfully parameterized locales.json templates with dynamic placeholders!")


if __name__ == "__main__":
    main()
