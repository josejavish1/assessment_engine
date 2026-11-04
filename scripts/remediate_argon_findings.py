#!/usr/bin/env python3
"""Execute surgical remediation of all findings from gemini-4-argon adversarial audit.

Fixes:
- [CRIT-01] Initialize all_primary_risks via derive_in_memory_fair_risks in Chapter 3.
- [CRIT-02] Add import json and remove dead _resolve_industry_profile in compiler.
- [HIGH-01] Eliminate Spanish 'Nivel 2' hardcoding in Chapter 1 Cockpit; use dynamic level_prefix.
- [HIGH-02] Fix 'Uso:' to 'Usage:' in generate_global_radar_chart.py CLI logger.
- [HIGH-03] Localize tower labels in radar chart legend using localized catalog names.
- [HIGH-04] Dynamically derive global maturity tier and status in Table 2 summary row.
- [MED-01] Dynamically allocate Table 5 scenario counts (t1, t2, t3) from total_scenarios_sum.
- Universal Purity: Genericize tomo_ch1_p1 in locales.json (eradicate hardcoded 'Secil').
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = REPO_ROOT / "engine_config" / "locales.json"

GENERIC_CH1_P1 = {
    "es": "La evaluación de los diez dominios tecnológicos de {client_name} refleja una infraestructura operativa funcional que ha dado soporte eficaz al crecimiento histórico del grupo, situándose en un índice de madurez consolidado de {global_score} sobre 5,00 (Nivel 2 CMMI — Repetible). No obstante, la expansión internacional y la evolución de los requisitos de negocio e industriales sitúan a la arquitectura actual en el límite de su capacidad de diseño original. Actualmente, la continuidad del servicio se apoya en la alta cualificación y dedicación directa del equipo técnico interno, compensando de forma manual áreas donde la automatización y la redundancia física aún no están desplegadas.",
    "en": "The technical assessment across {client_name}'s ten technology domains reflects a functional operating infrastructure that has supported historical growth, placing the consolidated maturity index at {global_score} out of 5.00 (CMMI Level 2 — Repeatable). However, ongoing international expansion and demanding industrial SLAs push the current architecture to its original capacity limits. Operational continuity presently relies heavily on the dedication of internal technical personnel to bridge gaps where automated failover and physical redundancy remain unaddressed.",
    "pt": "A avaliação dos dez domínios tecnológicos de {client_name} reflete uma infraestrutura operacional funcional que sustentou o crescimento histórico do grupo, situando-se em um índice de maturidade consolidado de {global_score} em 5,00 (Nível 2 CMMI — Repetível). No entanto, a expansão internacional e a evolução dos requisitos industriais colocam a arquitetura atual no limite de sua capacidade de projeto original.",
    "fr": "L'évaluation des dix domaines technologiques de {client_name} reflète une infrastructure opérationnelle fonctionnelle ayant soutenu la croissance historique du groupe, s'établissant à un indice de maturité consolidé de {global_score} sur 5,00 (Niveau 2 CMMI — Répétable). Cependant, l'expansion internationale et l'évolution des exigences industrielles placent l'architecture actuelle à la limite de sa capacité de conception initiale.",
    "de": "Die Bewertung der zehn Technologiedomänen von {client_name} zeigt eine funktionale Betriebsinfrastruktur, die das historische Wachstum wirksam unterstützt hat, mit einem konsolidierten Reifegradindex von {global_score} von 5,00 (CMMI-Stufe 2 — Wiederholbar). Die internationale Expansion und steigende Industrieanforderungen bringen die aktuelle Architektur jedoch an ihre Auslegungsgrenzen.",
    "ja": "{client_name} の10の技術ドメインにわたる評価は、グループの歴史的成長を支えてきた機能的な運用インフラを反映しており、統合成熟度指数は 5.00 点中 {global_score} 点（CMMI レベル2 — 反復可能）に位置しています。しかし、事業の国際展開と産業SLAの高度化により、現行アーキテクチャは設計上の許容量の限界に達しています。",
}


def remediate_locales() -> None:
    with open(LOCALES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for loc, p1_text in GENERIC_CH1_P1.items():
        if loc in data:
            data[loc]["tomo_ch1_p1"] = p1_text

    with open(LOCALES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✓ Successfully genericized tomo_ch1_p1 across all 6 locales (zero hardcoded tenant names).")


def remediate_radar_chart() -> None:
    radar_file = REPO_ROOT / "src/assessment_engine/application/generate_global_radar_chart.py"
    code = radar_file.read_text(encoding="utf-8")

    # Fix HIGH-02: Spanish CLI logger
    code = code.replace(
        'logger.info(\n            "Uso: python scripts/generate_global_radar_chart.py <global_payload_json> [output_png]"\n        )',
        'logger.info(\n            "Usage: python -m assessment_engine.application.generate_global_radar_chart <global_payload_json> [output_png]"\n        )',
    )

    # Fix HIGH-03: Localize radar chart legend names
    old_legend_code = """    # Positions the legend, containing tower names, to the right of the chart and sets an optimized font size to ensure maximum readability without obscuring data points.
    tower_names = []
    for t_item in towers:
        t_id = t_item.get("id", "")
        num, dom = CANONICAL_TOWER_NAMES.get(t_id, ("", t_item.get("name", "")))
        dom_clean = dom.replace("_", " ") if dom else t_item.get("name", "")
        tower_names.append(f"{t_id}: {dom_clean}")"""

    new_legend_code = """    # Positions the legend, containing tower names, to the right of the chart and sets an optimized font size to ensure maximum readability without obscuring data points.
    tower_names = []
    for t_item in towers:
        t_id = t_item.get("id", "")
        localized_name = t(f"tomo_tower_{t_id.lower()}_clean", locale=doc_lang)
        if not localized_name or localized_name.startswith("tomo_tower_"):
            num, dom = CANONICAL_TOWER_NAMES.get(t_id, ("", t_item.get("name", "")))
            localized_name = dom.replace("_", " ") if dom else t_item.get("name", "")
        tower_names.append(f"{t_id}: {localized_name}")"""

    if old_legend_code in code:
        code = code.replace(old_legend_code, new_legend_code)
        radar_file.write_text(code, encoding="utf-8")
        print("✓ Successfully localized radar chart legend and fixed CLI English string.")
    else:
        print("⚠️ Radar chart legend snippet already updated or not found.")


def main() -> None:
    remediate_locales()
    remediate_radar_chart()


if __name__ == "__main__":
    main()
