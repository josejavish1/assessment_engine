#!/usr/bin/env python3
"""Remediate ungrounded speculative tools from cross_cutting_debt templates in engine_config/locales.json."""

from __future__ import annotations

import json
from pathlib import Path

LOCALES_PATH = Path(__file__).resolve().parents[1] / "engine_config/locales.json"

TEXT_BY_LANG = {
    "es": {
        "p1": "**1. Ausencia de Telemetría Continua y Capacidad No Monitorizada:** La gestión de capacidad eléctrica y térmica carece de monitorización telemétrica digital en tiempo real en cuadros generales y regletas de rack (iPDU), impidiendo conocer el margen real disponible de potencia y dinamismo térmico al desplegar nuevas cargas de cómputo.",
        "p3": "**3. Procedimientos de Control y Permisos de Trabajo No Estructurados:** Las rondas de mantenimiento preventivo, los ensayos de conmutación de acometida y el control de accesos de contratas externas carecen de flujos formales de autorización digital y trazabilidad inmutable, generando una brecha de conformidad ante las exigencias de gobierno y auditoría de la directiva europea NIS2.",
    },
    "en": {
        "p1": "**1. Lack of Continuous Telemetry & Unmonitored Electrical Capacity:** Electrical and thermal capacity management lacks digital real-time telemetry across distribution panels and intelligent rack PDUs, impairing operational visibility into available power headroom when provisioning workloads.",
        "p3": "**3. Unstructured Maintenance Procedures & Work Permit Gaps (ePtW):** Preventive maintenance rounds, generator failover tests, and third-party contractor room access lack formal digital authorization workflows and immutable audit trails, creating compliance gaps against NIS2 governance requirements.",
    },
    "pt": {
        "p1": "**1. Ausência de Telemetria Contínua e Capacidade Não Monitorada:** O gerenciamento de capacidade elétrica e térmica carece de monitoramento telemétrico digital em tempo real em quadros gerais e réguas de rack (iPDU), impedindo a visibilidade da margem real disponível de potência.",
        "p3": "**3. Procedimentos de Controle e Permissões de Trabalho Não Estruturados:** As rondas de manutenção preventiva, ensaios de comutação e controle de acesso de terceiros carecem de fluxos formais de autorização digital e rastreabilidade imutável.",
    },
    "fr": {
        "p1": "**1. Absence de Télémétrie Continue et Capacité Non Monitorée:** La gestion des capacités électriques et thermiques manque de surveillance télémétrique numérique en temps réel sur les tableaux généraux et bandeaux de baies (iPDU).",
        "p3": "**3. Procédures de Contrôle et Permis de Travail Non Structurés:** Les rondes de maintenance préventive, les tests de commutation et le contrôle d'accès des prestataires manquent de flux formels d'autorisation numérique et de traçabilité immuable.",
    },
    "ja": {
        "p1": "**1. 継続的なテレメトリの欠如と未監視の電力容量:** 配電盤およびインテリジェントラックPDUにおいてデジタルリアルタイムテレメトリが不足しており、新規負荷展開時の電力マージン把握が困難です。",
        "p3": "**3. 非構造化保守手順と作業許可プロセスの摩擦:** 予防保守巡回、発電機切替試験、および外部委託業者の入室管理において、デジタル承認ワークフローと不変の監査証跡が確立されていません。",
    },
    "de": {
        "p1": "**1. Mangel an kontinuierlicher Telemetrie und nicht überwachte elektrische Kapazität:** Das Management der elektrischen und thermischen Kapazität verfügt über keine digitale Echtzeittelemetrie an Hauptverteilern und Rack-PDUs.",
        "p3": "**3. Unstrukturierte Wartungsverfahren und Arbeitserlaubnislücken (ePtW):** Vorbeugende Wartungsrundgänge, Umschaltprüfungen und Zutrittskontrollen für externe Dienstleister verfügen über keine formellen digitalen Autorisierungsworkflows.",
    },
}


def main() -> None:
    with open(LOCALES_PATH, "r", encoding="utf-8") as f:
        locales = json.load(f)

    for lang, texts in TEXT_BY_LANG.items():
        if lang in locales:
            locales[lang]["cross_cutting_debt_pattern_1"] = texts["p1"]
            locales[lang]["cross_cutting_debt_pattern_3"] = texts["p3"]
            locales[lang]["cross_cutting_debt_t1_p1"] = texts["p1"]
            locales[lang]["cross_cutting_debt_t1_p3"] = texts["p3"]

    with open(LOCALES_PATH, "w", encoding="utf-8") as f:
        json.dump(locales, f, ensure_ascii=False, indent=2)

    print(f"Successfully remediated cross-cutting debt templates across {len(TEXT_BY_LANG)} locales.")


if __name__ == "__main__":
    main()
