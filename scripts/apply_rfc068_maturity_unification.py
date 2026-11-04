#!/usr/bin/env python3
"""Apply RFC 068: Canonical Maturity Model Scale Unification across all 6 locales."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = REPO_ROOT / "engine_config" / "locales.json"

RFC_068_UPDATES = {
    "es": {
        "tomo_ch1_p1": "La evaluación de los diez dominios tecnológicos de {client_name} refleja una infraestructura operativa funcional que ha dado soporte eficaz al crecimiento histórico del grupo, situándose en un índice de madurez consolidado de {global_score} sobre 5,00 (Nivel 2 CMMI — Repetible). No obstante, la expansión internacional tras la integración de Secil y la evolución de los requisitos industriales sitúan a la arquitectura actual en el límite de su capacidad de diseño original. Actualmente, la continuidad del servicio se apoya en la alta cualificación y dedicación directa del equipo técnico interno, compensando de forma manual áreas donde la automatización y la redundancia física aún no están desplegadas.",
        "tomo_ch2_intro": "La evaluación de capacidades de infraestructura y operaciones se rige por el estándar internacional CMMI (Capability Maturity Model Integration) y las mejores prácticas de la industria en una escala continua de cinco niveles objetivos: Nivel 1 (Inicial / Ad-Hoc: 1,00 - 1,79), Nivel 2 (Repetible / Reactivo: 1,80 - 2,59), Nivel 3 (Definido / Proactivo: 2,60 - 3,39), Nivel 4 (Gestionado / Medido Cuantitativamente: 3,40 - 4,19) y Nivel 5 (Optimizado / Mejora Continua: 4,20 - 5,00).",
    },
    "en": {
        "tomo_ch1_p1": "The technical assessment across {client_name}'s ten technology domains reflects a functional operating infrastructure that has supported historical growth, placing the consolidated maturity index at {global_score} out of 5.00 (CMMI Level 2 — Repeatable). However, post-merger international expansion and demanding industrial SLAs push the current architecture to its original capacity limits. Operational continuity presently relies heavily on the dedication of internal technical personnel to bridge gaps where automated failover and physical redundancy remain unaddressed.",
        "tomo_ch2_intro": "The infrastructure and operations capability assessment is governed by the international CMMI (Capability Maturity Model Integration) standard and industry best practices across a continuous five-tier scale: Level 1 (Initial / Ad-Hoc: 1.00 - 1.79), Level 2 (Repeatable / Reactive: 1.80 - 2.59), Level 3 (Defined / Proactive: 2.60 - 3.39), Level 4 (Managed / Quantitatively Measured: 3.40 - 4.19), and Level 5 (Optimized / Continuous Improvement: 4.20 - 5.00).",
    },
    "pt": {
        "tomo_ch1_p1": "A avaliação dos dez domínios tecnológicos de {client_name} reflete uma infraestrutura operacional funcional que sustentou o crescimento histórico do grupo, situando-se em um índice de maturidade consolidado de {global_score} em 5,00 (Nível 2 CMMI — Repetível). No entanto, a expansão internacional e a evolução dos requisitos industriais colocam a arquitetura atual no limite de sua capacidade de projeto original.",
        "tomo_ch2_intro": "A avaliação de capacidades de infraestrutura e operações é regida pelo padrão internacional CMMI (Capability Maturity Model Integration) e pelas melhores práticas da indústria em uma escala contínua de cinco níveis: Nível 1 (Inicial / Ad-Hoc: 1,00 - 1,79), Nível 2 (Repetível / Reativo: 1,80 - 2,59), Nível 3 (Definido / Proativo: 2,60 - 3,39), Nível 4 (Gerenciado / Medido Quantitativamente: 3,40 - 4,19) e Nível 5 (Otimizado / Melhoria Contínua: 4,20 - 5,00).",
    },
    "fr": {
        "tomo_ch1_p1": "L'évaluation des dix domaines technologiques de {client_name} reflète une infrastructure opérationnelle fonctionnelle ayant soutenu la croissance historique du groupe, s'établissant à un indice de maturité consolidé de {global_score} sur 5,00 (Niveau 2 CMMI — Répétable). Cependant, l'expansion internationale et l'évolution des exigences industrielles placent l'architecture actuelle à la limite de sa capacité de conception initiale.",
        "tomo_ch2_intro": "L'évaluation des capacités d'infrastructure et d'opérations est régie par la norme internationale CMMI (Capability Maturity Model Integration) et les meilleures pratiques de l'industrie sur une échelle continue à cinq niveaux : Niveau 1 (Initial / Ad-Hoc : 1,00 - 1,79), Niveau 2 (Répétable / Réactif : 1,80 - 2,59), Niveau 3 (Défini / Proactif : 2,60 - 3,39), Niveau 4 (Géré / Mesuré Quantitativement : 3,40 - 4,19) et Niveau 5 (Optimisé / Amélioration Continue : 4,20 - 5,00).",
    },
    "de": {
        "tomo_ch1_p1": "Die Bewertung der zehn Technologiedomänen von {client_name} zeigt eine funktionale Betriebsinfrastruktur, die das historische Wachstum wirksam unterstützt hat, mit einem konsolidierten Reifegradindex von {global_score} von 5,00 (CMMI-Stufe 2 — Wiederholbar). Die internationale Expansion und steigende Industrieanforderungen bringen die aktuelle Architektur jedoch an ihre Auslegungsgrenzen.",
        "tomo_ch2_intro": "Die Bewertung der Infrastruktur- und Betriebsfähigkeiten richtet sich nach dem internationalen CMMI-Standard (Capability Maturity Model Integration) und bewährten Branchenpraktiken auf einer kontinuierlichen fünfstufigen Skala: Stufe 1 (Initial / Ad-Hoc: 1,00 - 1,79), Stufe 2 (Wiederholbar / Reaktiv: 1,80 - 2,59), Stufe 3 (Definiert / Proaktiv: 2,60 - 3,39), Stufe 4 (Gesteuert / Quantitativ Gemessen: 3,40 - 4,19) und Stufe 5 (Optimiert / Kontinuierliche Verbesserung: 4,20 - 5,00).",
    },
    "ja": {
        "tomo_ch1_p1": "{client_name} の10の技術ドメインにわたる評価は、グループの歴史的成長を支えてきた機能的な運用インフラを反映しており、統合成熟度指数は 5.00 点中 {global_score} 点（CMMI レベル2 — 反復可能）に位置しています。しかし、国際展開と産業SLAの高度化により、現行アーキテクチャは設計上の許容量の限界に達しています。",
        "tomo_ch2_intro": "インフラストラクチャおよび運用能力の評価は、国際標準であるCMMI（能力成熟度モデル統合）および業界標準のベストプラクティスに準拠し、5段階の連続スケールで構成されています：レベル1（初期／アドホック：1.00 - 1.79）、レベル2（反復可能／リアクティブ：1.80 - 2.59）、レベル3（定義済み／プロアクティブ：2.60 - 3.39）、レベル4（管理された／定量的測定：3.40 - 4.19）、レベル5（最適化された／継続的改善：4.20 - 5.00）。",
    },
}


def main() -> None:
    with open(LOCALES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for loc, updates in RFC_068_UPDATES.items():
        if loc in data:
            for k, val in updates.items():
                data[loc][k] = val

    with open(LOCALES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Successfully applied RFC 068 updates across all 6 locales!")


if __name__ == "__main__":
    main()
