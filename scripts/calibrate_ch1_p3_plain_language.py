#!/usr/bin/env python3
"""Calibrate tomo_ch1_p3 to plain executive language across all 6 locales."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = REPO_ROOT / "engine_config" / "locales.json"

CALIBRATED_P3 = {
    "es": "En términos económicos prácticos, mantener la infraestructura en su estado actual supone asumir un coste de riesgo estimado en {formatted_ale} al año, derivado de la suma de ineficiencias operativas, duplicidades contractuales y la probabilidad estadística de sufrir averías o interrupciones de servicio. En un año especialmente adverso donde coincidan varios fallos críticos de forma simultánea, este impacto económico podría escalar hasta los {formatted_p90}. El diagnóstico detallado por áreas técnicas que se expone a continuación permite a la dirección priorizar las inversiones de modernización exactamente donde mayor riesgo se elimina por cada euro invertido.",
    "en": "In practical business terms, maintaining the current infrastructure unchanged means carrying an estimated annual risk cost of {formatted_ale}, driven by operational friction, contract duplication, and the statistical probability of technical outages. In an exceptionally adverse year where multiple critical failures strike concurrently, this economic impact could escalate up to {formatted_p90}. The detailed domain assessment that follows equips leadership to direct modernization investments precisely where they eliminate the greatest risk per unit of capital.",
    "pt": "Em termos econômicos práticos, manter a infraestrutura em seu estado atual significa assumir um custo de risco estimado em {formatted_ale} por ano, decorrente de ineficiências operacionais, duplicidades contratuais e da probabilidade estatística de interrupções de serviço. Em um ano excepcionalmente adverso, com a ocorrência simultânea de falhas críticas, esse impacto financeiro pode atingir {formatted_p90}. O diagnóstico detalhado por áreas permite direcionar os investimentos de modernização onde maior risco for eliminado por cada recurso aplicado.",
    "fr": "En termes économiques concrets, maintenir l'infrastructure en l'état équivaut à supporter un coût de risque annuel estimé à {formatted_ale}, résultant des inefficacités opérationnelles, des doublons contractuels et de la probabilité statistique de pannes. Lors d'une année particulièrement défavorable cumulant plusieurs défaillances critiques, cet impact économique pourrait s'élever à {formatted_p90}. Le diagnostic détaillé par domaine permet d'orienter les investissements de modernisation là où la réduction du risque est la plus forte pour chaque budget engagé.",
    "de": "In betriebswirtschaftlicher Hinsicht bedeutet das Beibehalten der aktuellen Infrastruktur ein geschätztes jährliches Risikokostenvolumen von {formatted_ale}, bedingt durch betriebliche Reibungsverluste, Lizenzüberschneidungen und die statistische Ausfallwahrscheinlichkeit. In einem besonders ungünstigen Jahr mit mehreren gleichzeitigen kritischen Störungen könnte dieser Schaden auf bis zu {formatted_p90} ansteigen. Die nachfolgende detaillierte Analyse ermöglicht es, Modernisierungsinvestitionen gezielt dort einzusetzen, wo pro investiertem Betrag das größte Risiko abgebaut wird.",
    "ja": "実質的な経済的観点から言えば、現在のインフラ構成を維持することは、運用の非効率性、ライセンスの重複、および障害の発生確率に伴い、年間約 {formatted_ale} の潜在的なリスクコストを負担していることを意味します。重大なシステム障害が複数同時に発生する特に不利な年においては、この経済的損失は最大で {formatted_p90} に達する可能性があります。以下の各ドメイン別詳細診断により、限られた予算で最大のリスク低減効果が得られる領域へ投資を優先配分することが可能になります。",
}


def main() -> None:
    with open(LOCALES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for loc, text in CALIBRATED_P3.items():
        if loc in data:
            data[loc]["tomo_ch1_p3"] = text

    with open(LOCALES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Successfully updated tomo_ch1_p3 across all 6 locales!")


if __name__ == "__main__":
    main()
